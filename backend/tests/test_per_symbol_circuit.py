"""
TR2.3 — 5 failures trip open, half-open after halfopen_s, success resets.
TR2.4 — 1000 backoff samples uniform within +/-15% and never exceed cap.
"""

import time

import pytest

from app.services.live.provider_circuit import (
    CIRCUIT_CLOSED,
    CIRCUIT_HALF_OPEN,
    CIRCUIT_OPEN,
    PerSymbolCircuitBreaker,
    exponential_backoff_with_jitter,
)


def test_tr2_3_5_consecutive_failures_trip_open():
    """5 consecutive record_failure -> state becomes open."""
    cb = PerSymbolCircuitBreaker(failure_threshold=5, halfopen_s=5.0)
    for i in range(4):
        cb.record_failure("AAPL")
        assert cb.get_state("AAPL") == CIRCUIT_CLOSED, (
            f"Should remain closed on failure #{i+1}"
        )
    cb.record_failure("AAPL")
    assert cb.get_state("AAPL") == CIRCUIT_OPEN


def test_tr2_3_half_open_after_halfopen_s():
    """After halfopen_s seconds, state transitions to half_open."""
    halfopen_s = 0.2
    cb = PerSymbolCircuitBreaker(failure_threshold=2, halfopen_s=halfopen_s)
    cb.record_failure("MSFT")
    cb.record_failure("MSFT")
    assert cb.get_state("MSFT") == CIRCUIT_OPEN
    assert cb.should_attempt("MSFT") is False
    time.sleep(halfopen_s + 0.05)
    assert cb.should_attempt("MSFT") is True
    assert cb.get_state("MSFT") == CIRCUIT_HALF_OPEN


def test_tr2_3_success_resets_to_closed():
    """1 record_success from half_open -> closed."""
    cb = PerSymbolCircuitBreaker(failure_threshold=2, halfopen_s=0.1)
    cb.record_failure("GOOG")
    cb.record_failure("GOOG")
    assert cb.get_state("GOOG") == CIRCUIT_OPEN
    time.sleep(0.15)
    _ = cb.should_attempt("GOOG")
    assert cb.get_state("GOOG") == CIRCUIT_HALF_OPEN
    cb.record_success("GOOG")
    assert cb.get_state("GOOG") == CIRCUIT_CLOSED


def test_tr2_3_halfopen_failure_reopens():
    """Half-open failure -> open again for full halfopen_s."""
    halfopen_s = 0.15
    cb = PerSymbolCircuitBreaker(failure_threshold=2, halfopen_s=halfopen_s)
    cb.record_failure("NFLX")
    cb.record_failure("NFLX")
    time.sleep(halfopen_s + 0.02)
    _ = cb.should_attempt("NFLX")
    assert cb.get_state("NFLX") == CIRCUIT_HALF_OPEN
    cb.record_failure("NFLX")
    assert cb.get_state("NFLX") == CIRCUIT_OPEN
    assert cb.should_attempt("NFLX") is False


def test_tr2_4_backoff_1000_samples_within_range_and_cap():
    """1000 samples: all within [raw*(1-0.15), raw*(1+0.15)] and <= cap."""
    n = 1000
    cap_s = 60.0
    base_s = 1.0
    samples = [
        exponential_backoff_with_jitter(
            attempt=5, base_s=base_s, cap_s=cap_s, jitter_ratio=0.15
        )
        for _ in range(n)
    ]
    raw = base_s * (2 ** 5)
    raw_capped = min(raw, cap_s)
    lower = raw_capped * (1 - 0.15)
    upper = raw_capped * (1 + 0.15)
    in_range = [s for s in samples if lower <= s <= upper]
    assert len(in_range) == n, (
        f"Expected all samples within [{lower:.4f}, {upper:.4f}], "
        f"but {n - len(in_range)} out of {n} were outside"
    )
    over_cap = [s for s in samples if s > cap_s + 1e-9]
    assert over_cap == [], f"Found samples exceeding cap {cap_s}: {over_cap[:5]}"
    under_zero = [s for s in samples if s < 0]
    assert under_zero == [], f"Found negative samples: {under_zero[:5]}"
    assert max(samples) <= cap_s
    assert min(samples) >= 0


def test_tr2_4_backoff_cap_enforced_at_high_attempts():
    """Even at attempt 100, backoff never exceeds cap_s."""
    cap_s = 2.0
    samples = [
        exponential_backoff_with_jitter(
            attempt=100, base_s=1.0, cap_s=cap_s, jitter_ratio=0.15
        )
        for _ in range(200)
    ]
    assert all(s <= cap_s for s in samples), (
        f"max={max(samples)} exceeds cap={cap_s}"
    )
