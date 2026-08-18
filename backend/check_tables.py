#!/usr/bin/env python
import sys
sys.path.insert(0, 'E:/Shakour/BedaanProjects/OldFils/BedaanWaves/backend')
import asyncio
from app.db.base import get_async_session
from sqlalchemy import text

async def check_all_tables():
    async for session in get_async_session():
        result = await session.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name"))
        tables = [row[0] for row in result]
        print(f"Currently existing tables ({len(tables)}):")
        for t in tables:
            print(f"  - {t}")
        break

asyncio.run(check_all_tables())
