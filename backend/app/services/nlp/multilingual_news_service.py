"""
Multilingual News Service - Tier 5 NLP Service

Fetches, aggregates, and classifies financial news across multiple languages
(English and Persian/Farsi).  Provides unified access to news from different
language sources with language-aware filtering and ranking.
"""

from contextlib import asynccontextmanager
from typing import Any

import aiohttp
import asyncio

from app.core.utils import utc_now_iso

from ..core import CachedService


class MultilingualNewsService(CachedService):
    """
    Multilingual news aggregation and classification service.

    Capabilities:
    - Multi-language support (English and Persian/Farsi)
    - Language-aware news fetching and filtering
    - News classification by category and language
    - Unified response format regardless of source language
    """

    SUPPORTED_LANGUAGES = ["en", "fa", "auto"]
    DEFAULT_LIMIT = 50
    PERSIAN_CHAR_RANGE = ("\u0600", "\u06FF")

    def __init__(
        self,
        service_name: str = "MultilingualNewsService",
        news_client: Any | None = None,
        cache_ttl_seconds: int = 1800,
    ):
        super().__init__(service_name, cache_ttl_seconds=cache_ttl_seconds)
        self.news_client = news_client

    async def initialize(self) -> None:
        self.logger.info("MultilingualNewsService initialized")

    async def shutdown(self) -> None:
        self.cache_clear()
        self.logger.info("MultilingualNewsService shutdown")

    def _detect_language(self, text: str) -> str:
        if not text:
            return "auto"
        persian_chars = sum(1 for c in text if self.PERSIAN_CHAR_RANGE[0] <= c <= self.PERSIAN_CHAR_RANGE[1])
        return "fa" if persian_chars > len(text) * 0.3 else "en"

    async def fetch_news(
        self,
        query: str | None = None,
        language: str = "auto",
        limit: int = DEFAULT_LIMIT,
    ) -> list[dict[str, Any]]:
        cache_key = f"ml_news:{language}:{limit}:{query or 'all'}"
        cached = self.get_cached(cache_key)
        if cached:
            return cached

        results: list[dict[str, Any]] = []

        if self.news_client:
            try:
                lang = "en" if language in ("en", "auto") else language
                fetched = await self.news_client.search(query or "", limit=limit)
                if isinstance(fetched, list):
                    results = fetched
            except Exception as exc:
                self.logger.warning(f"MultilingualNewsService fetch failed: {exc}")

        if not results:
            async with _get_async_session() as session:
                from app.models.models import News
                from sqlalchemy import desc, select

                stmt = select(News)
                if query:
                    stmt = stmt.where(News.title.ilike(f"%{query}%"))
                stmt = stmt.order_by(desc(News.published_at)).limit(limit)
                fetched = await session.execute(stmt)
                for row in fetched.scalars().all():
                    results.append(self._news_to_dict(row))

        if language != "auto" and results:
            results = [r for r in results if self._detect_language(r.get("title", "")) == language]

        self.set_cached(cache_key, results)
        return results

    async def classify_news(
        self,
        news_items: list[dict[str, Any]],
    ) -> dict[str, Any]:
        classified: dict[str, list[dict[str, Any]]] = {"en": [], "fa": []}
        for item in news_items:
            text = f"{item.get('title', '')} {item.get('body', '')}"
            lang = self._detect_language(text)
            classified[lang].append(item)

        return {
            "total": len(news_items),
            "by_language": {lang: len(items) for lang, items in classified.items()},
            "items": classified,
            "classified_at": utc_now_iso(),
        }

    async def get_news_by_language(
        self,
        language: str,
        limit: int = DEFAULT_LIMIT,
    ) -> list[dict[str, Any]]:
        return await self.fetch_news(language=language, limit=limit)

    async def batch_classify(
        self,
        batches: list[list[dict[str, Any]]],
    ) -> list[dict[str, Any]]:
        tasks = [self.classify_news(batch) for batch in batches]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        processed: list[dict[str, Any]] = []
        for batch, result in zip(batches, results):
            if isinstance(result, Exception):
                self.logger.error(f"Batch classification error: {result}")
                processed.append({"error": str(result), "total": len(batch)})
            else:
                processed.append(result)  # type: ignore[arg-type]
        return processed

    def _news_to_dict(self, news: Any) -> dict[str, Any]:
        return {
            "id": str(news.id) if hasattr(news, "id") else None,
            "source": getattr(news, "source", None),
            "title": getattr(news, "title", None),
            "body": getattr(news, "body", None),
            "url": getattr(news, "url", None),
            "language": getattr(news, "language", "en"),
            "published_at": news.published_at.isoformat() if getattr(news, "published_at", None) else None,
        }

    async def health_check(self) -> dict[str, Any]:
        base = await super().health_check()
        base.update({"source": "MultilingualNewsService", "supported_languages": self.SUPPORTED_LANGUAGES})
        return base


@asynccontextmanager
async def _get_async_session():
    from app.db.base import async_session_maker
    yield async_session_maker()
