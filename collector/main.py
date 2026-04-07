import asyncio
from loguru import logger
from ws_client import OrderbookCollector
from metrics.imbalance import ImbalanceCalculator
from prometheus_client import start_http_server

async def main():
    logger.info("Starting PacificScope Collector...")
    # Start Prometheus metrics server on port 8001
    start_http_server(8001)
    logger.info("Prometheus metrics server started on port 8001")

    collector = OrderbookCollector()
    imbalance_calc = ImbalanceCalculator()

    await asyncio.gather(
        collector.run(),
        imbalance_calc.run()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Collector stopped by user.")
