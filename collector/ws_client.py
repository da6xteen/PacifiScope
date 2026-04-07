import asyncio
import json
import gzip
import os
import time
from typing import Dict, List, Any, Optional
import aiohttp
import websockets
from loguru import logger
from sortedcontainers import SortedDict
from redis.asyncio import Redis
from prometheus_client import Counter

# Metrics
ORDERBOOK_UPDATES = Counter(
    "orderbook_updates_total", "Total number of orderbook updates", ["symbol"]
)
WS_RECONNECTS = Counter("ws_reconnects_total", "Total number of WebSocket reconnections")

class OrderbookCollector:
    def __init__(self):
        self.ws_url = os.getenv("PACIFICA_WS_URL", "wss://ws.pacifica.fi/ws")
        self.api_url = os.getenv("PACIFICA_API_URL", "https://api.pacifica.fi/api/v1")
        self.redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        self.redis = Redis.from_url(self.redis_url, decode_responses=False)
        self.symbols: List[str] = []
        self.orderbooks: Dict[str, Dict[str, SortedDict]] = {}
        self.reconnect_delay = 1
        self.max_reconnect_delay = 30
        self.running = True

    async def fetch_symbols(self):
        """Fetch all market symbols from Pacifica API."""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{self.api_url}/info") as response:
                    if response.status == 200:
                        res_json = await response.json()
                        if res_json.get("success"):
                            self.symbols = [item["symbol"] for item in res_json["data"]]
                            logger.info(f"Fetched {len(self.symbols)} symbols")
                            for symbol in self.symbols:
                                self.orderbooks[symbol] = {
                                    "bids": SortedDict(),  # price -> size (using SortedDict to maintain order)
                                    "asks": SortedDict()   # price -> size
                                }
                        else:
                            logger.error(f"API error fetching symbols: {res_json.get('error')}")
                    else:
                        logger.error(f"Failed to fetch symbols: {response.status}")
            except Exception as e:
                logger.error(f"Error fetching symbols: {e}")
                raise

    def process_l2_update(self, data: Dict[str, Any]):
        """Process incoming L2 update message."""
        symbol = data.get("s")
        if not symbol or symbol not in self.orderbooks:
            return

        book = self.orderbooks[symbol]
        updates = data.get("l", [[], []])
        if len(updates) < 2:
            return
        bids, asks = updates[0], updates[1]

        for update in bids:
            price = float(update["p"])
            size = float(update["a"])
            if size == 0:
                book["bids"].pop(price, None)
            else:
                book["bids"][price] = size

        for update in asks:
            price = float(update["p"])
            size = float(update["a"])
            if size == 0:
                book["asks"].pop(price, None)
            else:
                book["asks"][price] = size

        ORDERBOOK_UPDATES.labels(symbol=symbol).inc()

    async def publish_snapshots(self):
        """Background task to publish snapshots to Redis every 500ms."""
        while self.running:
            start_time = time.time()
            for symbol, book in self.orderbooks.items():
                # Take top 20 bids (highest prices) and asks (lowest prices)
                # SortedDict is ascending, so top bids are the last 20
                bids_list = [[p, s] for p, s in list(book["bids"].items())[-20:]]
                bids_list.reverse() # Sort descending for the consumer

                # top asks are the first 20
                asks_list = [[p, s] for p, s in list(book["asks"].items())[:20]]

                if not bids_list and not asks_list:
                    continue

                snapshot = {
                    "symbol": symbol,
                    "bids": bids_list,
                    "asks": asks_list,
                    "ts": int(time.time() * 1000)
                }

                try:
                    payload = json.dumps(snapshot).encode("utf-8")
                    compressed_payload = gzip.compress(payload)
                    await self.redis.publish(f"orderbook:{symbol}", compressed_payload)
                except Exception as e:
                    logger.error(f"Error publishing to Redis for {symbol}: {e}")

            elapsed = time.time() - start_time
            sleep_time = max(0, 0.5 - elapsed)
            await asyncio.sleep(sleep_time)

    async def connect_and_listen(self):
        """WebSocket connection with exponential backoff and heartbeat."""
        while self.running:
            try:
                logger.info(f"Connecting to Pacifica WS: {self.ws_url}")
                async with websockets.connect(self.ws_url) as websocket:
                    self.reconnect_delay = 1

                    # Subscribe to all symbols
                    for symbol in self.symbols:
                        await websocket.send(json.dumps({
                            "method": "subscribe",
                            "params": {
                                "source": "book",
                                "symbol": symbol,
                                "agg_level": 1
                            }
                        }))

                    # Heartbeat task
                    async def heartbeat():
                        while self.running:
                            try:
                                await websocket.send(json.dumps({"method": "ping"}))
                                await asyncio.sleep(30)
                            except:
                                break

                    heartbeat_task = asyncio.create_task(heartbeat())

                    try:
                        async for message in websocket:
                            data = json.loads(message)
                            if data.get("channel") == "book":
                                self.process_l2_update(data.get("data", {}))
                            elif data.get("channel") == "pong":
                                pass
                    finally:
                        heartbeat_task.cancel()

            except (websockets.ConnectionClosed, Exception) as e:
                WS_RECONNECTS.inc()
                logger.error(f"WebSocket error: {e}. Reconnecting in {self.reconnect_delay}s...")
                await asyncio.sleep(self.reconnect_delay)
                self.reconnect_delay = min(self.reconnect_delay * 2, self.max_reconnect_delay)

    async def run(self):
        """Main entry point."""
        await self.fetch_symbols()
        if not self.symbols:
            logger.error("No symbols found. Exiting.")
            return

        # Start listening and publishing
        await asyncio.gather(
            self.connect_and_listen(),
            self.publish_snapshots()
        )
