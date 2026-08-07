#!/usr/bin/env python
import sys
sys.path.insert(0, '.')
from app.db.base import get_async_session
from sqlalchemy import text
import asyncio

async def check_missing_tables():
    async for session in get_async_session():
        result = await session.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
        tables = [row[0] for row in result]
        
        # Check for tables that should exist per migration
        expected = ['ir_price_candles', 'intl_price_candles', 'crypto_price_candles']
        for t in expected:
            if t in tables:
                print(f'{t}: EXISTS')
            else:
                print(f'{t}: MISSING')
        
        # Check latest alembic version
        ver = await session.execute(text('SELECT version_num FROM alembic_version'))
        version = ver.scalar()
        print(f'Latest migration version: {version}')
        break

asyncio.run(check_missing_tables())