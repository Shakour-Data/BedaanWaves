"""User Profile Service (Tier 6: User Services)

Manages editable profile fields on the User model (full name, email, UI
preferences such as language/theme/notifications). Kept intentionally thin so
it can be unit-tested with an injected async session.
"""

from typing import Dict, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from app.db.base import async_session_maker
from app.models.models import User


class UserProfileService:
    """Reads and updates the profile of a user."""

    # Allow-list of fields that can be updated via profile service
    ALLOWED_FIELDS = {
        "email",
        "full_name",
        "preferred_language",
        "theme",
        "notifications_enabled",
    }

    def __init__(self, session_factory=async_session_maker):
        self.session_factory = session_factory

    async def get_profile(self, user_id: UUID, session=None) -> Optional[User]:
        session = session or self.session_factory()
        owns = session is None
        try:
            result = await session.execute(select(User).where(User.id == user_id))
            return result.scalars().first()
        finally:
            if owns:
                await session.close()

async def update_profile(
    self, user_id: UUID, data: Dict, session=None
) -> Optional[User]:
    """Apply non-null ``data`` fields to the user and persist.

    Uses allow-list validation to prevent mass-assignment vulnerabilities.
    Handles email uniqueness constraint violations.

    Returns the updated User, or ``None`` when the user does not exist.
    """
    session = session or self.session_factory()
    owns = session is None
    try:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()
        if user is None:
            return None

        # Apply only allowed fields using explicit validation
        for field, value in data.items():
            if field in self.ALLOWED_FIELDS and value is not None:
                setattr(user, field, value)

        await session.commit()
        await session.refresh(user)
        return user
    except IntegrityError as exc:
        await session.rollback()
        # Check if it's an email uniqueness violation
        if "users_email_key" in str(exc) or "duplicate key value violates unique constraint" in str(exc):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email address already in use"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database integrity error"
        )
    finally:
        if owns:
            await session.close()


user_profile_service = UserProfileService()
