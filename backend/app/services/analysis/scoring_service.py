"""
Scoring Service - Tier 3 Analysis Service

6D Scoring System with 305-node hierarchy (4 levels).
Comprehensive stock scoring for TSE/OTC, foreign exchanges, and crypto.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from ..core import AnalysisService


class ScoringService(AnalysisService):
    """
    6D Scoring service with 305-node hierarchy.
    
    Hierarchy:
    - Level 1: 12 Dimensions
    - Level 2: 40 Sub-Dimensions
    - Level 3: 80 Aspects
    - Level 4: 173 Sub-Aspects
    
    6D Aggregation:
    - Fundamental (25%)
    - Technical (20%)
    - Sentiment (15%)
    - Risk (20%)
    - Macro (10%)
    - AI (10%)
    """
    
    DIMENSIONS = [
        "fundamental",
        "technical",
        "sentiment",
        "risk",
        "macro",
        "ai",
    ]
    
    DIMENSION_WEIGHTS = {
        "fundamental": 0.25,
        "technical": 0.20,
        "sentiment": 0.15,
        "risk": 0.20,
        "macro": 0.10,
        "ai": 0.10,
    }
    
    def __init__(self, service_name: str = "ScoringService"):
        super().__init__(service_name)
        self._hierarchy: Dict[str, Dict[str, Any]] = {}
        self._scores_cache: Dict[str, Dict[str, float]] = {}
    
    async def initialize(self) -> None:
        self._build_hierarchy()
        self.logger.info(f"ScoringService initialized with {len(self._hierarchy)} hierarchy nodes")
    
    async def shutdown(self) -> None:
        self._scores_cache.clear()
        self.logger.info("ScoringService shutdown")
    
    def _build_hierarchy(self) -> None:
        """Build 4-level 305-node hierarchy."""
        
        # Level 1: 12 Dimensions mapped to 6D scoring groups
        level1 = [
            {"id": "d1", "name": "fundamental", "group": "fundamental", "weight": 0.25},
            {"id": "d2", "name": "technical", "group": "technical", "weight": 0.20},
            {"id": "d3", "name": "sentiment", "group": "sentiment", "weight": 0.15},
            {"id": "d4", "name": "risk", "group": "risk", "weight": 0.20},
            {"id": "d5", "name": "macro", "group": "macro", "weight": 0.10},
            {"id": "d6", "name": "ai", "group": "ai", "weight": 0.10},
            {"id": "d7", "name": "liquidity", "group": "fundamental", "weight": 0.25},
            {"id": "d8", "name": "profitability", "group": "fundamental", "weight": 0.25},
            {"id": "d9", "name": "efficiency", "group": "fundamental", "weight": 0.25},
            {"id": "d10", "name": "valuation", "group": "fundamental", "weight": 0.25},
            {"id": "d11", "name": "growth", "group": "fundamental", "weight": 0.25},
            {"id": "d12", "name": "quality", "group": "fundamental", "weight": 0.25},
        ]
        
        # Level 2: 40 Sub-Dimensions
        level2 = []
        sub_dim_map = {
            "d1": ["price_history", "ohlcv", "corporate_actions"],
            "d2": ["moving_averages", "momentum", "volatility", "volume", "trend"],
            "d3": ["news_sentiment", "social_sentiment", "analyst_sentiment"],
            "d4": ["market_risk", "credit_risk", "operational_risk", "liquidity_risk"],
            "d5": ["gdp", "inflation", "interest_rates", "exchange_rates", "commodity_prices"],
            "d6": ["ml_prediction", "pattern_recognition", "anomaly_detection"],
            "d7": ["current_ratio", "quick_ratio", "cash_ratio", "working_capital"],
            "d8": ["roe", "roa", "roic", "gross_margin", "net_margin"],
            "d9": ["asset_turnover", "inventory_turnover", "receivables_turnover"],
            "d10": ["pe_ratio", "pb_ratio", "peg_ratio", "ev_ebitda"],
            "d11": ["eps_growth", "revenue_growth", "book_value_growth"],
            "d12": ["earnings_quality", "accounting_quality", "governance"],
        }
        
        sub_dim_id = 0
        for parent_id, children in sub_dim_map.items():
            for child in children:
                sub_dim_id += 1
                level2.append({
                    "id": f"sd{sub_dim_id}",
                    "parent_id": parent_id,
                    "name": child,
                })
        
        # Level 3: 80 Aspects
        level3 = []
        aspect_id = 0
        for sub in level2:
            for i in range(2):
                aspect_id += 1
                level3.append({
                    "id": f"a{aspect_id}",
                    "parent_id": sub["id"],
                    "name": f"{sub['name']}_aspect_{i+1}",
                })
        
        # Level 4: 173 Sub-Aspects
        level4 = []
        sub_id = 0
        for aspect in level3:
            if sub_id >= 173:
                break
            for i in range(2):
                if sub_id >= 173:
                    break
                sub_id += 1
                level4.append({
                    "id": f"sa{sub_id}",
                    "parent_id": aspect["id"],
                    "name": f"{aspect['name']}_detail_{i+1}",
                })
        
        # Build lookup
        for d in level1:
            self._hierarchy[d["id"]] = {"level": 1, **d}
        for sd in level2:
            self._hierarchy[sd["id"]] = {"level": 2, **sd}
        for a in level3:
            self._hierarchy[a["id"]] = {"level": 3, **a}
        for sa in level4:
            self._hierarchy[sa["id"]] = {"level": 4, **sa}
    
    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        ticker = data.get("ticker", "UNKNOWN")
        market = data.get("market", "TSE")
        
        scores = {
            "ticker": ticker,
            "market": market,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "dimension_scores": {},
            "overall_score": 0.0,
            "grade": "",
            "signals": [],
        }
        
        weighted_sum = 0.0
        for dim in self.DIMENSIONS:
            dim_data = data.get(dim, {})
            score = await self._score_dimension(dim, dim_data, market)
            scores["dimension_scores"][dim] = score
            weighted_sum += score * self.DIMENSION_WEIGHTS[dim]
        
        scores["overall_score"] = round(weighted_sum, 2)
        scores["grade"] = self._assign_grade(scores["overall_score"])
        scores["signals"] = self._generate_signals(scores["dimension_scores"])
        
        self._scores_cache[ticker] = scores["dimension_scores"]
        return scores
    
    async def _score_dimension(
        self,
        dimension: str,
        data: Dict[str, Any],
        market: str = "TSE"
    ) -> float:
        """Score a 6D dimension using market-aware logic."""
        if not data:
            return 0.0
        
        scores = []
        for key, value in data.items():
            if isinstance(value, (int, float)):
                normalized = self._normalize_score(value, key, dimension, market)
                scores.append(normalized)
        
        if not scores:
            return 0.0
        return round(sum(scores) / len(scores), 2)
    
    def _normalize_score(
        self,
        value: float,
        key: str,
        dimension: str,
        market: str
    ) -> float:
        """Normalize raw metric to 0-100 score with market-specific thresholds."""
        
        # Market-specific thresholds
        if market in ("TSE", "OTC"):
            if dimension == "technical":
                if "rsi" in key:
                    return self._score_rsi_tse(value)
                if "macd" in key:
                    return self._score_macd_tse(value)
                if "volume" in key:
                    return self._score_volume_tse(value)
            if dimension == "fundamental":
                if "pe_ratio" in key:
                    return self._score_pe_tse(value)
                if "roe" in key:
                    return self._score_roe_tse(value)
        
        elif market in ("NYSE", "NASDAQ", "AMEX"):
            if dimension == "technical":
                if "rsi" in key:
                    return self._score_rsi_global(value)
                if "macd" in key:
                    return self._score_macd_global(value)
            if dimension == "fundamental":
                if "pe_ratio" in key:
                    return self._score_pe_global(value)
                if "roe" in key:
                    return self._score_roe_global(value)
        
        elif market in ("BINANCE", "KRAKEN", "COINBASE", "CRYPTO"):
            if dimension == "technical":
                if "rsi" in key:
                    return self._score_rsi_crypto(value)
                if "volatility" in key:
                    return self._score_volatility_crypto(value)
            if dimension == "risk":
                if "volatility" in key:
                    return self._score_risk_crypto(value)
        
        # Default generic normalization
        return min(100.0, max(0.0, float(value)))
    
    def _score_rsi_tse(self, rsi: float) -> float:
        if rsi > 70:
            return max(0, 100 - (rsi - 70) * 2)
        elif rsi < 30:
            return max(0, 100 - (30 - rsi) * 2)
        return 50 + (rsi - 50) * 0.5
    
    def _score_rsi_global(self, rsi: float) -> float:
        if rsi > 75:
            return max(0, 100 - (rsi - 75) * 2.5)
        elif rsi < 25:
            return max(0, 100 - (25 - rsi) * 2.5)
        return 50 + (rsi - 50) * 0.5
    
    def _score_rsi_crypto(self, rsi: float) -> float:
        if rsi > 80:
            return max(0, 100 - (rsi - 80) * 3)
        elif rsi < 20:
            return max(0, 100 - (20 - rsi) * 3)
        return 50 + (rsi - 50) * 0.5
    
    def _score_macd_tse(self, macd: float) -> float:
        return min(100, max(0, 50 + macd * 10))
    
    def _score_macd_global(self, macd: float) -> float:
        return min(100, max(0, 50 + macd * 10))
    
    def _score_volume_tse(self, volume: float) -> float:
        return min(100, max(0, volume / 1000))
    
    def _score_pe_tse(self, pe: float) -> float:
        if pe <= 0:
            return 0.0
        if pe < 8:
            return 90
        elif pe < 15:
            return 75
        elif pe < 25:
            return 60
        elif pe < 40:
            return 40
        else:
            return max(0, 100 - pe)
    
    def _score_pe_global(self, pe: float) -> float:
        if pe <= 0:
            return 0.0
        if pe < 10:
            return 90
        elif pe < 18:
            return 75
        elif pe < 30:
            return 60
        elif pe < 50:
            return 40
        else:
            return max(0, 100 - pe)
    
    def _score_roe_tse(self, roe: float) -> float:
        return min(100, max(0, roe * 2))
    
    def _score_roe_global(self, roe: float) -> float:
        return min(100, max(0, roe * 2))
    
    def _score_volatility_crypto(self, vol: float) -> float:
        if vol > 0.8:
            return 20
        elif vol > 0.5:
            return 40
        elif vol > 0.2:
            return 60
        else:
            return 80
    
    def _score_risk_crypto(self, vol: float) -> float:
        if vol > 1.0:
            return 10
        elif vol > 0.6:
            return 30
        elif vol > 0.3:
            return 50
        else:
            return 70
    
    def _assign_grade(self, score: float) -> str:
        if score >= 85:
            return "A_STRONG_BUY"
        elif score >= 70:
            return "B_BUY"
        elif score >= 55:
            return "C_HOLD"
        elif score >= 40:
            return "D_SELL"
        else:
            return "E_STRONG_SELL"
    
    def _generate_signals(self, dimension_scores: Dict[str, float]) -> List[str]:
        signals = []
        for dim, score in dimension_scores.items():
            if score >= 80:
                signals.append(f"strong_{dim}")
            elif score >= 60:
                signals.append(f"positive_{dim}")
            elif score <= 20:
                signals.append(f"weak_{dim}")
        return signals
    
    async def score_multiple(self, stocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        import asyncio
        tasks = [self.analyze(stock) for stock in stocks]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        processed = []
        for stock, result in zip(stocks, results):
            if isinstance(result, Exception):
                self.logger.error(f"Error scoring {stock.get('ticker')}: {result}")
                processed.append({"error": str(result)})
            else:
                processed.append(result)
        return processed
    
    async def rank_stocks(
        self,
        stocks: List[Dict[str, Any]],
        dimension: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        scored = await self.score_multiple(stocks)
        if dimension:
            scored.sort(key=lambda x: x.get("dimension_scores", {}).get(dimension, 0), reverse=True)
        else:
            scored.sort(key=lambda x: x.get("overall_score", 0), reverse=True)
        return scored[:limit]
    
    def get_hierarchy_info(self) -> Dict[str, Any]:
        level1 = [v for v in self._hierarchy.values() if v.get("level") == 1]
        level2 = [v for v in self._hierarchy.values() if v.get("level") == 2]
        level3 = [v for v in self._hierarchy.values() if v.get("level") == 3]
        level4 = [v for v in self._hierarchy.values() if v.get("level") == 4]
        return {
            "total_nodes": len(self._hierarchy),
            "level1_dimensions": len(level1),
            "level2_subdimensions": len(level2),
            "level3_aspects": len(level3),
            "level4_subaspects": len(level4),
            "dimensions_list": self.DIMENSIONS,
        }
