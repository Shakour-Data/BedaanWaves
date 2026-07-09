"""
Seed data script for local development.

Populates PostgreSQL with sample data:
- Demo user
- Sample TSE assets
- Price candles for each asset
- Sample portfolio

Run:
    cd backend
    python scripts/seed.py
"""

import asyncio
import random
from datetime import datetime, timedelta

from sqlalchemy import insert, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import async_session_maker
from app.models.models import User, Asset, PriceCandle, Portfolio, Position

# Demo user
DEMO_USER_ID = "00000000-0000-0000-0000-000000000001"

# Sample TSE symbols
TSE_SEED = [
    ("فملی", "ملی صنایع مس ایران", "IRO1MSMI0001", "EQUITY", 28500, "فلزات اساسی", "کالایی"),
    ("خودرو", "ایران خودرو", "IRO1IKCO0001", "EQUITY", 4100, "خودرو و ساخت قطعات", "صنعتی"),
    ("شستا", "سرمایه‌گذاری تامین اجتماعی", "IRO1SHTA0001", "EQUITY", 1950, "سرمایه‌گذاری‌ها", "مالی"),
    ("وبملت", "بانک ملت", "IRO1BMLT0001", "EQUITY", 6800, "بانک‌ها", "مالی"),
    ("فولاد", "فولاد مبارکه اصفهان", "IRO1FOLD0001", "EQUITY", 17200, "فلزات اساسی", "کالایی"),
]

N_DAYS = 90


def _build_candles(base_price: float):
    """Generate a simple daily OHLCV random walk using stdlib random."""
    candles = []
    price = base_price
    today = datetime.utcnow().date()
    rng = random.Random(1403)

    for i in range(N_DAYS):
        day = today - timedelta(days=(N_DAYS - 1 - i))
        ret = rng.gauss(0.0008, 0.018)
        open_p = price
        close_p = max(10.0, open_p * (1 + ret))
        high_p = max(open_p, close_p) * (1 + abs(rng.gauss(0, 0.006)))
        low_p = min(open_p, close_p) * (1 - abs(rng.gauss(0, 0.006)))
        volume = int(rng.gauss(5_000_000, 1_500_000))
        turnover = float(close_p * volume)

        candles.append({
            "timestamp": datetime(day.year, day.month, day.day, 12, 30),
            "open": round(open_p, 2),
            "high": round(high_p, 2),
            "low": round(low_p, 2),
            "close": round(close_p, 2),
            "volume": max(volume, 0),
            "turnover": round(turnover, 2),
            "transactions": int(rng.gauss(12000, 3000)),
        })
        price = close_p
    return candles


async def seed_user(session: AsyncSession):
    stmt = pg_insert(User).values(
        id=DEMO_USER_ID,
        username="demo",
        email="demo@bedaanwaves.local",
        hashed_password="$2b$12$demo_hash_not_real",
        full_name="Demo User",
        is_active=True,
        is_admin=True,
        preferred_language="fa",
        theme="light",
        notifications_enabled=True,
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=["id"],
        set_={
            "email": stmt.excluded.email,
            "full_name": stmt.excluded.full_name,
            "updated_at": datetime.utcnow(),
        },
    )
    await session.execute(stmt)


async def seed_assets(session: AsyncSession):
    for symbol, name, isin, asset_class, base, industry, sector in TSE_SEED:
        stmt = pg_insert(Asset).values(
            symbol=symbol,
            name=name,
            isin_code=isin,
            market="TSE",
            asset_class=asset_class,
            currency="IRR",
            active=True,
            industry=industry,
            sector=sector,
            meta={"source": "SEED"},
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["symbol"],
            set_={
                "name": stmt.excluded.name,
                "isin_code": stmt.excluded.isin_code,
                "industry": stmt.excluded.industry,
                "sector": stmt.excluded.sector,
                "market": stmt.excluded.market,
                "asset_class": stmt.excluded.asset_class,
                "active": stmt.excluded.active,
                "updated_at": datetime.utcnow(),
            },
        )
        await session.execute(stmt)

    assets = (await session.execute(select(Asset))).scalars().all()
    return {a.symbol: a for a in assets}


async def seed_prices(session: AsyncSession, assets: dict):
    for symbol, asset in assets.items():
        for c in _build_candles(28500 if symbol == "فملی" else 4100 if symbol == "خودرو" else 1950):
            stmt = pg_insert(PriceCandle).values(
                asset_id=asset.id,
                timestamp=c["timestamp"],
                timeframe="1d",
                open=c["open"],
                high=c["high"],
                low=c["low"],
                close=c["close"],
                volume=c["volume"],
                turnover=c["turnover"],
                transactions=c["transactions"],
                source="SEED",
                data_quality="CONFIRMED",
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["asset_id", "timestamp", "timeframe"],
                set_={
                    "open": stmt.excluded.open,
                    "high": stmt.excluded.high,
                    "low": stmt.excluded.low,
                    "close": stmt.excluded.close,
                    "volume": stmt.excluded.volume,
                    "turnover": stmt.excluded.turnover,
                    "transactions": stmt.excluded.transactions,
                    "source": stmt.excluded.source,
                },
            )
            await session.execute(stmt)


async def seed_portfolio(session: AsyncSession, assets: dict):
    portfolio = Portfolio(
        user_id=DEMO_USER_ID,
        name=" نمونه اولیه",
        description="نمونه اولیه برای توسعه",
        portfolio_type="PERSONAL",
        base_currency="IRR",
    )
    session.add(portfolio)
    await session.flush()

    rng = random.Random(1403)
    for idx, (symbol, asset) in enumerate(assets.items()):
        base_prices = [28500, 4100, 1950, 6800, 17200]
        entry_price = base_prices[idx % len(base_prices)] + rng.gauss(0, 500)
        position = Position(
            portfolio_id=portfolio.id,
            asset_id=asset.id,
            quantity=100 + idx * 50,
            entry_price=round(entry_price, 2),
            entry_date=datetime.utcnow() - timedelta(days=30),
        )
        session.add(position)


async def main():
    async with async_session_maker() as session:
        await seed_user(session)
        await session.commit()

        assets = await seed_assets(session)
        await session.commit()

        await seed_prices(session, assets)
        await session.commit()

        await seed_portfolio(session, assets)
        await session.commit()

        print(f"SEEDED {len(assets)} assets, {len(assets) * N_DAYS} candles, 1 portfolio")


if __name__ == "__main__":
    asyncio.run(main())
