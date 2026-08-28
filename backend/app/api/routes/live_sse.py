"""
Live Market Data SSE Routes - Server-Sent Events for real-time BRS API data.

Provides streaming endpoints that proxy brsapi.ir data as SSE events.
Frontend can connect with EventSource to receive live updates.
"""

import asyncio
import json
import logging
from typing import Any, AsyncGenerator, Optional

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse

from app.core.config import get_settings
from app.services.data.brs_api_client import BrsApiClient

logger = logging.getLogger(__name__)

router = APIRouter(tags=["market-live-sse"])

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


async def _sse_format(event: str, data: Any) -> str:
    """Format data as SSE event string."""
    payload = json.dumps(data, ensure_ascii=False, default=str)
    return f"event: {event}\ndata: {payload}\n\n"


async def _heartbeat() -> str:
    """SSE heartbeat to keep connection alive."""
    return ": heartbeat\n\n"


async def _stream_single(
    request: Request,
    fetch_coro,
    poll_interval: float = 5.0,
) -> AsyncGenerator[str, None]:
    """Stream a single data fetch as SSE, then close."""
    try:
        data = await fetch_coro()
        yield await _sse_format("update", data)
    except Exception as exc:
        logger.error("SSE stream error: %s", exc)
        yield await _sse_format("error", {"message": str(exc)})


async def _stream_polling(
    request: Request,
    fetch_coro,
    poll_interval: float = 5.0,
) -> AsyncGenerator[str, None]:
    """Continuously poll BRS API and push updates as SSE events."""
    client = await get_brs_client()
    try:
        while True:
            if await request.is_disconnected():
                break
            try:
                data = await fetch_coro(client)
                yield await _sse_format("update", data)
            except Exception as exc:
                logger.error("SSE polling error: %s", exc)
                yield await _sse_format("error", {"message": str(exc)})
            try:
                await asyncio.wait_for(request.is_disconnected(), timeout=poll_interval)
                break
            except asyncio.TimeoutError:
                continue
    except asyncio.CancelledError:
        pass


@router.get("/symbols/stream", summary="All real-time symbols (SSE stream)")
async def live_symbols_stream(
    request: Request,
    market_type: int = Query(1, ge=1, le=5, description="1=Stocks+ETF+Rights, 2=IME, 3=Futures, 4=Debt, 5=Housing"),
) -> StreamingResponse:
    """Real-time snapshot of every symbol as SSE stream."""
    async def fetch(client: BrsApiClient) -> Any:
        return await client.get_all_symbols(market_type=market_type)

    return StreamingResponse(
        _stream_polling(request, fetch, poll_interval=5.0),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/symbol/{l18}/stream", summary="Comprehensive real-time data for one symbol (SSE stream)")
async def live_symbol_stream(
    request: Request,
    l18: str,
) -> StreamingResponse:
    """Comprehensive real-time data for a single ticker as SSE stream."""
    async def fetch(client: BrsApiClient) -> Any:
        return await client.get_symbol(l18=l18)

    return StreamingResponse(
        _stream_polling(request, fetch, poll_interval=5.0),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/candlestick/{l18}/stream", summary="Candles (SSE stream)")
async def live_candlestick_stream(
    request: Request,
    l18: str,
    candle_type: int = Query(1, ge=1, le=3, description="1=realtime 2m, 2=unadjusted daily, 3=adjusted daily"),
) -> StreamingResponse:
    """Candlestick data as SSE stream."""
    async def fetch(client: BrsApiClient) -> Any:
        return await client.get_candlestick(l18=l18, candle_type=candle_type)

    return StreamingResponse(
        _stream_polling(request, fetch, poll_interval=5.0),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/history/{l18}/stream", summary="Daily price & trade history (SSE stream)")
async def live_history_stream(
    request: Request,
    l18: str,
) -> StreamingResponse:
    """Daily historical price & trade data as SSE stream."""
    async def fetch(client: BrsApiClient) -> Any:
        return await client.get_history(l18=l18)

    return StreamingResponse(
        _stream_polling(request, fetch, poll_interval=5.0),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
