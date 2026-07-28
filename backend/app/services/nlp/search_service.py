"""
Search Service - Tier 5 NLP Service

Full-text search across stocks, news, analysis, and platform content.
Supports Persian and English queries with relevance scoring.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from ..core import BaseService


class SearchService(BaseService):
    """
    Full-text search service for BedaanWaves platform.
    
    Capabilities:
    - Stock and symbol search
    - News article search
    - Analysis report search
    - Persian and English query support
    - Relevance scoring and ranking
    - Autocomplete suggestions
    """
    
    def __init__(self, service_name: str = "SearchService"):
        super().__init__(service_name)
        self._stock_index: Dict[str, Dict[str, Any]] = {}
        self._news_index: Dict[str, Dict[str, Any]] = {}
        self._max_results = 20
    
    async def initialize(self) -> None:
        """Initialize search service"""
        self._stock_index = {}
        self._news_index = {}
        self.logger.info("SearchService initialized")
    
    async def shutdown(self) -> None:
        """Shutdown search service"""
        self._stock_index.clear()
        self._news_index.clear()
        self.logger.info("SearchService shutdown")
    
    async def search(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform a search query.
        
        Args:
            data: Dictionary with 'query', optional 'type', 'limit', 'filters'
            
        Returns:
            Search results with relevance scoring
        """
        query = data.get("query", "")
        search_type = data.get("type", "all")
        limit = data.get("limit", self._max_results)
        filters = data.get("filters", {})
        
        if not query or len(query.strip()) < 2:
            return {
                "query": query,
                "results": [],
                "total": 0,
                "suggestions": [],
            }
        
        results = []
        
        if search_type in ["all", "stocks"]:
            stock_results = self._search_stocks(query, limit, filters)
            results.extend(stock_results)
        
        if search_type in ["all", "news"]:
            news_results = self._search_news(query, limit, filters)
            results.extend(news_results)
        
        results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        
        suggestions = self._get_suggestions(query, results)
        
        return {
            "query": query,
            "results": results[:limit],
            "total": len(results),
            "suggestions": suggestions,
            "search_type": search_type,
            "executed_at": datetime.now(timezone.utc).isoformat(),
        }
    
    def _search_stocks(self, query: str, limit: int, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search stocks by symbol or name"""
        results = []
        query_lower = query.lower()
        
        for symbol, stock_data in self._stock_index.items():
            score = 0.0
            
            if query_lower in symbol.lower():
                score += 10.0
                if symbol.lower().startswith(query_lower):
                    score += 5.0
            
            name = stock_data.get("name", "")
            if query_lower in name.lower():
                score += 8.0
            
            sector = stock_data.get("sector", "")
            if query_lower in sector.lower():
                score += 3.0
            
            if score > 0:
                results.append({
                    "type": "stock",
                    "symbol": symbol,
                    "name": name,
                    "market": stock_data.get("market"),
                    "sector": sector,
                    "relevance_score": score,
                    "data": stock_data,
                })
        
        return sorted(results, key=lambda x: x["relevance_score"], reverse=True)[:limit]
    
    def _search_news(self, query: str, limit: int, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search news articles"""
        results = []
        query_lower = query.lower()
        
        for news_id, news_data in self._news_index.items():
            score = 0.0
            
            title = news_data.get("title", "")
            if query_lower in title.lower():
                score += 10.0
            
            summary = news_data.get("summary", "")
            if query_lower in summary.lower():
                score += 5.0
            
            if score > 0:
                results.append({
                    "type": "news",
                    "id": news_id,
                    "title": title,
                    "summary": summary[:200],
                    "published_at": news_data.get("published_at"),
                    "relevance_score": score,
                    "data": news_data,
                })
        
        return sorted(results, key=lambda x: x["relevance_score"], reverse=True)[:limit]
    
    def _get_suggestions(self, query: str, results: List[Dict[str, Any]]) -> List[str]:
        """Get autocomplete suggestions based on query and results"""
        suggestions = set()
        query_lower = query.lower()
        
        for result in results[:5]:
            if result.get("type") == "stock":
                symbol = result.get("symbol", "")
                if symbol.lower().startswith(query_lower):
                    suggestions.add(symbol)
                name = result.get("name", "")
                if name.lower().startswith(query_lower):
                    suggestions.add(name)
        
        return list(suggestions)[:5]
    
    async def index_stock(self, symbol: str, stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Index a stock for search.
        
        Args:
            symbol: Stock symbol
            stock_data: Stock metadata
            
        Returns:
            Indexing status
        """
        self._stock_index[symbol] = {
            "symbol": symbol,
            "name": stock_data.get("name", ""),
            "market": stock_data.get("market"),
            "sector": stock_data.get("sector"),
            "indexed_at": datetime.now(timezone.utc).isoformat(),
        }
        return {"status": "indexed", "symbol": symbol}
    
    async def index_news(self, news_id: str, news_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Index a news article for search.
        
        Args:
            news_id: News identifier
            news_data: News content and metadata
            
        Returns:
            Indexing status
        """
        self._news_index[news_id] = {
            "title": news_data.get("title", ""),
            "summary": news_data.get("summary", ""),
            "published_at": news_data.get("published_at"),
            "indexed_at": datetime.now(timezone.utc).isoformat(),
        }
        return {"status": "indexed", "news_id": news_id}
    
    async def remove_stock(self, symbol: str) -> Dict[str, Any]:
        """Remove stock from search index"""
        self._stock_index.pop(symbol, None)
        return {"status": "removed", "symbol": symbol}
    
    async def remove_news(self, news_id: str) -> Dict[str, Any]:
        """Remove news from search index"""
        self._news_index.pop(news_id, None)
        return {"status": "removed", "news_id": news_id}
    
    async def get_suggestions(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """
        Get autocomplete suggestions for a query.
        
        Args:
            query: Search query prefix
            limit: Maximum suggestions
            
        Returns:
            List of suggestions
        """
        if not query or len(query.strip()) < 1:
            return {"query": query, "suggestions": []}
        
        results = await self.search({
            "query": query,
            "limit": limit,
        })
        
        return {
            "query": query,
            "suggestions": results.get("suggestions", []),
            "total": len(results.get("suggestions", [])),
        }
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get search index statistics"""
        return {
            "stocks_indexed": len(self._stock_index),
            "news_indexed": len(self._news_index),
            "total_indexed": len(self._stock_index) + len(self._news_index),
            "max_results": self._max_results,
        }
