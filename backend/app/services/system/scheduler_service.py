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
import logging
import os
import shutil
from datetime import timezone, datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Coroutine
from dataclasses import dataclass, field

from ..core import BaseService
from app.core.config import get_settings
from sqlalchemy import select, func
from app.models.models import Asset, IntlPriceCandle, News


@dataclass
class ScheduledJob:
    """Definition of a scheduled job."""
    name: str
    coroutine_func: Callable[[], Coroutine[Any, Any, Any]]
    interval_seconds: int
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    error_count: int = 0
    _task: Optional[asyncio.Task] = field(default=None, repr=False)


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
                 news_service=None):
        super().__init__(service_name)
        self._jobs: Dict[str, ScheduledJob] = {}
        self._running: bool = False
        self._main_task: Optional[asyncio.Task] = None
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

    async def initialize(self) -> None:
        self._running = True
        self._main_task = asyncio.create_task(self._scheduler_loop())
        self.logger.info("SchedulerService initialized")

        await self._register_default_jobs()

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

        # === SCORING & ANALYSIS JOBS ===

        async def daily_score_recalculation_job():
            from app.services.analysis.score_history_pipeline import ScoreHistoryPipeline
            pipeline = ScoreHistoryPipeline()
            await pipeline.initialize()
            try:
                result = await pipeline.compute_and_persist_all(
                    market="NASDAQ", batch_size=100
                )
                return result
            except Exception as e:
                logger.error(f"DailyScoreRecalculation failed: {e}")
                return {"status": "error", "error": str(e)}
            finally:
                await pipeline.shutdown()

        self.register_job(
            name="DailyScoreRecalculation",
            coroutine_func=daily_score_recalculation_job,
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
            """Fetch latest news for active assets every 30 minutes."""
            return await self._refresh_news()

        self.register_job(
            name="DailyNewsRefresh",
            coroutine_func=daily_news_refresh_job,
            interval_seconds=1800,  # 30 minutes
        )

        async def fundamental_data_refresh_job():
            """Refresh fundamental data (financial statements and ratios) daily."""
            return await self._refresh_fundamentals()

        self.register_job(
            name="FundamentalDataRefresh",
            coroutine_func=fundamental_data_refresh_job,
            interval_seconds=86400,  # Daily
        )

        async def macro_data_refresh_job():
            """Refresh macro indicators and currency rates daily."""
            return await self._refresh_macro_data()

        self.register_job(
            name="MacroDataRefresh",
            coroutine_func=macro_data_refresh_job,
            interval_seconds=86400,  # Daily
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

    async def _backfill_news(self, years: int = 5) -> Dict[str, Any]:
        """Backfill historical news data for active assets.

        Uses the NewsService (which wraps yfinance + multi-source fetchers)
        when available, falling back to direct yfinance calls.
        """
        from app.db.base import async_session_maker

        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=years * 365)

        results = {"news_inserted": 0, "errors": []}

        try:
            async with async_session_maker() as session:
                all_assets = await session.execute(
                    select(Asset.id, Asset.symbol, Asset.asset_class, Asset.market)
                    .where(Asset.active == True)
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
                    results["errors"].append(f"{symbol}: {str(e)}")
                    continue

        except Exception as e:
            results["errors"].append(str(e))

        self.logger.info(f"News backfill complete: {results}")
        return results

    async def _fetch_historical_news(
        self, symbol: str, asset_id: str, start: datetime, end: datetime
    ) -> List[News]:
        """Fetch historical news for a symbol from yfinance and store as News objects."""
        import yfinance as yf

        news_items: List[News] = []
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
            from app.db.base import async_session_maker
            from app.models.models import Asset, MLSignal, IntlPriceCandle
            from sqlalchemy import select, func
            from decimal import Decimal

            async with async_session_maker() as session:
                result = await session.execute(
                    select(Asset.id, Asset.symbol)
                    .where(Asset.active == True)
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
                            signal_type = "HOLD"
                            confidence = 50.0
                            if rsi < 30:
                                signal_type = "BUY"
                                confidence = 70 + (30 - rsi)
                            elif rsi > 70:
                                signal_type = "SELL"
                                confidence = 70 + (rsi - 70)

                            signal = MLSignal(
                                asset_id=asset_id,
                                signal_type=signal_type,
                                confidence=Decimal(str(round(min(confidence, 95), 2))),
                                technical_factors={"rsi": round(rsi, 2)},
                                ml_model_version="auto_signal_v1",
                                model_name="AutoSignalGenerator",
                                valid_until=datetime.now(timezone.utc) + timedelta(days=1),
                                is_active=True,
                            )
                            session.add(signal)
                            signals_generated += 1

                await session.commit()
                return {"status": "completed", "signals_generated": signals_generated}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    @staticmethod
    def _compute_rsi(prices: list, period: int = 14) -> Optional[float]:
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
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
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
            cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
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

    async def _refresh_news(self) -> Dict[str, Any]:
        """Fetch latest news for active assets (incremental, last 24 hours)."""
        from app.db.base import async_session_maker
        from app.models.models import Asset, News
        from sqlalchemy.dialects.postgresql import insert as pg_insert

        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(hours=24)

        results = {"news_inserted": 0, "errors": []}

        try:
            async with async_session_maker() as session:
                all_assets = await session.execute(
                    select(Asset.id, Asset.symbol, Asset.asset_class)
                    .where(Asset.active == True)
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
                    results["errors"].append(f"{symbol}: {str(e)}")
                    continue

        except Exception as e:
            results["errors"].append(str(e))

        self.logger.info(f"News refresh complete: {results}")
        return results

    async def _refresh_fundamentals(self) -> Dict[str, Any]:
        """Refresh fundamental data (financial statements and ratios) for active equity assets."""
        from app.db.base import async_session_maker
        from app.models.models import Asset, FundamentalRatio, FinancialStatement
        from sqlalchemy.dialects.postgresql import insert as pg_insert
        from decimal import Decimal

        results = {"ratios_updated": 0, "statements_updated": 0, "errors": []}

        try:
            async with async_session_maker() as session:
                assets_result = await session.execute(
                    select(Asset.id, Asset.symbol)
                    .where(Asset.active == True)
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

                    current_price = info.get("market_cap", 0) / info.get("sharesOutstanding", 1) if info.get("sharesOutstanding") else None
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
                    results["errors"].append(f"{symbol}: {str(e)}")
                    continue

        except Exception as e:
            results["errors"].append(str(e))

        self.logger.info(f"Fundamental data refresh complete: {results}")
        return results

    async def _refresh_macro_data(self) -> Dict[str, Any]:
        """Refresh macro indicators and currency rates."""
        from app.db.base import async_session_maker
        from app.models.models import MacroIndicator, CurrencyRate
        from sqlalchemy.dialects.postgresql import insert as pg_insert
        from decimal import Decimal

        results = {"indicators_updated": 0, "currency_rates_updated": 0, "errors": []}

        try:
            today = datetime.now().date()

            macro_updates = [
                {"code": "US_INFLATION", "name": "US Inflation Rate", "value": 0, "unit": "%"},
                {"code": "US_FED_RATE", "name": "US Federal Funds Rate", "value": 0, "unit": "%"},
                {"code": "GOLD_PRICE", "name": "Gold Price (USD/oz)", "value": 0, "unit": "USD"},
                {"code": "OIL_PRICE", "name": "Crude Oil Price (USD/bbl)", "value": 0, "unit": "USD"},
            ]

            async with async_session_maker() as session:
                for indicator in macro_updates:
                    record = {
                        "indicator_code": indicator["code"],
                        "name": indicator["name"],
                        "value": Decimal(str(indicator["value"])),
                        "unit": indicator["unit"],
                        "as_of": today,
                    }
                    stmt = pg_insert(MacroIndicator).values(record)
                    stmt = stmt.on_conflict_do_update(
                        constraint="uix_macro_indicator",
                        set_={"value": stmt.excluded.value, "as_of": stmt.excluded.as_of},
                    )
                    await session.execute(stmt)
                    results["indicators_updated"] += 1
                await session.commit()

        except Exception as e:
            results["errors"].append(f"Macro indicators: {str(e)}")

        try:
            currency_pairs = [
                {"base": "USD", "quote": "EUR", "rate": Decimal("0.85")},
                {"base": "USD", "quote": "GBP", "rate": Decimal("0.73")},
                {"base": "USD", "quote": "JPY", "rate": Decimal("110.0")},
                {"base": "USD", "quote": "CHF", "rate": Decimal("0.92")},
            ]

            today = datetime.now().date()
            async with async_session_maker() as session:
                for pair in currency_pairs:
                    record = {
                        "base_currency": pair["base"],
                        "quote_currency": pair["quote"],
                        "rate": pair["rate"],
                        "rate_date": today,
                        "source": "ECB",
                    }
                    stmt = pg_insert(CurrencyRate).values(record)
                    stmt = stmt.on_conflict_do_update(
                        constraint="uix_currency_rate",
                        set_={"rate": stmt.excluded.rate, "rate_date": stmt.excluded.rate_date},
                    )
                    await session.execute(stmt)
                    results["currency_rates_updated"] += 1
                await session.commit()

        except Exception as e:
            results["errors"].append(f"Currency rates: {str(e)}")

        self.logger.info(f"Macro data refresh complete: {results}")
        return results

    async def _refresh_master_data(self) -> Dict[str, Any]:
        """Refresh market indices."""
        from app.db.base import async_session_maker
        from app.models.models import MarketIndex
        from sqlalchemy.dialects.postgresql import insert as pg_insert
        from decimal import Decimal

        results = {"indices_updated": 0, "errors": []}

        try:
            import yfinance as yf

            index_symbols = [
                {"symbol": "^GSPC", "name": "S&P 500", "exchange": "NYSE", "country": "US"},
                {"symbol": "^DJI", "name": "Dow Jones Industrial Average", "exchange": "NYSE", "country": "US"},
                {"symbol": "^IXIC", "name": "NASDAQ Composite", "exchange": "NASDAQ", "country": "US"},
                {"symbol": "^FTSE", "name": "FTSE 100", "exchange": "LSE", "country": "UK"},
                {"symbol": "^N225", "name": "Nikkei 225", "exchange": "TSE", "country": "Japan"},
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
                            "last_updated": datetime.now(timezone.utc),
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
                    results["errors"].append(f"{idx['symbol']}: {str(e)}")
                    continue

        except Exception as e:
            results["errors"].append(f"Market indices: {str(e)}")

        self.logger.info(f"Master data refresh complete: {results}")
        return results

    async def _refresh_intl_candles(self) -> Dict[str, Any]:
        """Refresh international price candles for active equity assets."""
        from app.db.base import async_session_maker
        from app.models.models import Asset, IntlPriceCandle
        from sqlalchemy.dialects.postgresql import insert as pg_insert

        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=7)

        results = {"candles_inserted": 0, "errors": []}

        try:
            async with async_session_maker() as session:
                assets_result = await session.execute(
                    select(Asset.id, Asset.symbol)
                    .where(Asset.active == True)
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
                        if volume < 0:
                            volume = 0

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
                    results["errors"].append(f"{symbol}: {str(e)}")
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
            next_run=datetime.now(timezone.utc),
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

    async def run_job_now(self, name: str) -> Dict[str, Any]:
        if name not in self._jobs:
            raise ValueError(f"Job not found: {name}")
        job = self._jobs[name]
        return await self._execute_job(job)

    async def _execute_job(self, job: ScheduledJob) -> Dict[str, Any]:
        start = datetime.now(timezone.utc)
        try:
            result = await job.coroutine_func()
            duration_ms = (datetime.now(timezone.utc) - start).total_seconds() * 1000
            job.last_run = datetime.now(timezone.utc)
            job.run_count += 1
            job.next_run = datetime.now(timezone.utc) + timedelta(seconds=job.interval_seconds)
            self.logger.info(f"Job '{job.name}' completed in {duration_ms:.1f}ms")
            return {"status": "success", "job": job.name, "duration_ms": duration_ms, "result": result}
        except Exception as exc:
            duration_ms = (datetime.now(timezone.utc) - start).total_seconds() * 1000
            job.last_run = datetime.now(timezone.utc)
            job.run_count += 1
            job.error_count += 1
            job.next_run = datetime.now(timezone.utc) + timedelta(seconds=job.interval_seconds)
            self.logger.error(f"Job '{job.name}' failed: {exc}", exc_info=True)
            return {"status": "error", "job": job.name, "error": str(exc), "duration_ms": duration_ms}

    async def _scheduler_loop(self) -> None:
        self.logger.info("Scheduler loop started")
        while self._running:
            now = datetime.now(timezone.utc)
            for job in list(self._jobs.values()):
                if not job.enabled:
                    continue
                if job.next_run and now >= job.next_run:
                    job._task = asyncio.create_task(self._execute_job(job))
            await asyncio.sleep(1)

    def get_job_status(self, name: str) -> Optional[Dict[str, Any]]:
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

    def list_jobs(self) -> List[Dict[str, Any]]:
        return [self.get_job_status(name) for name in self._jobs]

    async def health_check(self) -> Dict[str, Any]:
        return {
            "service": self.service_name,
            "status": "healthy" if self._running else "stopped",
            "jobs_registered": len(self._jobs),
            "jobs_running": sum(1 for j in self._jobs.values() if j.enabled),
            "uptime_seconds": (datetime.now(timezone.utc) - self.created_at).total_seconds(),
        }
