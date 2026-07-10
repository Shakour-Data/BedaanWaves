"""Global API Middleware

Provides three FastAPI/Starlette middlewares:

* ``CorrelationIdMiddleware``  - attaches a request id (X-Correlation-ID) used for
  tracing and request logging.
* ``AuthGuardMiddleware``      - the global authentication guard. When
  ``REQUIRE_AUTH`` is enabled it rejects unauthenticated requests to every
  protected API path (with a configurable public allow-list).
* ``RateLimitMiddleware``     - in-memory sliding-window rate limiting keyed by
  client IP, honoring the ``RATE_LIMIT_*`` configuration.
"""

import time
import uuid
from collections import deque
from typing import Dict, List, Optional

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import get_settings
from app.services.user.auth_service import decode_token

settings = get_settings()


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


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

    def __init__(self, app, *, enabled: bool = True):
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
            # Still record a user id when a valid token is present (best effort).
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
    """In-memory sliding-window rate limiter keyed by client IP."""

    def __init__(self, app, *, enabled: bool = True):
        super().__init__(app)
        self.enabled = enabled
        self.per_minute = settings.RATE_LIMIT_REQUESTS_PER_MINUTE
        self.per_hour = settings.RATE_LIMIT_REQUESTS_PER_HOUR
        self._windows: Dict[str, deque] = {}

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if not self.enabled:
            return await call_next(request)

        if request.method == "OPTIONS":
            return await call_next(request)

        key = f"{_client_ip(request)}:{request.url.path}"
        now = time.monotonic()
        window = self._windows.setdefault(key, deque())

        # Drop entries older than one hour.
        cutoff = now - 3600
        while window and window[0] < cutoff:
            window.popleft()

        if len(window) >= self.per_hour:
            return self._too_many_requests("Hourly rate limit exceeded")
        # Drop entries older than one minute for the per-minute check.
        minute_cutoff = now - 60
        while window and window[0] < minute_cutoff:
            window.popleft()
        if len(window) >= self.per_minute:
            return self._too_many_requests("Rate limit exceeded")

        window.append(now)
        response = await call_next(request)
        response.headers["X-RateLimit-Limit-Minute"] = str(self.per_minute)
        response.headers["X-RateLimit-Remaining-Minute"] = str(max(0, self.per_minute - len(window)))
        return response

    @staticmethod
    def _too_many_requests(detail: str) -> JSONResponse:
        return JSONResponse(
            status_code=429,
            content={"status": "error", "error_code": "RATE_LIMITED", "message": detail},
        )


def protected_dependencies() -> List:
    """Router-level dependencies enforcing auth when the global guard is enabled.

    Returns a list containing ``Depends(get_current_active_user)`` only when
    ``REQUIRE_AUTH`` is on, so development keeps working with the guard disabled.
    """
    if not settings.REQUIRE_AUTH:
        return []
    from fastapi import Depends

    from app.api.dependencies import get_current_active_user

    return [Depends(get_current_active_user)]
