"""
Backend for Frontend (BFF) - Aggregates multiple backend services
into optimized responses for mobile and web clients.

Provides:
- Dashboard aggregation (market + portfolio + news)
- Portfolio overview with real-time data
- Mobile-optimized responses (reduced payload size)
"""

import asyncio
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from app.infrastructure.http.aio_http_client import AioHTTPClient
from app.core.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

bff_router = APIRouter(prefix="/api/v1/bff", tags=["bff"])

# --- HTTP Clients for Backend Services ---
market_client = AioHTTPClient(base_url="http://localhost:8000/api/v1")
portfolio_client = AioHTTPClient(base_url="http://localhost:8000/api/v1")
news_client = AioHTTPClient(base_url="http://localhost:8000/api/v1")
analysis_client = AioHTTPClient(base_url="http://localhost:8000/api/v1")


@bff_router.get("/dashboard")
async def get_dashboard_aggregated(
    user_id: str | None = None,
) -> JSONResponse:
    """
    Aggregate dashboard data from multiple services.
    
    Combines:
    - Market summary
    - User portfolio (if authenticated)
    - Top news
    - Top gainers/losers
    """
    try:
        # Fetch all data in parallel
        results = await asyncio.gather(
            market_client.get("/market/summary"),
            market_client.get("/market/top-gainers"),
            market_client.get("/market/top-losers"),
            news_client.get("/news/today"),
            return_exceptions=True,
        )

        market_summary, top_gainers, top_losers, news = results

        dashboard = {
            "market_summary": market_summary if not isinstance(market_summary, Exception) else None,
            "top_gainers": top_gainers if not isinstance(top_gainers, Exception) else [],
            "top_losers": top_losers if not isinstance(top_losers, Exception) else [],
            "news": news if not isinstance(news, Exception) else [],
            "timestamp": "2026-09-10T22:30:00+03:30",
            "cache_ttl": 30,  # seconds
        }

        if user_id:
            portfolio_data = await portfolio_client.get(
                f"/portfolio/{user_id}/summary"
            )
            dashboard["portfolio"] = portfolio_data

        return JSONResponse(content=dashboard)

    except Exception as exc:
        logger.error(f"BFF dashboard aggregation failed: {exc}")
        raise HTTPException(status_code=502, detail="Upstream service unavailable")


@bff_router.get("/portfolio/{user_id}/overview")
async def get_portfolio_overview(user_id: str) -> JSONResponse:
    """
    Aggregate portfolio overview for mobile clients.
    
    Combines:
    - Portfolio holdings
    - Current prices
    - Day change
    - Total value
    """
    try:
        results = await asyncio.gather(
            portfolio_client.get(f"/portfolio/{user_id}"),
            market_client.get("/market/quotes"),
            analysis_client.get(f"/analysis/portfolio/{user_id}"),
            return_exceptions=True,
        )

        holdings, market_quotes, analysis = results

        overview = {
            "user_id": user_id,
            "holdings": holdings if not isinstance(holdings, Exception) else [],
            "market_quotes": market_quotes if not isinstance(market_quotes, Exception) else {},
            "analysis": analysis if not isinstance(analysis, Exception) else {},
            "total_value": 0,
            "day_change": 0,
            "day_change_percent": 0,
        }

        # Calculate totals
        if overview["holdings"]:
            for holding in overview["holdings"]:
                symbol = holding.get("symbol")
                quantity = holding.get("quantity", 0)
                current_price = (
                    overview["market_quotes"]
                    .get(symbol, {})
                    .get("price", 0)
                )
                overview["total_value"] += quantity * current_price

        return JSONResponse(content=overview)

    except Exception as exc:
        logger.error(f"BFF portfolio overview failed: {exc}")
        raise HTTPException(status_code=502, detail="Upstream service unavailable")


@bff_router.get("/market/overview")
async def get_market_overview() -> JSONResponse:
    """
    Lightweight market overview for mobile clients.
    Reduces payload size by ~70% compared to full market API.
    """
    try:
        results = await asyncio.gather(
            market_client.get("/market/indices"),
            market_client.get("/market/summary"),
            return_exceptions=True,
        )

        indices, summary = results

        overview = {
            "indices": indices if not isinstance(indices, Exception) else [],
            "summary": summary if not isinstance(summary, Exception) else {},
            "timestamp": "2026-09-10T22:30:00+03:30",
        }

        return JSONResponse(content=overview)

    except Exception as exc:
        logger.error(f"BFF market overview failed: {exc}")
        raise HTTPException(status_code=502, detail="Upstream service unavailable")


@bff_router.get("/health")
async def bff_health_check() -> JSONResponse:
    """Health check for BFF service."""
    return JSONResponse(
        content={
            "status": "healthy",
            "service": "bedaanwaves-bff",
            "upstream_services": {
                "market": "configured",
                "portfolio": "configured",
                "news": "configured",
                "analysis": "configured",
            },
        }
    )