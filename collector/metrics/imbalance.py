import asyncio
import json
import gzip
import os
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from loguru import logger
from redis.asyncio import Redis
import asyncpg
from collections import deque

class ImbalanceCalculator:
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        self.db_url = os.getenv("DATABASE_URL", "postgresql://postgres:password@timescaledb:5432/pacifiscope")
        self.redis = Redis.from_url(self.redis_url, decode_responses=False)
        self.pg_pool: Optional[asyncpg.Pool] = None
        self.batch_size = 100
        self.batch_timeout = 0.5
        self.data_buffer = []
        self.running = True
        self.mid_price_history = {} # symbol -> deque[(timestamp, mid_price)]

    async def connect_db(self):
        self.pg_pool = await asyncpg.create_pool(self.db_url)
        logger.info("Connected to TimescaleDB")

    async def flush_batch(self):
        if not self.data_buffer:
            return

        batch_to_insert = self.data_buffer[:]
        self.data_buffer = []

        try:
            async with self.pg_pool.acquire() as conn:
                await conn.executemany("""
                    INSERT INTO orderbook_metrics (
                        time, symbol, imbalance_ratio, spread_bps,
                        depth_5bps, depth_10bps, depth_25bps, depth_50bps,
                        price_pressure, mid_price
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """, batch_to_insert)
            logger.debug(f"Inserted {len(batch_to_insert)} rows into orderbook_metrics")
        except Exception as e:
            logger.error(f"Error inserting into TimescaleDB: {e}")

    async def batch_timer(self):
        while self.running:
            await asyncio.sleep(self.batch_timeout)
            await self.flush_batch()

    def calculate_imbalance_ratio(self, bids: List[List[float]], asks: List[List[float]], mid: float) -> float:
        """
        imbalance_ratio = (bid_vol - ask_vol) / (bid_vol + ask_vol)
        where bid_vol = sum(size_i / (1 + |level_i - mid| / mid * 1000)) for top 5
        """
        def weighted_vol(levels):
            vol = 0
            for i in range(min(5, len(levels))):
                price, size = levels[i]
                weight = 1 / (1 + abs(price - mid) / mid * 1000)
                vol += size * weight
            return vol

        bid_vol = weighted_vol(bids)
        ask_vol = weighted_vol(asks)

        if bid_vol + ask_vol == 0:
            return 0
        return (bid_vol - ask_vol) / (bid_vol + ask_vol)

    def calculate_depth_imbalance(self, bids: List[List[float]], asks: List[List[float]], mid: float, bps: int) -> float:
        """depth_imbalance within N bps of mid"""
        limit = mid * (bps / 10000)

        def vol_in_range(levels):
            vol = 0
            for price, size in levels:
                if abs(price - mid) <= limit:
                    vol += size
                else:
                    break # Assuming levels are sorted by price proximity to mid
            return vol

        bid_vol = vol_in_range(bids)
        ask_vol = vol_in_range(asks)

        if bid_vol + ask_vol == 0:
            return 0
        return (bid_vol - ask_vol) / (bid_vol + ask_vol)

    def update_price_history(self, symbol: str, timestamp: float, mid_price: float) -> float:
        """
        Update mid price history and return mid_price_change_1min.
        mid_price_change_1min = mid_price_now - mid_price_1min_ago
        """
        if symbol not in self.mid_price_history:
            self.mid_price_history[symbol] = deque()

        history = self.mid_price_history[symbol]
        history.append((timestamp, mid_price))

        # Remove old entries (> 60s)
        cutoff = timestamp - 60
        while history and history[0][0] < cutoff:
            history.popleft()

        if len(history) < 2:
            return 0.0

        # Change since the oldest available price within the 1-minute window
        return mid_price - history[0][1]

    async def process_snapshot(self, snapshot: Dict[str, Any]):
        symbol = snapshot["symbol"]
        bids = snapshot["bids"]
        asks = snapshot["asks"]
        ts = snapshot["ts"] # ms
        dt = datetime.fromtimestamp(ts / 1000, tz=timezone.utc)

        if not bids or not asks:
            return

        best_bid = bids[0][0]
        best_ask = asks[0][0]
        mid_price = (best_bid + best_ask) / 2

        imbalance_ratio = self.calculate_imbalance_ratio(bids, asks, mid_price)
        spread_bps = (best_ask - best_bid) / mid_price * 10000

        depth_5 = self.calculate_depth_imbalance(bids, asks, mid_price, 5)
        depth_10 = self.calculate_depth_imbalance(bids, asks, mid_price, 10)
        depth_25 = self.calculate_depth_imbalance(bids, asks, mid_price, 25)
        depth_50 = self.calculate_depth_imbalance(bids, asks, mid_price, 50)

        mid_price_change_1min = self.update_price_history(symbol, ts / 1000, mid_price)
        price_pressure = imbalance_ratio * mid_price_change_1min

        self.data_buffer.append((
            dt, symbol, imbalance_ratio, spread_bps,
            depth_5, depth_10, depth_25, depth_50,
            price_pressure, mid_price
        ))

        if len(self.data_buffer) >= self.batch_size:
            await self.flush_batch()

    async def run(self):
        await self.connect_db()
        asyncio.create_task(self.batch_timer())

        pubsub = self.redis.pubsub()
        await pubsub.psubscribe("orderbook:*")

        logger.info("ImbalanceCalculator listening to orderbook:* channels")

        try:
            async for message in pubsub.listen():
                if message["type"] == "pmessage":
                    try:
                        compressed_data = message["data"]
                        payload = gzip.decompress(compressed_data)
                        snapshot = json.loads(payload)
                        await self.process_snapshot(snapshot)
                    except Exception as e:
                        logger.error(f"Error processing snapshot: {e}")
        finally:
            await pubsub.punsubscribe("orderbook:*")
            self.running = False
            await self.flush_batch()
            if self.pg_pool:
                await self.pg_pool.close()
