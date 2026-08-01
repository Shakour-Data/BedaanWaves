from typing import Any, Dict, List, Optional
import numpy as np
from datetime import datetime, timezone
from functools import lru_cache

from ..core import AnalysisService
from ..core.dependency_container import DependencyContainer
from app.core.config import get_settings

settings = get_settings()


class HistoricalRegimeCompressionService(AnalysisService):
    """Historical regime compression using Dynamic Time Warping (DTW)."""

    def __init__(self, service_name: str = "HistoricalRegimeCompressionService"):
        super().__init__(service_name)
        self.fingerprint_db: Dict[str, List[float]] = {}

    async def initialize(self) -> None:
        self.logger.info("HistoricalRegimeCompressionService initialized")
        # Load historical regime fingerprints (1850-present)
        await self._load_fingerprints()

    async def _load_fingerprints(self) -> None:
        """Load predefined regime fingerprints from configuration."""
        default_fingerprints = {
            "1870-1890_long_depression": [0.2, -0.5, -0.3, 0.1, 0.0, -0.1],
            "1929-1939_great_depression": [-1.0, -0.8, -0.6, -0.4, -0.2],
            "1945-1971_post_war_golden_age": [0.5, 1.0, 0.8, 0.6, 0.4],
            "1973-1975_oil_crisis": [-0.5, -0.3, 0.2, 0.1, -0.4],
            "1980s_liquidation": [-0.3, 0.5, 0.7, 0.8, 0.6],
            "2000-2002_dot_com_bubble": [0.8, 0.6, -0.5, -0.7, -0.4],
            "2008-2009_financial_crisis": [0.6, 0.4, -0.8, -1.0, -0.6],
            "2020-2021_pandemic": [0.2, -0.9, 0.8, 0.8, 0.7],
        }
        for name, fingerprint in default_fingerprints.items():
            self.fingerprint_db[name] = fingerprint

        self.logger.info("Loaded %d regime fingerprints", len(self.fingerprint_db))

    async def shutdown(self) -> None:
        self.logger.info("HistoricalRegimeCompressionService shutdown")

    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Run regime compression analysis."""
        current_series = data.get("series", [])
        if not current_series or len(current_series) < 5:
            return {"error": "Insufficient data for regime compression"}

        # Normalize the series to fingerprints
        normalized_series = self._normalize_series(current_series)

        # Match against historical fingerprints using DTW
        matches = await self._dtw_cycle_matching(normalized_series)

        # Generate regime fingerprint
        fingerprint = await self._generate_fingerprint(normalized_series)

        return {
            "current_fingerprint": fingerprint,
            "historical_matches": matches,
            "similarity_scores": {m["regime"]: m["similarity"] for m in matches[:3]},
            "analysis_at": datetime.now(timezone.utc).isoformat(),
        }

    def _normalize_series(self, series: List[float]) -> List[float]:
        """Normalize a time series to mean 0, std 1."""
        arr = np.array(series, dtype=float)
        mean = np.mean(arr)
        std = np.std(arr)
        if std == 0:
            return [0.0] * len(arr)
        return ((arr - mean) / std).tolist()

    def _dtw_distance(self, s1: List[float], s2: List[float]) -> float:
        """Compute Dynamic Time Warping distance between two series."""
        n = len(s1)
        m = len(s2)
        if n == 0 or m == 0:
            return float("inf")

        dtw_matrix = np.zeros((n + 1, m + 1))
        dtw_matrix[0, :] = np.inf
        dtw_matrix[:, 0] = np.inf
        dtw_matrix[0, 0] = 0

        for i in range(1, n + 1):
            for j in range(1, m + 1):
                cost = abs(s1[i - 1] - s2[j - 1])
                dtw_matrix[i, j] = cost + min(
                    dtw_matrix[i - 1, j],    # insertion
                    dtw_matrix[i, j - 1],    # deletion
                    dtw_matrix[i - 1, j - 1]  # match
                )

        return float(dtw_matrix[n, m])

    async def _dtw_cycle_matching(
        self, normalized_series: List[float]
    ) -> List[Dict[str, Any]]:
        """Match current series against historical regime fingerprints using DTW."""
        matches = []

        for regime_name, fingerprint in self.fingerprint_db.items():
            # Resample current series to match fingerprint length
            target_len = len(fingerprint)
            if len(normalized_series) > target_len:
                indices = np.linspace(0, len(normalized_series) - 1, target_len)
                resampled = [normalized_series[int(i)] for i in indices]
            else:
                resampled = normalized_series + [0.0] * (target_len - len(normalized_series))

            distance = self._dtw_distance(resampled, fingerprint)
            # Convert distance to similarity (lower distance = higher similarity)
            max_distance = float(target_len) * 2
            similarity = max(0.0, 1.0 - (distance / max_distance)) if max_distance > 0 else 0.0

            matches.append({
                "regime": regime_name,
                "distance": distance,
                "similarity": round(similarity, 4),
            })

        # Sort by similarity (descending)
        matches.sort(key=lambda x: x["similarity"], reverse=True)
        return matches

    async def _generate_fingerprint(self, normalized_series: List[float]) -> List[float]:
        """Generate a compressed fingerprint vector for the current regime."""
        series = np.array(normalized_series)

        # Create fingerprint using statistical moments + key percentiles
        fingerprint = [
            float(np.mean(series)),      # 1. Mean
            float(np.std(series)),       # 2. Volatility
            float(np.median(series)),    # 3. Median
            float(np.percentile(series, 75)),  # 4. Upper quartile
            float(np.percentile(series, 25)),  # 5. Lower quartile
            float(np.skew(series)) if len(series) > 2 else 0.0,  # 6. Skewness
            float(np.kurtosis(series)) if len(series) > 3 else 0.0,  # 7. Kurtosis
            float(series[-1] - series[0]),  # 8. Trend
        ]

        # Add autocorrelation features
        if len(series) > 10:
            autocorr = np.corrcoef(series[:-1], series[1:])[0, 1]
            fingerprint.append(float(autocorr))
        else:
            fingerprint.append(0.0)

        return [round(v, 4) for v in fingerprint]

    async def get_fingerprint_database(self) -> Dict[str, Any]:
        """Return all historical fingerprints."""
        return self.fingerprint_db


DependencyContainer.register("HistoricalRegimeCompressionService", HistoricalRegimeCompressionService)