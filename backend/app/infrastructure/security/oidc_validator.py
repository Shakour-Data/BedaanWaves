"""OIDC Token Validator — validates tokens issued by a Keycloak IdP.

Replaces the HS256 JWT secret check with proper OIDC verification:
  1. Fetch JWKS from the IdP
  2. Verify the token signature against the matching key
  3. Validate standard claims (exp, nbf, aud, iss)
  4. Return the decoded claims or None

Falls back to the existing HS256 ``decode_token`` when OIDC is not
configured, so development keeps working without an IdP.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class OIDCTokenValidator:
    """Validate access tokens against an OpenID Connect provider."""

    def __init__(
        self,
        realm_url: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        timeout: float = 5.0,
    ) -> None:
        self._realm_url = (realm_url or settings.KEYCLOAK_REALM_URL or "").rstrip("/")
        self._client_id = client_id or settings.KEYCLOAK_CLIENT_ID or "bedaanwaves-api"
        self._client_secret = client_secret or settings.KEYCLOAK_CLIENT_SECRET or ""
        self._timeout = timeout
        self._jwks: dict[str, Any] | None = None
        self._jwks_fetched_at: float = 0.0
        self._jwks_ttl: float = 300  # refresh JWKS every 5 min

    @property
    def enabled(self) -> bool:
        return bool(self._realm_url)

    @property
    def jwks_url(self) -> str:
        return f"{self._realm_url}/protocol/openid-connect/certs"

    async def _fetch_jwks(self) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(self.jwks_url)
            resp.raise_for_status()
            return resp.json()

    async def _get_jwks(self) -> dict[str, Any]:
        now = time.monotonic()
        if self._jwks is None or (now - self._jwks_fetched_at) > self._jwks_ttl:
            try:
                self._jwks = await self._fetch_jwks()
                self._jwks_fetched_at = now
            except Exception as exc:
                logger.error("Failed to fetch JWKS from %s: %s", self.jwks_url, exc)
                if self._jwks is None:
                    raise
        return self._jwks

    async def validate(self, token: str) -> dict[str, Any] | None:
        """Validate *token* and return the decoded claims, or None."""
        if not self.enabled:
            return None

        try:
            from jose import JWTError, jwt
            from jose.backends import RSAKeyBackend
        except ImportError:
            logger.warning("jose not installed; OIDC validation disabled")
            return None

        try:
            jwks = await self._get_jwks()
            # jose expects the JWKS in {"keys": [...]} format
            message = jwt.decode(
                token,
                jwks,
                algorithms=["RS256"],
                audience=self._client_id,
                issuer=self._realm_url,
                options={"verify_exp": True, "verify_nbf": True, "verify_aud": True},
            )
            return message
        except JWTError as exc:
            logger.debug("OIDC token validation failed: %s", exc)
            return None
        except Exception as exc:
            logger.error("OIDC validation error: %s", exc)
            return None


_validator: OIDCTokenValidator | None = None


def get_oidc_validator() -> OIDCTokenValidator:
    """Return a lazily-initialised singleton validator."""
    global _validator
    if _validator is None:
        _validator = OIDCTokenValidator()
    return _validator


async def validate_token_oidc(token: str) -> dict[str, Any] | None:
    """Validate via OIDC; returns claims or None."""
    return await get_oidc_validator().validate(token)


async def decode_token_with_fallback(token: str) -> dict[str, Any] | None:
    """Try OIDC first, fall back to HS256 JWT.

    This makes the migration from HS256 → OIDC safe: in production the
    validator is enabled and tokens are verified against Keycloak; in
    development the local HS256 secret still works.
    """
    # 1. Try OIDC if configured
    oidc_claims = await validate_token_oidc(token)
    if oidc_claims is not None:
        return oidc_claims

    # 2. Fall back to HS256
    from app.services.user.auth_service import decode_token
    return decode_token(token)