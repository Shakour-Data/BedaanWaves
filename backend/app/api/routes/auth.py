"""Authentication Routes

Endpoints (all mounted under ``/api/v1/auth`` by main.py):

POST /auth/register   Create a new user account
POST /auth/login      Authenticate and obtain access/refresh tokens
POST /auth/refresh    Exchange a valid refresh token for new tokens
"""

import hashlib
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from jose import jwt  # noqa: F401  (used by tests via app.api.routes.auth.jwt)
from sqlalchemy import select, update

from app.api.dependencies import require_auth_rate_limit
from app.core.config import get_settings
from app.db.base import async_session_maker
from app.models.models import RefreshToken
from app.schemas.schemas import LoginRequest, RefreshTokenRequest, RegisterRequest, Token
from app.services.user.auth_service import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    create_user,
    decode_token,
    get_user_by_email,
    get_user_by_username,
    hash_password,
    store_refresh_token,
)

settings = get_settings()
router = APIRouter(tags=["auth"])


@router.post("/register", response_model=Token)
async def register(
    data: RegisterRequest,
    request: Request,
    _rate_limit: None = Depends(require_auth_rate_limit),
) -> Token:
    """Register a new user account and return access/refresh tokens."""
    raise HTTPException(
        status_code=503,
        detail="Authentication service is temporarily disabled for development",
    )
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
    await store_refresh_token(
        user_id=user.id,
        refresh_token=refresh,
        user_agent=request.headers.get("user-agent"),
    )
    expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    return Token(access_token=access, refresh_token=refresh, expires_in=expires_in)


@router.post("/login", response_model=Token)
async def login(
    data: LoginRequest,
    request: Request,
    _rate_limit: None = Depends(require_auth_rate_limit),
) -> Token:
    """Authenticate user and return access/refresh tokens."""
    raise HTTPException(
        status_code=503,
        detail="Authentication service is temporarily disabled for development",
    )
    user = await authenticate_user(data.username, data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access = create_access_token({"sub": user.username, "user_id": str(user.id)})
    refresh = create_refresh_token({"sub": user.username, "user_id": str(user.id)})
    await store_refresh_token(
        user_id=user.id,
        refresh_token=refresh,
        user_agent=request.headers.get("user-agent"),
    )
    expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    return Token(access_token=access, refresh_token=refresh, expires_in=expires_in)


@router.post("/refresh", response_model=Token)
async def refresh_token(
    data: RefreshTokenRequest,
) -> Token:
    """Exchange a valid refresh token for new tokens.

    Accepts the refresh token in the JSON request body only.
    """
    token = data.refresh_token
    if token is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = decode_token(token)
        if payload is None:
            raise Exception("Invalid token")
    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    username: str = payload.get("sub")
    token_type: str = payload.get("type")
    if username is None or token_type != "refresh":
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await get_user_by_username(username)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    async with async_session_maker() as session:
        now = datetime.now(UTC)
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        result = await session.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user.id,
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked.is_(False),
                RefreshToken.expires_at > now,
            )
        )
        stored = result.scalars().first()
        if stored is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        await session.execute(
            update(RefreshToken).where(RefreshToken.id == stored.id).values(revoked=True)
        )

        access = create_access_token({"sub": user.username, "user_id": str(user.id)})
        refresh = create_refresh_token({"sub": user.username, "user_id": str(user.id)})

        new_hash = hashlib.sha256(refresh.encode("utf-8")).hexdigest()
        new_expires = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        new_stored = RefreshToken(
            user_id=user.id,
            token_hash=new_hash,
            expires_at=new_expires,
            revoked=False,
        )
        session.add(new_stored)
        await session.commit()

    expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    return Token(access_token=access, refresh_token=refresh, expires_in=expires_in)
