"""Authentication & Authorization Dependencies"""

import uuid
from typing import List, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from sqlalchemy import select

from app.core.config import get_settings
from app.db.base import async_session_maker
from app.models.models import User
from app.schemas.schemas import TokenData
from app.services.user.authorization_service import authorization_service

settings = get_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        token_type: str = payload.get("type")
        if username is None or token_type != "access":
            raise credentials_exception
    except jwt.JWTError:
        raise credentials_exception

    async with async_session_maker() as session:
        result = await session.execute(select(User).where(User.username == username))
        user = result.scalars().first()

    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_admin_user(current_user: User = Depends(get_current_active_user)) -> User:
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )
    return current_user


async def get_current_user_id(current_user: User = Depends(get_current_active_user)) -> uuid.UUID:
    """Return the authenticated user's id."""
    return current_user.id


def require_permissions(required: List[str]):
    """Dependency factory enforcing that the user holds ALL ``required`` permissions."""

    async def _checker(current_user: User = Depends(get_current_active_user)) -> User:
        missing = [p for p in required if not authorization_service.has_permission(current_user, p)]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permissions: {', '.join(missing)}",
            )
        return current_user

    return _checker


def require_roles(roles: List[str]):
    """Dependency factory enforcing that the user matches one of ``roles``.

    Supported roles: ``admin`` (``User.is_admin``) and ``user`` (any active user).
    """

    async def _checker(current_user: User = Depends(get_current_active_user)) -> User:
        normalized = {r.lower() for r in roles}
        if "admin" in normalized and authorization_service.is_admin(current_user):
            return current_user
        if "user" in normalized:
            return current_user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have the required role",
        )

    return _checker


async def get_route_user_id(request: Request) -> uuid.UUID:
    """Resolve the owning user id for a request.

    Uses the id validated by the global auth guard (``request.state.user_id``)
    when available, otherwise falls back to the configured dev user id so the
    local development frontend keeps working while the guard is disabled.
    """
    user_id = getattr(request.state, "user_id", None)
    if user_id is not None:
        return uuid.UUID(str(user_id))
    return uuid.UUID(settings.DEV_USER_ID)

