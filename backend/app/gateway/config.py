"""Gateway configuration.

Centralises all tunables for the API Gateway: backend target URL, ports,
rate-limit thresholds, JWT settings, Redis connection and logging behaviour.

All values can be overridden through environment variables (see the
``GATEWAY_`` prefix below).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class GatewayConfig:
    """Configuration container for the BedaanWaves API Gateway."""

    # ------------------------------------------------------------------
    # Networking
    # ------------------------------------------------------------------
    host: str = field(
        default_factory=lambda: os.environ.get("GATEWAY_HOST", "0.0.0.0")
    )
    port: int = field(
        default_factory=lambda: int(os.environ.get("GATEWAY_PORT", "8000"))
    )

    # URL of the backend FastAPI application that the gateway proxies to.
    backend_url: str = field(
        default_factory=lambda: os.environ.get(
            "GATEWAY_BACKEND_URL", "http://localhost:3000"
        ).rstrip("/")
    )

    # Path prefix that the gateway forwards to the backend. Anything under
    # this prefix is proxied; everything else is handled locally.
    proxy_prefix: str = field(
        default_factory=lambda: os.environ.get("GATEWAY_PROXY_PREFIX", "/api/v1")
    )

    trusted_proxies: tuple[str, ...] = field(
        default_factory=lambda: tuple(
            p.strip()
            for p in os.environ.get("GATEWAY_TRUSTED_PROXIES", "").split(",")
            if p.strip()
        )
    )

    enable_https: bool = field(
        default_factory=lambda: os.environ.get("GATEWAY_ENABLE_HTTPS", "false").lower()
        in ("1", "true", "yes", "on")
    )

    # ------------------------------------------------------------------
    # Rate limiting
    # ------------------------------------------------------------------
    rate_limit_enabled: bool = field(
        default_factory=lambda: os.environ.get(
            "GATEWAY_RATE_LIMIT_ENABLED", "true"
        ).lower()
        in ("1", "true", "yes", "on")
    )
    rate_limit_requests_per_minute: int = field(
        default_factory=lambda: int(
            os.environ.get("GATEWAY_RATE_LIMIT_RPM", "60")
        )
    )
    rate_limit_requests_per_hour: int = field(
        default_factory=lambda: int(
            os.environ.get("GATEWAY_RATE_LIMIT_RPH", "600")
        )
    )

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------
    auth_enabled: bool = field(
        default_factory=lambda: os.environ.get(
            "GATEWAY_AUTH_ENABLED", "true"
        ).lower()
        in ("1", "true", "yes", "on")
    )
    # Comma-separated list of paths that bypass authentication.
    auth_public_paths: tuple[str, ...] = field(
        default_factory=lambda: tuple(
            p.strip()
            for p in os.environ.get(
                "GATEWAY_AUTH_PUBLIC_PATHS",
                "/api/v1/auth/login,/api/v1/auth/register,/api/v1/auth/refresh,/api/v1/auth/password-reset,/api/v1/health,/api/v1/health/live,/api/v1/health/ready,/api/v1/health/services",
            ).split(",")
            if p.strip()
        )
    )
    # Comma-separated list of path prefixes that bypass authentication.
    auth_public_prefixes: tuple[str, ...] = field(
        default_factory=lambda: tuple(
            p.strip()
            for p in os.environ.get(
                "GATEWAY_AUTH_PUBLIC_PREFIXES",
                "/api/v1/auth,/api/v1/health,/api/v1/system/observability,/docs,/openapi.json,/redoc",
            ).split(",")
            if p.strip()
        )
    )

    # ------------------------------------------------------------------
    # JWT
    # ------------------------------------------------------------------
    jwt_algorithm: str = field(
        default_factory=lambda: os.environ.get("GATEWAY_JWT_ALGORITHM", "RS256")
    )
    jwt_secret: str = field(
        default_factory=lambda: os.environ.get("GATEWAY_JWT_SECRET", "")
    )
    jwt_private_key: str = field(
        default_factory=lambda: os.environ.get("GATEWAY_JWT_PRIVATE_KEY", "")
    )
    jwt_public_key: str = field(
        default_factory=lambda: os.environ.get("GATEWAY_JWT_PUBLIC_KEY", "")
    )
    jwt_access_token_expire_minutes: int = field(
        default_factory=lambda: int(
            os.environ.get("GATEWAY_JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "15")
        )
    )

    # ------------------------------------------------------------------
    # Redis
    # ------------------------------------------------------------------
    redis_url: str = field(
        default_factory=lambda: os.environ.get(
            "GATEWAY_REDIS_URL", "redis://localhost:6379/0"
        )
    )

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------
    log_level: str = field(
        default_factory=lambda: os.environ.get("GATEWAY_LOG_LEVEL", "INFO").upper()
    )
    log_json: bool = field(
        default_factory=lambda: os.environ.get(
            "GATEWAY_LOG_JSON", "true"
        ).lower()
        in ("1", "true", "yes", "on")
    )

    cors_origins: tuple[str, ...] = field(
        default_factory=lambda: tuple(
            p.strip()
            for p in os.environ.get(
                "GATEWAY_CORS_ORIGINS",
                "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3005,http://127.0.0.1:3005",
            ).split(",")
            if p.strip()
        )
    )
    cors_allow_credentials: bool = field(
        default_factory=lambda: os.environ.get("GATEWAY_CORS_ALLOW_CREDENTIALS", "true").lower()
        in ("1", "true", "yes", "on")
    )
    cors_allow_methods: tuple[str, ...] = field(
        default_factory=lambda: tuple(
            p.strip().upper()
            for p in os.environ.get(
                "GATEWAY_CORS_ALLOW_METHODS",
                "GET,POST,PUT,PATCH,DELETE,OPTIONS",
            ).split(",")
            if p.strip()
        )
    )
    cors_allow_headers: tuple[str, ...] = field(
        default_factory=lambda: tuple(
            p.strip()
            for p in os.environ.get(
                "GATEWAY_CORS_ALLOW_HEADERS",
                "Authorization,Content-Type,X-Correlation-ID,X-Request-ID",
            ).split(",")
            if p.strip()
        )
    )

    # ------------------------------------------------------------------
    # Proxy behaviour
    # ------------------------------------------------------------------
    proxy_timeout: float = field(
        default_factory=lambda: float(
            os.environ.get("GATEWAY_PROXY_TIMEOUT", "30.0")
        )
    )
    proxy_max_connections: int = field(
        default_factory=lambda: int(
            os.environ.get("GATEWAY_PROXY_MAX_CONNECTIONS", "100")
        )
    )
    proxy_forward_headers: tuple[str, ...] = field(
        default_factory=lambda: tuple(
            h.strip()
            for h in os.environ.get(
                "GATEWAY_PROXY_FORWARD_HEADERS",
                "authorization,cookie,x-correlation-id,x-request-id,content-type,accept,accept-encoding,user-agent",
            ).split(",")
            if h.strip()
        )
    )

    # ------------------------------------------------------------------
    # Derived helpers
    # ------------------------------------------------------------------
    @property
    def api_prefix(self) -> str:
        """The path prefix the gateway is responsible for."""
        return self.proxy_prefix

    @property
    def is_public_path(self) -> set[str]:
        """Set of exact paths that bypass authentication."""
        return set(self.auth_public_paths)

    @property
    def is_public_prefix(self) -> list[str]:
        """List of path prefixes that bypass authentication."""
        return list(self.auth_public_prefixes)


# ---------------------------------------------------------------------------
# Singleton accessor (mirrors the pattern used by ``app.core.config``).
# ---------------------------------------------------------------------------
_gateway_config: Optional[GatewayConfig] = None


def get_gateway_config() -> GatewayConfig:
    """Return a process-wide singleton :class:`GatewayConfig` instance."""
    global _gateway_config
    if _gateway_config is None:
        _gateway_config = GatewayConfig()
    return _gateway_config


def reset_gateway_config() -> None:
    """Reset the cached configuration (useful for tests)."""
    global _gateway_config
    _gateway_config = None