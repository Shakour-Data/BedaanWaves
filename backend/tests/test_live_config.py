"""
TR1.1 — Config values available with sane defaults + env overrides.
"""

import os

import pytest

from app.core.config import Settings


LIVE_KEYS_DEFAULTS = {
    "LIVE_POLL_INTERVAL_OPEN_S": 4,
    "LIVE_POLL_INTERVAL_CLOSED_S": 30,
    "LIVE_INTRADAY_POLL_INTERVAL_OPEN_S": 15,
    "LIVE_PING_INTERVAL_S": 10,
    "LIVE_IDLE_UNSUBSCRIBE_S": 60,
    "LIVE_MAX_QUOTE_AGE_OPEN_S": 120,
    "LIVE_MAX_QUOTE_AGE_CLOSED_S": 900,
    "LIVE_CIRCUIT_BREAKER_FAILURES": 5,
    "LIVE_CIRCUIT_BREAKER_HALFOPEN_S": 30,
    "LIVE_POLL_EXECUTOR_MAX": 8,
    "LIVE_BACKOFF_BASE_S": 1.0,
    "LIVE_BACKOFF_MAX_S": 60.0,
    "LIVE_SLO_WARN_MULTIPLIER": 1.5,
    "LIVE_SLO_ERROR_MULTIPLIER": 3.0,
}


def test_tr1_1_all_14_live_settings_present_with_defaults():
    """All 14 LIVE_* settings present and match documented defaults."""
    s = Settings(
        SECRET_KEY="x" * 32,
        JWT_SECRET="y" * 32,
    )
    assert len(LIVE_KEYS_DEFAULTS) == 14
    for key, default in LIVE_KEYS_DEFAULTS.items():
        assert hasattr(s, key), f"Missing setting: {key}"
        actual = getattr(s, key)
        assert type(actual) == type(default), (
            f"Type mismatch {key}: expected {type(default).__name__}, "
            f"got {type(actual).__name__}"
        )
        assert actual == default, (
            f"Wrong default for {key}: expected {default}, got {actual}"
        )


def test_tr1_1_env_override_honored_int(monkeypatch):
    """Integer env overrides coerced and honored."""
    monkeypatch.setenv("LIVE_POLL_INTERVAL_OPEN_S", "99")
    monkeypatch.setenv("LIVE_CIRCUIT_BREAKER_FAILURES", "12")
    monkeypatch.setenv("SECRET_KEY", "x" * 32)
    monkeypatch.setenv("JWT_SECRET", "y" * 32)
    s = Settings()
    assert s.LIVE_POLL_INTERVAL_OPEN_S == 99
    assert s.LIVE_CIRCUIT_BREAKER_FAILURES == 12


def test_tr1_1_env_override_honored_float(monkeypatch):
    """Float env overrides coerced and honored."""
    monkeypatch.setenv("LIVE_SLO_WARN_MULTIPLIER", "2.25")
    monkeypatch.setenv("LIVE_BACKOFF_MAX_S", "120.5")
    monkeypatch.setenv("SECRET_KEY", "x" * 32)
    monkeypatch.setenv("JWT_SECRET", "y" * 32)
    s = Settings()
    assert s.LIVE_SLO_WARN_MULTIPLIER == 2.25
    assert s.LIVE_BACKOFF_MAX_S == 120.5
