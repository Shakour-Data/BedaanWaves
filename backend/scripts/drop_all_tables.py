"""
Drop all database tables using SQLAlchemy metadata.

Uses Base.metadata.drop_all() so it stays in sync with models.py,
no raw SQL or hardcoded table names needed.

Run:
    cd backend
    python scripts/drop_all_tables.py
"""

import asyncio
import sys
import logging

sys.path.insert(0, r"E:\Shakour\BedaanProjects\BedaanWaves\backend")
from app.db.base import drop_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    logger.info("Dropping all tables from metadata...")
    await drop_db()


if __name__ == "__main__":
    asyncio.run(main())
