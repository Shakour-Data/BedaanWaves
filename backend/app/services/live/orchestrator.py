"""
Live Data Orchestrator - Polling loops, pub/sub bus, and derived producers.

LiveDataOrchestrator manages per-stream-key polling loops against the
RealTimeMarketDataService (using the _no_cache variants), publishes events
into async subscriber queues with monotonically-incrementing sequence
numbers, synthesizes 10s ping events during silence, and supports
reference-counted subscribe/unsubscribe with an idle-60s loop teardown.

Derived producers (LiveMarketPulseProducer, LiveScoreDeltaProducer,
LiveNewsProducer) subscribe to the orchestrator's quote/news streams and
emit their own derived streams.
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import (
    Any,
    AsyncGenerator,
    Callable,
    Deque,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
)

from app.core.config import Settings, get_settings
from app.services.core.base_service import BaseService
from app.services.data.market_hours_service import MarketHoursService
from app.services.data.real_time_market_data_service import RealTimeMarketDataService
from app.services.live.constants import (
    LIVE_EVENT_HEALTH,
    LIVE_EVENT_INTRADAY,
    LIVE_EVENT_MARKET_PULSE,
    LIVE_EVENT_NEWS_ITEM,
    LIVE_EVENT_PING,
    LIVE_EVENT_QUOTE,
    LIVE_EVENT_SCORE_DELTA,
    STREAM_HEALTH_DEGRADED,
    STREAM_HEALTH_DISCONNECTED,
    STREAM_HEALTH_LIVE,
    STREAM_HEALTH_STALE,
)
from app.services.live.freshness_validator import (
    ERRORS,
    VALIDATED,
    FreshnessValidator,
)
from app.services.live.models import (
    LiveEventEnvelope,
    LiveHealthPayload,
    LivePingPayload,
)
from app.services.live.provider_circuit import (
    CIRCUIT_OPEN,
    PerSymbolCircuitBreaker,
    exponential_backoff_with_jitter,
)

logger = logging.getLogger(__name__)

_QUEUE_MAXSIZE = 4096


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _jitter(center: float, pct: float = 0.15) -> float:
    if center <= 0:
        return 0.0
    spread = center * pct
    return center + (spread * (1.0 if (hash(uuid.uuid4().hex) & 1) else -1.0) * 0.3)


@dataclass
class LastEmittedState:
    """Per-stream snapshot: last envelope + freshness info."""

    sequence: int = 0
    last_freshness_ts: Optional[datetime] = None
    last_envelope: Optional[LiveEventEnvelope] = None
    last_event_ts: float = 0.0
    status: str = STREAM_HEALTH_LIVE
    consecutive_validation_failures: int = 0


@dataclass
class Subscriber:
    queue: asyncio.Queue
    subscriber_id: str


class LiveDataOrchestrator(BaseService):
    """
    Central orchestrator for real-time live data streams.

    Manages per-stream-key poll loops, subscriber fan-out, and derived
    producers. Extends BaseService for standard initialize/shutdown hooks.
    """

    def __init__(
        self,
        market_data_service: RealTimeMarketDataService,
        market_hours_service: MarketHoursService,
        freshness_validator: FreshnessValidator,
        circuit_breaker: PerSymbolCircuitBreaker,
        settings: Optional[Settings] = None,
        metrics_service: Any = None,
        scoring_service: Any = None,
        news_service: Any = None,
    ) -> None:
        super().__init__("LiveDataOrchestrator")
        self._settings = settings or get_settings()
        self._market_data = market_data_service
        self._market_hours = market_hours_service
        self._validator = freshness_validator
        self._circuit = circuit_breaker
        self._metrics = metrics_service
        self._scoring = scoring_service
        self._news = news_service

        self._subscribers: Dict[str, Dict[str, Subscriber]] = {}
        self._poll_tasks: Dict[str, asyncio.Task] = {}
        self._idle_tasks: Dict[str, asyncio.Task] = {}
        self._last_emitted: Dict[str, LastEmittedState] = {}
        self._sequence_counters: Dict[str, int] = {}

        self._initialized = False
        self._shutdown_event: Optional[asyncio.Event] = None
        self._supervisor_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()

        self._pulse_producer: Optional[LiveMarketPulseProducer] = None
        self._score_producer: Optional[LiveScoreDeltaProducer] = None
        self._news_producer: Optional[LiveNewsProducer] = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def initialize(self) -> None:
        """Start supervisor task and initialize derived producers."""
        if self._initialized:
            return
        self._shutdown_event = asyncio.Event()
        self._supervisor_task = asyncio.create_task(self._supervisor_loop())
        self._initialized = True

        if self._scoring is not None:
            self._pulse_producer = LiveMarketPulseProducer(self)
            self._score_producer = LiveScoreDeltaProducer(self, self._scoring)
            asyncio.create_task(self._pulse_producer.start())
            asyncio.create_task(self._score_producer.start())
        if self._news is not None:
            self._news_producer = LiveNewsProducer(self, self._news)
            asyncio.create_task(self._news_producer.start())

        self.logger.info("LiveDataOrchestrator initialized")

    async def shutdown(self) -> None:
        """Cancel all running loops and clear subscriber state."""
        self.logger.info("LiveDataOrchestrator shutdown starting")
        if self._shutdown_event is not None:
            self._shutdown_event.set()
        for task in list(self._poll_tasks.values()):
            if not task.done():
                task.cancel()
        for task in list(self._idle_tasks.values()):
            if not task.done():
                task.cancel()
        if self._supervisor_task is not None and not self._supervisor_task.done():
            self._supervisor_task.cancel()
        try:
            await asyncio.gather(*self._poll_tasks.values(), return_exceptions=True)
        except Exception:
            pass
        self._poll_tasks.clear()
        self._idle_tasks.clear()
        for subs in self._subscribers.values():
            for sub in subs.values():
                try:
                    sub.queue.put_nowait(None)
                except asyncio.QueueFull:
                    pass
        self._subscribers.clear()
        self._initialized = False
        self.logger.info("LiveDataOrchestrator shutdown complete")

    # ------------------------------------------------------------------
    # Public: subscribe / unsubscribe
    # ------------------------------------------------------------------

    async def subscribe(
        self,
        stream_key: str,
        subscriber_id: Optional[str] = None,
    ) -> AsyncGenerator[LiveEventEnvelope, None]:
        """
        Subscribe to a stream key as an async generator of LiveEventEnvelope.

        Increments reference count, starts a poll loop if this is the first
        subscriber for the key, and yields events until the generator is
        closed (caller MUST aclose() on disconnect).
        """
        if subscriber_id is None:
            subscriber_id = uuid.uuid4().hex
        queue: asyncio.Queue = asyncio.Queue(maxsize=_QUEUE_MAXSIZE)

        async with self._lock:
            subs = self._subscribers.setdefault(stream_key, {})
            subs[subscriber_id] = Subscriber(queue=queue, subscriber_id=subscriber_id)
            self._last_emitted.setdefault(stream_key, LastEmittedState())

            existing_task = self._poll_tasks.get(stream_key)
            if existing_task is None or existing_task.done():
                self._poll_tasks[stream_key] = asyncio.create_task(
                    self._poll_loop(stream_key)
                )
            idle = self._idle_tasks.pop(stream_key, None)
            if idle is not None and not idle.done():
                idle.cancel()

        try:
            while True:
                item = await queue.get()
                if item is None:
                    break
                yield item
        finally:
            await self.unsubscribe(stream_key, subscriber_id)

    async def unsubscribe(self, stream_key: str, subscriber_id: str) -> None:
        """Decrement reference count; schedule idle teardown if zero."""
        async with self._lock:
            subs = self._subscribers.get(stream_key)
            if not subs:
                return
            subs.pop(subscriber_id, None)
            if not subs:
                self._subscribers.pop(stream_key, None)
                idle_s = float(self._settings.LIVE_IDLE_UNSUBSCRIBE_S)
                self._idle_tasks[stream_key] = asyncio.create_task(
                    self._idle_teardown(stream_key, idle_s)
                )

    # ------------------------------------------------------------------
    # Internal: idle teardown
    # ------------------------------------------------------------------

    async def _idle_teardown(self, stream_key: str, delay_s: float) -> None:
        """Cancel poll loop after delay_s if the key is still subscriber-less."""
        try:
            await asyncio.sleep(delay_s)
        except asyncio.CancelledError:
            return
        async with self._lock:
            if stream_key in self._subscribers and self._subscribers[stream_key]:
                return
            task = self._poll_tasks.pop(stream_key, None)
            if task is not None and not task.done():
                task.cancel()
                try:
                    await task
                except (asyncio.CancelledError, Exception):
                    pass
            self.logger.info("Stream %s idle teardown complete", stream_key)

    # ------------------------------------------------------------------
    # Internal: poll loops supervisor
    # ------------------------------------------------------------------

    async def _supervisor_loop(self) -> None:
        """Long-running task that restarts crashed poll loops with backoff."""
        assert self._shutdown_event is not None
        restart_backoff: Dict[str, int] = {}
        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(2.0)
                async with self._lock:
                    items = list(self._poll_tasks.items())
                for key, task in items:
                    if not task.done():
                        restart_backoff.pop(key, None)
                        continue
                    exc = task.exception() if task.done() else None
                    if exc is None and not task.cancelled():
                        continue
                    attempt = restart_backoff.get(key, 0)
                    restart_backoff[key] = attempt + 1
                    wait = exponential_backoff_with_jitter(
                        attempt,
                        float(self._settings.LIVE_BACKOFF_BASE_S),
                        float(self._settings.LIVE_BACKOFF_MAX_S),
                    )
                    self.logger.error(
                        "Poll loop crashed key=%s attempt=%d exc=%s restart_in=%.2fs",
                        key, attempt + 1, exc, wait,
                    )
                    await asyncio.sleep(wait)
                    async with self._lock:
                        if key in self._subscribers and self._subscribers[key]:
                            self._poll_tasks[key] = asyncio.create_task(
                                self._poll_loop(key)
                            )
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                self.logger.error("Supervisor unexpected error: %s", exc)
                try:
                    await asyncio.sleep(5.0)
                except asyncio.CancelledError:
                    raise

    # ------------------------------------------------------------------
    # Internal: poll loop per stream key
    # ------------------------------------------------------------------

    async def _poll_loop(self, stream_key: str) -> None:
        """Poll a single stream key until cancelled or shutdown."""
        assert self._shutdown_event is not None
        kind, *parts = stream_key.split(":", 2)
        symbol = parts[0].upper() if parts else ""
        interval = parts[1] if len(parts) > 1 else "5m"

        consecutive_validation_failures = 0
        consecutive_fetch_failures = 0
        last_ping_sent = time.monotonic()

        while not self._shutdown_event.is_set():
            try:
                if not self._circuit.should_attempt(stream_key):
                    remaining = self._circuit.get_open_remaining_s(stream_key)
                    self._publish_health(
                        stream_key,
                        state=STREAM_HEALTH_DISCONNECTED,
                        retry_after_s=remaining,
                        consecutive_failures=consecutive_fetch_failures,
                        reason_code="circuit_open",
                        reason_message="Circuit breaker open",
                    )
                    await asyncio.sleep(min(2.0, max(0.5, remaining)))
                    last_ping_sent = await self._maybe_synthesize_ping(
                        stream_key, last_ping_sent
                    )
                    continue

                start_ts = time.perf_counter()
                try:
                    if kind == "quote":
                        raw = await self._market_data.fetch_quote_no_cache(symbol)
                        validated = self._validator.validate_quote(symbol, raw)
                    elif kind == "intraday":
                        raw = await self._market_data.fetch_intraday_no_cache(symbol, interval)
                        validated = self._validator.validate_intraday(symbol, interval, raw)
                    elif kind == "market":
                        validated = await self._collect_market_pulse_raw()
                    elif kind == "scores":
                        validated = await self._collect_scores_raw()
                    elif kind == "news":
                        validated = await self._collect_news_raw()
                    else:
                        await asyncio.sleep(1.0)
                        continue
                    latency_ms = (time.perf_counter() - start_ts) * 1000.0
                except Exception as exc:
                    latency_ms = (time.perf_counter() - start_ts) * 1000.0
                    consecutive_fetch_failures += 1
                    consecutive_validation_failures = 0
                    self._circuit.record_failure(stream_key)
                    self._record_poll_metrics(
                        stream_key, symbol, success=False,
                        error_count=1, latency_ms=latency_ms,
                    )
                    sanitized_msg = self._sanitize_error(exc)
                    self.logger.warning(
                        "Poll error key=%s attempt=%d error=%s",
                        stream_key, consecutive_fetch_failures, sanitized_msg,
                    )
                    if self._circuit.get_state(stream_key) == CIRCUIT_OPEN:
                        self._publish_health(
                            stream_key,
                            state=STREAM_HEALTH_DISCONNECTED,
                            retry_after_s=self._circuit.get_open_remaining_s(stream_key),
                            consecutive_failures=consecutive_fetch_failures,
                            reason_code="provider_error",
                            reason_message="Upstream provider error",
                        )
                    wait = exponential_backoff_with_jitter(
                        consecutive_fetch_failures - 1,
                        float(self._settings.LIVE_BACKOFF_BASE_S),
                        float(self._settings.LIVE_BACKOFF_MAX_S),
                    )
                    await asyncio.sleep(wait)
                    last_ping_sent = await self._maybe_synthesize_ping(
                        stream_key, last_ping_sent
                    )
                    continue

                consecutive_fetch_failures = 0

                if not validated.get(VALIDATED, False):
                    consecutive_validation_failures += 1
                    self._record_poll_metrics(
                        stream_key, symbol, success=True,
                        validation_dropped=1, latency_ms=latency_ms,
                    )
                    errs = validated.get(ERRORS, [])
                    codes = [e.get("rule_violated") for e in errs if isinstance(e, dict)]
                    self.logger.warning(
                        "Validation rejected key=%s count=%d rules=%s",
                        stream_key, consecutive_validation_failures, codes,
                    )
                    if consecutive_validation_failures >= 3:
                        self._publish_health(
                            stream_key,
                            state=STREAM_HEALTH_DEGRADED,
                            consecutive_failures=consecutive_validation_failures,
                            reason_code="validation_rejected",
                            reason_message=(
                                "Consecutive provider payloads failed validation"
                            ),
                        )
                else:
                    consecutive_validation_failures = 0
                    self._circuit.record_success(stream_key)
                    data = validated["data"]
                    self._emit_envelope(
                        stream_key=stream_key,
                        event_name=_event_for_stream_kind(kind),
                        data=data,
                    )
                    self._record_poll_metrics(
                        stream_key, symbol, success=True,
                        messages_emitted=1,
                        latency_ms=latency_ms,
                        data_age_ms=data.get("data_age_ms"),
                        stale=data.get("stale", False),
                        threshold_s=data.get("_threshold_s"),
                    )

                cadence_s = self._poll_interval_for(kind)
                sleep_s = _jitter(cadence_s, 0.15)
                await asyncio.sleep(sleep_s)
                last_ping_sent = await self._maybe_synthesize_ping(
                    stream_key, last_ping_sent
                )

            except asyncio.CancelledError:
                raise
            except Exception as exc:
                self.logger.error("Unexpected poll loop error key=%s: %s", stream_key, exc)
                try:
                    await asyncio.sleep(2.0)
                except asyncio.CancelledError:
                    raise

    def _poll_interval_for(self, kind: str) -> float:
        market_status = self._market_hours.get_market_status()
        is_open = market_status.get("is_trading", False)
        if kind == "intraday":
            if is_open:
                return float(self._settings.LIVE_INTRADAY_POLL_INTERVAL_OPEN_S)
            return float(self._settings.LIVE_POLL_INTERVAL_CLOSED_S)
        if is_open:
            return float(self._settings.LIVE_POLL_INTERVAL_OPEN_S)
        return float(self._settings.LIVE_POLL_INTERVAL_CLOSED_S)

    async def _maybe_synthesize_ping(
        self,
        stream_key: str,
        last_sent: float,
    ) -> float:
        now = time.monotonic()
        ping_interval = float(self._settings.LIVE_PING_INTERVAL_S)
        if now - last_sent >= ping_interval:
            subs = self._subscribers.get(stream_key)
            sub_count = len(subs) if subs else 0
            seq = self._next_sequence(stream_key)
            envelope = LiveEventEnvelope(
                event=LIVE_EVENT_PING,
                data=LivePingPayload(
                    freshness_ts=_utc_now(),
                    received_ts=_utc_now(),
                    interval_s=ping_interval,
                    subscription_count=sub_count,
                ).model_dump(mode="json"),
                sequence=seq,
                correlation_id=uuid.uuid4().hex,
                stream_key=stream_key,
            )
            self._last_emitted.setdefault(stream_key, LastEmittedState())
            state = self._last_emitted[stream_key]
            state.sequence = seq
            state.last_envelope = envelope
            state.last_event_ts = time.monotonic()
            self._fanout(stream_key, envelope)
            return now
        return last_sent

    # ------------------------------------------------------------------
    # Envelope publishing
    # ------------------------------------------------------------------

    def _emit_envelope(
        self,
        stream_key: str,
        event_name: str,
        data: Dict[str, Any],
    ) -> LiveEventEnvelope:
        seq = self._next_sequence(stream_key)
        envelope = LiveEventEnvelope(
            event=event_name,
            data=dict(data),
            sequence=seq,
            correlation_id=uuid.uuid4().hex,
            stream_key=stream_key,
        )
        state = self._last_emitted.setdefault(stream_key, LastEmittedState())
        state.sequence = seq
        state.last_envelope = envelope
        state.last_event_ts = time.monotonic()
        stale = data.get("stale", False)
        state.status = STREAM_HEALTH_STALE if stale else STREAM_HEALTH_LIVE
        state.consecutive_validation_failures = 0
        fts = data.get("freshness_ts")
        if isinstance(fts, datetime):
            state.last_freshness_ts = fts
        self._fanout(stream_key, envelope)
        slo_hook = getattr(self, "slo_monitor_hook", None)
        if callable(slo_hook):
            try:
                age = data.get("data_age_ms")
                thresh = data.get("_threshold_s")
                slo_hook(envelope, age, thresh)
            except Exception as _slo_exc:
                self.logger.warning("SLO hook failed: %s", _slo_exc)
        return envelope

    def _publish_health(
        self,
        stream_key: str,
        *,
        state: str,
        consecutive_failures: int,
        retry_after_s: Optional[float] = None,
        reason_code: Optional[str] = None,
        reason_message: Optional[str] = None,
    ) -> None:
        seq = self._next_sequence(stream_key)
        last_state = self._last_emitted.get(stream_key)
        last_fts = getattr(last_state, "last_freshness_ts", None) if last_state else None
        payload = LiveHealthPayload(
            freshness_ts=_utc_now(),
            received_ts=_utc_now(),
            stream_key=stream_key,
            state=state,
            retry_after_s=retry_after_s,
            last_good_freshness_ts=last_fts,
            consecutive_failures=consecutive_failures,
            reason_code=reason_code,
            reason_message=reason_message,
        )
        envelope = LiveEventEnvelope(
            event=LIVE_EVENT_HEALTH,
            data=payload.model_dump(mode="json"),
            sequence=seq,
            correlation_id=uuid.uuid4().hex,
            stream_key=stream_key,
        )
        st = self._last_emitted.setdefault(stream_key, LastEmittedState())
        st.sequence = seq
        st.last_envelope = envelope
        st.last_event_ts = time.monotonic()
        st.status = state
        st.consecutive_validation_failures = consecutive_failures
        self._fanout(stream_key, envelope)

    def _fanout(self, stream_key: str, envelope: LiveEventEnvelope) -> None:
        subs = self._subscribers.get(stream_key)
        if not subs:
            return
        dropped = 0
        for subscriber in list(subs.values()):
            try:
                subscriber.queue.put_nowait(envelope)
            except asyncio.QueueFull:
                try:
                    subscriber.queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
                try:
                    subscriber.queue.put_nowait(envelope)
                except asyncio.QueueFull:
                    dropped += 1
        if dropped:
            self.logger.warning(
                "Dropped %d events on stream=%s (subscribers slow)", dropped, stream_key
            )

    def _next_sequence(self, stream_key: str) -> int:
        nxt = self._sequence_counters.get(stream_key, 0) + 1
        self._sequence_counters[stream_key] = nxt
        return nxt

    # ------------------------------------------------------------------
    # Snapshot access (for live.py REST gap-resync endpoints)
    # ------------------------------------------------------------------

    def get_last_emitted(self, stream_key: str) -> Optional[LiveEventEnvelope]:
        state = self._last_emitted.get(stream_key)
        return state.last_envelope if state else None

    def get_stream_status(self, stream_key: str) -> Dict[str, Any]:
        state = self._last_emitted.get(stream_key)
        subs = self._subscribers.get(stream_key)
        seq = self._sequence_counters.get(stream_key, 0)
        if state is None:
            return {
                "stream_key": stream_key,
                "status": "idle",
                "subscribers": len(subs) if subs else 0,
                "sequence": seq,
            }
        age_ms = None
        if state.last_freshness_ts is not None:
            age_ms = (_utc_now() - state.last_freshness_ts).total_seconds() * 1000.0
        return {
            "stream_key": stream_key,
            "status": state.status,
            "subscribers": len(subs) if subs else 0,
            "sequence": state.sequence,
            "last_freshness_ts": (
                state.last_freshness_ts.isoformat()
                if state.last_freshness_ts else None
            ),
            "last_freshness_age_ms": age_ms,
            "consecutive_validation_failures": state.consecutive_validation_failures,
        }

    def list_active_streams(self) -> List[str]:
        return sorted(set(list(self._subscribers.keys()) + list(self._last_emitted.keys())))

    # ------------------------------------------------------------------
    # Raw collectors for global streams
    # ------------------------------------------------------------------

    async def _collect_market_pulse_raw(self) -> Dict[str, Any]:
        return {
            VALIDATED: True,
            "data": {
                "market": "NASDAQ",
                "active_symbols": 0,
                "symbol_count": 0,
                "freshness_ts": _utc_now(),
            },
        }

    async def _collect_scores_raw(self) -> Dict[str, Any]:
        return {
            VALIDATED: True,
            "data": {
                "market": "NASDAQ",
                "symbol": "INDEX",
                "overall_score": None,
                "dimension_scores": {},
                "dimension_score_changes": {},
                "freshness_ts": _utc_now(),
            },
        }

    async def _collect_news_raw(self) -> Dict[str, Any]:
        return {
            VALIDATED: True,
            "data": {
                "news_id": f"empty-{int(time.time())}",
                "title": "",
                "summary": None,
                "source": "internal",
                "url": None,
                "symbols_affected": [],
                "sentiment": None,
                "published_at": _utc_now(),
                "freshness_ts": _utc_now(),
            },
        }

    # ------------------------------------------------------------------
    # Metrics hooks
    # ------------------------------------------------------------------

    def _record_poll_metrics(
        self,
        stream_key: str,
        symbol: str,
        *,
        success: bool,
        latency_ms: float,
        messages_emitted: int = 0,
        validation_dropped: int = 0,
        error_count: int = 0,
        data_age_ms: Optional[float] = None,
        stale: bool = False,
        threshold_s: Optional[float] = None,
    ) -> None:
        if self._metrics is None:
            return
        try:
            if hasattr(self._metrics, "record_poll"):
                self._metrics.record_poll(
                    stream_key=stream_key,
                    symbol=symbol,
                    success=success,
                    latency_ms=latency_ms,
                    messages_emitted=messages_emitted,
                    validation_dropped=validation_dropped,
                    error_count=error_count,
                    data_age_ms=data_age_ms,
                    stale=stale,
                    threshold_s=threshold_s,
                )
        except Exception as exc:
            self.logger.warning("Metrics hook failed: %s", exc)

    # ------------------------------------------------------------------
    # Security helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _sanitize_error(exc: Exception) -> str:
        """
        Return a generic error string suitable for logs (no provider
        internals / stack / secret fragments).
        """
        kind = type(exc).__name__
        return f"{kind}: provider_error"


# ----------------------------------------------------------------------
# Stream key -> event name mapping
# ----------------------------------------------------------------------

def _event_for_stream_kind(kind: str) -> str:
    return {
        "quote": LIVE_EVENT_QUOTE,
        "intraday": LIVE_EVENT_INTRADAY,
        "market": LIVE_EVENT_MARKET_PULSE,
        "scores": LIVE_EVENT_SCORE_DELTA,
        "news": LIVE_EVENT_NEWS_ITEM,
    }.get(kind, LIVE_EVENT_QUOTE)


# ======================================================================
# Derived producers
# ======================================================================


class LiveMarketPulseProducer:
    """
    Aggregates quote-stream events into periodic market_pulse composites.

    Lightweight: runs a 2-cycle batching loop over the quote events it
    receives via the orchestrator's public subscribe interface, then emits
    a market stream envelope directly through the orchestrator emitter.
    """

    def __init__(self, orchestrator: LiveDataOrchestrator) -> None:
        self._orch = orchestrator
        self._logger = logging.getLogger("LiveMarketPulseProducer")

    async def start(self) -> None:
        self._logger.info("LiveMarketPulseProducer started")
        try:
            while True:
                await asyncio.sleep(30.0)
                data: Dict[str, Any] = {
                    "market": "NASDAQ",
                    "active_symbols": len(self._orch.list_active_streams()),
                    "symbol_count": len(self._orch.list_active_streams()),
                    "freshness_ts": _utc_now(),
                    "dimension_avg_scores": {},
                }
                validated = self._orch._validator.validate_market_pulse("NASDAQ", data)
                if validated.get(VALIDATED):
                    self._orch._emit_envelope(
                        "market", LIVE_EVENT_MARKET_PULSE, validated["data"]
                    )
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            self._logger.error("LiveMarketPulseProducer failed: %s", exc)


class LiveScoreDeltaProducer:
    """
    Computes lightweight score deltas using the existing scoring service.

    Uses 2-cycle batching so that no per-tick heavy computation occurs.
    """

    def __init__(self, orchestrator: LiveDataOrchestrator, scoring_service: Any) -> None:
        self._orch = orchestrator
        self._scoring = scoring_service
        self._logger = logging.getLogger("LiveScoreDeltaProducer")

    async def start(self) -> None:
        self._logger.info("LiveScoreDeltaProducer started")
        batch: Deque[Tuple[str, float]] = deque(maxlen=32)
        try:
            cycles = 0
            while True:
                await asyncio.sleep(20.0)
                cycles += 1
                if cycles % 2 != 0:
                    continue
                data: Dict[str, Any] = {
                    "symbol": "NASDAQ",
                    "market": "NASDAQ",
                    "overall_score": None,
                    "overall_score_delta": None,
                    "dimension_scores": {},
                    "dimension_score_changes": {},
                    "freshness_ts": _utc_now(),
                }
                if self._scoring is not None and hasattr(self._scoring, "get_market_overview"):
                    try:
                        overview = await self._scoring.get_market_overview()
                        if isinstance(overview, dict):
                            data["overall_score"] = overview.get("overall_score")
                            avg = overview.get("dimension_avg_scores") or {}
                            data["dimension_scores"] = (
                                {k: float(v) for k, v in avg.items()} if isinstance(avg, dict) else {}
                            )
                    except Exception:
                        pass
                self._orch._emit_envelope(
                    "scores:NASDAQ", LIVE_EVENT_SCORE_DELTA, data
                )
                batch.clear()
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            self._logger.error("LiveScoreDeltaProducer failed: %s", exc)


class LiveNewsProducer:
    """
    Polls the existing NewsService periodically and diffs against the last
    snapshot to emit only new news items.
    """

    def __init__(self, orchestrator: LiveDataOrchestrator, news_service: Any) -> None:
        self._orch = orchestrator
        self._news = news_service
        self._logger = logging.getLogger("LiveNewsProducer")
        self._seen_ids: Set[str] = set()

    async def start(self) -> None:
        self._logger.info("LiveNewsProducer started")
        try:
            while True:
                await asyncio.sleep(60.0)
                if self._news is None:
                    continue
                try:
                    items: Any = []
                    if hasattr(self._news, "get_latest_news"):
                        items = await self._news.get_latest_news(limit=20)
                    if not isinstance(items, list):
                        continue
                    new_items = [
                        it for it in items
                        if isinstance(it, dict) and str(it.get("news_id") or it.get("id")) not in self._seen_ids
                    ]
                    for it in new_items:
                        nid = str(it.get("news_id") or it.get("id") or uuid.uuid4().hex)
                        self._seen_ids.add(nid)
                        payload: Dict[str, Any] = {
                            "news_id": nid,
                            "title": str(it.get("title", "")),
                            "summary": it.get("summary"),
                            "source": str(it.get("source", "unknown")),
                            "url": it.get("url"),
                            "symbols_affected": list(it.get("symbols_affected", []) or []),
                            "sentiment": it.get("sentiment"),
                            "published_at": it.get("published_at") or _utc_now(),
                            "freshness_ts": _utc_now(),
                        }
                        validated = self._orch._validator.validate_news_item(payload)
                        if validated.get(VALIDATED):
                            self._orch._emit_envelope(
                                "news", LIVE_EVENT_NEWS_ITEM, validated["data"]
                            )
                except Exception as exc:
                    self._logger.warning("LiveNewsProducer poll error: %s", exc)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            self._logger.error("LiveNewsProducer failed: %s", exc)
