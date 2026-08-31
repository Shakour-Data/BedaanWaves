#!/usr/bin/env python
"""
populate_database.py
Populates all database tables with realistic synthetic data.

Fixes: Uses correct model names from app.models.models
"""

import asyncio
import os
import sys
from datetime import timezone, datetime, timedelta, date
from decimal import Decimal
import random
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.base import get_async_session
from app.models.models import (
    Base,
    Asset,
    RawMarketData,
    MarketDataSnapshot,
    CryptoPriceCandle,
    IntlPriceCandle,
    FinancialStatement,
    News,
    NewsSentiment,
    Portfolio,
    Position,
    Alert,
    MLSignal,
    APILog,
    User,
)
from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert as pg_insert


async def populate_database():
    """Populates the entire database with realistic synthetic data."""

    print("Starting database population...")

    async for session in get_async_session():
        try:
            # Check if we already have data
            asset_count = await session.execute(select(func.count()).select_from(Asset))
            count = asset_count.scalar()
            print(f"Existing assets: {count}")

            if count > 0:
                from sqlalchemy import text
                await session.execute(text("DELETE FROM raw_market_data"))
                await session.execute(text("DELETE FROM market_data_snapshots"))
                await session.execute(text("DELETE FROM news_sentiment"))
                await session.execute(text("DELETE FROM news_summaries"))
                await session.execute(text("DELETE FROM news"))
                await session.execute(text("DELETE FROM financial_statements"))
                await session.execute(text("DELETE FROM ml_signals"))
                await session.execute(text("DELETE FROM crypto_price_candles"))
                await session.execute(text("DELETE FROM intl_price_candles"))
                await session.execute(text("DELETE FROM price_candles"))
                print("Cleared existing data tables")

            # Get all assets
            result = await session.execute(select(Asset))
            assets = result.scalars().all()

            if not assets:
                print("No assets found. Creating sample assets...")
                await create_sample_assets(session)
                result = await session.execute(select(Asset))
                assets = result.scalars().all()

            print(f"Working with {len(assets)} assets")

            # Calculate 3-year date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365 * 3)
            total_days = (end_date - start_date).days
            print(f"Date range: {start_date.date()} to {end_date.date()} ({total_days} days)")

            # Populate price candles
            await populate_price_candles(session, assets, start_date, end_date)

            # Populate raw market data
            await populate_raw_market_data(session, assets, start_date, end_date)

            # Populate market snapshots
            await populate_market_snapshots(session, assets, start_date, end_date)

            # Populate financial statements
            await populate_financial_statements(session, assets)

            # Populate news articles
            await populate_news_articles(session, assets, start_date, end_date)

            # Populate ML signals
            await populate_ml_signals(session, assets)

            # Populate other supporting tables
            await populate_other_tables(session, assets)

            await session.commit()
            print("Database population completed successfully!")

            await print_final_counts(session)

        except Exception as e:
            print(f"Error during population: {e}")
            import traceback
            traceback.print_exc()
            await session.rollback()

        break


async def create_sample_assets(session):
    """Creates sample assets if none exist."""
    crypto_symbols = [
        ("BTCUSD", "Bitcoin", "CRYPTO", "BINANCE"),
        ("ETHUSD", "Ethereum", "CRYPTO", "BINANCE"),
        ("ADAUSD", "Cardano", "CRYPTO", "BINANCE"),
        ("XRPUSD", "XRP", "CRYPTO", "BINANCE"),
        ("DOGEUSD", "Dogecoin", "CRYPTO", "BINANCE"),
    ]

    intl_symbols = [
        ("AAPL", "Apple Inc.", "EQUITY", "NASDAQ"),
        ("GOOGL", "Google LLC", "EQUITY", "NASDAQ"),
        ("MSFT", "Microsoft Corp", "EQUITY", "NASDAQ"),
        ("TSLA", "Tesla Inc.", "EQUITY", "NASDAQ"),
        ("AMZN", "Amazon.com Inc.", "EQUITY", "NASDAQ"),
        ("JPM", "JPMorgan Chase", "EQUITY", "NYSE"),
    ]

    all_symbols = crypto_symbols + intl_symbols

    for symbol, name, asset_class, market in all_symbols:
        asset = Asset(
            symbol=symbol,
            name=name,
            asset_class=asset_class,
            market=market,
            country_code="US" if market in ("NASDAQ", "NYSE") else "GLOBAL",
            currency="USD" if market in ("NASDAQ", "NYSE") else "USD",
            active=True,
            metadata={},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        session.add(asset)

    await session.flush()
    print(f"Created {len(all_symbols)} sample assets")


async def populate_price_candles(session, assets, start_date, end_date):
    """Populates price candles for all assets over 3 years."""

    total_records = 0
    batch_size = 1000

    for asset in assets:
        market = asset.market
        if market in ("NASDAQ", "NYSE"):
            CandleModel = IntlPriceCandle
            main_table = "intl_price_candles"
        elif market in ("BINANCE", "KRAKEN", "COINBASE"):
            CandleModel = CryptoPriceCandle
            main_table = "crypto_price_candles"
        else:
            CandleModel = None
            main_table = "price_candles"

        if CandleModel is None:
            continue

        current_date = start_date
        price = random.uniform(100, 5000)

        candles = []

        while current_date <= end_date:
            volatility = 0.02
            change_percent = random.gauss(0, volatility)
            change_amount = price * change_percent

            new_price = price + change_amount
            new_price = max(new_price, 1.0)

            open_price = price
            close_price = new_price
            high_price = max(open_price, close_price) * (1 + random.random() * 0.01)
            low_price = min(open_price, close_price) * (1 - random.random() * 0.01)
            volume = max(100, int(new_price * 100 * random.uniform(0.5, 2.0)))

            candle = CandleModel(
                asset_id=asset.id,
                timeframe="1d",
                timestamp=current_date,
                open=Decimal(str(round(open_price, 2))),
                high=Decimal(str(round(high_price, 2))),
                low=Decimal(str(round(low_price, 2))),
                close=Decimal(str(round(close_price, 2))),
                volume=Decimal(volume),
                turnover=Decimal(str(round(volume * close_price, 2))),
                transactions=random.randint(100, 1000)
            )
            candles.append(candle)

            if len(candles) >= batch_size:
                await session.execute(
                    pg_insert(CandleModel).values([
                        {
                            "asset_id": c.asset_id,
                            "timeframe": c.timeframe,
                            "timestamp": c.timestamp,
                            "open": c.open,
                            "high": c.high,
                            "low": c.low,
                            "close": c.close,
                            "volume": c.volume,
                            "turnover": c.turnover,
                            "transactions": c.transactions
                        } for c in candles
                    ]).on_conflict_do_nothing()
                )
                await session.flush()
                total_records += len(candles)
                candles = []

            price = close_price
            current_date += timedelta(days=1)

        if market in ("BINANCE", "KRAKEN", "COINBASE") and candles:
            await session.execute(
                pg_insert(CandleModel).values([
                    {
                        "asset_id": c.asset_id,
                        "timeframe": c.timeframe,
                        "timestamp": c.timestamp,
                        "open": c.open,
                        "high": c.high,
                        "low": c.low,
                        "close": c.close,
                        "volume": c.volume,
                        "turnover": c.turnover,
                        "transactions": c.transactions
                    } for c in candles
                ]).on_conflict_do_nothing()
            )
            await session.flush()
            total_records += len(candles)

        if (assets.index(asset) + 1) % 5 == 0:
            print(f"Candles populated for {len(assets[:assets.index(asset)+1])} assets...")

    print(f"Total price candles inserted: {total_records}")


async def populate_raw_market_data(session, assets, start_date, end_date):
    """Populates raw market data records."""

    total_records = 0
    current_time = start_date

    while current_time <= end_date:
        for asset in assets:
            raw_data = RawMarketData(
                asset_id=asset.id,
                timestamp=current_time,
                source="simulation",
                data={
                    "price": str(round(random.uniform(50, 1000), 2)),
                    "bid": str(round(random.uniform(49, 999), 2)),
                    "ask": str(round(random.uniform(51, 1001), 2)),
                    "volume": str(random.randint(100, 10000)),
                    "spread": str(round(random.uniform(0.01, 0.5), 2)),
                },
                raw_json={},
                processed=False,
            )
            session.add(raw_data)
            total_records += 1

        if total_records % 5000 == 0:
            await session.flush()
            print(f"Raw market data: {total_records} records inserted...")

        current_time += timedelta(minutes=15)

    await session.flush()
    print(f"Total raw market data records: {total_records}")


async def populate_market_snapshots(session, assets, start_date, end_date):
    """Populates processed market data snapshots."""

    total_records = 0
    current_date = start_date

    while current_date <= end_date:
        if current_date.weekday() < 5:
            for asset in assets[:15]:
                snapshot = MarketDataSnapshot(
                    asset_id=asset.id,
                    timeframe="1d",
                    timestamp=current_date,
                    open_price=Decimal(str(round(random.uniform(100, 5000), 2))),
                    high_price=Decimal(str(round(random.uniform(100, 5200), 2))),
                    low_price=Decimal(str(round(random.uniform(95, 5000), 2))),
                    close_price=Decimal(str(round(random.uniform(100, 5000), 2))),
                    volume=Decimal(random.randint(100000, 10000000)),
                    adjusted_close=Decimal(str(round(random.uniform(100, 5000), 2))),
                )
                session.add(snapshot)
                total_records += 1

                snapshot.indicators = {
                    "rsi": round(random.uniform(20, 80), 2),
                    "macd": round(random.uniform(-5, 5), 4),
                    "bb_upper": round(random.uniform(105, 110), 2),
                    "bb_lower": round(random.uniform(90, 95), 2),
                }

        if total_records % 1000 == 0:
            await session.flush()
            print(f"Market snapshots: {total_records} records inserted...")

        current_date += timedelta(days=1)

    await session.flush()
    print(f"Total market snapshots inserted: {total_records}")


async def populate_financial_statements(session, assets):
    """Populates financial statement data for assets."""

    total_records = 0

    for asset in assets:
        for i in range(3):
            year = datetime.now().year - i

            balance_sheet = FinancialStatement(
                asset_id=asset.id,
                market=asset.market,
                statement_type="balance_sheet",
                period=f"{year}-annual",
                fiscal_year=year,
                as_of=date(year, 12, 31),
                data={
                    "revenue": str(round(random.uniform(50000000, 5000000000), 2)),
                    "net_income": str(round(random.uniform(1000000, 1000000000), 2)),
                    "total_assets": str(round(random.uniform(100000000, 5000000000), 2)),
                    "total_liabilities": str(round(random.uniform(50000000, 3000000000), 2)),
                    "shareholders_equity": str(round(random.uniform(100000000, 2000000000), 2)),
                    "cash": str(round(random.uniform(1000000, 1000000000), 2)),
                    "debt": str(round(random.uniform(1000000, 2000000000), 2)),
                },
            )
            session.add(balance_sheet)
            total_records += 1

            income_statement = FinancialStatement(
                asset_id=asset.id,
                market=asset.market,
                statement_type="income_statement",
                period=f"{year}-annual",
                fiscal_year=year,
                as_of=date(year, 12, 31),
                data={
                    "revenue": str(round(random.uniform(50000000, 5000000000), 2)),
                    "gross_profit": str(round(random.uniform(20000000, 2000000000), 2)),
                    "operating_expense": str(round(random.uniform(10000000, 1000000000), 2)),
                    "operating_income": str(round(random.uniform(10000000, 1000000000), 2)),
                    "net_income": str(round(random.uniform(1000000, 1000000000), 2)),
                    "eps_basic": str(round(random.uniform(0.10, 10.00), 2)),
                    "eps_diluted": str(round(random.uniform(0.10, 9.50), 2)),
                },
            )
            session.add(income_statement)
            total_records += 1

            cash_flow = FinancialStatement(
                asset_id=asset.id,
                market=asset.market,
                statement_type="cash_flow_statement",
                period=f"{year}-annual",
                fiscal_year=year,
                as_of=date(year, 12, 31),
                data={
                    "operating_cash_flow": str(round(random.uniform(5000000, 2000000000), 2)),
                    "investing_cash_flow": str(round(random.uniform(-1000000000, 500000000), 2)),
                    "financing_cash_flow": str(round(random.uniform(-500000000, 1000000000), 2)),
                    "free_cash_flow": str(round(random.uniform(1000000, 1000000000), 2)),
                },
            )
            session.add(cash_flow)
            total_records += 1

    await session.flush()
    print(f"Total financial statements inserted: {total_records}")


async def populate_news_articles(session, assets, start_date, end_date):
    """Populates news articles for assets."""

    total_records = 0
    total_sentiments = 0
    current_date = start_date
    batch = []

    news_headlines = {
        "positive": [
            "Earnings beat expectations",
            "New product launch announced",
            "Strategic partnership formed",
            "Market expansion confirmed",
            "Regulatory approval granted"
        ],
        "negative": [
            "Earnings miss forecasts",
            "Product recall announced",
            "Regulatory investigation opened",
            "Market share declining",
            "Leadership transition announced"
        ],
        "neutral": [
            "Quarterly earnings reported",
            "Annual shareholder meeting held",
            "Board composition updated",
            "Office relocation announced",
            "New hire in executive team"
        ]
    }

    while current_date <= end_date:
        for _ in range(random.randint(1, 3)):
            asset = random.choice(assets)
            sentiment = random.choice(["positive", "negative", "neutral"])
            headline = random.choice(news_headlines[sentiment])

            news = News(
                asset_id=asset.id,
                title=headline,
                body=f"Lorem ipsum dolor sit amet, consectetur adipiscing elit. {headline.lower()} for {asset.symbol}.",
                url="https://example-news-source.com/news/" + str(uuid.uuid4()),
                source="synthetic-news-service",
                published_at=current_date + timedelta(hours=random.randint(8, 17)),
                language="en",
            )
            batch.append((news, sentiment))
            total_records += 1

        if total_records % 1000 == 0 and total_records > 0:
            for news, _ in batch:
                session.add(news)
            await session.flush()
            for news, sentiment in batch:
                if sentiment == "positive":
                    score = round(random.uniform(0.5, 1.0), 2)
                elif sentiment == "negative":
                    score = round(random.uniform(0.0, 0.5), 2)
                else:
                    score = round(random.uniform(0.4, 0.6), 2)
                sentiment_record = NewsSentiment(
                    news_id=news.id,
                    asset_id=news.asset_id,
                    sentiment_label=sentiment.upper(),
                    sentiment_score=Decimal(str(score)),
                    model_version="populate-v1",
                )
                session.add(sentiment_record)
                total_sentiments += 1
            await session.flush()
            print(f"News articles: {total_records} records inserted, {total_sentiments} sentiments...")
            batch = []

        current_date += timedelta(days=1)

    if batch:
        for news, _ in batch:
            session.add(news)
        await session.flush()
        for news, sentiment in batch:
            if sentiment == "positive":
                score = round(random.uniform(0.5, 1.0), 2)
            elif sentiment == "negative":
                score = round(random.uniform(0.0, 0.5), 2)
            else:
                score = round(random.uniform(0.4, 0.6), 2)
            sentiment_record = NewsSentiment(
                news_id=news.id,
                asset_id=news.asset_id,
                sentiment_label=sentiment.upper(),
                sentiment_score=Decimal(str(score)),
                model_version="populate-v1",
            )
            session.add(sentiment_record)
            total_sentiments += 1
        await session.flush()

    print(f"Total news articles inserted: {total_records}")
    print(f"Total news sentiments inserted: {total_sentiments}")


async def populate_ml_signals(session, assets):
    """Populates ML prediction signals for assets."""

    total_records = 0

    for asset in assets:
        for i in range(30):
            timestamp = datetime.now(timezone.utc) - timedelta(days=i)

            ml_signal = MLSignal(
                asset_id=asset.id,
                timestamp=timestamp,
                model_name="LSTM-Predictor-v1",
                signal_type="prediction",
                confidence=Decimal(str(round(random.uniform(0.4, 0.95), 4))),
                predicted_price=Decimal(str(round(random.uniform(100, 5000), 2))),
                actual_price=Decimal(str(round(random.uniform(100, 5000), 2))),
                direction=random.choice(["up", "down", "neutral"]),
                features_used={
                    "rsi": round(random.uniform(20, 80), 2),
                    "macd": round(random.uniform(-2, 2), 4),
                    "volume_ma": round(random.uniform(50000, 500000), 2),
                    "price_volatility": round(random.uniform(0.01, 0.05), 4),
                },
                raw_output=str({
                    "predictions": [round(random.uniform(100, 5000), 2) for _ in range(5)],
                    "uncertainty": round(random.uniform(0.05, 0.20), 4)
                })
            )
            session.add(ml_signal)
            total_records += 1

    await session.flush()
    print(f"Total ML signals inserted: {total_records}")


async def populate_other_tables(session, assets):
    """Populates other supporting tables."""

    for _ in range(50):
        asset = random.choice(assets)
        alert_type = random.choice(["price_above", "price_below", "volume_spike", "news_sentiment"])
        session.add(Alert(
            asset_id=asset.id,
            user_id=1,
            alert_type=alert_type,
            condition_value=Decimal(str(round(random.uniform(50, 2000), 2))),
            triggered=False,
            created_at=datetime.now(timezone.utc) - timedelta(days=random.randint(0, 365)),
        ))

    user_count = await session.execute(select(func.count()).select_from(User))
    if user_count.scalar() == 0:
        for i in range(5):
            session.add(User(
                email=f"user{i+1}@example.com",
                hashed_password="fake_hashed_password_" + str(i+1),
                full_name=f"Test User {i+1}",
                is_active=True,
                is_superuser=False,
                created_at=datetime.now(timezone.utc),
            ))

    portfolio_count = await session.execute(select(func.count()).select_from(Portfolio))
    if portfolio_count.scalar() == 0:
        for i in range(3):
            portfolio = Portfolio(
                user_id=1,
                name=f"Portfolio {i+1}",
                description="Sample portfolio for testing",
                cash_balance=Decimal(str(round(random.uniform(10000, 100000), 2))),
                currency="USD",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            session.add(portfolio)
            await session.flush()

            for j in range(random.randint(3, 8)):
                asset = random.choice(assets)
                session.add(Position(
                    portfolio_id=portfolio.id,
                    asset_id=asset.id,
                    quantity=Decimal(str(round(random.uniform(10, 1000), 4))),
                    avg_cost=Decimal(str(round(random.uniform(50, 1500), 2))),
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                ))

    await session.flush()
    print("Other tables populated: alerts, users, portfolios, positions")


async def print_final_counts(session):
    """Prints final statistics of the database."""

    tables_to_check = [
        ("assets", Asset),
        ("intl_price_candles", IntlPriceCandle),
        ("crypto_price_candles", CryptoPriceCandle),
        ("raw_market_data", RawMarketData),
        ("market_data_snapshots", MarketDataSnapshot),
        ("news", News),
        ("financial_statements", FinancialStatement),
        ("ml_signals", MLSignal),
        ("alerts", Alert),
        ("portfolios", Portfolio),
        ("positions", Position),
        ("users", User),
    ]

    print("\n=== DATABASE POPULATION SUMMARY ===")
    for table_name, model in tables_to_check:
        try:
            count = await session.execute(select(func.count()).select_from(model))
            total = count.scalar()
            print(f"  {table_name}: {total:,} records")
        except Exception as e:
            print(f"  {table_name}: Error counting - {e}")

    print("\nDatabase population completed successfully!")


if __name__ == "__main__":
    asyncio.run(populate_database())
