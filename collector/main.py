import asyncio
from loguru import logger
from ws_client import OrderbookCollector
from prometheus_client import start_http_server

async def main():
    logger.info("Starting PacificScope Collector...")
    # Start Prometheus metrics server on port 8001
    start_http_server(8001)
    logger.info("Prometheus metrics server started on port 8001")

    collector = OrderbookCollector()
    await collector.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Collector stopped by user.")
