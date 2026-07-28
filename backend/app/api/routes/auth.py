"""Authentication Routes"""

from fastapi import APIRouter, Depends, HTTPException, status
from datetime import timedelta
from jose import jwt

from app.core.config import get_settings
from app.db.base import async_session_maker
from app.models.models import User
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

settings = get_settings()
router = APIRouter(prefix="/auth", tags=["auth"])


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
    return Token(access_token=access, refresh_token=refresh)


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
    return Token(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=Token)
async def refresh_token(token: str) -> Token:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    username: str = payload.get("sub")
    token_type: str = payload.get("type")
    if username is None or token_type != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user = await get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    access = create_access_token({"sub": user.username, "user_id": str(user.id)})
    refresh = create_refresh_token({"sub": user.username, "user_id": str(user.id)})
    return Token(access_token=access, refresh_token=refresh)
