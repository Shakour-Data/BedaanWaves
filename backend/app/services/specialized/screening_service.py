"""Screening Service - Tier 7 Specialized Service

Filters a stock universe by flexible criteria and ranks matches.

Supported criteria (all optional):
- min_score / max_score        : 0-100 overall 6D score bounds
- min_price / max_price        : price bounds
- min_change / max_change      : daily change percent bounds
- sectors                      : list of allowed sector names
- asset_class                  : single asset class filter
- min_volume / max_volume      : traded volume bounds
- signals                      : list of allowed signal types (BUY, SELL, HOLD, ...)
- min_momentum                 : minimum absolute momentum
"""

from typing import Any, Dict, List, Optional
from ..core import AnalysisService


class ScreeningService(AnalysisService):
    """Filters a stock universe against configurable criteria."""

    def __init__(self, service_name: str = "ScreeningService"):
        super().__init__(service_name)

    async def initialize(self) -> None:
        self.logger.info("ScreeningService initialized")

    async def shutdown(self) -> None:
        self.logger.info("ScreeningService shutdown")

    async def screen(
        self,
        universe: List[Dict[str, Any]],
        criteria: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Screen a universe of stocks against criteria.

        Args:
            universe: List of stock records
            criteria: Optional filter dict (see module docstring)

        Returns:
            {total, matched, criteria, results: [...]}
        """
        criteria = criteria or {}
        results: List[Dict[str, Any]] = []

        for stock in universe:
            if self._passes(stock, criteria):
                match = self._match_record(stock, criteria)
                results.append(match)

        # Rank by match strength (descending)
        results.sort(key=lambda r: r.get("match_score", 0.0), reverse=True)

        return {
            "status": "success",
            "total": len(universe),
            "matched": len(results),
            "criteria": criteria,
            "results": results,
        }

    def _passes(self, stock: Dict[str, Any], criteria: Dict[str, Any]) -> bool:
        """Return True if a stock satisfies all provided criteria."""
        score = stock.get("score")
        if score is not None:
            if "min_score" in criteria and float(score) < float(criteria["min_score"]):
                return False
            if "max_score" in criteria and float(score) > float(criteria["max_score"]):
                return False

        price = stock.get("price")
        if price is not None:
            if "min_price" in criteria and float(price) < float(criteria["min_price"]):
                return False
            if "max_price" in criteria and float(price) > float(criteria["max_price"]):
                return False

        change = stock.get("change_pct", 0.0)
        if "min_change" in criteria and float(change) < float(criteria["min_change"]):
            return False
        if "max_change" in criteria and float(change) > float(criteria["max_change"]):
            return False

        if "min_momentum" in criteria and abs(float(change)) < float(criteria["min_momentum"]):
            return False

        if "sectors" in criteria:
            allowed = {str(s).upper() for s in criteria["sectors"]}
            if str(stock.get("sector", "")).upper() not in allowed:
                return False

        if "asset_class" in criteria:
            if str(stock.get("asset_class", "")).upper() != str(criteria["asset_class"]).upper():
                return False

        volume = stock.get("volume")
        if volume is not None:
            if "min_volume" in criteria and int(volume) < int(criteria["min_volume"]):
                return False
            if "max_volume" in criteria and int(volume) > int(criteria["max_volume"]):
                return False

        if "signals" in criteria:
            allowed = {str(s).upper() for s in criteria["signals"]}
            if str(stock.get("signal", "")).upper() not in allowed:
                return False

        return True

    def _match_record(self, stock: Dict[str, Any], criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Build a result record with a normalized match_score (0-1)."""
        score = stock.get("score")
        score_component = 0.0
        if score is not None:
            score_component = max(0.0, min(1.0, float(score) / 100.0))

        change = float(stock.get("change_pct", 0.0))
        change_component = max(0.0, min(1.0, abs(change) / 10.0))

        match_score = round(0.6 * score_component + 0.4 * change_component, 4)

        return {
            "symbol": stock.get("symbol", "UNKNOWN"),
            "name": stock.get("name", stock.get("symbol", "UNKNOWN")),
            "sector": stock.get("sector"),
            "asset_class": stock.get("asset_class"),
            "score": score,
            "change_pct": change,
            "price": stock.get("price"),
            "volume": stock.get("volume"),
            "signal": stock.get("signal"),
            "match_score": match_score,
        }
