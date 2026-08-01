"""
User Crypto Settings Service - Tier 6 User Service

Manages user preferences for cryptocurrency selection and filtering.
Allows users to select from top 300 cryptocurrencies for personalized ranking.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
from app.services.core.base_service import BaseService
from app.services.user.preference_service import PreferenceService
import logging

class UserCryptoSettingsService(BaseService):
    """
    User Crypto Settings Service.
    
    Handles user preferences for:
    - Cryptocurrency selection from top 300
    - Exchange preferences
    - Custom watchlists
    - Ranking filters
    """
    
    def __init__(self,
                 service_name: str = "UserCryptoSettingsService",
                 preference_service: Optional[PreferenceService] = None,
                 crypto_client: Optional[Any] = None,
                 logger: Optional[logging.Logger] = None):
        """
        Initialize user crypto settings service.
        
        Args:
            service_name: Service identifier
            preference_service: User preference service instance
            crypto_client: Crypto API client instance
            logger: Optional logger instance
        """
        super().__init__(service_name, logger=logger)
        self.preference_service = preference_service or PreferenceService()
        self.crypto_client = crypto_client
        
        # Default crypto settings
        self.default_settings = {
            "selected_cryptos": [
                "BTC", "ETH", "BNB", "ADA", "SOL", "XRP", "DOT", 
                "DOGE", "AVAX", "MATIC", "LINK", "UNI", "LTC", "BCH"
            ],
            "excluded_cryptos": [],
            "exchange_source": "binance",
            "min_volume_24h": 1000000,
            "min_market_cap": 50000000,
            "price_change_filter": "all",  # all, positive, negative
            "custom_watchlist": []
        }
        
        # Top 300 cryptocurrencies (simplified - in production would come from API)
        self.top_300_cryptos = self._get_default_top_300()
        
        # Available exchanges
        self.available_exchanges = ["binance", "coinbase", "kraken", "bybit", "kucoin", "gate"]
    
    def _get_default_top_300(self) -> List[Dict[str, Any]]:
        """Get default list of top 300 cryptocurrencies."""
        # In production, this would be fetched from API
        return [
            {"symbol": "BTC", "name": "Bitcoin", "rank": 1, "market_cap": 800000000000},
            {"symbol": "ETH", "name": "Ethereum", "rank": 2, "market_cap": 300000000000},
            {"symbol": "BNB", "name": "Binance Coin", "rank": 3, "market_cap": 50000000000},
            {"symbol": "ADA", "name": "Cardano", "rank": 4, "market_cap": 20000000000},
            {"symbol": "SOL", "name": "Solana", "rank": 5, "market_cap": 15000000000},
            {"symbol": "XRP", "name": "XRP", "rank": 6, "market_cap": 30000000000},
            {"symbol": "DOT", "name": "Polkadot", "rank": 7, "market_cap": 10000000000},
            {"symbol": "DOGE", "name": "Dogecoin", "rank": 8, "market_cap": 12000000000},
            {"symbol": "AVAX", "name": "Avalanche", "rank": 9, "market_cap": 8000000000},
            {"symbol": "MATIC", "name": "Polygon", "rank": 10, "market_cap": 9000000000},
            {"symbol": "LINK", "name": "Chainlink", "rank": 11, "market_cap": 6000000000},
            {"symbol": "UNI", "name": "Uniswap", "rank": 12, "market_cap": 5000000000},
            {"symbol": "LTC", "name": "Litecoin", "rank": 13, "market_cap": 7000000000},
            {"symbol": "BCH", "name": "Bitcoin Cash", "rank": 14, "market_cap": 4000000000},
            {"symbol": "ATOM", "name": "Cosmos", "rank": 15, "market_cap": 3000000000},
            {"symbol": "ETC", "name": "Ethereum Classic", "rank": 16, "market_cap": 3000000000},
            {"symbol": "FIL", "name": "Filecoin", "rank": 17, "market_cap": 2500000000},
            {"symbol": "TRX", "name": "TRON", "rank": 18, "market_cap": 7000000000},
            {"symbol": "XLM", "name": "Stellar", "rank": 19, "market_cap": 3000000000},
            {"symbol": "NEAR", "name": "Near Protocol", "rank": 20, "market_cap": 2000000000},
            # ... more would be added
        ]
    
    async def initialize(self) -> None:
        """Initialize user crypto settings service."""
        self.logger.info("Initializing UserCryptoSettingsService")
        await self.preference_service.initialize()
        
        # Try to fetch latest top 300 from API if client available
        if self.crypto_client:
            try:
                await self._refresh_top_300()
            except Exception as e:
                self.logger.warning(f"Failed to refresh top 300: {str(e)}")
        
        self.logger.info("UserCryptoSettingsService initialized")
    
    async def shutdown(self) -> None:
        """Shutdown user crypto settings service."""
        await self.preference_service.shutdown()
        self.logger.info("UserCryptoSettingsService shutdown")
    
    async def get_user_settings(self, user_id: str) -> Dict[str, Any]:
        """
        Get user's crypto settings.
        
        Args:
            user_id: User identifier
            
        Returns:
            User's crypto settings
        """
        try:
            stored_prefs = await self.preference_service.get_user_preference(
                user_id, "crypto_settings"
            )
            
            if stored_prefs:
                return stored_prefs
            else:
                return self.default_settings.copy()
                
        except Exception as e:
            self.logger.error(f"Error getting crypto settings for {user_id}: {str(e)}")
            return self.default_settings.copy()
    
    async def update_user_settings(self,
                                   user_id: str,
                                   settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update user's crypto settings.
        
        Args:
            user_id: User identifier
            settings: New settings to save
            
        Returns:
            Updated settings
        """
        try:
            # Validate settings
            validated_settings = await self._validate_settings(settings)
            
            # Save to preference service
            await self.preference_service.set_user_preference(
                user_id, "crypto_settings", validated_settings
            )
            
            # Log the update
            await self._log_settings_change(user_id, "updated", validated_settings)
            
            return validated_settings
            
        except Exception as e:
            self.logger.error(f"Error updating crypto settings for {user_id}: {str(e)}")
            raise
    
    async def get_available_cryptos(self) -> List[Dict[str, Any]]:
        """
        Get list of available cryptocurrencies (top 300).
        
        Returns:
            List of top 300 cryptocurrencies with metadata
        """
        return self.top_300_cryptos
    
    async def update_selected_cryptos(self,
                                      user_id: str,
                                      selected: List[str]) -> Dict[str, Any]:
        """
        Update user's selected cryptocurrencies.
        
        Args:
            user_id: User identifier
            selected: List of crypto symbols to include
            
        Returns:
            Updated selection
        """
        try:
            # Validate against top 300
            available_symbols = {c["symbol"].upper() for c in self.top_300_cryptos}
            valid_selected = [s.upper() for s in selected if s.upper() in available_symbols]
            invalid = [s for s in selected if s.upper() not in available_symbols]
            
            if invalid:
                self.logger.warning(f"Invalid crypto symbols: {invalid}")
            
            # Get current settings
            current_settings = await self.get_user_settings(user_id)
            
            # Update selection
            current_settings["selected_cryptos"] = valid_selected
            
            # Save updated settings
            await self.update_user_settings(user_id, current_settings)
            
            return current_settings
            
        except Exception as e:
            self.logger.error(f"Error updating selected cryptos for {user_id}: {str(e)}")
            raise
    
    async def add_to_watchlist(self,
                               user_id: str,
                               symbol: str) -> Dict[str, Any]:
        """
        Add a cryptocurrency to user's custom watchlist.
        
        Args:
            user_id: User identifier
            symbol: Crypto symbol to add
            
        Returns:
            Updated settings
        """
        try:
            symbol = symbol.upper()
            available_symbols = {c["symbol"].upper() for c in self.top_300_cryptos}
            
            if symbol not in available_symbols:
                raise ValueError(f"Cryptocurrency {symbol} not in top 300")
            
            current_settings = await self.get_user_settings(user_id)
            
            if "custom_watchlist" not in current_settings:
                current_settings["custom_watchlist"] = []
            
            if symbol not in current_settings["custom_watchlist"]:
                current_settings["custom_watchlist"].append(symbol)
            
            await self.update_user_settings(user_id, current_settings)
            
            return current_settings
            
        except Exception as e:
            self.logger.error(f"Error adding to watchlist for {user_id}: {str(e)}")
            raise
    
    async def remove_from_watchlist(self,
                                    user_id: str,
                                    symbol: str) -> Dict[str, Any]:
        """
        Remove a cryptocurrency from user's custom watchlist.
        
        Args:
            user_id: User identifier
            symbol: Crypto symbol to remove
            
        Returns:
            Updated settings
        """
        try:
            symbol = symbol.upper()
            current_settings = await self.get_user_settings(user_id)
            
            if "custom_watchlist" in current_settings:
                current_settings["custom_watchlist"] = [
                    s for s in current_settings["custom_watchlist"] if s != symbol
                ]
            
            await self.update_user_settings(user_id, current_settings)
            
            return current_settings
            
        except Exception as e:
            self.logger.error(f"Error removing from watchlist for {user_id}: {str(e)}")
            raise
    
    async def get_effective_filters(self, user_id: str) -> Dict[str, Any]:
        """
        Get effective filters for a user (combining preferences with defaults).
        
        Args:
            user_id: User identifier
            
        Returns:
            Effective filters for crypto data querying
        """
        settings = await self.get_user_settings(user_id)
        
        return {
            "selected_cryptos": settings.get("selected_cryptos", self.default_settings["selected_cryptos"]),
            "excluded_cryptos": settings.get("excluded_cryptos", self.default_settings["excluded_cryptos"]),
            "exchange_source": settings.get("exchange_source", self.default_settings["exchange_source"]),
            "min_volume_24h": settings.get("min_volume_24h", self.default_settings["min_volume_24h"]),
            "min_market_cap": settings.get("min_market_cap", self.default_settings["min_market_cap"]),
            "price_change_filter": settings.get("price_change_filter", self.default_settings["price_change_filter"]),
            "custom_watchlist": settings.get("custom_watchlist", self.default_settings["custom_watchlist"]),
            "last_updated": datetime.utcnow().isoformat()
        }
    
    async def filter_cryptos_by_preferences(self,
                                           cryptos: List[Dict[str, Any]],
                                           user_id: str) -> List[Dict[str, Any]]:
        """
        Filter cryptocurrency list based on user preferences.
        
        Args:
            cryptos: List of cryptocurrency data
            user_id: User identifier
            
        Returns:
            Filtered list of cryptocurrencies
        """
        filters = await self.get_effective_filters(user_id)
        
        filtered = []
        for crypto in cryptos:
            symbol = crypto.get("symbol", "").upper()
            
            # Check if in selected list
            if filters["selected_cryptos"] and symbol not in filters["selected_cryptos"]:
                continue
            
            # Check if excluded
            if symbol in filters["excluded_cryptos"]:
                continue
            
            # Check volume filter
            volume_24h = crypto.get("volume_24h", 0)
            if volume_24h < filters["min_volume_24h"]:
                continue
            
            # Check market cap filter
            market_cap = crypto.get("market_cap", 0)
            if market_cap < filters["min_market_cap"]:
                continue
            
            # Check price change filter
            price_change = crypto.get("price_change_24h", 0)
            if filters["price_change_filter"] == "positive" and price_change <= 0:
                continue
            elif filters["price_change_filter"] == "negative" and price_change >= 0:
                continue
            
            filtered.append(crypto)
        
        return filtered
    
    async def _refresh_top_300(self) -> None:
        """Refresh top 300 cryptocurrencies from API."""
        try:
            if self.crypto_client:
                top_cryptos = await self.crypto_client.get_top_cryptocurrencies(limit=300)
                if top_cryptos:
                    self.top_300_cryptos = top_cryptos
                    self.logger.info(f"Refreshed top 300 cryptos: {len(top_cryptos)} items")
        except Exception as e:
            self.logger.error(f"Error refreshing top 300: {str(e)}")
    
    async def _validate_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate crypto settings.
        
        Args:
            settings: Settings to validate
            
        Returns:
            Validated settings
        """
        validated = {}
        
        # Validate selected cryptos
        available_symbols = {c["symbol"].upper() for c in self.top_300_cryptos}
        
        if "selected_cryptos" in settings:
            selected = settings["selected_cryptos"]
            if isinstance(selected, list):
                validated["selected_cryptos"] = [s.upper() for s in selected if s.upper() in available_symbols]
            else:
                validated["selected_cryptos"] = self.default_settings["selected_cryptos"]
        else:
            validated["selected_cryptos"] = self.default_settings["selected_cryptos"]
        
        # Validate excluded cryptos
        if "excluded_cryptos" in settings:
            excluded = settings["excluded_cryptos"]
            if isinstance(excluded, list):
                validated["excluded_cryptos"] = [s.upper() for s in excluded if s.upper() in available_symbols]
            else:
                validated["excluded_cryptos"] = self.default_settings["excluded_cryptos"]
        else:
            validated["excluded_cryptos"] = self.default_settings["excluded_cryptos"]
        
        # Validate exchange source
        if "exchange_source" in settings:
            exchange = settings["exchange_source"]
            if exchange in self.available_exchanges:
                validated["exchange_source"] = exchange
            else:
                validated["exchange_source"] = self.default_settings["exchange_source"]
        else:
            validated["exchange_source"] = self.default_settings["exchange_source"]
        
        # Validate numeric filters
        if "min_volume_24h" in settings:
            validated["min_volume_24h"] = max(0, float(settings["min_volume_24h"]))
        else:
            validated["min_volume_24h"] = self.default_settings["min_volume_24h"]
        
        if "min_market_cap" in settings:
            validated["min_market_cap"] = max(0, float(settings["min_market_cap"]))
        else:
            validated["min_market_cap"] = self.default_settings["min_market_cap"]
        
        # Validate price change filter
        if "price_change_filter" in settings:
            pcf = settings["price_change_filter"]
            if pcf in ["all", "positive", "negative"]:
                validated["price_change_filter"] = pcf
            else:
                validated["price_change_filter"] = self.default_settings["price_change_filter"]
        else:
            validated["price_change_filter"] = self.default_settings["price_change_filter"]
        
        # Copy custom watchlist
        if "custom_watchlist" in settings:
            watchlist = settings["custom_watchlist"]
            if isinstance(watchlist, list):
                validated["custom_watchlist"] = [s.upper() for s in watchlist if s.upper() in available_symbols]
            else:
                validated["custom_watchlist"] = self.default_settings["custom_watchlist"]
        else:
            validated["custom_watchlist"] = self.default_settings["custom_watchlist"]
        
        return validated
    
    async def _log_settings_change(self,
                                   user_id: str,
                                   action: str,
                                   settings: Dict[str, Any]) -> None:
        """
        Log settings changes for audit trail.
        
        Args:
            user_id: User identifier
            action: Action performed
            settings: Settings that were changed
        """
        self.logger.info(
            f"User {user_id} {action} crypto settings: "
            f"selected={len(settings.get('selected_cryptos', []))}, "
            f"excluded={len(settings.get('excluded_cryptos', []))}, "
            f"exchange={settings.get('exchange_source')}, "
            f"watchlist={len(settings.get('custom_watchlist', []))}"
        )

# Factory function for dependency injection
def get_user_crypto_settings_service(preference_service=None,
                                     crypto_client=None,
                                     logger=None) -> UserCryptoSettingsService:
    """Factory function to create UserCryptoSettingsService instance."""
    return UserCryptoSettingsService(
        service_name="UserCryptoSettingsService",
        preference_service=preference_service,
        crypto_client=crypto_client,
        logger=logger
    )