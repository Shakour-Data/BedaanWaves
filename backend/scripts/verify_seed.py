import asyncio
import sys
sys.path.insert(0, r"E:\Shakour\BedaanProjects\BedaanWaves\backend")
from app.db.base import async_session_maker
from app.models.models import User, Asset, PriceCandle, Portfolio, Position
from sqlalchemy import select, func

async def main():
    async with async_session_maker() as session:
        for model in [User, Asset, PriceCandle, Portfolio, Position]:
            cnt = (await session.execute(select(func.count()).select_from(model))).scalar()
            print(model.__tablename__, cnt)

if __name__ == "__main__":
    asyncio.run(main())
