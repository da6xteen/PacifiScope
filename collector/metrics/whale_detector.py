import asyncio
import json
import gzip
import os
import time
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from loguru import logger
from redis.asyncio import Redis
import asyncpg

WHALE_SIZE_USD = float(os.getenv("WHALE_SIZE_USD", "50000"))
ICEBERG_TICKS = 5

class WhaleDetector:
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        self.db_url = os.getenv("DATABASE_URL", "postgresql://postgres:password@timescaledb:5432/pacifiscope")
        self.redis = Redis.from_url(self.redis_url, decode_responses=False)
        self.pg_pool: Optional[asyncpg.Pool] = None
        self.batch_size = 50
        self.batch_timeout = 1.0
        self.data_buffer = []
        self.running = True

        # Track orders for iceberg detection: (symbol, side, price) -> {last_size_usd, ticks, last_ts}
        self.tracked_orders = {}

    async def connect_db(self):
        try:
            self.pg_pool = await asyncpg.create_pool(self.db_url)
            logger.info("WhaleDetector connected to TimescaleDB")
        except Exception as e:
            logger.error(f"WhaleDetector failed to connect to DB: {e}")

    async def flush_batch(self):
        if not self.data_buffer or not self.pg_pool:
            return

        batch_to_insert = self.data_buffer[:]
        self.data_buffer = []

        try:
            async with self.pg_pool.acquire() as conn:
                await conn.executemany("""
                    INSERT INTO whale_events (
                        time, symbol, price, size_usd, type, persisted_ticks
                    ) VALUES ($1, $2, $3, $4, $5, $6)
                """, batch_to_insert)
            logger.debug(f"Inserted {len(batch_to_insert)} whale events")
        except Exception as e:
            logger.error(f"Error inserting whale events: {e}")

    async def batch_timer(self):
        while self.running:
            await asyncio.sleep(self.batch_timeout)
            await self.flush_batch()

    async def process_snapshot(self, snapshot: Dict[str, Any]):
        symbol = snapshot["symbol"]
        bids = snapshot["bids"]
        asks = snapshot["asks"]
        ts = snapshot["ts"]
        dt = datetime.fromtimestamp(ts / 1000, tz=timezone.utc)

        current_snapshot_keys = set()

        # Process bids and asks
        for side, levels in [("bid", bids), ("ask", asks)]:
            for price, size in levels:
                size_usd = price * size
                if size_usd >= WHALE_SIZE_USD:
                    key = (symbol, side, price)
                    current_snapshot_keys.add(key)

                    if key in self.tracked_orders:
                        self.tracked_orders[key]["ticks"] += 1
                        self.tracked_orders[key]["last_size_usd"] = size_usd
                        self.tracked_orders[key]["last_ts"] = ts
                    else:
                        self.tracked_orders[key] = {
                            "ticks": 1,
                            "last_size_usd": size_usd,
                            "last_ts": ts,
                            "alerted_iceberg": False
                        }

                    order_info = self.tracked_orders[key]

                    # Detect Iceberg
                    if order_info["ticks"] >= ICEBERG_TICKS and not order_info["alerted_iceberg"]:
                        await self.emit_alert(dt, symbol, price, size_usd, "iceberg", order_info["ticks"])
                        order_info["alerted_iceberg"] = True
                    # Initial Whale Alert
                    elif order_info["ticks"] == 1:
                        alert_type = f"whale_{side}"
                        await self.emit_alert(dt, symbol, price, size_usd, alert_type, 1)

        # Cleanup tracked orders that disappeared
        disappeared = [k for k in self.tracked_orders if k[0] == symbol and k not in current_snapshot_keys]
        for k in disappeared:
            del self.tracked_orders[k]

    async def emit_alert(self, dt, symbol, price, size_usd, alert_type, ticks):
        event = {
            "time": dt.isoformat(),
            "symbol": symbol,
            "price": price,
            "size_usd": size_usd,
            "type": alert_type,
            "persisted_ticks": ticks
        }

        # Publish to Redis
        await self.redis.publish(f"whales:{symbol}", json.dumps(event))

        # Buffer for DB
        self.data_buffer.append((
            dt, symbol, price, size_usd, alert_type, ticks
        ))

        logger.info(f"🐋 ALERT: {alert_type.upper()} {symbol} ${size_usd:,.0f} @ {price} ({ticks} ticks)")

    async def run(self):
        await self.connect_db()
        asyncio.create_task(self.batch_timer())

        pubsub = self.redis.pubsub()
        await pubsub.psubscribe("orderbook:*")

        logger.info("WhaleDetector listening to orderbook:* channels")

        try:
            async for message in pubsub.listen():
                if message["type"] == "pmessage":
                    try:
                        compressed_data = message["data"]
                        payload = gzip.decompress(compressed_data)
                        snapshot = json.loads(payload)
                        await self.process_snapshot(snapshot)
                    except Exception as e:
                        logger.error(f"WhaleDetector error: {e}")
        finally:
            await pubsub.punsubscribe("orderbook:*")
            self.running = False
            await self.flush_batch()
            if self.pg_pool:
                await self.pg_pool.close()
