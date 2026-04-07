import websockets
from loguru import logger
import os

class PacificaWSClient:
    def __init__(self):
        self.url = os.getenv("PACIFICA_WS_URL", "ws://localhost:8080")

    async def connect(self):
        logger.info(f"Connecting to {self.url}")
        self.websocket = await websockets.connect(self.url)

    async def listen(self):
        try:
            async for message in self.websocket:
                logger.info(f"Received message: {message}")
                # Process message and store in DB/Redis
        except Exception as e:
            logger.error(f"Error in websocket listener: {e}")
        finally:
            await self.websocket.close()
