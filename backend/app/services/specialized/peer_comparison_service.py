"""
Peer Comparison Service - Tier 7 Specialized Service

Benchmark an asset against its industry/segment peers across normalized
metrics, producing relative rankings, percentile scores, and z-score deltas.
"""

from typing import Any

from app.core.utils import utc_now_iso
from app.services.core.base_service import AnalysisService


class PeerComparisonService(AnalysisService):
    """
    Cross-asset peer benchmarking service.

    Compares a target asset against a universe of peer assets using
    configurable metrics and returns relative positioning data.
    """

    def __init__(self, service_name: str = "PeerComparisonService"):
        super().__init__(service_name)

    async def initialize(self) -> None:
        self.logger.info("PeerComparisonService initialized")

    async def shutdown(self) -> None:
        self.cache_clear()
        self.logger.info("PeerComparisonService shutdown")

    async def analyze(self, data: dict[str, Any]) -> dict[str, Any]:
        return await self.compare_peers(
            target=data.get("target", ""),
            peers=data.get("peers", []),
            metrics=data.get("metrics", []),
        )

    async def compare_peers(
        self,
        target: str,
        peers: list[dict[str, Any]],
        metrics: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Compare a target asset against its peers.

        Args:
            target: The symbol/identifier being benchmarked.
            peers: List of peer dicts, each containing ``symbol`` and metric values.
            metrics: Optional list of metric keys to compare.

        Returns:
            Dictionary with peer comparison results, rankings, and z-scores.
        """
        if metrics is None:
            metrics = ["score", "price", "change_pct"]

        if not peers:
            return {
                "target": target,
                "peers": [],
                "rankings": {},
                "percentile": 0.0,
                "timestamp": utc_now_iso(),
            }

        # Build metric series
        series: dict[str, list[float]] = {}
        for metric in metrics:
            values: list[float] = []
            for peer in peers:
                raw = peer.get(metric)
                try:
                    values.append(float(raw))
                except (TypeError, ValueError):
                    values.append(0.0)
            series[metric] = values

        rankings: dict[str, dict[str, Any]] = {}
        target_metrics = {p.get("symbol", ""): p for p in peers}
        target_entry = target_metrics.get(target, {})

        for metric in metrics:
            vals = series[metric]
            if not vals:
                continue
            mean_val = sum(vals) / len(vals) if vals else 0
            std = (sum((v - mean_val) ** 2 for v in vals) / len(vals)) ** 0.5 if vals else 0
            target_val = float(target_entry.get(metric, 0) or 0)
            z_score = (target_val - mean_val) / std if std > 0 else 0.0
            sorted_vals = sorted(vals, reverse=True)
            try:
                pct = (sorted_vals.index(target_val) + 1) / len(sorted_vals)
            except ValueError:
                pct = 0.5
            rankings[metric] = {
                "target_value": target_val,
                "peer_mean": mean_val,
                "peer_std": std,
                "z_score": z_score,
                "percentile": pct,
            }

        overall_pct = (
            sum(r.get("percentile", 0.5) for r in rankings.values()) / len(rankings)
            if rankings
            else 0.0
        )

        return {
            "target": target,
            "peers": [p.get("symbol", "") for p in peers],
            "rankings": rankings,
            "percentile": round(overall_pct, 4),
            "timestamp": utc_now_iso(),
        }
