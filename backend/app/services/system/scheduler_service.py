"""
Scheduler Service - Tier 9 System Service
Enhanced with full automation:
- All platform jobs registered automatically
- Model training (weekly)
- Signal updates (every 15 minutes)
- Data backup (daily)
- Data archival (weekly)
- Log cleanup (daily)
- Missed job recovery on startup
"""
import asyncio
import os
import re as _re
import uuid as _uuid
from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from datetime import date as _date
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.config import get_settings
from app.db.base import async_session_maker
from app.models.models import (
    Asset,
    CurrencyRate,
    IntlPriceCandle,
    MacroIndicator,
    MarketDataSnapshot,
    News,
    ScoreHistory,
)
from app.models.scoring_snapshot import ScoringSnapshot, SnapshotLevel, SnapshotTier

from ..core import BaseService


@dataclass
class ScheduledJob:
    """Definition of a scheduled job."""
    name: str
    coroutine_func: Callable[[], Coroutine[Any, Any, Any]]
    interval_seconds: int
    enabled: bool = True
    last_run: datetime | None = None
    next_run: datetime | None = None
    run_count: int = 0
    error_count: int = 0
    _task: asyncio.Task | None = field(default=None, repr=False)


class SchedulerService(BaseService):
    """
    Background scheduler for periodic platform jobs.
    All jobs are registered automatically on startup.
    """

    def __init__(self, service_name: str = "SchedulerService",
                 scoring_service=None,
                 metrics_service=None,
                 health_checker=None,
                 cache_service=None,
                 nasdaq_service=None,
                 data_ingest_service=None,
                 data_integrity_service=None,
                 ml_training_service=None,
                 backup_service=None,
                 news_service=None,
                 ingestion_service=None,
                 orderbook_service=None):
        super().__init__(service_name)
        self._jobs: dict[str, ScheduledJob] = {}
        self._running: bool = False
        self._main_task: asyncio.Task | None = None
        self.settings = get_settings()
        self.scoring_service = scoring_service
        self.metrics_service = metrics_service
        self.health_checker = health_checker
        self.cache_service = cache_service
        self.nasdaq_service = nasdaq_service
        self.data_ingest_service = data_ingest_service
        self.data_integrity_service = data_integrity_service
        self.ml_training_service = ml_training_service
        self.backup_service = backup_service
        self.news_service = news_service
        self.ingestion_service = ingestion_service
        self.orderbook_service = orderbook_service

    async def initialize(self) -> None:
        self._running = True
        self._main_task = asyncio.create_task(self._scheduler_loop())
        self.logger.info("SchedulerService initialized")

        await self._register_default_jobs()

        if self.ingestion_service is not None:
            try:
                await self.ingestion_service.initialize()
                self.logger.info("ContinuousNewsIngestionService started")
            except Exception as exc:
                self.logger.error("Failed to start ContinuousNewsIngestionService: %s", exc)

    async def _register_default_jobs(self) -> None:
        """Register ALL platform jobs automatically."""

        # === DATA INGESTION JOBS ===

        async def nasdaq_daily_update_job():
            if self.nasdaq_service:
                await self.nasdaq_service.initialize()
                result = await self.nasdaq_service.daily_update()
                await self.nasdaq_service.shutdown()
                return result
            return {"status": "skipped", "reason": "service not available"}

        self.register_job(
            name="NasdaqDailyUpdate",
            coroutine_func=nasdaq_daily_update_job,
            interval_seconds=86400,
        )

        async def data_ingestion_job():
            if self.data_ingest_service is not None:
                await self.data_ingest_service.initialize()
                if hasattr(self.data_ingest_service, "batch_ingest"):
                    import inspect
                    sig = inspect.signature(self.data_ingest_service.batch_ingest)
                    if "requests" in sig.parameters:
                        result = await self.data_ingest_service.batch_ingest([])
                    else:
                        result = await self.data_ingest_service.batch_ingest(
                            symbols=[], market=None
                        )
                else:
                    result = {"status": "no batch_ingest method"}
                await self.data_ingest_service.shutdown()
                return result
            return {"status": "skipped", "reason": "service not available"}

        self.register_job(
            name="DataIngestion",
            coroutine_func=data_ingestion_job,
            interval_seconds=21600,
        )

        # === ML / AI JOBS ===

        async def model_training_job():
            if self.ml_training_service:
                await self.ml_training_service.initialize()
                result = await self.ml_training_service.retrain_all()
                await self.ml_training_service.shutdown()
                return result
            return self._fallback_model_training()

        self.register_job(
            name="ModelTraining",
            coroutine_func=model_training_job,
            interval_seconds=604800,
        )

        async def signal_update_job():
            return await self._generate_signals()

        self.register_job(
            name="SignalUpdate",
            coroutine_func=signal_update_job,
            interval_seconds=900,
        )

        # === ORDER BOOK SNAPSHOT JOB ===
        # Captures top-5 bid/ask snapshots every 15 minutes (900 seconds)
        # for tracked symbols and persists them to the intl_order_book table.

        async def orderbook_snapshot_job():
            if self.orderbook_service is None:
                return {"status": "skipped", "reason": "orderbook_service not available"}
            try:
                tracked = await self._get_tracked_symbols()
                results: dict[str, bool] = {}
                async with async_session_maker() as session:
                    for sym in tracked:
                        snap_dict = await self.orderbook_service.get_latest_orderbook(sym)
                        snaps = self._dict_to_snapshot(snap_dict)
                        if snaps:
                            await self.orderbook_service.persist_snapshots(
                                snaps, sym, session
                            )
                        results[sym] = True
                    await session.commit()
                return {
                    "status": "success",
                    "symbols_processed": len(results),
                    "symbols": list(results.keys()),
                }
            except Exception as exc:
                self.logger.error("OrderBookSnapshot job failed: %s", exc)
                return {"status": "error", "error": str(exc)}

        self.register_job(
            name="OrderBookSnapshot",
            coroutine_func=orderbook_snapshot_job,
            interval_seconds=900,
        )

        # === SCORING & ANALYSIS JOBS ===

        # ------------------------------------------------------------------
        # Idempotency helper: probes the unique constraint before running
        # expensive scoring. Returns (skip_reason|None) to short-circuit.
        # ------------------------------------------------------------------
        async def _scoring_idempotency_probe(
            tier: SnapshotTier,
            effective_at: datetime,
            market: str = "NASDAQ",
        ) -> str | None:
            """Return skip reason if this tier+effective_at already has rows."""
            async with async_session_maker() as session:
                probe_q = (
                    select(func.count())
                    .select_from(ScoringSnapshot)
                    .join(Asset, Asset.id == ScoringSnapshot.asset_id)
                    .where(
                        and_(
                            ScoringSnapshot.snapshot_tier == tier.value,
                            ScoringSnapshot.effective_at == effective_at,
                            Asset.market == market,
                        )
                    )
                )
                cnt = (await session.execute(probe_q)).scalar_one()
            if cnt and cnt > 0:
                return "already_computed"
            return None

        def _floor_to_hour(dt: datetime) -> datetime:
            return dt.replace(minute=0, second=0, microsecond=0)

        def _floor_to_day(dt: datetime) -> datetime:
            return dt.replace(hour=0, minute=0, second=0, microsecond=0)

        async def _promote_scorehistory_to_snapshot(
            target_date: _date,
            tier: SnapshotTier,
            effective_at: datetime,
            market: str = "NASDAQ",
        ) -> int:
            """Read ScoreHistory rows for target_date and explode them into
            4-level ScoringSnapshot rows. Returns the count of snapshots rows
            inserted (overall + dimension + sub-dimension + aspect + sub-aspect).
            """
            async with async_session_maker() as session:
                sh_q = (
                    select(
                        ScoreHistory.asset_id,
                        ScoreHistory.overall_score,
                        ScoreHistory.dimension_scores,
                        ScoreHistory.sub_dimension_scores,
                        ScoreHistory.aspect_scores,
                        ScoreHistory.sub_aspect_scores,
                        ScoreHistory.grade,
                    )
                    .join(Asset, Asset.id == ScoreHistory.asset_id)
                    .where(
                        and_(
                            ScoreHistory.date == target_date,
                            Asset.market == market,
                            Asset.active,
                        )
                    )
                )
                sh_rows = (await session.execute(sh_q)).all()

                snapshot_rows: list[dict[str, Any]] = []

                def _append(
                    asset_id,
                    level: SnapshotLevel,
                    level_key: str,
                    level_name: str,
                    score: float,
                ):
                    snapshot_rows.append({
                        "id": _uuid.uuid4(),
                        "asset_id": asset_id,
                        "date": target_date,
                        "snapshot_tier": tier.value,
                        "effective_at": effective_at,
                        "level": level.value,
                        "level_key": level_key,
                        "level_name": level_name,
                        "score": score,
                        "score_change": None,
                        "industry": None,
                        "company_id": None,
                        "timestamp": datetime.now(UTC),
                        "extra_fields": {},
                    })

                for asset_id, overall, dims, sub_dims, aspects, sub_aspects, grade in sh_rows:
                    if overall is None:
                        continue
                    _append(asset_id, SnapshotLevel.OVERALL, "overall", "Overall", float(overall))

                    if dims:
                        for k, v in dims.items():
                            try:
                                fv = float(v)
                            except (TypeError, ValueError):
                                continue
                            _append(asset_id, SnapshotLevel.DIMENSION, k, k.replace("_", " ").title(), fv)

                    if sub_dims:
                        for k, v in sub_dims.items():
                            try:
                                fv = float(v)
                            except (TypeError, ValueError):
                                continue
                            _append(asset_id, SnapshotLevel.SUB_DIMENSION, k, k.replace("_", " ").title(), fv)

                    if aspects:
                        for k, v in aspects.items():
                            try:
                                fv = float(v)
                            except (TypeError, ValueError):
                                continue
                            _append(asset_id, SnapshotLevel.ASPECT, k, k.replace("_", " ").title(), fv)

                    if sub_aspects:
                        for k, v in sub_aspects.items():
                            try:
                                fv = float(v)
                            except (TypeError, ValueError):
                                continue
                            _append(asset_id, SnapshotLevel.SUB_ASPECT, k, k.replace("_", " ").title(), fv)

                if not snapshot_rows:
                    return 0

                # Upsert via unique composite index (asset_id, tier, effective_at, level, level_key)
                # We batch-insert under the unique composite index for snapshot_tier+effective_at+asset+level+level_key.
                chunk_size = 5000
                total_inserted = 0
                for i in range(0, len(snapshot_rows), chunk_size):
                    chunk = snapshot_rows[i:i + chunk_size]
                    stmt = pg_insert(ScoringSnapshot).values(chunk)
                    stmt = stmt.on_conflict_do_nothing(
                        index_elements=["asset_id", "snapshot_tier", "effective_at", "level", "level_key"],
                    )
                    res = await session.execute(stmt)
                    total_inserted += int(getattr(res, "rowcount", len(chunk)))
                await session.commit()
                return total_inserted

        async def daily_score_recalculation_job():
            from app.services.analysis.score_history_pipeline import (
                ScoreHistoryPipeline,
            )
            now_utc = datetime.now(UTC)
            effective_day = _floor_to_day(now_utc)
            target_date = effective_day.date()
            result_base: dict[str, Any] = {
                "tier": SnapshotTier.DAILY.value,
                "effective_at": effective_day.isoformat(),
                "date": target_date.isoformat(),
                "written": 0,
                "paired_hourly_written": 0,
                "skip_reason": None,
            }

            skip = await _scoring_idempotency_probe(SnapshotTier.DAILY, effective_day, market="NASDAQ")
            if skip:
                result_base["skip_reason"] = skip
                return result_base

            pipeline = ScoreHistoryPipeline()
            await pipeline.initialize()
            t0 = datetime.now(UTC)
            try:
                pipe_result = await pipeline.compute_and_persist_v2(
                    market="NASDAQ",
                    target_date=target_date,
                )
                if pipe_result.get("written", 0) == 0:
                    pipe_result = await pipeline.compute_and_persist_all(
                        market="NASDAQ",
                        batch_size=100,
                        target_date=target_date,
                    )
                result_base["scorehistory_written"] = pipe_result.get("written", 0)
                written_snap = await _promote_scorehistory_to_snapshot(
                    target_date,
                    SnapshotTier.DAILY,
                    effective_day,
                    market="NASDAQ",
                )
                result_base["written"] = written_snap

                # Guarantee paired hourly reference at 00:00 UTC so current_vs_daily
                # delta frame always has a matching hourly anchor at day boundary.
                paired_hourly_skip = await _scoring_idempotency_probe(
                    SnapshotTier.HOURLY, effective_day, market="NASDAQ"
                )
                if not paired_hourly_skip:
                    paired = await _promote_scorehistory_to_snapshot(
                        target_date,
                        SnapshotTier.HOURLY,
                        effective_day,
                        market="NASDAQ",
                    )
                    result_base["paired_hourly_written"] = paired
                else:
                    result_base["paired_hourly_skip_reason"] = paired_hourly_skip

                t1 = datetime.now(UTC)
                result_base["duration_ms"] = int((t1 - t0).total_seconds() * 1000)
                self.logger.info(
                    "DailyScoreRecalculation complete: %d snapshots, paired_hourly=%d, duration=%dms",
                    written_snap, result_base["paired_hourly_written"], result_base["duration_ms"]
                )
                return result_base
            except Exception as e:
                self.logger.error(f"DailyScoreRecalculation failed: {e}", exc_info=True)
                result_base["status"] = "error"
                result_base["error"] = str(e)
                return result_base
            finally:
                await pipeline.shutdown()

        self.register_job(
            name="DailyScoreRecalculation",
            coroutine_func=daily_score_recalculation_job,
            interval_seconds=86400,
        )

        async def hourly_score_recompute_job():
            """Full 4-level hierarchy scoring, tier=hourly, effective_at=floor_1h(UTC)."""
            from app.services.analysis.score_history_pipeline import (
                ScoreHistoryPipeline,
            )
            now_utc = datetime.now(UTC)
            effective_hour = _floor_to_hour(now_utc)
            target_date = effective_hour.date()

            result_base: dict[str, Any] = {
                "tier": SnapshotTier.HOURLY.value,
                "effective_at": effective_hour.isoformat(),
                "date": target_date.isoformat(),
                "written": 0,
                "skip_reason": None,
            }

            skip = await _scoring_idempotency_probe(SnapshotTier.HOURLY, effective_hour, market="NASDAQ")
            if skip:
                result_base["skip_reason"] = skip
                return result_base

            pipeline = ScoreHistoryPipeline()
            await pipeline.initialize()
            t0 = datetime.now(UTC)
            try:
                # We compute through the v2 engine (cross-sectional ranks are
                # market-relative so still valid on hourly cadence).
                pipe_result = await pipeline.compute_and_persist_v2(
                    market="NASDAQ",
                    target_date=target_date,
                )
                result_base["scorehistory_written"] = pipe_result.get("written", 0)
                written_snap = await _promote_scorehistory_to_snapshot(
                    target_date,
                    SnapshotTier.HOURLY,
                    effective_hour,
                    market="NASDAQ",
                )
                result_base["written"] = written_snap
                t1 = datetime.now(UTC)
                result_base["duration_ms"] = int((t1 - t0).total_seconds() * 1000)
                self.logger.info(
                    "HourlyScoreRecompute complete: %d snapshots, duration=%dms",
                    written_snap, result_base["duration_ms"]
                )
                return result_base
            except Exception as e:
                self.logger.error(f"HourlyScoreRecompute failed: {e}", exc_info=True)
                result_base["status"] = "error"
                result_base["error"] = str(e)
                return result_base
            finally:
                await pipeline.shutdown()

        self.register_job(
            name="HourlyScoreRecompute",
            coroutine_func=hourly_score_recompute_job,
            interval_seconds=3600,
        )

        async def fast_indicators_5m_job():
            """Every 5 minutes: compute RSI/MACD/BB%/volatility/momentum per active
            NASDAQ asset and write MarketDataSnapshot with interval='5m'. Skips
            cleanly if the market is closed using a lightweight clock check.
            """
            from app.services.analysis.technical_indicators import (
                Candle,
                compute_all_indicators,
            )

            now_utc = datetime.now(UTC)
            # Lightweight NYSE/NASDAQ market hours check (9:30-16:00 ET => 13:30-20:00 UTC in winter).
            # We still run outside hours so that pre/post/weekend pipelines produce
            # stable rows; the TemporalSnapshotService weights by age.
            effective_5m = now_utc.replace(minute=(now_utc.minute // 5) * 5, second=0, microsecond=0)
            result_base: dict[str, Any] = {
                "interval": "5m",
                "effective_at": effective_5m.isoformat(),
                "written_rows": 0,
                "skipped_assets": 0,
                "duration_ms": 0,
                "skip_reason": None,
            }
            t0 = datetime.now(UTC)

            try:
                async with async_session_maker() as session:
                    active_q = (
                        select(Asset.id, Asset.symbol, Asset.market, Asset.asset_class)
                        .where(
                            and_(
                                Asset.active,
                                Asset.market == "NASDAQ",
                                Asset.asset_class.in_(["EQUITY", "ETF"]),
                            )
                        )
                        .limit(200)
                    )
                    assets = (await session.execute(active_q)).all()

                if not assets:
                    result_base["skip_reason"] = "no_active_assets"
                    return result_base

                rows_to_write: list[dict[str, Any]] = []
                for asset_id, symbol, market, asset_class in assets:
                    try:
                        # Fetch latest ~120 1-minute candles (or 1d fallback).
                        candle_q = (
                            select(IntlPriceCandle)
                            .where(
                                and_(
                                    IntlPriceCandle.asset_id == asset_id,
                                    IntlPriceCandle.timeframe.in_(["1m", "5m", "1d"]),
                                )
                            )
                            .order_by(IntlPriceCandle.timestamp.desc())
                            .limit(120)
                        )
                        async with async_session_maker() as s2:
                            candle_rows = (await s2.execute(candle_q)).scalars().all()
                        if len(candle_rows) < 20:
                            result_base["skipped_assets"] += 1
                            continue
                        candles: list[Candle] = []
                        for c in reversed(candle_rows):
                            try:
                                candles.append(Candle(
                                    open=float(c.open),
                                    high=float(c.high),
                                    low=float(c.low),
                                    close=float(c.close),
                                    volume=float(c.volume) if c.volume else 0.0,
                                ))
                            except (TypeError, ValueError):
                                continue
                        if len(candles) < 20:
                            result_base["skipped_assets"] += 1
                            continue
                        inds = compute_all_indicators(candles)
                        if not inds:
                            result_base["skipped_assets"] += 1
                            continue
                        closes = [c.close for c in candles]
                        last_close = closes[-1] if closes else 0.0
                        rows_to_write.append({
                            "id": _uuid.uuid4(),
                            "asset_id": asset_id,
                            "interval": "5m",
                            "snapshot_time": effective_5m,
                            "open_price": candles[-1].open if candles else None,
                            "high_price": candles[-1].high if candles else None,
                            "low_price": candles[-1].low if candles else None,
                            "close_price": last_close,
                            "volume": int(candles[-1].volume) if candles else 0,
                            "turnover": None,
                            "rsi": inds.get("rsi"),
                            "macd": inds.get("macd"),
                            "macd_signal": inds.get("macd_signal"),
                            "macd_histogram": inds.get("macd_histogram"),
                            "bb_upper": inds.get("bb_upper"),
                            "bb_middle": inds.get("bb_middle"),
                            "bb_lower": inds.get("bb_lower"),
                            "bb_percent_b": inds.get("bb_percent_b"),
                            "bb_width": inds.get("bb_width"),
                            "sma_20": inds.get("sma_20"),
                            "sma_50": inds.get("sma_50"),
                            "sma_200": inds.get("sma_200"),
                            "ema_12": inds.get("ema_12"),
                            "ema_26": inds.get("ema_26"),
                            "volatility": inds.get("volatility"),
                            "volume_ratio": inds.get("volume_ratio"),
                            "momentum": inds.get("momentum"),
                            "stoch_k": inds.get("stoch_k"),
                            "stoch_d": inds.get("stoch_d"),
                            "atr": inds.get("atr"),
                            "price_change_pct": inds.get("price_change_pct"),
                        })
                    except Exception as inner_e:
                        self.logger.warning(f"FastIndicators5m skipped {symbol}: {inner_e}")
                        result_base["skipped_assets"] += 1
                        continue

                if rows_to_write:
                    chunk_size = 500
                    async with async_session_maker() as session:
                        for i in range(0, len(rows_to_write), chunk_size):
                            chunk = rows_to_write[i:i + chunk_size]
                            stmt = pg_insert(MarketDataSnapshot).values(chunk)
                            # Conflict on (asset_id, interval, snapshot_time) if such index exists; else do nothing.
                            try:
                                stmt = stmt.on_conflict_do_nothing(
                                    index_elements=["asset_id", "interval", "snapshot_time"],
                                )
                            except Exception:
                                # Fallback: just do insert, caller will log duplicates.
                                pass
                            res = await session.execute(stmt)
                            result_base["written_rows"] += int(getattr(res, "rowcount", len(chunk)))
                        await session.commit()

                t1 = datetime.now(UTC)
                result_base["duration_ms"] = int((t1 - t0).total_seconds() * 1000)
                self.logger.info(
                    "FastIndicators5m complete: written=%d, skipped=%d, duration=%dms",
                    result_base["written_rows"], result_base["skipped_assets"], result_base["duration_ms"]
                )
                return result_base
            except Exception as e:
                self.logger.error(f"FastIndicators5m failed: {e}", exc_info=True)
                result_base["status"] = "error"
                result_base["error"] = str(e)
                t1 = datetime.now(UTC)
                result_base["duration_ms"] = int((t1 - t0).total_seconds() * 1000)
                return result_base

        self.register_job(
            name="FastIndicators5m",
            coroutine_func=fast_indicators_5m_job,
            interval_seconds=300,
        )

        async def coefficient_snapshot_daily_job():
            """At 00:10 UTC: persist the current 4-level weight coefficients into
            coefficient_history rows tagged with tier=DAILY and effective_at of the
            prior midnight boundary.
            """
            from app.services.ml.coefficient_learning_service import (
                CoefficientLearningService,
            )

            now_utc = datetime.now(UTC)
            effective_day = _floor_to_day(now_utc)
            result_base: dict[str, Any] = {
                "tier": SnapshotTier.DAILY.value,
                "effective_at": effective_day.isoformat(),
                "written": 0,
                "duration_ms": 0,
                "skip_reason": None,
            }
            t0 = datetime.now(UTC)

            try:
                service = CoefficientLearningService()
                if hasattr(service, "initialize"):
                    init_coro = service.initialize()
                    if asyncio.iscoroutine(init_coro):
                        await init_coro

                coefficients_result = None
                # Attempt to learn or load current coefficients.
                for method_name in ("learn_coefficients", "get_current_coefficients", "get_coefficients"):
                    if hasattr(service, method_name):
                        fn = getattr(service, method_name)
                        try:
                            if method_name == "learn_coefficients":
                                coefficients_result = await fn([])
                            else:
                                res = fn()
                                if asyncio.iscoroutine(res):
                                    coefficients_result = await res
                                else:
                                    coefficients_result = res
                            if coefficients_result:
                                break
                        except Exception as inner:
                            self.logger.warning(f"CoefficientSnapshotDaily {method_name}: {inner}")
                            continue

                if not coefficients_result:
                    result_base["skip_reason"] = "no_coefficients"
                    if hasattr(service, "shutdown"):
                        sdn_coro = service.shutdown()
                        if asyncio.iscoroutine(sdn_coro):
                            await sdn_coro
                    return result_base

                # Normalize coefficients_result into a list of weight rows.
                weights: list[dict[str, Any]] = []
                if isinstance(coefficients_result, dict):
                    # Best-effort: accept common coefficient payload shapes.
                    for lvl_key in ("dimensions", "dimension_weights", "dimension", "sub_dimensions", "aspects", "sub_aspects"):
                        bucket = coefficients_result.get(lvl_key) or {}
                        if isinstance(bucket, dict):
                            for k, v in bucket.items():
                                try:
                                    fv = float(v)
                                except (TypeError, ValueError):
                                    continue
                                weights.append({
                                    "level": lvl_key.replace("_weights", ""),
                                    "level_key": k,
                                    "weight": fv,
                                })
                    # Coefficient matrix (per-asset) handling is left to the
                    # CoefficientLearningService own persistence; here we only
                    # write a market-wide summary row.
                    result_base["weight_rows_detected"] = len(weights)

                # Attempt to persist via coefficient_history model if available.
                try:
                    from app.models.models import CoefficientHistory
                    async with async_session_maker() as session:
                        # Probe: has any row been written for this effective_at?
                        probe_q = (
                            select(func.count())
                            .select_from(CoefficientHistory)
                            .where(CoefficientHistory.captured_at == effective_day)
                        )
                        try:
                            exists = (await session.execute(probe_q)).scalar_one()
                        except Exception:
                            exists = 0
                        if exists:
                            result_base["skip_reason"] = "already_computed"
                        else:
                            # Write a single aggregate marker row with tier tag in context.
                            payload = {
                                "market": "NASDAQ",
                                "tier": SnapshotTier.DAILY.value,
                                "weights_summary": weights,
                                "raw": coefficients_result if isinstance(coefficients_result, dict) else str(coefficients_result),
                            }
                            import json as _json
                            context_json = _json.dumps(payload, default=str)
                            try:
                                ch_row = CoefficientHistory(
                                    market="NASDAQ",
                                    captured_at=effective_day,
                                    context=context_json,
                                    score=None,
                                    created_at=datetime.now(UTC),
                                )
                                session.add(ch_row)
                                await session.commit()
                                result_base["written"] = 1
                            except Exception as insert_err:
                                self.logger.warning(f"CoefficientSnapshotDaily insert failed: {insert_err}")
                                result_base["written"] = 0
                except Exception as model_err:
                    self.logger.warning(f"CoefficientSnapshotDaily: CoefficientHistory not usable: {model_err}")
                    result_base["skip_reason"] = "model_unavailable"

                if hasattr(service, "shutdown"):
                    sdn_coro = service.shutdown()
                    if asyncio.iscoroutine(sdn_coro):
                        await sdn_coro

                t1 = datetime.now(UTC)
                result_base["duration_ms"] = int((t1 - t0).total_seconds() * 1000)
                self.logger.info(
                    "CoefficientSnapshotDaily complete: written=%d, duration=%dms",
                    result_base["written"], result_base["duration_ms"]
                )
                return result_base
            except Exception as e:
                self.logger.error(f"CoefficientSnapshotDaily failed: {e}", exc_info=True)
                result_base["status"] = "error"
                result_base["error"] = str(e)
                t1 = datetime.now(UTC)
                result_base["duration_ms"] = int((t1 - t0).total_seconds() * 1000)
                return result_base

        self.register_job(
            name="CoefficientSnapshotDaily",
            coroutine_func=coefficient_snapshot_daily_job,
            interval_seconds=86400,
        )

        async def market_score_trend_recompute_job():
            from app.services.analysis.market_score_trend_service import (
                MarketScoreTrendService,
            )
            service = MarketScoreTrendService()
            await service.initialize()
            try:
                result = await service.compute_and_persist(market="NASDAQ")
                return result
            except Exception as e:
                self.logger.error(f"MarketScoreTrendRecompute failed: {e}", exc_info=True)
                return {"status": "error", "error": str(e)}
            finally:
                await service.shutdown()

        self.register_job(
            name="MarketScoreTrendRecompute",
            coroutine_func=market_score_trend_recompute_job,
            interval_seconds=86400,
        )

        # === SYSTEM MAINTENANCE JOBS ===

        async def metrics_aggregation_job():
            if self.metrics_service:
                await self.metrics_service.initialize()
                result = self.metrics_service.get_all_metrics()
                await self.metrics_service.shutdown()
                return result
            return {"status": "skipped", "reason": "service not available"}

        self.register_job(
            name="MetricsAggregation",
            coroutine_func=metrics_aggregation_job,
            interval_seconds=900,
        )

        async def health_check_job():
            if self.health_checker:
                await self.health_checker.initialize()
                result = await self.health_checker.health_check()
                await self.health_checker.shutdown()
                return result
            return {"status": "skipped", "reason": "service not available"}

        self.register_job(
            name="HealthCheck",
            coroutine_func=health_check_job,
            interval_seconds=300,
        )

        async def db_watchdog_job():
            from app.services.core.database_service import DatabaseService
            from app.services.core.dependency_container import get_global_container

            container = get_global_container()
            if not container:
                return {"status": "skipped", "reason": "no global container"}

            db_service = container.get("database_service")
            if not isinstance(db_service, DatabaseService):
                return {"status": "skipped", "reason": "database service not found"}

            health = await db_service.health_check()
            if health["status"] != "healthy":
                self.logger.warning("Database connection lost! Attempting recovery...")
                success = await db_service.reconnect()
                return {"status": "recovered" if success else "failed", "health": health}

            return {"status": "healthy", "health": health}

        self.register_job(
            name="DatabaseWatchdog",
            coroutine_func=db_watchdog_job,
            interval_seconds=60,  # Check every minute
        )

        async def cache_warming_job():
            if self.cache_service is not None:
                await self.cache_service.initialize()
                await self.cache_service.clear()
                stats = self.cache_service.get_stats()
                await self.cache_service.shutdown()
                return {"status": "completed", "stats": stats}
            return {"status": "skipped", "reason": "service not available"}

        self.register_job(
            name="CacheWarming",
            coroutine_func=cache_warming_job,
            interval_seconds=1800,
        )

        async def data_integrity_job():
            if self.data_integrity_service:
                await self.data_integrity_service.initialize()
                result = await self.data_integrity_service.run_full_integrity_check()
                await self.data_integrity_service.shutdown()
                return result
            return {"status": "skipped", "reason": "service not available"}

        self.register_job(
            name="DataIntegrityVerification",
            coroutine_func=data_integrity_job,
            interval_seconds=3600,
        )

        # === BACKUP & ARCHIVAL JOBS ===

        async def backup_job():
            if self.backup_service is not None:
                await self.backup_service.initialize()
                result = await self.backup_service.backup_database()
                await self.backup_service.shutdown()
                return result
            return await self._run_backup()

        self.register_job(
            name="DataBackup",
            coroutine_func=backup_job,
            interval_seconds=86400,
        )

        async def archival_job():
            return await self._run_archival()

        self.register_job(
            name="DataArchival",
            coroutine_func=archival_job,
            interval_seconds=604800,
        )

        async def log_cleanup_job():
            return await self._run_log_cleanup()

        self.register_job(
            name="LogCleanup",
            coroutine_func=log_cleanup_job,
            interval_seconds=86400,
        )

        # === DATA BACKFILL JOBS ===

        async def news_backfill_job():
            """Backfill 5 years of news history."""
            return await self._backfill_news(years=5)

        self.register_job(
            name="NewsBackfill",
            coroutine_func=news_backfill_job,
            interval_seconds=86400 * 7,  # Weekly
        )

        # === REAL-TIME DATA REFRESH JOBS ===

        async def daily_news_refresh_job():
            """Fallback news refresh if continuous ingestion is disabled or unhealthy."""
            if self.ingestion_service is not None:
                return {"status": "skipped", "reason": "continuous_ingestion_active"}
            if self.news_service:
                return await self._refresh_news()
            return {"status": "skipped", "reason": "no_news_service"}

        self.register_job(
            name="DailyNewsRefresh",
            coroutine_func=daily_news_refresh_job,
            interval_seconds=3600,  # 1 hour fallback
        )

        async def continuous_news_supervisor_job():
            """Supervise continuous news ingestion service."""
            if self.ingestion_service is None:
                return {"status": "skipped", "reason": "ingestion_service_not_available"}
            try:
                if not getattr(self.ingestion_service, "_initialized", False):
                    await self.ingestion_service.initialize()
                return {"status": "running", "sources": len(self.ingestion_service._source_loops)}
            except Exception as exc:
                return {"status": "error", "error": str(exc)}

        self.register_job(
            name="ContinuousNewsIngestion",
            coroutine_func=continuous_news_supervisor_job,
            interval_seconds=900,  # 15 minutes supervisor check
        )

        async def fundamental_data_refresh_job():
            """Refresh fundamental data (financial statements and ratios) daily."""
            return await self._refresh_fundamentals()

        self.register_job(
            name="FundamentalDataRefresh",
            coroutine_func=fundamental_data_refresh_job,
            interval_seconds=86400,  # Daily
        )

        async def sec_financials_bulk_job():
            """Bulk-refresh quarterly financial statements via free SEC EDGAR."""
            if self.nasdaq_service:
                await self.nasdaq_service.initialize()
                result = await self.nasdaq_service.backfill_sec_financials(
                    min_quarters=20,
                )
                await self.nasdaq_service.shutdown()
                return result
            return {"status": "skipped", "reason": "nasdaq_service not available"}

        self.register_job(
            name="SecFinancialsBulkRefresh",
            coroutine_func=sec_financials_bulk_job,
            interval_seconds=604800,  # Weekly
        )

        async def macro_data_refresh_job():
            """Refresh macro indicators and currency rates daily."""
            return await self._refresh_macro_data()

        self.register_job(
            name="MacroDataRefresh",
            coroutine_func=macro_data_refresh_job,
            interval_seconds=86400,  # Daily
        )

        async def macro_forecast_refresh_job():
            """Generate free in-process macro forecasts from stored history."""
            return await self._refresh_macro_forecasts()

        self.register_job(
            name="MacroForecastRefresh",
            coroutine_func=macro_forecast_refresh_job,
            interval_seconds=21600,  # every 6h
        )

        async def master_data_refresh_job():
            """Refresh market indices weekly."""
            return await self._refresh_master_data()

        self.register_job(
            name="MasterDataRefresh",
            coroutine_func=master_data_refresh_job,
            interval_seconds=604800,  # Weekly
        )

        async def intl_candle_refresh_job():
            """Refresh international price candles every 6 hours during market hours."""
            return await self._refresh_intl_candles()

        self.register_job(
            name="IntlCandleRefresh",
            coroutine_func=intl_candle_refresh_job,
            interval_seconds=21600,  # 6 hours
        )

        self.logger.info(f"Registered {len(self._jobs)} platform jobs")

    # ------------------------------------------------------------------ #
    # Backfill helpers
    # ------------------------------------------------------------------ #

    async def _backfill_news(self, years: int = 5) -> dict[str, Any]:
        """Backfill historical news data for active assets.

        Uses the NewsService (which wraps yfinance + multi-source fetchers)
        when available, falling back to direct yfinance calls.
        """
        from app.db.base import async_session_maker

        end_date = datetime.now(UTC)
        start_date = end_date - timedelta(days=years * 365)

        results = {"news_inserted": 0, "errors": []}

        try:
            async with async_session_maker() as session:
                all_assets = await session.execute(
                    select(Asset.id, Asset.symbol, Asset.asset_class, Asset.market)
                    .where(
                        and_(
                            Asset.active,
                            Asset.market == "NASDAQ",
                            Asset.asset_class.in_(["EQUITY", "ETF"]),
                        )
                    )
                    .limit(200)
                )
                assets = all_assets.fetchall()

            for asset_id, symbol, asset_class, market in assets:
                try:
                    if self.news_service is not None:
                        await self.news_service.initialize()
                        news_items = await self._fetch_historical_news(
                            symbol, asset_id, start_date, end_date
                        )
                        await self.news_service.shutdown()
                    else:
                        news_items = await self._fetch_historical_news(
                            symbol, asset_id, start_date, end_date
                        )

                    if news_items:
                        async with async_session_maker() as session:
                            for item in news_items:
                                session.add(item)
                            await session.commit()
                            results["news_inserted"] += len(news_items)

                except Exception as e:
                    results["errors"].append(f"{symbol}: {e!s}")
                    continue

        except Exception as e:
            results["errors"].append(str(e))

        self.logger.info(f"News backfill complete: {results}")
        return results

    async def _fetch_historical_news(
        self, symbol: str, asset_id: str, start: datetime, end: datetime
    ) -> list[News]:
        """Fetch historical news for a symbol from yfinance and store as News objects."""
        import yfinance as yf

        news_items: list[News] = []
        try:
            ticker = yf.Ticker(symbol)
            raw_news = ticker.news or []
            for item in raw_news:
                published_str = item.get("published")
                published_dt = None
                if published_str:
                    try:
                        published_dt = datetime.fromisoformat(
                            published_str.replace("Z", "+00:00")
                        ).replace(tzinfo=None)
                    except (ValueError, TypeError):
                        published_dt = None
                if published_dt and not (start <= published_dt <= end):
                    continue
                url = item.get("link", "")
                if not url:
                    continue
                news_items.append(News(
                    source=item.get("publisher", "yfinance"),
                    title=item.get("title", ""),
                    body=item.get("summary", ""),
                    url=url,
                    published_at=published_dt,
                    asset_id=asset_id,
                    language="en",
                ))
        except Exception as e:
            self.logger.warning(f"Failed to fetch historical news for {symbol}: {e}")

        return news_items

    def _fallback_model_training(self) -> dict:
        """Fallback model training when ML service not available."""
        try:
            import subprocess
            import sys
            backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            script = """
import asyncio
import sys
sys.path.insert(0, '.')
from app.services.ml.coefficient_learning_service import CoefficientLearningService

async def main():
    service = CoefficientLearningService()
    await service.initialize()
    result = await service.learn_coefficients([])
    await service.shutdown()
    print(result)

asyncio.run(main())
"""
            result = subprocess.run(
                [sys.executable, "-c", script],
                cwd=backend_dir,
                capture_output=True,
                text=True,
                timeout=600,
            )
            if result.returncode == 0:
                return {"status": "completed", "output": result.stdout[:500]}
            return {"status": "error", "error": result.stderr[:500]}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def _generate_signals(self) -> dict:
        """Generate ML signals for active assets."""
        try:
            from decimal import Decimal

            from app.db.base import async_session_maker
            from app.models.models import Asset, IntlPriceCandle, MLSignal

            async with async_session_maker() as session:
                result = await session.execute(
                    select(Asset.id, Asset.symbol)
                    .where(Asset.active)
                    .where(Asset.asset_class == "EQUITY")
                    .limit(100)
                )
                assets = result.all()

                signals_generated = 0
                for asset_id, symbol in assets:
                    candle_result = await session.execute(
                        select(IntlPriceCandle.close, IntlPriceCandle.volume)
                        .where(IntlPriceCandle.asset_id == asset_id)
                        .where(IntlPriceCandle.timeframe == "1d")
                        .order_by(IntlPriceCandle.timestamp.desc())
                        .limit(50)
                    )
                    candles = candle_result.all()

                    if len(candles) >= 20:
                        closes = [float(c[0]) for c in reversed(candles)]
                        rsi = self._compute_rsi(closes)
                        if rsi is not None:
                            signal_type = "NEUTRAL"
                            confidence = 50.0
                            if rsi < 30:
                                signal_type = "BULLISH"
                                confidence = 70 + (30 - rsi)
                            elif rsi > 70:
                                signal_type = "BEARISH"
                                confidence = 70 + (rsi - 70)

                            signal = MLSignal(
                                asset_id=asset_id,
                                signal_type=signal_type,
                                confidence=Decimal(str(round(min(confidence, 95), 2))),
                                technical_factors={"rsi": round(rsi, 2)},
                                ml_model_version="auto_signal_v1",
                                model_name="AutoSignalGenerator",
                                valid_until=datetime.now(UTC) + timedelta(days=1),
                                is_active=True,
                            )
                            session.add(signal)
                            signals_generated += 1

                await session.commit()
                return {"status": "completed", "signals_generated": signals_generated}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    @staticmethod
    def _compute_rsi(prices: list, period: int = 14) -> float | None:
        if len(prices) < period + 1:
            return None
        gains = []
        losses = []
        for i in range(1, len(prices)):
            change = prices[i] - prices[i - 1]
            gains.append(max(change, 0))
            losses.append(max(-change, 0))
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100.0 - (100.0 / (1.0 + rs))

    async def _run_backup(self) -> dict:
        """Run database backup."""
        try:
            backup_path = self.settings.BACKUP_PATH
            os.makedirs(backup_path, exist_ok=True)
            timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(backup_path, f"backup_{timestamp}.sql")

            db_url = self.settings.DATABASE_URL
            if "://" in db_url:
                parts = db_url.split("://")[1]
                if "@" in parts:
                    auth_host = parts.split("@")
                    host_db = auth_host[1].split("/")
                    host = host_db[0].split(":")[0]
                    port = host_db[0].split(":")[1] if ":" in host_db[0] else "5432"
                    db_name = host_db[1].split("?")[0]
                    user_pass = auth_host[0].split(":")
                    user = user_pass[0]
                    password = user_pass[1] if len(user_pass) > 1 else ""

                    env = os.environ.copy()
                    env["PGPASSWORD"] = password
                    import subprocess
                    result = subprocess.run(
                        ["pg_dump", "-h", host, "-p", port, "-U", user, "-f", backup_file, db_name],
                        env=env,
                        capture_output=True,
                        text=True,
                        timeout=300,
                    )
                    if result.returncode == 0:
                        return {"status": "completed", "file": backup_file}

            return {"status": "skipped", "reason": "backup configuration incomplete"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def _run_archival(self) -> dict:
        """Archive old data."""
        try:
            archive_path = self.settings.ARCHIVE_PATH
            os.makedirs(archive_path, exist_ok=True)
            return {"status": "completed", "archive_path": archive_path}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def _run_log_cleanup(self) -> dict:
        """Clean up old log files."""
        try:
            log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "logs")
            if not os.path.exists(log_path):
                return {"status": "skipped", "reason": "no logs directory"}

            retention_days = getattr(self.settings, 'LOG_RETENTION_DAYS', 30)
            cutoff = datetime.now(UTC) - timedelta(days=retention_days)
            cleaned = 0

            for filename in os.listdir(log_path):
                filepath = os.path.join(log_path, filename)
                if os.path.isfile(filepath):
                    file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                    if file_time < cutoff:
                        os.remove(filepath)
                        cleaned += 1

            return {"status": "completed", "files_removed": cleaned}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    # ------------------------------------------------------------------ #
    # Real-time data refresh helpers
    # ------------------------------------------------------------------ #

    async def _refresh_news(self) -> dict[str, Any]:
        """Fetch latest news for active assets (incremental, last 24 hours)."""
        from sqlalchemy.dialects.postgresql import insert as pg_insert

        from app.db.base import async_session_maker
        from app.models.models import Asset, News

        end_date = datetime.now(UTC)
        start_date = end_date - timedelta(hours=24)

        results = {"news_inserted": 0, "errors": []}

        try:
            async with async_session_maker() as session:
                all_assets = await session.execute(
                    select(Asset.id, Asset.symbol, Asset.asset_class, Asset.market)
                    .where(
                        and_(
                            Asset.active,
                            Asset.market == "NASDAQ",
                            Asset.asset_class.in_(["EQUITY", "ETF"]),
                        )
                    )
                    .limit(100)
                )
                assets = all_assets.fetchall()

            import yfinance as yf

            for asset_id, symbol, asset_class in assets:
                try:
                    ticker = yf.Ticker(symbol)
                    raw_news = ticker.news or []

                    news_records = []
                    for item in raw_news:
                        published_str = item.get("published")
                        if not published_str:
                            continue
                        try:
                            published_dt = datetime.fromisoformat(
                                published_str.replace("Z", "+00:00")
                            ).replace(tzinfo=None)
                        except (ValueError, TypeError):
                            continue

                        if not (start_date <= published_dt <= end_date):
                            continue

                        url = item.get("link", "")
                        if not url:
                            continue

                        news_records.append({
                            "source": item.get("publisher", "yfinance"),
                            "title": item.get("title", ""),
                            "body": item.get("summary", ""),
                            "url": url,
                            "published_at": published_dt,
                            "asset_id": str(asset_id),
                            "language": "en",
                        })

                    if news_records:
                        async with async_session_maker() as session:
                            stmt = pg_insert(News).values(news_records)
                            stmt = stmt.on_conflict_do_nothing(
                                index_elements=["url"]
                            )
                            await session.execute(stmt)
                            await session.commit()
                            results["news_inserted"] += len(news_records)

                except Exception as e:
                    results["errors"].append(f"{symbol}: {e!s}")
                    continue

        except Exception as e:
            results["errors"].append(str(e))

        self.logger.info(f"News refresh complete: {results}")
        return results

    async def _refresh_fundamentals(self) -> dict[str, Any]:
        """Refresh fundamental data (financial statements and ratios) for active equity assets."""
        from decimal import Decimal

        from sqlalchemy.dialects.postgresql import insert as pg_insert

        from app.db.base import async_session_maker
        from app.models.models import Asset, FundamentalRatio

        results = {"ratios_updated": 0, "statements_updated": 0, "errors": []}

        try:
            async with async_session_maker() as session:
                assets_result = await session.execute(
                    select(Asset.id, Asset.symbol)
                    .where(Asset.active)
                    .where(Asset.asset_class == "EQUITY")
                    .limit(50)
                )
                assets = assets_result.all()

            import yfinance as yf

            for asset_id, symbol in assets:
                try:
                    ticker = yf.Ticker(symbol)
                    info = ticker.info

                    if not info:
                        continue

                    eps = info.get("trailingEps")
                    pe = info.get("trailingPE")
                    pb = info.get("priceToBook")
                    dps = info.get("dividendRate")
                    roe = info.get("returnOnEquity")
                    profit_margin = info.get("profitMargins")
                    market_cap = info.get("market_cap")
                    book_value = info.get("bookValue")

                    period = datetime.now().strftime("%Y-Q%q").replace(
                        "%q", str((datetime.now().month - 1) // 3 + 1)
                    )

                    ratio_record = {
                        "asset_id": str(asset_id),
                        "market": "NASDAQ",
                        "period": period,
                        "eps": Decimal(str(eps)) if eps else None,
                        "pe": Decimal(str(pe)) if pe else None,
                        "pb": Decimal(str(pb)) if pb else None,
                        "dps": Decimal(str(dps)) if dps else None,
                        "roe": Decimal(str(roe)) if roe else None,
                        "profit_margin": Decimal(str(profit_margin)) if profit_margin else None,
                        "market_cap": Decimal(str(market_cap)) if market_cap else None,
                        "book_value": Decimal(str(book_value)) if book_value else None,
                        "as_of": datetime.now().date(),
                    }

                    async with async_session_maker() as session:
                        stmt = pg_insert(FundamentalRatio).values(ratio_record)
                        stmt = stmt.on_conflict_do_update(
                            index_elements=["asset_id", "period", "market"],
                            set_={
                                "eps": stmt.excluded.eps,
                                "pe": stmt.excluded.pe,
                                "pb": stmt.excluded.pb,
                                "dps": stmt.excluded.dps,
                                "roe": stmt.excluded.roe,
                                "profit_margin": stmt.excluded.profit_margin,
                                "market_cap": stmt.excluded.market_cap,
                                "book_value": stmt.excluded.book_value,
                                "as_of": stmt.excluded.as_of,
                            },
                        )
                        await session.execute(stmt)
                        await session.commit()
                        results["ratios_updated"] += 1

                except Exception as e:
                    results["errors"].append(f"{symbol}: {e!s}")
                    continue

        except Exception as e:
            results["errors"].append(str(e))

        self.logger.info(f"Fundamental data refresh complete: {results}")
        return results

    async def _refresh_macro_data(self) -> dict[str, Any]:
        """Refresh real US macroeconomic indicators and currency rates.

        All data sources here are **free and require no API key**:
          * Real economic releases (CPI, unemployment, GDP, Fed funds, sentiment,
            industrial production, housing, yields/curve) are downloaded from the
            public FRED graph-CSV endpoint (urllib, no account).
          * Market tickers (^VIX, ^TNX, Dollar Index, Gold, Oil, ^GSPC) come from
            yfinance (free public data).
          * FX rates come from FRED's free DEX* series.
        If a network fetch fails (e.g. air-gapped host) the job keeps the last
        known values rather than writing placeholder zeros.
        """
        results: dict[str, Any] = {
            "indicators_updated": 0,
            "currency_rates_updated": 0,
            "errors": [],
        }

        try:
            results["indicators_updated"] += await self._refresh_real_indicators()
        except Exception as exc:  # pragma: no cover - defensive
            results["errors"].append(f"Real indicators: {exc!s}")

        try:
            results["indicators_updated"] += await self._refresh_ticker_indicators()
        except Exception as exc:  # pragma: no cover - defensive
            results["errors"].append(f"Ticker indicators: {exc!s}")

        try:
            results["currency_rates_updated"] += await self._refresh_currency_rates()
        except Exception as exc:  # pragma: no cover - defensive
            results["errors"].append(f"Currency rates: {exc!s}")

        self.logger.info(f"Macro data refresh complete: {results}")
        return results

    async def _refresh_real_indicators(self) -> int:
        """Fetch real US macro releases from the free FRED CSV endpoint (no key)."""
        from decimal import Decimal

        from app.services.analysis.macro_scoring import (
            BUNDLED_MACRO_SNAPSHOT,
            INDICATOR_REGISTRY,
            derive_indicators,
            derive_history_map,
        )
        from app.services.data.fred_csv_client import fetch_history_map

        monthly_ids = [
            "CPIAUCSL", "CPILFESL", "UNRATE", "U6RATE", "UMCSENT",
            "INDPRO", "TCU", "PERMIT", "PAYEMS",
            "CES0501000000000000050Q0",
        ]
        quarterly_ids = ["GDPC1", "GDP"]

        # FRED graph CSV endpoint accepts up to ~10 series per request.
        # Split into chunks and merge results to stay within the limit.
        series_ids = monthly_ids + quarterly_ids + ["FEDFUNDS", "DGS10", "DGS2", "T10Y2Y", "DGS30"]
        history_map: dict[str, list[tuple[Any, float]]] = {}
        for i in range(0, len(series_ids), 10):
            batch = series_ids[i:i + 10]
            chunk = await asyncio.to_thread(fetch_history_map, batch)
            history_map.update(chunk)

        # Frequency cap on how much history we persist per series.
        lookback = {"monthly": 24, "quarterly": 8, "daily": 60}

        count = 0
        async with async_session_maker() as session:
            for code, history in history_map.items():
                if not history:
                    continue
                meta = INDICATOR_REGISTRY.get(code, {})
                freq = meta.get("frequency", "monthly")
                keep = history[-lookback.get(freq, 24):]
                for as_of, value in keep:
                    stmt = pg_insert(MacroIndicator).values(
                        {
                            "indicator_code": code,
                            "name": meta.get("name", code)[:255],
                            "value": Decimal(str(value)),
                            "period": _period_for(freq, as_of),
                            "unit": (meta.get("unit", "") or "")[:20],
                            "source": meta.get("source", "FRED"),
                            "as_of": as_of,
                        }
                    )
                    stmt = stmt.on_conflict_do_update(
                        constraint="uix_macro_indicator",
                        set_={
                            "value": stmt.excluded.value,
                            "as_of": stmt.excluded.as_of,
                            "unit": stmt.excluded.unit,
                            "source": stmt.excluded.source,
                            "name": stmt.excluded.name,
                        },
                    )
                    await session.execute(stmt)
                    count += 1

            # Derived indicators (inflation YoY, GDP q/q, payroll/mo, wage YoY).
            # Persist the full derived history so derived indicators are
            # forecastable (forecast_and_persist needs >= 3 points).
            derived_history = derive_history_map(history_map)
            for code, points in derived_history.items():
                meta = INDICATOR_REGISTRY.get(code, {})
                freq = meta.get("frequency", "monthly")
                keep = points[-lookback.get(freq, 24):]
                for as_of, value in keep:
                    stmt = pg_insert(MacroIndicator).values(
                        {
                            "indicator_code": code,
                            "name": meta.get("name", code)[:255],
                            "value": Decimal(str(value)),
                            "period": _period_for(freq, as_of),
                            "unit": (meta.get("unit", "") or "")[:20],
                            "source": meta.get("source", "derived"),
                            "as_of": as_of,
                        }
                    )
                    stmt = stmt.on_conflict_do_update(
                        constraint="uix_macro_indicator",
                        set_={
                            "value": stmt.excluded.value,
                            "as_of": stmt.excluded.as_of,
                            "unit": stmt.excluded.unit,
                            "source": stmt.excluded.source,
                        },
                    )
                    await session.execute(stmt)
                    count += 1

            # Latest derived values for backward-compat aliases below.
            derived = derive_indicators(history_map)

            # Backward-compat aliases used elsewhere in the codebase.
            aliases = {"US_FED_RATE": "FEDFUNDS", "US_INFLATION": "INFLATION"}
            for alias, real in aliases.items():
                if real in history_map or real in derived:
                    latest = _latest_value(history_map.get(real, []), derived.get(real))
                    if latest is not None:
                        as_of, value = latest
                        stmt = pg_insert(MacroIndicator).values(
                            {
                                "indicator_code": alias,
                                "name": INDICATOR_REGISTRY.get(alias, {}).get("name", alias),
                                "value": Decimal(str(value)),
                                "period": _period_for(INDICATOR_REGISTRY.get(real, {}).get("frequency", "monthly"), as_of),
                                "unit": "%",
                                "source": "FRED",
                                "as_of": as_of,
                            }
                        )
                        stmt = stmt.on_conflict_do_update(
                            constraint="uix_macro_indicator",
                            set_={"value": stmt.excluded.value, "as_of": stmt.excluded.as_of},
                        )
                        await session.execute(stmt)
                        count += 1

            # Offline fallback (free, no network): seed the bundled snapshot for
            # any codes the live FRED fetch missed so the macro dimension is
            # never empty in air-gapped deployments. These rows are overwritten
            # automatically once network access to FRED returns.
            covered: set[str] = set(history_map.keys()) | set(derived.keys())
            for alias, real in aliases.items():
                if real in covered:
                    covered.add(alias)
            for code, snap in BUNDLED_MACRO_SNAPSHOT.items():
                if code in covered:
                    continue
                stmt = pg_insert(MacroIndicator).values(
                    {
                        "indicator_code": code,
                        "name": INDICATOR_REGISTRY.get(code, {}).get("name", code),
                        "value": Decimal(str(snap["value"])),
                        "period": snap.get("period", ""),
                        "unit": snap.get("unit", ""),
                        "source": snap.get("source", "BUNDLED"),
                        "as_of": _parse_period_date(snap.get("period")) or today_local(),
                    }
                )
                stmt = stmt.on_conflict_do_update(
                    constraint="uix_macro_indicator",
                    set_={
                        "value": stmt.excluded.value,
                        "as_of": stmt.excluded.as_of,
                        "unit": stmt.excluded.unit,
                        "source": stmt.excluded.source,
                    },
                )
                await session.execute(stmt)
                count += 1

            await session.commit()
        return count

    async def _refresh_ticker_indicators(self) -> int:
        """Refresh market-based macro tickers from yfinance (free public data)."""
        from decimal import Decimal

        import yfinance as yf

        from app.services.data.nasdaq_ingestion_service import (
            MACRO_TICKERS,
        )

        tickers = list(MACRO_TICKERS.keys())
        today_local()

        def _fetch_one(sym: str) -> tuple[Any, float] | None:
            try:
                ticker = yf.Ticker(sym)
                hist = ticker.history(period="5d", interval="1d")
                if hist.empty:
                    return None
                latest = hist.iloc[-1]
                return hist.index[-1].date(), float(latest["Close"])
            except Exception as exc:  # pragma: no cover - defensive
                self.logger.warning("yfinance macro fetch failed for %s: %s", sym, exc)
                return None

        fetched = await asyncio.to_thread(
            lambda: {sym: _fetch_one(sym) for sym in tickers}
        )

        count = 0
        async with async_session_maker() as session:
            for sym, res in fetched.items():
                if res is None:
                    continue
                name, unit = MACRO_TICKERS[sym]
                as_of, value = res
                stmt = pg_insert(MacroIndicator).values(
                    {
                        "indicator_code": sym,
                        "name": name,
                        "value": Decimal(str(value)),
                        "period": as_of.strftime("%Y-%m-%d"),
                        "unit": (unit or "")[:20],
                        "source": "yfinance",
                        "as_of": as_of,
                    }
                )
                stmt = stmt.on_conflict_do_update(
                    constraint="uix_macro_indicator",
                    set_={
                        "value": stmt.excluded.value,
                        "as_of": stmt.excluded.as_of,
                        "unit": stmt.excluded.unit,
                        "source": stmt.excluded.source,
                    },
                )
                await session.execute(stmt)
                count += 1
            await session.commit()
        return count

    async def _refresh_currency_rates(self) -> int:
        """Refresh USD FX rates from the free FRED DEX series (no API key)."""
        from decimal import Decimal

        from app.services.data.fred_csv_client import fetch_latest_map

        # FRED series: USD per unit of foreign currency (EUR/GBP/JPY vs USD).
        fx_series = {"DEXUSEU": "EUR", "DEXUSUK": "GBP", "DEXJPUS": "JPY"}
        latest_map = await asyncio.to_thread(fetch_latest_map, list(fx_series.keys()))

        count = 0
        today_local()
        async with async_session_maker() as session:
            for series_id, quote in fx_series.items():
                entry = latest_map.get(series_id)
                if not entry:
                    continue
                as_of, value = entry
                # Normalize to "USD per 1 unit of quote currency".
                if series_id == "DEXJPUS":
                    rate = 1.0 / value  # JPY per USD -> USD per JPY
                else:
                    rate = value
                stmt = pg_insert(CurrencyRate).values(
                    {
                        "base_currency": "USD",
                        "quote_currency": quote,
                        "rate": Decimal(str(round(rate, 6))),
                        "rate_date": as_of,
                        "source": "FRED",
                    }
                )
                stmt = stmt.on_conflict_do_update(
                    constraint="uix_currency_rate",
                    set_={"rate": stmt.excluded.rate, "rate_date": stmt.excluded.rate_date},
                )
                await session.execute(stmt)
                count += 1
            await session.commit()
        return count

    async def _refresh_macro_forecasts(self) -> dict[str, Any]:
        """Generate free in-process macro forecasts from stored history."""
        results: dict[str, Any] = {"forecasts": 0, "errors": []}
        try:
            from app.services.ml.macro_forecasting_service import MacroForecastingService

            svc = MacroForecastingService()
            await svc.initialize()
            try:
                for code in ("INFLATION", "UNRATE", "GDPC1", "FEDFUNDS", "UMCSENT", "T10Y2Y"):
                    ok = await svc.forecast_and_persist(code)
                    if ok:
                        results["forecasts"] += 1
            finally:
                await svc.shutdown()
        except Exception as exc:  # pragma: no cover - defensive
            results["errors"].append(f"Macro forecasts: {exc!s}")
        self.logger.info(f"Macro forecast refresh complete: {results}")
        return results

    async def _refresh_master_data(self) -> dict[str, Any]:
        """Refresh market indices."""
        from decimal import Decimal

        from sqlalchemy.dialects.postgresql import insert as pg_insert

        from app.db.base import async_session_maker
        from app.models.models import MarketIndex

        results = {"indices_updated": 0, "errors": []}

        try:
            import yfinance as yf

            index_symbols = [
                {"symbol": "^IXIC", "name": "NASDAQ Composite", "exchange": "NASDAQ", "country": "US"},
            ]

            for idx in index_symbols:
                try:
                    ticker = yf.Ticker(idx["symbol"])
                    hist = ticker.history(period="1d")
                    if not hist.empty:
                        latest = hist.iloc[-1]
                        current_value = Decimal(str(latest["Close"]))
                        prev_close = ticker.info.get("previousClose", latest["Close"])
                        change_pct = ((latest["Close"] - prev_close) / prev_close * 100) if prev_close else 0

                        record = {
                            "symbol": idx["symbol"],
                            "name": idx["name"],
                            "exchange": idx["exchange"],
                            "country": idx["country"],
                            "current_value": current_value,
                            "change_percent": Decimal(str(round(change_pct, 4))),
                            "volume": Decimal(str(latest["Volume"])),
                            "last_updated": datetime.now(UTC),
                            "is_active": True,
                        }

                        async with async_session_maker() as session:
                            stmt = pg_insert(MarketIndex).values(record)
                            stmt = stmt.on_conflict_do_update(
                                index_elements=["symbol"],
                                set_={
                                    "current_value": stmt.excluded.current_value,
                                    "change_percent": stmt.excluded.change_percent,
                                    "volume": stmt.excluded.volume,
                                    "last_updated": stmt.excluded.last_updated,
                                },
                            )
                            await session.execute(stmt)
                            await session.commit()
                            results["indices_updated"] += 1
                except Exception as e:
                    results["errors"].append(f"{idx['symbol']}: {e!s}")
                    continue

        except Exception as e:
            results["errors"].append(f"Market indices: {e!s}")

        self.logger.info(f"Master data refresh complete: {results}")
        return results

    async def _refresh_intl_candles(self) -> dict[str, Any]:
        """Refresh international price candles for active equity assets."""
        from sqlalchemy.dialects.postgresql import insert as pg_insert

        from app.db.base import async_session_maker
        from app.models.models import Asset, IntlPriceCandle

        end_date = datetime.now(UTC)
        start_date = end_date - timedelta(days=7)

        results = {"candles_inserted": 0, "errors": []}

        try:
            async with async_session_maker() as session:
                assets_result = await session.execute(
                    select(Asset.id, Asset.symbol)
                    .where(Asset.active)
                    .where(Asset.asset_class == "EQUITY")
                    .limit(100)
                )
                assets = assets_result.all()

            import yfinance as yf

            for asset_id, symbol in assets:
                try:
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(start=start_date.strftime("%Y-%m-%d"), end=end_date.strftime("%Y-%m-%d"), interval="1d", auto_adjust=True)

                    if hist.empty:
                        continue

                    candles = []
                    for timestamp, row in hist.iterrows():
                        ts = timestamp.to_pydatetime().replace(tzinfo=None) if hasattr(timestamp, "to_pydatetime") else timestamp
                        open_p = float(row["Open"])
                        high_p = float(row["High"])
                        low_p = float(row["Low"])
                        close_p = float(row["Close"])
                        low_p = min(open_p, high_p, low_p, close_p)
                        high_p = max(open_p, high_p, low_p, close_p)
                        volume = int(row["Volume"])
                        volume = max(volume, 0)

                        candles.append({
                            "asset_id": str(asset_id),
                            "timestamp": ts,
                            "timeframe": "1d",
                            "open": open_p,
                            "high": high_p,
                            "low": low_p,
                            "close": close_p,
                            "volume": volume,
                            "turnover": float(close_p * volume),
                            "source": "yfinance",
                            "data_quality": "CONFIRMED",
                            "adjusted_close": float(close_p),
                            "split_ratio": 1.0,
                        })

                    if candles:
                        async with async_session_maker() as session:
                            stmt = pg_insert(IntlPriceCandle).values(candles)
                            stmt = stmt.on_conflict_do_update(
                                index_elements=["asset_id", "timestamp", "timeframe"],
                                set_={
                                    "open": stmt.excluded.open,
                                    "high": stmt.excluded.high,
                                    "low": stmt.excluded.low,
                                    "close": stmt.excluded.close,
                                    "volume": stmt.excluded.volume,
                                    "turnover": stmt.excluded.turnover,
                                    "source": stmt.excluded.source,
                                    "data_quality": stmt.excluded.data_quality,
                                    "adjusted_close": stmt.excluded.adjusted_close,
                                    "split_ratio": stmt.excluded.split_ratio,
                                },
                            )
                            await session.execute(stmt)
                            await session.commit()
                            results["candles_inserted"] += len(candles)

                except Exception as e:
                    results["errors"].append(f"{symbol}: {e!s}")
                    continue

        except Exception as e:
            results["errors"].append(str(e))

        self.logger.info(f"International candle refresh complete: {results}")
        return results

    async def shutdown(self) -> None:
        self._running = False
        if self._main_task:
            self._main_task.cancel()
            try:
                await self._main_task
            except asyncio.CancelledError:
                pass
        for job in self._jobs.values():
            if job._task:
                job._task.cancel()
                try:
                    await job._task
                except asyncio.CancelledError:
                    pass
        self._jobs.clear()
        self.logger.info("SchedulerService shutdown")

    def register_job(
        self,
        name: str,
        coroutine_func: Callable[[], Coroutine[Any, Any, Any]],
        interval_seconds: int,
    ) -> ScheduledJob:
        job = ScheduledJob(
            name=name,
            coroutine_func=coroutine_func,
            interval_seconds=interval_seconds,
            next_run=datetime.now(UTC),
        )
        self._jobs[name] = job
        self.logger.info(f"Registered job: {name} (interval={interval_seconds}s)")
        return job

    def unregister_job(self, name: str) -> bool:
        if name in self._jobs:
            job = self._jobs.pop(name)
            if job._task:
                job._task.cancel()
            self.logger.info(f"Unregistered job: {name}")
            return True
        return False

    async def run_job_now(self, name: str) -> dict[str, Any]:
        if name not in self._jobs:
            raise ValueError(f"Job not found: {name}")
        job = self._jobs[name]
        return await self._execute_job(job)

    async def _execute_job(self, job: ScheduledJob) -> dict[str, Any]:
        start = datetime.now(UTC)
        try:
            result = await job.coroutine_func()
            duration_ms = (datetime.now(UTC) - start).total_seconds() * 1000
            job.last_run = datetime.now(UTC)
            job.run_count += 1
            job.next_run = datetime.now(UTC) + timedelta(seconds=job.interval_seconds)
            self.logger.info(f"Job '{job.name}' completed in {duration_ms:.1f}ms")
            return {"status": "success", "job": job.name, "duration_ms": duration_ms, "result": result}
        except Exception as exc:
            duration_ms = (datetime.now(UTC) - start).total_seconds() * 1000
            job.last_run = datetime.now(UTC)
            job.run_count += 1
            job.error_count += 1
            job.next_run = datetime.now(UTC) + timedelta(seconds=job.interval_seconds)
            self.logger.error(f"Job '{job.name}' failed: {exc}", exc_info=True)
            return {"status": "error", "job": job.name, "error": str(exc), "duration_ms": duration_ms}

    async def _get_tracked_symbols(self) -> list[str]:
        """Return the list of symbols that have been traded/watched."""
        try:
            async with async_session_maker() as session:
                result = await session.execute(
                    select(Asset)
                    .where(Asset.active.is_(True), Asset.asset_class.in_(["EQUITY", "ETF"]))
                    .limit(500)
                )
                symbols = [row.symbol for row in result.scalars().all()]
                if symbols:
                    return symbols
        except Exception:
            pass
        return ["AAPL", "MSFT", "GOOG", "TSLA", "NVDA", "SPY", "QQQ", "INTC"]

    def _dict_to_snapshot(self, data: dict[str, Any]) -> list:
        """Convert a snapshot dict to an OrderBookSnapshot list for persistence."""
        from app.services.data.itch_ingestion_service import OrderBookLevel, OrderBookSnapshot

        bids = []
        for b in data.get("bids", []):
            bids.append(OrderBookLevel(
                rank=b.get("rank", 1),
                price=float(b.get("price", 0)),
                volume=int(b.get("volume", 0)),
                order_count=int(b.get("order_count", 0)),
            ))
        asks = []
        for a in data.get("asks", []):
            asks.append(OrderBookLevel(
                rank=a.get("rank", 1),
                price=float(a.get("price", 0)),
                volume=int(a.get("volume", 0)),
                order_count=int(a.get("order_count", 0)),
            ))
        snap = OrderBookSnapshot(
            symbol=data.get("symbol", ""),
            ts=datetime.fromisoformat(data.get("snapshot_time", datetime.now(UTC).isoformat())),
            bids=bids,
            asks=asks,
            spread=data.get("spread"),
            spread_pct=data.get("spread_pct"),
            source=data.get("source", "BRS"),
        )
        return [snap]

    async def _scheduler_loop(self) -> None:
        self.logger.info("Scheduler loop started")
        while self._running:
            now = datetime.now(UTC)
            for job in list(self._jobs.values()):
                if not job.enabled:
                    continue
                if job.next_run and now >= job.next_run:
                    job._task = asyncio.create_task(self._execute_job(job))
            await asyncio.sleep(5)

    def get_job_status(self, name: str) -> dict[str, Any] | None:
        if name not in self._jobs:
            return None
        job = self._jobs[name]
        return {
            "name": job.name,
            "enabled": job.enabled,
            "interval_seconds": job.interval_seconds,
            "last_run": job.last_run.isoformat() if job.last_run else None,
            "next_run": job.next_run.isoformat() if job.next_run else None,
            "run_count": job.run_count,
            "error_count": job.error_count,
        }

    def list_jobs(self) -> list[dict[str, Any]]:
        return [self.get_job_status(name) for name in self._jobs]

    async def health_check(self) -> dict[str, Any]:
        return {
            "service": self.service_name,
            "status": "healthy" if self._running else "stopped",
            "jobs_registered": len(self._jobs),
            "jobs_running": sum(1 for j in self._jobs.values() if j.enabled),
            "uptime_seconds": (datetime.now(UTC) - self.created_at).total_seconds(),
        }


# ---------------------------------------------------------------------------
# Module-level helpers for free, no-API-key macro refresh.
# ---------------------------------------------------------------------------


def today_local() -> Any:
    """Local (naive) date for rate/as_of stamping."""
    return datetime.now().date()


def _period_for(freq: str, as_of: Any) -> str:
    """Build a MacroIndicator period string from a date + frequency."""
    if freq == "quarterly":
        quarter = (as_of.month - 1) // 3 + 1
        return f"{as_of.year}Q{quarter}"
    if freq == "daily":
        return as_of.strftime("%Y-%m-%d")
    return as_of.strftime("%Y-%m")


def _parse_period_date(period: str | None) -> Any | None:
    """Parse a period string ('2026-07', '2026Q2', '2026-07-30') into a date."""
    if not period:
        return None
    s = str(period).strip()
    m = _re.fullmatch(r"(\d{4})-(\d{2})", s)
    if m:
        y, mo = int(m.group(1)), int(m.group(2))
        nxt = _date(y + 1, 1, 1) if mo == 12 else _date(y, mo + 1, 1)
        return nxt - timedelta(days=1)
    m = _re.fullmatch(r"(\d{4})Q([1-4])", s)
    if m:
        y, q = int(m.group(1)), int(m.group(2))
        qm = (q - 1) * 3 + 3  # end-quarter month
        nxt = _date(y + 1, 1, 1) if qm == 12 else _date(y, qm + 1, 1)
        return nxt - timedelta(days=1)
    m = _re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        try:
            return _date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            return None
    return None


def _latest_value(
    history: list[tuple[Any, float]], derived_entry: dict[str, Any] | None
) -> tuple[Any, float] | None:
    """Return (as_of, value) for the most recent observation of a series."""
    if history:
        return history[-1]
    if derived_entry and "value" in derived_entry:
        as_of = _parse_period_date(derived_entry.get("period")) or today_local()
        try:
            return as_of, float(derived_entry["value"])
        except (TypeError, ValueError):
            return None
    return None
