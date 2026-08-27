"""
Comprehensive Database Population Script (Synthetic 5-Year Dev/Test Data)
========================================================================
Generates realistic synthetic market data spanning 5 years (2021-08-27 → present):
  - Assets across TSE, NASDAQ, and Crypto markets
  - Price candles (OHLCV) in three tables: ir_price_candles, intl_price_candles, crypto_price_candles
  - Macroeconomic indicators
  - News articles
  - Financial statements and ratios
  - ML signals and predictions

Run:
    cd backend
    python scripts/populate_database.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import math
import random
import uuid
from datetime import datetime, timezone, timedelta, date
from decimal import Decimal

from sqlalchemy import delete, select, func
from app.db.base import async_session_maker
from app.models.models import (
    Asset,
    IRPriceCandle,
    IntlPriceCandle,
    CryptoPriceCandle,
    News,
    MacroIndicator,
    IRFinancialStatement,
    IRFundamentalRatio,
    MLSignal,
    MLPrediction,
    MLModel,
)

START_DATE = datetime(2021, 8, 27, tzinfo=timezone.utc)
END_DATE = datetime.now(timezone.utc)

BATCH_SIZE = 1000

# Base assets definition
ASSETS = [
    # Tehran Stock Exchange
    {"symbol": "KHC1", "name": "کاهید", "asset_class": "EQUITY", "market": "TSE",
     "country_code": "IR", "currency": "IRR", "sector": "Banks"},
    {"symbol": "FAZF1", "name": "فازف", "asset_class": "EQUITY", "market": "TSE",
     "country_code": "IR", "currency": "IRR", "sector": "Pharmaceuticals"},
    {"symbol": "KHOD1", "name": "خود", "asset_class": "EQUITY", "market": "TSE",
     "country_code": "IR", "currency": "IRR", "sector": "Automotive"},
    {"symbol": "MELL1", "name": "ملت", "asset_class": "EQUITY", "market": "TSE",
     "country_code": "IR", "currency": "IRR", "sector": "Banking"},
    {"symbol": "SHAH1", "name": "شهید", "asset_class": "EQUITY", "market": "TSE",
     "country_code": "IR", "currency": "IRR", "sector": "Construction"},
    # NASDAQ
    {"symbol": "AAPL", "name": "Apple Inc.", "asset_class": "EQUITY", "market": "NASDAQ",
     "country_code": "US", "currency": "USD", "sector": "Technology"},
    {"symbol": "GOOGL", "name": "Google LLC", "asset_class": "EQUITY", "market": "NASDAQ",
     "country_code": "US", "currency": "USD", "sector": "Technology"},
    {"symbol": "MSFT", "name": "Microsoft Corp", "asset_class": "EQUITY", "market": "NASDAQ",
     "country_code": "US", "currency": "USD", "sector": "Technology"},
    {"symbol": "TSLA", "name": "Tesla Inc.", "asset_class": "EQUITY", "market": "NASDAQ",
     "country_code": "US", "currency": "USD", "sector": "Automotive"},
    {"symbol": "AMZN", "name": "Amazon.com Inc.", "asset_class": "EQUITY", "market": "NASDAQ",
     "country_code": "US", "currency": "USD", "sector": "Technology"},
    {"symbol": "^IXIC", "name": "Nasdaq Composite", "asset_class": "INDEX", "market": "NASDAQ",
     "country_code": "US", "currency": "USD", "sector": "Index"},
    # Crypto
    {"symbol": "BTC-USD", "name": "Bitcoin", "asset_class": "CRYPTO", "market": "GLOBAL",
     "country_code": "US", "currency": "USD", "sector": "Cryptocurrency"},
    {"symbol": "ETH-USD", "name": "Ethereum", "asset_class": "CRYPTO", "market": "GLOBAL",
     "country_code": "US", "currency": "USD", "sector": "Cryptocurrency"},
    {"symbol": "SOL-USD", "name": "Solana", "asset_class": "CRYPTO", "market": "GLOBAL",
     "country_code": "US", "currency": "USD", "sector": "Cryptocurrency"},
    {"symbol": "ADA-USD", "name": "Cardano", "asset_class": "CRYPTO", "market": "GLOBAL",
     "country_code": "US", "currency": "USD", "sector": "Cryptocurrency"},
]

# Candle model mapping per market
MARKET_CANDLE_MODELS = {
    "TSE": IRPriceCandle,
    "NASDAQ": IntlPriceCandle,
    "GLOBAL": CryptoPriceCandle,
}

MACRO_INDICATORS = [
    {"indicator_code": "^GSPC", "name": "S&P 500", "unit": "Index"},
    {"indicator_code": "^VIX", "name": "VIX", "unit": "Percent"},
    {"indicator_code": "^TNX", "name": "10Y Treasury Yield", "unit": "Percent"},
    {"indicator_code": "DX-Y.NPB", "name": "USD Index", "unit": "Index"},
    {"indicator_code": "GC=F", "name": "Gold Futures", "unit": "USD/oz"},
    {"indicator_code": "CL=F", "name": "Crude Oil Futures", "unit": "USD/barrel"},
]

NEWS_SENTENCE_TEMPLATES = [
    "Market analysts observe a shift in {sector} dynamics following recent economic data.",
    "{company} announced quarterly results that exceeded expert forecasts.",
    "Institutional investors are rebalancing positions in the {sector} sector.",
    "Regulatory developments in {country} could impact {company}'s operations.",
    "Technical indicators suggest a potential trend reversal for {company}.",
    "Global macroeconomic factors are driving volatility in {sector}.",
    "{company} reported strong earnings growth driven by increased demand.",
    "Market sentiment improved after the latest policy announcement.",
    "Trading volumes rose significantly as investors react to earnings news.",
    "Analysts upgraded {company} citing improved fundamentals.",
]


def generate_synthetic_price(
    base_price: float, day_idx: int, volatility: float = 0.02,
    trend: float = 0.0002, seed: int = 42,
) -> tuple[float, float, float, float, int]:
    """Generate a single synthetic OHLCV candle."""
    rng = random.Random(seed + day_idx)
    # Geometric random walk with mild trend
    log_return = rng.gauss(trend, volatility)
    close_price = base_price * math.exp(log_return)
    # Generate OHLC within the day's range
    day_range = close_price * volatility * 1.5
    open_price = close_price + rng.gauss(0, day_range * 0.3)
    high_price = max(open_price, close_price) + rng.uniform(0, day_range * 0.5)
    low_price = min(open_price, close_price) - rng.uniform(0, day_range * 0.5)
    # Ensure low <= open, close <= high
    low_price = min(low_price, open_price, close_price)
    high_price = max(high_price, open_price, close_price)
    volume = max(1000, int(abs(close_price * 1000 * rng.gauss(1, 0.3))))
    # Update base price for next day
    new_base = close_price
    return float(open_price), float(high_price), float(low_price), float(close_price), volume, new_base


async def ensure_assets(session) -> dict[str, uuid.UUID]:
    """Create all base assets and return a {symbol: asset_id} mapping."""
    asset_ids: dict[str, uuid.UUID] = {}
    for asset_def in ASSETS:
        existing = await session.execute(
            select(Asset).where(Asset.symbol == asset_def["symbol"])
        )
        asset = existing.scalar_one_or_none()
        if asset is None:
            asset = Asset(
                symbol=asset_def["symbol"],
                name=asset_def["name"],
                asset_class=asset_def["asset_class"],
                market=asset_def["market"],
                sector=asset_def["sector"],
                country_code=asset_def["country_code"],
                currency=asset_def["currency"],
                active=True,
                meta={"source": "populate_database"},
            )
            session.add(asset)
            await session.flush()
        asset_ids[asset_def["symbol"]] = asset.id
    await session.commit()
    return asset_ids


def trading_days_between(start: datetime, end: datetime) -> int:
    """Count approximate trading days between two dates."""
    days = (end - start).days
    return max(int(days * 5 / 7), 1)


async def populate_candles(session) -> dict[str, int]:
    """Generate 5 years of synthetic OHLCV candles for all assets."""
    asset_ids = await ensure_assets(session)

    total_trading_days = trading_days_between(START_DATE, END_DATE)
    counts: dict[str, int] = {}

    for asset_def in ASSETS:
        symbol = asset_def["symbol"]
        market = asset_def["market"]
        candle_cls = MARKET_CANDLE_MODELS.get(market, IntlPriceCandle)
        asset_id = asset_ids[symbol]

        # Clear existing seed data for this asset
        await session.execute(
            delete(candle_cls).where(candle_cls.asset_id == asset_id)
        )
        await session.flush()

        # Base price varies by asset
        if market == "TSE":
            base_price = random.uniform(50000, 200000)  # IRR
        elif market == "CRYPTO":
            base_price = {
                "BTC-USD": 50000, "ETH-USD": 3500, "SOL-USD": 200, "ADA-USD": 0.5
            }.get(symbol, 1000)
        else:
            base_price = random.uniform(50, 300)

        volatility = 0.015 if market == "INDEX" else (0.035 if market == "CRYPTO" else 0.02)
        seed_val = random.randint(1, 10000)

        candles: list = []
        current_price = base_price
        current_date = START_DATE
        day_idx = 0

        while current_date <= END_DATE:
            # Skip weekends for stock markets (except crypto which trades 7/7)
            if market != "CRYPTO" and current_date.weekday() >= 5:
                current_date += timedelta(days=1)
                continue

            open_p, high_p, low_p, close_p, volume, current_price = generate_synthetic_price(
                current_price, day_idx, volatility=volatility, seed=seed_val
            )

            candle = candle_cls(
                asset_id=asset_id,
                timestamp=current_date.replace(tzinfo=None),
                timeframe="1d",
                open=Decimal(str(round(open_p, 8))),
                high=Decimal(str(round(high_p, 8))),
                low=Decimal(str(round(low_p, 8))),
                close=Decimal(str(round(close_p, 8))),
                volume=volume,
                turnover=Decimal(str(round(close_p * volume, 2))),
                source="populate_database",
                data_quality="CONFIRMED",
            )
            candles.append(candle)
            day_idx += 1
            current_date += timedelta(days=1)

            if len(candles) >= BATCH_SIZE:
                session.bulk_save_objects(candles)
                await session.flush()
                candles.clear()

        if candles:
            session.bulk_save_objects(candles)
            await session.flush()

        counts[symbol] = day_idx
        await session.commit()

    return counts


async def populate_macro_indicators(session) -> int:
    """Generate 5 years of synthetic macro indicators."""
    await session.execute(delete(MacroIndicator).where(MacroIndicator.source == "populate_database"))
    await session.flush()

    count = 0
    current = START_DATE
    while current <= END_DATE:
        for idx_def in MACRO_INDICATORS:
            base_val = {
                "^GSPC": 4500, "^VIX": 20, "^TNX": 2.5,
                "DX-Y.NPB": 93, "GC=F": 1800, "CL=F": 70,
            }.get(idx_def["indicator_code"], 100)

            rng = random.Random(hash(idx_def["indicator_code"] + str(current.date())))
            value = base_val * (1 + rng.gauss(0, 0.01))
            if rng.random() < 0.02 * (current - START_DATE).days / 365:
                # Occasional macro event spike
                value *= rng.uniform(1.1, 1.3) if rng.random() > 0.5 else rng.uniform(0.7, 0.9)

            indicator = MacroIndicator(
                indicator_code=idx_def["indicator_code"],
                name=idx_def["name"],
                value=Decimal(str(round(value, 6))),
                period=current.strftime("%Y-%m-%d"),
                unit=idx_def["unit"],
                source="populate_database",
                as_of=current.date(),
            )
            session.add(indicator)
            count += 1

        current += timedelta(days=1)

    await session.commit()
    return count


async def populate_news(session) -> int:
    """Generate synthetic news articles over the 5-year period."""
    asset_ids = await ensure_assets(session)
    await session.execute(delete(News).where(News.source == "populate_database"))
    await session.flush()

    # Use a subset of assets for news
    news_assets = list(asset_ids.items())[:10]
    rng = random.Random(12345)
    count = 0
    current_date = START_DATE

    while current_date <= END_DATE:
        # Generate ~2-5 news articles per day
        num_articles = rng.randint(2, 5)
        for _ in range(num_articles):
            symbol, asset_id = rng.choice(news_assets)
            asset = ASSETS[[a["symbol"] for a in ASSETS].index(symbol)]
            template = rng.choice(NEWS_SENTENCE_TEMPLATES)
            title = template.format(
                sector=asset["sector"] or "market",
                company=asset["name"],
                country="global",
            )
            body = f"{title} Full analysis available for {symbol} on {current_date.strftime('%Y-%m-%d')}."

            news = News(
                source="populate_database",
                title=title,
                body=body,
                url=f"https://example.com/news/{symbol}/{current_date.strftime('%Y%m%d')}/{uuid.uuid4().hex[:8]}",
                published_at=current_date.replace(
                    hour=rng.randint(8, 18),
                    minute=rng.randint(0, 59),
                    tzinfo=None,
                ),
                asset_id=asset_id,
                language="en" if asset["country_code"] == "US" else "fa",
            )
            session.add(news)
            count += 1

        current_date += timedelta(days=1)

        if count % 500 == 0:
            await session.flush()

    await session.commit()
    return count


async def populate_fundamentals(session) -> int:
    """Generate synthetic financial statements and ratios."""
    asset_ids = await ensure_assets(session)

    # Only generate for NASDAQ equities
    nasdaq_equities = [
        (sym, aid) for sym, aid in asset_ids.items()
        if any(a["symbol"] == sym and a["market"] == "NASDAQ" and a["asset_class"] == "EQUITY" for a in ASSETS)
    ]

    count = 0
    current_year = START_DATE.year
    end_year = END_DATE.year.year

    for symbol, asset_id in nasdaq_equities:
        for year in range(current_year, end_year + 1):
            for quarter in range(1, 5):
                period_end = date(year, quarter * 3, 1) if quarter < 4 else date(year, 12, 31)
                period_str = f"{year}Q{quarter}"

                rng = random.Random(hash(f"{symbol}{period_str}"))

                income_stmt = {
                    "revenue": str(round(rng.uniform(80e9, 350e9), 2)),
                    "gross_profit": str(round(rng.uniform(40e9, 180e9), 2)),
                    "operating_income": str(round(rng.uniform(20e9, 100e9), 2)),
                    "net_income": str(round(rng.uniform(15e9, 90e9), 2)),
                }
                stmt = IRFinancialStatement(
                    asset_id=asset_id,
                    market="NASDAQ",
                    period=period_str,
                    statement_type="INCOME",
                    fiscal_year=year,
                    data=income_stmt,
                    as_of=period_end,
                )
                session.add(stmt)
                count += 1

                balance_sheet = {
                    "total_assets": str(round(rng.uniform(200e9, 600e9), 2)),
                    "total_liabilities": str(round(rng.uniform(100e9, 300e9), 2)),
                    "shareholder_equity": str(round(rng.uniform(100e9, 300e9), 2)),
                }
                stmt_bs = IRFinancialStatement(
                    asset_id=asset_id,
                    market="NASDAQ",
                    period=period_str,
                    statement_type="BALANCE_SHEET",
                    fiscal_year=year,
                    data=balance_sheet,
                    as_of=period_end,
                )
                session.add(stmt_bs)

                # Fundamental ratio
                pe = round(rng.uniform(10, 40), 2)
                pb = round(rng.uniform(3, 15), 2)
                eps = round(rng.uniform(1.0, 10.0), 2)
                ratio = IRFundamentalRatio(
                    asset_id=asset_id,
                    market="NASDAQ",
                    period=period_str,
                    eps=Decimal(str(eps)),
                    pe=Decimal(str(pe)),
                    pb=Decimal(str(pb)),
                    roe=Decimal(str(round(rng.uniform(0.10, 0.35), 4))),
                    profit_margin=Decimal(str(round(rng.uniform(0.05, 0.25), 4))),
                    market_cap=Decimal(str(round(rng.uniform(500e9, 2000e9), 2))),
                    book_value=Decimal(str(round(rng.uniform(20, 150), 2))),
                )
                session.add(ratio)

    await session.commit()
    return count


async def populate_ml_signals(session) -> int:
    """Generate synthetic ML signals and predictions."""
    asset_ids = await ensure_assets(session)
    await session.execute(delete(MLPrediction).where(MLPrediction.model_version.like("populate_%")))
    await session.execute(delete(MLSignal).where(MLSignal.ml_model_version.like("populate_%")))
    await session.flush()

    # Insert MLModel if not exists
    model_existing = await session.execute(
        select(MLModel).where(
            MLModel.name == "SyntheticGenerator",
            MLModel.version == "populate_synthetic_v1",
        )
    )
    model = model_existing.scalar_one_or_none()
    if model is None:
        model = MLModel(
            name="SyntheticGenerator",
            version="populate_synthetic_v1",
            model_type="PREDICTION",
            metrics={"accuracy": 0.65, "sharpe": 1.5},
            is_active=True,
            description="Synthetic ML signals for development and testing",
        )
        session.add(model)
        await session.flush()

    rng = random.Random(999)
    count = 0
    signal_types = ["BUY", "SELL", "HOLD"]
    valid_until = datetime.now(timezone.utc) + timedelta(days=7)

    for asset_def in ASSETS:
        if asset_def["asset_class"] == "INDEX":
            continue
        asset_id = asset_ids[asset_def["symbol"]]
        for _ in range(12):
            signal_type = rng.choice(signal_types)
            confidence = round(rng.uniform(55, 90), 2)
            signal = MLSignal(
                asset_id=asset_id,
                signal_type=signal_type,
                confidence=Decimal(str(confidence)),
                expected_return=Decimal(str(round(rng.uniform(-0.05, 0.08), 4))),
                expected_volatility=Decimal(str(round(rng.uniform(0.02, 0.05), 4))),
                risk_score=Decimal(str(round(100 - confidence, 2))),
                reasoning=f"Synthetic signal from populate_database for {asset_def['symbol']}",
                technical_factors={
                    "rsi": round(rng.uniform(20, 80), 2),
                    "sma_20": round(rng.uniform(100, 200), 2),
                    "sma_50": round(rng.uniform(100, 200), 2),
                },
                fundamental_factors={},
                sentiment_factors={"news_sentiment": round(rng.uniform(-1, 1), 2)},
                ml_model_version="populate_synthetic_v1",
                model_name="SyntheticGenerator",
                model_confidence=Decimal(str(round(confidence * 0.9, 2))),
                valid_until=valid_until,
                is_active=True,
                win_rate=Decimal(str(round(rng.uniform(0.45, 0.75), 2))),
            )
            session.add(signal)
            count += 1

            predictions = [
                MLPrediction(
                    asset_id=asset_id,
                    model_id=model.id,
                    model_version="populate_synthetic_v1",
                    horizon="7d",
                    predicted_value=Decimal(str(round(rng.uniform(100, 500), 8))),
                    lower_bound=Decimal(str(round(rng.uniform(95, 475), 8))),
                    upper_bound=Decimal(str(round(rng.uniform(105, 525), 8))),
                    confidence=Decimal(str(round(confidence, 2))),
                    target_date=datetime.now(timezone.utc) + timedelta(days=7),
                ),
                MLPrediction(
                    asset_id=asset_id,
                    model_id=model.id,
                    model_version="populate_synthetic_v1",
                    horizon="30d",
                    predicted_value=Decimal(str(round(rng.uniform(100, 500), 8))),
                    lower_bound=Decimal(str(round(rng.uniform(90, 450), 8))),
                    upper_bound=Decimal(str(round(rng.uniform(110, 550), 8))),
                    confidence=Decimal(str(round(confidence * 0.9, 2))),
                    target_date=datetime.now(timezone.utc) + timedelta(days=30),
                ),
            ]
            session.bulk_save_objects(predictions)

    await session.commit()
    return count


async def main():
    async with async_session_maker() as session:
        print("=" * 60)
        print("POPULATING DATABASE WITH SYNTHETIC 5-YEAR DATA")
        print(f"  Period: {START_DATE.strftime('%Y-%m-%d')} → {END_DATE.strftime('%Y-%m-%d')}")
        print("=" * 60)

        print("\n--- Ensuring assets...")
        asset_ids = await ensure_assets(session)
        print(f"  Assets: {len(asset_ids)}")

        print("\n--- Generating price candles (5 years)...")
        candle_counts = await populate_candles(session)
        total_candles = sum(candle_counts.values())
        for sym, cnt in candle_counts.items():
            print(f"    {sym}: {cnt} candles")
        print(f"  Total candles: {total_candles}")

        print("\n--- Generating macro indicators (5 years)...")
        macro_count = await populate_macro_indicators(session)
        print(f"    Total macro records: {macro_count}")

        print("\n--- Generating news articles (5 years)...")
        news_count = await populate_news(session)
        print(f"    Total news articles: {news_count}")

        print("\n--- Generating financial statements & ratios...")
        fund_count = await populate_fundamentals(session)
        print(f"    Total fundamental records: {fund_count}")

        print("\n--- Generating ML signals & predictions...")
        ml_count = await populate_ml_signals(session)
        print(f"    Total ML signals: {ml_count}")

    print("\n" + "=" * 60)
    print("DATABASE POPULATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
