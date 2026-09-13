"""Sector Analysis Service - Tier 7 Specialized Service

Aggregates stock-level metrics into sector-level intelligence:
- Per-sector summary (counts, average score, average change, movers)
- Cross-sector ranking by composite strength
- Market-wide overview
"""

from typing import Any, Dict, List, Optional
from ..core import AnalysisService


class SectorAnalysisService(AnalysisService):
    """Aggregates stock metrics into sector-level intelligence."""

    def __init__(self, service_name: str = "SectorAnalysisService"):
        super().__init__(service_name)

    async def initialize(self) -> None:
        self.logger.info("SectorAnalysisService initialized")

    async def shutdown(self) -> None:
        self.logger.info("SectorAnalysisService shutdown")

    def _validate_stock(self, stock: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize a single stock record, filling missing fields."""
        score = stock.get("score")
        change = stock.get("change_pct")
        return {
            "symbol": stock.get("symbol", "UNKNOWN"),
            "name": stock.get("name", stock.get("symbol", "UNKNOWN")),
            "sector": stock.get("sector", "UNCLASSIFIED"),
            "score": float(score) if score is not None else None,
            "change_pct": float(change) if change is not None else 0.0,
            "price": float(stock.get("price", 0.0)) if stock.get("price") is not None else None,
            "volume": int(stock.get("volume", 0)) if stock.get("volume") is not None else None,
            "signal": stock.get("signal"),
        }

    async def analyze_sector(self, sector: str, stocks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Summarize a single sector from its constituent stocks.

        Args:
            sector: Sector name
            stocks: List of stock records (symbol, name, score, change_pct, ...)

        Returns:
            Sector summary with aggregates and movers
        """
        if not stocks:
            return {
                "sector": sector,
                "count": 0,
                "average_score": None,
                "average_change_pct": 0.0,
                "scored_count": 0,
                "top_mover": None,
                "bottom_mover": None,
                "score_distribution": {"strong": 0, "neutral": 0, "weak": 0},
            }

        normalized = [self._validate_stock(s) for s in stocks]

        scored = [s for s in normalized if s["score"] is not None]
        avg_score = sum(s["score"] for s in scored) / len(scored) if scored else None
        avg_change = sum(s["change_pct"] for s in normalized) / len(normalized)

        ranked = sorted(normalized, key=lambda s: s["change_pct"], reverse=True)
        top_mover = ranked[0]
        bottom_mover = ranked[-1]

        distribution = {"strong": 0, "neutral": 0, "weak": 0}
        for s in scored:
            if s["score"] >= 66:
                distribution["strong"] += 1
            elif s["score"] >= 33:
                distribution["neutral"] += 1
            else:
                distribution["weak"] += 1

        return {
            "sector": sector,
            "count": len(normalized),
            "scored_count": len(scored),
            "average_score": round(avg_score, 2) if avg_score is not None else None,
            "average_change_pct": round(avg_change, 2),
            "top_mover": {"symbol": top_mover["symbol"], "change_pct": round(top_mover["change_pct"], 2)},
            "bottom_mover": {"symbol": bottom_mover["symbol"], "change_pct": round(bottom_mover["change_pct"], 2)},
            "score_distribution": distribution,
        }

    async def analyze_all(self, stocks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Group stocks by sector and summarize each, plus market overview.

        Args:
            stocks: Flat list of stock records

        Returns:
            {sectors: [...], market_overview: {...}}
        """
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for stock in stocks:
            sector = (stock.get("sector") or "UNCLASSIFIED")
            grouped.setdefault(sector, []).append(stock)

        sector_summaries = []
        for sector, members in grouped.items():
            summary = await self.analyze_sector(sector, members)
            sector_summaries.append(summary)

        ranked = await self.rank_sectors(sector_summaries)

        scored = [s for s in stocks if s.get("score") is not None]
        market_avg_score = (
            round(sum(float(s["score"]) for s in scored) / len(scored), 2) if scored else None
        )
        market_avg_change = (
            round(sum(float(s.get("change_pct", 0.0)) for s in stocks) / len(stocks), 2)
            if stocks else 0.0
        )

        return {
            "sectors": sector_summaries,
            "ranked_sectors": ranked,
            "market_overview": {
                "total_stocks": len(stocks),
                "total_sectors": len(sector_summaries),
                "average_score": market_avg_score,
                "average_change_pct": market_avg_change,
                "strongest_sector": ranked[0]["sector"] if ranked else None,
                "weakest_sector": ranked[-1]["sector"] if ranked else None,
            },
            "timestamp": None,
        }

    async def rank_sectors(self, sector_summaries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Rank sectors by a composite strength score.

        Composite = 0.6 * normalized average score + 0.4 * normalized average change.

        Args:
            sector_summaries: Output of analyze_sector / analyze_all

        Returns:
            Sorted list (strongest first) with composite_score
        """
        if not sector_summaries:
            return []

        def _score_of(s: Dict[str, Any]) -> Optional[float]:
            return s.get("average_score")

        def _change_of(s: Dict[str, Any]) -> float:
            return float(s.get("average_change_pct", 0.0))

        scores = [s for s in sector_summaries if _score_of(s) is not None]
        score_min = min(_score_of(s) for s in scores) if scores else 0.0
        score_max = max(_score_of(s) for s in scores) if scores else 1.0
        score_range = (score_max - score_min) or 1.0

        changes = [abs(_change_of(s)) for s in sector_summaries]
        change_max = max(changes) if changes else 1.0
        change_max = change_max or 1.0

        enriched = []
        for s in sector_summaries:
            raw_score = _score_of(s)
            norm_score = ((raw_score - score_min) / score_range) if raw_score is not None else 0.0
            norm_change = abs(_change_of(s)) / change_max
            composite = round(0.6 * norm_score + 0.4 * norm_change, 4)
            enriched.append({**s, "composite_score": composite})

        enriched.sort(key=lambda s: s["composite_score"], reverse=True)
        return enriched
