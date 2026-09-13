"""Event-Driven Cache Invalidation Service.

Subscribes to domain events published on the EventBus and invalidates
stale cache entries in real time.  This removes the need for brittle
TTL-only cache eviction and keeps read-models consistent with the
write-model within milliseconds.

Usage::

    from app.infrastructure.events.event_bus import EventBus
    from app.services.core.cache_service import CacheService

    svc = CacheInvalidationService(event_bus, cache_service)
    await svc.start()          # subscribes to all topics
    await svc.stop()
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.infrastructure.events.event_bus import EventBus, Event
    from app.services.core.cache_service import CacheService

logger = logging.getLogger(__name__)


class CacheInvalidationService:
    """Invalidate cache entries reactively when domain events fire."""

    def __init__(
        self,
        event_bus: "EventBus",
        cache_service: "CacheService",
    ) -> None:
        self._event_bus = event_bus
        self._cache = cache_service
        self._started = False

    # ------------------------------------------------------------------
    # lifecycle
    # ------------------------------------------------------------------
    async def start(self) -> None:
        if self._started:
            return
        await self._event_bus.subscribe("asset-updated", self._handle_asset_event)
        await self._event_bus.subscribe("asset-created", self._handle_asset_event)
        await self._event_bus.subscribe("price-updated", self._handle_price_event)
        await self._event_bus.subscribe("ml-signal-created", self._handle_ml_event)
        await self._event_bus.subscribe("portfolio-updated", self._handle_portfolio_event)
        await self._event_bus.subscribe("news-updated", self._handle_news_event)
        await self._event_bus.subscribe("user-preferences-updated", self._handle_user_event)
        self._started = True
        logger.info("CacheInvalidationService subscribed to 7 event topics")

    async def stop(self) -> None:
        self._started = False
        logger.info("CacheInvalidationService stopped")

    # ------------------------------------------------------------------
    # event handlers
    # ------------------------------------------------------------------
    async def _handle_asset_event(self, event: "Event") -> None:
        asset_id = event.data.get("asset_id") or event.data.get("symbol")
        if not asset_id:
            return
        await self._cache.delete(f"asset:{asset_id}", namespace="assets")
        await self._cache.delete(f"asset:{asset_id}:*", namespace="analysis")
        await self._cache.clear(namespace="dashboard")
        logger.debug("Invalidated asset cache for %s", asset_id)

    async def _handle_price_event(self, event: "Event") -> None:
        asset_id = event.data.get("asset_id") or event.data.get("symbol")
        if not asset_id:
            return
        await self._cache.delete(f"prices:{asset_id}:*", namespace="market")
        await self._cache.delete(f"indicators:{asset_id}:*", namespace="analysis")
        await self._cache.delete(f"quotes:{asset_id}", namespace="market")
        logger.debug("Invalidated price cache for %s", asset_id)

    async def _handle_ml_event(self, event: "Event") -> None:
        symbol = event.data.get("symbol") or event.data.get("asset_id")
        if not symbol:
            return
        await self._cache.delete(f"ml:{symbol}:*", namespace="ml")
        await self._cache.delete(f"prediction:{symbol}", namespace="ml")
        logger.debug("Invalidated ML cache for %s", symbol)

    async def _handle_portfolio_event(self, event: "Event") -> None:
        user_id = event.data.get("user_id")
        if not user_id:
            return
        await self._cache.delete(f"portfolio:{user_id}:*", namespace="portfolio")
        await self._cache.clear(namespace="dashboard")
        logger.debug("Invalidated portfolio cache for user %s", user_id)

    async def _handle_news_event(self, event: "Event") -> None:
        await self._cache.clear(namespace="news")
        await self._cache.clear(namespace="sentiment")
        logger.debug("Invalidated news/sentiment cache")

    async def _handle_user_event(self, event: "Event") -> None:
        user_id = event.data.get("user_id")
        if not user_id:
            return
        await self._cache.delete(f"user:{user_id}:*", namespace="user")
        await self._cache.delete(f"preferences:{user_id}", namespace="user")
        logger.debug("Invalidated user cache for %s", user_id)

    # ------------------------------------------------------------------
    # manual invalidation helpers
    # ------------------------------------------------------------------
    async def invalidate_asset(self, asset_id: str) -> None:
        await self._cache.delete(f"asset:{asset_id}", namespace="assets")
        await self._cache.delete(f"asset:{asset_id}:*", namespace="analysis")

    async def invalidate_prices(self, asset_id: str) -> None:
        await self._cache.delete(f"prices:{asset_id}:*", namespace="market")
        await self._cache.delete(f"indicators:{asset_id}:*", namespace="analysis")

    async def invalidate_namespace(self, namespace: str) -> None:
        await self._cache.clear(namespace=namespace)

    def get_stats(self) -> dict[str, Any]:
        return {
            "service": "CacheInvalidationService",
            "started": self._started,
            "topics": [
                "asset-updated",
                "asset-created",
                "price-updated",
                "ml-signal-created",
                "portfolio-updated",
                "news-updated",
                "user-preferences-updated",
            ],
        }