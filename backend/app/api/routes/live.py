"""
Live Market Data Routes

Market data streaming endpoints.
"""
import logging
from typing import Any

from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(tags=["market-live"])


async def _not_available() -> Any:
    raise HTTPException(
        status_code=501,
        detail="Live streaming endpoints are not available. "
               "NASDAQ data is available via /api/v1/market/* endpoints.",
    )


@router.get("/symbols", summary="All real-time symbols")
async def live_symbols() -> Any:
    return await _not_available()


@router.get("/symbol/{l18}", summary="Comprehensive real-time data for one symbol")
async def live_symbol(l18: str) -> Any:
    return await _not_available()


@router.get("/candlestick/{l18}", summary="Candles")
async def live_candlestick(l18: str) -> Any:
    return await _not_available()


@router.get("/history/{l18}", summary="Daily price & trade history")
async def live_history(l18: str) -> Any:
    return await _not_available()


@router.get("/option/{l18}", summary="Option data")
async def live_option(l18: str) -> Any:
    return await _not_available()


@router.get("/realtime/{l18}", summary="Realtime price")
async def live_realtime(l18: str) -> Any:
    return await _not_available()