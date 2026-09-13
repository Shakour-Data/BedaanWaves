from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import time
import uuid
from typing import Any, Callable

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.infrastructure.utils.redis_rate_limiter import InMemoryRateLimiter, RedisRateLimiter

from .config import GatewayConfig, get_gateway_config
from app.shared.middleware_utils import (
    _CORRELATION_ID_RE as _SHARED_CORRELATION_ID_RE,
    _header,
    _set_header,
    _replace_request_header,
    _state_value,
    _set_state,
    _request_headers,
    _client_ip,
    _normalise_path,
    _path_matches,
    _validated_user_id,
    _unauthorized,
    _too_many_requests,
    _register_shutdown,
)

logger = logging.getLogger(__name__)

__all__ = [
    "GatewayAuthMiddleware",
    "GatewayLoggingMiddleware",
    "GatewayRateLimitMiddleware",
    "GatewaySecurityHeadersMiddleware",
    "_RedisRateLimiter",
    "_client_ip",
    "_decode_jwt",
]

_RedisRateLimiter = RedisRateLimiter
# Use shared correlation ID regex
_CORRELATION_ID_RE = _SHARED_CORRELATION_ID_RE

# Gateway-specific JWT algorithms
_ALLOWED_JWT_ALGORITHMS = {
    "HS256",
    "HS384",
    "HS512",
    "RS256",
    "RS384",
    "RS512",
    "ES256",
    "ES384",
    "ES512",
}

# Gateway-specific rate limit exempt paths
_RateLimitExemptPathsGateway = {
    "/",
    "/health",
    "/health/live",
    "/health/ready",
    "/health/ready/services",
    "/docs",
    "/redoc",
    "/openapi.json",
}
_RateLimitExemptPrefixesGateway = (
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
)


def _is_rate_limit_exempt(path: str, proxy_prefix: str) -> bool:
    """Check if a path is exempt from rate limiting (Gateway middleware)."""
    normal_path = _normalise_path(path)
    if normal_path in _RateLimitExemptPathsGateway:
        return True
    return any(_path_matches(normal_path, prefix) for prefix in _RateLimitExemptPrefixesGateway)


def _jwt_material(config: GatewayConfig) -> tuple[str, str | None]:
    """Resolve JWT algorithm and verification key from config and environment."""
    gateway_algorithm = os.environ.get("GATEWAY_JWT_ALGORITHM", "").strip().upper()
    configured_algorithm = str(getattr(config, "jwt_algorithm", "") or "").strip().upper()
    public_key = str(getattr(config, "jwt_public_key", "") or "").strip()
    secret = str(getattr(config, "jwt_secret", "") or "").strip()

    if gateway_algorithm:
        algorithm = gateway_algorithm
    elif configured_algorithm == "RS256" and not public_key:
        algorithm = os.environ.get("JWT_ALGORITHM", "").strip().upper() or os.environ.get("ALGORITHM", "").strip().upper() or configured_algorithm
    else:
        algorithm = configured_algorithm

    if algorithm in {"HS256", "HS384", "HS512"}:
        key = secret or os.environ.get("GATEWAY_JWT_SECRET", "").strip() or os.environ.get("JWT_SECRET", "").strip()
    elif algorithm in {"RS256", "RS384", "RS512", "ES256", "ES384", "ES512"}:
        key = public_key or os.environ.get("GATEWAY_JWT_PUBLIC_KEY", "").strip() or os.environ.get("JWT_PUBLIC_KEY", "").strip()
    else:
        key = None
    return algorithm or "RS256", key or None


def _decode_jwt(token: str, config: GatewayConfig) -> dict[str, Any] | None:
    """Decode and validate a JWT token for the gateway."""
    algorithm, verification_key = _jwt_material(config)
    if not verification_key or algorithm not in _ALLOWED_JWT_ALGORITHMS:
        return None
    try:
        from jose import jwt

        payload = jwt.decode(
            token,
            verification_key,
            algorithms=[algorithm],
            options={"require": ["exp", "sub", "type", "user_id"]},
        )
    except Exception as exc:
        logger.info("Gateway token validation failed: %s", type(exc).__name__)
        return None
    if not isinstance(payload, dict):
        return None
    subject = payload.get("sub")
    user_id = _validated_user_id(payload.get("user_id"))
    if payload.get("type") != "access" or not isinstance(subject, str) or not subject.strip() or user_id is None:
        return None
    result = dict(payload)
    result["sub"] = subject.strip()
    result["user_id"] = user_id
    return result


def _auth_unavailable() -> JSONResponse:
    """Create a 503 response when gateway auth is not configured."""
    return JSONResponse(
        status_code=503,
        content={
            "status": "error",
            "error_code": "GATEWAY_AUTH_UNAVAILABLE",
            "message": "Gateway JWT verification is not configured",
        },
    )


class GatewayRateLimitMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        *,
        enabled: bool = True,
        config: GatewayConfig | None = None,
        limiter: Any | None = None,
        fallback_limiter: Any | None = None,
    ) -> None:
        self.app = app
        self.config = config or get_gateway_config()
        self.enabled = enabled and bool(self.config.rate_limit_enabled)
        self.per_minute = max(1, int(self.config.rate_limit_requests_per_minute))
        self.per_hour = max(1, int(self.config.rate_limit_requests_per_hour))
        self.trusted_proxies = tuple(getattr(self.config, "trusted_proxies", ()))
        self._limiter = limiter or RedisRateLimiter(redis_url=self.config.redis_url)
        self._fallback_limiter = fallback_limiter or InMemoryRateLimiter()
        _register_shutdown(app, self.close)

    async def close(self) -> None:
        close_method = getattr(self._limiter, "close", None)
        if callable(close_method):
            result = close_method()
            if result is not None:
                await result

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = str(scope.get("path", ""))
        if not self.enabled or scope.get("method") == "OPTIONS" or _is_rate_limit_exempt(path, self.config.proxy_prefix):
            await self.app(scope, receive, send)
            return

        client_ip = _client_ip(scope, self.trusted_proxies)
        key = hashlib.sha256(f"gateway:{client_ip}".encode("utf-8")).hexdigest()
        allowed, info = await self._limiter.is_allowed(key, self.per_minute, self.per_hour)
        info = dict(info or {})

        if not info.get("redis_available", False):
            fallback_allowed, fallback_info = await self._fallback_limiter.is_allowed(
                key, self.per_minute, self.per_hour
            )
            info.update(fallback_info or {})
            info["redis_available"] = False
            if not fallback_allowed:
                retry_after = max(1, int(info.get("retry_after", 60)))
                response = _too_many_requests("Rate limit exceeded (fallback)", retry_after)
                self._add_headers(response.headers, info)
                response.headers["X-RateLimit-Source"] = "fallback"
                await response(scope, receive, send)
                return

        if not allowed:
            hourly = int(info.get("hour_count", 0)) >= self.per_hour
            retry_after = max(1, int(info.get("hour_reset", 3600 if hourly else 60)))
            response = _too_many_requests(
                "Hourly rate limit exceeded" if hourly else "Rate limit exceeded",
                retry_after,
            )
            self._add_headers(response.headers, info)
            response.headers["X-RateLimit-Source"] = "redis" if info.get("redis_available") else "fallback"
            await response(scope, receive, send)
            return

        async def send_with_rate_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                self._add_headers(message, info)
                _set_header(message, "X-RateLimit-Source", "redis" if info.get("redis_available") else "fallback")
            await send(message)

        await self.app(scope, receive, send_with_rate_headers)

    def _add_headers(self, container: Any, info: dict[str, Any]) -> None:
        minute_count = max(0, int(info.get("minute_count", 0)))
        hour_count = max(0, int(info.get("hour_count", 0)))
        _set_header(container, "X-RateLimit-Limit-Minute", str(self.per_minute))
        _set_header(container, "X-RateLimit-Limit-Hour", str(self.per_hour))
        _set_header(container, "X-RateLimit-Remaining-Minute", str(max(0, self.per_minute - minute_count)))
        _set_header(container, "X-RateLimit-Remaining-Hour", str(max(0, self.per_hour - hour_count)))
        minute_reset = max(1, int(info.get("minute_reset", 60 - (int(time.time()) % 60))))
        hour_reset = max(1, int(info.get("hour_reset", 3600 - (int(time.time()) % 3600))))
        _set_header(container, "X-RateLimit-Reset-Minute", str(minute_reset))
        _set_header(container, "X-RateLimit-Reset-Hour", str(hour_reset))


class GatewayAuthMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        *,
        enabled: bool = True,
        config: GatewayConfig | None = None,
    ) -> None:
        self.app = app
        self.config = config or get_gateway_config()
        self.enabled = enabled and bool(self.config.auth_enabled)
        self.api_prefix = self.config.api_prefix
        self.public_paths = set(self.config.is_public_path)
        self.public_prefixes = tuple(self.config.is_public_prefix)
        self.algorithm, self.verification_key = _jwt_material(self.config)

    def _is_public(self, path: str) -> bool:
        normal_path = _normalise_path(path)
        if normal_path in {_normalise_path(item) for item in self.public_paths}:
            return True
        return any(_path_matches(normal_path, prefix) for prefix in self.public_prefixes)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = str(scope.get("path", ""))
        headers = _request_headers(scope)

        if (
            not self.enabled
            or scope.get("method") == "OPTIONS"
            or not _path_matches(path, self.api_prefix)
            or self._is_public(path)
        ):
            if not self.enabled:
                self._attach_user(scope, headers)
            await self.app(scope, receive, send)
            return

        # Auth enabled and protected path - clear any existing user headers first
        _replace_request_header(scope, "x-user-id", None)
        _replace_request_header(scope, "x-username", None)

        if not self.verification_key or self.algorithm not in _ALLOWED_JWT_ALGORITHMS:
            await _auth_unavailable()(scope, receive, send)
            return

        authorization = headers.get("authorization", "")
        scheme, separator, token = authorization.partition(" ")
        if not separator or scheme.lower() != "bearer" or not token.strip() or any(ch.isspace() for ch in token):
            await _unauthorized("Authorization header missing or malformed")(scope, receive, send)
            return

        payload = _decode_jwt(token.strip(), self.config)
        if payload is None:
            await _unauthorized("Invalid or expired token")(scope, receive, send)
            return

        user_id = str(payload["user_id"])
        username = str(payload["sub"])
        _set_state(scope, "user_id", user_id)
        _set_state(scope, "username", username)
        _set_state(scope, "jwt_payload", payload)
        _replace_request_header(scope, "x-user-id", user_id)
        _replace_request_header(scope, "x-username", username)
        await self.app(scope, receive, send)

    def _attach_user(self, scope: Scope, headers: dict[str, str]) -> None:
        authorization = headers.get("authorization", "")
        scheme, separator, token = authorization.partition(" ")
        if not separator or scheme.lower() != "bearer" or not token.strip():
            return
        payload = _decode_jwt(token.strip(), self.config)
        if payload is None:
            return
        user_id = str(payload["user_id"])
        username = str(payload["sub"])
        _set_state(scope, "user_id", user_id)
        _set_state(scope, "username", username)
        _set_state(scope, "jwt_payload", payload)
        _replace_request_header(scope, "x-user-id", user_id)
        _replace_request_header(scope, "x-username", username)


class GatewayLoggingMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        *,
        enabled: bool = True,
        config: GatewayConfig | None = None,
    ) -> None:
        self.app = app
        self.config = config or get_gateway_config()
        self.enabled = enabled
        self.trusted_proxies = tuple(getattr(self.config, "trusted_proxies", ()))

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or not self.enabled:
            await self.app(scope, receive, send)
            return

        start_time = time.monotonic()
        headers = _request_headers(scope)
        incoming = headers.get("x-correlation-id")
        correlation_id = incoming if incoming and _CORRELATION_ID_RE.fullmatch(incoming) else uuid.uuid4().hex
        _set_state(scope, "correlation_id", correlation_id)
        path = str(scope.get("path", ""))
        client_ip = _client_ip(scope, self.trusted_proxies)
        user_agent = headers.get("user-agent", "")[:500]
        status_code: int | None = None

        self._log(
            "request",
            method=str(scope.get("method", "")),
            path=path,
            correlation_id=correlation_id,
            client_ip=client_ip,
            user_agent=user_agent,
        )

        async def send_with_logging(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = int(message.get("status", 0))
                _set_header(message, "X-Correlation-ID", correlation_id)
                _set_header(message, "X-Process-Time", f"{time.monotonic() - start_time:.3f}")
            await send(message)

        try:
            await self.app(scope, receive, send_with_logging)
        except Exception as exc:
            self._log(
                "request_error",
                method=str(scope.get("method", "")),
                path=path,
                correlation_id=correlation_id,
                duration_ms=round((time.monotonic() - start_time) * 1000, 3),
                error_type=type(exc).__name__,
                level="error",
            )
            raise

        self._log(
            "response",
            method=str(scope.get("method", "")),
            path=path,
            status_code=status_code or 0,
            correlation_id=correlation_id,
            client_ip=client_ip,
            duration_ms=round((time.monotonic() - start_time) * 1000, 3),
        )

    def _log(self, event: str, level: str = "info", **values: Any) -> None:
        record = {"event": event, **values}
        if self.config.log_json:
            getattr(logger, level)(json.dumps(record, ensure_ascii=False, default=str))
        else:
            getattr(logger, level)(
                "%s method=%s path=%s status=%s correlation_id=%s duration_ms=%s",
                event,
                record.get("method", ""),
                record.get("path", ""),
                record.get("status_code", "-"),
                record.get("correlation_id", "-"),
                record.get("duration_ms", "-"),
            )


class GatewaySecurityHeadersMiddleware:
    def __init__(self, app: ASGIApp, *, config: GatewayConfig | None = None) -> None:
        self.app = app
        self.config = config or get_gateway_config()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_security_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                self._apply(scope, message)
            await send(message)

        await self.app(scope, receive, send_with_security_headers)

    def _apply(self, scope: Scope, message: Message) -> None:
        content_type = (_header(message, "content-type") or "").lower()
        path = str(scope.get("path", ""))
        enable_https = bool(getattr(self.config, "enable_https", False)) or os.environ.get("GATEWAY_ENABLE_HTTPS", "false").lower() in {"1", "true", "yes", "on"}
        if enable_https or scope.get("scheme") == "https":
            _set_header(
                message,
                "Strict-Transport-Security",
                "max-age=31536000; includeSubDomains; preload",
            )

        if content_type.startswith("text/html"):
            csp = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data: https:; "
                "connect-src 'self' ws: wss: "
                "http://localhost:3000 http://localhost:3005 "
                "http://127.0.0.1:3000 http://127.0.0.1:3005 "
                "ws://localhost:3000 ws://localhost:3005 "
                "ws://127.0.0.1:3000 ws://127.0.0.1:3005; "
                "frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
            )
        else:
            csp = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"
        _set_header(message, "Content-Security-Policy", csp)
        _set_header(message, "X-Frame-Options", "DENY")
        _set_header(message, "X-Content-Type-Options", "nosniff")
        _set_header(message, "Referrer-Policy", "strict-origin-when-cross-origin")
        _set_header(
            message,
            "Permissions-Policy",
            "camera=(), microphone=(), geolocation=(), interest-cohort=()",
        )
        _set_header(message, "Cross-Origin-Resource-Policy", "same-origin")
        _set_header(message, "X-Gateway", "bedaanwaves-gateway")

        proxy_prefix = _normalise_path(self.config.proxy_prefix)
        if _path_matches(path, proxy_prefix) or path.startswith("/api/"):
            _set_header(message, "Cache-Control", "no-store, no-cache, must-revalidate, proxy-revalidate")
            _set_header(message, "Pragma", "no-cache")
            _set_header(message, "Expires", "0")

        for header_name in ("Server", "X-Powered-By"):
            target = header_name.lower().encode("latin-1")
            message["headers"] = [
                (key, value)
                for key, value in message.get("headers", [])
                if not (
                    (key.lower() if isinstance(key, bytes) else str(key).lower().encode("latin-1"))
                    == target
                )
            ]