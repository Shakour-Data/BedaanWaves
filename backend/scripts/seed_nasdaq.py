"""
Seed Nasdaq Composite constituents into the database.

Reads backend/nasdaq_symbols.csv and bulk-inserts all symbols as assets.
Uses PostgreSQL upsert for idempotency.

Run:
    cd backend
    python scripts/seed_nasdaq.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio  # noqa: E402
import csv  # noqa: E402
import logging  # noqa: E402
from datetime import timezone, datetime  # noqa: E402
from typing import List, Tuple  # noqa: E402

from sqlalchemy import select  # noqa: E402
from sqlalchemy.dialects.postgresql import insert as pg_insert  # noqa: E402
from app.db.base import async_session_maker  # noqa: E402
from app.models.models import Asset  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

NASDAQ_CSV_PATH = os.path.join(
    os.path.dirname(__file__), "..", "nasdaq_symbols.csv"
)


def load_symbols_from_csv() -> List[Tuple[str, str]]:
    """Load (symbol, security_name) tuples from CSV."""
    symbols = []
    with open(NASDAQ_CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)  # skip header
        for row in reader:
            if row and len(row) >= 2 and row[0] and not row[0].startswith("File Creation"):
                symbols.append((row[0].strip(), row[1].strip() if len(row) > 1 else row[0].strip()))
    logger.info(f"Loaded {len(symbols)} symbols from CSV")
    return symbols


async def seed_nasdaq_symbols():
    """Bulk insert Nasdaq symbols as assets."""
    symbols = load_symbols_from_csv()
    if not symbols:
        logger.error("No symbols loaded from CSV")
        return

    batch_size = 500
    total_inserted = 0

    async with async_session_maker() as session:
        for i in range(0, len(symbols), batch_size):
            batch = symbols[i:i + batch_size]
            rows = []
            for symbol, name in batch:
                rows.append({
                    "symbol": symbol,
                    "name": name,
                    "asset_class": "EQUITY",
                    "market": "NASDAQ",
                    "country_code": "US",
                    "currency": "USD",
                    "active": True,
                })

            stmt = pg_insert(Asset).values(rows)
            stmt = stmt.on_conflict_do_update(
                index_elements=["symbol"],
                set_={
                    "name": stmt.excluded.name,
                    "asset_class": stmt.excluded.asset_class,
                    "market": stmt.excluded.market,
                    "country_code": stmt.excluded.country_code,
                    "currency": stmt.excluded.currency,
                    "active": stmt.excluded.active,
                    "updated_at": datetime.now(timezone.utc),
                },
            )
            await session.execute(stmt)
            await session.commit()
            total_inserted += len(rows)
            logger.info(f"Processed batch {i // batch_size + 1}: {len(rows)} symbols")

    # Ensure index asset exists
    async with async_session_maker() as session:
        existing = await session.execute(select(Asset).where(Asset.symbol == "^IXIC"))
        if not existing.scalar_one_or_none():
            index_asset = Asset(
                symbol="^IXIC",
                name="Nasdaq Composite",
                asset_class="INDEX",
                market="NASDAQ",
                country_code="US",
                currency="USD",
                active=True,
            )
            session.add(index_asset)
            await session.commit()
            logger.info("Inserted ^IXIC index asset")

    logger.info(f"Seeding complete. Total symbols processed: {total_inserted}")


async def main():
    await seed_nasdaq_symbols()


if __name__ == "__main__":
    asyncio.run(main())
