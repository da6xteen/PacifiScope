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

class DemoReplay:
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        self.db_url = os.getenv("DATABASE_URL", "postgresql://postgres:password@timescaledb:5432/pacifiscope")
        self.redis = Redis.from_url(self.redis_url, decode_responses=False)
        self.pg_pool: Optional[asyncpg.Pool] = None
        self.speed_multiplier = 10.0
        self.running = True

    async def connect_db(self):
        self.pg_pool = await asyncpg.create_pool(self.db_url)
        logger.info("DemoReplay connected to TimescaleDB")

    def synthesize_orderbook(self, symbol: str, mid: float, spread_bps: float, imbalance: float) -> Dict[str, Any]:
        """Synthesize a top-20 orderbook from metrics to drive the frontend heatmap."""
        best_ask = mid * (1 + spread_bps / 20000)
        best_bid = mid * (1 - spread_bps / 20000)

        # Base volume unit
        base_vol = 10.0

        bid_vol_total = base_vol * (1 + imbalance)
        ask_vol_total = base_vol * (1 - imbalance)

        bids = []
        asks = []

        # Create 20 levels
        tick_size = mid * 0.0001 # 1bps steps
        for i in range(20):
            # Distribute volume roughly
            b_price = best_bid - i * tick_size
            a_price = best_ask + i * tick_size

            # Simple distribution: more volume near the top
            b_size = (bid_vol_total / 20) * (1.5 if i < 5 else 0.8)
            a_size = (ask_vol_total / 20) * (1.5 if i < 5 else 0.8)

            bids.append([b_price, b_size])
            asks.append([a_price, a_size])

        return {
            "symbol": symbol,
            "bids": bids,
            "asks": asks,
            "ts": int(time.time() * 1000)
        }

    async def fetch_data(self):
        """Fetch last 24h of data."""
        async with self.pg_pool.acquire() as conn:
            # Metrics
            logger.info("Fetching metrics for replay...")
            metrics = await conn.fetch("""
                SELECT time, symbol, imbalance_ratio, spread_bps, mid_price
                FROM orderbook_metrics
                WHERE time >= NOW() - INTERVAL '24 hours'
                ORDER BY time ASC
            """)

            # Whales
            logger.info("Fetching whale events for replay...")
            whales = await conn.fetch("""
                SELECT time, symbol, price, size_usd, type, persisted_ticks
                FROM whale_events
                WHERE time >= NOW() - INTERVAL '24 hours'
                ORDER BY time ASC
            """)

            return metrics, whales

    async def run(self):
        await self.connect_db()
        metrics, whales = await self.fetch_data()

        if not metrics:
            logger.warning("No metrics found in DB for the last 24h. Replay will have no data.")
            return

        logger.info(f"Starting replay of {len(metrics)} metrics and {len(whales)} whales at {self.speed_multiplier}x speed")

        start_sim_time = metrics[0]['time']
        start_real_time = time.time()

        m_idx = 0
        w_idx = 0

        while self.running and (m_idx < len(metrics) or w_idx < len(whales)):
            now_real = time.time()
            elapsed_real = now_real - start_real_time
            sim_elapsed = elapsed_real * self.speed_multiplier
            current_sim_time = start_sim_time + timedelta(seconds=sim_elapsed)

            # Process metrics
            while m_idx < len(metrics) and metrics[m_idx]['time'] <= current_sim_time:
                m = metrics[m_idx]
                snapshot = self.synthesize_orderbook(
                    m['symbol'], m['mid_price'], m['spread_bps'], m['imbalance_ratio']
                )

                # Update snapshot TS to now
                snapshot['ts'] = int(time.time() * 1000)

                payload = json.dumps(snapshot).encode("utf-8")
                compressed = gzip.compress(payload)
                await self.redis.publish(f"orderbook:{m['symbol']}", compressed)
                m_idx += 1

            # Process whales
            while w_idx < len(whales) and whales[w_idx]['time'] <= current_sim_time:
                w = whales[w_idx]
                event = {
                    "time": datetime.now(timezone.utc).isoformat(),
                    "symbol": w['symbol'],
                    "price": w['price'],
                    "size_usd": w['size_usd'],
                    "type": w['type'],
                    "persisted_ticks": w['persisted_ticks']
                }
                await self.redis.publish(f"whales:{w['symbol']}", json.dumps(event))
                w_idx += 1

            await asyncio.sleep(0.01) # 10ms resolution for replay loop

        logger.info("Replay completed.")
