"""
Stock Service - Tier 2 Data Service

Manages stock data and operations using live external APIs (yfinance).
No hardcoded data. No fallback to static arrays.
"""

from typing import Any, Dict, Optional, List
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor

from app.core.config import get_settings
from app.core.exceptions import DataProviderException
from ..core import CachedService

settings = get_settings()
_EXECUTOR = ThreadPoolExecutor(max_workers=8)


class StockService(CachedService):
    """
    Stock data management service using yfinance.
    
    Provides:
    - Stock information retrieval
    - Price data management
    - Stock search via yfinance suggestions
    - Batch stock operations
    """
    
    def __init__(
        self,
        service_name: str = "StockService",
        brs_client=None,
        cache_ttl_seconds: int = 3600,
    ):
        super().__init__(service_name, cache_ttl_seconds=cache_ttl_seconds)
        self.brs_client = brs_client
    
    async def initialize(self) -> None:
        """Initialize stock service"""
        self.logger.info("StockService initialized (yfinance provider)")
    
    async def shutdown(self) -> None:
        """Shutdown stock service"""
        self.cache_clear()
        self.logger.info("StockService shutdown")
    
    async def _run_blocking(self, func, *args, **kwargs):
        loop = __import__("asyncio").get_event_loop()
        return await loop.run_in_executor(_EXECUTOR, lambda: func(*args, **kwargs))

    def _fetch_yfinance_search(self, query: str) -> List[Dict[str, Any]]:
        """Blocking call to yfinance for symbol suggestions."""
        import yfinance as yf
        try:
            tickers = yf.Ticker(query).symbols if hasattr(yf.Ticker(query), "symbols") else []
        except Exception:
            tickers = []

        if not tickers:
            try:
                import requests
                url = "https://query1.finance.yahoo.com/v1/finance/search"
                params = {"q": query, "quotesCount": 10, "newsCount": 0}
                headers = {"User-Agent": "Mozilla/5.0"}
                resp = requests.get(url, params=params, headers=headers, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    tickers = [q.get("symbol") for q in data.get("quotes", []) if q.get("symbol")]
            except Exception:
                tickers = []

        results = []
        for symbol in tickers[:20]:
            try:
                info = yf.Ticker(symbol).info or {}
                name = info.get("shortName") or info.get("longName") or symbol
                exchange = info.get("exchange") or ""
                results.append({
                    "symbol": symbol,
                    "name": name,
                    "exchange": exchange,
                    "type": "EQUITY",
                    "active": True,
                })
            except Exception:
                results.append({
                    "symbol": symbol,
                    "name": symbol,
                    "exchange": "",
                    "type": "EQUITY",
                    "active": True,
                })
        return results

    async def search(self, query: str) -> List[Dict[str, Any]]:
        """
        Search stocks using yfinance live suggestions.
        
        Args:
            query: Search query
            
        Returns:
            Search results from live API
        """
        cache_key = f"search:{query}"
        cached = self.get_cached(cache_key)
        if cached:
            return cached
        
        results = await self._run_blocking(self._fetch_yfinance_search, query)
        self.set_cached(cache_key, results, ttl_seconds=300)
        return results
    
    async def get_stock(self, ticker: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        Get stock information from yfinance.
        
        Args:
            ticker: Stock ticker
            
        Returns:
            Stock information from live API
        """
        cache_key = f"stock:{ticker}"
        
        if use_cache:
            cached = self.get_cached(cache_key)
            if cached:
                return cached
        
        def fetch():
            import yfinance as yf
            t = yf.Ticker(ticker)
            info = t.info or {}
            if not info:
                raise DataProviderException(f"No data returned for {ticker}", details={"provider": "yfinance"})
            price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose")
            previous_close = info.get("regularMarketPreviousClose") or info.get("previousClose")
            change = None
            change_percent = None
            if isinstance(price, (int, float)) and isinstance(previous_close, (int, float)) and previous_close:
                change = round(price - previous_close, 4)
                change_percent = round((change / previous_close) * 100, 4)
            return {
                "symbol": ticker.upper(),
                "name": info.get("shortName") or info.get("longName") or ticker,
                "sector": info.get("sector") or "",
                "industry": info.get("industry") or "",
                "exchange": info.get("exchange") or "",
                "currency": info.get("currency") or "USD",
                "market_cap": info.get("marketCap"),
                "pe_ratio": info.get("trailingPE"),
                "price": price,
                "previous_close": previous_close,
                "change": change,
                "change_percent": change_percent,
                "volume": info.get("volume") or info.get("regularMarketVolume"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        
        stock_data = await self._run_blocking(fetch)
        self.set_cached(cache_key, stock_data, ttl_seconds=30)
        return stock_data
    
    async def get_price(self, ticker: str) -> Dict[str, float]:
        """
        Get current stock price from yfinance.
        
        Args:
            ticker: Stock ticker
            
        Returns:
            Price data from live API
        """
        def fetch():
            import yfinance as yf
            t = yf.Ticker(ticker)
            info = t.info or {}
            current = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose")
            if current is None:
                raise DataProviderException(f"No price for {ticker}", details={"provider": "yfinance"})
            return {
                "open": info.get("open") or info.get("regularMarketOpen") or current,
                "high": info.get("dayHigh") or info.get("regularMarketDayHigh") or current,
                "low": info.get("dayLow") or info.get("regularMarketDayLow") or current,
                "close": current,
                "last": current,
            }
        
        return await self._run_blocking(fetch)
    
    async def get_history(
        self,
        ticker: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        interval: str = "daily",
    ) -> List[Dict[str, Any]]:
        """
        Get historical stock data from yfinance.
        
        Args:
            ticker: Stock ticker
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            interval: Data interval
            
        Returns:
            Historical data from live API
        """
        cache_key = f"history:{ticker}:{start_date}:{end_date}:{interval}"
        cached = self.get_cached(cache_key)
        if cached:
            return cached
        
        def fetch():
            import yfinance as yf
            t = yf.Ticker(ticker)
            end = end_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
            start = start_date or (datetime.now(timezone.utc) - __import__("datetime").timedelta(days=365)).strftime("%Y-%m-%d")
            hist = t.history(start=start, end=end, interval=interval, auto_adjust=False)
            if hist.empty:
                raise DataProviderException(f"No history for {ticker}", details={"provider": "yfinance"})
            records = []
            for ts, row in hist.iterrows():
                records.append({
                    "timestamp": ts.isoformat(),
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "adjusted_close": float(row.get("Adj Close", row["Close"])),
                    "volume": int(row["Volume"]),
                })
            return records
        
        history = await self._run_blocking(fetch)
        self.set_cached(cache_key, history, ttl_seconds=3600)
        return history
    
    async def get_multiple(self, tickers: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Get multiple stocks from yfinance.
        
        Args:
            tickers: List of stock tickers
            
        Returns:
            Dictionary of {ticker: stock_data} from live API
        """
        results = {}
        for ticker in tickers:
            try:
                results[ticker] = await self.get_stock(ticker)
            except Exception as e:
                self.logger.error(f"Error getting stock {ticker}: {e}")
                results[ticker] = {"error": str(e)}
        
        return results
