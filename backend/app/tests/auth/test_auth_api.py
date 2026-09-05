"""Unit tests for the auth API layer (register / login / refresh).

Tests both English (lang=en) and Persian (lang=fa) error messages, since the
lang parameter is validated with the pattern ``^(en|fa)$`` in auth.py.
All service-layer functions are mocked — no database or real JWT required.
"""
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.auth import router


@pytest.fixture
def app():
    _app = FastAPI()
    _app.include_router(router, prefix="/api/v1/auth", tags=["auth"])
    return _app


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def mock_user():
    """A simple stand-in user object returned by auth service mocks."""
    user = MagicMock()
    user.username = "testuser"
    user.email = "test@example.com"
    user.id = "123e4567-e89b-12d6-0000-000000000000"
    user.hashed_password = "hashed"
    return user


class TestRegister:
    @pytest.fixture
    def mock_service(self):
        with patch(
            "app.api.routes.auth.get_user_by_username",
            new_callable=AsyncMock,
            return_value=None,
        ) as mock_username, \
        patch(
            "app.api.routes.auth.get_user_by_email",
            new_callable=AsyncMock,
            return_value=None,
        ) as mock_email, \
        patch(
            "app.api.routes.auth.create_user",
            new_callable=AsyncMock,
        ) as mock_create, \
        patch(
            "app.api.routes.auth.hash_password",
            return_value="hashed_pass",
        ) as mock_hash, \
        patch(
            "app.api.routes.auth.create_access_token",
            return_value="access.jwt.token",
        ) as mock_access, \
        patch(
            "app.api.routes.auth.create_refresh_token",
            return_value="refresh.jwt.token",
        ) as mock_refresh:
            yield {
                "username": mock_username,
                "email": mock_email,
                "create": mock_create,
                "hash": mock_hash,
                "access": mock_access,
                "refresh": mock_refresh,
            }

    def test_success(self, client, mock_service, mock_user):
        mock_service["create"].return_value = mock_user
        resp = client.post(
            "/api/v1/auth/register",
            json={
                "username": "newuser",
                "email": "new@example.com",
                "password": "securepass123",
                "full_name": "New User",
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["access_token"] == "access.jwt.token"
        assert body["refresh_token"] == "refresh.jwt.token"
        assert body["token_type"] == "bearer"

    def test_register_rejects_duplicate_username_en(self, client, mock_service):
        mock_service["username"].return_value = mock_user
        resp = client.post(
            "/api/v1/auth/register?lang=en",
            json={
                "username": "existing",
                "email": "new@example.com",
                "password": "securepass123",
                "full_name": "New User",
            },
        )
        assert resp.status_code == 400
        assert "already registered" in resp.json()["detail"]

    def test_register_rejects_duplicate_username_fa(self, client, mock_service):
        """Persian: 'نام کاربری قبلاً ثبت شده است'"""
        mock_service["username"].return_value = mock_user
        resp = client.post(
            "/api/v1/auth/register?lang=fa",
            json={
                "username": "existing",
                "email": "new@example.com",
                "password": "securepass123",
                "full_name": "کاربر جدید",
            },
        )
        assert resp.status_code == 400
        assert "نام کاربری" in resp.json()["detail"]

    def test_register_rejects_duplicate_email_en(self, client, mock_service):
        mock_service["email"].return_value = mock_user
        resp = client.post(
            "/api/v1/auth/register?lang=en",
            json={
                "username": "newuser",
                "email": "existing@example.com",
                "password": "securepass123",
            },
        )
        assert resp.status_code == 400
        assert "Email already registered" in resp.json()["detail"]

    def test_register_rejects_duplicate_email_fa(self, client, mock_service):
        """Persian: 'ایمیل قبلاً ثبت شده است'"""
        mock_service["email"].return_value = mock_user
        resp = client.post(
            "/api/v1/auth/register?lang=fa",
            json={
                "username": "newuser",
                "email": "existing@example.com",
                "password": "securepass123",
            },
        )
        assert resp.status_code == 400
        assert "ایمیل" in resp.json()["detail"]

    def test_register_rejects_short_username(self, client, mock_service):
        resp = client.post(
            "/api/v1/auth/register",
            json={
                "username": "ab",
                "email": "new@example.com",
                "password": "securepass123",
            },
        )
        assert resp.status_code == 422

    def test_register_rejects_invalid_lang(self, client, mock_service):
        resp = client.post(
            "/api/v1/auth/register?lang=de",
            json={
                "username": "newuser",
                "email": "new@example.com",
                "password": "securepass123",
            },
        )
        assert resp.status_code == 422


class TestLogin:
    @pytest.fixture
    def mock_service(self):
        with patch(
            "app.api.routes.auth.authenticate_user",
            new_callable=AsyncMock,
        ) as mock_auth, \
        patch(
            "app.api.routes.auth.create_access_token",
            return_value="access.jwt.token",
        ) as mock_access, \
        patch(
            "app.api.routes.auth.create_refresh_token",
            return_value="refresh.jwt.token",
        ) as mock_refresh:
            yield {
                "auth": mock_auth,
                "access": mock_access,
                "refresh": mock_refresh,
            }

    def test_login_success(self, client, mock_service, mock_user):
        mock_service["auth"].return_value = mock_user
        resp = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "correctpass"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["access_token"] == "access.jwt.token"
        assert body["refresh_token"] == "refresh.jwt.token"

    def test_login_invalid_credentials_en(self, client, mock_service):
        mock_service["auth"].return_value = None
        resp = client.post(
            "/api/v1/auth/login?lang=en",
            json={"username": "testuser", "password": "wrong"},
        )
        assert resp.status_code == 401
        assert "Incorrect username or password" in resp.json()["detail"]

    def test_login_invalid_credentials_fa(self, client, mock_service):
        """Persian: 'نام کاربری یا رمز عبور اشتباه است'"""
        mock_service["auth"].return_value = None
        resp = client.post(
            "/api/v1/auth/login?lang=fa",
            json={"username": "testuser", "password": "wrong"},
        )
        assert resp.status_code == 401
        assert "رمز عبور" in resp.json()["detail"]

    def test_login_missing_password(self, client, mock_service):
        resp = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser"},
        )
        assert resp.status_code == 422


class TestRefreshToken:
    """The refresh_token endpoint takes ``token`` as a query parameter
    (bare ``str`` in the signature, not annotated with ``Body``)."""

    def _mock_async_session(self, stored_token):
        """Build a MagicMock async context manager that yields a session
        whose ``execute().scalars().first()`` returns ``stored_token``."""
        session = MagicMock()
        session.execute = AsyncMock()
        session.commit = AsyncMock()

        async def mock_execute(*args, **kwargs):
            result = MagicMock()
            result.scalars.return_value.first.return_value = stored_token
            return result

        session.execute = AsyncMock(side_effect=mock_execute)

        async def aenter():
            return session

        async def aexit(*args):
            return None

        cm = MagicMock()
        cm.__aenter__.side_effect = aenter
        cm.__aexit__.side_effect = aexit
        return cm

    def test_refresh_success(self, client, mock_user):
        """A valid refresh token should return new access + refresh tokens."""
        stored_token = MagicMock()
        stored_token.id = "token-uuid"
        mock_sm = self._mock_async_session(stored_token)

        with patch("app.api.routes.auth.jwt.decode", return_value={"sub": "testuser", "type": "refresh"}), \
             patch("app.api.routes.auth.get_user_by_username", new_callable=AsyncMock, return_value=mock_user), \
             patch("app.api.routes.auth.async_session_maker", return_value=mock_sm), \
             patch("app.api.routes.auth.create_access_token", return_value="new.access"), \
             patch("app.api.routes.auth.create_refresh_token", return_value="new.refresh"):
            resp = client.post("/api/v1/auth/refresh?token=valid-refresh-token")

        assert resp.status_code == 200
        body = resp.json()
        assert body["access_token"] == "new.access"
        assert body["refresh_token"] == "new.refresh"

    def test_refresh_invalid_token_en(self, client):
        """An invalid (undecodable) refresh token should return 401 with English message."""
        with patch("app.api.routes.auth.jwt.decode", side_effect=Exception("Invalid token")):
            resp = client.post("/api/v1/auth/refresh?lang=en&token=garbage")
        assert resp.status_code == 401
        assert "refresh token" in resp.json()["detail"].lower()

    def test_refresh_invalid_token_fa(self, client):
        """Persian: 'توکن ریفرش نامعتبر یا منقضی شده است'"""
        with patch("app.api.routes.auth.jwt.decode", side_effect=Exception("Invalid token")):
            resp = client.post("/api/v1/auth/refresh?lang=fa&token=garbage")
        assert resp.status_code == 401
        detail = resp.json()["detail"]
        assert "توکن" in detail or "ریفرش" in detail

    def test_refresh_wrong_token_type(self, client):
        """A token with type != 'refresh' should be rejected."""
        with patch("app.api.routes.auth.jwt.decode", return_value={"sub": "testuser", "type": "access"}):
            resp = client.post("/api/v1/auth/refresh?lang=en&token=some-token")
        assert resp.status_code == 401
        assert "refresh token" in resp.json()["detail"].lower()

    def test_refresh_user_not_found_fa(self, client):
        """Persian: 'کاربر یافت نشد' — username in token doesn't exist."""
        with patch("app.api.routes.auth.jwt.decode", return_value={"sub": "ghost", "type": "refresh"}), \
             patch("app.api.routes.auth.get_user_by_username", new_callable=AsyncMock, return_value=None):
            resp = client.post("/api/v1/auth/refresh?lang=fa&token=valid-but-ghost")
        assert resp.status_code == 401
        assert "کاربر" in resp.json()["detail"]
