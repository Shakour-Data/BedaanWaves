"""
Risk Analysis Service - Tier 3 Analysis Service

Risk assessment and portfolio risk analysis.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import math
from ..core import AnalysisService


class RiskAnalysisService(AnalysisService):
    """
    Risk analysis service.
    
    Provides:
    - Value at Risk (VaR)
    - Beta calculation
    - Volatility analysis
    - Sharpe ratio
    - Correlation analysis
    - Stress testing
    """
    
    def __init__(self, service_name: str = "RiskAnalysisService"):
        """Initialize risk analysis service"""
        super().__init__(service_name)
    
    async def initialize(self) -> None:
        """Initialize service"""
        self.logger.info("RiskAnalysisService initialized")
    
    async def shutdown(self) -> None:
        """Shutdown service"""
        self.logger.info("RiskAnalysisService shutdown")
    
    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform risk analysis.
        
        Args:
            data: Price and returns data
            
        Returns:
            Risk metrics
        """
        returns = data.get("returns", [])
        prices = data.get("prices", [])
        
        if not returns or len(returns) < 20:
            return {"error": "Insufficient return data"}
        
        analysis = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "ticker": data.get("ticker", "UNKNOWN"),
            "metrics": {},
        }
        
        # Calculate risk metrics
        analysis["metrics"].update(
            await self._calculate_volatility_metrics(returns, data)
        )
        analysis["metrics"].update(
            await self._calculate_value_at_risk(returns)
        )
        analysis["metrics"].update(
            await self._calculate_performance_metrics(returns)
        )
        
        return analysis
    
    async def _calculate_volatility_metrics(self, returns: List[float], data: Optional[Dict[str, Any]] = None) -> Dict[str, float]:
        """Calculate volatility metrics"""
        volatility = self._calculate_std_dev(returns)
        beta = data.get("beta", 1.0) if data else 1.0
        
        return {
            "volatility": volatility,
            "annual_volatility": volatility * math.sqrt(252),  # 252 trading days
            "beta": beta,
        }
    
    async def _calculate_value_at_risk(self, returns: List[float]) -> Dict[str, float]:
        """Calculate Value at Risk"""
        if not returns:
            return {"var_95": 0.0, "var_99": 0.0, "cvar_95": 0.0}

        sorted_returns = sorted(returns)
        n = len(sorted_returns)
        
        idx_95 = max(0, int(n * 0.05) - 1)
        idx_99 = max(0, int(n * 0.01) - 1)
        
        var_95 = sorted_returns[idx_95]
        var_99 = sorted_returns[idx_99]
        
        cvar_count = max(1, int(n * 0.05))
        cvar_95 = sum(sorted_returns[:cvar_count]) / cvar_count
        
        return {
            "var_95": var_95 * 100,
            "var_99": var_99 * 100,
            "cvar_95": cvar_95 * 100,
        }
    
    async def _calculate_performance_metrics(self, returns: List[float]) -> Dict[str, float]:
        """Calculate performance metrics"""
        mean_return = sum(returns) / len(returns)
        volatility = self._calculate_std_dev(returns)
        
        return {
            "mean_return": mean_return * 100,
            "sharpe_ratio": (mean_return / volatility) if volatility > 0 else 0,
            "max_drawdown": self._calculate_max_drawdown(returns),
            "sortino_ratio": self._calculate_sortino_ratio(returns),
        }
    
    def _calculate_std_dev(self, values: List[float]) -> float:
        """Standard deviation"""
        if not values or len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return math.sqrt(variance)
    
    def _calculate_max_drawdown(self, returns: List[float]) -> float:
        """Maximum drawdown"""
        if not returns:
            return 0.0
        
        cumulative = 1.0
        peak = 1.0
        max_dd = 0.0
        
        for ret in returns:
            cumulative *= (1 + ret)
            if cumulative > peak:
                peak = cumulative
            drawdown = (peak - cumulative) / peak
            if drawdown > max_dd:
                max_dd = drawdown
        
        return max_dd * 100
    
    def _calculate_sortino_ratio(self, returns: List[float]) -> float:
        """Sortino ratio (downside volatility focused)"""
        mean_return = sum(returns) / len(returns)
        
        downside_returns = [r for r in returns if r < 0]
        if not downside_returns:
            return 0.0
        
        downside_volatility = self._calculate_std_dev(downside_returns)
        
        return (mean_return / downside_volatility) if downside_volatility > 0 else 0
    
    async def calculate_portfolio_risk(
        self,
        weights: Dict[str, float],
        correlations: Dict[str, float],
        volatilities: Dict[str, float],
    ) -> Dict[str, Any]:
        """
        Calculate portfolio risk.
        
        Args:
            weights: Portfolio weights {ticker: weight}
            correlations: Asset correlations
            volatilities: Asset volatilities
            
        Returns:
            Portfolio risk metrics
        """
        # Calculate portfolio variance with correlations
        portfolio_var = 0.0
        tickers = list(weights.keys())
        
        for i, ticker_i in enumerate(tickers):
            w_i = weights[ticker_i]
            vol_i = volatilities.get(ticker_i, 0.0)
            
            for j, ticker_j in enumerate(tickers):
                w_j = weights[ticker_j]
                vol_j = volatilities.get(ticker_j, 0.0)
                corr = correlations.get(f"{ticker_i}_{ticker_j}", 1.0 if i == j else 0.0)
                
                portfolio_var += w_i * w_j * vol_i * vol_j * corr
        
        return {
            "portfolio_volatility": math.sqrt(portfolio_var) if portfolio_var > 0 else 0.0,
            "portfolio_var_95": math.sqrt(portfolio_var) * 1.645 if portfolio_var > 0 else 0.0,
            "portfolio_var_99": math.sqrt(portfolio_var) * 2.326 if portfolio_var > 0 else 0.0,
        }
    
    async def stress_test(
        self,
        portfolio: Dict[str, float],
        scenarios: List[Dict[str, float]],
    ) -> List[Dict[str, Any]]:
        """
        Stress test portfolio under scenarios.
        
        Args:
            portfolio: Portfolio {ticker: position_value}
            scenarios: Stress scenarios {ticker: price_change}
            
        Returns:
            Stress test results
        """
        results = []
        
        for scenario in scenarios:
            portfolio_value = 0.0
            
            for ticker, position in portfolio.items():
                change = scenario.get(ticker, 0.0)
                new_value = position * (1 + change)
                portfolio_value += new_value
            
            results.append({
                "scenario": scenario,
                "portfolio_value": portfolio_value,
                "loss": sum(portfolio.values()) - portfolio_value,
            })
        
        return results
