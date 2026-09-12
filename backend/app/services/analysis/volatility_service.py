"""
Volatility Service - Tier 3 Analysis Service

Volatility analysis and forecasting.
"""

import math
from typing import Any

from app.core.utils import utc_now_iso

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

    async def analyze(self, data: dict[str, Any]) -> dict[str, Any]:
        """Perform volatility analysis"""
        prices = data.get("prices", [])

        if len(prices) < 20:
            return {"error": "Insufficient price data"}

        returns = [
            (prices[i] - prices[i - 1]) / prices[i - 1]
            for i in range(1, len(prices))
        ]

        return {
            "timestamp": utc_now_iso(),
            "ticker": data.get("ticker", "UNKNOWN"),
            "volatility": {
                "historical": self._calculate_historical_volatility(returns),
                "annualized": self._calculate_annualized_volatility(returns),
                "short_term": self._calculate_short_term_volatility(returns),
                "long_term": self._calculate_long_term_volatility(returns),
                "regime": self._detect_volatility_regime(returns),
            },
        }

    def _calculate_historical_volatility(self, returns: list[float]) -> float:
        """Calculate historical volatility"""
        if len(returns) < 2:
            return 0.0

        mean = sum(returns) / len(returns)
        variance = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
        return math.sqrt(variance)

    def _calculate_annualized_volatility(self, returns: list[float]) -> float:
        """Calculate annualized volatility"""
        hist_vol = self._calculate_historical_volatility(returns)
        return hist_vol * math.sqrt(252)  # 252 trading days

    def _calculate_short_term_volatility(self, returns: list[float]) -> float:
        """Calculate short-term volatility (last 5 periods)"""
        short_returns = returns[-5:] if len(returns) >= 5 else returns
        return self._calculate_historical_volatility(short_returns)

    def _calculate_long_term_volatility(self, returns: list[float]) -> float:
        """Calculate long-term volatility (20 periods)"""
        long_returns = returns[-20:] if len(returns) >= 20 else returns
        return self._calculate_historical_volatility(long_returns)

    def _detect_volatility_regime(self, returns: list[float]) -> str:
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
    ) -> list[float]:
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
        returns: list[float],
        threshold: float = 2.0,
    ) -> list[dict[str, Any]]:
        """
        Detect volatility clusters.

        Args:
            returns: Return series
            threshold: Standard deviation threshold

        Returns:
            Volatility cluster information
        """
        clusters: list[dict[str, Any]] = []
        if not returns:
            return clusters

    async def sensitivity_analysis(
        self,
        returns: list[float],
        parameter: str = "window",
        window_sizes: list[int] | None = None,
    ) -> dict[str, Any]:
        """
        Perform sensitivity analysis on volatility estimates.

        Measures how volatility estimates vary with the lookback window,
        providing confidence intervals for the volatility estimate.
        Reference: Mandelbrot, B. (1963). "The Variation of Certain
        Speculative Prices."

        Args:
            returns: Return series
            parameter: Parameter to vary ('window' or 'ddof')
            window_sizes: List of window sizes to test

        Returns:
            Dictionary with sensitivity results including mean, std, min, max,
            and confidence intervals for each parameter value.
        """
        if not returns or len(returns) < 2:
            return {"status": "insufficient_data", "results": {}}

        if window_sizes is None:
            window_sizes = [5, 10, 20, 30, 60, min(126, len(returns))]

        window_sizes = [w for w in window_sizes if 2 <= w <= len(returns)]
        results = {}
        vol_values = []

        for w in window_sizes:
            window_returns = returns[-w:]
            vol = self._calculate_historical_volatility(window_returns)
            vol_annualized = vol * math.sqrt(252)
            vol_values.append(vol_annualized)
            results[w] = {
                "volatility": round(vol_annualized, 6),
                "window_size": w,
            }

        if len(vol_values) >= 2:
            mean_vol = sum(vol_values) / len(vol_values)
            std_vol = math.sqrt(sum((v - mean_vol) ** 2 for v in vol_values) / (len(vol_values) - 1))
            z_95 = 1.96
            results["summary"] = {
                "mean": round(mean_vol, 6),
                "std": round(std_vol, 6),
                "min": round(min(vol_values), 6),
                "max": round(max(vol_values), 6),
                "ci_95_lower": round(mean_vol - z_95 * std_vol, 6),
                "ci_95_upper": round(mean_vol + z_95 * std_vol, 6),
                "parameter_tested": parameter,
            }
        else:
            results["summary"] = {"error": "Not enough data for sensitivity analysis"}

        return {"status": "success", "results": results}

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
