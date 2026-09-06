"""
Data Health Endpoint

Provides /api/data-health as a top-level route (not versioned).
Verifies connectivity to the data provider and returns status.

Enhanced with live-pipeline specific sections:
    streams      -> per-stream status, freshness age, counts, SLO attainment
    sse_clients  -> total count + top subscribed stream keys
    slo_summary  -> warn/error totals + current threshold values
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter

from app.core.config import get_settings
from app.core.utils import utc_now_iso
from app.services.data.market_hours_service import MarketHoursService
from app.services.data.real_time_market_data_service import RealTimeMarketDataService
from app.services.core.dependency_container import get_global_container

logger = logging.getLogger(__name__)
router = APIRouter(tags=["data-health"])

settings = get_settings()


def _overall_status_from_parts(
    provider: str,
    live_slo_warn: int,
    live_slo_error: int,
) -> str:
    if provider == "unhealthy" or live_slo_error > 0:
        return "unhealthy"
    if live_slo_warn > 0:
        return "degraded"
    if provider == "healthy":
        return "healthy"
    return "stale"


@router.get("/data-health")
async def data_health_check() -> Dict[str, Any]:
    """
    Health check for the live data pipeline.

    Verifies connectivity to the data provider, confirms last successful fetch,
    and returns current data source status.
    """
    timestamp = utc_now_iso()
    container = get_global_container()

    provider_health: Dict[str, Any] = {}
    provider_status = "unknown"
    try:
        service: Optional[RealTimeMarketDataService] = container.get("real_time_market_data_service")
        if service is None:
            provider_health = {
                "status": "unhealthy",
                "last_successful_fetch": None,
                "last_error": "Real-time market data service is not registered",
                "latency_ms": None,
                "provider": settings.DATA_PROVIDER,
            }
            provider_status = "unhealthy"
        else:
            provider_health = await service.health_check()
            provider_status = provider_health.get("status", "unknown")
    except Exception as exc:
        logger.error(f"Data health provider check failed: {exc}")
        provider_health = {
            "status": "unhealthy",
            "last_successful_fetch": None,
            "last_error": str(exc),
            "latency_ms": None,
            "provider": settings.DATA_PROVIDER,
        }
        provider_status = "unhealthy"

    # Live-pipeline specific metrics
    live_pipeline: Dict[str, Any] = {}
    streams: Dict[str, Any] = {}
    sse_clients: Dict[str, Any] = {"count": 0, "top_subscriptions": []}
    slo_summary: Dict[str, Any] = {
        "warn": 0,
        "error": 0,
        "threshold_values_open": {
            "quote_max_age_s": settings.LIVE_MAX_QUOTE_AGE_OPEN_S,
            "poll_interval_s": settings.LIVE_POLL_INTERVAL_OPEN_S,
            "intraday_poll_interval_s": settings.LIVE_INTRADAY_POLL_INTERVAL_OPEN_S,
            "slo_warn_multiplier": settings.LIVE_SLO_WARN_MULTIPLIER,
            "slo_error_multiplier": settings.LIVE_SLO_ERROR_MULTIPLIER,
            "circuit_breaker_failures": settings.LIVE_CIRCUIT_BREAKER_FAILURES,
            "circuit_breaker_halfopen_s": settings.LIVE_CIRCUIT_BREAKER_HALFOPEN_S,
            "ping_interval_s": settings.LIVE_PING_INTERVAL_S,
            "idle_unsubscribe_s": settings.LIVE_IDLE_UNSUBSCRIBE_S,
        },
        "threshold_values_closed": {
            "quote_max_age_s": settings.LIVE_MAX_QUOTE_AGE_CLOSED_S,
            "poll_interval_s": settings.LIVE_POLL_INTERVAL_CLOSED_S,
            "intraday_poll_interval_s": settings.LIVE_POLL_INTERVAL_CLOSED_S,
            "slo_warn_multiplier": settings.LIVE_SLO_WARN_MULTIPLIER,
            "slo_error_multiplier": settings.LIVE_SLO_ERROR_MULTIPLIER,
            "circuit_breaker_failures": settings.LIVE_CIRCUIT_BREAKER_FAILURES,
            "circuit_breaker_halfopen_s": settings.LIVE_CIRCUIT_BREAKER_HALFOPEN_S,
            "ping_interval_s": settings.LIVE_PING_INTERVAL_S,
            "idle_unsubscribe_s": settings.LIVE_IDLE_UNSUBSCRIBE_S,
        },
    }
    slo_attainment_pct_last_5m: Optional[float] = None
    circuit_snapshot: Dict[str, Any] = {}

    try:
        metrics_svc = None
        try:
            metrics_svc = container.get("live_pipeline_metrics")
        except KeyError:
            metrics_svc = None
        if metrics_svc is not None and hasattr(metrics_svc, "snapshot"):
            snap = metrics_svc.snapshot() or {}
            live_pipeline = {
                "active_subscriptions": snap.get("active_subscriptions", 0),
                "sse_connections": snap.get("sse_connections", 0),
                "reconnects_total": snap.get("reconnects_total", 0),
                "slo_violations_total": snap.get("slo_violations_total", 0),
                "symbols_latency": snap.get("symbols", {}),
            }
            streams = snap.get("streams") or {}
            sse_clients = snap.get("sse_clients") or {"count": 0, "top_subscriptions": []}
            inner_slo = snap.get("slo_summary") or {}
            slo_summary["warn"] = inner_slo.get("warn", 0)
            slo_summary["error"] = inner_slo.get("error", 0)

            # Compute weighted average slo_attainment_pct_last_5m across streams
            total_pct = 0.0
            total_weight = 0
            for info in streams.values():
                if not isinstance(info, dict):
                    continue
                pct = info.get("slo_attainment_pct_last_5m")
                msg_count = info.get("messages_last_5m", 0) or 0
                if isinstance(pct, (int, float)) and msg_count > 0:
                    total_pct += float(pct) * msg_count
                    total_weight += msg_count
                elif isinstance(pct, (int, float)) and total_weight == 0:
                    total_pct += float(pct)
                    total_weight += 1
            slo_attainment_pct_last_5m = (
                round(total_pct / total_weight, 2) if total_weight > 0 else 100.0
            )
    except Exception as exc:
        logger.warning(f"Live pipeline metrics aggregation error: {exc}")

    try:
        circuit = None
        try:
            circuit = container.get("live_circuit_breaker")
        except KeyError:
            circuit = None
        if circuit is not None and hasattr(circuit, "snapshot"):
            circuit_snapshot = circuit.snapshot() or {}
    except Exception:
        pass

    # Market-hours context
    market_ctx: Dict[str, Any] = {}
    try:
        market_hours = MarketHoursService()
        market_ctx = market_hours.get_market_status()
    except Exception:
        market_ctx = {"status": "unknown"}

    overall = _overall_status_from_parts(
        provider_status,
        slo_summary.get("warn", 0),
        slo_summary.get("error", 0),
    )

    return {
        "status": overall,
        "timestamp": timestamp,
        "provider": provider_health,
        "market": market_ctx,
        "live_pipeline": live_pipeline,
        "streams": streams,
        "sse_clients": sse_clients,
        "slo_summary": slo_summary,
        "circuits": circuit_snapshot,
        "slo_attainment_pct_last_5m": slo_attainment_pct_last_5m,
        "version": {
            "live_config": "v1",
            "app_version": settings.APP_VERSION,
        },
    }
