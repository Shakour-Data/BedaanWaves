"""Unit tests for the password-reset API layer.

Tests the request / verify / confirm endpoints using FastAPI's TestClient
with the service layer mocked out (no DB or email required).
"""
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.password_reset import router


@pytest.fixture
def app():
    """Create a minimal FastAPI app with only the password-reset router."""
    _app = FastAPI()
    _app.include_router(router, prefix="/api/v1/auth", tags=["password-reset"])
    return _app


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def mock_service():
    """Patch all service functions used by the route handlers."""
    with patch("app.api.routes.password_reset.create_password_reset_token") as mock_create, \
         patch("app.api.routes.password_reset.verify_reset_token") as mock_verify, \
         patch("app.api.routes.password_reset.reset_password") as mock_reset:
        yield {
            "create": mock_create,
            "verify": mock_verify,
            "reset": mock_reset,
        }


class TestRequestPasswordReset:
    def test_returns_200_with_generic_message_for_known_email(self, client, mock_service):
        mock_service["create"].return_value = "fake_raw_token"

        resp = client.post("/api/v1/auth/password-reset/request", json={"email": "user@example.com"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        assert "sent" in body["message"].lower() or "link" in body["message"].lower()

    def test_returns_200_with_generic_message_for_unknown_email(self, client, mock_service):
        """Anti-enumeration: same response whether email exists or not."""
        mock_service["create"].return_value = None

        resp = client.post("/api/v1/auth/password-reset/request", json={"email": "nobody@example.com"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"

    def test_rejects_invalid_email_format(self, client, mock_service):
        resp = client.post("/api/v1/auth/password-reset/request", json={"email": "not-an-email"})
        assert resp.status_code == 422  # Pydantic EmailStr validation


class TestVerifyResetToken:
    def test_returns_valid_true(self, client, mock_service):
        mock_service["verify"].return_value = True
        resp = client.post("/api/v1/auth/password-reset/verify", json={"token": "valid-token"})
        assert resp.status_code == 200
        assert resp.json()["valid"] is True

    def test_returns_valid_false(self, client, mock_service):
        mock_service["verify"].return_value = False
        resp = client.post("/api/v1/auth/password-reset/verify", json={"token": "invalid"})
        assert resp.status_code == 200
        assert resp.json()["valid"] is False


class TestConfirmPasswordReset:
    def test_returns_200_on_success(self, client, mock_service):
        mock_service["reset"].return_value = True
        resp = client.post(
            "/api/v1/auth/password-reset/confirm",
            json={"token": "valid-token", "new_password": "newpass123"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"

    def test_returns_400_on_invalid_token(self, client, mock_service):
        mock_service["reset"].return_value = False
        resp = client.post(
            "/api/v1/auth/password-reset/confirm",
            json={"token": "expired", "new_password": "newpass123"},
        )
        assert resp.status_code == 400
        body = resp.json()
        assert "expired" in body["detail"].lower() or "invalid" in body["detail"].lower()

    def test_returns_400_when_password_too_short(self, client, mock_service):
        mock_service["reset"].return_value = True
        resp = client.post(
            "/api/v1/auth/password-reset/confirm",
            json={"token": "valid-token", "new_password": "short"},
        )
        assert resp.status_code == 400

    def test_returns_400_when_token_missing(self, client, mock_service):
        mock_service["reset"].return_value = True
        resp = client.post(
            "/api/v1/auth/password-reset/confirm",
            json={"token": "", "new_password": "newpass123"},
        )
        assert resp.status_code == 400

    def test_uses_lang_query_param(self, client, mock_service):
        mock_service["reset"].return_value = True
        resp = client.post(
            "/api/v1/auth/password-reset/confirm?lang=fa",
            json={"token": "valid", "new_password": "newpass123"},
        )
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Shared / language message tests
# ---------------------------------------------------------------------------
class TestLanguageSupport:
    def test_request_returns_farsi_message(self, client, mock_service):
        mock_service["create"].return_value = "token"
        resp = client.post(
            "/api/v1/auth/password-reset/request?lang=fa",
            json={"email": "user@example.com"},
        )
        assert resp.status_code == 200
        # The Persian message should contain Persian characters
        assert "ایمیل" in resp.json()["message"] or "لینک" in resp.json()["message"]

    def test_confirm_returns_farsi_on_invalid_token(self, client, mock_service):
        mock_service["reset"].return_value = False
        resp = client.post(
            "/api/v1/auth/password-reset/confirm?lang=fa",
            json={"token": "expired", "new_password": "newpass123"},
        )
        assert resp.status_code == 400
        assert "بازیابی" in resp.json()["detail"] or "لینک" in resp.json()["detail"]
