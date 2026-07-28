"""Authentication Service"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select

from app.core.config import get_settings
from app.db.base import async_session_maker
from app.models.models import User

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


async def get_user_by_username(username: str) -> Optional[User]:
    async with async_session_maker() as session:
        result = await session.execute(select(User).where(User.username == username))
        return result.scalars().first()


async def get_user_by_email(email: str) -> Optional[User]:
    async with async_session_maker() as session:
        result = await session.execute(select(User).where(User.email == email))
        return result.scalars().first()


async def create_user(username: str, email: str, hashed_password: str, full_name: Optional[str] = None) -> User:
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


async def authenticate_user(username: str, password: str) -> Optional[User]:
    user = await get_user_by_username(username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
