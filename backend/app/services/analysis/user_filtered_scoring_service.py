"""
User Filtered Scoring Service - Tier 3 Analysis Service

Provides scoring and ranking based on user-selected preferences for sectors
and industries. Only instruments that participate in the formation of the
Nasdaq index are considered (Nasdaq-listed EQUITY and ETF).
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, date
import asyncio
from app.services.core.base_service import BaseService
from app.services.analysis.scoring_service import ScoringService
from app.services.data.stock_service import StockService
from app.services.data.market_service import MarketService
import logging

class UserFilteredScoringService(BaseService):
    """
    User Filtered Scoring Service.

    Applies user-preference filtering (sector, industry) before scoring and
    ranking assets. Crypto, forex, commodities, bonds, and non-Nasdaq
    equities are not part of the supported universe.
    """

    def __init__(
        self,
        service_name: str = "UserFilteredScoringService",
        scoring_service: Optional[ScoringService] = None,
        stock_service: Optional[StockService] = None,
        market_service: Optional[MarketService] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize user filtered scoring service.

        Args:
            service_name: Service identifier
            scoring_service: Core scoring service instance
            stock_service: Stock data service instance
            market_service: Market data service instance
            logger: Optional logger instance
        """
        super().__init__(service_name, logger=logger)
        self.scoring_service = scoring_service or ScoringService()
        self.stock_service = stock_service
        self.market_service = market_service

        self.default_preferences = {
            "sectors": [],
            "industries": [],
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

        Only assets whose ``market`` is ``NASDAQ`` and whose ``asset_class``
        is ``EQUITY`` or ``ETF`` are retained. Crypto, forex, commodities,
        bonds, and non-Nasdaq instruments are always excluded.

        Args:
            assets: List of assets to filter
            user_preferences: User's preference configuration

        Returns:
            Filtered list of assets matching criteria
        """
        sectors = user_preferences.get("sectors", self.default_preferences["sectors"])
        industries = user_preferences.get("industries", self.default_preferences["industries"])

        filtered_assets = []
        for asset in assets:
            if asset.get("market") != "NASDAQ":
                continue
            if asset.get("asset_class") not in ("EQUITY", "ETF"):
                continue

            asset_sector = asset.get("sector", "")
            if sectors and asset_sector not in sectors:
                continue

            asset_industry = asset.get("industry", asset.get("sector", ""))
            if industries and asset_industry not in industries:
                if not self._is_part_of_industry(asset, industries):
                    continue

            filtered_assets.append(asset)

        return filtered_assets

    def _is_part_of_industry(self, asset: Dict[str, Any], industries: List[str]) -> bool:
        asset_industry = asset.get("industry", asset.get("sector", ""))

        for user_industry in industries:
            if asset_industry.upper() == user_industry.upper():
                return True
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
            scoring_method: Scoring method

        Returns:
            Ranked list of assets with scores
        """
        filtered_assets = await self.filter_by_user_preferences(assets, user_preferences)

        if not filtered_assets:
            return []

        scored_assets = []
        for asset in filtered_assets:
            try:
                score_data = await self.scoring_service.analyze(asset)
                scored_asset = {
                    **asset,
                    "score": score_data.get("score", 0.0),
                    "rank": 0,
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

        scored_assets.sort(key=lambda x: x.get("score", 0.0), reverse=True)
        for rank, asset in enumerate(scored_assets, start=1):
            asset["rank"] = rank

        return scored_assets

    async def rank_assets_by_sector(self,
                                    sector: str,
                                    assets: List[Dict[str, Any]],
                                    user_preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Rank Nasdaq assets from a specific sector."""
        sector_assets = [a for a in assets
                         if (a.get("sector") or "").upper() == sector.upper()]

        user_prefs = {**user_preferences, "sectors": [sector]}
        return await self.score_and_rank(sector_assets, user_prefs)

    async def rank_assets_by_industry(self,
                                      industry: str,
                                      assets: List[Dict[str, Any]],
                                      user_preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Rank Nasdaq assets from a specific industry."""
        industry_assets = [a for a in assets
                           if (a.get("industry") or a.get("sector") or "").upper() == industry.upper()]

        user_prefs = {**user_preferences, "industries": [industry]}
        return await self.score_and_rank(industry_assets, user_prefs)


# Factory function for dependency injection
def get_user_filtered_scoring_service(scoring_service=None, stock_service=None,
                                      market_service=None,
                                      logger=None) -> UserFilteredScoringService:
    """Factory function to create UserFilteredScoringService instance."""
    return UserFilteredScoringService(
        service_name="UserFilteredScoringService",
        scoring_service=scoring_service,
        stock_service=stock_service,
        market_service=market_service,
        logger=logger
    )
