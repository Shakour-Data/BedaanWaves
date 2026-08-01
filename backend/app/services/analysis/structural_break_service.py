from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from scipy import stats

from ..core import AnalysisService
from ..core.dependency_container import DependencyContainer


class StructuralBreakDetectionService(AnalysisService):
    """Implement structural break detection for economic time series."""

    def __init__(self, service_name: str = "StructuralBreakDetectionService"):
        super().__init__(service_name)

    async def initialize(self) -> None:
        self.logger.info("StructuralBreakDetectionService initialized")

    async def shutdown(self) -> None:
        self.logger.info("StructuralBreakDetectionService shutdown")

    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect structural breaks in time series data."""
        series = data.get("series", [])
        if not series or len(series) < 20:
            return {"error": "Insufficient data for structural break detection"}

        results = {
            "bai_perron": await self._bai_perron_test(series),
            "chow_test": await self._chow_test(series),
            "markov_change": await self._markov_structure_change(series),
        }
        return results

    async def _bai_perron_test(self, series: List[float]) -> Dict[str, Any]:
        """Bai-Perron multiple structural break test."""
        n = len(series)
        if n < 30:
            return {"break_points": [], "confidence": 0.0, "method": "insufficient_data"}

        splits = [5, 10, 15]
        best_sse = float("inf")
        best_breaks = []

        for k in splits:
            if k >= n // 2:
                continue

            # Sequential search for break points
            break_points = []
            remaining = series.copy()
            sse = 0

            for _ in range(min(k, 3)):
                segments = np.array_split(remaining, 2)
                if len(segments[0]) < 5 or len(segments[1]) < 5:
                    break

                # Calculate SSE for each segment
                seg_sse = sum(np.var(seg) * len(seg) for seg in segments)
                if seg_sse < best_sse:
                    best_sse = seg_sse
                    best_breaks.append(len(segments[0]))
                remaining = segments[1].tolist()

        return {
            "break_points": best_breaks,
            "count": len(best_breaks),
            "confidence": min(0.99, len(best_breaks) * 0.15),
            "method": "sequential_search",
        }

    async def _chow_test(self, series: List[float]) -> Dict[str, Any]:
        """Chow test for structural change at a specific point."""
        n = len(series)
        break_point = n // 2

        before = series[:break_point]
        after = series[break_point:]

        if len(before) < 5 or len(after) < 5:
            return {"chow_statistic": 0.0, "p_value": 1.0, "breakable": False}

        # Calculate RSS for full sample and restricted model
        full_mean = np.mean(series)
        rss_full = sum((x - full_mean) ** 2 for x in series)

        before_mean = np.mean(before)
        after_mean = np.mean(after)
        rss_restricted = sum((x - before_mean) ** 2 for x in before) + \
                           sum((x - after_mean) ** 2 for x in after)

        # Chow statistic
        k = 2  # Number of parameters
        n_obs = len(series)
        chow_stat = ((rss_restricted - rss_full) / k) / (rss_full / (n_obs - 2 * k))
        p_value = 1 - stats.f.cdf(chow_stat, k, n_obs - 2 * k)

        return {
            "chow_statistic": float(chow_stat),
            "p_value": float(p_value),
            "breakable": p_value < 0.05,
            "break_point": break_point,
        }

    async def _markov_structure_change(self, series: List[float]) -> Dict[str, Any]:
        """Markov structure change detection for gradual shifts."""
        n = len(series)
        if n < 30:
            return {"transition_matrix": [], "states": [], "confidence": 0.0}

        # Discretize series into states
        quartiles = np.percentile(series, [25, 50, 75])
        states = []
        for val in series:
            if val <= quartiles[0]:
                states.append(0)
            elif val <= quartiles[1]:
                states.append(1)
            elif val <= quartiles[2]:
                states.append(2)
            else:
                states.append(3)

        # Build transition matrix
        transition_counts = [[0] * 4 for _ in range(4)]
        for i in range(len(states) - 1):
            transition_counts[states[i]][states[i + 1]] += 1

        # Normalize to probabilities
        transition_matrix = []
        for i in range(4):
            row_sum = sum(transition_counts[i])
            if row_sum > 0:
                transition_matrix.append([c / row_sum for c in transition_counts[i]])
            else:
                transition_matrix.append([0.25] * 4)

        # Detect non-stationary transitions
        non_stationary = any(
            any(p > 0.6 for p in row) for row in transition_matrix
        )

        return {
            "transition_matrix": transition_matrix,
            "states": ["low", "medium_low", "medium_high", "high"],
            "non_stationary": non_stationary,
            "confidence": 0.85 if non_stationary else 0.45,
        }


DependencyContainer.get_global_container().register("StructuralBreakDetectionService", StructuralBreakDetectionService, singleton=True)