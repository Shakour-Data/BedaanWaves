"""
Live Market Data SSE Routes.

Provides 5 server-sent event streaming endpoints:
    GET /api/v1/live-sse/quote/{symbol}/stream
    GET /api/v1/live-sse/intraday/{symbol}/stream?interval=5m
    GET /api/v1/live-sse/market/stream
    GET /api/v1/live-sse/scores/stream?scope=NASDAQ
    GET /api/v1/live-sse/news/stream

Authentication accepts both `Authorization: Bearer <token>` header and
the `?token=<token>` query parameter (needed for native EventSource clients
that cannot set custom headers).

SSE response headers disable all intermediate buffering so that pings and
events arrive at the client with minimal added latency. Provider errors
are sent as sanitized `error_code=provider_error` events (no raw stack
or internal exception messages leak).
"""

from __future__ import annotations

import json
import logging
import re
import time
import uuid
from typing import AsyncGenerator, Dict, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from starlette import status as http_status

from app.core.config import get_settings
from app.services.core.dependency_container import get_global_container
from app.services.live.constants import VALID_INTRADAY_INTERVALS
from app.services.live.endpoint_validators import (
    validate_interval,
    validate_scope,
    validate_symbol,
)
from app.services.live.models import LiveEventEnvelope
from app.services.user.auth_service import decode_token

logger = logging.getLogger(__name__)

router = APIRouter(tags=["market-live-sse"])

settings = get_settings()

_SSE_HEADERS: Dict[str, str] = {
    "Cache-Control": "no-cache, no-store, must-revalidate",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
    "Content-Type": "text/event-stream; charset=utf-8",
    "Transfer-Encoding": "chunked",
}

_TOKEN_QUERY_RE = re.compile(r"[?&]token=([^&\s]+)", re.IGNORECASE)


def _sanitize_log_message(message: str) -> str:
    """Remove any `?token=...` fragments from a string before logging."""
    if not message:
        return message
    return _TOKEN_QUERY_RE.sub("[?token=<redacted>]", message)


def _safe_log(level: int, fmt: str, *args: object) -> None:
    """Emit a log record after sanitizing any ?token= occurrences."""
    if not logger.isEnabledFor(level):
        return
    cleaned_args = tuple(
        _sanitize_log_message(a) if isinstance(a, str) else a for a in args
    )
    cleaned_fmt = _sanitize_log_message(fmt)
    logger.log(level, cleaned_fmt, *cleaned_args)


def _extract_token(request: Request) -> Optional[str]:
    """Extract token from Authorization header or ?token= query string."""
    auth_header = request.headers.get("authorization", "")
    if auth_header.lower().startswith("bearer "):
        return auth_header.split(" ", 1)[1].strip()
    qp_token = request.query_params.get("token")
    if qp_token:
        return str(qp_token).strip()
    return None


def _authenticate(request: Request) -> Dict[str, object]:
    """
    Pre-streaming authentication check.

    Returns the decoded token payload on success. Raises HTTPException 401
    as a plain JSON response (NOT an SSE stream) when the token is missing
    or invalid.
    """
    if not settings.REQUIRE_AUTH:
        token = _extract_token(request)
        if token:
            payload = decode_token(token)
            if payload and payload.get("type") == "access":
                return payload
        return {"dev_mode": True, "user_id": settings.DEV_USER_ID}

    token = _extract_token(request)
    if not token:
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"},
            detail={
                "status": "error",
                "error_code": "UNAUTHORIZED",
                "message": "Authentication required for live SSE streams",
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
    return payload


def _format_sse(event: str, data_obj: Dict[str, object]) -> str:
    """Format a single SSE `event:` / `data:` block."""
    try:
        payload = json.dumps(data_obj, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        payload = json.dumps({"error_code": "serialization_failed"}, ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n"


async def _stream_generator(
    orchestrator: Any,
    stream_key: str,
    metrics: Any,
    connection_id: str,
) -> AsyncGenerator[str, None]:
    """
    Async generator that subscribes to the orchestrator and yields
    formatted SSE frames until the client disconnects.
    """
    subscriber_id = f"{connection_id}-{uuid.uuid4().hex[:8]}"
    if metrics is not None and hasattr(metrics, "register_sse_connection"):
        try:
            metrics.register_sse_connection(connection_id, stream_key)
        except Exception:
            pass
    _safe_log(
        logging.INFO,
        "SSE connect stream=%s subscriber=%s cid=%s",
        stream_key, subscriber_id, connection_id,
    )

    first_event = True
    try:
        gen = orchestrator.subscribe(stream_key, subscriber_id=subscriber_id)
        async for envelope in gen:
            if not isinstance(envelope, LiveEventEnvelope):
                continue
            event_type = envelope.event
            raw_data = envelope.data or {}
            # Sanitize any provider errors before sending over the wire.
            if event_type == "health":
                reason = raw_data.get("reason_message")
                code = raw_data.get("reason_code")
                if code in ("provider_error", "circuit_open"):
                    sanitized = dict(raw_data)
                    sanitized["error_code"] = "provider_error"
                    if reason and any(needle in str(reason) for needle in (
                        "ValueError", "KeyError", "Traceback", "yfinance",
                        "HTTPError", "timeout",
                    )):
                        sanitized["reason_message"] = (
                            "Upstream data provider unavailable; "
                            "retrying with backoff."
                        )
                    frame = _format_sse(event_type, sanitized)
                else:
                    frame = _format_sse(event_type, raw_data)
            else:
                frame = _format_sse(event_type, raw_data)
            if first_event:
                first_event = False
                # FastAPI StreamingResponse will already have sent the
                # headers by the time we yield the first byte; we rely on
                # _authenticate() having returned before headers went out.
                pass
            yield frame

            if metrics is not None:
                try:
                    if hasattr(metrics, "record_sequence"):
                        metrics.record_sequence(stream_key, envelope.sequence)
                    if hasattr(metrics, "observe_envelope"):
                        age = (raw_data or {}).get("data_age_ms")
                        thresh = (raw_data or {}).get("_threshold_s")
                        metrics.observe_envelope(envelope, data_age_ms=age, threshold_s=thresh)
                except Exception:
                    pass
    except asyncio.CancelledError:
        _safe_log(
            logging.INFO,
            "SSE client cancelled stream=%s subscriber=%s",
            stream_key, subscriber_id,
        )
        raise
    except GeneratorExit:
        raise
    except Exception as exc:
        _safe_log(
            logging.WARNING,
            "SSE stream error stream=%s subscriber=%s error=%s",
            stream_key, subscriber_id, type(exc).__name__,
        )
        sanitized = {
            "error_code": "provider_error",
            "message": "Stream encountered an internal error and will close.",
            "stream_key": stream_key,
        }
        yield _format_sse("health", sanitized)
    finally:
        _safe_log(
            logging.INFO,
            "SSE disconnect stream=%s subscriber=%s cid=%s",
            stream_key, subscriber_id, connection_id,
        )
        if metrics is not None and hasattr(metrics, "unregister_sse_connection"):
            try:
                metrics.unregister_sse_connection(connection_id)
            except Exception:
                pass
        try:
            await orchestrator.unsubscribe(stream_key, subscriber_id)
        except Exception:
            pass


def _get_orchestrator_and_metrics() -> tuple:
    container = get_global_container()
    try:
        orch = container.get("live_orchestrator")
    except KeyError:
        orch = None
    metrics = None
    try:
        metrics = container.get("live_pipeline_metrics")
    except KeyError:
        pass
    if orch is None:
        raise HTTPException(
            status_code=http_status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "error",
                "error_code": "SERVICE_UNAVAILABLE",
                "message": "Live data orchestrator not yet initialized",
            },
        )
    return orch, metrics


# ----------------------------------------------------------------------
# Endpoints
# ----------------------------------------------------------------------


@router.get("/quote/{symbol}/stream", summary="Live per-symbol quote SSE stream")
async def live_quote_stream(
    request: Request,
    symbol: str,
) -> StreamingResponse:
    """
    Stream quote events for a single ticker symbol.

    Accepts auth via `Authorization: Bearer <JWT>` header or `?token=<JWT>`.
    Disallowed symbols or charset violations return HTTP 422 before
    opening the SSE stream.
    """
    safe_symbol = validate_symbol(symbol, param_name="symbol")
    _authenticate(request)
    stream_key = f"quote:{safe_symbol}"
    orch, metrics = _get_orchestrator_and_metrics()

    connection_id = getattr(request.state, "correlation_id", None) or uuid.uuid4().hex
    if metrics is not None and hasattr(metrics, "increment_active_subscriptions"):
        try:
            metrics.increment_active_subscriptions(1)
        except Exception:
            pass

    return StreamingResponse(
        _stream_generator(orch, stream_key, metrics, connection_id),
        headers=_SSE_HEADERS,
        media_type="text/event-stream",
    )


@router.get("/intraday/{symbol}/stream", summary="Live per-symbol intraday SSE stream")
async def live_intraday_stream(
    request: Request,
    symbol: str,
    interval: Optional[str] = Query(default=None),
) -> StreamingResponse:
    """
    Stream intraday OHLCV bars for a single ticker + interval.

    `interval` must be one of: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h (default 5m).
    """
    safe_symbol = validate_symbol(symbol, param_name="symbol")
    safe_interval = validate_interval(interval)
    _authenticate(request)
    stream_key = f"intraday:{safe_symbol}:{safe_interval}"
    orch, metrics = _get_orchestrator_and_metrics()

    connection_id = getattr(request.state, "correlation_id", None) or uuid.uuid4().hex
    if metrics is not None and hasattr(metrics, "increment_active_subscriptions"):
        try:
            metrics.increment_active_subscriptions(1)
        except Exception:
            pass

    return StreamingResponse(
        _stream_generator(orch, stream_key, metrics, connection_id),
        headers=_SSE_HEADERS,
        media_type="text/event-stream",
    )


@router.get("/market/stream", summary="Live NASDAQ market pulse SSE stream")
async def live_market_stream(
    request: Request,
) -> StreamingResponse:
    """Stream aggregate market-pulse composite events."""
    _authenticate(request)
    stream_key = "market"
    orch, metrics = _get_orchestrator_and_metrics()

    connection_id = getattr(request.state, "correlation_id", None) or uuid.uuid4().hex
    if metrics is not None and hasattr(metrics, "increment_active_subscriptions"):
        try:
            metrics.increment_active_subscriptions(1)
        except Exception:
            pass

    return StreamingResponse(
        _stream_generator(orch, stream_key, metrics, connection_id),
        headers=_SSE_HEADERS,
        media_type="text/event-stream",
    )


@router.get("/scores/stream", summary="Live 6D score delta SSE stream")
async def live_scores_stream(
    request: Request,
    scope: Optional[str] = Query(default="NASDAQ"),
) -> StreamingResponse:
    """
    Stream per-market or per-symbol score delta events.

    Default and currently supported scope: `NASDAQ`.
    """
    safe_scope = validate_scope(scope, allowed={"NASDAQ"}, default="NASDAQ")
    _authenticate(request)
    stream_key = f"scores:{safe_scope}"
    orch, metrics = _get_orchestrator_and_metrics()

    connection_id = getattr(request.state, "correlation_id", None) or uuid.uuid4().hex
    if metrics is not None and hasattr(metrics, "increment_active_subscriptions"):
        try:
            metrics.increment_active_subscriptions(1)
        except Exception:
            pass

    return StreamingResponse(
        _stream_generator(orch, stream_key, metrics, connection_id),
        headers=_SSE_HEADERS,
        media_type="text/event-stream",
    )


@router.get("/news/stream", summary="Live news item SSE stream")
async def live_news_stream(
    request: Request,
) -> StreamingResponse:
    """Stream news items as they are detected by the periodic news poller."""
    _authenticate(request)
    stream_key = "news"
    orch, metrics = _get_orchestrator_and_metrics()

    connection_id = getattr(request.state, "correlation_id", None) or uuid.uuid4().hex
    if metrics is not None and hasattr(metrics, "increment_active_subscriptions"):
        try:
            metrics.increment_active_subscriptions(1)
        except Exception:
            pass

    return StreamingResponse(
        _stream_generator(orch, stream_key, metrics, connection_id),
        headers=_SSE_HEADERS,
        media_type="text/event-stream",
    )
