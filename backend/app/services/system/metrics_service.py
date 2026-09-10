"""
Metrics Service - Tier 9 System Service

Aggregates metrics from all registered BedaanWaves services.
Provides Prometheus-style counters and health summaries.
"""

from datetime import UTC, datetime
from typing import Any

from prometheus_client import REGISTRY, Counter, Gauge, Histogram, generate_latest

from ..core import BaseService

REQUESTS_TOTAL = Counter(
    "bedaanwaves_requests_total",
    "Total API requests",
    ["method", "endpoint", "status"],
)
REQUEST_LATENCY = Histogram(
    "bedaanwaves_request_latency_seconds",
    "Request latency in seconds",
    ["method", "endpoint"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)
ACTIVE_CONNECTIONS = Gauge(
    "bedaanwaves_active_connections",
    "Currently active SSE/WebSocket connections",
)
SIGNAL_COUNT = Counter(
    "bedaanwaves_signals_total",
    "Total generated signals",
    ["signal_type"],
)
ACTIVE_USERS = Gauge(
    "bedaanwaves_active_users",
    "Number of concurrently active users (5-min window)",
)
STOCK_SCORE_COUNT = Counter(
    "bedaanwaves_stock_scores_computed_total",
    "Total stock scores computed",
    ["dimension"],
)
DATA_FRESHNESS_LAG = Gauge(
    "bedaanwaves_data_freshness_lag_seconds",
    "Seconds since last successful data ingestion",
    ["source"],
)
ALERT_TRIGGER_COUNT = Counter(
    "bedaanwaves_alerts_triggered_total",
    "Total user-defined alerts triggered",
    ["alert_type"],
)
CACHE_OPERATIONS = Counter(
    "bedaanwaves_cache_operations_total",
    "Cache hit/miss operations",
    ["operation", "result"],
)


class MetricsService(BaseService):
    """
    Service metrics aggregator with Prometheus exposition.

    Collects metrics from all registered services and exposes
    platform-wide health and performance summaries.
    """

    def __init__(self, service_name: str = "MetricsService"):
        super().__init__(service_name)
        self._registered_services: dict[str, BaseService] = {}
        self._platform_start: datetime = datetime.now(UTC)

    async def initialize(self) -> None:
        self.logger.info("MetricsService initialized")

    async def shutdown(self) -> None:
        self._registered_services.clear()
        self.logger.info("MetricsService shutdown")

    def register_service(self, name: str, service: BaseService) -> None:
        self._registered_services[name] = service
        self.logger.debug(f"Registered metrics source: {name}")

    def unregister_service(self, name: str) -> bool:
        if name in self._registered_services:
            del self._registered_services[name]
            return True
        return False

    def get_service_metrics(self, name: str) -> dict[str, Any] | None:
        if name not in self._registered_services:
            return None
        return self._registered_services[name].get_metrics()

    def get_all_metrics(self) -> dict[str, Any]:
        services_metrics = {}
        total_calls = 0
        total_errors = 0
        total_cache_hits = 0
        total_cache_misses = 0

        for name, service in self._registered_services.items():
            try:
                metrics = service.get_metrics()
                services_metrics[name] = metrics
                total_calls += metrics.get("calls", 0)
                total_errors += metrics.get("errors", 0)
                total_cache_hits += metrics.get("cache_hits", 0)
                total_cache_misses += metrics.get("cache_misses", 0)
            except Exception as exc:
                self.logger.warning(f"Failed to collect metrics from {name}: {exc}")
                services_metrics[name] = {"error": str(exc)}

        total_cache_requests = total_cache_hits + total_cache_misses
        platform_uptime = (datetime.now(UTC) - self._platform_start).total_seconds()

        return {
            "platform": {
                "uptime_seconds": platform_uptime,
                "services_count": len(self._registered_services),
                "total_calls": total_calls,
                "total_errors": total_errors,
                "global_error_rate": total_errors / total_calls if total_calls > 0 else 0,
                "total_cache_hits": total_cache_hits,
                "total_cache_misses": total_cache_misses,
                "global_cache_hit_rate": (
                    total_cache_hits / total_cache_requests if total_cache_requests > 0 else 0
                ),
            },
            "services": services_metrics,
        }

    def get_health_summary(self) -> dict[str, Any]:
        health: dict[str, Any] = {"platform": "healthy", "services": {}}
        for name, service in self._registered_services.items():
            try:
                health["services"][name] = {
                    "status": "healthy",
                    "service": name,
                }
            except Exception as exc:
                health["services"][name] = {"status": "unhealthy", "error": str(exc)}
        return health

    def render_prometheus(self) -> bytes:
        return generate_latest(REGISTRY)

    def record_active_users(self, count: int) -> None:
        """Update the active-users gauge."""
        ACTIVE_USERS.set(count)

    def record_stock_score(self, dimension: str, count: int = 1) -> None:
        """Increment the stock-score-computed counter."""
        STOCK_SCORE_COUNT.labels(dimension=dimension).inc(count)

    def record_data_freshness(self, source: str, lag_seconds: float) -> None:
        """Set the data-freshness-lag gauge for a given source."""
        DATA_FRESHNESS_LAG.labels(source=source).set(lag_seconds)

    def record_alert_triggered(self, alert_type: str, count: int = 1) -> None:
        """Increment the alert-trigger counter."""
        ALERT_TRIGGER_COUNT.labels(alert_type=alert_type).inc(count)

    def record_cache_operation(self, operation: str, result: str, count: int = 1) -> None:
        """Increment the cache-operations counter."""
        CACHE_OPERATIONS.labels(operation=operation, result=result).inc(count)

    def record_signal(self, signal_type: str, count: int = 1) -> None:
        """Increment the signal counter."""
        SIGNAL_COUNT.labels(signal_type=signal_type).inc(count)

    def record_request(self, method: str, endpoint: str, status_code: int, duration: float) -> None:
        """Record a single HTTP request metric."""
        REQUESTS_TOTAL.labels(method=method, endpoint=endpoint, status=str(status_code)).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(duration)

    async def health_check(self) -> dict[str, Any]:
        return {
            "service": self.service_name,
            "status": "healthy",
            "registered_services": len(self._registered_services),
            "uptime_seconds": (datetime.now(UTC) - self.created_at).total_seconds(),
        }
