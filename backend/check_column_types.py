#!/usr/bin/env python
import sys
sys.path.insert(0, 'E:/Shakour/BedaanProjects/OldFils/BedaanWaves/backend')
from app.models.models import PriceCandle, Asset
print("Asset.id column type:", PriceCandle.asset_id.property.columns[0].py.type_)
import sqlalchemy
print("Asset.id column class:", PriceCandle.asset_id.property.columns[0].py.class_)

# Check the assets table in DB
async def check():
    from app.db.base import get_async_session
    from sqlalchemy import text
    async for session in get_async_session():
        result = await session.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'assets' AND column_name = 'id'"))
        row = result.first()
        if row:
            print(f"Assets.id in DB: {row.data_type}")
        result = await session.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'price_candles' AND column_name = 'asset_id'"))
        row = result.first()
        if row:
            print(f"PriceCandles.asset_id in DB: {row.data_type}")
        result = await session.execute(text("SELECT COUNT(*) FROM assets"))
        count = result.scalar()
        print(f"Assets count: {count}")
        break

import asyncio
asyncio.run(check())
