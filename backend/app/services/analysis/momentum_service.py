"""
Momentum Service - Tier 3 Analysis Service

Momentum-based analysis and trading signals.
"""

from typing import Any, Dict, List
from datetime import datetime, timezone
from ..core import AnalysisService


class MomentumService(AnalysisService):
    """
    Momentum analysis service.
    
    Provides:
    - Momentum indicators
    - Trend strength
    - Reversal signals
    - Momentum convergence/divergence
    """
    
    def __init__(self, service_name: str = "MomentumService"):
        """Initialize momentum service"""
        super().__init__(service_name)
    
    async def initialize(self) -> None:
        """Initialize service"""
        self.logger.info("MomentumService initialized")
    
    async def shutdown(self) -> None:
        """Shutdown service"""
        self.logger.info("MomentumService shutdown")
    
    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform momentum analysis"""
        prices = data.get("prices", [])
        
        if len(prices) < 30:
            return {"error": "Insufficient price data"}
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "ticker": data.get("ticker", "UNKNOWN"),
            "momentum": {
                "strength": self._calculate_momentum_strength(prices),
                "direction": self._determine_momentum_direction(prices),
                "acceleration": self._calculate_acceleration(prices),
                "reversal_probability": self._estimate_reversal_probability(prices),
            },
        }
    
    def _calculate_momentum_strength(self, prices: List[float]) -> float:
        """Calculate momentum strength"""
        if len(prices) < 2:
            return 0.0

        recent = prices[-10:]
        historical = prices[-30:-20]

        if not historical:
            return 0.0

        recent_momentum = (recent[-1] - recent[0]) / recent[0] if recent[0] != 0 else 0.0
        hist_momentum = (historical[-1] - historical[0]) / historical[0] if historical[0] != 0 else 0.0
        
        return (recent_momentum - hist_momentum) * 100
    
    def _determine_momentum_direction(self, prices: List[float]) -> str:
        """Determine momentum direction"""
        momentum = self._calculate_momentum_strength(prices)
        
        if momentum > 2:
            return "strong_bullish"
        elif momentum > 0.5:
            return "bullish"
        elif momentum > -0.5:
            return "neutral"
        elif momentum > -2:
            return "bearish"
        else:
            return "strong_bearish"
    
    def _calculate_acceleration(self, prices: List[float]) -> float:
        """Calculate momentum acceleration"""
        if len(prices) < 10:
            return 0.0
        
        m1 = prices[-1] - prices[-5]
        m2 = prices[-5] - prices[-10]
        
        return m1 - m2
    
    def _estimate_reversal_probability(self, prices: List[float]) -> float:
        """Estimate probability of reversal"""
        if len(prices) < 20:
            return 50.0
        
        # Simplified: check extremes
        recent_high = max(prices[-20:])
        recent_low = min(prices[-20:])
        current = prices[-1]
        
        # If at extremes, higher reversal probability
        if current >= recent_high:
            return 60.0
        elif current <= recent_low:
            return 60.0
        else:
            return 40.0
