"""
Base API Client Interface - Unified Market Access Layer

This module provides a unified interface for accessing different market data sources
(Tehran Stock Exchange, Nasdaq, other international exchanges, forex)
through a consistent API pattern.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import logging
from datetime import datetime, timezone

from ..core import ExternalAPIService
from app.core.config import get_settings


class MarketType:
    """Market type constants for unified access"""
    TEHRAN = "tehran"
    NASDAQ = "nasdaq"
    NYSE = "nyse"
    OTHER_COUNTRIES = "other_countries"
    FOREX = "forex"
    SUPPORTED = [TEHRAN, NASDAQ, NYSE, OTHER_COUNTRIES, FOREX]


class ApiClient(ABC):
    """
    Abstract base class for market data API clients.

    Provides unified interface for stock, index, and market data across different
    exchanges while abstracting away the specific API implementation details.
    """

    def __init__(
        self,
        market_type: str,
        service_name: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
    ):
        """
        Initialize API client for specific market type.

        Args:
            market_type: Type of market (TEHRAN, NASDAQ, etc.)
            service_name: Optional service name
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.market_type = market_type
        self.service_name = service_name or f"{market_type.title()}ApiClient"
        self.timeout = timeout
        self.max_retries = max_retries
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        self.last_error = None
        self.call_count = 0

    @abstractmethod
    async def get_stock(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """
        Get stock information for a specific symbol.

        Args:
            symbol: Stock ticker symbol
            **kwargs: Additional parameters specific to the market

        Returns:
            Dictionary containing stock information
        """
        pass

    @abstractmethod
    async def get_index(self, index_code: str, **kwargs) -> Dict[str, Any]:
        """
        Get index information for a specific index code.

        Args:
            index_code: Index identifier
            **kwargs: Additional parameters specific to the market

        Returns:
            Dictionary containing index information
        """
        pass

    @abstractmethod
    async def get_market_stats(self, **kwargs) -> Dict[str, Any]:
        """
        Get overall market statistics.

        Args:
            **kwargs: Additional parameters specific to the market

        Returns:
            Dictionary containing market statistics
        """
        pass

    async def get_multiple_stocks(self, symbols: List[str], **kwargs) -> Dict[str, Dict[str, Any]]:
        """
        Get stock information for multiple symbols concurrently.

        Args:
            symbols: List of stock ticker symbols
            **kwargs: Additional parameters

        Returns:
            Dictionary mapping symbols to their data
        """
        tasks = [self.get_stock(symbol, **kwargs) for symbol in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        stock_data = {}
        for symbol, result in zip(symbols, results):
            if isinstance(result, Exception):
                self.logger.error(f"Error fetching stock {symbol}: {result}")
                stock_data[symbol] = {"error": str(result)}
            else:
                stock_data[symbol] = result

        return stock_data

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on the API client.

        Returns:
            Dictionary with health status information
        """
        return {
            "market_type": self.market_type,
            "service_name": self.service_name,
            "status": "healthy" if self.call_count > 0 else "uninitialized",
            "last_error": self.last_error,
            "call_count": self.call_count,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


class TehranApiClient(ApiClient):
    """
    Tehran Stock Exchange (BRS) API client.

    Provides real-time and historical market data for Tehran Stock Exchange.
    """

    def __init__(self, service_name: str = "TehranApiClient", **kwargs):
        super().__init__(MarketType.TEHRAN, service_name, **kwargs)
        self.base_url = "https://Api.BrsApi.ir"
        self.api_key = kwargs.get("api_key")
        self.session = None

    async def initialize(self) -> None:
        """Initialize the HTTP session."""
        import aiohttp

        self.session = aiohttp.ClientSession()
        self.logger.info("TehranApiClient initialized")

    async def shutdown(self) -> None:
        """Close the HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()
        self.logger.info("TehranApiClient shutdown")

    async def get_stock(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """
        Get stock information for Tehran Stock Exchange symbol.

        Args:
            symbol: Persian ticker symbol (e.g., "فملی", "خودرو")

        Returns:
            Stock information with OHLC, volume, etc.
        """
        if not self.session:
            raise RuntimeError("TehranApiClient not initialized")

        self.call_count += 1
        try:
            # Import here to avoid circular imports
            from .brs_api_client import BrsApiClient

            # Create BRS client instance with rate limiting
            settings = get_settings()

            brs_client = BrsApiClient(
                service_name=f"BRS_{symbol}",
                base_url=self.base_url,
                api_key=self.api_key,
                timeout=self.timeout,
                max_retries=self.max_retries,
            )

            # Initialize the BRS client session
            await brs_client.initialize()

            # Get stock info
            result = await brs_client.get_stock_info(symbol)

            # Cleanup
            await brs_client.shutdown()

            return result

        except Exception as e:
            self.last_error = str(e)
            self.logger.error(f"Error getting stock {symbol} from Tehran: {e}")
            raise

    async def get_index(self, index_code: str, **kwargs) -> Dict[str, Any]:
        """
        Get index information from Tehran Stock Exchange.

        Args:
            index_code: Index type (1=Total, 2=Fara Bours, etc.)

        Returns:
            Index data
        """
        if not self.session:
            raise RuntimeError("TehranApiClient not initialized")

        self.call_count += 1
        try:
            # Import here to avoid circular imports
            from .brs_api_client import BrsApiClient

            brs_client = BrsApiClient(
                service_name=f"BRS_Index_{index_code}",
                base_url=self.base_url,
                api_key=self.api_key,
                timeout=self.timeout,
                max_retries=self.max_retries,
            )

            await brs_client.initialize()
            result = await brs_client.get_index(index_type=int(index_code))
            await brs_client.shutdown()

            return result

        except Exception as e:
            self.last_error = str(e)
            self.logger.error(f"Error getting index {index_code} from Tehran: {e}")
            raise

    async def get_market_stats(self, **kwargs) -> Dict[str, Any]:
        """
        Get market statistics from Tehran Stock Exchange.

        Returns:
            Market statistics including top gainers, losers, volume
        """
        if not self.session:
            raise RuntimeError("TehranApiClient not initialized")

        self.call_count += 1
        try:
            # Import here to avoid circular imports
            from .brs_api_client import BrsApiClient

            brs_client = BrsApiClient(
                service_name="BRS_MarketStats",
                base_url=self.base_url,
                api_key=self.api_key,
                timeout=self.timeout,
                max_retries=self.max_retries,
            )

            await brs_client.initialize()
            result = await brs_client.get_market_stats()
            await brs_client.shutdown()

            return result

        except Exception as e:
            self.last_error = str(e)
            self.logger.error(f"Error getting market stats from Tehran: {e}")
            raise


class NasdaqApiClient(ApiClient):
    """
    Nasdaq Stock Market API client.

    Provides real-time and historical market data for Nasdaq stocks using
    yfinance library for reliable data access.
    """

    def __init__(self, service_name: str = "NasdaqApiClient", **kwargs):
        super().__init__(MarketType.NASDAQ, service_name, **kwargs)
        self.session = None
        import yfinance as yf

        self.yf = yf

    async def initialize(self) -> None:
        """Initialize the client."""
        self.logger.info("NasdaqApiClient initialized")

    async def shutdown(self) -> None:
        """Shutdown the client."""
        self.logger.info("NasdaqApiClient shutdown")

    async def get_stock(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """
        Get stock information for Nasdaq symbol.

        Args:
            symbol: Nasdaq ticker symbol (e.g., "AAPL", "MSFT", "GOOGL")

        Returns:
            Stock information with OHLC, volume, technical indicators
        """
        self.call_count += 1
        try:
            # Fetch data using yfinance
            ticker = self.yf.Ticker(symbol)

            # Get basic stock info
            info = ticker.info

            # Get historical data (last 5 days for demo, can be adjusted)
            hist = ticker.history(period="5d", interval="1d")

            # Format the result
            result = {
                "symbol": symbol,
                "market_type": MarketType.NASDAQ,
                "info": info,
                "history": hist.to_dict("records") if not hist.empty else [],
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "metadata": {
                    "source": "yfinance",
                    "exchange": "NASDAQ",
                    "timezone": "UTC",
                }
            }

            return result

        except Exception as e:
            self.last_error = str(e)
            self.logger.error(f"Error getting stock {symbol} from Nasdaq: {e}")
            raise

    async def get_index(self, index_code: str, **kwargs) -> Dict[str, Any]:
        """
        Get index information for Nasdaq indices.

        Args:
            index_code: Index code (e.g., "^IXIC" for NASDAQ Composite)

        Returns:
            Index data with current value, change, etc.
        """
        self.call_count += 1
        try:
            # Map common Nasdaq index codes
            index_mapping = {
                "^IXIC": "NASDAQ Composite",
                "^GSPC": "S&P 500",
                "^DJI": "Dow Jones",
                "^RUT": "Russell 2000",
                "^NDX": "NASDAQ 100",
                "^NQC": "NASDAQ Composite",
            }

            display_name = index_mapping.get(index_code, index_code)

            # Fetch index data using yfinance
            ticker = self.yf.Ticker(index_code)
            info = ticker.info

            # Get historical data
            hist = ticker.history(period="5d", interval="1d")

            result = {
                "symbol": index_code,
                "market_type": MarketType.NASDAQ,
                "name": display_name,
                "info": info,
                "history": hist.to_dict("records") if not hist.empty else [],
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "metadata": {
                    "source": "yfinance",
                    "exchange": "NASDAQ",
                    "index": True,
                    "timezone": "UTC",
                }
            }

            return result

        except Exception as e:
            self.last_error = str(e)
            self.logger.error(f"Error getting index {index_code} from Nasdaq: {e}")
            raise

    async def get_market_stats(self, **kwargs) -> Dict[str, Any]:
        """
        Get Nasdaq market statistics.

        Returns:
            Market statistics including indices, gainers, losers
        """
        self.call_count += 1
        try:
            # Get major indices
            indices = [
                "^IXIC",  # NASDAQ Composite
                "^NDX",   # NASDAQ 100
                "^GSPC",  # S&P 500
                "^DJI",   # Dow Jones
                "^RUT",   # Russell 2000
            ]

            # Fetch data for all indices
            index_data = {}
            for index_code in indices:
                ticker = self.yf.Ticker(index_code)
                info = ticker.info
                hist = ticker.history(period="1d", interval="1m")

                index_data[index_code] = {
                    "name": info.get("shortName", index_code),
                    "price": info.get("regularMarketPrice", info.get("previousClose", 0)),
                    "change": info.get("regularMarketChangePercent", 0),
                    "volume": info.get("regularMarketVolume", 0),
                    "high": info.get("dayHigh", 0),
                    "low": info.get("dayLow", 0),
                    "history": hist.to_dict("records") if not hist.empty else [],
                }

            # Get market summary
            result = {
                "market_type": MarketType.NASDAQ,
                "market_name": "NASDAQ Stock Market",
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "indices": index_data,
                "metadata": {
                    "source": "yfinance",
                    "exchange": "NASDAQ",
                    "timezone": "UTC",
                }
            }

            return result

        except Exception as e:
            self.last_error = str(e)
            self.logger.error(f"Error getting market stats from Nasdaq: {e}")
            raise


class MarketClientFactory:
    """
    Factory for creating market-specific API clients.

    Provides a unified interface for accessing different market data sources
    based on market type configuration.
    """

    def __init__(self):
        self._clients = {}
        self._lock = asyncio.Lock()

    async def get_client(self, market_type: str, **kwargs) -> ApiClient:
        """
        Get or create a market-specific API client.

        Args:
            market_type: Type of market
            **kwargs: Additional parameters for client creation

        Returns:
            Market-specific API client instance
        """
        if market_type not in MarketType.SUPPORTED:
            raise ValueError(f"Unsupported market type: {market_type}")

        async with self._lock:
            if market_type not in self._clients:
                self._clients[market_type] = await self._create_client(market_type, **kwargs)

            return self._clients[market_type]

    async def _create_client(self, market_type: str, **kwargs) -> ApiClient:
        """
        Create a new market-specific API client.

        Args:
            market_type: Type of market
            **kwargs: Additional parameters for client creation

        Returns:
            Market-specific API client instance
        """
        # Get settings
        settings = get_settings()

        # Common initialization parameters
        init_kwargs = {
            "timeout": getattr(settings, "API_TIMEOUT", 30),
            "max_retries": getattr(settings, "API_MAX_RETRIES", 3),
            **kwargs
        }

        # Create market-specific client
        if market_type == MarketType.TEHRAN:
            return TehranApiClient(**init_kwargs)
        elif market_type == MarketType.NASDAQ:
            return NasdaqApiClient(**init_kwargs)
        else:
            # For other markets, return a generic client
            return ApiClient(market_type=market_type, **init_kwargs)

    async def get_all_clients(self, **kwargs) -> Dict[str, ApiClient]:
        """
        Get all configured market clients.

        Args:
            **kwargs: Additional parameters for client creation

        Returns:
            Dictionary mapping market types to client instances
        """
        clients = {}

        for market_type in MarketType.SUPPORTED:
            try:
                clients[market_type] = await self.get_client(market_type, **kwargs)
            except Exception as e:
                logging.getLogger(__name__).warning(
                    f"Failed to create client for {market_type}: {e}"
                )

        return clients

    async def initialize_all(self) -> None:
        """Initialize all market clients."""
        clients = await self.get_all_clients()
        for client in clients.values():
            try:
                if hasattr(client, "initialize"):
                    await client.initialize()
            except Exception as e:
                logging.getLogger(__name__).error(
                    f"Failed to initialize {client.service_name}: {e}"
                )

    async def shutdown_all(self) -> None:
        """Shutdown all market clients."""
        clients = await self.get_all_clients()
        for client in clients.values():
            try:
                if hasattr(client, "shutdown"):
                    await client.shutdown()
            except Exception as e:
                logging.getLogger(__name__).error(
                    f"Failed to shutdown {client.service_name}: {e}"
                )


# Global factory instance
_market_factory = None


def get_market_factory() -> MarketClientFactory:
    """Get the global market client factory instance."""
    global _market_factory
    if _market_factory is None:
        _market_factory = MarketClientFactory()
    return _market_factory


async def get_market_client(market_type: str, **kwargs) -> ApiClient:
    """
    Convenience function to get a market client.

    Args:
        market_type: Type of market
        **kwargs: Additional parameters

    Returns:
        Market-specific API client instance
    """
    factory = get_market_factory()
    return await factory.get_client(market_type, **kwargs)
