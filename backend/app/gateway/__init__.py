"""API Gateway package.

Provides a lightweight, FastAPI-based API Gateway that sits in front of the
BedaanWaves backend service. The gateway is responsible for:

- Centralized rate limiting (Redis-backed, distributed)
- Centralized JWT authentication / validation (RS256)
- Request routing / proxying to the backend service
- Structured request logging with correlation ID propagation
- Security header injection
- A self health-check endpoint

The gateway runs on a separate port (default 8000) and forwards all
``/api/v1/*`` traffic to the configured backend URL (default
``http://localhost:3000``).
"""

from .config import GatewayConfig, get_gateway_config
from .main import create_gateway_app, gateway_lifespan
from .proxy import ProxyClient
from .middleware import (
    GatewayAuthMiddleware,
    GatewayLoggingMiddleware,
    GatewayRateLimitMiddleware,
    GatewaySecurityHeadersMiddleware,
)

__all__ = [
    "GatewayConfig",
    "GatewayAuthMiddleware",
    "GatewayLoggingMiddleware",
    "GatewayRateLimitMiddleware",
    "GatewaySecurityHeadersMiddleware",
    "ProxyClient",
    "create_gateway_app",
    "gateway_lifespan",
    "get_gateway_config",
]