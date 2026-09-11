"""Shared middleware utilities for API and Gateway.

This module extracts common functionality from:
- app.api.middleware
- app.gateway.middleware

to eliminate ~400 lines of duplicated code.
"""

from __future__ import annotations

import hashlib
import ipaddress
import logging
import re
import time
import uuid
from typing import Any, Callable

from starlette.datastructures import MutableHeaders
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

logger = logging.getLogger(__name__)

# --- Constants ---
_CORRELATION_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}")
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

# --- Header Utilities ---


def _header(container: Any, name: str) -> str | None:
    """Extract a header value from ASGI message/scope headers."""
    target = name.lower().encode("latin-1")
    for key, value in container.get("headers", []):
        raw_key = key.lower() if isinstance(key, bytes) else str(key).lower().encode("latin-1")
        if raw_key == target:
            return value.decode("latin-1", "replace") if isinstance(value, bytes) else str(value)
    return None


def _set_header(message: Message | MutableHeaders, name: str, value: str) -> None:
    """Set a header in an ASGI message or MutableHeaders object."""
    if isinstance(message, MutableHeaders):
        message[name] = value
        return

    target = name.lower().encode("latin-1")
    raw_value = value.encode("latin-1", "replace")
    headers = [
        (key, val)
        for key, val in message.get("headers", [])
        if not (
            (key.lower() if isinstance(key, bytes) else str(key).lower().encode("latin-1"))
            == target
        )
    ]
    headers.append((target, raw_value))
    message["headers"] = headers


def _replace_request_header(scope: Scope, name: str, value: str | None) -> None:
    """Replace a header in the request scope."""
    target = name.lower().encode("latin-1")
    headers = [
        (key, val)
        for key, val in scope.get("headers", [])
        if not (
            (key.lower() if isinstance(key, bytes) else str(key).lower().encode("latin-1"))
            == target
        )
    ]
    if value is not None:
        headers.append((target, value.encode("latin-1", "replace")))
    scope["headers"] = headers


def _request_headers(scope: Scope) -> dict[str, str]:
    """Extract all request headers as a lowercase dict."""
    result: dict[str, str] = {}
    for key, value in scope.get("headers", []):
        raw_key = key.decode("latin-1", "ignore") if isinstance(key, bytes) else str(key)
        raw_value = value.decode("latin-1", "replace") if isinstance(value, bytes) else str(value)
        result[raw_key.lower()] = raw_value
    return result


# --- State Utilities ---


def _state_value(scope: Scope, name: str, default: Any = None) -> Any:
    """Get a value from the ASGI scope state."""
    state = scope.get("state")
    if isinstance(state, dict):
        return state.get(name, default)
    return getattr(state, name, default)


def _set_state(scope: Scope, name: str, value: Any) -> None:
    """Set a value in the ASGI scope state."""
    state = scope.setdefault("state", {})
    if isinstance(state, dict):
        state[name] = value
    else:
        setattr(state, name, value)


# --- IP Extraction ---


def _is_trusted_proxy(host: str | None, trusted_proxies: tuple[str, ...] | list[str]) -> bool:
    """Check if a host is in the trusted proxies list."""
    if not host:
        return False
    try:
        address = ipaddress.ip_address(host.strip("[]"))
    except ValueError:
        return False
    for proxy in trusted_proxies:
        item = proxy.strip()
        if not item:
            continue
        if item == "*":
            return True
        try:
            if "/" in item:
                if address in ipaddress.ip_network(item, strict=False):
                    return True
            elif address == ipaddress.ip_address(item.strip("[]")):
                return True
        except ValueError:
            continue
    return False


def _forwarded_ip(value: str) -> str | None:
    """Extract the first valid IP from X-Forwarded-For header."""
    for item in value.split(","):
        candidate = item.strip()
        if candidate.startswith("["):
            end = candidate.find("]")
            if end != -1:
                candidate = candidate[1:end]
            else:
                candidate = candidate.split(":", 1)[0]
        else:
            candidate = candidate.split(":", 1)[0]
        try:
            ipaddress.ip_address(candidate)
        except ValueError:
            continue
        return candidate
    return None


def _client_ip(
    scope: Scope,
    trusted_proxies: tuple[str, ...] | list[str] | None = None,
) -> str:
    """Extract client IP, respecting X-Forwarded-For from trusted proxies."""
    client = scope.get("client")
    direct_host = str(client[0]) if client else None
    proxies = tuple(trusted_proxies or ())
    forwarded = _request_headers(scope).get("x-forwarded-for")
    if forwarded and _is_trusted_proxy(direct_host, proxies):
        client_ip = _forwarded_ip(forwarded)
        if client_ip:
            return client_ip
    return direct_host or "unknown"


# --- Path Matching ---


def _normalise_path(path: str) -> str:
    """Normalize a path: ensure leading slash, remove trailing slash."""
    if not path.startswith("/"):
        path = f"/{path}"
    return path.rstrip("/") or "/"


def _path_matches(path: str, prefix: str) -> bool:
    """Check if path matches prefix (exact or subpath)."""
    normal_path = _normalise_path(path)
    normal_prefix = _normalise_path(prefix)
    if normal_prefix == "/":
        return True
    return normal_path == normal_prefix or normal_path.startswith(f"{normal_prefix}/")


# --- Validation ---


def _validated_user_id(value: Any) -> str | None:
    """Validate a value as a UUID string."""
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return str(uuid.UUID(value.strip()))
    except (AttributeError, ValueError, TypeError):
        return None


# --- Error Responses ---


def _unauthorized(detail: str) -> JSONResponse:
    """Create a 401 Unauthorized response."""
    return JSONResponse(
        status_code=401,
        headers={"WWW-Authenticate": "Bearer"},
        content={"status": "error", "error_code": "UNAUTHORIZED", "message": detail},
    )


def _too_many_requests(detail: str, retry_after: int = 60) -> JSONResponse:
    """Create a 429 Too Many Requests response."""
    response = JSONResponse(
        status_code=429,
        content={"status": "error", "error_code": "RATE_LIMITED", "message": detail},
    )
    response.headers["Retry-After"] = str(max(1, int(retry_after)))
    return response


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


# --- Shutdown Registration ---


def _register_shutdown(app: ASGIApp, callback: Callable[[], Any]) -> None:
    """Register a shutdown callback on the ASGI app."""
    register = getattr(app, "add_event_handler", None)
    if callable(register):
        try:
            register("shutdown", callback)
        except (TypeError, ValueError):
            pass


# --- Rate Limit Exempt Paths (API-specific) ---
# Note: Gateway has its own exempt paths in gateway/middleware.py
_RateLimitExemptPathsAPI = {
    "/",
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/api/v1/health",
    "/api/v1/docs",
    "/api/v1/redoc",
    "/api/v1/openapi.json",
}
_RateLimitExemptPrefixesAPI = (
    "/docs",
    "/redoc",
    "/openapi.json",
    "/api/v1/health",
    "/api/v1/docs",
    "/api/v1/redoc",
    "/api/v1/openapi.json",
)


def _is_rate_limit_exempt_api(path: str) -> bool:
    """Check if a path is exempt from rate limiting (API middleware)."""
    normal_path = _normalise_path(path)
    if normal_path in _RateLimitExemptPathsAPI:
        return True
    return any(_path_matches(normal_path, prefix) for prefix in _RateLimitExemptPrefixesAPI)


# --- JWT Payload Validation ---


def _validated_access_payload(token: str, decoder: Callable[[str], Any]) -> dict[str, Any] | None:
    """Validate an access token payload."""
    try:
        payload = decoder(token)
    except Exception as exc:
        logger.info("Token validation failed: %s", type(exc).__name__)
        return None
    if not isinstance(payload, dict):
        return None
    if payload.get("type") != "access":
        return None
    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject.strip():
        return None
    user_id = _validated_user_id(payload.get("user_id"))
    if user_id is None:
        return None
    result = dict(payload)
    result["sub"] = subject.strip()
    result["user_id"] = user_id
    return result