#!/usr/bin/env python3
"""Verify database connection and Nasdaq data import."""

import asyncio
from sqlalchemy import text
from app.db.base import async_session_maker
from app.models.models import Asset


async def verify():
    async with async_session_maker() as session:
        result = await session.execute(text("SELECT COUNT(*) FROM assets"))
        total = result.scalar_one()
        print(f"Database connected successfully!")
        print(f"Total assets in database: {total}")
        
        result = await session.execute(text("SELECT symbol, market, asset_class FROM assets WHERE market='NASDAQ' LIMIT 10"))
        rows = result.fetchall()
        print("Sample NASDAQ stocks:")
        for row in rows:
            print(f"  {row}")
        
        result = await session.execute(text("SELECT COUNT(*) FROM assets WHERE market='NASDAQ'"))
        nasdaq_count = result.scalar_one()
        print(f"NASDAQ-specific count: {nasdaq_count}")


if __name__ == "__main__":
    asyncio.run(verify())