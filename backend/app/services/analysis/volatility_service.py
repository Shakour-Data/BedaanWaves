"""
Volatility Service - Tier 3 Analysis Service

Volatility analysis and forecasting.
"""

from typing import Any, Dict, List
from datetime import datetime, timezone
import math
from ..core import AnalysisService


class VolatilityService(AnalysisService):
    """
    Volatility analysis service.
    
    Provides:
    - Volatility calculation
    - Volatility forecasting
    - Volatility clusters detection
    - Implied vs realized volatility
    """
    
    def __init__(self, service_name: str = "VolatilityService"):
        """Initialize volatility service"""
        super().__init__(service_name)
    
    async def initialize(self) -> None:
        """Initialize service"""
        self.logger.info("VolatilityService initialized")
    
    async def shutdown(self) -> None:
        """Shutdown service"""
        self.logger.info("VolatilityService shutdown")
    
    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform volatility analysis"""
        prices = data.get("prices", [])
        
        if len(prices) < 20:
            return {"error": "Insufficient price data"}
        
        returns = [
            (prices[i] - prices[i-1]) / prices[i-1]
            for i in range(1, len(prices))
        ]
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "ticker": data.get("ticker", "UNKNOWN"),
            "volatility": {
                "historical": self._calculate_historical_volatility(returns),
                "annualized": self._calculate_annualized_volatility(returns),
                "short_term": self._calculate_short_term_volatility(returns),
                "long_term": self._calculate_long_term_volatility(returns),
                "regime": self._detect_volatility_regime(returns),
            },
        }
    
    def _calculate_historical_volatility(self, returns: List[float]) -> float:
        """Calculate historical volatility"""
        if len(returns) < 2:
            return 0.0
        
        mean = sum(returns) / len(returns)
        variance = sum((r - mean) ** 2 for r in returns) / len(returns)
        return math.sqrt(variance)
    
    def _calculate_annualized_volatility(self, returns: List[float]) -> float:
        """Calculate annualized volatility"""
        hist_vol = self._calculate_historical_volatility(returns)
        return hist_vol * math.sqrt(252)  # 252 trading days
    
    def _calculate_short_term_volatility(self, returns: List[float]) -> float:
        """Calculate short-term volatility (last 5 periods)"""
        short_returns = returns[-5:] if len(returns) >= 5 else returns
        return self._calculate_historical_volatility(short_returns)
    
    def _calculate_long_term_volatility(self, returns: List[float]) -> float:
        """Calculate long-term volatility (20 periods)"""
        long_returns = returns[-20:] if len(returns) >= 20 else returns
        return self._calculate_historical_volatility(long_returns)
    
    def _detect_volatility_regime(self, returns: List[float]) -> str:
        """Detect volatility regime"""
        short_vol = self._calculate_short_term_volatility(returns)
        long_vol = self._calculate_long_term_volatility(returns)
        
        ratio = short_vol / long_vol if long_vol > 0 else 1.0
        
        if ratio > 1.5:
            return "high_volatility"
        elif ratio > 1.1:
            return "elevated_volatility"
        elif ratio < 0.9:
            return "low_volatility"
        else:
            return "normal_volatility"
    
    async def forecast_volatility(
        self,
        historical_volatility: float,
        mean_volatility: float,
        periods: int = 5,
    ) -> List[float]:
        """
        Forecast future volatility.
        
        Args:
            historical_volatility: Current volatility
            mean_volatility: Long-term mean volatility
            periods: Number of periods to forecast
            
        Returns:
            Volatility forecasts
        """
        forecasts = []
        current_vol = historical_volatility
        
        # Mean-reverting volatility model (simplified)
        mean_reversion_speed = 0.1
        
        for _ in range(periods):
            # Move toward mean
            current_vol = (
                current_vol * (1 - mean_reversion_speed) +
                mean_volatility * mean_reversion_speed
            )
            forecasts.append(current_vol)
        
        return forecasts
    
    async def detect_volatility_clusters(
        self,
        returns: List[float],
        threshold: float = 2.0,
    ) -> List[Dict[str, Any]]:
        """
        Detect volatility clusters.
        
        Args:
            returns: Return series
            threshold: Standard deviation threshold
            
        Returns:
            Volatility cluster information
        """
        clusters = []
        if not returns:
            return clusters

        mean = sum(returns) / len(returns)
        std = self._calculate_historical_volatility(returns)
        
        in_cluster = False
        cluster_start = 0
        
        for i, ret in enumerate(returns):
            if abs(ret - mean) > threshold * std:
                if not in_cluster:
                    in_cluster = True
                    cluster_start = i
            else:
                if in_cluster:
                    clusters.append({
                        "start": cluster_start,
                        "end": i,
                        "duration": i - cluster_start,
                    })
                    in_cluster = False
        
        return clusters
