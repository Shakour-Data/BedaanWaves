
import asyncio
import sys
import os

# Add the backend directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.base import async_session_maker
from app.models.models import MacroIndicator
from sqlalchemy import select

async def check():
    print("Starting check...")
    try:
        async with async_session_maker() as session:
            print("Session created.")
            query = select(MacroIndicator.indicator_code).distinct()
            result = await session.execute(query)
            codes = result.scalars().all()
            print(f"Available Macro Indicator Codes: {codes}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check())
