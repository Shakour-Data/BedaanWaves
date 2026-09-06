"""
TR1.2 — Schemas validate and serialize strictly.

- Payload round-trip JSON preserves fields.
- stale defaults False (not True).
- Non-UTC timestamp coerced to UTC.
"""

import json
from datetime import datetime, timezone

import pytest

from app.services.live.models import (
    LiveEventEnvelope,
    LiveHealthPayload,
    LiveIntradayCandle,
    LiveIntradayPayload,
    LiveMarketPulsePayload,
    LiveNewsPayload,
    LivePingPayload,
    LiveQuotePayload,
    LiveScoreDeltaPayload,
)


def _utc(ts: str) -> datetime:
    return datetime.fromisoformat(ts).replace(tzinfo=timezone.utc)


def test_tr1_2_stale_defaults_false():
    """Every payload type: stale defaults to False when omitted."""
    now = datetime.now(timezone.utc)
    q = LiveQuotePayload(
        symbol="AAPL",
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
    assert q.stale is False

    mp = LiveMarketPulsePayload(
        active_symbols=0,
        symbol_count=0,
        freshness_ts=now,
    )
    assert mp.stale is False

    pp = LivePingPayload(freshness_ts=now)
    assert pp.stale is False


def test_tr1_2_quote_json_roundtrip_preserves_fields():
    """LiveQuotePayload: JSON roundtrip preserves types and values."""
    now = datetime.now(timezone.utc)
    original = LiveQuotePayload(
        symbol="AAPL",
        current_price=180.42,
        change_value=2.3,
        change_percent=1.29,
        open=178.0,
        high=181.0,
        low=177.5,
        previous_close=178.12,
        volume=12345678,
        adjusted_close=180.42,
        freshness_ts=now,
        stale=False,
    )
    j = original.model_dump_json()
    restored = LiveQuotePayload.model_validate_json(j)
    assert restored.symbol == "AAPL"
    assert restored.current_price == pytest.approx(180.42)
    assert restored.volume == 12345678
    assert restored.freshness_ts == original.freshness_ts
    assert restored.stale is False
    assert restored.data_age_ms is not None
    assert restored.data_age_ms >= 0


def test_tr1_2_non_utc_timestamp_coerced_to_utc():
    """Non-UTC-aware datetime is coerced to UTC by field_validator."""
    naive = datetime(2026, 9, 6, 12, 0, 0)
    payload = LiveQuotePayload(
        symbol="MSFT",
        current_price=1.0,
        change_value=0.0,
        change_percent=0.0,
        open=1.0,
        high=1.0,
        low=1.0,
        previous_close=1.0,
        volume=0,
        freshness_ts=naive,
    )
    assert payload.freshness_ts.tzinfo is not None
    assert payload.freshness_ts.utcoffset().total_seconds() == 0


def test_tr1_2_intraday_monotonic_candles_roundtrip():
    """LiveIntradayPayload: multiple candles with monotonic timestamps OK."""
    now = datetime.now(timezone.utc)
    candles = [
        LiveIntradayCandle(
            timestamp=now.replace(minute=(now.minute - 5 + i) % 60),
            open=100.0 + i,
            high=101.0 + i,
            low=99.0 + i,
            close=100.5 + i,
            adjusted_close=100.5 + i,
            volume=1000,
        )
        for i in range(3)
    ]
    p = LiveIntradayPayload(
        symbol="NVDA",
        interval="5m",
        candles=candles,
        freshness_ts=now,
    )
    j = p.model_dump_json()
    p2 = LiveIntradayPayload.model_validate_json(j)
    assert len(p2.candles) == 3
    assert p2.symbol == "NVDA"
    assert p2.interval == "5m"


def test_tr1_2_envelope_event_enum_restricted():
    """LiveEventEnvelope rejects invalid event name."""
    with pytest.raises(Exception):
        LiveEventEnvelope(
            event="not_a_real_event",
            data={},
            sequence=1,
            stream_key="quote:AAPL",
        )


def test_tr1_2_health_payload_validates_state_enum():
    """LiveHealthPayload rejects invalid stream health state."""
    now = datetime.now(timezone.utc)
    with pytest.raises(Exception):
        LiveHealthPayload(
            stream_key="quote:AAPL",
            state="totally_broken",
            consecutive_failures=1,
            freshness_ts=now,
        )


def test_tr1_2_iso_string_freshness_ts_coerced():
    """freshness_ts given as ISO string is coerced via validator."""
    p = LiveQuotePayload(
        symbol="TSLA",
        current_price=250.0,
        change_value=0.0,
        change_percent=0.0,
        open=250.0,
        high=250.0,
        low=250.0,
        previous_close=250.0,
        volume=1,
        freshness_ts="2026-09-06T12:00:00Z",
    )
    assert isinstance(p.freshness_ts, datetime)
    assert p.freshness_ts.tzinfo is not None
