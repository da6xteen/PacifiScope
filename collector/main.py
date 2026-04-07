import asyncio
from loguru import logger
from ws_client import PacificaWSClient

async def main():
    logger.info("Starting PacificScope Collector...")
    client = PacificaWSClient()
    await client.connect()
    await client.listen()

if __name__ == "__main__":
    asyncio.run(main())
