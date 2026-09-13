"""CSRF Protection - Token generation, validation, and middleware.

Provides CSRF protection for state-changing HTTP requests using
cryptographically secure tokens stored in Redis.
"""

from __future__ import annotations

import logging
import secrets
from typing import Optional

import redis.asyncio as aioredis
from fastapi import HTTPException, Request, status

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class CSRFProtection:
    """
    CSRF token generation and validation service.

    Tokens are stored in Redis with a configurable TTL.  Each token is
    single-use: it is deleted after successful validation.
    """

    def __init__(self, redis_url: str | None = None) -> None:
        self.redis_url = redis_url or settings.REDIS_URL
        self._client: aioredis.Redis | None = None
        self.token_ttl: int = getattr(settings, "CSRF_TOKEN_TTL_SECONDS", 3600)

    async def _get_client(self) -> aioredis.Redis:
        if self._client is None:
            try:
                self._client = aioredis.from_url(
                    self.redis_url, socket_connect_timeout=5
                )
                await self._client.ping()
            except Exception as exc:
                logger.error("CSRF Redis connection failed: %s", exc)
                raise RuntimeError(
                    f"CSRF Redis connection failed: {exc}"
                ) from exc
        return self._client

    def generate_token(self) -> str:
        """Generate a new cryptographically secure CSRF token."""
        return secrets.token_urlsafe(32)

    async def store_token(self, user_id: str, token: str) -> None:
        """Store a CSRF token for a user with the configured TTL."""
        client = await self._get_client()
        key = f"csrf:{user_id}:{token}"
        await client.set(key, "1", ex=self.token_ttl)
        logger.debug("Stored CSRF token for user %s", user_id)

    async def validate_token(self, user_id: str, token: str) -> bool:
        """Validate a CSRF token for a user and remove it (single-use).

        Args:
            user_id: The authenticated user's id.
            token: The token presented by the client.

        Returns:
            ``True`` if the token is valid and was consumed.
        """
        if not token:
            return False
        client = await self._get_client()
        key = f"csrf:{user_id}:{token}"
        exists = await client.exists(key)
        if exists:
            await client.delete(key)
            logger.debug("Consumed CSRF token for user %s", user_id)
            return True
        logger.warning("Invalid CSRF token for user %s", user_id)
        return False

    async def close(self) -> None:
        """Close the Redis connection."""
        if self._client:
            await self._client.close()
            self._client = None


_csrf_service: Optional[CSRFProtection] = None


def get_csrf_protection() -> CSRFProtection:
    """Return the singleton CSRFProtection instance."""
    global _csrf_service
    if _csrf_service is None:
        _csrf_service = CSRFProtection()
    return _csrf_service


async def csrf_protect(request: Request) -> None:
    """
    FastAPI dependency for explicit CSRF protection on a route.

    Reads ``X-CSRF-Token`` from the request headers, validates it against
    the stored token for the authenticated user, and marks the request as
    validated so the CSRF middleware skips it.

    Raises:
        HTTPException: 403 if the token is missing or invalid.
    """
    csrf = get_csrf_protection()
    token = request.headers.get("X-CSRF-Token", "")

    user_id = getattr(request.state, "user_id", None)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token validation failed: no authenticated user",
        )

    valid = await csrf.validate_token(str(user_id), token)
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token missing or invalid",
        )

    request.state.csrf_validated = True
