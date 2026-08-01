from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import numpy as np
import aiohttp

from ..core import AnalysisService
from ..core.dependency_container import DependencyContainer
from app.core.config import get_settings

settings = get_settings()


class ShadowBankingMetricsService(AnalysisService):
    """Track shadow banking exposure and systemic risk indicators."""

    def __init__(self, service_name: str = "ShadowBankingMetricsService"):
        super().__init__(service_name)
        self.session: Optional[aiohttp.ClientSession] = None

    async def initialize(self) -> None:
        """Initialize HTTP session for repo market data."""
        self.session = aiohttp.ClientSession()
        self.logger.info("ShadowBankingMetricsService initialized")

    async def shutdown(self) -> None:
        """Close HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()
        self.logger.info("ShadowBankingMetricsService shutdown")

    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate shadow banking risk metrics."""
        results = {
            "credit_intermediation_ratio": await self._credit_intermediation_ratio(data),
            "money_multiplier_stress": await self._money_multiplier_stress(data),
            "repo_market_stress": await self._repo_market_stress(data),
            "structured_products_tracking": await self._structured_products_tracking(data),
        }
        return results

    async def _credit_intermediation_ratio(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate credit intermediation ratio: Shadow banking assets / regulated banking assets."""
        shadow_assets = data.get("shadow_banking_assets", 1_000_000_000_000)  # $1T default
        regulated_assets = data.get("regulated_banking_assets", 20_000_000_000_000)  # $20T default

        ratio = shadow_assets / regulated_assets if regulated_assets > 0 else 0.0
        return {
            "ratio": ratio,
            "shadow_assets": shadow_assets,
            "regulated_assets": regulated_assets,
            "risk_level": "high" if ratio > 0.15 else "moderate" if ratio > 0.10 else "low",
        }

    async def _money_multiplier_stress(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Monitor money multipliers: M0/M1, M1/M2, M2/M3 contractions."""
        m0 = data.get("m0", 100)
        m1 = data.get("m1", 1000)
        m2 = data.get("m2", 5000)
        m3 = data.get("m3", 8000)

        multipliers = {
            "m0_m1": m0 / m1 if m1 > 0 else 0.0,
            "m1_m2": m1 / m2 if m2 > 0 else 0.0,
            "m2_m3": m2 / m3 if m3 > 0 else 0.0,
        }

        # Detect contraction (decreasing multipliers)
        stress = any(v < 0.1 for v in multipliers.values())
        return {
            "multipliers": multipliers,
            "contraction_detected": stress,
            "stress_level": "high" if stress else "normal",
        }

    async def _repo_market_stress(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Track repo market stress indicators: spreads, haircut volatility."""
        if not self.session:
            return {"error": "Service not initialized"}

        try:
            # Fetch repo market data (placeholder endpoint)
            repo_rate = data.get("repo_rate", 5.0)
            sofr = data.get("sofr", 4.5)
            spread = repo_rate - sofr

            haircut_data = data.get("haircuts", [2, 3, 5, 3, 4])
            haircut_vol = np.std(haircut_data)

            return {
                "repo_rate": repo_rate,
                "sofr": sofr,
                "spread_bps": spread * 100,
                "haircut_volatility": float(haircut_vol),
                "stress": "elevated" if spread > 0.5 or haircut_vol > 1.5 else "normal",
            }
        except Exception as e:
            self.logger.error("Repo market stress fetch failed: %s", str(e))
            return {"error": str(e)}

    async def _structured_products_tracking(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Track structured product issuance: MBS, CDO, crypto-backed tokens."""
        mbs = data.get("mbs_issuance", 0)
        cdo = data.get("cdo_issuance", 0)
        crypto_tokens = data.get("crypto_backed_tokens", 0)

        total = mbs + cdo + crypto_tokens
        return {
            "mbs_issuance": mbs,
            "cdo_issuance": cdo,
            "crypto_backed_tokens": crypto_tokens,
            "total_issuance": total,
            "trend": "increasing" if total > 500 else "stable",
        }


DependencyContainer.register("ShadowBankingMetricsService", ShadowBankingMetricsService)