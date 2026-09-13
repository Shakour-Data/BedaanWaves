"""
Historical News Backfill Script

Backfills historical news for all active NASDAQ assets into the database.
Uses yfinance + MultiSourceNewsFetcher and classifies all news items.

Usage:
    python backfill_news.py --days 40
    python backfill_news.py --years 1
    python backfill_news.py --days 40 --batch-size 50
    python backfill_news.py --symbol AAPL --days 90

Run from project root or backend directory.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from datetime import UTC, datetime, timedelta
from typing import Any

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)
_BACKEND_DIR = os.path.join(_PROJECT_ROOT, "backend")

for _p in (_BACKEND_DIR, _PROJECT_ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from sqlalchemy import and_, select

from app.core.config import get_settings
from app.db.base import async_session_maker
from app.models.models import Asset, News
from app.services.news.continuous_news_ingestion_service import ContinuousNewsIngestionService
from app.services.news.news_classifier import NewsClassifier
from app.services.news.source_registry import DEFAULT_NEWS_SOURCES

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def get_active_assets(batch_size: int = 200) -> list[tuple[str, str]]:
    """Fetch active NASDAQ equity/ETF symbols from DB."""
    async with async_session_maker() as session:
        result = await session.execute(
            select(Asset.id, Asset.symbol, Asset.asset_class, Asset.market)
            .where(
                and_(
                    Asset.active,
                    Asset.market == "NASDAQ",
                    Asset.asset_class.in_(["EQUITY", "ETF"]),
                )
            )
            .limit(batch_size)
        )
        rows = result.all()
        return [(str(row.id), row.symbol) for row in rows]


async def backfill_symbol(
    symbol: str,
    asset_id: str,
    start: datetime,
    end: datetime,
    classifier: NewsClassifier,
    ingestion: ContinuousNewsIngestionService | None = None,
) -> int:
    """Backfill news for a single symbol using yfinance + multi-source fallback."""
    import yfinance as yf

    news_items: list[News] = []
    seen_urls: set[str] = set()

    try:
        ticker = yf.Ticker(symbol)
        raw_news = ticker.news or []

        for item in raw_news:
            published_str = item.get("published")
            published_dt = None
            if published_str:
                try:
                    published_dt = datetime.fromisoformat(
                        published_str.replace("Z", "+00:00")
                    ).replace(tzinfo=None)
                except (ValueError, TypeError):
                    published_dt = None

            if published_dt and not (start <= published_dt <= end):
                continue

            url = item.get("link", "")
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)

            title = item.get("title", "")
            body = item.get("summary", "")
            category, sub_category = await classifier.classify(title, body, "STOCK_MARKET")
            priority = ContinuousNewsIngestionService._determine_priority(title, category)
            is_market_moving = ContinuousNewsIngestionService._is_market_moving(title)

            news_items.append(
                News(
                    source=item.get("publisher", "yfinance"),
                    title=title[:512],
                    body=body[:4000] if body else None,
                    url=url,
                    published_at=published_dt,
                    asset_id=asset_id,
                    language="en",
                    category=category,
                    sub_category=sub_category,
                    region="US",
                    priority=priority,
                    is_market_moving=is_market_moving,
                )
            )
    except Exception as exc:
        logger.warning("yfinance backfill failed for %s: %s", symbol, exc)

    if not news_items and ingestion is not None:
        try:
            from app.services.data.multi_source_news_fetcher import MultiSourceNewsFetcher
            fetcher = MultiSourceNewsFetcher()
            await fetcher.initialize()
            raw_items = await fetcher.fetch_news_for_symbol(
                symbol=symbol,
                days=(end - start).days,
                asset_id=asset_id,
                language="en",
            )
            await fetcher.shutdown()
            for item in raw_items:
                url = item.url
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    title = item.title or ""
                    body = item.body or ""
                    category, sub_category = await classifier.classify(title, body, "STOCK_MARKET")
                    priority = ContinuousNewsIngestionService._determine_priority(title, category)
                    is_market_moving = ContinuousNewsIngestionService._is_market_moving(title)
                    item.category = category
                    item.sub_category = sub_category
                    item.region = "US"
                    item.priority = priority
                    item.is_market_moving = is_market_moving
                    news_items.append(item)
        except Exception as exc:
            logger.warning("Multi-source backfill failed for %s: %s", symbol, exc)

    if not news_items:
        return 0

    async with async_session_maker() as session:
        for item in news_items:
            existing = await session.execute(
                select(News.id).where(News.url == item.url)
            )
            if existing.scalar_one_or_none():
                continue
            session.add(item)
        await session.commit()

    return len(news_items)


async def run_backfill(
    days: int | None = None,
    years: int | None = None,
    batch_size: int = 50,
    symbols: list[str] | None = None,
) -> dict[str, Any]:
    """Run historical news backfill."""
    if days is None and years is None:
        days = 40
    if years is not None:
        days = years * 365

    end_date = datetime.now(UTC)
    start_date = end_date - timedelta(days=days)

    logger.info("Backfill window: %s to %s", start_date.isoformat(), end_date.isoformat())

    classifier = NewsClassifier()
    ingestion = ContinuousNewsIngestionService()
    await ingestion.initialize()

    try:
        if symbols:
            assets = [(f"symbol-{sym}", sym) for sym in symbols]
        else:
            assets = await get_active_assets(batch_size=batch_size)

        total_inserted = 0
        errors: list[str] = []

        semaphore = asyncio.Semaphore(10)

        async def process_one(asset_id: str, symbol: str) -> tuple[str, int]:
            async with semaphore:
                try:
                    inserted = await backfill_symbol(
                        symbol, asset_id, start_date, end_date, classifier, ingestion
                    )
                    return symbol, inserted
                except Exception as exc:
                    return symbol, -1

        tasks = [process_one(aid, sym) for aid, sym in assets]
        for coro in asyncio.as_completed(tasks):
            symbol, inserted = await coro
            if inserted < 0:
                errors.append(symbol)
                logger.error("Backfill error for %s", symbol)
            else:
                total_inserted += inserted
                logger.info("%s: inserted %d news items", symbol, inserted)

        return {
            "status": "completed",
            "window_days": days,
            "assets_processed": len(assets),
            "news_inserted": total_inserted,
            "errors": errors,
        }
    finally:
        await ingestion.shutdown()


def main() -> None:
    parser = argparse.ArgumentParser(description="Historical news backfill")
    parser.add_argument("--days", type=int, help="Number of days to backfill")
    parser.add_argument("--years", type=int, help="Number of years to backfill")
    parser.add_argument("--batch-size", type=int, default=50, help="Assets per batch")
    parser.add_argument("--symbol", action="append", help="Specific symbol(s) to backfill")
    args = parser.parse_args()

    result = asyncio.run(run_backfill(
        days=args.days,
        years=args.years,
        batch_size=args.batch_size,
        symbols=args.symbol,
    ))
    print(result)


if __name__ == "__main__":
    main()
