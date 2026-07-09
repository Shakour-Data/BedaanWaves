import asyncio
import sys
sys.path.insert(0, r"E:\Shakour\BedaanProjects\BedaanWaves\backend")
from app.db.base import engine, Base
from sqlalchemy import text

async def main():
    async with engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
        print("Dropped and recreated public schema")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
