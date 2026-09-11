"""Authentication Service"""

import hashlib
import logging
import os
import secrets
from datetime import UTC, datetime, timedelta
from functools import lru_cache

import bcrypt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jose import JWTError, jwt
from sqlalchemy import select, update

from app.core.config import get_settings
from app.db.base import async_session_maker
from app.models.models import RefreshToken, User

settings = get_settings()


def _generate_rsa_keys():
    """Generate RSA key pair for RS256 JWT signing."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    return private_pem, public_pem


@lru_cache(maxsize=1)
def _get_jwt_keys():
    """Return (signing_key, verification_key) based on configured algorithm."""
    if settings.JWT_ALGORITHM == "RS256":
        private_key = settings.JWT_PRIVATE_KEY
        public_key = settings.JWT_PUBLIC_KEY
        if not private_key or not public_key:
            if settings.ENVIRONMENT == "production":
                raise RuntimeError(
                    "JWT_PRIVATE_KEY and JWT_PUBLIC_KEY must be set when "
                    "JWT_ALGORITHM=RS256 in production."
                )
            private_key, public_key = _generate_rsa_keys()
        return private_key, public_key
    return settings.JWT_SECRET, settings.JWT_SECRET


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
    key, _ = _get_jwt_keys()
    return jwt.encode(to_encode, key, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + (expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))
    to_encode.update({"exp": expire, "type": "refresh"})
    key, _ = _get_jwt_keys()
    return jwt.encode(to_encode, key, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict | None:
    try:
        _, verification_key = _get_jwt_keys()
        payload = jwt.decode(token, verification_key, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


async def store_refresh_token(user_id, refresh_token: str, user_agent: str | None = None) -> None:
    """Persist a hashed refresh token so the refresh endpoint can validate it server-side."""
    token_hash = _hash_token(refresh_token)
    expires_at = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    async with async_session_maker() as session:
        stored = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            revoked=False,
            user_agent=user_agent,
        )
        session.add(stored)
        await session.commit()


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

    if getattr(user, "locked_until", None) and user.locked_until > datetime.now(UTC):
        return None

    if not verify_password(password, str(user.hashed_password)):
        if user.id is not None:
            await _increment_failed_login(user.id)
        return None

    if getattr(user, "failed_login_attempts", 0) > 0:
        await _reset_failed_login(user.id)
    return user


async def _increment_failed_login(user_id: int) -> None:
    async with async_session_maker() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()
        if not user:
            return
        user.failed_login_attempts = int(getattr(user, "failed_login_attempts", 0) + 1)
        if user.failed_login_attempts >= 5:
            user.locked_until = datetime.now(UTC) + timedelta(minutes=15)
        await session.commit()


async def _reset_failed_login(user_id: int) -> None:
    async with async_session_maker() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()
        if not user:
            return
        user.failed_login_attempts = 0
        user.locked_until = None
        await session.commit()


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
        import sys
        print(
            f"WARNING: ADMIN_PASSWORD not set. Generated temporary admin password: {admin_password}",
            file=sys.stderr,
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
