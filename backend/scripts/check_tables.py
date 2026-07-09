import asyncio
import sys
sys.path.insert(0, r"E:\Shakour\BedaanProjects\BedaanWaves\backend")
from app.db.base import engine
from sqlalchemy import text

async def main():
    async with engine.begin() as conn:
        result = await conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'"))
        tables = [row[0] for row in result.fetchall()]
        print("Tables:", tables)
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
