"""
Live Pipeline Metrics Service.

Tracks per-stream message counters, per-symbol poll latency/success/error
(using reservoir p50/p95), and global counters (active subscriptions, SSE
connections, reconnects, SLO violations).

Integrates with the existing MetricsService.register_service hook so the
system metrics endpoint automatically exposes live-pipeline data.
"""

from __future__ import annotations

import logging
import math
import random
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.services.core.base_service import BaseService

logger = logging.getLogger(__name__)

_RESERVOIR_SIZE = 1024
_SLIDING_WINDOW_S = 300


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _percentile(sorted_values: list[float], pct: float) -> float | None:
    if not sorted_values:
        return None
    if pct <= 0:
        return sorted_values[0]
    if pct >= 100:
        return sorted_values[-1]
    rank = (pct / 100.0) * (len(sorted_values) - 1)
    lo = int(math.floor(rank))
    hi = int(math.ceil(rank))
    if lo == hi:
        return sorted_values[lo]
    frac = rank - lo
    return sorted_values[lo] * (1.0 - frac) + sorted_values[hi] * frac


@dataclass
class _LatencyReservoir:
    """Simple reservoir sampling for latency percentiles."""

    size: int = _RESERVOIR_SIZE
    samples: list[float] = field(default_factory=list)
    _n: int = 0

    def add(self, value: float) -> None:
        self._n += 1
        if len(self.samples) < self.size:
            self.samples.append(value)
            return
        j = random.randint(0, self._n - 1)
        if j < self.size:
            self.samples[j] = value

    def p50(self) -> float | None:
        if not self.samples:
            return None
        return _percentile(sorted(self.samples), 50.0)

    def p95(self) -> float | None:
        if not self.samples:
            return None
        return _percentile(sorted(self.samples), 95.0)


@dataclass
class _StreamSample:
    ts: float
    age_ms: float | None
    threshold_s: float | None
    emitted: bool
    dropped: bool


@dataclass
class _StreamCounters:
    messages_emitted_total: int = 0
    messages_dropped_validation_total: int = 0
    poll_success_total: int = 0
    poll_error_total: int = 0
    last_freshness_ts: datetime | None = None
    last_data_age_ms: float | None = None
    last_sequence: int = 0
    samples: deque[_StreamSample] = field(
        default_factory=lambda: deque(maxlen=4096)
    )


@dataclass
class _SymbolPollStats:
    success: int = 0
    errors: int = 0
    latency: _LatencyReservoir = field(default_factory=_LatencyReservoir)


class LivePipelineMetrics(BaseService):
    """
    Aggregates all live-pipeline metrics for health endpoints and the
    MetricsService registry.
    """

    def __init__(self) -> None:
        super().__init__("LivePipelineMetrics")
        self._streams: dict[str, _StreamCounters] = {}
        self._symbols: dict[str, _SymbolPollStats] = {}
        self._active_subscriptions: int = 0
        self._sse_connections: int = 0
        self._reconnects_total: int = 0
        self._slo_violations_total: int = 0
        self._connection_sub_counts: dict[str, int] = {}
        self._connection_first_ts: dict[str, float] = {}
        self._lock_time = 0.0

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def initialize(self) -> None:
        self.logger.info("LivePipelineMetrics initialized")

    async def shutdown(self) -> None:
        self.logger.info("LivePipelineMetrics shutdown")

    def register_with_metrics_service(self, metrics_service: Any) -> None:
        """Register this service with the shared MetricsService registry."""
        try:
            if hasattr(metrics_service, "register_service"):
                metrics_service.register_service(self.service_name, self)
                self.logger.info("Registered LivePipelineMetrics with MetricsService")
        except Exception as exc:
            self.logger.warning("Metrics registration failed: %s", exc)

    # ------------------------------------------------------------------
    # Recording hooks
    # ------------------------------------------------------------------

    def record_poll(
        self,
        *,
        stream_key: str,
        symbol: str,
        success: bool,
        latency_ms: float,
        messages_emitted: int = 0,
        validation_dropped: int = 0,
        error_count: int = 0,
        data_age_ms: float | None = None,
        stale: bool = False,
        threshold_s: float | None = None,
    ) -> None:
        stream = self._streams.setdefault(stream_key, _StreamCounters())
        if success:
            stream.poll_success_total += 1
            if messages_emitted:
                stream.messages_emitted_total += messages_emitted
            if validation_dropped:
                stream.messages_dropped_validation_total += validation_dropped
            if data_age_ms is not None:
                stream.last_data_age_ms = data_age_ms
        else:
            stream.poll_error_total += 1
            if error_count:
                stream.messages_dropped_validation_total += error_count
        threshold_s_value = float(threshold_s) if threshold_s is not None else None
        if threshold_s_value is not None and data_age_ms is not None:
            if data_age_ms > threshold_s_value * 1000.0:
                self._slo_violations_total += 1
        stream.samples.append(_StreamSample(
            ts=time.monotonic(),
            age_ms=data_age_ms,
            threshold_s=threshold_s_value,
            emitted=bool(messages_emitted),
            dropped=bool(validation_dropped or (not success and error_count)),
        ))

        if symbol:
            stats = self._symbols.setdefault(symbol.upper(), _SymbolPollStats())
            if success:
                stats.success += 1
            else:
                stats.errors += 1
            if latency_ms >= 0:
                stats.latency.add(latency_ms)

    def record_sequence(self, stream_key: str, sequence: int) -> None:
        stream = self._streams.setdefault(stream_key, _StreamCounters())
        stream.last_sequence = sequence

    def record_freshness(self, stream_key: str, ts: datetime | None) -> None:
        stream = self._streams.setdefault(stream_key, _StreamCounters())
        stream.last_freshness_ts = ts

    def increment_active_subscriptions(self, delta: int = 1) -> None:
        self._active_subscriptions = max(0, self._active_subscriptions + delta)

    def register_sse_connection(
        self,
        connection_id: str,
        stream_key: str,
    ) -> None:
        self._sse_connections += 1
        self._connection_sub_counts[connection_id] = self._connection_sub_counts.get(
            connection_id, 0
        ) + 1
        self._connection_first_ts.setdefault(connection_id, time.monotonic())

    def unregister_sse_connection(self, connection_id: str) -> None:
        cur = self._connection_sub_counts.pop(connection_id, 0)
        if cur:
            self._sse_connections = max(0, self._sse_connections - 1)
        self._connection_first_ts.pop(connection_id, None)

    def record_reconnect(self) -> None:
        self._reconnects_total += 1

    def top_subscriptions(self, n: int = 10) -> list[tuple[str, int, float]]:
        counts: dict[str, list[float]] = {}
        for cid, ts in self._connection_first_ts.items():
            cnt = self._connection_sub_counts.get(cid, 0)
            for stream_key in self._streams:
                bucket = counts.setdefault(stream_key, [0, ts])
                bucket[0] = max(bucket[0], cnt)
        items = sorted(
            ((k, v[0], v[1]) for k, v in counts.items()),
            key=lambda x: (-x[1], x[2]),
        )
        return items[:n]

    # ------------------------------------------------------------------
    # Health-endpoint helpers
    # ------------------------------------------------------------------

    def stream_health(self, stream_key: str) -> dict[str, Any]:
        stream = self._streams.get(stream_key)
        if stream is None:
            return {
                "status": "idle",
                "last_event_freshness_age_ms": None,
                "messages_last_5m": 0,
                "dropped_last_5m": 0,
                "slo_attainment_pct_last_5m": 100.0,
            }
        now = time.monotonic()
        cutoff = now - _SLIDING_WINDOW_S
        messages = 0
        dropped = 0
        slo_meet = 0
        slo_total = 0
        last_age: float | None = None
        for sample in reversed(stream.samples):
            if sample.ts < cutoff:
                break
            if sample.emitted:
                messages += 1
            if sample.dropped:
                dropped += 1
            if sample.age_ms is not None and sample.threshold_s is not None:
                slo_total += 1
                if sample.age_ms <= sample.threshold_s * 1000.0:
                    slo_meet += 1
                last_age = sample.age_ms
        if last_age is None and stream.last_data_age_ms is not None:
            last_age = stream.last_data_age_ms
        pct = (slo_meet / slo_total * 100.0) if slo_total else 100.0
        status = "live"
        if slo_total and pct < 70:
            status = "degraded"
        elif last_age is not None and (
            stream.last_freshness_ts is None
            or (_utc_now() - stream.last_freshness_ts).total_seconds() > 180
        ):
            status = "stale"
        return {
            "status": status,
            "last_event_freshness_age_ms": last_age,
            "messages_last_5m": messages,
            "dropped_last_5m": dropped,
            "slo_attainment_pct_last_5m": round(pct, 2),
        }

    def all_streams_health(self) -> dict[str, dict[str, Any]]:
        out: dict[str, dict[str, Any]] = {}
        for key in list(self._streams.keys()):
            out[key] = self.stream_health(key)
        return out

    def symbol_latency(self, symbol: str) -> dict[str, float | None]:
        stats = self._symbols.get(symbol.upper())
        if stats is None:
            return {"p50_ms": None, "p95_ms": None, "success": 0, "errors": 0}
        return {
            "p50_ms": stats.latency.p50(),
            "p95_ms": stats.latency.p95(),
            "success": stats.success,
            "errors": stats.errors,
        }

    def slo_attainment_pct_last_5m(self, stream_key: str) -> float:
        return self.stream_health(stream_key)["slo_attainment_pct_last_5m"]

    # ------------------------------------------------------------------
    # Snapshot for /data-health
    # ------------------------------------------------------------------

    def snapshot(self) -> dict[str, Any]:
        streams = self.all_streams_health()
        warn_count = 0
        error_count = 0
        for info in streams.values():
            pct = info.get("slo_attainment_pct_last_5m", 100.0)
            age_ms = info.get("last_event_freshness_age_ms")
            if pct < 95 or (age_ms is not None and age_ms > 300_000):
                warn_count += 1
            if pct < 70 or (age_ms is not None and age_ms > 600_000):
                error_count += 1
        return {
            "active_subscriptions": self._active_subscriptions,
            "sse_connections": self._sse_connections,
            "reconnects_total": self._reconnects_total,
            "slo_violations_total": self._slo_violations_total,
            "streams": streams,
            "sse_clients": {
                "count": self._sse_connections,
                "top_subscriptions": [
                    {
                        "stream_key": k,
                        "count": c,
                        "first_seen_ts": ts,
                    }
                    for k, c, ts in self.top_subscriptions(10)
                ],
            },
            "slo_summary": {
                "warn": warn_count,
                "error": error_count,
            },
            "symbols": {
                sym: self.symbol_latency(sym) for sym in list(self._symbols.keys())[:200]
            },
        }

    async def health_check(self) -> dict[str, Any]:
        base = await super().health_check()
        base.update(self.snapshot())
        return base
