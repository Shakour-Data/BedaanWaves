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

from sqlalchemy import select, and_, desc, func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import async_session_maker
from app.models.models import (
    Asset,
    IntlPriceCandle,
    ScoreHistory,
    FundamentalRatio,
    NewsSentiment,
    MacroIndicator,
    MLSignal,
    MarketDataSnapshot,
    RawPerformanceScore,
    candle_model_for_market,
)
from app.services.analysis.scoring_service import ScoringService
from app.services.analysis.scoring_engine_v2 import (
    METRIC_UNIVERSE, score_market, grade as v2_grade,
)
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
                .where(and_(
                    Asset.active == True,
                    Asset.market == market,
                    Asset.asset_class.in_(["EQUITY", "ETF"]),
                ))
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

        fundamental_data = await self._fetch_fundamental_data(asset_id)
        sentiment_data = await self._fetch_sentiment_data(asset_id)
        macro_data = await self._fetch_macro_data()
        ai_data = await self._fetch_ai_data(asset_id)

        scoring_input = self._build_scoring_input(
            symbol, market, candles, fundamental_data, sentiment_data, macro_data, ai_data
        )
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

    async def _fetch_fundamental_data(self, asset_id) -> Dict[str, Any]:
        """Fetch fundamental ratios for an asset."""
        async with async_session_maker() as session:
            result = await session.execute(
                select(FundamentalRatio)
                .where(FundamentalRatio.asset_id == asset_id)
                .order_by(desc(FundamentalRatio.as_of))
                .limit(1)
            )
            row = result.scalar_one_or_none()

        if not row:
            return {}

        data = {}
        if row.pe is not None:
            data["pe_ratio"] = float(row.pe)
        if row.pb is not None:
            data["pb_ratio"] = float(row.pb)
        if row.roe is not None:
            data["roe"] = float(row.roe)
        if row.profit_margin is not None:
            data["profit_margin"] = float(row.profit_margin)
        if row.eps is not None:
            data["eps"] = float(row.eps)
        if row.dps is not None:
            data["dps"] = float(row.dps)
        if row.market_cap is not None:
            data["market_cap"] = float(row.market_cap)
        if row.book_value is not None:
            data["book_value"] = float(row.book_value)

        return data

    async def _fetch_sentiment_data(self, asset_id) -> Dict[str, Any]:
        """Fetch news sentiment for an asset."""
        async with async_session_maker() as session:
            result = await session.execute(
                select(
                    func.avg(NewsSentiment.sentiment_score).label("avg_sentiment"),
                    func.count(NewsSentiment.id).label("count"),
                )
                .where(NewsSentiment.asset_id == asset_id)
            )
            row = result.first()

        if not row or row.count == 0:
            return {}

        return {
            "news_sentiment": float(row.avg_sentiment) if row.avg_sentiment else 0.5,
            "news_count": row.count,
        }

    async def _fetch_macro_data(self) -> Dict[str, Any]:
        """Fetch latest macro indicators."""
        async with async_session_maker() as session:
            result = await session.execute(
                select(MacroIndicator)
                .order_by(desc(MacroIndicator.as_of))
                .limit(10)
            )
            rows = result.scalars().all()

        data = {}
        for row in rows:
            code = row.indicator_code
            val = float(row.value) if row.value else 0
            if code == "^VIX":
                data["vix"] = val
            elif code == "^TNX":
                data["treasury_yield"] = val
            elif code == "DX-Y.NYB":
                data["dollar_index"] = val
            elif code == "GC=F":
                data["gold_price"] = val
            elif code == "CL=F":
                data["oil_price"] = val

        return data

    async def _fetch_ai_data(self, asset_id) -> Dict[str, Any]:
        """Fetch latest ML signal for an asset."""
        async with async_session_maker() as session:
            result = await session.execute(
                select(MLSignal)
                .where(and_(MLSignal.asset_id == asset_id, MLSignal.is_active == True))
                .order_by(desc(MLSignal.generated_at))
                .limit(1)
            )
            row = result.scalar_one_or_none()

        if not row:
            return {}

        data = {}
        if row.expected_return is not None:
            exp_ret = float(row.expected_return)
            data["expected_return"] = exp_ret
            if exp_ret > 0.05:
                data["prediction"] = "BUY"
            elif exp_ret < -0.05:
                data["prediction"] = "SELL"
            else:
                data["prediction"] = "HOLD"
        if row.confidence is not None:
            data["confidence"] = float(row.confidence)
        if row.risk_score is not None:
            data["risk_score"] = float(row.risk_score)
        if row.technical_factors:
            if "rsi" in row.technical_factors:
                data["ml_rsi"] = row.technical_factors["rsi"]
            if "macd" in row.technical_factors:
                data["ml_macd"] = row.technical_factors["macd"]

        return data

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
        self,
        symbol: str,
        market: str,
        candles: List[Candle],
        fundamental_data: Optional[Dict[str, Any]] = None,
        sentiment_data: Optional[Dict[str, Any]] = None,
        macro_data: Optional[Dict[str, Any]] = None,
        ai_data: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Build the scoring input dict from computed indicators and additional data."""
        if not candles:
            return None

        indicators = compute_all_indicators(candles)
        if not indicators:
            return None

        closes = [c.close for c in candles]
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
            "fundamental": fundamental_data or {},
            "sentiment": sentiment_data or {},
            "macro": macro_data or {},
            "ai": ai_data or {},
        }

        return scoring_input

    async def compute_and_persist_v2(
        self,
        target_date: Optional[date] = None,
        market: str = "NASDAQ",
    ) -> Dict[str, Any]:
        """Score an entire market with the v2 engine in one pass.

        1. Load every active equity's latest metrics.
        2. Run a single `score_market` call (cross-sectional ranks).
        3. Upsert one ScoreHistory row + one RawPerformanceScore row
           per asset.

        Returns a summary dict (counts, mean, stdev, grade distribution).
        """
        from sqlalchemy.dialects.postgresql import insert as pg_insert
        from sqlalchemy import literal
        from datetime import datetime as _dt

        if target_date is None:
            target_date = _dt.now(timezone.utc).date()

        async with async_session_maker() as session:
            asset_q = (
                select(Asset.id, Asset.symbol, Asset.asset_class)
                .where(and_(
                    Asset.active == True,
                    Asset.market == market,
                    Asset.asset_class.in_(["EQUITY", "ETF"]),
                ))
            )
            assets = (await session.execute(asset_q)).all()
            equities = [a for a in assets if a.asset_class == "EQUITY"]
            logger.info("compute_and_persist_v2: %d equities in %s", len(equities), market)

            # Load latest snapshot per asset (technical)
            snap_sub = (
                select(
                    MarketDataSnapshot.asset_id if False else MarketDataSnapshot.asset_id,  # placeholder
                )
            ) if False else None  # suppress; we'll inline the query

            metrics: Dict[str, Dict[str, Any]] = {}
            for asset_id, symbol, _ in equities:
                metrics[str(asset_id)] = {db: None for *_, db, _ in METRIC_UNIVERSE}

            # Technical (latest 1d snapshot per asset)
            tech_q = (
                select(MarketDataSnapshot)
                .where(MarketDataSnapshot.interval == "1d")
                .distinct(MarketDataSnapshot.asset_id)
                .order_by(
                    MarketDataSnapshot.asset_id,
                    MarketDataSnapshot.snapshot_time.desc(),
                )
            )
            for row in (await session.execute(tech_q)).scalars():
                m = metrics.get(str(row.asset_id))
                if not m: continue
                if row.rsi is not None:           m["rsi_14"]           = float(row.rsi)
                if row.macd_histogram is not None: m["macd_histogram"]   = float(row.macd_histogram)
                if row.volatility is not None:    m["realized_vol_30d"] = float(row.volatility)
                if row.volume_ratio is not None:   m["volume_ratio"]     = float(row.volume_ratio)
                if row.atr is not None:           m["atr_value"]        = float(row.atr)
                if row.bb_upper is not None and row.bb_lower is not None and row.bb_middle not in (None, 0):
                    m["bb_width"] = float((row.bb_upper - row.bb_lower) / row.bb_middle)

            # Fundamental (DISTINCT ON)
            fr_q = (
                select(
                    FundamentalRatio.asset_id, FundamentalRatio.pe, FundamentalRatio.pb,
                    FundamentalRatio.roe, FundamentalRatio.profit_margin, FundamentalRatio.eps,
                )
                .distinct(FundamentalRatio.asset_id)
                .order_by(FundamentalRatio.asset_id, FundamentalRatio.as_of.desc())
            )
            for aid, pe, pb, roe, pm, _ in (await session.execute(fr_q)):
                m = metrics.get(str(aid))
                if not m: continue
                if pe is not None: m["pe_ratio"]      = float(pe)
                if pb is not None: m["pb_ratio"]      = float(pb)
                if roe is not None: m["roe"]          = float(roe)
                if pm is not None:  m["profit_margin"]= float(pm)

            # News sentiment aggregate
            ns_q = select(
                NewsSentiment.asset_id,
                func.avg(NewsSentiment.sentiment_score),
                func.count(NewsSentiment.id),
            ).group_by(NewsSentiment.asset_id)
            for aid, avg_s, cnt in (await session.execute(ns_q)):
                m = metrics.get(str(aid))
                if not m: continue
                if avg_s is not None:
                    m["news_sentiment_avg"] = (float(avg_s) + 1.0) / 2.0
                m["news_volume"] = float(cnt) if cnt else None

            # Macro (single snapshot for all)
            macro_q = (
                select(MacroIndicator)
                .order_by(MacroIndicator.as_of.desc())
                .limit(20)
            )
            macro_vals: Dict[str, float] = {}
            for row in (await session.execute(macro_q)).scalars():
                if row.value is None: continue
                code = row.indicator_code
                val = float(row.value)
                if code == "^TNX" and "treasury_yield_10y" not in macro_vals:
                    macro_vals["treasury_yield_10y"] = val
                elif code == "DX-Y.NYB" and "dollar_index" not in macro_vals:
                    macro_vals["dollar_index"] = val
                elif code == "CL=F" and "oil_price" not in macro_vals:
                    macro_vals["oil_price"] = val
                elif code == "GC=F" and "gold_price" not in macro_vals:
                    macro_vals["gold_price"] = val
            for m in metrics.values():
                for k, v in macro_vals.items():
                    m[k] = v

            # ML signals (latest active)
            ml_q = (
                select(MLSignal)
                .where(MLSignal.is_active == True)
                .distinct(MLSignal.asset_id)
                .order_by(MLSignal.asset_id, MLSignal.generated_at.desc())
            )
            for row in (await session.execute(ml_q)).scalars():
                m = metrics.get(str(row.asset_id))
                if not m: continue
                if row.expected_return is not None: m["expected_return"] = float(row.expected_return)
                if row.confidence is not None:      m["confidence"]      = float(row.confidence)

        # Score in one pass
        results = score_market(metrics)

        # Persist
        written = 0
        for asset_id, symbol, _ in equities:
            hs = results.get(str(asset_id))
            if hs is None: continue
            sh_payload = {
                "dimension_scores": hs.dimension_scores,
                "overall_score": hs.overall_score,
                "grade": v2_grade(hs.overall_score),
            }
            hierarchy = {
                "sub_dimension_scores": hs.sub_dimension_scores,
                "aspect_scores": hs.aspect_scores,
                "sub_aspect_scores": hs.sub_aspect_scores,
                "coverage": hs.coverage,
            }
            await self._persist_score_history(
                asset_id, target_date, sh_payload, market, hierarchy=hierarchy,
            )
            written += 1

        # Summary
        overalls = [hs.overall_score for hs in results.values()]
        from collections import Counter
        grades = Counter(v2_grade(s) for s in overalls)
        mean = sum(overalls) / len(overalls) if overalls else 0.0
        stdev = (sum((x - mean) ** 2 for x in overalls) / len(overalls)) ** 0.5 if overalls else 0.0

        summary = {
            "status": "completed",
            "date": target_date.isoformat(),
            "market": market,
            "equities_total": len(equities),
            "written": written,
            "overall_mean": round(mean, 2),
            "overall_stdev": round(stdev, 2),
            "grade_distribution": dict(grades),
        }
        logger.info("compute_and_persist_v2 complete: %s", summary)
        return summary

    async def _persist_score_history(
        self,
        asset_id,
        target_date: date,
        scored: Dict[str, Any],
        market: str,
        hierarchy: Optional[Dict[str, Any]] = None,
    ):
        """Persist scored results to ScoreHistory and RawPerformanceScore.

        Args:
            asset_id: Asset UUID.
            target_date: Trading date.
            scored: Legacy flat-dim dict from `ScoringService.analyze`
                (kept for backward compatibility).
            market: Market code (NASDAQ, NYSE, ...).
            hierarchy: Optional 4-level hierarchy from
                `scoring_engine_v2.score_market`. If provided, all 4
                levels are persisted to `raw_performance_scores`. If
                missing, the L1 dimension_scores from `scored` are used
                instead.
        """
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

            # Persist the full 4-level hierarchy to RawPerformanceScore so
            # the dashboard can read L2/L3/L4 without regex fallbacks.
            if hierarchy is None:
                sub_dim = {}
                aspects = {}
                sub_aspects = {}
            else:
                sub_dim = dict(hierarchy.get("sub_dimension_scores", {}))
                aspects = dict(hierarchy.get("aspect_scores", {}))
                sub_aspects = dict(hierarchy.get("sub_aspect_scores", {}))

            rps_stmt = pg_insert(RawPerformanceScore).values(
                asset_id=asset_id,
                market=market,
                exchange=market,
                captured_at=datetime.now(timezone.utc),
                dimension_scores=dimension_scores,
                sub_dimension_scores=sub_dim,
                aspect_scores=aspects,
                sub_aspect_scores=sub_aspects,
                context={
                    "overall_score": overall_score,
                    "grade": grade,
                    "coverage": hierarchy.get("coverage", 0.0) if hierarchy else 0.0,
                },
            )
            # RawPerformanceScore has no natural unique key other than
            # the auto id, so we just insert one row per pipeline call.
            await session.execute(rps_stmt)
            await session.commit()
