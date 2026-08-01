from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import aiohttp
import numpy as np

from ..core import AnalysisService
from ..core.dependency_container import DependencyContainer
from app.core.config import get_settings

settings = get_settings()


class BehavioralEconomicsService(AnalysisService):
    """Integrate behavioral economics components into regime detection."""

    def __init__(self, service_name: str = "BehavioralEconomicsService"):
        super().__init__(service_name)
        self.session: Optional[aiohttp.ClientSession] = None

    async def initialize(self) -> None:
        """Initialize HTTP session for survey APIs."""
        self.session = aiohttp.ClientSession()
        self.logger.info("BehavioralEconomicsService initialized")

    async def shutdown(self) -> None:
        """Close HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()
        self.logger.info("BehavioralEconomicsService shutdown")

    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Run behavioral economics analysis."""
        market_data = data.get("market_data", {})
        survey_data = data.get("survey_data", {})

        results = {
            "behavioral_index": await self.behavioral_inconsistency_index(market_data, survey_data),
            "noise_trader_risk": await self._noise_trader_risk(market_data),
            "prospect_theory": await self._prospect_theory_weighting(market_data),
            "regime_classifier": await self._behavioral_regime_classifier(market_data),
        }
        return results

    async def behavioral_inconsistency_index(
        self, market_data: Dict[str, Any], survey_data: Dict[str, Any]
    ) -> float:
        """Behavioral Inconsistency Index: Survey data vs market data divergence."""
        market_sentiment = market_data.get("sentiment", 0.0)
        survey_expectation = survey_data.get("expectation", 0.0)
        divergence = abs(market_sentiment - survey_expectation)
        normalized = min(1.0, divergence / 0.5)
        self.logger.info("Behavioral inconsistency index: %.3f", normalized)
        return normalized

    async def _noise_trader_risk(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """NoiseTrader Risk assessment using volatility clustering and volume spikes."""
        volatility = market_data.get("volatility", [])
        volume = market_data.get("volume", [])

        if not volatility or len(volatility) < 10:
            return {"noise_risk": 0.0, "confidence": 0.0}

        # Volatility clustering (ARCH test proxy)
        arch_stat = np.std(np.diff(volatility))

        # Volume spike detection
        mean_vol = np.mean(volume[-10:]) if volume else 0
        recent_vol = volume[-1] if volume else 0
        volume_spike = recent_vol / mean_vol if mean_vol > 0 else 0

        # Combine signals
        noise_risk = min(1.0, (arch_stat * 0.3 + max(0, volume_spike - 1) * 0.7))

        return {
            "noise_risk": float(noise_risk),
            "volatility_clustering": float(arch_stat),
            "volume_spike_ratio": float(volume_spike),
            "confidence": 0.9 if noise_risk > 0.5 else 0.6,
        }

    async def _prospect_theory_weighting(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prospect Theory value function asymmetry in risk metrics."""
        returns = market_data.get("returns", [])

        if not returns or len(returns) < 5:
            return {"value_function_asymmetry": 0.0}

        gains = [r for r in returns if r > 0]
        losses = [r for r in returns if r <= 0]

        if not gains or not losses:
            return {"value_function_asymmetry": 0.0}

        # Kahneman-Tversky value function parameters
        alpha = 0.88  # Diminishing sensitivity for gains
        beta = 0.88   # Diminishing sensitivity for losses
        lambda_kt = 2.25  # Loss aversion

        # Calculate weighted values
        gain_sum = sum(abs(g) ** alpha for g in gains) / len(gains)
        loss_sum = sum(abs(l) ** beta for l in losses) * lambda_kt / len(losses)

        asymmetry = (loss_sum - gain_sum) / (loss_sum + gain_sum + 0.001)

        return {
            "value_function_asymmetry": float(asymmetry),
            "loss_aversion_ratio": float(loss_sum / (gain_sum + 0.001)),
            "gain_count": len(gains),
            "loss_count": len(losses),
        }

    async def _behavioral_regime_classifier(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Behavioral regime classifier as ensemble model."""
        noise_risk = await self._noise_trader_risk(market_data)
        sentiment = market_data.get("sentiment", 0.0)
        volatility = market_data.get("volatility", [0])

        vol_level = np.mean(volatility[-10:]) if len(volatility) >= 10 else (volatility[-1] if volatility else 0)

        # Determine regime
        if sentiment > 0.7 and noise_risk["noise_risk"] > 0.6:
            regime = "irrational_exuberance"
            confidence = 0.92
        elif sentiment < -0.6 and noise_risk["noise_risk"] > 0.5:
            regime = "panic_selling"
            confidence = 0.88
        elif noise_risk["noise_risk"] > 0.7:
            regime = "noise_dominated"
            confidence = 0.75
        elif vol_level > 0.02:
            regime = "high_volatility"
            confidence = 0.65
        else:
            regime = "normal"
            confidence = 0.80

        return {
            "regime": regime,
            "confidence": float(confidence),
            "components": {
                "sentiment": float(sentiment),
                "noise_risk": float(noise_risk["noise_risk"]),
                "volatility": float(vol_level),
            },
        }

    async def fetch_survey_data(self, source: str = "umich") -> Dict[str, Any]:
        """Fetch survey data from University of Michigan or ECB Survey."""
        endpoints = {
            "umich": "https://api.bls.gov/publicAPI/v1/data/SURVEY_UMICH",
            "ecb": "https://sdw-wsrest.ecb.europa.eu/service/data/ECS",
        }
        url = endpoints.get(source)
        if not url or not self.session:
            return {"error": f"Invalid survey source: {source}"}

        try:
            async with self.session.get(url, timeout=30) as response:
                if response.status == 200:
                    return await response.json()
                return {"error": f"Survey API returned {response.status}"}
        except Exception as e:
            self.logger.warning("Failed to fetch survey data from %s: %s", source, str(e))
            return {"error": str(e)}


DependencyContainer.register("BehavioralEconomicsService", BehavioralEconomicsService)