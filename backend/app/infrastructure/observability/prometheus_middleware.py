"""Prometheus metrics instrumentation middleware for FastAPI.

Automatically records HTTP request counts and latency histograms
with labels for method, endpoint, and status code.
"""

from __future__ import annotations

import logging
import time
from typing import Callable

from prometheus_client import Counter, Histogram
from starlette.types import ASGIApp, Message, Receive, Scope, Send

logger = logging.getLogger(__name__)

REQUEST_COUNTER = Counter(
    "bedaanwaves_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

REQUEST_LATENCY = Histogram(
    "bedaanwaves_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)


class PrometheusMetricsMiddleware:
    """ASGI middleware that instruments HTTP request metrics for Prometheus."""

    def __init__(self, app: ASGIApp, metrics_getter: Callable[[], object] | None = None) -> None:
        self.app = app
        self._metrics_getter = metrics_getter

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = str(scope.get("method", "UNKNOWN"))
        path = str(scope.get("path", "/"))
        endpoint = self._normalise_path(path)
        start_time = time.monotonic()
        status_code = 500

        async def send_with_metrics(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = int(message.get("status", 500))
            await send(message)

        try:
            await self.app(scope, receive, send_with_metrics)
        except Exception:
            status_code = 500
            raise
        finally:
            duration = time.monotonic() - start_time
            status_str = str(status_code)
            REQUEST_COUNTER.labels(method=method, endpoint=endpoint, status=status_str).inc()
            REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(duration)

            if self._metrics_getter is not None:
                try:
                    metrics_svc = self._metrics_getter()
                    if hasattr(metrics_svc, "record_request"):
                        metrics_svc.record_request(method, endpoint, status_code, duration)
                except Exception:
                    pass

    @staticmethod
    def _normalise_path(path: str) -> str:
        parts = path.strip("/").split("/")
        normalised = []
        for part in parts:
            if part.isdigit() or (part.startswith("{") and part.endswith("}")):
                normalised.append("{id}")
            else:
                normalised.append(part)
        return "/" + "/".join(normalised) if normalised else "/"
