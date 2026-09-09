"""
Live Market Data Snapshot Routes (REST gap-resync endpoints).

Each endpoint returns the **last emitted event** from the LiveDataOrchestrator
for the corresponding stream key. Frontend SSE consumers call these REST
snapshots to gap-resync whenever they detect a sequence discontinuity
(sequence received != previous_sequence + 1 with gap > 2).

URL shape intentionally mirrors the SSE endpoint layout so clients can
derive the snapshot URL by dropping the trailing `/stream`.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request
from starlette import status as http_status

from app.core.config import get_settings
from app.core.utils import utc_now_iso
from app.schemas.schemas import (
    LiveMarketResponse,
    LiveNewsResponse,
    LiveOrderbookResponse,
    LiveQuoteResponse,
    LiveScoresResponse,
)
from app.services.core.dependency_container import get_global_container
from app.services.live.endpoint_validators import (
    validate_interval,
    validate_scope,
    validate_symbol,
)
from app.services.live.models import LiveEventEnvelope
from app.services.user.auth_service import decode_token

logger = logging.getLogger(__name__)

router = APIRouter(tags=["market-live"])

settings = get_settings()


def _extract_token(request: Request) -> str | None:
    auth_header = request.headers.get("authorization", "")
    if auth_header.lower().startswith("bearer "):
        return auth_header.split(" ", 1)[1].strip()
    qp = request.query_params.get("token")
    if qp:
        return str(qp).strip()
    return None


def _authenticate(request: Request) -> None:
    """REST snapshot authentication (same rules as SSE endpoints)."""
    if not settings.REQUIRE_AUTH:
        return
    token = _extract_token(request)
    if not token:
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"},
            detail={
                "status": "error",
                "error_code": "UNAUTHORIZED",
                "message": "Authentication required for live snapshot endpoints",
            },
        )
    payload = decode_token(token)
    if payload is None or payload.get("type") != "access" or payload.get("sub") is None:
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"},
            detail={
                "status": "error",
                "error_code": "UNAUTHORIZED",
                "message": "Invalid or expired token",
            },
        )


def _get_orchestrator() -> Any:
    container = get_global_container()
    try:
        orch = container.get("live_orchestrator")
    except KeyError:
        orch = None
    if orch is None:
        raise HTTPException(
            status_code=http_status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "error",
                "error_code": "SERVICE_UNAVAILABLE",
                "message": "Live data orchestrator not yet initialized",
            },
        )
    return orch


def _envelope_to_response(envelope: LiveEventEnvelope | None) -> dict[str, Any]:
    if envelope is None:
        return {
            "stream_key": None,
            "event": None,
            "data": None,
            "error": "No live snapshot available yet for this stream key",
            "timestamp": None,
        }
    model = envelope.model_dump(mode="json")
    return {
        "stream_key": model.get("stream_key"),
        "event": model.get("event"),
        "data": model.get("data"),
        "error": model.get("error"),
        "timestamp": model.get("timestamp"),
    }


def _get_stream_status(orch: Any, stream_key: str) -> dict[str, Any]:
    env = orch.get_last_emitted(stream_key)
    snap = _envelope_to_response(env)
    snap["timestamp"] = utc_now_iso()
    if snap.get("stream_key") is None:
        snap["stream_key"] = stream_key
    return snap


# ----------------------------------------------------------------------
# Snapshot endpoints
# ----------------------------------------------------------------------


@router.get("/quote/{symbol}", response_model=LiveQuoteResponse)
async def live_quote_snapshot(
    request: Request,
    symbol: str,
) -> LiveQuoteResponse:
    """
    Return the most recent quote event for the symbol.

    Use this after detecting a sequence gap on the SSE stream to reset
    the frontend's sequence baseline without missing intermediate ticks.
    """
    safe_symbol = validate_symbol(symbol, param_name="symbol")
    _authenticate(request)
    orch = _get_orchestrator()
    stream_key = f"quote:{safe_symbol}"
    return _get_stream_status(orch, stream_key)


@router.get("/intraday/{symbol}", response_model=LiveQuoteResponse)
async def live_intraday_snapshot(
    request: Request,
    symbol: str,
    interval: str | None = Query(default=None),
) -> LiveQuoteResponse:
    """Return the most recent intraday bar set for the symbol+interval pair."""
    safe_symbol = validate_symbol(symbol, param_name="symbol")
    safe_interval = validate_interval(interval)
    _authenticate(request)
    orch = _get_orchestrator()
    stream_key = f"intraday:{safe_symbol}:{safe_interval}"
    return _get_stream_status(orch, stream_key)


@router.get("/market", response_model=LiveMarketResponse)
async def live_market_snapshot(
    request: Request,
) -> LiveMarketResponse:
    """Return the most recent aggregate market_pulse composite event."""
    _authenticate(request)
    orch = _get_orchestrator()
    stream_key = "market"
    return _get_stream_status(orch, stream_key)


@router.get("/scores", response_model=LiveScoresResponse)
async def live_scores_snapshot(
    request: Request,
    scope: str | None = Query(default="NASDAQ"),
) -> LiveScoresResponse:
    """Return the most recent score_delta event for a given market scope."""
    safe_scope = validate_scope(scope, allowed={"NASDAQ"}, default="NASDAQ")
    _authenticate(request)
    orch = _get_orchestrator()
    stream_key = f"scores:{safe_scope}"
    return _get_stream_status(orch, stream_key)


@router.get("/news", response_model=LiveNewsResponse)
async def live_news_snapshot(
    request: Request,
) -> LiveNewsResponse:
    """Return the most recent news_item event emitted by the news poller."""
    _authenticate(request)
    orch = _get_orchestrator()
    stream_key = "news"
    return _get_stream_status(orch, stream_key)


@router.get("/orderbook/{symbol}", response_model=LiveOrderbookResponse)
async def live_orderbook_snapshot(
    request: Request,
    symbol: str,
) -> LiveOrderbookResponse:
    """
    Return the most recent order book event for the symbol.

    Use this after detecting a sequence gap on the SSE stream to reset
    the frontend's sequence baseline without missing intermediate ticks.
    """
    safe_symbol = validate_symbol(symbol, param_name="symbol")
    _authenticate(request)
    orch = _get_orchestrator()
    stream_key = f"orderbook:{safe_symbol}"
    return _get_stream_status(orch, stream_key)


@router.get("/streams", summary="List all active live stream keys + status")
async def live_streams_list(
    request: Request,
) -> dict[str, Any]:
    """
    Admin/debug endpoint listing every active or recently-emitted stream.

    Returns a mapping of stream keys to their current orchestrator status.
    """
    _authenticate(request)
    orch = _get_orchestrator()
    keys = orch.list_active_streams()
    entries: dict[str, dict[str, Any]] = {}
    for key in keys:
        entries[key] = orch.get_stream_status(key)
    return {
        "snapshot_at": utc_now_iso(),
        "count": len(entries),
        "streams": entries,
    }
