"""API Gateway entry point.

A standalone FastAPI application that fronts the BedaanWaves backend. It
performs centralised rate limiting, JWT validation, correlation-ID
propagation, structured logging and security-header injection, then
proxies all ``/api/v1/*`` traffic to the configured backend service.
"""

from __future__ import annotations

import logging
import os
import uuid
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from starlette.responses import StreamingResponse

from .config import GatewayConfig, get_gateway_config
from .middleware import (
    GatewayAuthMiddleware,
    GatewayLoggingMiddleware,
    GatewayRateLimitMiddleware,
)
from .proxy import ProxyClient, ProxyConnectionError, ProxyError, ProxyTimeoutError

logger = logging.getLogger(__name__)


def _configure_logging(config: GatewayConfig) -> None:
    level = getattr(logging, config.log_level.upper(), logging.INFO)
    logging.basicConfig(level=level)


def _build_upstream_headers(request: Request, correlation_id: str) -> dict[str, str]:
    """Forward a safe allow-list of headers to the backend."""
    forward = {
        "authorization",
        "cookie",
        "x-correlation-id",
        "x-request-id",
        "x-user-id",
        "x-username",
        "content-type",
        "accept",
        "accept-encoding",
        "user-agent",
    }
    upstream: dict[str, str] = {}
    for name, value in request.headers.items():
        if name.lower() in forward:
            upstream[name] = value
    upstream["X-Correlation-ID"] = correlation_id
    upstream["X-Gateway"] = "bedaanwaves-gateway"
    return upstream


@asynccontextmanager
async def gateway_lifespan(app: FastAPI):
    """Manage the gateway's proxy client lifecycle."""
    config = get_gateway_config()
    logger.info(
        "Starting BedaanWaves API Gateway (backend=%s, port=%s)",
        config.backend_url,
        config.port,
    )
    app.state.proxy_client = ProxyClient(config)
    try:
        yield
    finally:
        client: Optional[ProxyClient] = getattr(app.state, "proxy_client", None)
        if client is not None:
            await client.close()
        logger.info("BedaanWaves API Gateway stopped")


def create_gateway_app(config: Optional[GatewayConfig] = None) -> FastAPI:
    """Build and configure the gateway FastAPI application."""
    if config is None:
        config = get_gateway_config()
    _configure_logging(config)

    app = FastAPI(
        title="BedaanWaves API Gateway",
        description="Centralised API Gateway for the BedaanWaves backend",
        version="1.0.0",
        docs_url="/docs" if os.environ.get("GATEWAY_ENABLE_DOCS", "true").lower() in ("1", "true", "yes") else None,
        redoc_url="/redoc" if os.environ.get("GATEWAY_ENABLE_DOCS", "true").lower() in ("1", "true", "yes") else None,
        openapi_url="/openapi.json" if os.environ.get("GATEWAY_ENABLE_DOCS", "true").lower() in ("1", "true", "yes") else None,
        lifespan=gateway_lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(GatewayLoggingMiddleware, enabled=True)
    app.add_middleware(GatewayAuthMiddleware, enabled=config.auth_enabled)
    app.add_middleware(GatewayRateLimitMiddleware, enabled=config.rate_limit_enabled)

    # ------------------------------------------------------------------
    # Health endpoints
    # ------------------------------------------------------------------
    @app.get("/health", tags=["gateway"])
    async def gateway_health() -> dict:
        return {
            "status": "healthy",
            "service": "bedaanwaves-api-gateway",
            "version": "1.0.0",
            "backend_url": config.backend_url,
        }

    @app.get("/health/live", tags=["gateway"])
    async def gateway_live() -> dict:
        return {"status": "alive", "service": "bedaanwaves-api-gateway"}

    @app.get("/health/ready", tags=["gateway"])
    async def gateway_ready() -> dict:
        client: Optional[ProxyClient] = getattr(app.state, "proxy_client", None)
        backend_ok = False
        if client is not None:
            try:
                backend_ok = await client.health_check()
            except Exception:
                backend_ok = False
        return {
            "status": "ready" if backend_ok else "not_ready",
            "backend_reachable": backend_ok,
        }

    # ------------------------------------------------------------------
    # Proxy route — everything under the configured prefix
    # ------------------------------------------------------------------
    @app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"], tags=["proxy"])
    async def proxy(full_path: str, request: Request) -> Response:
        client: ProxyClient = getattr(app.state, "proxy_client", None)
        if client is None:
            return JSONResponse(
                status_code=503,
                content={"status": "error", "error_code": "GATEWAY_UNAVAILABLE", "message": "Gateway proxy not initialised"},
            )

        correlation_id = getattr(request.state, "correlation_id", None) or uuid.uuid4().hex
        request.state.correlation_id = correlation_id

        target_path = request.url.path
        prefix = config.proxy_prefix
        if prefix and target_path.startswith(prefix):
            target_path = target_path[len(prefix):] or "/"

        body: Optional[bytes] = None
        if request.method in ("POST", "PUT", "PATCH"):
            try:
                body = await request.body()
            except Exception:
                body = None

        upstream_headers = _build_upstream_headers(request, correlation_id)

        try:
            upstream = await client.proxy(
                method=request.method,
                path=target_path,
                request_headers=upstream_headers,
                correlation_id=correlation_id,
                body=body,
            )
        except ProxyTimeoutError:
            return JSONResponse(
                status_code=504,
                content={"status": "error", "error_code": "GATEWAY_TIMEOUT", "message": "Backend request timed out"},
            )
        except ProxyConnectionError:
            return JSONResponse(
                status_code=502,
                content={"status": "error", "error_code": "BAD_GATEWAY", "message": "Backend unreachable"},
            )
        except ProxyError:
            return JSONResponse(
                status_code=502,
                content={"status": "error", "error_code": "BAD_GATEWAY", "message": "Backend request failed"},
            )

        excluded = {"content-encoding", "content-length", "transfer-encoding", "connection"}
        response_headers = {
            k: v for k, v in upstream.headers.items() if k.lower() not in excluded
        }
        response_headers["X-Correlation-ID"] = correlation_id
        response_headers["X-Gateway"] = "bedaanwaves-gateway"

        return StreamingResponse(
            upstream.aiter_raw(),
            status_code=upstream.status_code,
            headers=response_headers,
        )

    return app


# Module-level app instance for direct uvicorn usage.
app = create_gateway_app()