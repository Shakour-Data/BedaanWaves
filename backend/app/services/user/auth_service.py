"""Authentication Service"""

import logging
import os
import secrets
from datetime import UTC, datetime, timedelta

import bcrypt
from jose import JWTError, jwt
from sqlalchemy import select, update

from app.core.config import get_settings
from app.db.base import async_session_maker
from app.models.models import User

settings = get_settings()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + (expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


async def get_user_by_username(username: str) -> User | None:
    async with async_session_maker() as session:
        result = await session.execute(select(User).where(User.username == username))
        return result.scalars().first()


async def get_user_by_email(email: str) -> User | None:
    async with async_session_maker() as session:
        result = await session.execute(select(User).where(User.email == email))
        return result.scalars().first()


async def create_user(username: str, email: str, hashed_password: str, full_name: str | None = None) -> User:
    user = User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        full_name=full_name,
    )
    async with async_session_maker() as session:
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


async def authenticate_user(username: str, password: str) -> User | None:
    user = await get_user_by_username(username)
    if not user:
        return None
    if not verify_password(password, str(user.hashed_password)):
        return None
    return user


async def ensure_admin_user() -> None:
    if await get_user_by_username("admin"):
        return
    admin_password = os.environ.get("ADMIN_PASSWORD")
    if not admin_password:
        if os.environ.get("ENVIRONMENT", "development") == "production":
            raise RuntimeError(
                "ADMIN_PASSWORD must be set in environment for production deployments"
            )
        admin_password = secrets.token_urlsafe(16)
        hashed = hash_password(admin_password)
        logging.getLogger(__name__).warning(
            "ADMIN_PASSWORD not set in environment. Generated temporary admin "
            f"password. Hash prefix (first 8 chars): {hashed[:8]}... - "
            "Store the password securely; it will not be shown again."
        )
    await create_user(
        username="admin",
        email="admin@bedaanwaves.local",
        hashed_password=hash_password(admin_password),
        full_name="Admin User",
    )
    async with async_session_maker() as session:
        await session.execute(
            update(User).where(User.username == "admin").values(is_admin=True)
        )
        await session.commit()
