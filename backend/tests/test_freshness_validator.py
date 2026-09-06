"""
TR2.1 — Freshness boundary matrix (quote) market open+closed.
TR2.2 — Intraday monotonic check: decreasing timestamps rejected.
"""

import datetime as _dt
from datetime import datetime, timezone
from typing import Any, Dict

import pytest

from app.services.live.freshness_validator import (
    ERRORS,
    RULE_FRESHNESS,
    RULE_INTRADAY_MONOTONIC,
    RULE_NON_NULL_PRICE,
    RULE_OHLC_CONSISTENCY,
    VALIDATED,
    FreshnessValidator,
)


class _AlwaysOpen:
    def get_market_status(self):
        return {"status": "regular", "is_trading": True, "freshness_label": "Live"}


class _AlwaysClosed:
    def get_market_status(self):
        return {"status": "closed", "is_trading": False, "freshness_label": "Closed"}


def _quote_payload(freshness_ts: datetime, **overrides: Any) -> Dict[str, Any]:
    base: Dict[str, Any] = {
        "symbol": "AAPL",
        "current_price": 100.0,
        "change_value": 0.5,
        "change_percent": 0.5,
        "open": 99.5,
        "high": 101.0,
        "low": 99.0,
        "previous_close": 99.5,
        "volume": 10000,
        "adjusted_close": 100.0,
        "freshness_ts": freshness_ts,
    }
    base.update(overrides)
    return base


def _make_validator(market_hours, *, open_s=120, closed_s=900):
    from app.core.config import Settings

    s = Settings(
        SECRET_KEY="x" * 32,
        JWT_SECRET="y" * 32,
    )
    object.__setattr__(s, "LIVE_MAX_QUOTE_AGE_OPEN_S", open_s)
    object.__setattr__(s, "LIVE_MAX_QUOTE_AGE_CLOSED_S", closed_s)
    object.__setattr__(s, "LIVE_SLO_WARN_MULTIPLIER", 1.5)
    object.__setattr__(s, "LIVE_SLO_ERROR_MULTIPLIER", 3.0)
    return FreshnessValidator(market_hours=market_hours, settings=s)


@pytest.mark.parametrize(
    "market_open,age_s,expect_pass",
    [
        (True, 119, True),
        (True, 121, False),
        (False, 899, True),
        (False, 901, False),
    ],
)
def test_tr2_1_freshness_boundary_matrix(market_open, age_s, expect_pass):
    """Freshness boundaries at 119/121 (open) and 899/901 (closed)."""
    mh = _AlwaysOpen() if market_open else _AlwaysClosed()
    v = _make_validator(mh)
    now = datetime.now(timezone.utc)
    fts = now - _dt.timedelta(seconds=age_s)
    result = v.validate_quote("AAPL", _quote_payload(freshness_ts=fts))
    if expect_pass:
        assert result.get(VALIDATED) is True, (
            f"Expected pass at age_s={age_s} open={market_open} "
            f"but got errors: {result.get(ERRORS)}"
        )
        assert result["data"]["stale"] is False
    else:
        assert result.get(VALIDATED) is True
        assert result["data"]["stale"] is True


def test_tr2_1_null_price_rule_violated():
    """Null current_price -> rejected with rule_violated=non_null_price."""
    v = _make_validator(_AlwaysOpen())
    now = datetime.now(timezone.utc)
    p = _quote_payload(freshness_ts=now)
    p["current_price"] = None
    result = v.validate_quote("AAPL", p)
    assert result.get(VALIDATED) is False
    errs = result.get(ERRORS) or []
    codes = [e.get("rule_violated") for e in errs]
    assert RULE_NON_NULL_PRICE in codes


def test_tr2_1_high_less_than_low_violated():
    """high < low -> rejected with rule_violated=ohlc_consistency."""
    v = _make_validator(_AlwaysOpen())
    now = datetime.now(timezone.utc)
    p = _quote_payload(freshness_ts=now, high=95.0, low=100.0)
    result = v.validate_quote("AAPL", p)
    assert result.get(VALIDATED) is False
    errs = result.get(ERRORS) or []
    codes = [e.get("rule_violated") for e in errs]
    assert RULE_OHLC_CONSISTENCY in codes


def test_tr2_2_intraday_non_monotonic_rejected():
    """Two bars with decreasing timestamps for same symbol -> second rejected."""
    v = _make_validator(_AlwaysOpen())
    now = datetime.now(timezone.utc)
    ts1 = now - _dt.timedelta(minutes=5)
    ts2 = now - _dt.timedelta(minutes=2)

    payload_ok = {
        "symbol": "AAPL",
        "interval": "5m",
        "candles": [
            {"timestamp": ts1, "open": 100, "high": 101, "low": 99, "close": 100.5,
             "adjusted_close": 100.5, "volume": 1000},
            {"timestamp": ts2, "open": 100, "high": 102, "low": 99.5, "close": 101.5,
             "adjusted_close": 101.5, "volume": 1000},
        ],
        "freshness_ts": now,
    }
    r1 = v.validate_intraday("AAPL", "5m", payload_ok)
    assert r1.get(VALIDATED) is True, f"First set should pass: {r1.get(ERRORS)}"

    payload_bad = {
        "symbol": "AAPL",
        "interval": "5m",
        "candles": [
            {"timestamp": ts2, "open": 101, "high": 103, "low": 100, "close": 102,
             "adjusted_close": 102, "volume": 1000},
        ],
        "freshness_ts": now,
    }
    r2 = v.validate_intraday("AAPL", "5m", payload_bad)
    assert r2.get(VALIDATED) is False
    errs = r2.get(ERRORS) or []
    codes = [e.get("rule_violated") for e in errs]
    assert RULE_INTRADAY_MONOTONIC in codes
