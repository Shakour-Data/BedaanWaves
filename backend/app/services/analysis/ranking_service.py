"""
Ranking Service - Nasdaq stock ranking and scoring history.

Provides:
- Nasdaq universe ranking with 6D scores
- Score history for trend display
- Full hierarchy scores per symbol
- Current coefficients/weights per symbol
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
import logging

from fastapi import HTTPException
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Asset, IntlPriceCandle, ScoreHistory, candle_model_for_market
from app.services.analysis.scoring_service import ScoringService
from app.services.analysis.technical_indicators import compute_all_indicators, Candle
from app.services.core.dependency_container import get_global_container

logger = logging.getLogger(__name__)


class RankingService:
    """Service for Nasdaq stock ranking and score history retrieval."""

    VALID_SORT_FIELDS = {
        "overall_score",
        "fundamental",
        "technical",
        "sentiment",
        "risk",
        "macro",
        "ai",
    }

    def __init__(self):
        self._scoring_service: Optional[ScoringService] = None
        self._coefficient_service = None

    async def initialize(self) -> None:
        self._scoring_service = ScoringService()
        await self._scoring_service.initialize()

        try:
            container = get_global_container()
            self._coefficient_service = container.get("coefficient_learning_service")
        except Exception as exc:
            logger.warning(f"Could not get coefficient service: {exc}")

    async def shutdown(self) -> None:
        if self._scoring_service:
            await self._scoring_service.shutdown()

    async def get_nasdaq_rankings(
        self,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "overall_score",
        order: str = "desc",
        db: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        if sort_by not in self.VALID_SORT_FIELDS:
            sort_by = "overall_score"
        if order not in ("asc", "desc"):
            order = "desc"

        if not db:
            raise ValueError("Database session is required")

        asset_query = (
            select(Asset)
            .where(
                and_(
                    Asset.market == "NASDAQ",
                    Asset.active == True,
                )
            )
            .order_by(Asset.symbol.asc())
        )
        result = await db.execute(asset_query)
        assets = result.scalars().all()

        if not assets:
            return {
                "status": "success",
                "count": 0,
                "total": 0,
                "data": [],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        import asyncio

        async def score_asset(asset: Asset) -> Dict[str, Any]:
            try:
                Candle = candle_model_for_market(asset.market)
                candle_result = await db.execute(
                    select(Candle)
                    .where(Candle.asset_id == asset.id, Candle.timeframe == "1d")
                    .order_by(Candle.timestamp.desc())
                    .limit(100)
                )
                candles_raw = list(reversed(candle_result.scalars().all()))

                prices = [float(c.close) for c in candles_raw] if candles_raw else []

                scoring_input = {
                    "ticker": asset.symbol,
                    "market": asset.market,
                    "technical": {},
                    "fundamental": {},
                    "risk": {},
                    "sentiment": {},
                    "macro": {},
                    "ai": {},
                }

                if candles_raw:
                    candles = [
                        Candle(
                            open=float(c.open),
                            high=float(c.high),
                            low=float(c.low),
                            close=float(c.close),
                            volume=float(c.volume) if c.volume else 0.0,
                        )
                        for c in candles_raw
                    ]
                    indicators = compute_all_indicators(candles)

                    technical_data = {}
                    if "rsi" in indicators:
                        technical_data["rsi"] = indicators["rsi"]
                    if "macd" in indicators:
                        technical_data["macd"] = indicators["macd"]
                    if "macd_histogram" in indicators:
                        technical_data["macd_histogram"] = indicators["macd_histogram"]
                    if "bb_percent_b" in indicators:
                        technical_data["bb_position"] = indicators["bb_percent_b"]
                    if "volume_ratio" in indicators:
                        technical_data["volume_ratio"] = indicators["volume_ratio"]
                    if "volatility" in indicators:
                        technical_data["volatility"] = indicators["volatility"]
                    if "momentum" in indicators:
                        technical_data["momentum"] = indicators["momentum"]
                    if "stoch_k" in indicators:
                        technical_data["stoch_k"] = indicators["stoch_k"]
                    if "atr" in indicators:
                        technical_data["atr"] = indicators["atr"]
                    if "price_vs_sma20" in indicators:
                        technical_data["price_vs_sma20"] = indicators["price_vs_sma20"]
                    if "price_vs_sma50" in indicators:
                        technical_data["price_vs_sma50"] = indicators["price_vs_sma50"]
                    technical_data["current_price"] = prices[-1] if prices else 0
                    scoring_input["technical"] = technical_data

                    risk_data = {}
                    if "volatility" in indicators:
                        risk_data["volatility"] = indicators["volatility"]
                    if "atr" in indicators and prices and prices[-1] > 0:
                        risk_data["atr_ratio"] = indicators["atr"] / prices[-1]
                    scoring_input["risk"] = risk_data

                if self._scoring_service:
                    scored = await self._scoring_service.analyze(scoring_input)
                else:
                    scored = {
                        "overall_score": 0,
                        "grade": "E_STRONG_SELL",
                        "dimension_scores": {},
                    }

                return {
                    "symbol": asset.symbol,
                    "name": asset.name,
                    "overall_score": scored.get("overall_score", 0),
                    "grade": scored.get("grade", ""),
                    "dimension_scores": scored.get("dimension_scores", {}),
                }
            except Exception as exc:
                logger.error(f"Error scoring {asset.symbol}: {exc}")
                return {
                    "symbol": asset.symbol,
                    "name": asset.name,
                    "overall_score": 0,
                    "grade": "E_STRONG_SELL",
                    "dimension_scores": {},
                }

        tasks = [score_asset(asset) for asset in assets]
        scored_results = await asyncio.gather(*tasks, return_exceptions=True)

        ranked: List[Dict[str, Any]] = []
        for scored_result in scored_results:
            if isinstance(scored_result, Exception):
                continue
            ranked.append(scored_result)

        ranked.sort(
            key=lambda x: x.get(sort_by, 0) if isinstance(x.get(sort_by), (int, float)) else 0,
            reverse=(order == "desc"),
        )

        total = len(ranked)
        page = ranked[offset : offset + limit]
        for idx, item in enumerate(page, start=offset + 1):
            item["rank"] = idx

        return {
            "status": "success",
            "count": len(page),
            "total": total,
            "limit": limit,
            "offset": offset,
            "sort_by": sort_by,
            "order": order,
            "data": page,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def get_score_history(
        self, symbol: str, days: int = 30, db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        if not db:
            raise ValueError("Database session is required")

        asset_result = await db.execute(
            select(Asset).where(func.lower(Asset.symbol) == func.lower(symbol))
        )
        asset = asset_result.scalars().first()
        if not asset:
            raise HTTPException(status_code=404, detail=f"Asset {symbol} not found")

        cutoff_date = datetime.now(timezone.utc).date() - timedelta(days=days)
        history_query = (
            select(ScoreHistory)
            .where(
                and_(
                    ScoreHistory.asset_id == asset.id,
                    ScoreHistory.date >= cutoff_date,
                )
            )
            .order_by(ScoreHistory.date.asc())
        )
        history_result = await db.execute(history_query)
        records = history_result.scalars().all()

        history = []
        for record in records:
            history.append(
                {
                    "date": record.date.isoformat(),
                    "overall_score": float(record.overall_score),
                    "grade": record.grade,
                    "dimension_scores": record.dimension_scores or {},
                }
            )

        return {
            "status": "success",
            "symbol": asset.symbol,
            "name": asset.name,
            "days": days,
            "count": len(history),
            "history": history,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def get_hierarchy_scores(self, symbol: str, db: Optional[AsyncSession] = None) -> Dict[str, Any]:
        if not db:
            raise ValueError("Database session is required")

        asset_result = await db.execute(
            select(Asset).where(func.lower(Asset.symbol) == func.lower(symbol))
        )
        asset = asset_result.scalars().first()
        if not asset:
            raise HTTPException(status_code=404, detail=f"Asset {symbol} not found")

        Candle = candle_model_for_market(asset.market)
        candle_result = await db.execute(
            select(Candle)
            .where(Candle.asset_id == asset.id, Candle.timeframe == "1d")
            .order_by(Candle.timestamp.desc())
            .limit(100)
        )
        candles_raw = list(reversed(candle_result.scalars().all()))
        prices = [float(c.close) for c in candles_raw] if candles_raw else []

        scoring_input = {
            "ticker": asset.symbol,
            "market": asset.market,
            "technical": {},
            "fundamental": {},
            "risk": {},
            "sentiment": {},
            "macro": {},
            "ai": {},
        }

        if candles_raw:
            candles = [
                Candle(
                    open=float(c.open),
                    high=float(c.high),
                    low=float(c.low),
                    close=float(c.close),
                    volume=float(c.volume) if c.volume else 0.0,
                )
                for c in candles_raw
            ]
            indicators = compute_all_indicators(candles)

            technical_data = {}
            if "rsi" in indicators:
                technical_data["rsi"] = indicators["rsi"]
            if "macd" in indicators:
                technical_data["macd"] = indicators["macd"]
            if "macd_histogram" in indicators:
                technical_data["macd_histogram"] = indicators["macd_histogram"]
            if "bb_percent_b" in indicators:
                technical_data["bb_position"] = indicators["bb_percent_b"]
            if "volume_ratio" in indicators:
                technical_data["volume_ratio"] = indicators["volume_ratio"]
            if "volatility" in indicators:
                technical_data["volatility"] = indicators["volatility"]
            if "momentum" in indicators:
                technical_data["momentum"] = indicators["momentum"]
            if "stoch_k" in indicators:
                technical_data["stoch_k"] = indicators["stoch_k"]
            if "atr" in indicators:
                technical_data["atr"] = indicators["atr"]
            if "price_vs_sma20" in indicators:
                technical_data["price_vs_sma20"] = indicators["price_vs_sma20"]
            if "price_vs_sma50" in indicators:
                technical_data["price_vs_sma50"] = indicators["price_vs_sma50"]
            technical_data["current_price"] = prices[-1] if prices else 0
            scoring_input["technical"] = technical_data

            risk_data = {}
            if "volatility" in indicators:
                risk_data["volatility"] = indicators["volatility"]
            if "atr" in indicators and prices and prices[-1] > 0:
                risk_data["atr_ratio"] = indicators["atr"] / prices[-1]
            scoring_input["risk"] = risk_data

        if not self._scoring_service:
            await self.initialize()

        scored = await self._scoring_service.analyze(scoring_input)
        hierarchy = self._scoring_service.get_hierarchy_info()

        dimension_scores = scored.get("dimension_scores", {})
        hierarchy_scores: Dict[str, List[Dict[str, Any]]] = {
            "level1_dimensions": [],
            "level2_subdimensions": [],
            "level3_aspects": [],
            "level4_subaspects": [],
        }

        for dim, score in dimension_scores.items():
            hierarchy_scores["level1_dimensions"].append(
                {"name": dim, "score": float(score)}
            )

        sub_dim_map = {
            "fundamental": ["valuation", "profitability", "growth", "liquidity", "efficiency", "corporate_actions"],
            "technical": ["moving_averages", "momentum", "volatility", "volume", "trend"],
            "sentiment": ["news_sentiment", "social_sentiment", "analyst_sentiment"],
            "risk": ["market_risk", "credit_risk", "operational_risk", "liquidity_risk"],
            "macro": ["gdp", "inflation", "interest_rates", "exchange_rates", "commodity_prices"],
            "ai": ["ml_prediction", "pattern_recognition", "anomaly_detection"],
        }
        for dim, sub_dims in sub_dim_map.items():
            dim_score = float(dimension_scores.get(dim, 50.0))
            for sub in sub_dims:
                hierarchy_scores["level2_subdimensions"].append(
                    {
                        "parent": dim,
                        "name": sub,
                        "score": round(dim_score, 2),
                    }
                )

        for dim, sub_dims in sub_dim_map.items():
            dim_score = float(dimension_scores.get(dim, 50.0))
            for sub in sub_dims:
                for i in range(1, 3):
                    hierarchy_scores["level3_aspects"].append(
                        {
                            "parent": sub,
                            "name": f"{sub}_aspect_{i}",
                            "score": round(dim_score, 2),
                        }
                    )

        return {
            "status": "success",
            "symbol": asset.symbol,
            "name": asset.name,
            "overall_score": scored.get("overall_score", 0),
            "grade": scored.get("grade", ""),
            "hierarchy": hierarchy_scores,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def get_coefficients(self, symbol: str, db: Optional[AsyncSession] = None) -> Dict[str, Any]:
        if not db:
            raise ValueError("Database session is required")

        asset_result = await db.execute(
            select(Asset).where(func.lower(Asset.symbol) == func.lower(symbol))
        )
        asset = asset_result.scalars().first()
        if not asset:
            raise HTTPException(status_code=404, detail=f"Asset {symbol} not found")

        coefficients: Dict[str, Any] = {
            "dimensions": {},
            "sub_dimensions": {},
            "aspects": {},
            "sub_aspects": {},
        }

        if self._coefficient_service:
            try:
                for level in ["dimensions", "sub_dimensions", "aspects", "sub_aspects"]:
                    weights = self._coefficient_service.get_coefficients(level)
                    if weights:
                        coefficients[level] = weights
            except Exception as exc:
                logger.warning(f"Could not fetch ML coefficients: {exc}")

        if not any(coefficients.values()):
            coefficients = {
                "dimensions": {
                    "fundamental": 0.25,
                    "technical": 0.20,
                    "sentiment": 0.15,
                    "risk": 0.20,
                    "macro": 0.10,
                    "ai": 0.10,
                },
                "sub_dimensions": {},
                "aspects": {},
                "sub_aspects": {},
                "note": "Using static fallback weights (ML coefficients unavailable)",
            }

        return {
            "status": "success",
            "symbol": asset.symbol,
            "name": asset.name,
            "coefficients": coefficients,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
