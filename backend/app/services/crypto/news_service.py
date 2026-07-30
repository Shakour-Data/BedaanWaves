"""
Crypto News Service - Tier 8 Complete Implementation
"""
import aiohttp
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ..data.crypto_api_client import CryptoApiClient
from ..nlp.sentiment_analysis_service import SentimentAnalysisService

class CryptoNewsService(CachedService):
    def __init__(self, service_name: str = "CryptoNewsService", cache_ttl_seconds: int = 300):
        super().__init__(service_name, cache_ttl_seconds=cache_ttl_seconds)
        self.crypto_client = CryptoApiClient()
        self.sentiment_analyzer = SentimentAnalysisService()
        # Define categories and keywords
        self.category_keywords = {
            "DeFi": ["defi", "decentralized finance", "lending", "staking", "yields", "liquidity"],
            "NFT": ["nft", "non-fungible", "collection", "art", "meta", "metaverse"],
            "Layer1": ["layer 1", "layer one", "mainnet", "scalability", "network"],
            "Exchange": ["exchange", "trading pair", "spot", "margin"],
        }

    async def _fetch_crypto_news(self) -> List[Dict[str, Any]]:
        """Fetch crypto news from multiple sources."""
        news = []
        sources = [
            {"name": "CoinGecko", "url": "https://api.coingecko.com/api/v3/news"},
            {"name": "CryptoPanic", "url": "https://api.cryptopanic.com/v1/posts"},
            {"name": "CoinDesk", "url": "https://api.coindesk.com/api/v1/articles"},
        ]
        for source in sources:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(source['url'], headers={"User-Agent": "Mozilla/5.0"}) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            for item in data.get('articles') or data.get('posts') or []:
                                article = {
                                    "title": item.get("title", ""),
                                    "summary": item.get("summary", ""),
                                    "content": item.get("content", ""),
                                    "source": source['name'],
                                    "url": item.get("url", ""),
                                    "published_at": datetime.fromisoformat(item.get("published_at", datetime.now(timezone.utc).isoformat())),
                                    "asset": item.get("symbol", ""),
                                    "tags": [t.lower() for t in (item.get("tags", []) + item.get("topics", []))],
                                    "image_url": item.get("image", ""),
                                }
                                news.append(article)
                        else:
                            self.logger.warning(f"Failed to fetch from {source['name']}: HTTP {resp.status}")
            except Exception as e:
                self.logger.warning(f"Error fetching from {source['name']}: {str(e)}")
        return news

    async def _categorize_article(self, article: Dict[str, Any]) -> List[str]:
        """Categorize article based on keywords."""
        categories = []
        text = " ".join([article.get('summary', '')])
        for cat, keywords in self.category_keywords.items():
            if any(kw in text.lower() for kw in keywords):
                categories.append(cat)
        return categories

    async def _analyze_sentiment(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze sentiment of article using sentiment analysis service."""
        try:
            sentiment = await self.sentiment_analyzer.analyze({
                "text": f"{article.get('title', '')} {article.get('summary', '')}",
                "symbol": article.get("asset")
            })
            return {
                **article,
                "sentiment": sentiment["label"],
                "sentiment_score": sentiment["confidence"],
                "sentiment_breakdown": sentiment["scores"]
            }
        except Exception as e:
            self.logger.error(f"Sentiment analysis failed: {str(e)}")
            return article

    async def get_crypto_news(self, symbol: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Get filtered crypto news with sentiment analysis."""
        raw_news = await self._fetch_crypto_news()
        filtered_news = [
            article for article in raw_news
            if symbol is None or symbol.upper() in (article.get('asset') or article.get('title') or '')
        ]
        # Process each article for sentiment and categories
        tasks = [self._analyze_sentiment(article) for article in filtered_news]
        processed_news = await asyncio.gather(*tasks)
        for article in processed_news:
            article["categories"] = await self._categorize_article(article)
        processed_news.sort(key=lambda x: x["published_at"], reverse=True)
        return processed_news[:limit]

    async def search_news(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search crypto news articles by query."""
        filtered = await self.get_crypto_news(limit=limit*2)
        results = [
            article for article in filtered 
            if query.lower() in (article.get('title', '') + article.get('summary', '')).lower()
        ][:limit]
        return results

    async def get_trending_topics(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get trending cryptocurrency topics."""
        news = await self.get_crypto_news()
        topic_counts = {}
        for article in news:
            for tag in article.get('tags', []):
                tag_lower = tag.lower()
                topic_counts[tag_lower] = topic_counts.get(tag_lower, 0) + 1
        topics = [
            {"topic": tag, "count": count, "category": next((c for c, kw in self.category_keywords.items() if tag in kw), "general")}
            for tag, count in topic_counts.items()
        ]
        topics.sort(key=lambda x: x["count"], reverse=True)
        return topics[:limit]

    async def get_sentiment_summary(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """Get aggregated sentiment summary for a symbol."""
        news = await self.get_crypto_news(symbol=symbol, limit=100)
        if not news:
            return {
                "symbol": symbol or "all",
                "total_articles": 0,
                "sentiment_distribution": {"positive": 0, "neutral": 0, "negative": 0},
                "categories": {}, 
            }
        distribution = {"positive": 0, "neutral": 0, "negative": 0}
        for article in news:
            label = article.get("sentiment", "neutral")
            distribution[label] += 1
        return {
            "symbol": symbol or "all",
            "total_articles": len(news),
            "sentiment_distribution": distribution,
            "articles": news[:10]  # Sample of recent articles
        }

    async def get_breaking_news_alerts(self, time_window: int = 300) -> List[Dict[str, Any]]:
        """Get alerts for breaking news within time window (seconds)."""
        now = datetime.now(timezone.utc)
        recent_news = await self.get_crypto_news(limit=200)
        alerts = [
            article for article in recent_news
            if (now - article.get("published_at")).total_seconds() <= time_window
        ]
        for article in alerts:
            article["is_breaking"] = article.get("sentiment_score", 0) > 0.8 or len(article.get("categories", [])) > 1
        return alerts

    async def health_check(self) -> Dict[str, Any]:
        """Health check for crypto news service."""
        return {
            "service": self.service_name,
            "status": "healthy",
            "cache_size": len(self._cache),
            "last_update": datetime.now(timezone.utc).isoformat(),
        }