"""
Real-Time Market Data Routes

Provides live quotes, adjusted historical data, and intraday bars for NASDAQ equities.
All endpoints connect to live external APIs — no hardcoded or mock data.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime, timezone
from typing import Optional
import logging

from app.services.data.real_time_market_data_service import RealTimeMarketDataService
from app.services.data.market_hours_service import MarketHoursService
from app.schemas.schemas import (
    RealtimeQuoteResponse,
    HistoricalDataResponse,
    IntradayDataResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["market-data"])


def get_market_data_service() -> RealTimeMarketDataService:
    """Dependency factory for RealTimeMarketDataService."""
    from app.services.core.dependency_container import get_global_container
    container = get_global_container()
    service = container.get("real_time_market_data_service")
    if service is None:
        raise HTTPException(status_code=503, detail="Real-time market data service unavailable")
    return service


def get_market_hours_service() -> MarketHoursService:
    """Dependency factory for MarketHoursService."""
    return MarketHoursService()


@router.get("/quote/{symbol}", response_model=RealtimeQuoteResponse)
async def get_realtime_quote(
    symbol: str,
    service: RealTimeMarketDataService = Depends(get_market_data_service),
) -> RealtimeQuoteResponse:
    """
    Get the current real-time quote for a NASDAQ symbol.

    Returns current price, change %, volume, timestamp, and market status.
    adjusted_close is included for downstream analytical use.
    """
    try:
        return await service.get_realtime_quote(symbol)
    except Exception as exc:
        logger.error(f"Failed to fetch quote for {symbol}: {exc}")
        raise HTTPException(status_code=502, detail=str(exc))


@router.get("/history/{symbol}", response_model=HistoricalDataResponse)
async def get_adjusted_historical(
    symbol: str,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    interval: str = Query("1d", pattern="^(1m|2m|5m|15m|30m|60m|90m|1h|1d|5d|1wk|1mo|3mo)$"),
    service: RealTimeMarketDataService = Depends(get_market_data_service),
) -> HistoricalDataResponse:
    """
    Get adjusted OHLCV historical data for a symbol.

    All candles include adjusted_close for analytical calculations.
    """
    try:
        return await service.get_adjusted_historical(symbol, start_date, end_date, interval)
    except Exception as exc:
        logger.error(f"Failed to fetch history for {symbol}: {exc}")
        raise HTTPException(status_code=502, detail=str(exc))


@router.get("/intraday/{symbol}", response_model=IntradayDataResponse)
async def get_intraday(
    symbol: str,
    interval: str = Query("5m", pattern="^(1m|2m|5m|15m|30m|60m|90m|1h)$"),
    service: RealTimeMarketDataService = Depends(get_market_data_service),
) -> IntradayDataResponse:
    """
    Get intraday OHLCV bars for the current trading session.

    Returns the most recent intraday bars with adjusted_close.
    """
    try:
        return await service.get_intraday(symbol, interval)
    except Exception as exc:
        logger.error(f"Failed to fetch intraday for {symbol}: {exc}")
        raise HTTPException(status_code=502, detail=str(exc))


@router.get("/market-status", response_model=dict)
async def get_market_status(
    market_hours: MarketHoursService = Depends(get_market_hours_service),
) -> dict:
    """
    Get current NASDAQ market status and freshness label.

    Returns whether the market is in pre-market, regular, after-hours, or closed.
    """
    status = market_hours.get_market_status()
    return {
        "status": "success",
        "data": status,
    }
