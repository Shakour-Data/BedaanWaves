"""Tests for the password-reset service layer.

All database access is mocked — no real DB connection required.
"""
import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from uuid import uuid4

import pytest

from app.services.user.password_reset_service import (
    create_password_reset_token,
    verify_reset_token,
    consume_reset_token,
    reset_password,
    generate_raw_token,
    hash_token,
    verify_token_hash,
    RESET_TOKEN_TTL_MINUTES,
)


class FakeToken:
    """In-memory stand-in for PasswordResetToken rows in the mock DB."""

    def __init__(self, user_id, token_hash, expires_at, consumed=False, id=None):
        self.id = id or uuid4()
        self.user_id = user_id
        self.token_hash = token_hash
        self.expires_at = expires_at
        self.consumed = consumed
        self.consumed_at = None


class FakeUser:
    def __init__(self, email="user@example.com", user_id=None):
        self.id = user_id or uuid4()
        self.email = email
        self.hashed_password = "old_hash"


@pytest.fixture
def mock_session():
    """A MagicMock that behaves like an async SQLAlchemy session."""
    session = MagicMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def mock_async_session_maker(mock_session):
    """Patch async_session_maker to return our mock session."""
    with patch(
        "app.services.user.password_reset_service.async_session_maker",
        return_value=mock_session,
    ):
        yield mock_session


# ---------------------------------------------------------------------------
# 1. Token generation helpers
# ---------------------------------------------------------------------------
class TestTokenHelpers:
    def test_generate_raw_token_is_url_safe(self):
        token = generate_raw_token()
        assert len(token) >= 32
        assert "/" not in token  # url-safe

    def test_hash_token_returns_bcrypt_hash(self):
        raw = generate_raw_token()
        h = hash_token(raw)
        assert h != raw
        assert h.startswith("$2")  # bcrypt

    def test_verify_token_hash_accepts_correct(self):
        raw = generate_raw_token()
        h = hash_token(raw)
        assert verify_token_hash(h, raw) is True

    def test_verify_token_hash_rejects_wrong(self):
        raw = generate_raw_token()
        h = hash_token(raw)
        assert verify_token_hash(h, generate_raw_token()) is False


# ---------------------------------------------------------------------------
# 2. create_password_reset_token
# ---------------------------------------------------------------------------
class TestCreatePasswordResetToken:
    @pytest.mark.asyncio
    async def test_returns_token_for_existing_user(self, mock_session, mock_async_session_maker):
        user = FakeUser()
        mock_session.execute = AsyncMock(return_value=MagicMock(scalars=lambda: MagicMock(all=lambda: [])))

        with patch(
            "app.services.user.password_reset_service.get_user_by_email",
            new_callable=AsyncMock,
            return_value=user,
        ), patch(
            "app.services.user.password_reset_service.hash_token",
            side_effect=lambda t: f"hash_{t}",
        ):
            raw = await create_password_reset_token("user@example.com")

        assert raw is not None
        assert isinstance(raw, str)
        mock_session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_none_for_unknown_user(self, mock_session, mock_async_session_maker):
        mock_session.execute = AsyncMock(return_value=MagicMock(scalars=lambda: MagicMock(all=lambda: [])))
        with patch(
            "app.services.user.password_reset_service.get_user_by_email",
            new_callable=AsyncMock,
            return_value=None,
        ):
            raw = await create_password_reset_token("nobody@example.com")

        assert raw is None
        mock_session.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_invalidates_previous_tokens(self, mock_session, mock_async_session_maker):
        user = FakeUser()
        old_token = FakeToken(
            user_id=user.id,
            token_hash="old_hash",
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
            consumed=False,
        )

        mock_session.execute = AsyncMock(
            side_effect=[
                MagicMock(scalars=lambda: MagicMock(all=lambda: [old_token])),  # invalidate old
                MagicMock(scalars=lambda: _NoRows()),  # refresh select
            ]
        )

        with patch(
            "app.services.user.password_reset_service.get_user_by_email",
            new_callable=AsyncMock,
            return_value=user,
        ), patch(
            "app.services.user.password_reset_service.hash_token",
            side_effect=lambda t: f"hash_{t}",
        ):
            raw = await create_password_reset_token("user@example.com")

        assert raw is not None
        assert old_token.consumed is True


class _NoRows:
    def scalars(self):
        return self
    def all(self):
        return []
    def first(self):
        return None


# ---------------------------------------------------------------------------
# 3. verify_reset_token
# ---------------------------------------------------------------------------
class TestVerifyResetToken:
    @pytest.mark.asyncio
    async def test_returns_true_for_valid_token(self, mock_session, mock_async_session_maker):
        user = FakeUser()
        raw = generate_raw_token()
        stored_hash = hash_token(raw)
        valid_token = FakeToken(
            user_id=user.id,
            token_hash=stored_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
        )
        mock_session.execute = AsyncMock(
            return_value=MagicMock(scalars=lambda: MagicMock(all=lambda: [valid_token]))
        )

        result = await verify_reset_token(raw)
        assert result is True

    @pytest.mark.asyncio
    async def test_returns_false_for_consumed_token(self, mock_session, mock_async_session_maker):
        raw = generate_raw_token()
        consumed = FakeToken(
            user_id=uuid4(),
            token_hash=hash_token(raw),
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
            consumed=True,
        )
        # The query already filters consumed=False, so consumed tokens won't appear
        mock_session.execute = AsyncMock(
            return_value=MagicMock(scalars=lambda: MagicMock(all=lambda: []))
        )

        result = await verify_reset_token(raw)
        assert result is False

    @pytest.mark.asyncio
    async def test_returns_false_for_expired_token(self, mock_session, mock_async_session_maker):
        raw = generate_raw_token()
        # Query filters expires_at > now, so expired tokens won't appear
        mock_session.execute = AsyncMock(
            return_value=MagicMock(scalars=lambda: MagicMock(all=lambda: []))
        )

        result = await verify_reset_token(raw)
        assert result is False


# ---------------------------------------------------------------------------
# 4. consume_reset_token
# ---------------------------------------------------------------------------
class TestConsumeResetToken:
    @pytest.mark.asyncio
    async def test_consumes_and_returns_user(self, mock_session, mock_async_session_maker):
        user = FakeUser()
        raw = generate_raw_token()
        token = FakeToken(
            user_id=user.id,
            token_hash=hash_token(raw),
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
        )
        mock_session.execute = AsyncMock(
            side_effect=[
                MagicMock(scalars=lambda: MagicMock(all=lambda: [token])),  # lookup token
                MagicMock(scalars=lambda: MagicMock(first=lambda: user)),  # lookup user
            ]
        )

        with patch(
            "app.services.user.password_reset_service.get_user_by_email",
            new_callable=AsyncMock,
        ):
            consumed_user = await consume_reset_token(raw)

        assert consumed_user is not None
        assert consumed_user.id == user.id
        assert token.consumed is True
        assert token.consumed_at is not None

    @pytest.mark.asyncio
    async def test_returns_none_for_invalid_token(self, mock_session, mock_async_session_maker):
        mock_session.execute = AsyncMock(
            return_value=MagicMock(scalars=lambda: MagicMock(all=lambda: []))
        )

        result = await consume_reset_token("invalid-token")
        assert result is None


# ---------------------------------------------------------------------------
# 5. reset_password
# ---------------------------------------------------------------------------
class TestResetPassword:
    @pytest.mark.asyncio
    async def test_returns_true_on_valid_token(self, mock_session, mock_async_session_maker):
        user = FakeUser()
        raw = generate_raw_token()
        token = FakeToken(
            user_id=user.id,
            token_hash=hash_token(raw),
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
        )
        mock_session.execute = AsyncMock(
            side_effect=[
                MagicMock(scalars=lambda: MagicMock(all=lambda: [token])),  # lookup
                MagicMock(scalars=lambda: MagicMock(first=lambda: user)),  # user lookup
            ]
        )

        with patch(
            "app.services.user.password_reset_service.hash_password",
            return_value="new_hashed",
        ):
            result = await reset_password(raw, "newpassword123")

        assert result is True
        assert user.hashed_password == "new_hashed"
        mock_session.commit.assert_called()

    @pytest.mark.asyncio
    async def test_returns_false_for_invalid_token(self, mock_session, mock_async_session_maker):
        mock_session.execute = AsyncMock(
            return_value=MagicMock(scalars=lambda: MagicMock(all=lambda: []))
        )

        result = await reset_password("bad-token", "newpassword123")
        assert result is False
        mock_session.commit.assert_not_called()
