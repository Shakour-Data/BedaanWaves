"""News Routes"""

from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List
import logging

from app.services.data.news_service import NewsService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/news", tags=["news"])


@router.get("/market", response_model=dict)
async def get_market_news(
    limit: int = Query(20, ge=1, le=100),
) -> dict:
    """Get market news."""
    service = NewsService()
    await service.initialize()
    news = await service.get_market_news(limit)
    return {
        "status": "success",
        "count": len(news),
        "data": news,
    }


@router.get("/{ticker}", response_model=dict)
async def get_stock_news(
    ticker: str,
    limit: int = Query(10, ge=1, le=100),
) -> dict:
    """Get news for a specific stock."""
    service = NewsService()
    await service.initialize()
    news = await service.get_stock_news(ticker, limit)
    return {
        "status": "success",
        "ticker": ticker.upper(),
        "count": len(news),
        "data": news,
    }


@router.get("/search", response_model=dict)
async def search_news(
    q: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=100),
) -> dict:
    """Search news articles."""
    service = NewsService()
    await service.initialize()
    results = await service.search_news(q, limit)
    return {
        "status": "success",
        "query": q,
        "count": len(results),
        "data": results,
    }
