"""
User Filtered Recommendation Service - Tier 4 ML Service

Provides personalized recommendations filtered by user preferences for
countries, indices, industries, and cryptocurrencies.
"""

from typing import Dict, List, Optional, Any
from datetime import timezone, datetime
import asyncio
from app.services.core.base_service import BaseService
from app.services.ml.recommendation_service import RecommendationService
from app.services.analysis.scoring_service import ScoringService
import logging

class UserFilteredRecommendationService(BaseService):
    """
    User Filtered Recommendation Service.
    
    Generates personalized recommendations based on user-selected filters
    (country, index, industry, crypto) and applies ML-based ranking.
    """
    
    def __init__(self,
                 service_name: str = "UserFilteredRecommendationService",
                 recommendation_service: Optional[RecommendationService] = None,
                 scoring_service: Optional[ScoringService] = None,
                 logger: Optional[logging.Logger] = None):
        """
        Initialize user filtered recommendation service.
        
        Args:
            service_name: Service identifier
            recommendation_service: Core recommendation service instance
            scoring_service: Scoring service for asset evaluation
            logger: Optional logger instance
        """
        super().__init__(service_name, logger=logger)
        self.recommendation_service = recommendation_service or RecommendationService()
        self.scoring_service = scoring_service or ScoringService()
        
        # Default recommendation parameters
        self.default_limit = 50
        self.default_diversification = {"max_stocks_per_sector": 5, "max_crypto": 20}
    
    async def initialize(self) -> None:
        """Initialize user filtered recommendation service."""
        self.logger.info("Initializing UserFilteredRecommendationService")
        await self.recommendation_service.initialize()
        self.logger.info("UserFilteredRecommendationService initialized")
    
    async def shutdown(self) -> None:
        """Shutdown user filtered recommendation service."""
        await self.recommendation_service.shutdown()
        self.logger.info("UserFilteredRecommendationService shutdown")
    
    async def get_recommendations(self,
                                  user_id: str,
                                  user_preferences: Dict[str, Any],
                                  limit: int = None,
                                  include_diversification: bool = True) -> List[Dict[str, Any]]:
        """
        Get personalized recommendations based on user preferences.
        
        Args:
            user_id: User identifier
            user_preferences: User's preference configuration
            limit: Maximum number of recommendations
            include_diversification: Apply diversification rules
            
        Returns:
            List of recommended assets with scores
        """
        if limit is None:
            limit = self.default_limit
        
        # Step 1: Get initial recommendations from core service
        try:
            initial_recommendations = await self.recommendation_service.generate_recommendations(
                user_id=user_id,
                portfolio_value=user_preferences.get("portfolio_value", 100000),
                risk_tolerance=user_preferences.get("risk_tolerance", "medium")
            )
        except Exception as e:
            self.logger.error(f"Error generating initial recommendations: {str(e)}")
            initial_recommendations = []
        
        # Step 2: Filter by user preferences
        filtered_recommendations = await self._apply_user_filters(
            initial_recommendations, user_preferences
        )
        
        # Step 3: Score filtered recommendations
        scored_recommendations = await self._score_recommendations(filtered_recommendations)
        
        # Step 4: Apply diversification if requested
        if include_diversification:
            diversified_recommendations = await self._apply_diversification(
                scored_recommendations, user_preferences
            )
        else:
            diversified_recommendations = scored_recommendations[:limit]
        
        # Step 5: Sort by score and limit
        diversified_recommendations.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        return diversified_recommendations[:limit]
    
    async def _apply_user_filters(self,
                                  recommendations: List[Dict[str, Any]],
                                  user_preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Apply user preference filters to recommendations.
        
        Args:
            recommendations: Initial recommendations
            user_preferences: User's preference configuration
            
        Returns:
            Filtered recommendations
        """
        countries = user_preferences.get("countries", [])
        indices = user_preferences.get("indices", [])
        industries = user_preferences.get("industries", [])
        crypto = user_preferences.get("crypto", [])
        
        filtered = []
        
        for rec in recommendations:
            # Apply country filter
            if countries:
                asset_country = rec.get("country", rec.get("country_code", ""))
                if asset_country and asset_country not in countries:
                    continue
            
            # Apply index filter
            if indices:
                rec_index = rec.get("index", rec.get("market_index", ""))
                if rec_index and rec_index not in indices:
                    # Check if part of index
                    rec_indices = rec.get("indices", [])
                    if isinstance(rec_indices, str):
                        rec_indices = [rec_indices]
                    if rec_index not in indices and not any(i in indices for i in rec_indices):
                        continue
            
            # Apply industry filter
            if industries:
                rec_industry = rec.get("industry", rec.get("sector", ""))
                if rec_industry and rec_industry not in industries:
                    continue
            
            # Apply crypto filter
            if crypto:
                rec_symbol = rec.get("symbol", "").upper()
                if rec.get("asset_class") == "cryptocurrency":
                    if rec_symbol not in [c.upper() for c in crypto]:
                        continue
            
            filtered.append(rec)
        
        return filtered
    
    async def _score_recommendations(self,
                                     recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Score recommendations using scoring service.
        
        Args:
            recommendations: Recommendations to score
            
        Returns:
            Recommendations with scores
        """
        scored = []
        
        for rec in recommendations:
            try:
                score_data = await self.scoring_service.analyze(rec)
                rec["score"] = score_data.get("score", 0.0)
                rec["scoring_details"] = score_data
                scored.append(rec)
            except Exception as e:
                self.logger.warning(f"Error scoring recommendation {rec.get('symbol')}: {str(e)}")
                rec["score"] = 0.0
                scored.append(rec)
        
        return scored
    
    async def _apply_diversification(self,
                                     recommendations: List[Dict[str, Any]],
                                     user_preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Apply diversification rules to recommendations.
        
        Args:
            recommendations: Scored recommendations
            user_preferences: User's preference configuration
            
        Returns:
            Diversified recommendations
        """
        diversification_rules = user_preferences.get(
            "diversification", 
            self.default_diversification
        )
        
        diversified = []
        sector_counts = {}
        index_counts = {}
        country_counts = {}
        crypto_count = 0
        
        for rec in recommendations:
            asset_class = rec.get("asset_class", "")
            
            # Handle stocks
            if asset_class != "cryptocurrency":
                sector = rec.get("sector", rec.get("industry", "Other"))
                index = rec.get("index", rec.get("market_index", "Other"))
                country = rec.get("country", rec.get("country_code", "Other"))
                
                # Check diversification limits
                sector_count = sector_counts.get(sector, 0)
                max_sector = diversification_rules.get("max_stocks_per_sector", 5)
                
                if sector_count < max_sector:
                    sector_counts[sector] = sector_count + 1
                    index_counts[index] = index_counts.get(index, 0) + 1
                    country_counts[country] = country_counts.get(country, 0) + 1
                    diversified.append(rec)
            else:
                # Handle crypto
                max_crypto = diversification_rules.get("max_crypto", 20)
                if crypto_count < max_crypto:
                    crypto_count += 1
                    diversified.append(rec)
        
        return diversified
    
    async def generate_diversified_portfolio(self,
                                            user_id: str,
                                            user_preferences: Dict[str, Any],
                                            target_value: float = 100000) -> Dict[str, Any]:
        """
        Generate a diversified portfolio recommendation.
        
        Args:
            user_id: User identifier
            user_preferences: User's preference configuration
            target_value: Target portfolio value
            
        Returns:
            Portfolio allocation recommendation
        """
        recommendations = await self.get_recommendations(
            user_id=user_id,
            user_preferences=user_preferences,
            limit=100,
            include_diversification=True
        )
        
        if not recommendations:
            return {"error": "No recommendations available", "allocation": {}}
        
        # Calculate allocation based on scores and risk tolerance
        total_score = sum(r.get("score", 0) for r in recommendations)
        
        allocation = {}
        for rec in recommendations:
            symbol = rec.get("symbol", "")
            score = rec.get("score", 0)
            
            if total_score > 0:
                weight = score / total_score
                allocation[symbol] = {
                    "target_value": target_value * weight,
                    "weight": weight,
                    "score": score,
                    "asset_class": rec.get("asset_class", ""),
                    "country": rec.get("country", ""),
                    "sector": rec.get("sector", "")
                }
        
        return {
            "user_id": user_id,
            "target_value": target_value,
            "total_assets": len(recommendations),
            "allocation": allocation,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }

# Factory function for dependency injection
def get_user_filtered_recommendation_service(recommendation_service=None,
                                              scoring_service=None,
                                              logger=None) -> UserFilteredRecommendationService:
    """Factory function to create UserFilteredRecommendationService instance."""
    return UserFilteredRecommendationService(
        service_name="UserFilteredRecommendationService",
        recommendation_service=recommendation_service,
        scoring_service=scoring_service,
        logger=logger
    )