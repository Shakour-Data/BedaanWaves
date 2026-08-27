"""
User Filtered Scoring Service - Tier 3 Analysis Service

Provides scoring and ranking based on user-selected preferences for countries,
indices, industries, and cryptocurrencies.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, date
import asyncio
from app.services.core.base_service import BaseService
from app.services.analysis.scoring_service import ScoringService
from app.services.data.stock_service import StockService
from app.services.data.crypto_api_client import CryptoApiClient
from app.services.data.market_service import MarketService
import logging

class UserFilteredScoringService(BaseService):
    """
    User Filtered Scoring Service.
    
    Applies user-preference filtering (country, index, industry, crypto) 
    before scoring and ranking assets.
    """
    
    def __init__(
        self,
        service_name: str = "UserFilteredScoringService",
        scoring_service: Optional[ScoringService] = None,
        stock_service: Optional[StockService] = None,
        crypto_client: Optional[CryptoApiClient] = None,
        market_service: Optional[MarketService] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize user filtered scoring service.
        
        Args:
            service_name: Service identifier
            scoring_service: Core scoring service instance
            stock_service: Stock data service instance
            crypto_client: Crypto API client instance
            market_service: Market data service instance
            logger: Optional logger instance
        """
        super().__init__(service_name, logger=logger)
        self.scoring_service = scoring_service or ScoringService()
        self.stock_service = stock_service
        self.crypto_client = crypto_client
        self.market_service = market_service
        
        # Default user preferences (can be overridden per user)
        self.default_preferences = {
            "countries": ["Iran"],
            "indices": ["TEPIX", "TEDPIX"],
            "industries": [],
            "crypto": []
        }
    
    async def initialize(self) -> None:
        """Initialize user filtered scoring service."""
        self.logger.info("Initializing UserFilteredScoringService")
        await self.scoring_service.initialize()
        self.logger.info("UserFilteredScoringService initialized")
    
    async def shutdown(self) -> None:
        """Shutdown user filtered scoring service."""
        await self.scoring_service.shutdown()
        self.logger.info("UserFilteredScoringService shutdown")
    
    async def filter_by_user_preferences(self,
                                         assets: List[Dict[str, Any]],
                                         user_preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Filter assets based on user preferences.
        
        Args:
            assets: List of assets to filter
            user_preferences: User's preference configuration
            
        Returns:
            Filtered list of assets matching user preferences
        """
        filtered_assets = []
        
        countries = user_preferences.get("countries", self.default_preferences["countries"])
        indices = user_preferences.get("indices", self.default_preferences["indices"])
        industries = user_preferences.get("industries", self.default_preferences["industries"])
        crypto = user_preferences.get("crypto", self.default_preferences["crypto"])
        
        for asset in assets:
            # Check country filter
            asset_country = asset.get("country") or asset.get("country_code", "")
            if countries and asset_country not in countries:
                continue
            
            # Check index filter
            asset_index = asset.get("index", asset.get("market_index", ""))
            if indices and asset_index not in indices:
                # Check if it's part of the index
                if not self._is_part_of_index(asset, indices):
                    continue
            
            # Check industry filter
            asset_industry = asset.get("industry", asset.get("sector", ""))
            if industries and asset_industry not in industries:
                # Check if it's part of the industry index
                if not self._is_part_of_industry(asset, industries):
                    continue
            
            # Check crypto filter (if crypto-related asset)
            asset_class = asset.get("asset_class", asset.get("type", ""))
            if asset_class == "cryptocurrency" or "crypto" in str(asset.get("market", "")).lower():
                if crypto:
                    symbol = asset.get("symbol", "").upper()
                    if symbol not in [c.upper() for c in crypto]:
                        continue
            
            filtered_assets.append(asset)
        
        return filtered_assets
    
    def _is_part_of_index(self, asset: Dict[str, Any], indices: List[str]) -> bool:
        """Check if asset belongs to any of the specified indices."""
        # Simple check - compare index name in asset metadata
        asset_indices = asset.get("indices", [])
        if isinstance(asset_indices, str):
            asset_indices = [asset_indices]
        
        for asset_index in asset_indices:
            for user_index in indices:
                if asset_index.upper() == user_index.upper():
                    return True
        return False
    
    def _is_part_of_industry(self, asset: Dict[str, Any], industries: List[str]) -> bool:
        """Check if asset belongs to any of the specified industries."""
        asset_industry = asset.get("industry", asset.get("sector", ""))
        
        for user_industry in industries:
            if asset_industry.upper() == user_industry.upper():
                return True
            # Partial match
            if user_industry.upper() in asset_industry.upper():
                return True
        return False
    
    async def score_and_rank(self,
                             assets: List[Dict[str, Any]],
                             user_preferences: Dict[str, Any],
                             scoring_method: str = "default") -> List[Dict[str, Any]]:
        """
        Score and rank assets based on user preferences.
        
        Args:
            assets: List of assets to score
            user_preferences: User's preference configuration
            scoring_method: Scoring method to use
            
        Returns:
            Ranked list of assets with scores
        """
        # Step 1: Filter assets by user preferences
        filtered_assets = await self.filter_by_user_preferences(assets, user_preferences)
        
        if not filtered_assets:
            return []
        
        # Step 2: Score assets using core scoring service
        scored_assets = []
        
        for asset in filtered_assets:
            try:
                if scoring_method == "default":
                    score_data = await self.scoring_service.analyze(asset)
                else:
                    score_data = await self.scoring_service.analyze(asset)
                
                scored_asset = {
                    **asset,
                    "score": score_data.get("score", 0.0),
                    "rank": 0,  # Will be set after sorting
                    "scoring_details": score_data,
                    "user_preferences_applied": user_preferences
                }
                scored_assets.append(scored_asset)
                
            except Exception as e:
                self.logger.error(f"Error scoring asset {asset.get('symbol')}: {str(e)}")
                scored_assets.append({
                    **asset,
                    "score": 0.0,
                    "rank": 0,
                    "scoring_error": str(e)
                })
        
        # Step 3: Sort by score and assign ranks
        scored_assets.sort(key=lambda x: x.get("score", 0.0), reverse=True)
        
        for rank, asset in enumerate(scored_assets, start=1):
            asset["rank"] = rank
        
        return scored_assets
    
    async def rank_assets_by_country(self,
                                     country: str,
                                     assets: List[Dict[str, Any]],
                                     user_preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Rank assets from a specific country.
        
        Args:
            country: Country name to filter by
            assets: List of assets to rank
            user_preferences: User's preference configuration
            
        Returns:
            Ranked assets from the specified country
        """
        country_assets = [a for a in assets 
                          if a.get("country", a.get("country_code", "")).lower() == country.lower()]
        
        user_prefs = {**user_preferences, "countries": [country]}
        
        return await self.score_and_rank(country_assets, user_prefs)
    
    async def rank_assets_by_index(self,
                                   index: str,
                                   assets: List[Dict[str, Any]],
                                   user_preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Rank assets from a specific index.
        
        Args:
            index: Index name to filter by
            assets: List of assets to rank
            user_preferences: User's preference configuration
            
        Returns:
            Ranked assets from the specified index
        """
        index_assets = [a for a in assets 
                        if a.get("index", a.get("market_index", "")).upper() == index.upper()]
        
        user_prefs = {**user_preferences, "indices": [index]}
        
        return await self.score_and_rank(index_assets, user_prefs)
    
    async def rank_assets_by_industry(self,
                                      industry: str,
                                      assets: List[Dict[str, Any]],
                                      user_preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Rank assets from a specific industry.
        
        Args:
            industry: Industry name to filter by
            assets: List of assets to rank
            user_preferences: User's preference configuration
            
        Returns:
            Ranked assets from the specified industry
        """
        industry_assets = [a for a in assets 
                           if a.get("industry", a.get("sector", "")).upper() == industry.upper()]
        
        user_prefs = {**user_preferences, "industries": [industry]}
        
        return await self.score_and_rank(industry_assets, user_prefs)
    
    async def rank_crypto_by_user_selection(self,
                                           selected_crypto: List[str],
                                           all_crypto_assets: List[Dict[str, Any]],
                                           user_preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Rank cryptocurrencies based on user's selected list.
        
        Args:
            selected_crypto: List of crypto symbols user wants to rank
            all_crypto_assets: All available crypto assets
            user_preferences: User's preference configuration
            
        Returns:
            Ranked selected cryptocurrencies with scores
        """
        crypto_filter = {**user_preferences, "crypto": selected_crypto}
        
        selected_assets = [a for a in all_crypto_assets 
                           if a.get("symbol", "").upper() in [c.upper() for c in selected_crypto]]
        
        return await self.score_and_rank(selected_assets, crypto_filter)

# Factory function for dependency injection
def get_user_filtered_scoring_service(scoring_service=None, stock_service=None,
                                        crypto_client=None, market_service=None,
                                        logger=None) -> UserFilteredScoringService:
    """Factory function to create UserFilteredScoringService instance."""
    return UserFilteredScoringService(
        service_name="UserFilteredScoringService",
        scoring_service=scoring_service,
        stock_service=stock_service,
        crypto_client=crypto_client,
        market_service=market_service,
        logger=logger
    )