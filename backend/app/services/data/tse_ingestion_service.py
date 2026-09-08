"""
TSE Ingestion Service - Fetches Tehran Stock Exchange data and Neark index constituents.

Data sources:
- Price history: yfinance (Yahoo Finance) with .IR suffix fallback
- Fundamentals: TSETMC scraping fallback (yfinance limited for TSE)
- Market overview: TSETMC public endpoints

Features:
- Neark index constituent ingestion
- Concurrent batch processing with rate limiting
- Batched database writes for performance
- Incremental daily updates
- Idempotent operations (upsert on conflict)
"""

import asyncio
import csv
import logging
import math
import os
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError

from app.core.config import get_settings
from app.core.exceptions import IngestionException
from app.db.base import async_session_maker
from app.models.models import (
    Asset,
    FinancialStatement,
    FundamentalRatio,
    TSEOrderBook,
    TSEPriceCandle,
)
from app.services.core.base_service import DataService

logger = logging.getLogger(__name__)

# Path to TSE symbols CSV
TSE_CSV_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "tse_symbols.csv"
)

# Neark index constituents (major TSE stocks)
NEARK_CONSTITUENTS = [
    "6675",  # خپارس
    "6583",  # فولاد
    "6369",  # ک Sí س
    "6587",  # پترا
    "6391",  # شاراک
    "6374",  # ک▪گل
    "6390",  # مپنا
    "6623",  # فیروزه
    "6403",  # Ĵ▪از
    "6387",  # ك▪ماس
    "6624",  # دماون
    "6392",  # تاپ
    "6622",  # ك▪شار
    "6402",  # ك.ت
    "6621",  # ك▪ح
    "6394",  # ك.پ
    "6620",  # ك.ش
    "6393",  # ك.ف
    "6619",  # ك.م
    "6618",  # ك.ن
]

# Max concurrent requests
MAX_CONCURRENT = 3
# Batch size for DB inserts
CANDLE_BATCH_SIZE = 1000
# TSETMC base URL
TSETMC_BASE_URL = "http://www.tsetmc.com"


class TseIngestionService(DataService):
    """Service for ingesting Tehran Stock Exchange data and Neark index constituents."""

    def __init__(self, service_name: str = "TseIngestionService"):
        super().__init__(service_name)
        self.settings = get_settings()
        self._symbols: list[str] = []
        self._semaphore = asyncio.Semaphore(MAX_CONCURRENT)
        self._http_client = httpx.AsyncClient(
            timeout=30.0,
            headers={"User-Agent": "Mozilla/5.0 (compatible; BedaanWaves/1.0)"},
        )

    @staticmethod
    def _clean_nan(obj):
        """Replace NaN/Inf values with None for JSON serialization."""
        if isinstance(obj, str):
            lower = obj.strip().lower()
            if lower in ("nan", "inf", "-inf", "infinity", "-infinity", "none", "null"):
                return None
            try:
                f = float(obj)
                if math.isnan(f) or math.isinf(f):
                    return None
                return f
            except (ValueError, TypeError):
                return obj
        if isinstance(obj, float):
            if math.isnan(obj) or math.isinf(obj):
                return None
            return obj
        elif isinstance(obj, dict):
            return {k: TseIngestionService._clean_nan(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [TseIngestionService._clean_nan(v) for v in obj]
        return obj

    def _load_symbols_from_csv(self) -> list[str]:
        """Load all TSE symbols from the CSV file."""
        symbols = []
        try:
            with open(TSE_CSV_PATH, newline="", encoding="utf-8") as f:
                reader = csv.reader(f)
                next(reader, None)
                for row in reader:
                    if row and len(row) >= 1 and row[0] and not row[0].startswith("File Creation"):
                        symbols.append(row[0].strip())
            logger.info(f"Loaded {len(symbols)} symbols from {TSE_CSV_PATH}")
        except FileNotFoundError:
            logger.warning(f"TSE symbols CSV not found at {TSE_CSV_PATH}, using default constituents")
            symbols = list(NEARK_CONSTITUENTS)
        except (PermissionError, csv.Error) as exc:
            logger.error(f"Failed to load TSE symbols from CSV: {exc}")
            raise IngestionException(f"TSE symbol CSV load failed: {exc}") from exc
        return symbols

    @property
    def DEFAULT_CONSTITUENTS(self) -> list[str]:
        if not self._symbols:
            self._symbols = self._load_symbols_from_csv()
        return self._symbols

    async def initialize(self) -> None:
        self.logger.info("TseIngestionService initialized")

    async def shutdown(self) -> None:
        self.logger.info("TseIngestionService shutdown")
        await self._http_client.aclose()

    async def _ensure_asset(
        self,
        symbol: str,
        name: str,
        asset_class: str = "EQUITY",
        sector: str = "",
        industry: str = "",
    ) -> Asset:
        """Get or create asset record for TSE market."""
        async with async_session_maker() as session:
            result = await session.execute(select(Asset).where(Asset.symbol == symbol))
            asset = result.scalar_one_or_none()
            if not asset:
                asset = Asset(
                    symbol=symbol,
                    name=name,
                    asset_class=asset_class,
                    market="TSE",
                    sector=sector,
                    industry=industry,
                    country_code="IR",
                    currency="IRR",
                    active=True,
                )
                session.add(asset)
                try:
                    await session.commit()
                    await session.refresh(asset)
                except IntegrityError:
                    await session.rollback()
                    result = await session.execute(select(Asset).where(Asset.symbol == symbol))
                    asset = result.scalar_one_or_none()
            else:
                updated = False
                if asset.market != "TSE":
                    asset.market = "TSE"
                    updated = True
                if sector and not asset.sector:
                    asset.sector = sector
                    updated = True
                if industry and not asset.industry:
                    asset.industry = industry
                    updated = True
                if updated:
                    await session.commit()
                    await session.refresh(asset)
            return asset

    async def _bulk_upsert_candles(self, candles: list[TSEPriceCandle]) -> int:
        """Bulk upsert candles using PostgreSQL upsert."""
        if not candles:
            return 0
        inserted = 0
        async with async_session_maker() as session:
            try:
                rows = []
                for c in candles:
                    rows.append({
                        "asset_id": str(c.asset_id),
                        "timestamp": c.timestamp,
                        "timeframe": c.timeframe,
                        "open": float(c.open),
                        "high": float(c.high),
                        "low": float(c.low),
                        "close": float(c.close),
                        "volume": int(c.volume),
                        "turnover": float(c.turnover) if c.turnover else None,
                        "transactions": int(c.transactions) if c.transactions else None,
                        "source": c.source,
                        "data_quality": c.data_quality,
                        "adjusted_close": float(c.adjusted_close) if c.adjusted_close else None,
                        "split_ratio": float(c.split_ratio) if c.split_ratio else 1.0,
                    })

                stmt = pg_insert(TSEPriceCandle).values(rows)
                stmt = stmt.on_conflict_do_update(
                    index_elements=["asset_id", "timestamp", "timeframe"],
                    set_={
                        "open": stmt.excluded.open,
                        "high": stmt.excluded.high,
                        "low": stmt.excluded.low,
                        "close": stmt.excluded.close,
                        "volume": stmt.excluded.volume,
                        "turnover": stmt.excluded.turnover,
                        "transactions": stmt.excluded.transactions,
                        "source": stmt.excluded.source,
                        "data_quality": stmt.excluded.data_quality,
                        "adjusted_close": stmt.excluded.adjusted_close,
                        "split_ratio": stmt.excluded.split_ratio,
                    },
                )
                await session.execute(stmt)
                await session.commit()
                inserted = len(rows)
            except IntegrityError:
                await session.rollback()
                raise
            except Exception as exc:
                await session.rollback()
                self.logger.error(f"Bulk candle upsert failed: {exc}")
                raise IngestionException(f"TSE candle upsert failed: {exc}") from exc
        return inserted

    async def _fetch_from_yfinance(self, symbol: str, period: str = "2y") -> tuple[Any, Any]:
        """Fetch data from yfinance with .IR suffix fallback."""
        import yfinance as yf

        ticker_symbols = [symbol, f"{symbol}.IR", f"{symbol}.TSE"]
        hist = None
        info = {}

        for sym in ticker_symbols:
            try:
                async with self._semaphore:
                    ticker = yf.Ticker(sym)
                    info = ticker.info or {}
                    hist = ticker.history(period=period, interval="1d", auto_adjust=True)
                    if not hist.empty:
                        logger.info(f"Successfully fetched {symbol} using ticker {sym}")
                        break
            except Exception as e:
                logger.debug(f"yfinance fetch failed for {sym}: {e}")
                continue

        return hist, info

    async def _fetch_from_tsetmc(self, symbol: str) -> tuple[Any, dict]:
        """Fallback: fetch data from TSETMC public API."""
        try:
            async with self._semaphore:
                url = f"{TSETMC_BASE_URL}/tsev2/xchart/inst/ historical/{symbol}.csv"
                resp = await self._http_client.get(url, follow_redirects=True)
                if resp.status_code == 200 and resp.text.strip():
                    import pandas as pd
                    from io import StringIO

                    df = pd.read_csv(StringIO(resp.text))
                    if not df.empty and len(df.columns) >= 6:
                        df.columns = ["Date", "High", "Low", "Close", "Open", "Volume"]
                        df["Date"] = pd.to_datetime(df["Date"])
                        df = df.set_index("Date")
                        return df, {"source": "tsetmc"}
        except Exception as e:
            logger.warning(f"TSETMC fetch failed for {symbol}: {e}")

        return None, {}

    async def ingest_price_history(self, symbol: str, period: str = "2y") -> int:
        """Fetch and store price history for a TSE symbol."""
        try:
            hist, info = await self._fetch_from_yfinance(symbol, period=period)

            if hist is None or hist.empty:
                hist, info = await self._fetch_from_tsetmc(symbol)

            if hist is None or hist.empty:
                logger.warning(f"No price data found for TSE symbol {symbol}")
                return 0

            asset = await self._ensure_asset(
                symbol,
                info.get("longName", info.get("shortName", symbol)),
                asset_class=info.get("quoteType", "EQUITY").upper() if info.get("quoteType") else "EQUITY",
                sector=info.get("sector", ""),
                industry=info.get("industry", ""),
            )

            candles = []
            for timestamp, row in hist.iterrows():
                ts = timestamp.to_pydatetime().replace(tzinfo=None) if hasattr(timestamp, 'to_pydatetime') else timestamp
                open_p = float(row.get("Open", 0))
                high_p = float(row.get("High", 0))
                low_p = float(row.get("Low", 0))
                close_p = float(row.get("Close", 0))
                volume_p = float(row.get("Volume", 0))

                low_p = min(open_p, high_p, low_p, close_p)
                high_p = max(open_p, high_p, low_p, close_p)

                candle = TSEPriceCandle(
                    asset_id=asset.id,
                    timestamp=ts,
                    timeframe="1d",
                    open=open_p,
                    high=high_p,
                    low=low_p,
                    close=close_p,
                    volume=int(volume_p),
                    turnover=volume_p * close_p if close_p > 0 else None,
                    source=info.get("source", "yfinance"),
                    data_quality="CONFIRMED",
                )
                candles.append(candle)

                if len(candles) >= CANDLE_BATCH_SIZE:
                    count = await self._bulk_upsert_candles(candles)
                    candles = []

            if candles:
                count = await self._bulk_upsert_candles(candles)
            return count if candles else 0
        except IngestionException:
            raise
        except Exception as exc:
            self.logger.error(f"Failed to ingest prices for {symbol}: {exc}")
            raise IngestionException(f"TSE price ingestion failed for {symbol}: {exc}") from exc

    async def ingest_fundamentals(self, symbol: str) -> bool:
        """Fetch and store fundamental data for a TSE symbol."""
        try:
            hist, info = await self._fetch_from_yfinance(symbol, period="1y")
            asset = await self._ensure_asset(
                symbol,
                info.get("longName", info.get("shortName", symbol)),
                asset_class=info.get("quoteType", "EQUITY").upper() if info.get("quoteType") else "EQUITY",
            )

            if not info:
                logger.warning(f"No fundamental data available for {symbol}")
                return False

            statements = []
            ratios = []
            seen_periods = set()

            if info.get("earningsQuarterly"):
                for quarter_data in info.get("earningsQuarterly", []):
                    period_end = quarter_data.get("endDate", "")
                    if not period_end:
                        continue
                    try:
                        period_dt = datetime.strptime(period_end, "%Y-%m-%d")
                        quarter = (period_dt.month - 1) // 3 + 1
                        period_str = f"{period_dt.year}Q{quarter}"
                        fiscal_year = period_dt.year
                        seen_periods.add(period_str)

                        stmt = FinancialStatement(
                            asset_id=asset.id,
                            market="TSE",
                            period=period_str,
                            statement_type="INCOME",
                            fiscal_year=fiscal_year,
                            data=self._clean_nan(quarter_data),
                            as_of=period_dt.date(),
                        )
                        statements.append(stmt)

                        ratios.append(
                            FundamentalRatio(
                                asset_id=asset.id,
                                market="TSE",
                                period=period_str,
                                eps=self._clean_nan(info.get("trailingEps")),
                                pe=self._clean_nan(info.get("trailingPE")),
                                pb=self._clean_nan(info.get("priceToBook")),
                                dps=self._clean_nan(info.get("dividendRate")),
                                roe=self._clean_nan(info.get("returnOnEquity")),
                                profit_margin=self._clean_nan(info.get("profitMargins")),
                                market_cap=self._clean_nan(info.get("marketCap")),
                                book_value=self._clean_nan(info.get("bookValue")),
                                as_of=period_dt.date(),
                            )
                        )
                    except (ValueError, TypeError) as e:
                        logger.debug(f"Skipping quarter for {symbol}: {e}")
                        continue

            if statements:
                async with async_session_maker() as session:
                    for stmt in statements:
                        stmt_data = {
                            "asset_id": str(stmt.asset_id),
                            "market": stmt.market,
                            "period": stmt.period,
                            "statement_type": stmt.statement_type,
                            "fiscal_year": stmt.fiscal_year,
                            "data": stmt.data,
                            "as_of": stmt.as_of,
                        }
                        upsert = pg_insert(FinancialStatement).values(stmt_data)
                        upsert = upsert.on_conflict_do_update(
                            index_elements=["asset_id", "period", "statement_type", "market"],
                            set_={"data": upsert.excluded.data, "as_of": upsert.excluded.as_of},
                        )
                        await session.execute(upsert)

                    for ratio in ratios:
                        ratio_data = {
                            "asset_id": str(ratio.asset_id),
                            "market": ratio.market,
                            "period": ratio.period,
                            "eps": ratio.eps,
                            "pe": ratio.pe,
                            "pb": ratio.pb,
                            "dps": ratio.dps,
                            "roe": ratio.roe,
                            "profit_margin": ratio.profit_margin,
                            "market_cap": ratio.market_cap,
                            "book_value": ratio.book_value,
                            "as_of": ratio.as_of,
                        }
                        upsert = pg_insert(FundamentalRatio).values(ratio_data)
                        upsert = upsert.on_conflict_do_update(
                            index_elements=["asset_id", "period", "market"],
                            set_={
                                "eps": upsert.excluded.eps,
                                "pe": upsert.excluded.pe,
                                "pb": upsert.excluded.pb,
                                "dps": upsert.excluded.dps,
                                "roe": upsert.excluded.roe,
                                "profit_margin": upsert.excluded.profit_margin,
                                "market_cap": upsert.excluded.market_cap,
                                "book_value": upsert.excluded.book_value,
                                "as_of": upsert.excluded.as_of,
                            },
                        )
                        await session.execute(upsert)

                    await session.commit()

            return len(seen_periods) > 0
        except Exception as e:
            self.logger.error(f"Failed to ingest fundamentals for {symbol}: {e}")
            return False

    async def bulk_ingest(self, symbols: list[str] | None = None, include_fundamentals: bool = False) -> dict[str, Any]:
        """Bulk ingest price history for TSE symbols."""
        symbols = symbols or self.DEFAULT_CONSTITUENTS
        self.logger.info(f"Starting TSE bulk ingestion for {len(symbols)} symbols")

        results = {"prices": 0, "fundamentals": 0, "errors": []}

        chunk_size = 20
        for i in range(0, len(symbols), chunk_size):
            chunk = symbols[i:i + chunk_size]
            self.logger.info(f"TSE chunk {i // chunk_size + 1}/{(len(symbols) + chunk_size - 1) // chunk_size}: {chunk[0]}..{chunk[-1]}")

            price_tasks = [self.ingest_price_history(sym, period="2y") for sym in chunk]
            price_results = await asyncio.gather(*price_tasks, return_exceptions=True)
            for r in price_results:
                if isinstance(r, int):
                    results["prices"] += r
                else:
                    results["errors"].append(str(r))

            if include_fundamentals:
                fund_tasks = [self.ingest_fundamentals(sym) for sym in chunk]
                fund_results = await asyncio.gather(*fund_tasks, return_exceptions=True)
                for r in fund_results:
                    if isinstance(r, bool) and r:
                        results["fundamentals"] += 1
                    elif isinstance(r, Exception):
                        results["errors"].append(str(r))

            await asyncio.sleep(1)

        self.logger.info(f"TSE bulk ingestion complete: {results}")
        return results

    async def daily_update(self, symbols: list[str] | None = None) -> dict[str, Any]:
        """Run daily incremental update for TSE symbols."""
        symbols = symbols or self.DEFAULT_CONSTITUENTS
        self.logger.info(f"Starting TSE daily update for {len(symbols)} symbols")

        results = {"prices": 0, "errors": []}

        chunk_size = 20
        for i in range(0, len(symbols), chunk_size):
            chunk = symbols[i:i + chunk_size]
            self.logger.info(f"TSE daily update chunk {i // chunk_size + 1}/{(len(symbols) + chunk_size - 1) // chunk_size}")

            price_tasks = [self.ingest_price_history(sym, period="5d") for sym in chunk]
            price_results = await asyncio.gather(*price_tasks, return_exceptions=True)
            for r in price_results:
                if isinstance(r, int):
                    results["prices"] += r
                else:
                    results["errors"].append(str(r))

            await asyncio.sleep(1)

        self.logger.info(f"TSE daily update complete: {results}")
        return results

    async def get_nerk_constituents(self) -> list[dict[str, Any]]:
        """Get Neark index constituents with basic info."""
        constituents = []
        for symbol in self.DEFAULT_CONSTITUENTS:
            async with async_session_maker() as session:
                result = await session.execute(
                    select(Asset).where(Asset.symbol == symbol).where(Asset.market == "TSE")
                )
                asset = result.scalar_one_or_none()
                if asset:
                    constituents.append({
                        "symbol": asset.symbol,
                        "name": asset.name,
                        "sector": asset.sector,
                        "asset_class": asset.asset_class,
                        "market": asset.market,
                        "active": asset.active,
                    })
                else:
                    constituents.append({
                        "symbol": symbol,
                        "name": symbol,
                        "sector": None,
                        "asset_class": "EQUITY",
                        "market": "TSE",
                        "active": True,
                    })
        return constituents

    async def get_market_overview(self) -> dict[str, Any]:
        """Get TSE market overview summary."""
        async with async_session_maker() as session:
            total_assets = await session.execute(
                select(func.count(Asset.id)).where(Asset.market == "TSE")
            )
            total_count = total_assets.scalar_one_or_none() or 0

            active_assets = await session.execute(
                select(func.count(Asset.id)).where(Asset.market == "TSE").where(Asset.active)
            )
            active_count = active_assets.scalar_one_or_none() or 0

            return {
                "market": "TSE",
                "total_symbols": total_count,
                "active_symbols": active_count,
                "currency": "IRR",
                "timezone": "Asia/Tehran",
                "index": "Nerek (نزدک)",
                "last_updated": datetime.now(UTC).isoformat(),
            }
