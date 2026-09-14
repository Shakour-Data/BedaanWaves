"""
Scoring Service - Tier 3 Analysis Service

6D Scoring System with a 4-level hierarchy.
Comprehensive stock scoring for US/OTC and foreign exchanges.
Now supports ML-driven dynamic coefficient learning.

The hierarchy is *derived*, not hardcoded: every level comes from
``scoring_engine_v2.METRIC_UNIVERSE`` via ``app.services.analysis.hierarchy``,
which is the single source of truth shared with the trend endpoints.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import asyncio
from ..core import AnalysisService
from ..ml import CoefficientLearningService
from app.services.core.dependency_container import get_global_container
from app.core.utils import utc_now_iso
from app.services.analysis.hierarchy import (
    ASPECT_TO_PARENT,
    SUB_ASPECT_TO_PARENT,
    SUB_DIMENSION_TO_PARENT,
    V2_ASPECTS,
    V2_DIMENSIONS,
    V2_SUB_ASPECTS,
    V2_SUB_DIMENSIONS,
)


class ScoringService(AnalysisService):
    """
    6D Scoring service with a 4-level hierarchy derived from METRIC_UNIVERSE.

    Hierarchy (counts come from ``app.services.analysis.hierarchy``):
    - Level 1: Dimensions (fundamental, technical, sentiment, risk, macro, ai)
    - Level 2: Sub-Dimensions
    - Level 3: Aspects
    - Level 4: Sub-Aspects

    Call :meth:`get_hierarchy_info` for the authoritative live counts.

    6D Aggregation now uses ML-learned weights with fallback to static weights:
    - Fundamental (learned, fallback 25%)
    - Technical (learned, fallback 20%)
    - Sentiment (learned, fallback 15%)
    - Risk (learned, fallback 20%)
    - Macro (learned, fallback 10%)
    - AI (learned, fallback 10%)
    """
    
    # Static fallback weights (used when ML service unavailable or not trained)
    DIMENSION_WEIGHTS = {
        "fundamental": 0.25,
        "technical": 0.20,
        "sentiment": 0.15,
        "risk": 0.20,
        "macro": 0.10,
        "ai": 0.10,
    }
    
    DIMENSIONS = ['fundamental', 'technical', 'sentiment', 'risk', 'macro', 'ai']
    
    def __init__(self, service_name: str = "ScoringService"):
        super().__init__(service_name)
        self._hierarchy: Dict[str, Dict[str, Any]] = {}
        self._scores_cache: Dict[str, Dict[str, float]] = {}
        self._coefficient_service: Optional[CoefficientLearningService] = None
        self._use_ml_coefficients = True  # Feature flag
        
    async def initialize(self) -> None:
        """Initialize service and build hierarchy"""
        self._build_hierarchy()
        
        # Initialize coefficient learning service
        try:
            container = get_global_container()
            self._coefficient_service = container.get("coefficient_learning_service")
            if self._coefficient_service:
                self.logger.info("ML Coefficient Learning Service connected")
            else:
                self.logger.warning("Coefficient Learning Service not found in container")
                self._coefficient_service = None
        except Exception as e:
            self.logger.warning(f"Could not initialize Coefficient Learning Service: {e}")
            self._coefficient_service = None
        
        self.logger.info(f"ScoringService initialized with {len(self._hierarchy)} hierarchy nodes")
    
    async def shutdown(self) -> None:
        """Shutdown service"""
        self._scores_cache.clear()
        self.logger.info("ScoringService shutdown")
    
    def _build_hierarchy(self) -> None:
        """Build the 4-level hierarchy from the canonical v2 definition.

        Every node id is a real metric key from
        ``scoring_engine_v2.METRIC_UNIVERSE`` (surfaced via
        ``app.services.analysis.hierarchy``), so the tree reported by
        :meth:`get_hierarchy_info` is the same tree the scoring pipeline
        actually uses. Level 1 weights come from ``DIMENSION_WEIGHTS``.
        """
        self._hierarchy = {}

        for dim in V2_DIMENSIONS:
            self._hierarchy[dim] = {
                "level": 1,
                "id": dim,
                "name": dim,
                "group": dim,
                "parent_id": None,
                "weight": self.DIMENSION_WEIGHTS.get(dim, 0.0),
            }

        for sub_dim in V2_SUB_DIMENSIONS:
            self._hierarchy[sub_dim] = {
                "level": 2,
                "id": sub_dim,
                "name": sub_dim,
                "parent_id": SUB_DIMENSION_TO_PARENT.get(sub_dim),
            }

        for aspect in V2_ASPECTS:
            self._hierarchy[aspect] = {
                "level": 3,
                "id": aspect,
                "name": aspect,
                "parent_id": ASPECT_TO_PARENT.get(aspect),
            }

        for sub_aspect in V2_SUB_ASPECTS:
            self._hierarchy[sub_aspect] = {
                "level": 4,
                "id": sub_aspect,
                "name": sub_aspect,
                "parent_id": SUB_ASPECT_TO_PARENT.get(sub_aspect),
            }

        self._verify_hierarchy_counts()

    def _verify_hierarchy_counts(self) -> None:
        """Verify the derived hierarchy matches the canonical definition."""
        level1_count = sum(1 for v in self._hierarchy.values() if v.get("level") == 1)
        level2_count = sum(1 for v in self._hierarchy.values() if v.get("level") == 2)
        level3_count = sum(1 for v in self._hierarchy.values() if v.get("level") == 3)
        level4_count = sum(1 for v in self._hierarchy.values() if v.get("level") == 4)

        expected = (
            len(V2_DIMENSIONS),
            len(V2_SUB_DIMENSIONS),
            len(V2_ASPECTS),
            len(V2_SUB_ASPECTS),
        )
        actual = (level1_count, level2_count, level3_count, level4_count)

        if actual != expected:
            self.logger.warning(
                "Hierarchy drift: derived L1=%d L2=%d L3=%d L4=%d but the canonical "
                "definition has L1=%d L2=%d L3=%d L4=%d",
                *actual, *expected,
            )
        else:
            self.logger.debug(
                "Hierarchy built from canonical v2 definition: L1=%d, L2=%d, L3=%d, L4=%d "
                "(%d nodes total)",
                level1_count, level2_count, level3_count, level4_count,
                len(self._hierarchy),
            )

    def _get_dynamic_weights(self, level: str = "dimensions") -> Dict[str, float]:
        """
        Get weights for a specific hierarchy level, trying ML first then falling back to static.
        
        Args:
            level: The hierarchy level to get weights for.
                Currently only "dimensions" is implemented for 6D aggregation.
                   
        Returns:
            Dictionary of item names to weights (should sum to ~1.0)
        """
        # Try to get ML weights first if enabled and service available
        if (self._use_ml_coefficients and 
            self._coefficient_service and 
            self._coefficient_service.is_model_trained(level)):
            
            ml_weights = self._coefficient_service.get_coefficients(level)
            if ml_weights and len(ml_weights) > 0:
                # Validate that weights sum to approximately 1.0
                total = sum(ml_weights.values())
                if 0.9 <= total <= 1.1:  # Sum must be close to 1.0
                    self.logger.debug(f"Using ML weights for {level}: {ml_weights}")
                    return ml_weights
                else:
                    self.logger.warning(
                        f"ML weights for {level} sum to {total}, not close to 1.0. Using fallback."
                    )
        
        # Fallback to static weights
        self.logger.debug(f"Using static weights for {level}")
        if level == "dimensions":
            return self.DIMENSION_WEIGHTS.copy()
        else:
            # For other levels, we don't have static weights defined yet
            # Return empty dict or uniform distribution based on known counts
            if level == "sub_dimensions":
                # Count total sub-dimensions from our map
                total_sub_dims = sum(len(sub_dims) for sub_dims in [
                    ["price_history", "ohlcv", "corporate_actions"],  # d1
                    ["moving_averages", "momentum", "volatility", "volume", "trend"],  # d2
                    ["news_sentiment", "social_sentiment", "analyst_sentiment"],  # d3
                    ["market_risk", "credit_risk", "operational_risk", "liquidity_risk"],  # d4
                    ["gdp", "inflation", "interest_rates", "exchange_rates", "commodity_prices"],  # d5
                    ["ml_prediction", "pattern_recognition", "anomaly_detection"],  # d6
                    ["current_ratio", "quick_ratio", "cash_ratio", "working_capital"],  # d7
                    ["roe", "roa", "roic", "gross_margin", "net_margin"],  # d8
                    ["asset_turnover", "inventory_turnover", "receivables_turnover"],  # d9
                    ["pe_ratio", "pb_ratio", "peg_ratio", "ev_ebitda"],  # d10
                    ["eps_growth", "revenue_growth", "book_value_growth"],  # d11
                    ["earnings_quality", "accounting_quality", "governance"]   # d12
                ])
                # This should equal 40
                uniform_weight = 1.0 / total_sub_dims if total_sub_dims > 0 else 0.0
                # We'd need to map back to actual names - for now return empty to signal need for ML
                return {}
            elif level in ["aspects", "sub_aspects"]:
                # Similar approach for other levels
                return {}
            else:
                return {}
    
    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform 6D scoring analysis using ML-learned or static weights.
        
        Args:
            data: Input data containing ticker, market, and scores for each dimension.
                Expected format:
                {
                    "ticker": "AAPL",
                    "market": "NASDAQ",
                    "fundamental": {"pe_ratio": 12.5, "roe": 0.15, ...},
                    "technical": {"rsi": 55, "macd": 0.5, ...},
                    ...
                }
                  
        Returns:
            Dictionary containing scores, overall score, grade, and signals
        """
        ticker = data.get("ticker", "UNKNOWN")
        market = data.get("market", "NASDAQ")
        
        scores = {
            "ticker": ticker,
            "market": market,
            "timestamp": utc_now_iso(),
            "dimension_scores": {},
            "overall_score": 0.0,
            "grade": "",
            "signals": [],
        }
        
        # Get dynamic weights for the 6 dimensions (Level 1)
        dimension_weights = self._get_dynamic_weights("dimensions")
        
        # Fallback: if we couldn't get weights (empty dict), use static weights
        if not dimension_weights:
            dimension_weights = self.DIMENSION_WEIGHTS
            self.logger.debug("Using static dimension weights (ML unavailable or not trained)")
        else:
            self.logger.debug("Using ML-derived dimension weights")
        
        # Score each dimension and calculate weighted sum
        weighted_sum = 0.0
        total_weight = sum(dimension_weights.values())
        
        # Normalize weights to sum to 1.0 (in case of any floating point issues)
        if total_weight > 0:
            normalized_weights = {k: v / total_weight for k, v in dimension_weights.items()}
        else:
            normalized_weights = self.DIMENSION_WEIGHTS
        
        for dim in self.DIMENSIONS:  # Use the canonical list for iteration
            dim_data = data.get(dim, {})
            score = await self._score_dimension(dim, dim_data, market)
            # Validate score is within [0, 100] range
            score = max(0.0, min(100.0, score))
            scores["dimension_scores"][dim] = score
            
            # Apply weight (default to 0.0 if dimension not in weights)
            weight = normalized_weights.get(dim, 0.0)
            weighted_sum += score * weight
        
        # Validate overall score is within [0, 100] range
        scores["overall_score"] = round(max(0.0, min(100.0, weighted_sum)), 2)
        scores["grade"] = self._assign_grade(scores["overall_score"])
        scores["signals"] = self._generate_signals(scores["dimension_scores"])
        
        # Cache the dimension scores for potential reuse
        self._scores_cache[ticker] = scores["dimension_scores"]
        
        return scores
    
    # Remaining methods (_score_dimension, _normalize_score, scoring helpers, etc.)
    # remain unchanged from the original implementation
    
    async def _score_dimension(
        self,
        dimension: str,
        data: Dict[str, Any],
        market: str = "NASDAQ"
    ) -> float:
        """Score a 6D dimension using market-aware logic."""
        if not data:
            return 50.0

        scores = []
        for key, value in data.items():
            if isinstance(value, (int, float)):
                normalized = self._normalize_score(value, key, dimension, market)
                scores.append(normalized)

        if not scores:
            return 50.0
        return round(sum(scores) / len(scores), 2)
    
    def _normalize_score(
        self,
        value: float,
        key: str,
        dimension: str,
        market: str
    ) -> float:
        """Normalize raw metric to 0-100 score with market-specific thresholds."""
        
        # Market-specific thresholds
        if market in ("NYSE", "NASDAQ", "AMEX"):
            if dimension == "technical":
                if "rsi" in key:
                    return self._score_rsi_global(value)
                if "macd" in key:
                    return self._score_macd_global(value)
            if dimension == "fundamental":
                if "pe_ratio" in key:
                    return self._score_pe_global(value)
                if "roe" in key:
                    return self._score_roe_global(value)
            if dimension == "technical":
                if "rsi" in key:
                    return self._score_rsi_global(value)
                if "macd" in key:
                    return self._score_macd_global(value)
            if dimension == "fundamental":
                if "pe_ratio" in key:
                    return self._score_pe_global(value)
                if "roe" in key:
                    return self._score_roe_global(value)
        
        # Default generic normalization
        return min(100.0, max(0.0, float(value)))
    
    # ... (remaining scoring helper methods unchanged from original)
    # These are: _score_rsi_global,
    # _score_macd_global, _score_volume_global,
    # _score_pe_global, _score_roe_global,
    # _assign_grade, _generate_signals, score_multiple, rank_stocks, get_hierarchy_info
    
    def _score_rsi_global(self, rsi: float) -> float:
        if rsi > 75:
            return max(0, 100 - (rsi - 75) * 2.5)
        elif rsi < 25:
            return max(0, 100 - (25 - rsi) * 2.5)
        return 50 + (rsi - 50) * 0.5
    
    def _score_macd_global(self, macd: float) -> float:
        return min(100, max(0, 50 + macd * 10))
    
    def _score_pe_global(self, pe: float) -> float:
        if pe <= 0:
            return 0.0
        if pe < 10:
            return 90
        elif pe < 18:
            return 75
        elif pe < 30:
            return 60
        elif pe < 50:
            return 40
        else:
            return max(0, 100 - pe)
    
    def _score_roe_global(self, roe: float) -> float:
        return min(100, max(0, roe * 2))
    
    def _assign_grade(self, score: float) -> str:
        if score >= 85:
            return "STRONG_BULLISH"
        elif score >= 70:
            return "BULLISH"
        elif score >= 55:
            return "NEUTRAL"
        elif score >= 40:
            return "BEARISH"
        else:
            return "STRONG_BEARISH"
    
    def _generate_signals(self, dimension_scores: Dict[str, float]) -> List[str]:
        signals = []
        for dim, score in dimension_scores.items():
            if score >= 80:
                signals.append(f"strong_{dim}")
            elif score >= 60:
                signals.append(f"positive_{dim}")
            elif score <= 20:
                signals.append(f"weak_{dim}")
        return signals
    
    async def score_multiple(self, stocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        tasks = [self.analyze(stock) for stock in stocks]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        processed = []
        for stock, result in zip(stocks, results):
            if isinstance(result, Exception):
                self.logger.error(f"Error scoring {stock.get('ticker')}: {result}")
                processed.append({"error": str(result)})
            else:
                processed.append(result)
        return processed
    
    async def rank_stocks(
        self,
        stocks: List[Dict[str, Any]],
        dimension: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        scored = await self.score_multiple(stocks)
        if dimension:
            scored.sort(key=lambda x: x.get("dimension_scores", {}).get(dimension, 0), reverse=True)
        else:
            scored.sort(key=lambda x: x.get("overall_score", 0), reverse=True)
        return scored[:limit]
    
    def get_hierarchy_info(self) -> Dict[str, Any]:
        level1 = [v for v in self._hierarchy.values() if v.get("level") == 1]
        level2 = [v for v in self._hierarchy.values() if v.get("level") == 2]
        level3 = [v for v in self._hierarchy.values() if v.get("level") == 3]
        level4 = [v for v in self._hierarchy.values() if v.get("level") == 4]
        return {
            "total_nodes": len(self._hierarchy),
            "level1_dimensions": len(level1),
            "level2_subdimensions": len(level2),
            "level3_aspects": len(level3),
            "level4_subaspects": len(level4),
            "dimensions_list": self.DIMENSIONS,
        }