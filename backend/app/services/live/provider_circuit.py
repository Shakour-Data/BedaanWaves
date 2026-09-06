"""
Per-Symbol Circuit Breaker + Exponential Backoff with Jitter.

Implements a three-state (closed/open/half-open) circuit breaker per
stream key, plus a capped exponential backoff helper with uniform jitter
to prevent thundering herd on provider recovery.
"""

from __future__ import annotations

import logging
import math
import random
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, Optional

logger = logging.getLogger(__name__)

CIRCUIT_CLOSED = "closed"
CIRCUIT_OPEN = "open"
CIRCUIT_HALF_OPEN = "half_open"

StateChangeCallback = Callable[[str, str, str], None]


@dataclass
class _CircuitState:
    """Per-key circuit internal state."""

    failures: int = 0
    state: str = CIRCUIT_CLOSED
    open_until_ts: float = 0.0
    last_change_ts: float = 0.0
    consecutive_good: int = 0


def exponential_backoff_with_jitter(
    attempt: int,
    base_s: float,
    cap_s: float,
    jitter_ratio: float = 0.15,
) -> float:
    """
    Exponential backoff with uniform jitter.

    Args:
        attempt: 0-based consecutive failure count.
        base_s: base delay in seconds.
        cap_s: maximum delay in seconds (hard cap).
        jitter_ratio: fraction of the raw delay to use as jitter range.

    Returns:
        Sleep time in seconds, within [raw*(1-jitter), raw*(1+jitter)],
        never exceeding cap_s.
    """
    if attempt < 0:
        attempt = 0
    if base_s <= 0:
        base_s = 0.001
    if cap_s <= 0:
        cap_s = 60.0
    if jitter_ratio < 0:
        jitter_ratio = 0.0
    if jitter_ratio > 1.0:
        jitter_ratio = 1.0

    raw = base_s * (2 ** attempt)
    raw = min(raw, cap_s)
    spread = raw * jitter_ratio
    lower = max(0.0, raw - spread)
    upper = min(cap_s, raw + spread)
    if upper <= lower:
        return lower
    return random.uniform(lower, upper)


class PerSymbolCircuitBreaker:
    """
    Three-state circuit breaker keyed by arbitrary string stream keys.

    Transitions:
        closed  -- N consecutive failures --> open
        open    -- after halfopen_s       --> half_open
        half_open -- 1 success            --> closed
        half_open -- 1 failure            --> open (resets timer)
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        halfopen_s: float = 30.0,
        on_state_change: Optional[StateChangeCallback] = None,
    ) -> None:
        if failure_threshold < 1:
            failure_threshold = 1
        if halfopen_s <= 0:
            halfopen_s = 30.0
        self._failure_threshold = failure_threshold
        self._halfopen_s = float(halfopen_s)
        self._on_state_change = on_state_change
        self._states: Dict[str, _CircuitState] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def failure_threshold(self) -> int:
        return self._failure_threshold

    @property
    def halfopen_seconds(self) -> float:
        return self._halfopen_s

    def record_success(self, key: str) -> None:
        """Register a successful call for key."""
        state = self._get_or_create(key)
        state.failures = 0
        state.consecutive_good += 1
        if state.state in (CIRCUIT_OPEN, CIRCUIT_HALF_OPEN):
            self._transition(key, state, CIRCUIT_CLOSED)

    def record_failure(self, key: str) -> None:
        """Register a failed call for key."""
        state = self._get_or_create(key)
        state.failures += 1
        state.consecutive_good = 0
        if state.state == CIRCUIT_CLOSED:
            if state.failures >= self._failure_threshold:
                self._transition(key, state, CIRCUIT_OPEN)
        elif state.state == CIRCUIT_HALF_OPEN:
            self._transition(key, state, CIRCUIT_OPEN)

    def should_attempt(self, key: str) -> bool:
        """Return True if a caller is allowed to attempt a call for key."""
        state = self._get_or_create(key)
        if state.state == CIRCUIT_CLOSED:
            return True
        if state.state == CIRCUIT_OPEN:
            if time.monotonic() >= state.open_until_ts:
                self._transition(key, state, CIRCUIT_HALF_OPEN)
                return True
            return False
        # half_open
        return True

    def get_state(self, key: str) -> str:
        """Return the current state for key (performs transition checks)."""
        state = self._get_or_create(key)
        if state.state == CIRCUIT_OPEN and time.monotonic() >= state.open_until_ts:
            self._transition(key, state, CIRCUIT_HALF_OPEN)
        return state.state

    def get_open_remaining_s(self, key: str) -> float:
        """Seconds until open state transitions to half_open (0 if not open)."""
        state = self._get_or_create(key)
        if state.state != CIRCUIT_OPEN:
            return 0.0
        remaining = state.open_until_ts - time.monotonic()
        return max(0.0, remaining)

    def snapshot(self) -> Dict[str, Dict[str, object]]:
        """Return a serializable snapshot of all tracked keys."""
        out: Dict[str, Dict[str, object]] = {}
        for key, st in list(self._states.items()):
            out[key] = {
                "state": st.state,
                "failures": st.failures,
                "consecutive_good": st.consecutive_good,
                "open_remaining_s": max(0.0, st.open_until_ts - time.monotonic())
                if st.state == CIRCUIT_OPEN else 0.0,
                "last_change_ts": st.last_change_ts,
            }
        return out

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_or_create(self, key: str) -> _CircuitState:
        state = self._states.get(key)
        if state is None:
            state = _CircuitState(last_change_ts=time.monotonic())
            self._states[key] = state
        return state

    def _transition(self, key: str, state: _CircuitState, new_state: str) -> None:
        old = state.state
        if old == new_state:
            return
        state.state = new_state
        state.last_change_ts = time.monotonic()
        if new_state == CIRCUIT_OPEN:
            state.open_until_ts = time.monotonic() + self._halfopen_s
        elif new_state == CIRCUIT_HALF_OPEN:
            state.open_until_ts = 0.0
        else:  # closed
            state.open_until_ts = 0.0
            state.failures = 0
        logger.info(
            "Circuit transition key=%s old=%s new=%s failures=%d",
            key, old, new_state, state.failures,
        )
        if self._on_state_change is not None:
            try:
                self._on_state_change(key, old, new_state)
            except Exception as exc:  # pragma: no cover - defensive
                logger.error("Circuit on_state_change hook failed: %s", exc)
