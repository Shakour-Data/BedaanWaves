#!/usr/bin/env python
import os
import sys
sys.path.insert(0, '.')
from app.db.base import get_async_session
from sqlalchemy import text
import asyncio

async def check_database():
    async for session in get_async_session():
        result = await session.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
        tables = [row[0] for row in result]
        print("Available tables:", tables)

        critical_tables = ['raw_market_data', 'market_data_snapshots', 'assets']
        missing_tables = [t for t in critical_tables if t not in tables]
        if missing_tables:
            print(f"Missing critical tables: {missing_tables}")

        for table in tables:
            try:
                cnt = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = cnt.scalar()
                print(f"{table}: {count} rows")
            except Exception as e:
                print(f"{table}: Error - {e}")
        break

asyncio.run(check_database())
