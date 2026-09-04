"""Password Reset Service (Tier 6: User Services)

Handles generation, verification, and consumption of single-use password
reset tokens.  Tokens are stored hashed and expire automatically.

Traceability: powers the Processing / Result / Error_Recovery states of the
password-recovery finite state machine defined in spec.yaml.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID
from secrets import token_urlsafe

from sqlalchemy import select

from app.core.config import get_settings
from app.db.base import async_session_maker
from app.models.models import User, PasswordResetToken
from app.services.user.auth_service import hash_password, verify_password, get_user_by_email

settings = get_settings()

# Tokens expire after 1 hour (operational Definition for the FSM's timeout edge)
RESET_TOKEN_TTL_MINUTES: int = 60


def generate_raw_token() -> str:
    """Generate a cryptographically random, URL-safe token string."""
    return token_urlsafe(32)


def hash_token(token: str) -> str:
    """Hash a raw token for secure storage (bcrypt)."""
    return hash_password(token)


def verify_token_hash(stored_hash: str, raw_token: str) -> bool:
    """Verify a raw token against a stored hash."""
    return verify_password(raw_token, stored_hash)


async def create_password_reset_token(email: str, session=None) -> Optional[str]:
    """Create a single-use reset token for the user identified by *email*.

    Returns the **raw** token string (to be sent via email link) or
    ``None`` when no account exists.  Account existence is deliberately
    hidden from the caller — see the API layer for the generic message
    (error philosophy: "Never blame user; always suggest next action").
    """
    owns = session is None
    if owns:
        session = async_session_maker()
    try:
        user = await get_user_by_email(email)
        if user is None:
            return None

        raw_token = generate_raw_token()
        now = datetime.now(timezone.utc)

        # Invalidate previous non-consumed tokens for this user (single valid token)
        result = await session.execute(
            select(PasswordResetToken).where(
                PasswordResetToken.user_id == user.id,
                PasswordResetToken.consumed.is_(False),
                PasswordResetToken.expires_at > now,
            )
        )
        for old in result.scalars().all():
            old.consumed = True
            old.consumed_at = now

        token = PasswordResetToken(
            user_id=user.id,
            token_hash=hash_token(raw_token),
            expires_at=now + timedelta(minutes=RESET_TOKEN_TTL_MINUTES),
            consumed=False,
        )
        session.add(token)
        await session.commit()
        await session.refresh(token)
        return raw_token
    finally:
        if owns:
            await session.close()


async def get_valid_reset_token(raw_token: str, session=None) -> Optional[PasswordResetToken]:
    """Look up a token by its raw value.

    Returns the token row only when it is not consumed and not expired.
    Iterates and verifies each hash (constant-time bcrypt compare).
    """
    owns = session is None
    if owns:
        session = async_session_maker()
    try:
        now = datetime.now(timezone.utc)
        result = await session.execute(
            select(PasswordResetToken).where(
                PasswordResetToken.consumed.is_(False),
                PasswordResetToken.expires_at > now,
            )
        )
        for row in result.scalars().all():
            if verify_token_hash(row.token_hash, raw_token):
                return row
        return None
    finally:
        if owns:
            await session.close()


async def verify_reset_token(raw_token: str, session=None) -> bool:
    """Return ``True`` when *raw_token* is valid (not consumed, not expired)."""
    owns = session is None
    if owns:
        session = async_session_maker()
    try:
        token = await get_valid_reset_token(raw_token, session=session)
        return token is not None
    finally:
        if owns:
            await session.close()


async def consume_reset_token(raw_token: str, session=None) -> Optional[User]:
    """Consume a valid token and return the associated user.

    Returns ``None`` when the token is invalid, consumed, or expired.
    """
    owns = session is None
    if owns:
        session = async_session_maker()
    try:
        token = await get_valid_reset_token(raw_token, session=session)
        if token is None:
            return None
        token.consumed = True
        token.consumed_at = datetime.now(timezone.utc)
        await session.commit()

        result = await session.execute(select(User).where(User.id == token.user_id))
        return result.scalars().first()
    finally:
        if owns:
            await session.close()


async def reset_password(raw_token: str, new_password: str, session=None) -> bool:
    """Reset a user's password using a valid, non-consumed token.

    Returns ``True`` on success, ``False`` if the token is invalid/expired.
    The token is consumed in the same transaction so it cannot be reused.
    """
    owns = session is None
    if owns:
        session = async_session_maker()
    try:
        user = await consume_reset_token(raw_token, session=session)
        if user is None:
            return False
        user.hashed_password = hash_password(new_password)
        await session.commit()
        return True
    finally:
        if owns:
            await session.close()
