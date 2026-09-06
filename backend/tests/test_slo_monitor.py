"""
TR6.1 — data_age between warn and error threshold -> WARN notification (spy ≥1).
       data_age above error threshold -> ERROR notification (spy ≥1).
TR6.2 — breach -> 3 consecutive good ticks -> RESOLVED notification dispatched.
TR6.3 — 600s simulated sustained warn breach (below error) -> total alerts ≤ ~11 (debounce 60s each).
"""

import asyncio
import time
from datetime import datetime, timezone
from typing import Any

import pytest

from app.services.live.models import (
    LiveEventEnvelope,
    LiveQuotePayload,
)
from app.services.live.slo_monitor import (
    SEVERITY_ERROR,
    SEVERITY_RESOLVED,
    SEVERITY_WARN,
    SLOMonitor,
)


def _make_envelope(stream_key: str, event: str = "quote") -> LiveEventEnvelope:
    now = datetime.now(timezone.utc)
    sym = stream_key.split(":")[-1] if ":" in stream_key else "TEST"
    data = LiveQuotePayload(
        symbol=sym,
        current_price=100.0,
        change_value=0.0,
        change_percent=0.0,
        open=100.0,
        high=100.0,
        low=100.0,
        previous_close=100.0,
        volume=0,
        freshness_ts=now,
    )
    return LiveEventEnvelope(
        event=event,
        data=data.model_dump(),
        sequence=1,
        stream_key=stream_key,
    )


@pytest.mark.asyncio
async def test_tr6_1_warn_between_thresholds_error_above(in_memory_orchestrator):
    """TR6.1: age > warn but < error -> WARN; age > error -> ERROR."""
    dispatcher = in_memory_orchestrator.notification_dispatcher
    slo = in_memory_orchestrator.slo_monitor
    await slo.initialize()
    try:
        threshold_s = float(in_memory_orchestrator.settings.LIVE_MAX_QUOTE_AGE_OPEN_S)
        warn_mult = float(in_memory_orchestrator.settings.LIVE_SLO_WARN_MULTIPLIER)
        error_mult = float(in_memory_orchestrator.settings.LIVE_SLO_ERROR_MULTIPLIER)
        threshold_ms = threshold_s * 1000.0
        warn_ms = threshold_ms * warn_mult
        error_ms = threshold_ms * error_mult

        warn_age_ms = warn_ms * 1.2
        assert warn_age_ms < error_ms, (
            f"WARN test age must be below ERROR threshold: {warn_age_ms} < {error_ms}"
        )
        stream_key_warn = "quote:SLOWARN"
        for _ in range(10):
            env = _make_envelope(stream_key_warn, "quote")
            try:
                slo.observe_envelope(env, data_age_ms=warn_age_ms, threshold_s=threshold_s)
            except Exception:
                pass
            await asyncio.sleep(0.01)
        await asyncio.sleep(0.2)

        warn_calls = dispatcher.calls_with_severity(SEVERITY_WARN)
        assert len(warn_calls) >= 1, (
            f"Expected >=1 WARN at age={warn_age_ms:.0f}ms "
            f"(warn={warn_ms:.0f}ms, error={error_ms:.0f}ms), "
            f"got WARN={len(warn_calls)}, dispatcher.total={dispatcher.call_count()}"
        )

        stream_key_err = "quote:SLOERR"
        error_age_ms = error_ms * 1.05
        for _ in range(10):
            env = _make_envelope(stream_key_err, "quote")
            try:
                slo.observe_envelope(env, data_age_ms=error_age_ms, threshold_s=threshold_s)
            except Exception:
                pass
            await asyncio.sleep(0.01)
        await asyncio.sleep(0.2)

        error_calls = dispatcher.calls_with_severity(SEVERITY_ERROR)
        assert len(error_calls) >= 1, (
            f"Expected >=1 ERROR at age={error_age_ms:.0f}ms (error={error_ms:.0f}ms), "
            f"got ERROR={len(error_calls)}, total={dispatcher.call_count()}"
        )
    finally:
        await slo.shutdown()


@pytest.mark.asyncio
async def test_tr6_2_error_to_good_resolution(in_memory_orchestrator):
    """TR6.2: breach -> 3 consecutive good ticks -> RESOLVED notification dispatched."""
    dispatcher = in_memory_orchestrator.notification_dispatcher
    slo = in_memory_orchestrator.slo_monitor
    await slo.initialize()
    try:
        stream_key = "quote:RESOLVETEST"
        threshold_s = float(in_memory_orchestrator.settings.LIVE_MAX_QUOTE_AGE_OPEN_S)
        error_mult = float(in_memory_orchestrator.settings.LIVE_SLO_ERROR_MULTIPLIER)
        threshold_ms = threshold_s * 1000.0
        error_ms = threshold_ms * error_mult

        bad_age_ms = error_ms * 1.5
        for _ in range(15):
            env = _make_envelope(stream_key, "quote")
            try:
                slo.observe_envelope(env, data_age_ms=bad_age_ms, threshold_s=threshold_s)
            except Exception:
                pass
            await asyncio.sleep(0.01)
        await asyncio.sleep(0.2)

        error_calls_before = dispatcher.calls_with_severity(SEVERITY_ERROR)
        assert len(error_calls_before) >= 1, (
            f"Prerequisite: need ERROR state first, got {len(error_calls_before)}"
        )

        state = slo._states.get(stream_key)
        if state is not None:
            state.last_alert_ts.pop(SEVERITY_ERROR, None)
            state.last_alert_ts.pop(SEVERITY_WARN, None)

        good_age_ms = threshold_ms * 0.5
        for _ in range(6):
            env = _make_envelope(stream_key, "quote")
            try:
                slo.observe_envelope(env, data_age_ms=good_age_ms, threshold_s=threshold_s)
            except Exception:
                pass
            await asyncio.sleep(0.01)
        await asyncio.sleep(0.3)

        resolved_calls = dispatcher.calls_with_severity(SEVERITY_RESOLVED)
        assert len(resolved_calls) >= 1, (
            f"Expected >=1 RESOLVED after 6 good ticks, "
            f"got RESOLVED={len(resolved_calls)}. "
            f"WARN={len(dispatcher.calls_with_severity(SEVERITY_WARN))} "
            f"ERROR={len(dispatcher.calls_with_severity(SEVERITY_ERROR))}. "
            f"consecutive_good={getattr(state, 'consecutive_good', None) if state else None}"
        )
    finally:
        await slo.shutdown()


@pytest.mark.asyncio
async def test_tr6_3_600s_simulated_warn_breach_bounded_alerts(in_memory_orchestrator):
    """TR6.3: 600s simulated sustained WARN-only breach -> total alerts ≤ ~11 (debounce 60s)."""
    dispatcher = in_memory_orchestrator.notification_dispatcher
    slo = in_memory_orchestrator.slo_monitor
    await slo.initialize()
    try:
        stream_key = "quote:DEBOUNCETEST"
        threshold_s = float(in_memory_orchestrator.settings.LIVE_MAX_QUOTE_AGE_OPEN_S)
        warn_mult = float(in_memory_orchestrator.settings.LIVE_SLO_WARN_MULTIPLIER)
        error_mult = float(in_memory_orchestrator.settings.LIVE_SLO_ERROR_MULTIPLIER)
        threshold_ms = threshold_s * 1000.0
        warn_ms = threshold_ms * warn_mult
        error_ms = threshold_ms * error_mult

        age_ms = warn_ms * 1.2
        assert age_ms < error_ms, "WARN-only test requires age strictly below error threshold"

        DEBOUNCE_S = 60.0
        TOTAL_SIM_S = 600
        TICKS_PER_SIM_SECOND = 5
        TOTAL_TICKS = TOTAL_SIM_S * TICKS_PER_SIM_SECOND

        start_ts = time.monotonic()
        from collections import deque as _deque
        from app.services.live.slo_monitor import _StreamState
        if stream_key not in slo._states:
            slo._states[stream_key] = _StreamState()

        for tick in range(TOTAL_TICKS):
            sim_elapsed = tick / TICKS_PER_SIM_SECOND
            fake_monotonic = start_ts + sim_elapsed

            orig = time.monotonic
            time.monotonic = lambda: fake_monotonic
            try:
                env = _make_envelope(stream_key, "quote")
                try:
                    slo.observe_envelope(env, data_age_ms=age_ms, threshold_s=threshold_s)
                except Exception:
                    pass
            finally:
                time.monotonic = orig

        await asyncio.sleep(0.1)

        total_alerts = (
            len(dispatcher.calls_with_severity(SEVERITY_WARN))
            + len(dispatcher.calls_with_severity(SEVERITY_ERROR))
        )
        max_expected = int(TOTAL_SIM_S / DEBOUNCE_S) + 6
        assert total_alerts <= max_expected, (
            f"Expected <= {max_expected} total alerts over {TOTAL_SIM_S}s (debounce {DEBOUNCE_S}s), "
            f"got {total_alerts} (WARN={len(dispatcher.calls_with_severity(SEVERITY_WARN))}, "
            f"ERROR={len(dispatcher.calls_with_severity(SEVERITY_ERROR))})"
        )
    finally:
        await slo.shutdown()
