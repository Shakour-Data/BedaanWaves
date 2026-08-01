"""
User Market Settings Service - Tier 6 User Service

Manages user preferences for countries, market indices, and industries.
Enables customizable financial data filtering based on geographic and sector preferences.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, date
import asyncio
import json
from app.services.core.base_service import BaseService
from app.services.user.preference_service import PreferenceService
import logging

class UserMarketSettingsService(BaseService):
    """
    User Market Settings Service.
    
    Handles user preferences for:
    - Country/region selection
    - Market index selection  
    - Industry/sector filtering
    - Geographic data filtering
    """
    
    def __init__(self,
                 service_name: str = "UserMarketSettingsService",
                 preference_service: Optional[PreferenceService] = None,
                 logger: Optional[logging.Logger] = None):
        """
        Initialize user market settings service.
        
        Args:
            service_name: Service identifier
            preference_service: User preference service instance
            logger: Optional logger instance
        """
        super().__init__(service_name, logger=logger)
        self.preference_service = preference_service or PreferenceService()
        
        # Default market settings
        self.default_settings = {
            "countries": ["Iran"],
            "indices": ["TEPIX", "TEDPIX"],
            "industries": [],
            "regions": ["Middle East"],
            "exchanges": [],
            "currencies": ["IRR"]
        }
        
        # Available options (would typically come from database/cache)
        self.available_countries = [
            "Iran", "USA", "UK", "Germany", "France", "Japan", "China", 
            "Korea", "India", "Brazil", "Canada", "Australia", "Russia",
            "Turkey", "Saudi Arabia", "UAE", "Singapore", "Switzerland"
        ]
        
        self.available_indices = {
            "Iran": ["TEPIX", "TEDPIX", "IFX", "IRTEC"],
            "USA": ["SPX", "DJI", "IXIC", "RUT"],
            "UK": ["FTSE", "FTSE250"],
            "Germany": ["GDAXI", "MDX"],
            "France": ["FCHI", "SBF120"],
            "Japan": ["N225", "TOPX"],
            "China": ["SSE", "SZSE"],
            "Korea": ["KS11", "KSQ11"],
            "India": ["BSESN", "NIFTY"],
            "Brazil": ["BVSP"],
            "Canada": ["GSPTSE"],
            "Australia": ["AXJO"],
            "Russia": ["IMOEX"],
            "Turkey": ["XU100"],
            "Saudi Arabia": ["TASI"],
            "UAE": ["ADX", "DFM"]
        }
        
        self.available_industries = [
            "Technology", "Healthcare", "Financial", "Energy", "Materials",
            "Industrials", "Consumer Discretionary", "Consumer Staples",
            "Utilities", "Real Estate", "Communication Services"
        ]
    
    async def initialize(self) -> None:
        """Initialize user market settings service."""
        self.logger.info("Initializing UserMarketSettingsService")
        await self.preference_service.initialize()
        self.logger.info("UserMarketSettingsService initialized")
    
    async def shutdown(self) -> None:
        """Shutdown user market settings service."""
        await self.preference_service.shutdown()
        self.logger.info("UserMarketSettingsService shutdown")
    
    async def get_user_settings(self, user_id: str) -> Dict[str, Any]:
        """
        Get user's market settings.
        
        Args:
            user_id: User identifier
            
        Returns:
            User's market settings
        """
        try:
            stored_prefs = await self.preference_service.get_user_preference(
                user_id, "market_settings"
            )
            
            if stored_prefs:
                return stored_prefs
            else:
                # Return default settings
                return self.default_settings.copy()
                
        except Exception as e:
            self.logger.error(f"Error getting user settings for {user_id}: {str(e)}")
            return self.default_settings.copy()
    
    async def update_user_settings(self,
                                   user_id: str,
                                   settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update user's market settings.
        
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
                user_id, "market_settings", validated_settings
            )
            
            # Log the update
            await self._log_settings_change(user_id, "updated", validated_settings)
            
            return validated_settings
            
        except Exception as e:
            self.logger.error(f"Error updating user settings for {user_id}: {str(e)}")
            raise
    
    async def get_available_options(self) -> Dict[str, Any]:
        """
        Get available market settings options.
        
        Returns:
            Dictionary of available countries, indices, industries, etc.
        """
        return {
            "countries": self.available_countries,
            "indices": self.available_indices,
            "industries": self.available_industries,
            "regions": [
                "North America", "Europe", "Asia Pacific", "Middle East",
                "Latin America", "Africa"
            ],
            "exchanges": [
                "TSE", "NYSE", "NASDAQ", "LSE", "XETRA", "Euronext",
                "HKEX", "SSE", "SZSE", "KRX", "BSE", "NSE", "TSX", "ASX"
            ],
            "currencies": ["IRR", "USD", "EUR", "GBP", "JPY", "CNY", "KRW", 
                          "INR", "BRL", "CAD", "AUD", "RUB", "TRY", "SAR", "AED"]
        }
    
    async def update_country_selection(self,
                                       user_id: str,
                                       countries: List[str]) -> Dict[str, Any]:
        """
        Update user's country selection.
        
        Args:
            user_id: User identifier
            countries: List of selected countries
            
        Returns:
            Updated country selection
        """
        try:
            # Validate countries
            valid_countries = [c for c in countries if c in self.available_countries]
            invalid_countries = [c for c in countries if c not in self.available_countries]
            
            if invalid_countries:
                self.logger.warning(f"Invalid countries provided: {invalid_countries}")
            
            # Get current settings
            current_settings = await self.get_user_settings(user_id)
            
            # Update countries
            current_settings["countries"] = valid_countries
            
            # Auto-select relevant indices based on countries
            selected_indices = []
            for country in valid_countries:
                if country in self.available_indices:
                    selected_indices.extend(self.available_indices[country])
            
            # Remove duplicates
            current_settings["indices"] = list(set(selected_indices))
            
            # Save updated settings
            await self.update_user_settings(user_id, current_settings)
            
            return current_settings
            
        except Exception as e:
            self.logger.error(f"Error updating country selection for {user_id}: {str(e)}")
            raise
    
    async def update_index_selection(self,
                                     user_id: str,
                                     indices: List[str]) -> Dict[str, Any]:
        """
        Update user's index selection.
        
        Args:
            user_id: User identifier
            indices: List of selected indices
            
        Returns:
            Updated index selection
        """
        try:
            # Validate indices
            valid_indices = []
            for country, country_indices in self.available_indices.items():
                valid_indices.extend(country_indices)
            
            # Flatten available indices for validation
            all_available = []
            for country_indices in self.available_indices.values():
                all_available.extend(country_indices)
            
            valid_indices = [i for i in indices if i in all_available]
            invalid_indices = [i for i in indices if i not in all_available]
            
            if invalid_indices:
                self.logger.warning(f"Invalid indices provided: {invalid_indices}")
            
            # Get current settings
            current_settings = await self.get_user_settings(user_id)
            
            # Update indices
            current_settings["indices"] = valid_indices
            
            # Save updated settings
            await self.update_user_settings(user_id, current_settings)
            
            return current_settings
            
        except Exception as e:
            self.logger.error(f"Error updating index selection for {user_id}: {str(e)}")
            raise
    
    async def update_industry_selection(self,
                                        user_id: str,
                                        industries: List[str]) -> Dict[str, Any]:
        """
        Update user's industry selection.
        
        Args:
            user_id: User identifier
            industries: List of selected industries
            
        Returns:
            Updated industry selection
        """
        try:
            # Validate industries
            valid_industries = [i for i in industries if i in self.available_industries]
            invalid_industries = [i for i in industries if i not in self.available_industries]
            
            if invalid_industries:
                self.logger.warning(f"Invalid industries provided: {invalid_industries}")
            
            # Get current settings
            current_settings = await self.get_user_settings(user_id)
            
            # Update industries
            current_settings["industries"] = valid_industries
            
            # Save updated settings
            await self.update_user_settings(user_id, current_settings)
            
            return current_settings
            
        except Exception as e:
            self.logger.error(f"Error updating industry selection for {user_id}: {str(e)}")
            raise
    
    async def get_effective_filters(self, user_id: str) -> Dict[str, Any]:
        """
        Get effective filters for a user (combining preferences with defaults).
        
        Args:
            user_id: User identifier
            
        Returns:
            Effective filters for data querying
        """
        settings = await self.get_user_settings(user_id)
        
        # Apply defaults where needed
        effective_filters = {
            "countries": settings.get("countries", self.default_settings["countries"]),
            "indices": settings.get("indices", self.default_settings["indices"]),
            "industries": settings.get("industries", self.default_settings["industries"]),
            "regions": settings.get("regions", self.default_settings["regions"]),
            "exchanges": settings.get("exchanges", self.default_settings["exchanges"]),
            "currencies": settings.get("currencies", self.default_settings["currencies"]),
            "last_updated": datetime.utcnow().isoformat()
        }
        
        return effective_filters
    
    async def _validate_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate user settings.
        
        Args:
            settings: Settings to validate
            
        Returns:
            Validated settings
        """
        validated = {}
        
        # Validate countries
        if "countries" in settings:
            countries = settings["countries"]
            if isinstance(countries, list):
                validated["countries"] = [c for c in countries if c in self.available_countries]
            else:
                validated["countries"] = self.default_settings["countries"]
        else:
            validated["countries"] = self.default_settings["countries"]
        
        # Validate indices
        if "indices" in settings:
            indices = settings["indices"]
            if isinstance(indices, list):
                # Flatten available indices for validation
                all_available = []
                for country_indices in self.available_indices.values():
                    all_available.extend(country_indices)
                validated["indices"] = [i for i in indices if i in all_available]
            else:
                validated["indices"] = self.default_settings["indices"]
        else:
            validated["indices"] = self.default_settings["indices"]
        
        # Validate industries
        if "industries" in settings:
            industries = settings["industries"]
            if isinstance(industries, list):
                validated["industries"] = [i for i in industries if i in self.available_industries]
            else:
                validated["industries"] = self.default_settings["industries"]
        else:
            validated["industries"] = self.default_settings["industries"]
        
        # Copy other fields
        for key in ["regions", "exchanges", "currencies"]:
            if key in settings:
                value = settings[key]
                if isinstance(value, list):
                    validated[key] = value
                else:
                    validated[key] = self.default_settings.get(key, [])
            else:
                validated[key] = self.default_settings.get(key, [])
        
        return validated
    
    async def _log_settings_change(self,
                                   user_id: str,
                                   action: str,
                                   settings: Dict[str, Any]) -> None:
        """
        Log settings changes for audit trail.
        
        Args:
            user_id: User identifier
            action: Action performed (created, updated, deleted)
            settings: Settings that were changed
        """
        try:
            # In production, would write to audit log table
            self.logger.info(
                f"User {user_id} {action} market settings: "
                f"countries={len(settings.get('countries', []))}, "
                f"indices={len(settings.get('indices', []))}, "
                f"industries={len(settings.get('industries', []))}"
            )
        except Exception as e:
            self.logger.warning(f"Failed to log settings change: {str(e)}")

# Factory function for dependency injection
def get_user_market_settings_service(preference_service=None,
                                     logger=None) -> UserMarketSettingsService:
    """Factory function to create UserMarketSettingsService instance."""
    return UserMarketSettingsService(
        service_name="UserMarketSettingsService",
        preference_service=preference_service,
        logger=logger
    )