"""Authentication Routes

Endpoints (all mounted under ``/api/v1/auth`` by main.py):

POST /auth/register   Create a new user account
POST /auth/login      Authenticate and obtain access/refresh tokens
POST /auth/refresh    Exchange a valid refresh token for new tokens
"""

from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, status
from jose import jwt
from sqlalchemy import select, update

from app.core.config import get_settings
from app.db.base import async_session_maker
from app.models.models import RefreshToken
from app.schemas.schemas import LoginRequest, RefreshTokenRequest, RegisterRequest, Token
from app.services.user.auth_service import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    create_user,
    get_user_by_email,
    get_user_by_username,
    hash_password,
)

settings = get_settings()
router = APIRouter(tags=["auth"])


@router.post("/register", response_model=Token)
async def register(data: RegisterRequest) -> Token:
    existing = await get_user_by_username(data.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already registered")
    existing_email = await get_user_by_email(data.email)
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")

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
async def login(data: LoginRequest) -> Token:
    user = await authenticate_user(data.username, data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access = create_access_token({"sub": user.username, "user_id": str(user.id)})
    refresh = create_refresh_token({"sub": user.username, "user_id": str(user.id)})
    expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    return Token(access_token=access, refresh_token=refresh, expires_in=expires_in)


@router.post("/refresh", response_model=Token)
async def refresh_token(data: RefreshTokenRequest) -> Token:
    token = data.refresh_token
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    username: str = payload.get("sub")
    token_type: str = payload.get("type")
    if username is None or token_type != "refresh":
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    user = await get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    async with async_session_maker() as session:
        now = datetime.now(UTC).replace(tzinfo=None)
        result = await session.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user.id,
                RefreshToken.revoked.is_(False),
                RefreshToken.expires_at > now,
            )
        )
        stored = result.scalars().first()
        if stored is None:
            raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

        await session.execute(
            update(RefreshToken).where(RefreshToken.id == stored.id).values(revoked=True)
        )
        await session.commit()

    access = create_access_token({"sub": user.username, "user_id": str(user.id)})
    refresh = create_refresh_token({"sub": user.username, "user_id": str(user.id)})
    expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    return Token(access_token=access, refresh_token=refresh, expires_in=expires_in)
