"""
News Service - Tier 2 Data Service

News data retrieval and management from external APIs and database.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, desc
from app.db.base import async_session_maker
from app.models.models import News, Asset
from ..core import CachedService


class NewsService(CachedService):
    """
    News data management service.
    
    Provides:
    - News retrieval from external API client
    - News retrieval from database
    - News filtering by stock/market
    - News caching
    - Sentiment association
    """
    
    def __init__(
        self,
        service_name: str = "NewsService",
        news_client: Optional[Any] = None,
        cache_ttl_seconds: int = 1800,
    ):
        super().__init__(service_name, cache_ttl_seconds=cache_ttl_seconds)
        self.news_client = news_client
    
    async def initialize(self) -> None:
        self.logger.info("NewsService initialized")
    
    async def shutdown(self) -> None:
        self.cache_clear()
        self.logger.info("NewsService shutdown")
    
    async def get_market_news(self, limit: int = 20) -> List[Dict[str, Any]]:
        cache_key = f"market_news_{limit}"
        cached = self.get_cached(cache_key)
        if cached:
            return cached
        
        news = []
        if self.news_client:
            try:
                news = await self.news_client.get_market_news(limit=limit)
            except Exception as exc:
                self.logger.warning(f"External news client failed: {exc}")
        
        if not news:
            async with async_session_maker() as session:
                result = await session.execute(
                    select(News).order_by(desc(News.published_at)).limit(limit)
                )
                news_items = result.scalars().all()
                news = [self._news_to_dict(n) for n in news_items]
        
        self.set_cached(cache_key, news)
        return news
    
    async def get_stock_news(
        self,
        ticker: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        cache_key = f"stock_news:{ticker}:{limit}"
        cached = self.get_cached(cache_key)
        if cached:
            return cached
        
        news = []
        if self.news_client:
            try:
                news = await self.news_client.get_stock_news(ticker=ticker, limit=limit)
            except Exception as exc:
                self.logger.warning(f"External news client failed for {ticker}: {exc}")
        
        if not news:
            async with async_session_maker() as session:
                asset_result = await session.execute(
                    select(Asset).where(Asset.symbol == ticker.upper())
                )
                asset = asset_result.scalar_one_or_none()
                if asset:
                    result = await session.execute(
                        select(News)
                        .where(News.asset_id == asset.id)
                        .order_by(desc(News.published_at))
                        .limit(limit)
                    )
                    news_items = result.scalars().all()
                    news = [self._news_to_dict(n) for n in news_items]
        
        self.set_cached(cache_key, news)
        return news
    
    async def search_news(
        self,
        query: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        cache_key = f"news_search:{query}:{limit}"
        cached = self.get_cached(cache_key)
        if cached:
            return cached
        
        results = []
        if self.news_client:
            try:
                results = await self.news_client.search_news(query=query, limit=limit)
            except Exception as exc:
                self.logger.warning(f"External news search failed: {exc}")
        
        if not results:
            async with async_session_maker() as session:
                result = await session.execute(
                    select(News)
                    .where(News.title.ilike(f"%{query}%"))
                    .order_by(desc(News.published_at))
                    .limit(limit)
                )
                news_items = result.scalars().all()
                results = [self._news_to_dict(n) for n in news_items]
        
        self.set_cached(cache_key, results)
        return results
    
    async def get_related_news(
        self,
        content: str,
        tickers: List[str],
    ) -> List[Dict[str, Any]]:
        related = []
        seen_urls = set()
        
        for ticker in tickers:
            news = await self.get_stock_news(ticker, limit=10)
            for item in news:
                if item.get("url") not in seen_urls:
                    related.append(item)
                    seen_urls.add(item.get("url"))
        
        return related
    
    def _news_to_dict(self, news: News) -> Dict[str, Any]:
        return {
            "id": str(news.id),
            "source": news.source,
            "title": news.title,
            "body": news.body,
            "url": news.url,
            "published_at": news.published_at.isoformat() if news.published_at else None,
            "asset_id": str(news.asset_id) if news.asset_id else None,
            "language": news.language,
            "fetched_at": news.fetched_at.isoformat() if news.fetched_at else None,
        }
