"""
ScoreHistory Pipeline Service

Computes real dimension scores from candle data and persists them to ScoreHistory.
This is the missing link between raw market data and the dashboard.

Flow:
1. Fetch candle data for each asset
2. Compute technical indicators (RSI, MACD, Bollinger Bands, etc.)
3. Score each dimension using the ScoringService
4. Persist results to ScoreHistory
"""

import asyncio
import logging
from datetime import datetime, date, timezone, timedelta
from typing import Dict, List, Any, Optional

from sqlalchemy import select, and_, desc
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import async_session_maker
from app.models.models import (
    Asset,
    IntlPriceCandle,
    ScoreHistory,
    candle_model_for_market,
)
from app.services.analysis.scoring_service import ScoringService
from app.services.analysis.technical_indicators import (
    compute_all_indicators,
    Candle,
)
from app.services.core.dependency_container import get_global_container

logger = logging.getLogger(__name__)


class ScoreHistoryPipeline:
    """
    Pipeline for computing and persisting ScoreHistory records.
    Computes real dimension scores from candle data using technical indicators.
    """

    def __init__(self, scoring_service: Optional[ScoringService] = None):
        self._scoring_service = scoring_service
        self._coefficient_service = None

    async def initialize(self):
        """Initialize the pipeline."""
        if self._scoring_service is None:
            self._scoring_service = ScoringService()
            await self._scoring_service.initialize()

        try:
            container = get_global_container()
            self._coefficient_service = container.get("coefficient_learning_service")
        except Exception:
            self._coefficient_service = None

    async def shutdown(self):
        """Shutdown the pipeline."""
        if self._scoring_service:
            await self._scoring_service.shutdown()

    async def compute_and_persist_all(
        self,
        target_date: Optional[date] = None,
        market: str = "NASDAQ",
        batch_size: int = 100,
    ) -> Dict[str, Any]:
        """
        Compute and persist ScoreHistory for all active assets in a market.

        Args:
            target_date: Date to compute scores for (default: today)
            market: Market to process (NASDAQ, NYSE, etc.)
            batch_size: Number of assets to process in parallel

        Returns:
            Summary of processing results
        """
        if target_date is None:
            target_date = datetime.now(timezone.utc).date()

        result = {
            "status": "started",
            "date": target_date.isoformat(),
            "market": market,
            "total_assets": 0,
            "scored": 0,
            "errors": 0,
            "skipped": 0,
        }

        async with async_session_maker() as session:
            asset_query = (
                select(Asset.id, Asset.symbol, Asset.market, Asset.asset_class)
                .where(and_(Asset.active == True, Asset.market == market))
                .order_by(Asset.symbol.asc())
            )
            assets_result = await session.execute(asset_query)
            assets = assets_result.fetchall()

        result["total_assets"] = len(assets)
        logger.info(
            f"ScoreHistoryPipeline: Processing {len(assets)} assets for {market} on {target_date}"
        )

        for i in range(0, len(assets), batch_size):
            batch = assets[i : i + batch_size]
            batch_results = await asyncio.gather(
                *[self._score_asset(asset, target_date) for asset in batch],
                return_exceptions=True,
            )

            for br in batch_results:
                if isinstance(br, Exception):
                    result["errors"] += 1
                    logger.error(f"ScoreHistoryPipeline error: {br}")
                elif br is None:
                    result["skipped"] += 1
                elif br.get("scored"):
                    result["scored"] += 1
                else:
                    result["skipped"] += 1

            if (i + batch_size) % 500 == 0:
                logger.info(
                    f"ScoreHistoryPipeline: Processed {min(i + batch_size, len(assets))}/{len(assets)}"
                )

        result["status"] = "completed"
        logger.info(f"ScoreHistoryPipeline complete: {result}")
        return result

    async def _score_asset(
        self, asset_row, target_date: date
    ) -> Optional[Dict[str, Any]]:
        """
        Compute and persist ScoreHistory for a single asset.
        """
        asset_id, symbol, market, asset_class = asset_row

        async with async_session_maker() as session:
            existing = await session.execute(
                select(ScoreHistory.id).where(
                    and_(
                        ScoreHistory.asset_id == asset_id,
                        ScoreHistory.date == target_date,
                    )
                )
            )
            if existing.scalar_one_or_none():
                return {"scored": False, "reason": "already_exists", "symbol": symbol}

        candles = await self._fetch_candles(asset_id, market, asset_class)
        if not candles or len(candles) < 30:
            return {"scored": False, "reason": "insufficient_candles", "symbol": symbol}

        scoring_input = self._build_scoring_input(symbol, market, candles)
        if not scoring_input:
            return {"scored": False, "reason": "scoring_input_failed", "symbol": symbol}

        try:
            scored = await self._scoring_service.analyze(scoring_input)
        except Exception as e:
            logger.error(f"Scoring failed for {symbol}: {e}")
            return {"scored": False, "reason": str(e), "symbol": symbol}

        await self._persist_score_history(
            asset_id, target_date, scored, market
        )

        return {"scored": True, "symbol": symbol, "overall": scored.get("overall_score")}

    async def _fetch_candles(
        self, asset_id, market: str, asset_class: str, lookback: int = 100
    ) -> List[Candle]:
        """Fetch candle data for an asset."""
        CandleModel = candle_model_for_market(market)
        if CandleModel is None:
            return []

        async with async_session_maker() as session:
            result = await session.execute(
                select(CandleModel)
                .where(
                    and_(
                        CandleModel.asset_id == asset_id,
                        CandleModel.timeframe == "1d",
                    )
                )
                .order_by(desc(CandleModel.timestamp))
                .limit(lookback)
            )
            rows = result.scalars().all()

        candles = []
        for row in reversed(rows):
            candles.append(
                Candle(
                    open=float(row.open),
                    high=float(row.high),
                    low=float(row.low),
                    close=float(row.close),
                    volume=float(row.volume) if row.volume else 0.0,
                )
            )

        return candles

    def _build_scoring_input(
        self, symbol: str, market: str, candles: List[Candle]
    ) -> Optional[Dict[str, Any]]:
        """Build the scoring input dict from computed indicators."""
        if not candles:
            return None

        indicators = compute_all_indicators(candles)
        if not indicators:
            return None

        closes = [c.close for c in candles]
        volumes = [c.volume for c in candles]

        current_price = closes[-1] if closes else 0

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
        technical_data["current_price"] = current_price

        risk_data = {}
        if "volatility" in indicators:
            risk_data["volatility"] = indicators["volatility"]
        if "atr" in indicators and current_price > 0:
            risk_data["atr_ratio"] = indicators["atr"] / current_price

        scoring_input = {
            "ticker": symbol,
            "market": market,
            "technical": technical_data,
            "risk": risk_data,
            "fundamental": {},
            "sentiment": {},
            "macro": {},
            "ai": {},
        }

        return scoring_input

    async def _persist_score_history(
        self,
        asset_id,
        target_date: date,
        scored: Dict[str, Any],
        market: str,
    ):
        """Persist scored results to ScoreHistory table."""
        async with async_session_maker() as session:
            dimension_scores = scored.get("dimension_scores", {})
            overall_score = scored.get("overall_score", 0)
            grade = scored.get("grade", "")

            stmt = pg_insert(ScoreHistory).values(
                asset_id=asset_id,
                date=target_date,
                dimension_scores=dimension_scores,
                overall_score=overall_score,
                grade=grade,
                created_at=datetime.now(timezone.utc).replace(tzinfo=None),
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["asset_id", "date"],
                set_={
                    "dimension_scores": stmt.excluded.dimension_scores,
                    "overall_score": stmt.excluded.overall_score,
                    "grade": stmt.excluded.grade,
                    "created_at": stmt.excluded.created_at,
                },
            )
            await session.execute(stmt)
            await session.commit()
