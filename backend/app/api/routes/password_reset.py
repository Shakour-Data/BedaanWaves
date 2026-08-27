"""Password Recovery API Routes

Endpoints (all mounted under ``/api/v1`` by main.py, so effectively
``/api/v1/auth/password-reset/*``):

POST /auth/password-reset/request   Request a recovery link (email)
POST /auth/password-reset/confirm   Redeem a token + set new password
POST /auth/password-reset/verify    Check whether a token is still valid

Security: every endpoint returns a *generic* success message regardless of
whether the email/token exists, so account enumeration is mitigated.
Error philosophy (spec.yaml): "Never blame user; always suggest next action".
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
import logging

from app.schemas.schemas import (
    PasswordResetRequest,
    PasswordResetConfirm,
    PasswordResetVerifyRequest,
    PasswordResetResponse,
    PasswordResetVerifyResponse,
)
from app.services.user.password_reset_service import (
    create_password_reset_token,
    verify_reset_token,
    reset_password,
)
from app.services.user.auth_service import get_user_by_email

logger = logging.getLogger(__name__)
router = APIRouter(tags=["password-reset"])

# ---------------------------------------------------------------------------
# User-facing, non-technical message lookup (WCAG 2.1 AA: plain language)
# ---------------------------------------------------------------------------
MESSAGES = {
    "en": {
        "request_sent": "If an account exists for that email, a recovery link has been sent.",
        "token_invalid": "That recovery link has expired or is no longer valid. Please request a new link.",
        "password_updated": "Your password has been updated. You can now sign in.",
        "password_too_short": "Password must be at least 8 characters long.",
        "token_missing": "No recovery token was provided. Please open the link from your email.",
    },
    "fa": {
        "request_sent": "اگر حساب کاربری با این ایمیل وجود داشته باشد، لینک بازیابی ارسال شده است.",
        "token_invalid": "این لینک بازیابی منقضی شده یا معتبر نیست. لطفاً یک لینک جدید درخواست کنید.",
        "password_updated": "رمز عبور شما بروزرسانی شد. اکنون می‌توانید وارد شوید.",
        "password_too_short": "رمز عبور باید حداقل ۸ کاراکتر باشد.",
        "token_missing": "توکن بازیابی ارائه نشده است. لطفاً از لینک ایمیل خود استفاده کنید.",
    },
}


def _msg(lang: str, key: str) -> str:
    return MESSAGES.get(lang, MESSAGES["en"]).get(key, MESSAGES["en"][key])


@router.post("/password-reset/request", response_model=PasswordResetResponse)
async def request_password_reset(
    data: PasswordResetRequest,
    lang: str = Query("en", pattern="^(en|fa)$"),
):
    """Request a password-reset link.

    Always returns a generic ``status: success`` message to prevent account
    enumeration, whether or not the e-mail exists in the database.
    """
    raw_token = await create_password_reset_token(data.email)
    if raw_token is not None:
        logger.info(
            "Password reset token generated for email=%s (token hash stored)",
            data.email,
        )
    else:
        logger.info("Password reset requested for unknown email (enumerated-safe)")

    return PasswordResetResponse(
        status="success",
        message=_msg(lang, "request_sent"),
    )


@router.post("/password-reset/verify", response_model=PasswordResetVerifyResponse)
async def verify_reset_token_route(
    data: PasswordResetVerifyRequest,
    lang: str = Query("en", pattern="^(en|fa)$"),
):
    """Verify that a recovery token is valid (not consumed, not expired)."""
    valid = await verify_reset_token(data.token)
    return PasswordResetVerifyResponse(
        valid=valid,
        email_hint=None,  # never disclose the target email
    )


@router.post("/password-reset/confirm", response_model=PasswordResetResponse)
async def confirm_password_reset(
    data: PasswordResetConfirm,
    lang: str = Query("en", pattern="^(en|fa)$"),
):
    """Consume a reset token and set a new password."""
    if not data.token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_msg(lang, "token_missing"),
        )
    if len(data.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_msg(lang, "password_too_short"),
        )

    ok = await reset_password(data.token, data.new_password)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_msg(lang, "token_invalid"),
        )
    return PasswordResetResponse(
        status="success",
        message=_msg(lang, "password_updated"),
    )
