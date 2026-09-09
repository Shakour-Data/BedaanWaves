"""Gateway-specific middleware.

Provides FastAPI/Starlette middlewares used exclusively by the API Gateway:

- :class:`GatewayRateLimitMiddleware` — Redis-backed distributed rate limiting
  at the gateway edge.
- :class:`GatewayAuthMiddleware` — centralised JWT (RS256) validation before
  requests reach the backend.
- :class:`GatewayLoggingMiddleware` — structured JSON request/response logging
  with correlation ID propagation.
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from collections import deque
from typing import Any

import redis.asyncio as aioredis
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from .config import GatewayConfig, get_gateway_config

logger = logging.getLogger(__name__)

__all__ = [
    "GatewayRateLimitMiddleware",
    "GatewayAuthMiddleware",
    "GatewayLoggingMiddleware",
    "GatewaySecurityHeadersMiddleware",
]


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    client = getattr(request, "client", None)
    host = getattr(client, "host", None) if client is not None else None
    if forwarded and host:
        return forwarded.split(",")[0].strip()
    return host or "unknown"


def _decode_jwt(token: str, config: GatewayConfig) -> dict[str, Any] | None:
    """Decode and validate a JWT access token using RS256 keys."""
    try:
        from jose import JWTError, jwt

        verification_key = config.jwt_public_key or config.jwt_secret
        payload = jwt.decode(
            token,
            verification_key,
            algorithms=[config.jwt_algorithm],
        )
        return payload
    except Exception:
        return None


class _RedisRateLimiter:
    """Redis-backed rate limiter using sorted sets (mirrors backend impl)."""

    def __init__(self, redis_url: str) -> None:
        self.redis_url = redis_url
        self._client: Any = None
        self._connected = False

    async def _get_client(self) -> Any:
        if self._client is None:
            try:
                self._client = aioredis.from_url(
                    self.redis_url, socket_connect_timeout=5
                )
                await self._client.ping()
                self._connected = True
            except Exception as exc:
                logger.warning("Gateway Redis rate limiter connection failed: %s", exc)
                self._connected = False
                self._client = None
        return self._client

    async def is_allowed(
        self, key: str, per_minute: int, per_hour: int
    ) -> tuple[bool, dict]:
        now = time.time()
        client = await self._get_client()
        if client is None:
            return True, {"redis_available": False}

        minute_key = f"gw_rate_limit:{key}:minute"
        hour_key = f"gw_rate_limit:{key}:hour"
        pipeline = client.pipeline()
        minute_ts = int(now)
        hour_ts = int(now / 3600)

        pipeline.zadd(minute_key, {str(minute_ts): minute_ts})
        pipeline.zremrangebyscore(minute_key, 0, now - 60)
        pipeline.zcard(minute_key)

        pipeline.zadd(hour_key, {str(hour_ts): hour_ts})
        pipeline.zremrangebyscore(hour_key, 0, now - 3600)
        pipeline.zcard(hour_key)

        try:
            results = await pipeline.execute()
        except Exception as exc:
            logger.warning("Gateway Redis rate limiter operation failed: %s", exc)
            self._client = None
            self._connected = False
            return True, {"redis_available": False}

        minute_count = results[2]
        hour_count = results[5]
        minute_allowed = minute_count < per_minute
        hour_allowed = hour_count < per_hour

        if minute_allowed:
            await client.expire(minute_key, 120)
        if hour_allowed:
            await client.expire(hour_key, 7200)

        return minute_allowed and hour_allowed, {
            "redis_available": True,
            "minute_count": minute_count,
            "hour_count": hour_count,
            "minute_limit": per_minute,
            "hour_limit": per_hour,
        }

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None
            self._connected = False


class GatewayRateLimitMiddleware(BaseHTTPMiddleware):
    """Distributed rate limiting at the gateway edge using Redis."""

    def __init__(self, app, *, enabled: bool = True) -> None:
        super().__init__(app)
        self.enabled = enabled
        self.config = get_gateway_config()
        self.per_minute = self.config.rate_limit_requests_per_minute
        self.per_hour = self.config.rate_limit_requests_per_hour
        self._limiter = _RedisRateLimiter(self.config.redis_url)
        self._windows: dict[str, deque[float]] = {}
        self._last_activity: dict[str, float] = {}
        self._eviction_interval = 3600
        self._lock = __import__("threading").Lock()

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if not self.enabled:
            return await call_next(request)
        if request.method == "OPTIONS":
            return await call_next(request)

        key = _client_ip(request)
        allowed, info = await self._limiter.is_allowed(key, self.per_minute, self.per_hour)

        if not info.get("redis_available", False):
            if self._fallback_rate_limit(key, time.monotonic()):
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
        response.headers["X-RateLimit-Remaining-Minute"] = str(
            max(0, self.per_minute - info.get("minute_count", 0))
        )
        response.headers["X-RateLimit-Remaining-Hour"] = str(
            max(0, self.per_hour - info.get("hour_count", 0))
        )
        return response

    def _fallback_rate_limit(self, key: str, now: float) -> bool:
        with self._lock:
            self._last_activity[key] = now
            if len(self._windows) > 1000:
                cutoff = now - self._eviction_interval
                for k in [k for k, t in self._last_activity.items() if t < cutoff]:
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


class GatewayAuthMiddleware(BaseHTTPMiddleware):
    """Centralised JWT (RS256) authentication at the gateway edge."""

    def __init__(self, app, *, enabled: bool = True) -> None:
        super().__init__(app)
        self.enabled = enabled
        self.config = get_gateway_config()
        self.api_prefix = self.config.api_prefix
        self.public_paths = set(self.config.is_public_path)
        self.public_prefixes = list(self.config.is_public_prefix)

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
        payload = _decode_jwt(token, self.config)
        if (
            payload is None
            or payload.get("type") != "access"
            or payload.get("sub") is None
        ):
            return self._unauthorized("Invalid or expired token")

        request.state.user_id = payload.get("user_id")
        request.state.username = payload.get("sub")
        request.state.jwt_payload = payload
        return await call_next(request)

    def _try_attach_user(self, request: Request) -> None:
        auth_header = request.headers.get("authorization", "")
        if auth_header.lower().startswith("bearer "):
            token = auth_header.split(" ", 1)[1].strip()
            payload = _decode_jwt(token, self.config)
            if payload and payload.get("type") == "access":
                request.state.user_id = payload.get("user_id")
                request.state.username = payload.get("sub")
                request.state.jwt_payload = payload

    @staticmethod
    def _unauthorized(detail: str) -> JSONResponse:
        return JSONResponse(
            status_code=401,
            headers={"WWW-Authenticate": "Bearer"},
            content={"status": "error", "error_code": "UNAUTHORIZED", "message": detail},
        )


class GatewayLoggingMiddleware(BaseHTTPMiddleware):
    """Structured JSON request/response logging with correlation ID propagation."""

    def __init__(self, app, *, enabled: bool = True) -> None:
        super().__init__(app)
        self.enabled = enabled
        self.config = get_gateway_config()

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if not self.enabled:
            return await call_next(request)

        start_time = time.monotonic()
        correlation_id = getattr(request.state, "correlation_id", None) or uuid.uuid4().hex
        request.state.correlation_id = correlation_id

        self._log(
            "request",
            {
                "method": request.method,
                "path": request.url.path,
                "correlation_id": correlation_id,
                "client_ip": _client_ip(request),
                "user_agent": request.headers.get("user-agent", ""),
            },
        )

        try:
            response = await call_next(request)
        except Exception as exc:
            duration = time.monotonic() - start_time
            self._log(
                "request_error",
                {
                    "method": request.method,
                    "path": request.url.path,
                    "correlation_id": correlation_id,
                    "duration_s": round(duration, 4),
                    "error": str(exc),
                },
                level="error",
            )
            raise

        duration = time.monotonic() - start_time
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Process-Time"] = f"{duration:.3f}"

        self._log(
            "response",
            {
                "method": request.method,
                "path": request.url.path,
                "correlation_id": correlation_id,
                "status_code": response.status_code,
                "duration_s": round(duration, 4),
            },
        )
        return response

    def _log(self, event: str, payload: dict, level: str = "info") -> None:
        if self.config.log_json:
            record = {"event": event, **payload}
            getattr(logger, level)(json.dumps(record, default=str))
        else:
            getattr(logger, level)(
                "%s: %s [correlation_id=%s] %s",
                event.upper(),
                payload.get("method"),
                payload.get("correlation_id"),
                payload.get("path"),
            )


class GatewaySecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Injects OWASP-recommended security headers on every gateway response."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response: Response = await call_next(request)

        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )
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
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), interest-cohort=()"
        )
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["X-Gateway"] = "bedaanwaves-gateway"

        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, proxy-revalidate"
            )
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"

        for header_name in ("Server", "X-Powered-By"):
            try:
                del response.headers[header_name]
            except KeyError:
                pass

        return response