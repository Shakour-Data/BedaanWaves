#!/usr/bin/env python3
"""
Import Nasdaq stock symbols into the assets table.
"""

import asyncio
import csv
import sys
from datetime import datetime
from io import StringIO

import aiohttp
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import async_session_maker
from app.models.models import Asset


NASDAQ_CSV_URL = "https://datahub.io/core/nasdaq-listings/r/nasdaq-listed-symbols.csv"


async def fetch_nasdaq_data() -> list[dict]:
    """Fetch Nasdaq listed symbols from the CSV source."""
    async with aiohttp.ClientSession() as session:
        async with session.get(NASDAQ_CSV_URL) as response:
            if response.status != 200:
                raise RuntimeError(f"Failed to fetch CSV: {response.status}")
            text = await response.text()
    
    rows = []
    reader = csv.DictReader(StringIO(text))
    for row in reader:
        # Skip ETFs and test issues
        if row.get('ETF') == 'Y' or row.get('Test Issue') == 'Y':
            continue
        rows.append(row)
    return rows


def parse_company_name(security_name: str) -> str:
    """Extract company name from security name (before ' - ')."""
    if ' - ' in security_name:
        return security_name.split(' - ')[0].strip()
    return security_name.strip()


async def import_assets(session: AsyncSession, rows: list[dict]) -> int:
    """Import assets into database."""
    inserted = 0
    skipped = 0
    
    for row in rows:
        symbol = row.get('Symbol', '').strip()
        if not symbol:
            continue
        
        # Check if already exists
        stmt = select(Asset).where(Asset.symbol == symbol)
        result = await session.execute(stmt)
        if result.scalar_one_or_none():
            skipped += 1
            continue
        
        company_name = parse_company_name(row.get('Security Name', ''))
        
        # Determine asset class based on Market Category
        market_category = row.get('Market Category', '')
        if market_category == 'G':
            asset_class = 'EQUITY'
        elif market_category == 'Q':
            asset_class = 'EQUITY'
        elif market_category == 'S':
            asset_class = 'EQUITY'
        else:
            asset_class = 'EQUITY'
        
        asset = Asset(
            symbol=symbol,
            name=company_name,
            asset_class=asset_class,
            market='NASDAQ',
            sector=row.get('Market Category', ''),
            currency='USD',
            country_code='US',
            active=True,
            meta={
                'security_name': row.get('Security Name', ''),
                'market_category': row.get('Market Category', ''),
                'financial_status': row.get('Financial Status', ''),
                'round_lot_size': row.get('Round Lot Size', ''),
                'etf': row.get('ETF', ''),
                'next_shares': row.get('NextShares', ''),
            }
        )
        
        session.add(asset)
        inserted += 1
        
        # Flush periodically
        if inserted % 100 == 0:
            await session.flush()
    
    await session.commit()
    return inserted, skipped


async def main():
    """Main import function."""
    print("Fetching Nasdaq listed symbols...")
    rows = await fetch_nasdaq_data()
    print(f"Fetched {len(rows)} rows (excluding ETFs and test issues)")
    
    print("Importing into database...")
    async with async_session_maker() as session:
        inserted, skipped = await import_assets(session, rows)
    
    print(f"Import complete: {inserted} inserted, {skipped} skipped")


if __name__ == "__main__":
    asyncio.run(main())