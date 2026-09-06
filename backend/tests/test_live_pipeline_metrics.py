"""
TR5.1 — Emit 100 events through record_poll: 80 pass (emitted=1 each) + 20 fail (validation_dropped=1 each)
-> exactly sum of messages_emitted=80, messages_dropped_validation_total=20 per stream.
"""

import time
from typing import Any

import pytest

from app.services.live.pipeline_metrics import LivePipelineMetrics


def test_tr5_1_emitted_dropped_counters_exact():
    """TR5.1: 100 polls, 8 pass validator (emit 1 each), 2 fail validator (dropped each) -> exactly metrics.emitted=8 dropped=2."""
    pm = LivePipelineMetrics()
    stream_key = "quote:TR5TEST"

    total_emitted_expected = 0
    total_dropped_expected = 0
    for i in range(100):
        if i < 80:
            pm.record_poll(
                stream_key=stream_key,
                symbol="TR5TEST",
                success=True,
                latency_ms=12.5 + (i * 0.1),
                messages_emitted=1,
                validation_dropped=0,
                data_age_ms=2000.0 + i,
                threshold_s=60.0,
            )
            total_emitted_expected += 1
        else:
            pm.record_poll(
                stream_key=stream_key,
                symbol="TR5TEST",
                success=True,
                latency_ms=10.0,
                messages_emitted=0,
                validation_dropped=1,
                data_age_ms=1500.0,
                threshold_s=60.0,
            )
            total_dropped_expected += 1

    snap = pm.snapshot()
    stream_info = snap["streams"].get(stream_key, {})

    counters = pm._streams.get(stream_key)
    assert counters is not None
    assert counters.messages_emitted_total == 80, (
        f"Expected 80 emitted, got {counters.messages_emitted_total}"
    )
    assert counters.messages_dropped_validation_total == 20, (
        f"Expected 20 dropped, got {counters.messages_dropped_validation_total}"
    )
    assert counters.poll_success_total == 100
    assert counters.poll_error_total == 0


def test_tr5_1_snapshot_slo_summary_integers():
    """snapshot() slo_summary.warn / error must be integers."""
    pm = LivePipelineMetrics()
    snap = pm.snapshot()
    slo = snap["slo_summary"]
    assert isinstance(slo["warn"], int), f"warn should be int, got {type(slo['warn'])}"
    assert isinstance(slo["error"], int), f"error should be int, got {type(slo['error'])}"


def test_tr5_1_snapshot_sse_clients_count_integer():
    """snapshot() sse_clients.count must be integer."""
    pm = LivePipelineMetrics()
    pm.register_sse_connection("conn-1", "quote:AAPL")
    snap = pm.snapshot()
    assert isinstance(snap["sse_clients"]["count"], int)
    assert snap["sse_clients"]["count"] == 1
