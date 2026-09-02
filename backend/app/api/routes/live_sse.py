"""
Live Market Data SSE Routes

TSE/BRS-specific SSE streams have been removed. These stubs preserve the router
for backward compatibility but return informational messages.
"""
import json
import logging
from typing import Any, AsyncGenerator

from fastapi import APIRouter, Query, Request
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["market-live-sse"])


async def _sse_format(event: str, data: Any) -> str:
    """Format data as SSE event string."""
    payload = json.dumps(data, ensure_ascii=False, default=str)
    return f"event: {event}\ndata: {payload}\n\n"


async def _stream_removed() -> AsyncGenerator[str, None]:
    """Stream a single message indicating the endpoint was removed."""
    yield await _sse_format("info", {
        "message": "TSE/BRS SSE streams have been removed. "
                    "NASDAQ data is available via standard OHLCV endpoints."
    })


@router.get("/symbols/stream", summary="All real-time symbols (SSE stream)")
async def live_symbols_stream(
    request: Request,
    market_type: int = Query(1, ge=1, le=5),
) -> StreamingResponse:
    """Streaming endpoint (stub — BRS removed)."""
    return StreamingResponse(
        _stream_removed(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@router.get("/symbol/{l18}/stream", summary="Comprehensive real-time data (SSE stream)")
async def live_symbol_stream(request: Request, l18: str) -> StreamingResponse:
    """Streaming endpoint (stub — BRS removed)."""
    return StreamingResponse(
        _stream_removed(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@router.get("/candlestick/{l18}/stream", summary="Candles (SSE stream)")
async def live_candlestick_stream(request: Request, l18: str) -> StreamingResponse:
    """Streaming endpoint (stub — BRS removed)."""
    return StreamingResponse(
        _stream_removed(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@router.get("/history/{l18}/stream", summary="Daily price & trade history (SSE stream)")
async def live_history_stream(request: Request, l18: str) -> StreamingResponse:
    """Streaming endpoint (stub — BRS removed)."""
    return StreamingResponse(
        _stream_removed(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
