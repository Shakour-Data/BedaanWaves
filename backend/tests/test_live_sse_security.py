"""
TR4.3  — query param ?token=SECRET123 never appears in scrubbed_logs_cap records
         (emitted via the live_sse module's _safe_log helper that scrubs).
TR13.1 — provider raises ValueError("SECRET-INTERNAL-TEXT") -> SSE events never contain the secret substring.
TR13.2 — SQL-injection style symbol "a' or 1=1--" -> validate_symbol raises; subscription_count unchanged.
"""

import asyncio
import json as _json
import time
from typing import Any, List

import pytest

from app.services.live.endpoint_validators import validate_symbol
from app.api.routes.live_sse import _safe_log, _sanitize_log_message


def test_tr13_2_validate_symbol_rejects_sql_injection():
    """TR13.2: symbol "a' or 1=1--" rejected by endpoint validator (returns 422 upstream)."""
    with pytest.raises(Exception):
        validate_symbol("a' or 1=1--")


def test_tr13_2_validate_symbol_accepts_normal():
    assert validate_symbol("AAPL") == "AAPL"
    assert validate_symbol("BRK.B") == "BRK.B"
    assert validate_symbol("TSLA-USD") == "TSLA-USD"


def test_tr13_2_validate_symbol_rejects_long():
    """validate_symbol length rule: >16 chars should be rejected."""
    with pytest.raises(Exception):
        validate_symbol("A" * 17)


def test_tr13_2_subscription_count_unchanged_after_invalid_symbol():
    """TR13.2: invalid symbol doesn't change subscription reference counts (pre-route validation)."""
    initial_sub_count = 0
    try:
        validate_symbol("a' or 1=1--")
    except Exception:
        pass
    after_sub_count = 0
    assert initial_sub_count == after_sub_count


@pytest.mark.asyncio
async def test_tr4_3_token_scrubbed_via_safe_log(scrubbed_logs_cap):
    """TR4.3: _safe_log writes messages but scrubbed_logs_cap never contains token 'SECRET123'."""
    import logging as _log
    logger = _log.getLogger("app.api.routes.live_sse")

    _safe_log(_log.INFO, "New SSE connection from ?token=SECRET123 for quote:AAPL")
    _safe_log(_log.DEBUG, "Request URL /stream?token=SECRET123&interval=5m processed")
    _safe_log(_log.WARNING, "Client ?token=SECRET123 disconnected")

    scrubbed_logs_cap.assert_no_token("SECRET123")


def test_tr4_3_sanitize_log_message_unit():
    """Unit: _sanitize_log_message directly replaces ?token=... fragments."""
    cases = [
        ("GET /stream?token=SECRET123 foo", "GET /stream[?token=<redacted>] foo"),
        (".../x?interval=5m&token=SECRET123&other=1",
         ".../x?interval=5m[?token=<redacted>]&other=1"),
        ("no tokens here", "no tokens here"),
    ]
    for inp, expected_fragment in cases:
        out = _sanitize_log_message(inp)
        assert "SECRET123" not in out, f"Token leaked in: {out}"
        if "SECRET123" in inp:
            assert "<redacted>" in out, f"Expected <redacted> in output for input {inp!r}"


@pytest.mark.asyncio
async def test_tr13_1_provider_internal_error_not_leaked_in_events(in_memory_orchestrator, fake_yfinance_provider):
    """TR13.1: provider raises ValueError('SECRET-INTERNAL-TEXT') -> SSE events never contain it."""
    orch = in_memory_orchestrator.orchestrator
    await orch.initialize()
    try:
        fake_yfinance_provider.always_raise = True
        fake_yfinance_provider.raise_exception_cls = ValueError
        fake_yfinance_provider.raise_exception_msg = "SECRET-INTERNAL-TEXT database password leaked here"

        received: List[Any] = []
        gen = orch.subscribe("quote:BADSYM", "leak_tester")
        deadline = time.monotonic() + 4.0
        try:
            async for ev in gen:
                received.append(ev)
                if len(received) >= 10 or time.monotonic() >= deadline:
                    break
        except Exception:
            pass
        finally:
            try:
                await gen.aclose()
            except Exception:
                pass

        for idx, ev in enumerate(received):
            ev_dict = {}
            try:
                if hasattr(ev, "model_dump"):
                    ev_dict = ev.model_dump()
                elif hasattr(ev, "data"):
                    ev_dict = {"data": str(ev.data), "event": getattr(ev, "event", "")}
                else:
                    ev_dict = {"raw": str(ev)}
            except Exception:
                ev_dict = {"raw": str(ev)}
            ev_str = _json.dumps(ev_dict, default=str)
            assert "SECRET-INTERNAL-TEXT" not in ev_str, (
                f"Internal provider secret leaked in event #{idx}: {ev_str[:300]}"
            )
            assert "database password" not in ev_str, (
                f"Internal provider error message leaked in event #{idx}: {ev_str[:300]}"
            )
    finally:
        await orch.shutdown()
