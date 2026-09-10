from __future__ import annotations

import hashlib
import logging
import re
import time
import uuid
from typing import Any, Callable

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.config import Settings, get_settings
from app.infrastructure.utils.redis_rate_limiter import InMemoryRateLimiter, RedisRateLimiter
from app.services.user.auth_service import decode_token
from app.shared.middleware_utils import (
    _CORRELATION_ID_RE,
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
    _validated_access_payload,
    _unauthorized,
    _too_many_requests,
    _register_shutdown,
    _is_rate_limit_exempt_api as _is_rate_limit_exempt,
)

logger = logging.getLogger(__name__)

__all__ = [
    "AuthGuardMiddleware",
    "CorrelationIdMiddleware",
    "RateLimitMiddleware",
    "RequestLoggingMiddleware",
    "SecurityHeadersMiddleware",
    "_client_ip",
]


class CorrelationIdMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        incoming = _request_headers(scope).get("x-correlation-id")
        correlation_id = incoming if incoming and _CORRELATION_ID_RE.fullmatch(incoming) else uuid.uuid4().hex
        _set_state(scope, "correlation_id", correlation_id)

        async def send_with_correlation(message: Message) -> None:
            if message["type"] == "http.response.start":
                _set_header(message, "X-Correlation-ID", correlation_id)
            await send(message)

        await self.app(scope, receive, send_with_correlation)


class AuthGuardMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        *,
        enabled: bool = True,
        settings: Settings | None = None,
        token_decoder: Callable[[str], Any] | None = None,
    ) -> None:
        self.app = app
        self.enabled = enabled
        self.settings = settings or get_settings()
        self.api_prefix = self.settings.API_V1_STR
        self.public_paths = set(self.settings.AUTH_PUBLIC_PATHS)
        self.public_prefixes = tuple(self.settings.AUTH_PUBLIC_PREFIXES)
        self.trusted_proxies = tuple(self.settings.TRUSTED_PROXIES)
        self._token_decoder = token_decoder or decode_token

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
                _replace_request_header(scope, "x-user-id", None)
                _replace_request_header(scope, "x-username", None)
            await self.app(scope, receive, send)
            return

        authorization = headers.get("authorization", "")
        scheme, separator, token = authorization.partition(" ")
        if not separator or scheme.lower() != "bearer" or not token.strip() or any(ch.isspace() for ch in token):
            await _unauthorized("Authorization header missing or malformed")(scope, receive, send)
            return

        payload = _validated_access_payload(token.strip(), self._token_decoder)
        if payload is None:
            await _unauthorized("Invalid or expired token")(scope, receive, send)
            return

        user_id = str(payload["user_id"])
        username = str(payload["sub"])
        _set_state(scope, "user_id", user_id)
        _set_state(scope, "username", username)
        _set_state(scope, "jwt_payload", payload)
        _replace_request_header(scope, "x-user-id", user_id)
        await self.app(scope, receive, send)


class RateLimitMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        *,
        enabled: bool = True,
        settings: Settings | None = None,
        limiter: Any | None = None,
        fallback_limiter: Any | None = None,
    ) -> None:
        self.app = app
        self.settings = settings or get_settings()
        self.enabled = enabled and bool(self.settings.RATE_LIMIT_ENABLED)
        self.per_minute = max(1, int(self.settings.RATE_LIMIT_REQUESTS_PER_MINUTE))
        self.per_hour = max(1, int(self.settings.RATE_LIMIT_REQUESTS_PER_HOUR))
        self.trusted_proxies = tuple(self.settings.TRUSTED_PROXIES)
        self._limiter = limiter or RedisRateLimiter(redis_url=self.settings.REDIS_URL)
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
        if not self.enabled or scope.get("method") == "OPTIONS" or _is_rate_limit_exempt(path):
            await self.app(scope, receive, send)
            return

        client_ip = _client_ip(scope, self.trusted_proxies)
        key = hashlib.sha256(f"api:{client_ip}".encode("utf-8")).hexdigest()
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
                message_source = "redis" if info.get("redis_available") else "fallback"
                _set_header(message, "X-RateLimit-Source", message_source)
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


class RequestLoggingMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        *,
        enabled: bool = True,
        settings: Settings | None = None,
    ) -> None:
        self.app = app
        self.enabled = enabled
        self.settings = settings or get_settings()
        self.trusted_proxies = tuple(self.settings.TRUSTED_PROXIES)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or not self.enabled:
            await self.app(scope, receive, send)
            return

        start_time = time.monotonic()
        path = str(scope.get("path", ""))
        correlation_id = str(_state_value(scope, "correlation_id", "unknown"))
        client_ip = _client_ip(scope, self.trusted_proxies)
        headers = _request_headers(scope)
        user_agent = headers.get("user-agent", "")[:500]
        status_code: int | None = None

        self._log(
            "request",
            method=str(scope.get("method", "")),
            path=path,
            client_ip=client_ip,
            correlation_id=correlation_id,
            user_agent=user_agent,
        )

        async def send_with_timing(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = int(message.get("status", 0))
                process_time = time.monotonic() - start_time
                _set_header(message, "X-Process-Time", f"{process_time:.3f}")
            await send(message)

        try:
            await self.app(scope, receive, send_with_timing)
        except Exception as exc:
            process_time = time.monotonic() - start_time
            logger.error(
                "request_failed path=%s correlation_id=%s duration=%.3fs error_type=%s",
                path,
                correlation_id,
                process_time,
                type(exc).__name__,
            )
            raise

        process_time = time.monotonic() - start_time
        self._log(
            "response",
            method=str(scope.get("method", "")),
            path=path,
            status_code=status_code or 0,
            client_ip=client_ip,
            correlation_id=correlation_id,
            duration_ms=round(process_time * 1000, 3),
        )

    def _log(self, event: str, **values: Any) -> None:
        record = {"event": event, **values}
        if str(self.settings.LOG_FORMAT).lower() == "json":
            import json

            logger.info(json.dumps(record, ensure_ascii=False, default=str))
        else:
            logger.info(
                "%s path=%s status=%s correlation_id=%s client=%s duration_ms=%s",
                event,
                record.get("path", ""),
                record.get("status_code", "-"),
                record.get("correlation_id", "-"),
                record.get("client_ip", "-"),
                record.get("duration_ms", "-"),
            )


class SecurityHeadersMiddleware:
    def __init__(self, app: ASGIApp, *, settings: Settings | None = None) -> None:
        self.app = app
        self.settings = settings or get_settings()

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
        headers = _request_headers(scope)
        content_type = (_header(message, "content-type") or "").lower()
        path = str(scope.get("path", ""))

        if self.settings.ENABLE_HTTPS or str(self.settings.ENVIRONMENT).lower() == "production" or scope.get("scheme") == "https":
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

        if path == "/api" or path.startswith("/api/") or path == "/data-health":
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