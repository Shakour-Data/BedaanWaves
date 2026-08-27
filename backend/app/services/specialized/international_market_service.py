"""
International Market Service - Tier 7 Specialized Service

Provides multi-country market data integration, comparison, and analysis.
Enables users to analyze and compare markets across different countries.
"""

from typing import Dict, List, Optional, Any
from datetime import timezone, datetime, date
import asyncio
from app.services.core.base_service import BaseService
from app.services.data.intl_api_client import IntlApiClient
from app.services.data.market_service import MarketService
import logging

class InternationalMarketService(BaseService):
    """
    International Market Service.
    
    Handles:
    - Multi-country market data retrieval
    - Cross-market comparison
    - Currency conversion
    - Regional market analysis
    - Global market indices tracking
    """
    
    def __init__(self,
                 service_name: str = "InternationalMarketService",
                 intl_client: Optional[IntlApiClient] = None,
                 market_service: Optional[MarketService] = None,
                 logger: Optional[logging.Logger] = None):
        """
        Initialize international market service.
        
        Args:
            service_name: Service identifier
            intl_client: International API client instance
            market_service: Market data service instance
            logger: Optional logger instance
        """
        super().__init__(service_name, logger=logger)
        self.intl_client = intl_client
        self.market_service = market_service
        
        # Country market configurations
        self.country_markets = {
            "USA": {
                "currency": "USD",
                "timezone": "America/New_York",
                "primary_exchange": "NYSE",
                "major_indices": ["SPX", "DJI", "IXIC", "RUT"],
                "trading_hours": {"open": "09:30", "close": "16:00"}
            },
            "UK": {
                "currency": "GBP",
                "timezone": "Europe/London",
                "primary_exchange": "LSE",
                "major_indices": ["FTSE", "FTSE250"],
                "trading_hours": {"open": "08:00", "close": "16:30"}
            },
            "Germany": {
                "currency": "EUR",
                "timezone": "Europe/Berlin",
                "primary_exchange": "XETRA",
                "major_indices": ["GDAXI", "MDX"],
                "trading_hours": {"open": "09:00", "close": "17:30"}
            },
            "France": {
                "currency": "EUR",
                "timezone": "Europe/Paris",
                "primary_exchange": "Euronext Paris",
                "major_indices": ["FCHI", "SBF120"],
                "trading_hours": {"open": "09:00", "close": "17:30"}
            },
            "Japan": {
                "currency": "JPY",
                "timezone": "Asia/Tokyo",
                "primary_exchange": "TSE",
                "major_indices": ["N225", "TOPX"],
                "trading_hours": {"open": "09:00", "close": "15:00"}
            },
            "China": {
                "currency": "CNY",
                "timezone": "Asia/Shanghai",
                "primary_exchange": "SSE",
                "major_indices": ["SSE", "SZSE", "CSI300"],
                "trading_hours": {"open": "09:30", "close": "15:00"}
            },
            "Korea": {
                "currency": "KRW",
                "timezone": "Asia/Seoul",
                "primary_exchange": "KRX",
                "major_indices": ["KS11", "KSQ11"],
                "trading_hours": {"open": "09:00", "close": "15:30"}
            },
            "India": {
                "currency": "INR",
                "timezone": "Asia/Kolkata",
                "primary_exchange": "NSE",
                "major_indices": ["NIFTY", "BSESN"],
                "trading_hours": {"open": "09:15", "close": "15:30"}
            },
            "Brazil": {
                "currency": "BRL",
                "timezone": "America/Sao_Paulo",
                "primary_exchange": "B3",
                "major_indices": ["BVSP"],
                "trading_hours": {"open": "10:00", "close": "17:00"}
            },
            "Canada": {
                "currency": "CAD",
                "timezone": "America/Toronto",
                "primary_exchange": "TSX",
                "major_indices": ["GSPTSE"],
                "trading_hours": {"open": "09:30", "close": "16:00"}
            },
            "Australia": {
                "currency": "AUD",
                "timezone": "Australia/Sydney",
                "primary_exchange": "ASX",
                "major_indices": ["AXJO"],
                "trading_hours": {"open": "10:00", "close": "16:00"}
            },
            "Russia": {
                "currency": "RUB",
                "timezone": "Europe/Moscow",
                "primary_exchange": "MOEX",
                "major_indices": ["IMOEX"],
                "trading_hours": {"open": "10:00", "close": "18:45"}
            },
            "Turkey": {
                "currency": "TRY",
                "timezone": "Europe/Istanbul",
                "primary_exchange": "BIST",
                "major_indices": ["XU100"],
                "trading_hours": {"open": "09:30", "close": "18:00"}
            },
            "Saudi Arabia": {
                "currency": "SAR",
                "timezone": "Asia/Riyadh",
                "primary_exchange": "Tadawul",
                "major_indices": ["TASI"],
                "trading_hours": {"open": "10:00", "close": "15:00"}
            },
            "UAE": {
                "currency": "AED",
                "timezone": "Asia/Dubai",
                "primary_exchange": "ADX",
                "major_indices": ["ADX", "DFM"],
                "trading_hours": {"open": "10:00", "close": "14:00"}
            }
        }
        
        # Regional groupings
        self.regions = {
            "North America": ["USA", "Canada"],
            "Europe": ["UK", "Germany", "France"],
            "Asia Pacific": ["Japan", "China", "Korea", "India", "Australia"],
            "Middle East": ["Saudi Arabia", "UAE", "Turkey"],
            "Latin America": ["Brazil"],
            "Emerging Markets": ["India", "Brazil", "Russia", "China", "Turkey", "Saudi Arabia"]
        }
    
    async def initialize(self) -> None:
        """Initialize international market service."""
        self.logger.info("Initializing InternationalMarketService")
        self.logger.info("InternationalMarketService initialized")
    
    async def shutdown(self) -> None:
        """Shutdown international market service."""
        self.logger.info("InternationalMarketService shutdown")
    
    async def get_available_countries(self) -> List[str]:
        """
        Get list of available countries.
        
        Returns:
            List of supported country names
        """
        return list(self.country_markets.keys())
    
    async def get_country_info(self, country: str) -> Dict[str, Any]:
        """
        Get information about a specific country's market.
        
        Args:
            country: Country name
            
        Returns:
            Country market information
        """
        return self.country_markets.get(country, {})
    
    async def get_regional_markets(self, region: str) -> List[Dict[str, Any]]:
        """
        Get market information for all countries in a region.
        
        Args:
            region: Region name
            
        Returns:
            List of country market information
        """
        countries = self.regions.get(region, [])
        return [await self.get_country_info(c) for c in countries]
    
    async def get_market_indices(self, country: str) -> List[str]:
        """
        Get major indices for a country.
        
        Args:
            country: Country name
            
        Returns:
            List of major index symbols
        """
        country_info = self.country_markets.get(country, {})
        return country_info.get("major_indices", [])
    
    async def get_global_market_snapshot(self) -> Dict[str, Any]:
        """
        Get global market snapshot across all supported countries.
        
        Returns:
            Dictionary mapping country to market data
        """
        snapshot = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "countries": {},
            "regions": {}
        }
        
        # Fetch data for each country (parallel)
        tasks = []
        for country in self.country_markets:
            tasks.append(self._fetch_country_snapshot(country))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, country in enumerate(self.country_markets):
            result = results[i]
            if isinstance(result, Exception):
                self.logger.error(f"Error fetching snapshot for {country}: {str(result)}")
                snapshot["countries"][country] = {"error": str(result)}
            else:
                snapshot["countries"][country] = result
        
        # Add regional summaries
        for region, countries in self.regions.items():
            snapshot["regions"][region] = await self._calculate_region_summary(countries, snapshot["countries"])
        
        return snapshot
    
    async def _fetch_country_snapshot(self, country: str) -> Dict[str, Any]:
        """
        Fetch market snapshot for a single country.
        
        Args:
            country: Country name
            
        Returns:
            Country market snapshot
        """
        if not self.intl_client:
            return {"status": "client_not_available"}
        
        try:
            indices = self.country_markets[country].get("major_indices", [])
            
            if not indices:
                return {"status": "no_indices"}
            
            # Fetch primary index
            primary_index = indices[0]
            index_data = await self.intl_client.get_index_data(primary_index)
            
            return {
                "currency": self.country_markets[country]["currency"],
                "primary_index": primary_index,
                "index_data": index_data,
                "trading_hours": self.country_markets[country]["trading_hours"],
                "status": "ok"
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def _calculate_region_summary(self, 
                                        countries: List[str],
                                        country_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate regional market summary.
        
        Args:
            countries: List of countries in region
            country_data: Dictionary of country snapshots
            
        Returns:
            Regional summary
        """
        changes = []
        for country in countries:
            data = country_data.get(country, {})
            index_data = data.get("index_data", {})
            change = index_data.get("change_percent")
            if change is not None:
                changes.append(change)
        
        if not changes:
            return {"count": 0, "avg_change": 0, "positive": 0, "negative": 0}
        
        avg_change = sum(changes) / len(changes)
        positive = sum(1 for c in changes if c > 0)
        negative = sum(1 for c in changes if c < 0)
        
        return {
            "count": len(changes),
            "avg_change": round(avg_change, 2),
            "positive": positive,
            "negative": negative,
            "best_performer": max(changes) if changes else 0,
            "worst_performer": min(changes) if changes else 0
        }
    
    async def compare_markets(self, 
                              countries: List[str],
                              metric: str = "change_percent") -> Dict[str, Any]:
        """
        Compare multiple markets on a specific metric.
        
        Args:
            countries: List of country names to compare
            metric: Metric to compare (change_percent, volume, etc.)
            
        Returns:
            Comparison results
        """
        comparison = {
            "metric": metric,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "countries": {}
        }
        
        tasks = [self._fetch_country_snapshot(c) for c in countries]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        values = {}
        for i, country in enumerate(countries):
            result = results[i]
            if isinstance(result, Exception):
                comparison["countries"][country] = {"error": str(result)}
            else:
                index_data = result.get("index_data", {})
                value = index_data.get(metric)
                if value is not None:
                    values[country] = value
                    comparison["countries"][country] = {
                        "value": value,
                        "currency": self.country_markets[country]["currency"]
                    }
        
        # Add rankings
        if values:
            sorted_countries = sorted(values.items(), key=lambda x: x[1], reverse=True)
            comparison["ranking"] = [
                {"country": c, "value": v, "rank": i + 1} 
                for i, (c, v) in enumerate(sorted_countries)
            ]
        
        return comparison
    
    async def get_currency_rates(self, 
                                 base_currency: str = "USD",
                                 target_currencies: List[str] = None) -> Dict[str, float]:
        """
        Get current currency exchange rates.
        
        Args:
            base_currency: Base currency code
            target_currencies: Target currency codes
            
        Returns:
            Dictionary mapping currency to exchange rate
        """
        if target_currencies is None:
            # Get all unique currencies from supported countries
            currencies = set()
            for country_info in self.country_markets.values():
                currencies.add(country_info["currency"])
            target_currencies = list(currencies)
        
        if not self.intl_client:
            return {c: 1.0 for c in target_currencies}
        
        try:
            return await self.intl_client.get_currency_rates(base_currency, target_currencies)
        except Exception as e:
            self.logger.error(f"Error fetching currency rates: {str(e)}")
            return {c: 1.0 for c in target_currencies}
    
    async def convert_currency(self,
                              amount: float,
                              from_currency: str,
                              to_currency: str) -> float:
        """
        Convert amount between currencies.
        
        Args:
            amount: Amount to convert
            from_currency: Source currency
            to_currency: Target currency
            
        Returns:
            Converted amount
        """
        rates = await self.get_currency_rates(from_currency, [to_currency])
        rate = rates.get(to_currency, 1.0)
        return amount * rate

# Factory function for dependency injection
def get_international_market_service(intl_client=None,
                                     market_service=None,
                                     logger=None) -> InternationalMarketService:
    """Factory function to create InternationalMarketService instance."""
    return InternationalMarketService(
        service_name="InternationalMarketService",
        intl_client=intl_client,
        market_service=market_service,
        logger=logger
    )