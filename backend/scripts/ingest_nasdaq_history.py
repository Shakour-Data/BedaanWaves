"""
Nasdaq Historical Data Backfill Script

Fetches historical data for Nasdaq Composite index and ALL constituents:
- Price candles (daily OHLCV)
- Fundamentals (quarterly income statements + ratios)
- Board members / officers
- Macro indicators
- News (yfinance)

Usage:
    python scripts/ingest_nasdaq_history.py [--symbols AAPL,MSFT,GOOGL] [--years 5] [--daily]
"""

import argparse
import asyncio
import logging
import sys
import time
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, ".")

from app.services.data.nasdaq_ingestion_service import NasdaqIngestionService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    parser = argparse.ArgumentParser(description="Nasdaq historical data backfill")
    parser.add_argument("--symbols", type=str, default=None,
                        help="Comma-separated list of symbols (default: all Nasdaq constituents from CSV)")
    parser.add_argument("--years", type=int, default=5,
                        help="Number of years of history to fetch (default: 5)")
    parser.add_argument("--daily", action="store_true",
                        help="Run daily incremental update instead of full backfill")
    args = parser.parse_args()

    symbols = args.symbols.split(",") if args.symbols else None

    service = NasdaqIngestionService()
    await service.initialize()

    start_time = time.time()
    try:
        if args.daily:
            logger.info("Running daily incremental update...")
            await service.daily_update(symbols)
        else:
            logger.info(f"Running full backfill: {args.years} years of history")
            results = await service.backfill_nasdaq(symbols=symbols, years=args.years)
            logger.info(f"Backfill results: {results}")
    finally:
        await service.shutdown()

    elapsed = time.time() - start_time
    logger.info(f"Completed in {elapsed:.1f} seconds")


if __name__ == "__main__":
    asyncio.run(main())
