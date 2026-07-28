"""
Live Market Data Routes - backed by brsapi.ir (Tehran Stock Exchange)

Every endpoint here calls the real BRS API documented in docs/BourseApi.txt.
No database is required: these return the live upstream payloads.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query

from app.core.config import get_settings
from app.services.data.brs_api_client import BrsApiClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/market/live", tags=["market-live"])

_settings = get_settings()
_client = BrsApiClient(
    base_url=_settings.BRS_API_BASE_URL,
    api_key=_settings.BRS_API_KEY,
    timeout=_settings.BRS_API_TIMEOUT,
)
_client_initialized = False


async def get_brs_client() -> BrsApiClient:
    """Return the singleton BRS client, initializing its session lazily."""
    global _client_initialized
    if not _client_initialized:
        await _client.initialize()
        _client_initialized = True
    return _client


async def close_brs_client() -> None:
    """Close the BRS client session (called on app shutdown)."""
    global _client_initialized
    if _client_initialized:
        await _client.shutdown()
        _client_initialized = False


@router.get("/symbols", summary="All real-time symbols (AllSymbols)")
async def live_symbols(
    market_type: int = Query(1, ge=1, le=5, description="1=Stocks+ETF+Rights, 2=IME, 3=Futures, 4=Debt, 5=Housing"),
    client: BrsApiClient = Depends(get_brs_client),
) -> Any:
    """Real-time snapshot of every symbol (docs/BourseApi.txt -> AllSymbols)."""
    return await client.get_all_symbols(market_type=market_type)


@router.get("/symbol/{l18}", summary="Comprehensive real-time data for one symbol")
async def live_symbol(
    l18: str,
    client: BrsApiClient = Depends(get_brs_client),
) -> Any:
    """Comprehensive real-time data for a single ticker (Symbol endpoint)."""
    return await client.get_symbol(l18=l18)


@router.get("/candlestick/{l18}", summary="Candles (real-time 2m or daily history)")
async def live_candlestick(
    l18: str,
    candle_type: int = Query(1, ge=1, le=3, description="1=realtime 2m, 2=unadjusted daily, 3=adjusted daily"),
    client: BrsApiClient = Depends(get_brs_client),
) -> Any:
    """Candlestick data (Candlestick endpoint)."""
    return await client.get_candlestick(l18=l18, candle_type=candle_type)


@router.get("/history/{l18}", summary="Daily price & trade history")
async def live_history(
    l18: str,
    client: BrsApiClient = Depends(get_brs_client),
) -> Any:
    """Daily historical price & trade data (History endpoint)."""
    return await client.get_history(l18=l18)


@router.get("/transaction/{l18}", summary="Intraday trade ticks")
async def live_transaction(
    l18: str,
    date: Optional[str] = Query(None, description="Jalali YYYY-MM-DD (defaults to last trading day)"),
    client: BrsApiClient = Depends(get_brs_client),
) -> Any:
    """Intraday trade ticks (Transaction endpoint)."""
    return await client.get_transaction(l18=l18, date=date)


@router.get("/shareholder/{l18}", summary="Major shareholders")
async def live_shareholder(
    l18: str,
    date: Optional[str] = Query(None, description="Jalali YYYY-MM-DD (defaults to latest)"),
    client: BrsApiClient = Depends(get_brs_client),
) -> Any:
    """Major shareholders of a symbol (Shareholder endpoint)."""
    return await client.get_shareholder(l18=l18, date=date)


@router.get("/index", summary="Market indices")
async def live_index(
    index_type: int = Query(1, ge=1, le=3, description="1=TSE, 2=Fara Bours, 3=Selected"),
    client: BrsApiClient = Depends(get_brs_client),
) -> Any:
    """Market indices (Index endpoint)."""
    return await client.get_index(index_type=index_type)


@router.get("/option", summary="Option market (call/put)")
async def live_option(client: BrsApiClient = Depends(get_brs_client)) -> Any:
    """Real-time option market (Option endpoint)."""
    return await client.get_option()


@router.get("/nav/{l18}", summary="ETF NAV")
async def live_nav(
    l18: str,
    client: BrsApiClient = Depends(get_brs_client),
) -> Any:
    """ETF NAV subscription/redemption (Nav endpoint)."""
    return await client.get_nav(l18=l18)


@router.get("/codal", summary="Codal disclosures")
async def live_codal(
    l18: Optional[str] = Query(None),
    category: Optional[int] = Query(None, description="1=Annual, 2=Disclosure, 3=Monthly, 6=Assembly, 7=Capital increase"),
    date_start: Optional[str] = Query(None),
    date_end: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    client: BrsApiClient = Depends(get_brs_client),
) -> Any:
    """Company disclosures (Codal Announcement endpoint)."""
    return await client.get_codal(
        l18=l18, category=category, date_start=date_start,
        date_end=date_end, page=page,
    )


@router.get("/ime/physical", summary="IME physical commodity trades")
async def live_ime_physical(client: BrsApiClient = Depends(get_brs_client)) -> Any:
    """Physical commodity trade statistics (IME Physical endpoint)."""
    return await client.get_ime_physical()


@router.get("/ime/fund", summary="IME commodity-backed funds")
async def live_ime_fund(client: BrsApiClient = Depends(get_brs_client)) -> Any:
    """Commodity-backed fund data (IME Fund endpoint)."""
    return await client.get_ime_fund()


@router.get("/ime/certificate", summary="IME deposit certificates")
async def live_ime_certificate(client: BrsApiClient = Depends(get_brs_client)) -> Any:
    """Commodity deposit certificates (IME Certificate endpoint)."""
    return await client.get_ime_certificate()


@router.get("/rate-limit/status", summary="BrsApi rate limit status")
async def brs_rate_limit_status(client: BrsApiClient = Depends(get_brs_client)) -> Any:
    """Return current BrsApi rate limit usage."""
    return client.get_rate_limit_status()
