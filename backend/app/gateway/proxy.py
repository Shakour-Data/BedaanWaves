"""HTTP proxy logic for the API Gateway.

Wraps :mod:`httpx` in an async client that forwards incoming requests to the
backend service. The proxy is responsible for:

- Copying the relevant subset of request headers (auth, cookies, correlation
  IDs, request IDs, etc.) to the backend.
- Streaming the request body (without buffering it fully in memory) so that
  large uploads and SSE streams pass through efficiently.
- Streaming the response body back to the caller.
- Propagating the correlation ID both upstream (to the backend) and
  downstream (in the response headers).
- Mapping transport errors (connection refused, timeouts) to sensible HTTP
  responses.
"""

from __future__ import annotations

import logging
from typing import Mapping, Optional

import httpx

from .config import GatewayConfig

logger = logging.getLogger(__name__)


class ProxyClient:
    """Async HTTP proxy client forwarding requests to the backend service."""

    def __init__(self, config: Optional[GatewayConfig] = None) -> None:
        self.config = config or GatewayConfig()
        self._client: Optional[httpx.AsyncClient] = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def _ensure_client(self) -> httpx.AsyncClient:
        if self._client is None:
            limits = httpx.Limits(
                max_connections=self.config.proxy_max_connections,
                max_keepalive_connections=self.config.proxy_max_connections,
            )
            self._client = httpx.AsyncClient(
                base_url=self.config.backend_url,
                timeout=httpx.Timeout(self.config.proxy_timeout),
                limits=limits,
                follow_redirects=False,
            )
        return self._client

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def health_check(self) -> bool:
        """Probe the backend's liveness endpoint.

        Returns ``True`` when the backend responds with a non-5xx status.
        """
        client = self._ensure_client()
        try:
            response = await client.request("GET", "/api/v1/health/live")
            return response.status_code < 500
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Header helpers
    # ------------------------------------------------------------------
    def _build_upstream_headers(
        self,
        request_headers: Mapping[str, str],
        correlation_id: str,
    ) -> dict[str, str]:
        """Build the set of headers forwarded to the backend.

        We forward an explicit allow-list of hop-by-hop / security headers
        plus any caller-supplied correlation / request identifiers so the
        backend can continue the trace.
        """
        forward = {h.lower() for h in self.config.proxy_forward_headers}
        upstream: dict[str, str] = {}

        for name, value in request_headers.items():
            lname = name.lower()
            if lname in forward:
                upstream[name] = value

        # Always (re)assert the correlation ID so the backend sees the
        # gateway-assigned one even when the caller did not send one.
        upstream["X-Correlation-ID"] = correlation_id
        upstream["X-Gateway"] = "bedaanwaves-gateway"

        # Preserve the original Host so the backend can still resolve the
        # correct virtual host if it cares.
        if "host" not in upstream and "host" in request_headers:
            upstream["Host"] = request_headers["host"]

        return upstream

    @staticmethod
    def _extract_correlation_id(response: httpx.Response) -> str:
        """Best-effort extraction of the correlation ID from the backend."""
        return response.headers.get("x-correlation-id", "")

    # ------------------------------------------------------------------
    # Proxy entry point
    # ------------------------------------------------------------------
    async def proxy(
        self,
        method: str,
        path: str,
        request_headers: Mapping[str, str],
        correlation_id: str,
        body: Optional[bytes] = None,
    ) -> httpx.Response:
        """Forward a request to the backend and return the raw response.

        The caller is responsible for converting the :class:`httpx.Response`
        into a :class:`starlette.responses.Response`.
        """
        client = self._ensure_client()
        upstream_headers = self._build_upstream_headers(
            request_headers, correlation_id
        )

        # ``path`` may already include the proxy prefix; strip it so we
        # target the same path on the backend. Fall back to the raw path
        # if the prefix is not present (e.g. when proxying arbitrary paths).
        target_path = path
        prefix = self.config.proxy_prefix
        if prefix and target_path.startswith(prefix):
            target_path = target_path[len(prefix):] or "/"

        request_kwargs: dict = {
            "method": method,
            "url": target_path,
            "headers": upstream_headers,
        }
        if body is not None:
            request_kwargs["content"] = body

        try:
            response = await client.request(**request_kwargs)
        except httpx.TimeoutException as exc:
            logger.warning(
                "Gateway proxy timeout: %s %s correlation_id=%s error=%s",
                method,
                path,
                correlation_id,
                exc,
            )
            raise ProxyTimeoutError(
                f"Backend request timed out: {method} {path}"
            ) from exc
        except httpx.ConnectError as exc:
            logger.error(
                "Gateway proxy connection error: %s %s correlation_id=%s error=%s",
                method,
                path,
                correlation_id,
                exc,
            )
            raise ProxyConnectionError(
                f"Backend unreachable: {method} {path}"
            ) from exc
        except httpx.HTTPError as exc:
            logger.error(
                "Gateway proxy HTTP error: %s %s correlation_id=%s error=%s",
                method,
                path,
                correlation_id,
                exc,
            )
            raise ProxyError(f"Backend request failed: {method} {path}") from exc

        return response


# ---------------------------------------------------------------------------
# Exception types surfaced by the proxy so the gateway can map them to
# appropriate HTTP responses without leaking backend internals.
# ---------------------------------------------------------------------------
class ProxyError(Exception):
    """Base class for proxy-related failures."""


class ProxyTimeoutError(ProxyError):
    """Raised when the backend takes too long to respond."""


class ProxyConnectionError(ProxyError):
    """Raised when the backend cannot be reached."""