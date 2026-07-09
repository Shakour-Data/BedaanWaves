"""
BRS API Client - Tier 2 Data Service

Integration with Tehran Stock Exchange (بورس اوراق بهادار تهران - BRS) API.
Handles stock data, market data, and trading information.
"""

from typing import Any, Dict, Optional, List
from datetime import datetime
import aiohttp
from ..core import ExternalAPIService


class BrsApiClient(ExternalAPIService):
    """
    Tehran Stock Exchange (BRS) API client.
    
    Provides:
    - Stock data retrieval
    - Market indices
    - Trading volumes
    - Company information
    - Historical data
    """
    
    def __init__(
        self,
        service_name: str = "BrsApiClient",
        base_url: str = "https://api.brs.ir",
        api_key: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
    ):
        """
        Initialize BRS API client.
        
        Args:
            service_name: Service identifier
            base_url: BRS API base URL
            api_key: Optional API key for authentication
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
        """
        super().__init__(
            service_name=service_name,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
        )
        self.api_key = api_key
        self.session = None
    
    async def initialize(self) -> None:
        """Initialize API client"""
        self.session = aiohttp.ClientSession()
        self.logger.info("BrsApiClient initialized")
    
    async def shutdown(self) -> None:
        """Shutdown API client"""
        if self.session:
            await self.session.close()
        self.logger.info("BrsApiClient shutdown")
    
    async def fetch(
        self,
        endpoint: str,
        method: str = "GET",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Fetch from BRS API.
        
        Args:
            endpoint: API endpoint
            method: HTTP method
            **kwargs: Additional request parameters
            
        Returns:
            API response
        """
        if not self.session:
            raise RuntimeError("API client not initialized")
        
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()
        
        for attempt in range(self.max_retries):
            try:
                async with self.session.request(
                    method,
                    url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                    **kwargs
                ) as response:
                    if response.status == 429:  # Rate limit
                        await self._handle_rate_limit(attempt)
                        continue
                    
                    data = await response.json()
                    
                    if response.status == 200:
                        return data
                    else:
                        raise Exception(f"API error: {response.status} - {data}")
            
            except Exception as e:
                if attempt < self.max_retries - 1:
                    self.logger.warning(f"Retry {attempt + 1}/{self.max_retries}: {e}")
                    await self._handle_rate_limit(attempt)
                else:
                    self.logger.error(f"API request failed after {self.max_retries} attempts: {e}")
                    raise
        
        raise Exception("Max retries exceeded")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers"""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "BedaanWaves/1.0",
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        return headers
    
    # Stock data endpoints
    
    async def get_stock_info(self, ticker: str) -> Dict[str, Any]:
        """
        Get stock information.
        
        Args:
            ticker: Stock ticker/symbol
            
        Returns:
            Stock information
        """
        return await self.fetch(f"/stocks/{ticker}")
    
    async def get_stock_price(self, ticker: str) -> Dict[str, Any]:
        """
        Get current stock price.
        
        Args:
            ticker: Stock ticker/symbol
            
        Returns:
            Price data including last, open, high, low
        """
        return await self.fetch(f"/stocks/{ticker}/price")
    
    async def get_stock_history(
        self,
        ticker: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        interval: str = "daily",
    ) -> List[Dict[str, Any]]:
        """
        Get historical stock data.
        
        Args:
            ticker: Stock ticker/symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            interval: Data interval (daily, weekly, monthly)
            
        Returns:
            Historical price data
        """
        params = {"interval": interval}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        
        response = await self.fetch(f"/stocks/{ticker}/history", params=params)
        return response.get("data", [])
    
    async def get_stock_volume(self, ticker: str) -> Dict[str, Any]:
        """
        Get stock trading volume.
        
        Args:
            ticker: Stock ticker/symbol
            
        Returns:
            Volume information
        """
        return await self.fetch(f"/stocks/{ticker}/volume")
    
    # Market endpoints
    
    async def get_market_indices(self) -> List[Dict[str, Any]]:
        """Get main market indices"""
        response = await self.fetch("/market/indices")
        return response.get("indices", [])
    
    async def get_market_stats(self) -> Dict[str, Any]:
        """Get overall market statistics"""
        return await self.fetch("/market/stats")
    
    async def get_top_gainers(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top gainers"""
        response = await self.fetch(f"/market/gainers?limit={limit}")
        return response.get("stocks", [])
    
    async def get_top_losers(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top losers"""
        response = await self.fetch(f"/market/losers?limit={limit}")
        return response.get("stocks", [])
    
    async def get_most_active(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most actively traded stocks"""
        response = await self.fetch(f"/market/most-active?limit={limit}")
        return response.get("stocks", [])
    
    # Company data endpoints
    
    async def get_company_info(self, ticker: str) -> Dict[str, Any]:
        """Get company information"""
        return await self.fetch(f"/companies/{ticker}")
    
    async def get_company_financials(self, ticker: str) -> Dict[str, Any]:
        """Get company financial data"""
        return await self.fetch(f"/companies/{ticker}/financials")
    
    async def search_stocks(self, query: str) -> List[Dict[str, Any]]:
        """
        Search stocks by name or ticker.
        
        Args:
            query: Search query
            
        Returns:
            Matching stocks
        """
        response = await self.fetch(f"/search?q={query}")
        return response.get("results", [])
