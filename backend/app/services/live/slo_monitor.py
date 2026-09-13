"""
SLO Monitor for the live data pipeline.

Maintains a sliding 30-second window of freshness-age samples per stream
key. Detects WARN (>1.5x threshold sustained), ERROR (>3x threshold or
gap >2min), debounces re-alerts to at least 60s apart, and recovers on
3 consecutive good ticks.

Dispatches system notifications (LIVE DATA: stream_key severity) through
the existing NotificationDispatcher service.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Deque, Dict, Optional, Tuple

from app.core.config import Settings, get_settings
from app.services.core.base_service import BaseService
from app.services.live.models import LiveEventEnvelope

logger = logging.getLogger(__name__)

_WINDOW_S = 30.0
_DEBOUNCE_S = 60.0
_GAP_ERROR_S = 120.0
_GOOD_TICKS_RECOVERY = 3

SEVERITY_WARN = "WARN"
SEVERITY_ERROR = "ERROR"
SEVERITY_RESOLVED = "RESOLVED"

CATEGORY_SYSTEM = "system"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class _StreamState:
    samples: Deque[Tuple[float, float]] = field(
        default_factory=lambda: deque(maxlen=4096)
    )
    current_severity: Optional[str] = None
    last_alert_ts: Dict[str, float] = field(default_factory=dict)
    consecutive_good: int = 0
    last_good_freshness_ts: Optional[float] = None
    last_seen_ts: float = 0.0
    known_threshold_s: Optional[float] = None


class SLOMonitor(BaseService):
    """
    Watches events emitted by LiveDataOrchestrator and raises/recovers
    SLO alerts via the notification dispatcher.
    """

    def __init__(
        self,
        notification_dispatcher: Any,
        settings: Optional[Settings] = None,
    ) -> None:
        super().__init__("SLOMonitor")
        self._settings = settings or get_settings()
        self._dispatcher = notification_dispatcher
        self._states: Dict[str, _StreamState] = {}
        self._shutdown_event: Optional[asyncio.Event] = None
        self._monitor_task: Optional[asyncio.Task] = None
        self._orchestrator: Any = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def initialize(self) -> None:
        self._shutdown_event = asyncio.Event()
        self._monitor_task = asyncio.create_task(self._periodic_tick())
        self.logger.info("SLOMonitor initialized")

    async def shutdown(self) -> None:
        if self._shutdown_event is not None:
            self._shutdown_event.set()
        if self._monitor_task is not None and not self._monitor_task.done():
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except (asyncio.CancelledError, Exception):
                pass
        self.logger.info("SLOMonitor shutdown")

    def bind_orchestrator(self, orchestrator: Any) -> None:
        """Expose orchestrator reference so we can read _last_emitted each tick."""
        self._orchestrator = orchestrator

    # ------------------------------------------------------------------
    # Public hook: feed from orchestrator envelope emission
    # ------------------------------------------------------------------

    def observe_envelope(
        self,
        envelope: LiveEventEnvelope,
        *,
        data_age_ms: Optional[float] = None,
        threshold_s: Optional[float] = None,
    ) -> None:
        """Register a single emitted envelope for SLO evaluation."""
        key = envelope.stream_key
        state = self._states.setdefault(key, _StreamState())
        state.last_seen_ts = time.monotonic()
        if threshold_s is not None:
            state.known_threshold_s = float(threshold_s)
        age_ms: float
        if data_age_ms is not None:
            age_ms = float(data_age_ms)
        else:
            data_payload = envelope.data or {}
            age_ms = float(data_payload.get("data_age_ms") or 0.0)
        state.samples.append((time.monotonic(), age_ms))
        thresh = state.known_threshold_s
        if thresh is not None:
            threshold_ms = thresh * 1000.0
            if age_ms <= threshold_ms:
                state.consecutive_good += 1
                state.last_good_freshness_ts = time.monotonic()
            else:
                state.consecutive_good = 0
        self._evaluate(key, state)

    # ------------------------------------------------------------------
    # Periodic evaluation + gap detection
    # ------------------------------------------------------------------

    async def _periodic_tick(self) -> None:
        assert self._shutdown_event is not None
        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(5.0)
                keys = list(self._states.keys())
                if self._orchestrator is not None:
                    for extra in getattr(self._orchestrator, "list_active_streams", lambda: [])():
                        if extra not in self._states:
                            self._states[extra] = _StreamState()
                    keys = list(self._states.keys())
                for key in keys:
                    state = self._states[key]
                    last_event_ts = getattr(
                        getattr(self._orchestrator, "_last_emitted", {}).get(key),
                        "last_event_ts",
                        0.0,
                    ) if self._orchestrator is not None else state.last_seen_ts
                    gap = time.monotonic() - max(state.last_seen_ts, last_event_ts)
                    if gap >= _GAP_ERROR_S and state.current_severity != SEVERITY_ERROR:
                        self._raise(
                            key, state, SEVERITY_ERROR,
                            reason=f"No fresh events for {gap:.0f}s (gap>{_GAP_ERROR_S:.0f}s)",
                            data_age_ms=None, threshold_s=state.known_threshold_s,
                            duration_s=gap,
                        )
                    self._evaluate(key, state)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                self.logger.error("SLOMonitor periodic tick error: %s", exc)

    # ------------------------------------------------------------------
    # Alert evaluation
    # ------------------------------------------------------------------

    def _evaluate(self, key: str, state: _StreamState) -> None:
        thresh = state.known_threshold_s
        if thresh is None:
            return
        threshold_ms = thresh * 1000.0
        warn_threshold_ms = threshold_ms * float(self._settings.LIVE_SLO_WARN_MULTIPLIER)
        error_threshold_ms = threshold_ms * float(self._settings.LIVE_SLO_ERROR_MULTIPLIER)

        now = time.monotonic()
        cutoff = now - _WINDOW_S
        warn_count = 0
        error_count = 0
        total = 0
        max_age = 0.0
        for sample_ts, age in reversed(state.samples):
            if sample_ts < cutoff:
                break
            total += 1
            max_age = max(max_age, age)
            if age >= error_threshold_ms:
                error_count += 1
                warn_count += 1
            elif age >= warn_threshold_ms:
                warn_count += 1

        if total == 0:
            return

        duration_s = min(_WINDOW_S, now - state.samples[0][0]) if state.samples else 0.0

        if error_count > 0:
            if state.current_severity == SEVERITY_ERROR:
                if state.consecutive_good >= _GOOD_TICKS_RECOVERY:
                    self._resolve(key, state, recovered_from=SEVERITY_ERROR)
                    return
            if state.current_severity != SEVERITY_ERROR:
                self._raise(
                    key, state, SEVERITY_ERROR,
                    reason=(
                        f"Data age max={max_age:.0f}ms exceeds "
                        f"{self._settings.LIVE_SLO_ERROR_MULTIPLIER:.1f}x threshold "
                        f"({error_threshold_ms:.0f}ms) over {duration_s:.0f}s window"
                    ),
                    data_age_ms=max_age, threshold_s=thresh,
                    duration_s=duration_s,
                )
            return
        if warn_count > 0:
            if state.current_severity == SEVERITY_ERROR:
                if state.consecutive_good >= _GOOD_TICKS_RECOVERY:
                    self._resolve(key, state, recovered_from=SEVERITY_ERROR)
            if state.current_severity not in (SEVERITY_ERROR, SEVERITY_WARN):
                self._raise(
                    key, state, SEVERITY_WARN,
                    reason=(
                        f"Data age max={max_age:.0f}ms exceeds "
                        f"{self._settings.LIVE_SLO_WARN_MULTIPLIER:.1f}x threshold "
                        f"({warn_threshold_ms:.0f}ms) over {duration_s:.0f}s window"
                    ),
                    data_age_ms=max_age, threshold_s=thresh,
                    duration_s=duration_s,
                )
            return
        if state.current_severity in (SEVERITY_WARN, SEVERITY_ERROR):
            if state.consecutive_good >= _GOOD_TICKS_RECOVERY:
                self._resolve(key, state, recovered_from=state.current_severity)

    # ------------------------------------------------------------------
    # Alert dispatch
    # ------------------------------------------------------------------

    def _raise(
        self,
        key: str,
        state: _StreamState,
        severity: str,
        *,
        reason: str,
        data_age_ms: Optional[float],
        threshold_s: Optional[float],
        duration_s: float,
    ) -> None:
        last = state.last_alert_ts.get(severity, 0.0)
        if time.monotonic() - last < _DEBOUNCE_S:
            return
        state.last_alert_ts[severity] = time.monotonic()
        state.current_severity = severity
        title = f"LIVE DATA: {key} {severity}"
        body_parts = [f"Stream {key} has reached {severity} SLO condition.", reason]
        if threshold_s is not None:
            body_parts.append(f"Configured SLO threshold: {threshold_s:.0f}s.")
        if data_age_ms is not None:
            body_parts.append(f"Current observed data age: {data_age_ms/1000.0:.1f}s.")
        if duration_s > 0:
            body_parts.append(f"Condition sustained for {duration_s:.0f}s.")
        body_parts.append("Please investigate upstream provider health and circuit state.")
        body = " ".join(body_parts)
        priority = "high" if severity == SEVERITY_ERROR else "medium"
        self.logger.warning(
            "SLO %s stream=%s severity=%s age_ms=%s threshold_s=%s",
            severity, key, severity, data_age_ms, threshold_s,
        )
        asyncio.create_task(self._dispatch(title, body, severity, priority))

    def _resolve(
        self,
        key: str,
        state: _StreamState,
        *,
        recovered_from: str,
    ) -> None:
        state.current_severity = None
        state.last_alert_ts.pop(recovered_from, None)
        title = f"LIVE DATA: {key} RESOLVED"
        body = (
            f"Stream {key} has recovered from the previous {recovered_from} SLO condition after "
            f"{_GOOD_TICKS_RECOVERY} consecutive fresh ticks. Freshness now within SLO threshold."
        )
        self.logger.info("SLO RESOLVED stream=%s from=%s", key, recovered_from)
        asyncio.create_task(self._dispatch(title, body, SEVERITY_RESOLVED, "low"))

    async def _dispatch(
        self,
        title: str,
        body: str,
        severity: str,
        priority: str,
    ) -> None:
        if self._dispatcher is None:
            return
        try:
            payload = {
                "title": title,
                "body": body,
                "severity": severity,
                "category": CATEGORY_SYSTEM,
                "timestamp": _utc_now().isoformat(),
            }
            method = getattr(self._dispatcher, "publish_event", None)
            if callable(method):
                await method(
                    event_type="system_health",
                    payload=payload,
                    recipients=["system", "admins"],
                    channel="in_app",
                    priority=priority,
                    sender="slo_monitor",
                )
        except Exception as exc:
            self.logger.warning("SLOMonitor notification dispatch failed: %s", exc)
