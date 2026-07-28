"""Watchlist Service (Tier 6: User Services)

Manages a user's watchlists and the assets contained within them.
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select

from app.db.base import async_session_maker
from app.models.models import Watchlist, WatchlistItem


class WatchlistService:
    """CRUD operations for watchlists and their items."""

    def __init__(self, session_factory=async_session_maker):
        self.session_factory = session_factory

    async def create_watchlist(
        self,
        user_id: UUID,
        name: str,
        description: Optional[str] = None,
        is_default: bool = False,
        session=None,
    ) -> Watchlist:
        session = session or self.session_factory()
        owns = session is None
        try:
            watchlist = Watchlist(
                user_id=user_id,
                name=name,
                description=description,
                is_default=is_default,
            )
            session.add(watchlist)
            await session.commit()
            await session.refresh(watchlist)
            return watchlist
        finally:
            if owns:
                await session.close()

    async def list_watchlists(self, user_id: UUID, session=None) -> List[Watchlist]:
        session = session or self.session_factory()
        owns = session is None
        try:
            result = await session.execute(
                select(Watchlist).where(Watchlist.user_id == user_id)
            )
            return list(result.scalars().all())
        finally:
            if owns:
                await session.close()

    async def get_watchlist(
        self, watchlist_id: UUID, user_id: UUID, session=None
    ) -> Optional[Watchlist]:
        session = session or self.session_factory()
        owns = session is None
        try:
            result = await session.execute(
                select(Watchlist).where(
                    Watchlist.id == watchlist_id,
                    Watchlist.user_id == user_id,
                )
            )
            return result.scalars().first()
        finally:
            if owns:
                await session.close()

    async def delete_watchlist(
        self, watchlist_id: UUID, user_id: UUID, session=None
    ) -> bool:
        session = session or self.session_factory()
        owns = session is None
        try:
            watchlist = await self.get_watchlist(watchlist_id, user_id, session=session)
            if watchlist is None:
                return False
            await session.delete(watchlist)
            await session.commit()
            return True
        finally:
            if owns:
                await session.close()

    async def add_item(
        self,
        watchlist_id: UUID,
        user_id: UUID,
        asset_id: UUID,
        note: Optional[str] = None,
        alert_threshold_pct: Optional[float] = None,
        session=None,
    ) -> Optional[WatchlistItem]:
        session = session or self.session_factory()
        owns = session is None
        try:
            watchlist = await self.get_watchlist(watchlist_id, user_id, session=session)
            if watchlist is None:
                return None
            item = WatchlistItem(
                watchlist_id=watchlist_id,
                asset_id=asset_id,
                note=note,
                alert_threshold_pct=alert_threshold_pct,
            )
            session.add(item)
            await session.commit()
            await session.refresh(item)
            return item
        finally:
            if owns:
                await session.close()

    async def remove_item(
        self, watchlist_id: UUID, item_id: UUID, user_id: UUID, session=None
    ) -> bool:
        session = session or self.session_factory()
        owns = session is None
        try:
            result = await session.execute(
                select(WatchlistItem).where(
                    WatchlistItem.id == item_id,
                    WatchlistItem.watchlist_id == watchlist_id,
                )
            )
            item = result.scalars().first()
            if item is None:
                return False
            watchlist = await self.get_watchlist(
                watchlist_id, user_id, session=session
            )
            if watchlist is None:
                return False
            await session.delete(item)
            await session.commit()
            return True
        finally:
            if owns:
                await session.close()


watchlist_service = WatchlistService()
