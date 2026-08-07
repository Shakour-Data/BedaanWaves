#!/usr/bin/env python
import sys, asyncio
sys.path.insert(0, '.')
from app.db.base import get_async_session
from sqlalchemy import text

async def check_db():
    async for session in get_async_session():
        result = await session.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name"))
        tables = [row[0] for row in result]
        print("Tables in database:")
        for t in tables:
            print(f"  - {t}")
        break

asyncio.run(check_db())