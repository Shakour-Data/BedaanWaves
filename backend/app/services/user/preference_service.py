"""Preference Service (Tier 6: User Services)

Stores arbitrary key/value user preferences as JSONB values.
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select

from app.db.base import async_session_maker
from app.models.models import UserPreference


class PreferenceService:
    """Get/set/list/delete generic user preferences."""

    def __init__(self, session_factory=async_session_maker):
        self.session_factory = session_factory

    async def get_preference(
        self, user_id: UUID, key: str, session=None
    ) -> Optional[UserPreference]:
        session = session or self.session_factory()
        owns = session is None
        try:
            result = await session.execute(
                select(UserPreference).where(
                    UserPreference.user_id == user_id,
                    UserPreference.key == key,
                )
            )
            return result.scalars().first()
        finally:
            if owns:
                await session.close()

    async def set_preference(
        self, user_id: UUID, key: str, value, session=None
    ) -> UserPreference:
        session = session or self.session_factory()
        owns = session is None
        try:
            result = await session.execute(
                select(UserPreference).where(
                    UserPreference.user_id == user_id,
                    UserPreference.key == key,
                )
            )
            preference = result.scalars().first()
            if preference is None:
                preference = UserPreference(user_id=user_id, key=key, value=value)
                session.add(preference)
            else:
                preference.value = value
            await session.commit()
            await session.refresh(preference)
            return preference
        finally:
            if owns:
                await session.close()

    async def list_preferences(
        self, user_id: UUID, session=None
    ) -> List[UserPreference]:
        session = session or self.session_factory()
        owns = session is None
        try:
            result = await session.execute(
                select(UserPreference).where(UserPreference.user_id == user_id)
            )
            return list(result.scalars().all())
        finally:
            if owns:
                await session.close()

    async def delete_preference(
        self, user_id: UUID, key: str, session=None
    ) -> bool:
        session = session or self.session_factory()
        owns = session is None
        try:
            result = await session.execute(
                select(UserPreference).where(
                    UserPreference.user_id == user_id,
                    UserPreference.key == key,
                )
            )
            preference = result.scalars().first()
            if preference is None:
                return False
            await session.delete(preference)
            await session.commit()
            return True
        finally:
            if owns:
                await session.close()


preference_service = PreferenceService()
