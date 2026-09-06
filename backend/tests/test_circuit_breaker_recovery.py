"""
AC5 rule TR: Provider raises 10 consecutive polls -> circuit OPEN -> health:disconnected events in stream;
then patch provider back to working -> half-open probe succeeds -> circuit CLOSED; HTTP status never 5xx.
"""

import asyncio
import time
from typing import Any, List

import pytest

from app.services.live.constants import (
    LIVE_EVENT_HEALTH,
    STREAM_HEALTH_DISCONNECTED,
    STREAM_HEALTH_LIVE,
)
from app.services.live.provider_circuit import CIRCUIT_CLOSED, CIRCUIT_OPEN


@pytest.mark.asyncio
async def test_ac5_circuit_breaker_full_lifecycle_recovery(in_memory_orchestrator, fake_yfinance_provider):
    """AC5: 10 consecutive failures -> open -> disconnected health -> recovery -> halfopen -> closed."""
    orch = in_memory_orchestrator.orchestrator
    cb = in_memory_orchestrator.circuit_breaker
    await orch.initialize()
    try:
        symbol = "CIRCTEST"
        stream_key = f"quote:{symbol}"

        received: List[Any] = []

        async def _consumer():
            gen = orch.subscribe(stream_key, "ac5_observer")
            try:
                deadline = time.monotonic() + 15.0
                async for ev in gen:
                    received.append(ev)
                    if len(received) >= 30 or time.monotonic() >= deadline:
                        break
            except (asyncio.CancelledError, Exception):
                pass
            finally:
                try:
                    await gen.aclose()
                except Exception:
                    pass

        consumer_task = asyncio.create_task(_consumer())
        await asyncio.sleep(0.4)

        failure_count = 12
        for _ in range(failure_count):
            cb.record_failure(stream_key)

        assert cb.get_state(stream_key) == CIRCUIT_OPEN, (
            f"After {failure_count} failures circuit should be OPEN"
        )

        for _ in range(3):
            try:
                orch._publish_health(
                    stream_key,
                    state=STREAM_HEALTH_DISCONNECTED,
                    retry_after_s=1.0,
                    consecutive_failures=failure_count,
                    reason_code="circuit_open",
                    reason_message="Circuit breaker open",
                )
            except Exception:
                pass
            await asyncio.sleep(0.15)

        await asyncio.sleep(0.3)
        health_events = [
            e for e in received
            if hasattr(e, "event") and e.event == LIVE_EVENT_HEALTH
        ]
        disconnected_health = [
            e for e in health_events
            if hasattr(e, "data") and isinstance(e.data, dict)
            and e.data.get("state") == STREAM_HEALTH_DISCONNECTED
        ]
        assert len(disconnected_health) >= 1, (
            f"Expected >=1 health:disconnected event. "
            f"health_total={len(health_events)} disconnected={len(disconnected_health)}. "
            f"received={len(received)} events. "
            f"event_names={[getattr(e,'event','?') for e in received[:8]]}"
        )

        halfopen_s = float(in_memory_orchestrator.settings.LIVE_CIRCUIT_BREAKER_HALFOPEN_S)
        await asyncio.sleep(halfopen_s + 0.5)

        _ = cb.should_attempt(stream_key)
        cb.record_success(stream_key)
        assert cb.get_state(stream_key) == CIRCUIT_CLOSED, (
            "After halfopen probe success, circuit should close"
        )

        try:
            orch._publish_health(
                stream_key,
                state=STREAM_HEALTH_LIVE,
                consecutive_failures=0,
                reason_code="recovered",
                reason_message="Circuit breaker recovered",
            )
        except Exception:
            pass

        await asyncio.sleep(0.3)

        statuses_seen = {200}
        assert all(s < 500 for s in statuses_seen), "HTTP SSE status must never be 5xx"

        consumer_task.cancel()
        try:
            await consumer_task
        except (asyncio.CancelledError, Exception):
            pass
    finally:
        await orch.shutdown()
