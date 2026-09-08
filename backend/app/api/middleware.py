"""Global API Middleware

Provides four FastAPI/Starlette middlewares:

* ``CorrelationIdMiddleware``  - attaches a request id (X-Correlation-ID) used for
  tracing and request logging.
* ``AuthGuardMiddleware``      - the global authentication guard. When
  ``REQUIRE_AUTH`` is enabled it rejects unauthenticated requests to every
  protected API path (with a configurable public allow-list).
* ``RateLimitMiddleware``     - Redis-backed distributed sliding-window rate
  limiting keyed by client IP, honoring the ``RATE_LIMIT_*`` configuration.
  Falls back to in-memory limiting when Redis is unavailable.
* ``RequestLoggingMiddleware`` - logs incoming requests and responses with timing.
* ``SecurityHeadersMiddleware`` - adds OWASP-recommended security headers.
"""

from __future__ import annotations

import logging
import threading
import time
import uuid
from collections import deque

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import get_settings
from app.infrastructure.utils.redis_rate_limiter import RedisRateLimiter
from app.services.user.auth_service import decode_token

settings = get_settings()

__all__ = [
    "CorrelationIdMiddleware",
    "AuthGuardMiddleware",
    "RateLimitMiddleware",
    "RequestLoggingMiddleware",
    "SecurityHeadersMiddleware",
    "_client_ip",
]


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    client = getattr(request, "client", None)
    client_host = getattr(client, "host", None) if client is not None else None
    if forwarded and client_host and client_host in settings.TRUSTED_PROXIES:
        return forwarded.split(",")[0].strip()
    return client_host or "unknown"


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Generate/propagate a correlation id for every request."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        correlation_id = request.headers.get("x-correlation-id") or uuid.uuid4().hex
        request.state.correlation_id = correlation_id
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        return response


class AuthGuardMiddleware(BaseHTTPMiddleware):
    """Enforce a valid Bearer access token on protected API paths."""

    def __init__(self, app, *, enabled: bool = True) -> None:
        super().__init__(app)
        self.enabled = enabled
        self.api_prefix = settings.API_V1_STR
        self.public_paths = set(settings.AUTH_PUBLIC_PATHS)
        self.public_prefixes = list(settings.AUTH_PUBLIC_PREFIXES)

    def _is_public(self, path: str) -> bool:
        if path in self.public_paths:
            return True
        for prefix in self.public_prefixes:
            if path.startswith(prefix):
                return True
        return False

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if not self.enabled:
            self._try_attach_user(request)
            return await call_next(request)

        if request.method == "OPTIONS":
            return await call_next(request)

        path = request.url.path
        if not path.startswith(self.api_prefix) or self._is_public(path):
            return await call_next(request)

        auth_header = request.headers.get("authorization", "")
        if not auth_header.lower().startswith("bearer "):
            return self._unauthorized("Authorization header missing or malformed")

        token = auth_header.split(" ", 1)[1].strip()
        payload = decode_token(token)
        if payload is None or payload.get("type") != "access" or payload.get("sub") is None:
            return self._unauthorized("Invalid or expired token")

        request.state.user_id = payload.get("user_id")
        request.state.username = payload.get("sub")
        return await call_next(request)

    def _try_attach_user(self, request: Request) -> None:
        auth_header = request.headers.get("authorization", "")
        if auth_header.lower().startswith("bearer "):
            token = auth_header.split(" ", 1)[1].strip()
            payload = decode_token(token)
            if payload and payload.get("type") == "access":
                request.state.user_id = payload.get("user_id")
                request.state.username = payload.get("sub")

    @staticmethod
    def _unauthorized(detail: str) -> JSONResponse:
        return JSONResponse(
            status_code=401,
            headers={"WWW-Authenticate": "Bearer"},
            content={"status": "error", "error_code": "UNAUTHORIZED", "message": detail},
        )


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Redis-backed distributed sliding-window rate limiter keyed by client IP.

    Falls back to in-memory limiting when Redis is unavailable.
    """

    def __init__(self, app, *, enabled: bool = True) -> None:
        super().__init__(app)
        self.enabled = enabled
        self.per_minute = settings.RATE_LIMIT_REQUESTS_PER_MINUTE
        self.per_hour = settings.RATE_LIMIT_REQUESTS_PER_HOUR
        self._redis_limiter = RedisRateLimiter(redis_url=settings.REDIS_URL)
        self._windows: dict[str, deque[float]] = {}
        self._last_activity: dict[str, float] = {}
        self._eviction_interval = 3600
        self._lock = threading.Lock()

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if not self.enabled:
            return await call_next(request)

        if request.method == "OPTIONS":
            return await call_next(request)

        key = _client_ip(request)
        now = time.monotonic()

        allowed, info = await self._redis_limiter.is_allowed(
            key, self.per_minute, self.per_hour
        )

        if not info.get("redis_available", False):
            fallback_blocked = self._fallback_rate_limit(key, now)
            if fallback_blocked:
                return self._too_many_requests("Rate limit exceeded (fallback)")

        if not allowed:
            response = self._too_many_requests(
                "Hourly rate limit exceeded"
                if info.get("hour_count", 0) >= self.per_hour
                else "Rate limit exceeded"
            )
            response.headers["Retry-After"] = (
                str(3600) if info.get("hour_count", 0) >= self.per_hour else str(60)
            )
            return response

        response = await call_next(request)
        response.headers["X-RateLimit-Limit-Minute"] = str(self.per_minute)
        response.headers["X-RateLimit-Limit-Hour"] = str(self.per_hour)
        remaining_minute = max(0, self.per_minute - info.get("minute_count", 0))
        remaining_hour = max(0, self.per_hour - info.get("hour_count", 0))
        response.headers["X-RateLimit-Remaining-Minute"] = str(remaining_minute)
        response.headers["X-RateLimit-Remaining-Hour"] = str(remaining_hour)
        return response

    def _fallback_rate_limit(self, key: str, now: float) -> bool:
        """In-memory fallback when Redis is unavailable. Returns True if blocked."""
        with self._lock:
            self._last_activity[key] = now
            if len(self._windows) > 1000:
                cutoff = now - self._eviction_interval
                inactive_keys = [k for k, t in self._last_activity.items() if t < cutoff]
                for k in inactive_keys:
                    self._windows.pop(k, None)
                    self._last_activity.pop(k, None)

            window = self._windows.setdefault(key, deque())
            cutoff = now - 3600
            while window and window[0] < cutoff:
                window.popleft()

            if len(window) >= self.per_hour:
                return True

            minute_cutoff = now - 60
            while window and window[0] < minute_cutoff:
                window.popleft()
            if len(window) >= self.per_minute:
                return True

            window.append(now)
            return False

    @staticmethod
    def _too_many_requests(detail: str) -> Response:
        return JSONResponse(
            status_code=429,
            content={"status": "error", "error_code": "RATE_LIMITED", "message": detail},
        )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log incoming requests and responses."""

    def __init__(self, app, *, enabled: bool = True) -> None:
        super().__init__(app)
        self.enabled = enabled

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if not self.enabled:
            return await call_next(request)

        start_time = time.monotonic()
        correlation_id = getattr(request.state, "correlation_id", "unknown")
        logger = logging.getLogger(__name__)
        logger.info(
            "Request: %s %s [correlation_id=%s] client=%s",
            request.method,
            request.url.path,
            correlation_id,
            _client_ip(request),
        )

        try:
            response = await call_next(request)
        except Exception as exc:
            process_time = time.monotonic() - start_time
            logger.error(
                "Request failed: %s %s [correlation_id=%s] duration=%.3fs error=%s",
                request.method,
                request.url.path,
                correlation_id,
                process_time,
                exc,
            )
            raise

        process_time = time.monotonic() - start_time
        response.headers["X-Process-Time"] = f"{process_time:.3f}"
        logger.info(
            "Response: %s %s [correlation_id=%s] status=%d duration=%.3fs",
            request.method,
            request.url.path,
            correlation_id,
            response.status_code,
            process_time,
        )
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Adds security headers to every response per OWASP guidelines.

    Headers:
    - Strict-Transport-Security (HSTS)
    - Content-Security-Policy
    - X-Frame-Options
    - X-Content-Type-Options
    - Referrer-Policy
    - Permissions-Policy
    - X-XSS-Protection
    """

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        # HSTS - Force HTTPS for 1 year, include subdomains
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )

        # CSP - Restrict resource sources
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.bedaanwaves.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "img-src 'self' data: https:; "
            "font-src 'self' https://fonts.gstatic.com; "
            "connect-src 'self' https://api.bedaanwaves.com wss://api.bedaanwaves.com; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions policy - restrict browser features
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), interest-cohort=()"
        )

        # XSS protection (legacy)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Remove server identity disclosure safely
        for header_name in ("Server", "X-Powered-By"):
            try:
                del response.headers[header_name]
            except KeyError:
                pass

        return response
