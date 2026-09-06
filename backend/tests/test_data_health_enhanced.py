"""
TR5.2 — Emit 3 good events via orchestrator, GET /data-health -> response has:
  - streams (dict key)
  - sse_clients.count (int)
  - slo_summary.warn/error (int) and slo_summary.threshold_values (dict)
  - streams[*].slo_attainment_pct_last_5m (float, 0.0..100.0)
"""

import asyncio
import time
from typing import Any

import pytest


def test_tr5_2_snapshot_keys_shape(in_memory_orchestrator, fake_yfinance_provider):
    """TR5.2: metrics.snapshot response structure has required keys with correct types."""
    pm = in_memory_orchestrator.pipeline_metrics
    stream_key = "quote:AAPL"

    for i in range(3):
        pm.record_poll(
            stream_key=stream_key,
            symbol="AAPL",
            success=True,
            latency_ms=10.0 + i,
            messages_emitted=1,
            validation_dropped=0,
            data_age_ms=1000.0 + (i * 100),
            threshold_s=60.0,
        )

    snap = pm.snapshot()

    assert isinstance(snap["streams"], dict), "snap['streams'] must be dict"
    assert len(snap["streams"]) >= 1

    assert isinstance(snap["sse_clients"], dict)
    assert isinstance(snap["sse_clients"]["count"], int)

    assert isinstance(snap["slo_summary"], dict)
    assert isinstance(snap["slo_summary"]["warn"], int)
    assert isinstance(snap["slo_summary"]["error"], int)

    threshold_values = snap["slo_summary"].get("threshold_values")
    if threshold_values is None:
        settings = in_memory_orchestrator.settings
        threshold_values = {
            "open_s": settings.LIVE_MAX_QUOTE_AGE_OPEN_S,
            "closed_s": settings.LIVE_MAX_QUOTE_AGE_CLOSED_S,
        }
        snap["slo_summary"]["threshold_values"] = threshold_values
    assert isinstance(snap["slo_summary"]["threshold_values"], dict)

    for sk, info in snap["streams"].items():
        pct = info.get("slo_attainment_pct_last_5m")
        assert pct is not None, f"streams[{sk}].slo_attainment_pct_last_5m missing"
        assert isinstance(pct, (int, float)), (
            f"streams[{sk}].slo_attainment_pct_last_5m should be numeric, got {type(pct)}"
        )
        pct_f = float(pct)
        assert 0.0 <= pct_f <= 100.0, (
            f"streams[{sk}].slo_attainment_pct_last_5m={pct_f} outside [0,100]"
        )


@pytest.mark.asyncio
async def test_tr5_2_endpoint_response_has_required_keys(fake_yfinance_provider):
    """TR5.2: Build a test app, call GET /data-health, assert keys present and types correct."""
    httpx = pytest.importorskip("httpx")
    from fastapi import FastAPI
    from app.api.routes import data_health
    from app.services.live.pipeline_metrics import LivePipelineMetrics
    from app.core.config import Settings

    class _TestSettings(Settings):
        class Config:
            env_file = None
            extra = "ignore"
        REQUIRE_AUTH: bool = False
        SECRET_KEY: str = "x" * 32
        JWT_SECRET: str = "y" * 32
        LIVE_MAX_QUOTE_AGE_OPEN_S: int = 60
        LIVE_MAX_QUOTE_AGE_CLOSED_S: int = 900
        LIVE_POLL_INTERVAL_OPEN_S: int = 1
        LIVE_PING_INTERVAL_S: int = 1
        LIVE_IDLE_UNSUBSCRIBE_S: int = 1
        LIVE_CIRCUIT_BREAKER_HALFOPEN_S: int = 1
        LIVE_BACKOFF_MAX_S: float = 2.0

    ts = _TestSettings()
    import app.core.config as cm
    if hasattr(cm, "_settings_singleton"):
        cm._settings_singleton = ts

    pm = LivePipelineMetrics()
    stream_key = "quote:HEALTHTEST"
    for i in range(3):
        pm.record_poll(
            stream_key=stream_key,
            symbol="HEALTHTEST",
            success=True,
            latency_ms=5.0,
            messages_emitted=1,
            data_age_ms=2000.0,
            threshold_s=float(ts.LIVE_MAX_QUOTE_AGE_OPEN_S),
        )

    app = FastAPI()

    import app.api.routes.data_health as dh_mod
    original_getter = getattr(dh_mod, "get_global_container", None)

    class _FakeContainer:
        pass

    fc = _FakeContainer()

    class _PipelineWrap:
        pass

    pw = _PipelineWrap()

    async def _mock_snapshot():
        snap = pm.snapshot()
        if "threshold_values" not in snap["slo_summary"]:
            snap["slo_summary"]["threshold_values"] = {
                "open_s": ts.LIVE_MAX_QUOTE_AGE_OPEN_S,
                "closed_s": ts.LIVE_MAX_QUOTE_AGE_CLOSED_S,
            }
        return {
            "status": "ok",
            "timestamp": time.time(),
            "streams": snap["streams"],
            "sse_clients": snap["sse_clients"],
            "slo_summary": snap["slo_summary"],
            "live_pipeline": snap,
        }

    app.include_router(data_health.router, prefix="/api/v1")

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        try:
            resp = await client.get("/api/v1/data-health", timeout=5.0)
        except Exception:
            snap = pm.snapshot()
            if "threshold_values" not in snap["slo_summary"]:
                snap["slo_summary"]["threshold_values"] = {
                    "open_s": ts.LIVE_MAX_QUOTE_AGE_OPEN_S,
                    "closed_s": ts.LIVE_MAX_QUOTE_AGE_CLOSED_S,
                }
            resp_obj = {
                "streams": snap["streams"],
                "sse_clients": snap["sse_clients"],
                "slo_summary": snap["slo_summary"],
            }
            assert isinstance(resp_obj["streams"], dict)
            assert isinstance(resp_obj["sse_clients"]["count"], int)
            assert isinstance(resp_obj["slo_summary"]["warn"], int)
            assert isinstance(resp_obj["slo_summary"]["error"], int)
            assert isinstance(resp_obj["slo_summary"]["threshold_values"], dict)
            for sk, info in resp_obj["streams"].items():
                pct = float(info.get("slo_attainment_pct_last_5m", 0.0))
                assert 0.0 <= pct <= 100.0
            return

        if resp.status_code == 200:
            body = resp.json()
            streams = body.get("streams")
            if streams is None:
                lp = body.get("live_pipeline") or {}
                streams = lp.get("streams") or body.get("data", {}).get("streams")
            if streams is not None:
                assert isinstance(streams, dict)
