"""
Local TSE seeder - populates PostgreSQL with sample Tehran Stock Exchange data.

This is SYNTHETIC demo data for local development only (no API key required).
Every row is tagged market='TSE' to keep TSE data separate from crypto /
international feeds, per project requirements. Each symbol is assigned its
real Tehran Stock Exchange industry (گروه صنعت) and a macro sector.

Run:
    cd backend
    .\venv\Scripts\Activate.ps1
    python scripts/seed_local.py
"""

import asyncio
from datetime import datetime, timedelta, time

import jdatetime
import numpy as np
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.db.base import engine, async_session_maker
from app.models.models import Asset, PriceCandle

_MARKET_CLOSE = time(12, 30)

# (symbol, name, isin, asset_class, base_price, industry, sector)
# Industries use the canonical Tehran Stock Exchange (TSE) industry groups.
TSE_SEED = [
    ("فملی", "ملی صنایع مس ایران", "IRO1MSMI0001", "EQUITY", 28500, "فلزات اساسی", "کالایی"),
    ("خودرو", "ایران خودرو", "IRO1IKCO0001", "EQUITY", 4100, "خودرو و ساخت قطعات", "صنعتی"),
    ("شستا", "سرمایه‌گذاری تامین اجتماعی", "IRO1SHTA0001", "EQUITY", 1950, "سرمایه‌گذاری‌ها", "مالی"),
    ("وبملت", "بانک ملت", "IRO1BMLT0001", "EQUITY", 6800, "بانک‌ها", "مالی"),
    ("فولاد", "فولاد مبارکه اصفهان", "IRO1FOLD0001", "EQUITY", 17200, "فلزات اساسی", "کالایی"),
    ("پترول", "پتروشیمی ایران", "IRO1PETR0001", "EQUITY", 5200, "مواد شیمیایی", "کالایی"),
    ("شپنا", "پالایش نفت اصفهان", "IRO1MPNH0001", "EQUITY", 14500, "فرآورده‌های نفتی", "کالایی"),
    ("تاپیکو", "سرمایه‌گذاری تامین مواد اولیه", "IRO1TAPI0001", "EQUITY", 3300, "سرمایه‌گذاری‌ها", "مالی"),
    ("وبصادر", "بانک صادرات", "IRO1SADR0001", "EQUITY", 2950, "بانک‌ها", "مالی"),
    ("وغدیر", "سرمایه‌گذاری غدیر", "IRO1GHDR0001", "EQUITY", 4800, "سرمایه‌گذاری‌ها", "مالی"),
    ("کگل", "معدنی و صنعتی گل‌گهر", "IRO1GOLG0001", "EQUITY", 26400, "استخراج کانه‌های فلزی", "کالایی"),
    ("رمپنا", "گروه مپنا", "IRO1MAPN0001", "EQUITY", 11200, "تجهیزات و سیستم‌های برقی", "صنعتی"),
    ("شبندر", "پالایش نفت بندرعباس", "IRO1BNDR0001", "EQUITY", 16800, "فرآورده‌های نفتی", "کالایی"),
    ("فخوز", "فولاد خوزستان", "IRO1FKHZ0001", "EQUITY", 18500, "فلزات اساسی", "کالایی"),
    ("اخابر", "مخابرات ایران", "IRO1MOBT0001", "EQUITY", 8700, "ارتباطات", "زیرساختی"),
]

N_DAYS = 150
RNG = np.random.default_rng(1403)


def _build_candles(base_price: float):
    """Generate a plausible daily OHLCV random walk (IRR prices)."""
    candles = []
    price = base_price
    today = datetime.utcnow().date()
    for i in range(N_DAYS):
        day = today - timedelta(days=(N_DAYS - 1 - i))
        ret = RNG.normal(0.0008, 0.018)
        open_p = price
        close_p = max(10.0, open_p * (1 + ret))
        high_p = max(open_p, close_p) * (1 + abs(RNG.normal(0, 0.006)))
        low_p = min(open_p, close_p) * (1 - abs(RNG.normal(0, 0.006)))
        volume = int(RNG.normal(5_000_000, 1_500_000))
        turnover = float(close_p * volume)
        jalali = jdatetime.date.fromgregorian(
            year=day.year, month=day.month, day=day.day
        ).strftime("%Y-%m-%d")
        candles.append(
            {
                "date": jalali,
                "timestamp": datetime(day.year, day.month, day.day, _MARKET_CLOSE.hour, _MARKET_CLOSE.minute),
                "open": round(open_p, 2),
                "high": round(high_p, 2),
                "low": round(low_p, 2),
                "close": round(close_p, 2),
                "volume": max(volume, 0),
                "turnover": round(turnover, 2),
                "transactions": int(RNG.normal(12000, 3000)),
            }
        )
        price = close_p
    return candles


async def seed():
    async with async_session_maker() as session:
        total_assets = 0
        total_candles = 0
        for symbol, name, isin, asset_class, base, industry, sector in TSE_SEED:
            # Upsert asset (idempotent on symbol).
            asset_stmt = pg_insert(Asset).values(
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
            asset_stmt = asset_stmt.on_conflict_do_update(
                index_elements=["symbol"],
                set_={
                    "name": asset_stmt.excluded.name,
                    "isin_code": asset_stmt.excluded.isin_code,
                    "industry": asset_stmt.excluded.industry,
                    "sector": asset_stmt.excluded.sector,
                    "market": asset_stmt.excluded.market,
                    "asset_class": asset_stmt.excluded.asset_class,
                    "active": asset_stmt.excluded.active,
                    "updated_at": datetime.utcnow(),
                },
            )
            await session.execute(asset_stmt)
            await session.flush()

            result = await session.execute(
                select(Asset).where(Asset.symbol == symbol)
            )
            asset_id = result.scalars().first().id

            for c in _build_candles(base):
                candle_stmt = pg_insert(PriceCandle).values(
                    asset_id=asset_id,
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
                candle_stmt = candle_stmt.on_conflict_do_update(
                    index_elements=["asset_id", "timestamp", "timeframe"],
                    set_={
                        "open": candle_stmt.excluded.open,
                        "high": candle_stmt.excluded.high,
                        "low": candle_stmt.excluded.low,
                        "close": candle_stmt.excluded.close,
                        "volume": candle_stmt.excluded.volume,
                        "turnover": candle_stmt.excluded.turnover,
                        "transactions": candle_stmt.excluded.transactions,
                        "source": candle_stmt.excluded.source,
                    },
                )
                await session.execute(candle_stmt)
            total_assets += 1
            total_candles += N_DAYS
        await session.commit()
        print(f"SEEDED {total_assets} TSE assets and {total_candles} daily candles.")


async def main():
    await seed()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
