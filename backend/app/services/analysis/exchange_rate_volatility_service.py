from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import numpy as np

from ..core import AnalysisService
from ..core.dependency_container import DependencyContainer


class ExchangeRateVolatilityService(AnalysisService):
    """Size-normalized exchange rate volatility metrics."""

    def __init__(self, service_name: str = "ExchangeRateVolatilityService"):
        super().__init__(service_name)
        self.benchmark_db: Dict[str, Dict[str, float]] = {}

    async def initialize(self) -> None:
        """Initialize volatility benchmarks indexed by GDP per capita."""
        # Volatility benchmarks by economy size buckets
        self.benchmark_db = {
            "mega": {"gdp_pc_range": (50000, float("inf")), "volatility_benchmark": 0.08},
            "large": {"gdp_pc_range": (20000, 50000), "volatility_benchmark": 0.12},
            "medium": {"gdp_pc_range": (5000, 20000), "volatility_benchmark": 0.18},
            "small": {"gdp_pc_range": (1000, 5000), "volatility_benchmark": 0.25},
            "tiny": {"gdp_pc_range": (0, 1000), "volatility_benchmark": 0.35},
        }
        self.logger.info("ExchangeRateVolatilityService initialized")

    async def shutdown(self) -> None:
        self.logger.info("ExchangeRateVolatilityService shutdown")

    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate size-normalized volatility metrics."""
        return {
            "volatility_per_gdp": await self._volatility_per_gdp(data),
            "fisher_information": await self._fisher_information_metric(data),
            "real_exchange_rate_vol": await self._real_exchange_rate_volatility(data),
            "benchmark_comparison": await self._benchmark_comparison(data),
        }

    async def _volatility_per_gdp(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Create volatility per Unit of GDP: σ(exchange) / GDP per capita."""
        exchange_rates = data.get("exchange_rates", [])
        gdp_per_capita = data.get("gdp_per_capita", 50000)

        if not exchange_rates or len(exchange_rates) < 5:
            return {"volatility_gdp_ratio": 0.0, "error": "Insufficient data"}

        volatility = np.std(exchange_rates)
        vol_gdp_ratio = volatility / max(gdp_per_capita, 1)

        return {
            "volatility_gdp_ratio": float(vol_gdp_ratio),
            "raw_volatility": float(volatility),
            "gdp_per_capita": float(gdp_per_capita),
        }

    async def _fisher_information_metric(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Convert nominal volatility to Fisher Information content."""
        exchange_rates = data.get("exchange_rates", [])

        if not exchange_rates or len(exchange_rates) < 10:
            return {"fisher_info": 0.0, "error": "Insufficient data"}

        # Fisher information for location parameter
        # I(θ) = n/σ² for normal distribution
        n = len(exchange_rates)
        sigma_sq = np.var(exchange_rates)

        if sigma_sq == 0:
            return {"fisher_info": 0.0}

        fisher_info = n / sigma_sq

        # Normalize by sqrt of volatility for interpretability
        normalized_info = np.sqrt(fisher_info) / (np.std(exchange_rates) + 0.001)

        return {
            "fisher_info": float(fisher_info),
            "normalized_info": float(normalized_info),
            "interpretation": "High information content" if normalized_info > 10 else "Low information content",
        }

    async def _real_exchange_rate_volatility(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate Real Exchange Rate Volatility adjusted for trade balance."""
        exchange_rate = data.get("exchange_rate", 1.0)
        domestic_price = data.get("domestic_price_index", 100.0)
        foreign_price = data.get("foreign_price_index", 100.0)
        trade_balance = data.get("trade_balance", 0.01)  # Ratio of exports/imports

        # Real Exchange Rate = E × P_domestic / P_foreign
        rer = exchange_rate * (domestic_price / (foreign_price + 0.001))

        # Adjust for trade balance effects
        rer_adjusted = rer * (1 + abs(trade_balance))

        return {
            "rer": float(rer),
            "rer_adjusted": float(rer_adjusted),
            "trade_balance_factor": float(1 + abs(trade_balance)),
        }

    async def _benchmark_comparison(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Compare volatility against benchmark database indexed by GDP per capita."""
        gdp_per_capita = data.get("gdp_per_capita", 50000)
        exchange_rates = data.get("exchange_rates", [])

        if not exchange_rates:
            return {"error": "No volatility data"}

        measured_vol = float(np.std(exchange_rates))

        # Find appropriate bucket
        bucket = "medium"  # default
        for name, info in self.benchmark_db.items():
            low, high = info["gdp_pc_range"]
            if low <= gdp_per_capita < high:
                bucket = name
                break

        benchmark = self.benchmark_db[bucket]["volatility_benchmark"]
        ratio = measured_vol / benchmark if benchmark > 0 else 1.0

        return {
            "bucket": bucket,
            "benchmark": benchmark,
            "actual_volatility": measured_vol,
            "ratio_to_benchmark": float(ratio),
            "relative_position": "above" if ratio > 1.2 else "below" if ratio < 0.8 else "at",
        }


DependencyContainer.register("ExchangeRateVolatilityService", ExchangeRateVolatilityService)