"""News Routes"""

import logging

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import desc, func, select

from app.db.base import async_session_maker
from app.models.models import Asset, News
from app.schemas.schemas import (
    NewsCategoryResponse,
    NewsCategoriesResponse,
    NewsMarketMovingResponse,
    NewsMarketResponse,
    NewsRegionsResponse,
    NewsSearchResponse,
    NewsTickerResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["news"])


def _news_to_dict(news: News) -> dict:
    return {
        "id": str(news.id),
        "source": news.source,
        "title": news.title,
        "body": news.body,
        "url": news.url,
        "published_at": news.published_at.isoformat() if news.published_at else None,
        "asset_id": str(news.asset_id) if news.asset_id else None,
        "language": news.language,
        "fetched_at": news.fetched_at.isoformat() if news.fetched_at else None,
        "category": news.category,
        "sub_category": news.sub_category,
        "region": news.region,
        "priority": news.priority,
        "is_market_moving": news.is_market_moving,
    }


@router.get("/market", response_model=NewsMarketResponse)
async def get_market_news(
    limit: int = Query(20, ge=1, le=100),
) -> dict:
    """Get market news."""
    from app.services.data.news_service import NewsService
    service = NewsService()
    await service.initialize()
    news = await service.get_market_news(limit)
    return {
        "status": "success",
        "count": len(news),
        "data": news,
    }


@router.get("/{ticker}", response_model=NewsTickerResponse)
async def get_stock_news(
    ticker: str,
    limit: int = Query(10, ge=1, le=100),
) -> dict:
    """Get news for a specific stock."""
    from app.services.data.news_service import NewsService
    service = NewsService()
    await service.initialize()
    news = await service.get_stock_news(ticker, limit)
    return {
        "status": "success",
        "ticker": ticker.upper(),
        "count": len(news),
        "data": news,
    }


@router.get("/search", response_model=NewsSearchResponse)
async def search_news(
    q: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=100),
) -> NewsSearchResponse:
    """Search news articles."""
    from app.services.data.news_service import NewsService
    service = NewsService()
    await service.initialize()
    results = await service.search_news(q, limit)
    return {
        "status": "success",
        "query": q,
        "count": len(results),
        "data": results,
    }


@router.get("/category/{category}", response_model=NewsCategoryResponse)
async def get_news_by_category(
    category: str,
    limit: int = Query(50, ge=1, le=200),
    region: str | None = Query(None),
    priority: str | None = Query(None),
    symbol: str | None = Query(None),
):
    """Get news filtered by domain category."""
    valid_categories = {
        "POLITICAL", "ECONOMIC", "INTERNATIONAL",
        "STOCK_MARKET", "INDUSTRY", "COMPANY",
    }
    if category.upper() not in valid_categories:
        raise HTTPException(422, f"Invalid category. Must be one of: {sorted(valid_categories)}")

    async with async_session_maker() as session:
        query = select(News).where(News.category == category.upper())

        if region:
            query = query.where(News.region == region.upper())
        if priority:
            query = query.where(News.priority == priority.upper())
        if symbol:
            query = query.join(Asset).where(Asset.symbol == symbol.upper())

        query = query.order_by(desc(News.published_at)).limit(limit)
        result = await session.execute(query)
        items = result.scalars().all()

        return {
            "status": "success",
            "category": category.upper(),
            "count": len(items),
            "data": [_news_to_dict(n) for n in items],
        }


@router.get("/categories", response_model=NewsCategoriesResponse)
async def get_news_categories():
    """Get available categories with counts."""
    async with async_session_maker() as session:
        result = await session.execute(
            select(News.category, func.count(News.id)).group_by(News.category)
        )
        counts = {row[0]: row[1] for row in result.all()}
        return {"status": "success", "categories": list(counts.keys()), "count": len(counts)}


@router.get("/regions", response_model=NewsRegionsResponse)
async def get_news_regions():
    """Get available regions with counts."""
    async with async_session_maker() as session:
        result = await session.execute(
            select(News.region, func.count(News.id)).group_by(News.region)
        )
        counts = {row[0] or "GLOBAL": row[1] for row in result.all()}
        return {"status": "success", "regions": list(counts.keys()), "count": len(counts)}


@router.get("/market-moving", response_model=NewsMarketMovingResponse)
async def get_market_moving_news(
    limit: int = Query(20, ge=1, le=100),
):
    """Get market-moving news only (is_market_moving=True)."""
    async with async_session_maker() as session:
        result = await session.execute(
            select(News).where(News.is_market_moving)
            .order_by(desc(News.published_at)).limit(limit)
        )
        items = result.scalars().all()
        return {
            "status": "success",
            "count": len(items),
            "data": [_news_to_dict(n) for n in items],
        }
