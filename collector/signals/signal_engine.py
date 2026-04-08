import asyncio
import os
import json
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from loguru import logger
import asyncpg
from signals.rules import rule_1_imbalance_level, rule_2_imbalance_trend, rule_3_whale_influence

class SignalEngine:
    def __init__(self):
        self.db_url = os.getenv("DATABASE_URL", "postgresql://postgres:password@timescaledb:5432/pacifiscope")
        self.pg_pool: Optional[asyncpg.Pool] = None
        self.interval = 60  # Run every 60 seconds
        self.running = True

    async def connect_db(self):
        try:
            self.pg_pool = await asyncpg.create_pool(self.db_url)
            logger.info("SignalEngine connected to TimescaleDB")
        except Exception as e:
            logger.error(f"SignalEngine failed to connect to DB: {e}")

    async def get_symbols(self) -> List[str]:
        async with self.pg_pool.acquire() as conn:
            rows = await conn.fetch("SELECT DISTINCT symbol FROM orderbook_metrics")
            return [row['symbol'] for row in rows]

    async def get_recent_data(self, symbol: str):
        async with self.pg_pool.acquire() as conn:
            # Last 10 imbalance readings
            metrics_rows = await conn.fetch("""
                SELECT imbalance_ratio
                FROM orderbook_metrics
                WHERE symbol = $1
                ORDER BY time DESC
                LIMIT 10
            """, symbol)

            # Whale events in last 2 minutes
            whale_rows = await conn.fetch("""
                SELECT type
                FROM whale_events
                WHERE symbol = $1 AND time >= now() - INTERVAL '2 minutes'
            """, symbol)

            return (
                [row['imbalance_ratio'] for row in reversed(metrics_rows)],
                [dict(row) for row in whale_rows]
            )

    def evaluate_signals(self, symbol: str, imbalance_readings: List[float], recent_whales: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        signals = []

        # Rule evaluations
        results = {
            "RULE_1": rule_1_imbalance_level(imbalance_readings),
            "RULE_2": rule_2_imbalance_trend(imbalance_readings),
            "RULE_3": rule_3_whale_influence(imbalance_readings, recent_whales)
        }

        # Aggregate by direction
        for direction in ["LONG", "SHORT"]:
            rules_fired = [rule for rule, res in results.items() if res == direction]
            if rules_fired:
                confidence = (len(rules_fired) / len(results)) * 100
                signals.append({
                    "time": datetime.now(timezone.utc),
                    "symbol": symbol,
                    "direction": direction,
                    "confidence": confidence,
                    "rules_fired": rules_fired,
                    "expires_at": datetime.now(timezone.utc) + timedelta(minutes=5)
                })

        return signals

    async def store_signals(self, signals: List[Dict[str, Any]]):
        if not signals:
            return

        async with self.pg_pool.acquire() as conn:
            await conn.executemany("""
                INSERT INTO signals (time, symbol, direction, confidence, rules_fired, expires_at)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, [(s['time'], s['symbol'], s['direction'], s['confidence'], s['rules_fired'], s['expires_at']) for s in signals])

        for s in signals:
            logger.info(f"🚦 SIGNAL: {s['direction']} {s['symbol']} Confidence: {s['confidence']:.1f}% Rules: {', '.join(s['rules_fired'])}")

    async def run_once(self):
        try:
            symbols = await self.get_symbols()
            all_signals = []
            for symbol in symbols:
                imbalance_readings, recent_whales = await self.get_recent_data(symbol)
                signals = self.evaluate_signals(symbol, imbalance_readings, recent_whales)
                all_signals.extend(signals)

            await self.store_signals(all_signals)
        except Exception as e:
            logger.error(f"Error in SignalEngine run_once: {e}")

    async def run(self):
        await self.connect_db()
        logger.info("SignalEngine starting main loop...")
        while self.running:
            await self.run_once()
            await asyncio.sleep(self.interval)

    async def replay(self, start_time: datetime, end_time: datetime, symbol: str):
        """Replay on historical data for backtesting."""
        await self.connect_db()
        logger.info(f"Starting replay for {symbol} from {start_time} to {end_time}")

        current_time = start_time
        while current_time <= end_time:
            async with self.pg_pool.acquire() as conn:
                # Fetch data as if 'now' was current_time
                metrics_rows = await conn.fetch("""
                    SELECT imbalance_ratio
                    FROM orderbook_metrics
                    WHERE symbol = $1 AND time <= $2
                    ORDER BY time DESC
                    LIMIT 10
                """, symbol, current_time)

                whale_rows = await conn.fetch("""
                    SELECT type
                    FROM whale_events
                    WHERE symbol = $1 AND time <= $2 AND time >= $2 - INTERVAL '2 minutes'
                """, symbol, current_time)

                imbalance_readings = [row['imbalance_ratio'] for row in reversed(metrics_rows)]
                recent_whales = [dict(row) for row in whale_rows]

                signals = self.evaluate_signals(symbol, imbalance_readings, recent_whales)
                if signals:
                    # Adjust time for historical accuracy
                    for s in signals:
                        s['time'] = current_time
                        s['expires_at'] = current_time + timedelta(minutes=5)
                    await self.store_signals(signals)

            current_time += timedelta(minutes=1)
        logger.info(f"Replay finished for {symbol}")
