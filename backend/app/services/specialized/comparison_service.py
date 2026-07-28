"""Comparison Service - Tier 7 Specialized Service

Compares multiple symbols across shared metrics and produces relative
rankings, highlighting the best/worst performer in each dimension.
"""

from typing import Any, Dict, List, Optional
from ..core import AnalysisService


class ComparisonService(AnalysisService):
    """Compares multiple symbols across a set of normalized metrics."""

    def __init__(self, service_name: str = "ComparisonService"):
        super().__init__(service_name)

    async def initialize(self) -> None:
        self.logger.info("ComparisonService initialized")

    async def shutdown(self) -> None:
        self.logger.info("ComparisonService shutdown")

    async def compare(self, symbols_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Compare symbols across available metrics.

        Each record may contain: symbol, name, score, change_pct,
        volatility, momentum, risk_score, expected_return.

        Returns:
            {symbols: [...], rankings: {...}, best: {...}, worst: {...}}
        """
        if not symbols_data:
            return {"symbols": [], "rankings": {}, "best": {}, "worst": {}}

        records = []
        for s in symbols_data:
            records.append({
                "symbol": s.get("symbol", "UNKNOWN"),
                "name": s.get("name", s.get("symbol", "UNKNOWN")),
                "score": self._to_float(s.get("score")),
                "change_pct": self._to_float(s.get("change_pct")),
                "volatility": self._to_float(s.get("volatility")),
                "momentum": self._to_float(s.get("momentum")),
                "risk_score": self._to_float(s.get("risk_score")),
                "expected_return": self._to_float(s.get("expected_return")),
            })

        metric_keys = ["score", "change_pct", "volatility", "momentum", "risk_score", "expected_return"]
        rankings: Dict[str, Dict[str, Any]] = {}

        for key in metric_keys:
            values = [(r["symbol"], r[key]) for r in records if r[key] is not None]
            if not values:
                rankings[key] = {"available": False, "best": None, "worst": None, "order": []}
                continue

            # Higher is "best" for all metrics except volatility & risk_score,
            # where lower is better.
            higher_is_better = key not in ("volatility", "risk_score")
            ordered = sorted(values, key=lambda x: x[1], reverse=higher_is_better)
            rankings[key] = {
                "available": True,
                "higher_is_better": higher_is_better,
                "best": {"symbol": ordered[0][0], "value": ordered[0][1]},
                "worst": {"symbol": ordered[-1][0], "value": ordered[-1][1]},
                "order": [{"symbol": sym, "value": val} for sym, val in ordered],
            }

        best: Dict[str, str] = {}
        worst: Dict[str, str] = {}
        for key, r in rankings.items():
            if r.get("available"):
                best[key] = r["best"]["symbol"]
                worst[key] = r["worst"]["symbol"]

        return {
            "status": "success",
            "count": len(records),
            "symbols": records,
            "rankings": rankings,
            "best": best,
            "worst": worst,
        }

    @staticmethod
    def _to_float(value: Any) -> Optional[float]:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
