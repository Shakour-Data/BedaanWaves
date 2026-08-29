"""
Live Market Data Routes

TSE/BRS-specific streaming endpoints have been removed. The ``get_brs_client``
dependency is preserved for backward compatibility with stocks.py / history.py
routes but is deprecated.
"""
import logging
from typing import Any

from fastapi import APIRouter, HTTPException

from app.services.data.brs_api_client import BrsApiClient

logger = logging.getLogger(__name__)

router = APIRouter(tags=["market-live"])

_client: BrsApiClient | None = None
_client_initialized = False


async def get_brs_client() -> BrsApiClient:
    """Return the singleton BRS client (deprecated — TSE endpoints removed)."""
    global _client, _client_initialized
    if _client is None:
        _client = BrsApiClient()
    if not _client_initialized:
        await _client.initialize()
        _client_initialized = True
    return _client


async def close_brs_client() -> None:
    """Close the BRS client session."""
    global _client, _client_initialized
    if _client and _client_initialized:
        await _client.shutdown()
        _client_initialized = False
        _client = None


async def _not_available() -> Any:
    raise HTTPException(
        status_code=501,
        detail="TSE/BRS live streaming endpoints have been removed. "
               "NASDAQ + Crypto data is available via /api/v1/market/* endpoints.",
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
