import asyncio
import json
import gzip
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set
from loguru import logger

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        # symbol -> set of active WebSockets
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # symbol -> asyncio task for Redis subscription
        self.subscription_tasks: Dict[str, asyncio.Task] = {}

    async def connect(self, websocket: WebSocket, symbol: str):
        await websocket.accept()
        if symbol not in self.active_connections:
            self.active_connections[symbol] = set()
            # Start Redis subscription for this symbol
            self.subscription_tasks[symbol] = asyncio.create_task(
                self._subscribe_to_redis(websocket, symbol)
            )
        self.active_connections[symbol].add(websocket)
        logger.info(f"Client connected to WS /ws/live/{symbol}. Total clients: {len(self.active_connections[symbol])}")

    async def disconnect(self, websocket: WebSocket, symbol: str):
        if symbol in self.active_connections:
            if websocket in self.active_connections[symbol]:
                self.active_connections[symbol].remove(websocket)
            logger.info(f"Client disconnected from WS /ws/live/{symbol}. Remaining: {len(self.active_connections[symbol])}")
            if not self.active_connections[symbol]:
                del self.active_connections[symbol]
                # Cancel Redis subscription task
                if symbol in self.subscription_tasks:
                    self.subscription_tasks[symbol].cancel()
                    del self.subscription_tasks[symbol]
                logger.info(f"Unsubscribed from Redis for {symbol} (no more clients)")

    async def _subscribe_to_redis(self, websocket: WebSocket, symbol: str):
        """Listen to Redis Pub/Sub for a symbol and forward to all clients."""
        # Use websocket.app to get redis client instead of circular import
        redis = websocket.app.state.redis
        pubsub = redis.pubsub()
        channel = f"orderbook:{symbol}"

        try:
            await pubsub.subscribe(channel)
            logger.info(f"Subscribed to Redis channel: {channel}")

            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        data_raw = message["data"]
                        try:
                            # Try decompressing as Gzip
                            payload = gzip.decompress(data_raw)
                            data = json.loads(payload)
                        except (OSError, gzip.BadGzipFile):
                            # Not gzipped, assume plain JSON
                            data = json.loads(data_raw)

                        # Forward to all connected clients for this symbol
                        if symbol in self.active_connections:
                            disconnected_clients = []
                            for ws in list(self.active_connections[symbol]):
                                try:
                                    await ws.send_json(data)
                                except Exception:
                                    disconnected_clients.append(ws)

                            for ws in disconnected_clients:
                                await self.disconnect(ws, symbol)
                    except Exception as e:
                        logger.error(f"Error processing Redis message for {symbol}: {e}")
        except asyncio.CancelledError:
            logger.info(f"Redis subscription task for {symbol} cancelled")
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.close()

manager = ConnectionManager()

@router.websocket("/live/{symbol}")
async def websocket_endpoint(websocket: WebSocket, symbol: str):
    await manager.connect(websocket, symbol)
    try:
        while True:
            # Keep connection open, wait for client messages (though we don't expect any)
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(websocket, symbol)
    except Exception as e:
        logger.error(f"WebSocket error for {symbol}: {e}")
        await manager.disconnect(websocket, symbol)


class WhaleManager:
    def __init__(self):
        # symbol -> set of active WebSockets
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # symbol -> asyncio task for Redis subscription
        self.subscription_tasks: Dict[str, asyncio.Task] = {}

    async def connect(self, websocket: WebSocket, symbol: str):
        await websocket.accept()
        if symbol not in self.active_connections:
            self.active_connections[symbol] = set()
            self.subscription_tasks[symbol] = asyncio.create_task(
                self._subscribe_to_whales(websocket, symbol)
            )
        self.active_connections[symbol].add(websocket)
        logger.info(f"Client connected to Whale WS /ws/whales/{symbol}")

    async def disconnect(self, websocket: WebSocket, symbol: str):
        if symbol in self.active_connections:
            if websocket in self.active_connections[symbol]:
                self.active_connections[symbol].remove(websocket)
            if not self.active_connections[symbol]:
                del self.active_connections[symbol]
                if symbol in self.subscription_tasks:
                    self.subscription_tasks[symbol].cancel()
                    del self.subscription_tasks[symbol]
                logger.info(f"Unsubscribed from Whale Redis for {symbol}")

    async def _subscribe_to_whales(self, websocket: WebSocket, symbol: str):
        redis = websocket.app.state.redis
        pubsub = redis.pubsub()
        channel = f"whales:{symbol}"
        try:
            await pubsub.subscribe(channel)
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = json.loads(message["data"])
                    if symbol in self.active_connections:
                        disconnected_clients = []
                        for ws in list(self.active_connections[symbol]):
                            try:
                                await ws.send_json(data)
                            except Exception:
                                disconnected_clients.append(ws)
                        for ws in disconnected_clients:
                            await self.disconnect(ws, symbol)
        except asyncio.CancelledError:
            pass
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.close()

whale_manager = WhaleManager()

@router.websocket("/whales/{symbol}")
async def whale_websocket_endpoint(websocket: WebSocket, symbol: str):
    await whale_manager.connect(websocket, symbol)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await whale_manager.disconnect(websocket, symbol)
    except Exception as e:
        logger.error(f"Whale WebSocket error for {symbol}: {e}")
        await whale_manager.disconnect(websocket, symbol)
