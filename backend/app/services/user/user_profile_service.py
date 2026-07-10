"""User Profile Service (Tier 6: User Services)

Manages editable profile fields on the User model (full name, email, UI
preferences such as language/theme/notifications). Kept intentionally thin so
it can be unit-tested with an injected async session.
"""

from typing import Dict, Optional
from uuid import UUID

from sqlalchemy import select

from app.db.base import async_session_maker
from app.models.models import User


class UserProfileService:
    """Reads and updates the profile of a user."""

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

        Returns the updated User, or ``None`` when the user does not exist.
        """
        session = session or self.session_factory()
        owns = session is None
        try:
            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalars().first()
            if user is None:
                return None
            for field, value in data.items():
                if value is not None:
                    setattr(user, field, value)
            await session.commit()
            await session.refresh(user)
            return user
        finally:
            if owns:
                await session.close()


user_profile_service = UserProfileService()
