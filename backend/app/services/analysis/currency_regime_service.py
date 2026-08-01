from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timezone
import numpy as np
import random

from ..core import AnalysisService
from ..core.dependency_container import get_global_container


class CurrencyRegimeClassifier(AnalysisService):
    """Explicit currency regime modeling with 4-state Markov model."""

    # Regime types
    HARD_PEG = "hard_peg"
    SOFT_PEG = "soft_peg"
    FREE_FLOAT = "free_float"
    BASKET_PEG = "basket_peg"

    REGIMES = [HARD_PEG, SOFT_PEG, FREE_FLOAT, BASKET_PEG]

    def __init__(self, service_name: str = "CurrencyRegimeClassifier"):
        super().__init__(service_name)
        # Transition matrix initialized with reasonable priors
        self.transition_matrix = self._init_transition_matrix()
        self.currency_regimes: Dict[str, str] = {}

    def _init_transition_matrix(self) -> np.ndarray:
        """Initialize 4x4 transition matrix with domain priors."""
        # Rows = from, Cols = to
        # Hard peg: stays pegged 99%, rarely moves to soft peg
        # Soft peg: can move to hard, free float, or basket
        # Free float: mostly stays, occasionally managed
        # Basket: can move to soft or free float
        return np.array([
            [0.98, 0.01, 0.005, 0.005],  # hard_peg
            [0.02, 0.90, 0.05, 0.03],    # soft_peg
            [0.005, 0.03, 0.95, 0.015],  # free_float
            [0.01, 0.04, 0.05, 0.90],    # basket_peg
        ])

    async def initialize(self) -> None:
        self.logger.info("CurrencyRegimeClassifier initialized with 4-state Markov model")

    async def shutdown(self) -> None:
        self.logger.info("CurrencyRegimeClassifier shutdown")

    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Classify currency regimes and calculate transition probabilities."""
        currencies = data.get("currencies", ["USD", "EUR", "CNY", "JPY", "GBP"])
        results = {}

        for currency in currencies:
            regime = await self.classify_currency(currency, data.get(currency, {}))
            results[currency] = {
                "regime": regime,
                "adjustment_factor": self._regime_adjustment_factor(regime),
                "pressure_indicator": await self._currency_pressure(currency, data),
            }

        # Add transition matrix
        results["transition_matrix"] = self.transition_matrix.tolist()
        results["regimes"] = self.REGIMES

        return results

    async def classify_currency(self, currency: str, currency_data: Dict[str, Any]) -> str:
        """Classify a currency into one of 4 regimes."""
        # Use volatility, reserves, policy statements
        volatility = currency_data.get("fx_volatility", 0.01)
        reserve_change = currency_data.get("reserve_change_pct", 0.0)
        intervention = currency_data.get("intervention_frequency", 0)

        if currency == "USD" or currency == "HKD":
            return self.HARD_PEG
        elif currency == "CNY":
            return self.SOFT_PEG
        elif currency in ["EUR", "JPY", "GBP", "AUD", "CAD"]:
            return self.FREE_FLOAT
        elif currency in ["SGD", "KWD"]:
            return self.BASKET_PEG
        else:
            # Heuristic classification
            if volatility < 0.005 and intervention > 10:
                return self.HARD_PEG
            elif volatility < 0.02 and reserve_change > 0.05:
                return self.SOFT_PEG
            elif volatility > 0.05:
                return self.FREE_FLOAT
            else:
                return self.BASKET_PEG

    def _regime_adjustment_factor(self, regime: str) -> float:
        """Get regime-specific inflation adjustment factor."""
        factors = {
            self.HARD_PEG: 0.5,      # Lower volatility weight
            self.SOFT_PEG: 0.75,
            self.BASKET_PEG: 0.85,
            self.FREE_FLOAT: 1.0,    # Full volatility weight
        }
        return factors.get(regime, 1.0)

    async def _currency_pressure(self, currency: str, data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate currency pressure indicator: capital flight, reserve depletion, peg pressure."""
        capital_flight = data.get(f"{currency}_capital_flight", 0.0)
        reserve_depletion = data.get(f"{currency}_reserve_depletion", 0.0)
        peg_pressure = data.get(f"{currency}_peg_pressure", 0.0)

        # Composite pressure index
        pressure = (capital_flight * 0.4 + reserve_depletion * 0.4 + peg_pressure * 0.2)

        return {
            "composite_pressure": float(pressure),
            "capital_flight": float(capital_flight),
            "reserve_depletion": float(reserve_depletion),
            "peg_pressure": float(peg_pressure),
            "risk_level": "high" if pressure > 0.7 else "moderate" if pressure > 0.4 else "low",
        }

    def get_transition_probabilities(self, from_regime: str) -> Dict[str, float]:
        """Get transition probabilities from a given regime."""
        idx = self.REGIMES.index(from_regime)
        return {r: float(self.transition_matrix[idx, i]) for i, r in enumerate(self.REGIMES)}

    def simulate_regime_path(self, start_regime: str, steps: int = 12) -> List[str]:
        """Simulate regime transitions over time."""
        path = [start_regime]
        current = start_regime
        for _ in range(steps):
            probs = self.get_transition_probabilities(current)
            current = np.random.choice(self.REGIMES, p=list(probs.values()))
            path.append(current)
        return path


get_global_container().register("CurrencyRegimeClassifier", CurrencyRegimeClassifier, singleton=True)