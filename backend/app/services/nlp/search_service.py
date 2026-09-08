"""
Search Service - Tier 5 NLP Service

Unified multi-language search across news articles, stock symbols,
and market data.  Provides ranked results with relevance scoring
and language-aware query processing.
"""

import asyncio
from typing import Any

from app.core.utils import utc_now_iso

from ..core import CachedService


class SearchService(CachedService):
    """
    Multi-language search service for the BedaanWaves platform.

    Capabilities:
    - Cross-domain search (news, stocks, portfolios)
    - Language-aware query processing (English / Persian)
    - Relevance-based result ranking
    - Faceted result aggregation
    """

    SUPPORTED_LANGUAGES = ["en", "fa", "auto"]
    DEFAULT_LIMIT = 20
    PERSIAN_CHAR_RANGE = ("\u0600", "\u06FF")

    def __init__(
        self,
        service_name: str = "SearchService",
        cache_ttl_seconds: int = 300,
        news_service: Any | None = None,
        stock_service: Any | None = None,
    ):
        super().__init__(service_name, cache_ttl_seconds=cache_ttl_seconds)
        self.news_service = news_service
        self.stock_service = stock_service

    async def initialize(self) -> None:
        self.logger.info("SearchService initialized")

    async def shutdown(self) -> None:
        self.cache_clear()
        self.logger.info("SearchService shutdown")

    def _detect_language(self, text: str) -> str:
        if not text:
            return "auto"
        persian_chars = sum(1 for c in text if self.PERSIAN_CHAR_RANGE[0] <= c <= self.PERSIAN_CHAR_RANGE[1])
        return "fa" if persian_chars > len(text) * 0.3 else "en"

    async def search(
        self,
        query: str,
        limit: int = DEFAULT_LIMIT,
        language: str = "auto",
        domains: list[str] | None = None,
    ) -> dict[str, Any]:
        cache_key = f"search:{query}:{limit}:{language}:{','.join(domains or [])}"
        cached = self.get_cached(cache_key)
        if cached:
            return cached

        lang = self._detect_language(query) if language == "auto" else language
        domains = domains or ["news", "stocks", "portfolios"]

        tasks = []
        if "news" in domains:
            tasks.append(self._search_news(query, limit, lang))
        if "stocks" in domains:
            tasks.append(self._search_stocks(query, limit))
        if "portfolios" in domains:
            tasks.append(self._search_portfolios(query, limit))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        news_results = results[0] if len(results) > 0 and not isinstance(results[0], Exception) else []
        stock_results = results[1] if len(results) > 1 and not isinstance(results[1], Exception) else []
        portfolio_results = results[2] if len(results) > 2 and not isinstance(results[2], Exception) else []

        ranked = self._rank_results(news_results + stock_results + portfolio_results)
        response = {
            "query": query,
            "language": lang,
            "total": len(ranked),
            "results": ranked[:limit],
            "facets": {
                "news": len(news_results),
                "stocks": len(stock_results),
                "portfolios": len(portfolio_results),
            },
            "timestamp": utc_now_iso(),
        }

        self.set_cached(cache_key, response)
        return response

    async def _search_news(self, query: str, limit: int, lang: str) -> list[dict[str, Any]]:
        if self.news_service and hasattr(self.news_service, "search_news"):
            try:
                return await self.news_service.search_news(query=query, limit=limit)
            except Exception as exc:
                self.logger.warning(f"News search failed: {exc}")
        async with _get_async_session() as session:
            from sqlalchemy import desc, select

            from app.models.models import News

            stmt = select(News).where(News.title.ilike(f"%{query}%")).order_by(desc(News.published_at)).limit(limit)
            result = await session.execute(stmt)
            return [
                {
                    "id": str(n.id),
                    "type": "news",
                    "title": n.title,
                    "url": n.url,
                    "source": n.source,
                    "score": 1.0,
                }
                for n in result.scalars().all()
            ]

    async def _search_stocks(self, query: str, limit: int) -> list[dict[str, Any]]:
        if self.stock_service and hasattr(self.stock_service, "search"):
            try:
                return await self.stock_service.search(query, limit=limit)
            except Exception:
                pass
        async with _get_async_session() as session:
            from sqlalchemy import select

            from app.models.models import Asset

            stmt = select(Asset).where(Asset.symbol.ilike(f"%{query}%")).limit(limit)
            result = await session.execute(stmt)
            return [
                {
                    "id": str(a.id),
                    "type": "stock",
                    "title": f"{a.symbol} - {a.name}",
                    "symbol": a.symbol,
                    "score": 1.0,
                }
                for a in result.scalars().all()
            ]

    async def _search_portfolios(self, query: str, limit: int) -> list[dict[str, Any]]:
        async with _get_async_session() as session:
            from sqlalchemy import select

            from app.models.models import Portfolio

            stmt = select(Portfolio).where(Portfolio.name.ilike(f"%{query}%")).limit(limit)
            result = await session.execute(stmt)
            return [
                {
                    "id": str(p.id),
                    "type": "portfolio",
                    "title": p.name,
                    "score": 0.8,
                }
                for p in result.scalars().all()
            ]

    def _rank_results(self, results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not results:
            return []
        max_score = max(r.get("score", 0) for r in results) or 1.0
        for r in results:
            r["relevance"] = round(r.get("score", 0) / max_score, 4)
        return sorted(results, key=lambda x: x.get("relevance", 0), reverse=True)

    async def suggest(self, partial: str, limit: int = 10) -> list[str]:
        if len(partial) < 2:
            return []
        results = await self.search(partial, limit=limit)
        suggestions = []
        for r in results["results"][:limit]:
            title = r.get("title", "")
            if title:
                suggestions.append(title)
        return suggestions

    async def health_check(self) -> dict[str, Any]:
        base = await super().health_check()
        base.update({
            "source": "SearchService",
            "supported_languages": self.SUPPORTED_LANGUAGES,
        })
        return base


async def _get_async_session():
    from app.db.base import async_session_maker
    return async_session_maker()
