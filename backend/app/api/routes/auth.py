"""Authentication Routes"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from datetime import timedelta, datetime, timezone
from jose import jwt

from app.core.config import get_settings
from app.db.base import async_session_maker
from app.models.models import User, RefreshToken
from app.schemas.schemas import Token, LoginRequest, RegisterRequest
from app.services.user.auth_service import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    get_user_by_username,
    get_user_by_email,
    create_user,
    authenticate_user,
)
from sqlalchemy import select, update

settings = get_settings()
router = APIRouter(tags=["auth"])

# Simple language mapping for error messages
ERROR_MESSAGES = {
    "en": {
        "username_exists": "Username already registered",
        "email_exists": "Email already registered",
        "invalid_credentials": "Incorrect username or password",
        "user_not_found": "User not found",
        "invalid_refresh": "Invalid or expired refresh token",
    },
    "fa": {
        "username_exists": "نام کاربری قبلاً ثبت شده است",
        "email_exists": "ایمیل قبلاً ثبت شده است",
        "invalid_credentials": "نام کاربری یا رمز عبور نادرست است",
        "user_not_found": "کاربر یافت نشد",
        "invalid_refresh": "توکن بازسازی نامعتبر یا منقضی شده است",
    },
}

def get_message(lang: str, key: str) -> str:
    return ERROR_MESSAGES.get(lang, ERROR_MESSAGES["en"]).get(key, "")

@router.post("/register", response_model=Token)
async def register(
    data: RegisterRequest, 
    lang: str = Query("en", pattern="^(en|fa)$")
) -> Token:
    existing = await get_user_by_username(data.username)
    if existing:
        raise HTTPException(status_code=400, detail=get_message(lang, "username_exists"))
    existing_email = await get_user_by_email(data.email)
    if existing_email:
        raise HTTPException(status_code=400, detail=get_message(lang, "email_exists"))

    user = await create_user(
        username=data.username,
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
    )
    access = create_access_token({"sub": user.username, "user_id": str(user.id)})
    refresh = create_refresh_token({"sub": user.username, "user_id": str(user.id)})
    expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    return Token(access_token=access, refresh_token=refresh, expires_in=expires_in)


@router.post("/login", response_model=Token)
async def login(
    data: LoginRequest, 
    lang: str = Query("en", pattern="^(en|fa)$")
) -> Token:
    user = await authenticate_user(data.username, data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=get_message(lang, "invalid_credentials"),
            headers={"WWW-Authenticate": "Bearer"},
        )
    access = create_access_token({"sub": user.username, "user_id": str(user.id)})
    refresh = create_refresh_token({"sub": user.username, "user_id": str(user.id)})
    expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    return Token(access_token=access, refresh_token=refresh, expires_in=expires_in)


@router.post("/refresh", response_model=Token)
async def refresh_token(
    token: str, 
    lang: str = Query("en", pattern="^(en|fa)$")
) -> Token:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except Exception:
        raise HTTPException(status_code=401, detail=get_message(lang, "invalid_refresh"))
    username: str = payload.get("sub")
    token_type: str = payload.get("type")
    if username is None or token_type != "refresh":
        raise HTTPException(status_code=401, detail=get_message(lang, "invalid_refresh"))

    user = await get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=401, detail=get_message(lang, "user_not_found"))

    async with async_session_maker() as session:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        result = await session.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user.id,
                RefreshToken.revoked.is_(False),
                RefreshToken.expires_at > now,
            )
        )
        stored = result.scalars().first()
        if stored is None:
            raise HTTPException(status_code=401, detail=get_message(lang, "invalid_refresh"))

        await session.execute(
            update(RefreshToken).where(RefreshToken.id == stored.id).values(revoked=True)
        )
        await session.commit()

    access = create_access_token({"sub": user.username, "user_id": str(user.id)})
    refresh = create_refresh_token({"sub": user.username, "user_id": str(user.id)})
    expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    return Token(access_token=access, refresh_token=refresh, expires_in=expires_in)