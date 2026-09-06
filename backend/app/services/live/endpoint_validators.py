"""
Input validators shared by the SSE + snapshot live endpoints.

Pure helpers that return FastAPI-compatible HTTP 422 responses for
invalid symbols, intervals, or other query parameters.
"""

from __future__ import annotations

import re

from fastapi import HTTPException

from app.services.live.constants import (
    SYMBOL_ALLOWED_CHARSET,
    SYMBOL_MAX_LENGTH,
    VALID_INTRADAY_INTERVALS,
)

_SYMBOL_RE = re.compile(r"^[A-Z0-9.\-]+$")


def validate_symbol(symbol: str, param_name: str = "symbol") -> str:
    """
    Validate and uppercase a stock symbol.

    Raises HTTPException 422 with structured detail if the symbol exceeds
    SYMBOL_MAX_LENGTH or contains characters outside SYMBOL_ALLOWED_CHARSET.
    """
    if not symbol or not isinstance(symbol, str):
        raise HTTPException(
            status_code=422,
            detail={
                "loc": ["path", param_name],
                "msg": f"{param_name} is required and must be a non-empty string",
                "type": "value_error.missing",
            },
        )
    sym = symbol.strip().upper()
    if len(sym) > SYMBOL_MAX_LENGTH:
        raise HTTPException(
            status_code=422,
            detail={
                "loc": ["path", param_name],
                "msg": (
                    f"{param_name} exceeds max length of {SYMBOL_MAX_LENGTH} "
                    f"(got {len(sym)})"
                ),
                "type": "string_too_long",
                "ctx": {"max_length": SYMBOL_MAX_LENGTH},
            },
        )
    if not sym:
        raise HTTPException(
            status_code=422,
            detail={
                "loc": ["path", param_name],
                "msg": f"{param_name} must not be empty",
                "type": "value_error.empty",
            },
        )
    if not _SYMBOL_RE.match(sym):
        bad = sorted({c for c in sym if c not in SYMBOL_ALLOWED_CHARSET})
        raise HTTPException(
            status_code=422,
            detail={
                "loc": ["path", param_name],
                "msg": (
                    f"{param_name} contains disallowed characters; "
                    f"allowed charset: A-Z 0-9 - . (discovered: {bad!r})"
                ),
                "type": "value_error.strpattern",
                "ctx": {"allowed": "".join(sorted(SYMBOL_ALLOWED_CHARSET))},
            },
        )
    return sym


def validate_interval(interval: str | None) -> str:
    """
    Validate intraday interval against VALID_INTRADAY_INTERVALS.

    Defaults to "5m" when absent. Raises 422 if not in the allow-list.
    """
    if interval is None:
        return "5m"
    iv = str(interval).strip().lower()
    if iv not in VALID_INTRADAY_INTERVALS:
        raise HTTPException(
            status_code=422,
            detail={
                "loc": ["query", "interval"],
                "msg": (
                    f"interval must be one of {sorted(VALID_INTRADAY_INTERVALS)} "
                    f"(got {interval!r})"
                ),
                "type": "enum",
                "ctx": {"allowed": sorted(VALID_INTRADAY_INTERVALS)},
            },
        )
    return iv


def validate_scope(scope: str | None, allowed: set, default: str) -> str:
    """Validate a scope query parameter against an allow-list."""
    if scope is None:
        return default
    s = str(scope).strip().upper()
    if s not in allowed:
        raise HTTPException(
            status_code=422,
            detail={
                "loc": ["query", "scope"],
                "msg": f"scope must be one of {sorted(allowed)} (got {scope!r})",
                "type": "enum",
                "ctx": {"allowed": sorted(allowed)},
            },
        )
    return s
