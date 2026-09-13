"""Correlation Service - Tier 7 Specialized Service

Computes a Pearson correlation matrix across symbols from aligned return
series, and surfaces highly-correlated / inversely-correlated pairs.
"""

from typing import Any, Dict, List, Tuple
from ..core import AnalysisService


class CorrelationService(AnalysisService):
    """Computes return correlations across multiple symbols."""

    def __init__(self, service_name: str = "CorrelationService"):
        super().__init__(service_name)

    async def initialize(self) -> None:
        self.logger.info("CorrelationService initialized")

    async def shutdown(self) -> None:
        self.logger.info("CorrelationService shutdown")

    @staticmethod
    def _pearson(a: List[float], b: List[float]) -> float:
        """Pearson correlation coefficient for two equal-length series."""
        n = len(a)
        if n < 2:
            return 0.0
        mean_a = sum(a) / n
        mean_b = sum(b) / n
        cov = sum((a[i] - mean_a) * (b[i] - mean_b) for i in range(n))
        var_a = sum((x - mean_a) ** 2 for x in a)
        var_b = sum((x - mean_b) ** 2 for x in b)
        denom = (var_a * var_b) ** 0.5
        if denom == 0:
            return 0.0
        return cov / denom

    async def compute_correlation(
        self,
        returns_map: Dict[str, List[float]],
        min_observations: int = 2,
        high_threshold: float = 0.7,
        low_threshold: float = -0.7,
    ) -> Dict[str, Any]:
        """
        Build a correlation matrix from per-symbol return series.

        Args:
            returns_map: {symbol: [returns...]} (already time-aligned)
            min_observations: minimum series length to include
            high_threshold: pairs >= this are "highly correlated"
            low_threshold: pairs <= this are "inversely correlated"

        Returns:
            {symbols, matrix, pairs: {high, inverse}, status}
        """
        symbols = [s for s, series in returns_map.items() if len(series) >= min_observations]
        if not symbols:
            return {"status": "empty", "symbols": [], "matrix": {}, "pairs": {"high": [], "inverse": []}}

        series_by_symbol = {s: returns_map[s] for s in symbols}
        # Align all series to the shortest length for fair comparison.
        min_len = min(len(series_by_symbol[s]) for s in symbols)

        matrix: Dict[str, Dict[str, float]] = {}
        for s in symbols:
            matrix[s] = {}
            sa = series_by_symbol[s][:min_len]
            for t in symbols:
                if s == t:
                    matrix[s][t] = 1.0
                else:
                    tb = series_by_symbol[t][:min_len]
                    matrix[s][t] = round(self._pearson(sa, tb), 4)

        high_pairs: List[Dict[str, Any]] = []
        inverse_pairs: List[Dict[str, Any]] = []
        pairs: Dict[Tuple[str, str], float] = {}
        for i, s in enumerate(symbols):
            for t in symbols[i + 1:]:
                corr = matrix[s][t]
                pairs[(s, t)] = corr
                if corr >= high_threshold:
                    high_pairs.append({"a": s, "b": t, "correlation": corr})
                elif corr <= low_threshold:
                    inverse_pairs.append({"a": s, "b": t, "correlation": corr})

        high_pairs.sort(key=lambda p: p["correlation"], reverse=True)
        inverse_pairs.sort(key=lambda p: p["correlation"])

        return {
            "status": "success",
            "observations": min_len,
            "symbols": symbols,
            "matrix": matrix,
            "pairs": {"high": high_pairs, "inverse": inverse_pairs},
        }
