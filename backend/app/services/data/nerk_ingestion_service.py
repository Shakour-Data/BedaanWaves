"""
Nerk Ingestion Service - Fetches Neark (نزدک) index constituent data.

Data sources:
- Price history: yfinance (Yahoo Finance) with .IR suffix fallback for Iranian stocks
- Fundamentals: yfinance + manual fallback
- Market overview: computed from stored data

Features:
- Neark index constituent ingestion (assets are flagged via is_nerk_constituent)
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
    IntlPriceCandle,
)
from app.services.core.base_service import DataService

logger = logging.getLogger(__name__)

# Path to Neark constituents CSV
NERK_CSV_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "nerk_constituents.csv"
)

# Neark index constituents (major Iranian stocks on Tehran Stock Exchange)
NEARK_CONSTITUENTS = [
    "6675",  # خپارس (Parsian)
    "6583",  # فولاد (Mobarakeh Steel)
    "6369",  # کنار
    "6587",  # پترا (Petra)
    "6391",  # شاراک (Sharak)
    "6374",  # ک.گل
    "6390",  # مپنا (Mapna)
    "6623",  # فیروزه (Firouz)
    "6403",  # غ.از
    "6387",  # ک.ماس
    "6624",  # دماون (Damavand)
    "6392",  # تاپ (Top)
    "6622",  # ک.شار
    "6402",  # ک.ت
    "6621",  # ک.ح
    "6394",  # ک.پ
    "6620",  # ک.ش
    "6393",  # ک.ف
    "6619",  # ک.م
    "6618",  # ک.ن
]

# Max concurrent requests
MAX_CONCURRENT = 3
# Batch size for DB inserts
CANDLE_BATCH_SIZE = 1000


class NerkIngestionService(DataService):
    """Service for ingesting Neark index constituent data.

    Neark constituents are regular assets flagged with
    ``is_nerk_constituent=True`` on the ``assets`` table.
    Price data is stored in ``intl_price_candles`` so the existing
    market-data pipeline can serve it without any special tables.
    """

    def __init__(self, service_name: str = "NerkIngestionService"):
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
            return {k: NerkIngestionService._clean_nan(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [NerkIngestionService._clean_nan(v) for v in obj]
        return obj

    def _load_symbols_from_csv(self) -> list[str]:
        """Load all Neark symbols from the CSV file."""
        symbols = []
        try:
            with open(NERK_CSV_PATH, newline="", encoding="utf-8") as f:
                reader = csv.reader(f)
                next(reader, None)
                for row in reader:
                    if row and len(row) >= 1 and row[0] and not row[0].startswith("File Creation"):
                        symbols.append(row[0].strip())
            logger.info(f"Loaded {len(symbols)} Neark symbols from {NERK_CSV_PATH}")
        except (FileNotFoundError, PermissionError, csv.Error) as exc:
            logger.error(f"Failed to load Neark symbols from CSV: {exc}")
            raise IngestionException(f"Neark symbol CSV load failed: {exc}") from exc
        return symbols

    @property
    def DEFAULT_CONSTITUENTS(self) -> list[str]:
        if not self._symbols:
            self._symbols = self._load_symbols_from_csv()
        return self._symbols

    async def initialize(self) -> None:
        self.logger.info("NerkIngestionService initialized")
        _ = self.DEFAULT_CONSTITUENTS

    async def shutdown(self) -> None:
        self.logger.info("NerkIngestionService shutdown")
        await self._http_client.aclose()

    async def _ensure_asset(self, symbol: str, name: str, sector: str = "", nerk_weight: float | None = None) -> Asset:
        """Get or create asset record for Neark constituent."""
        async with async_session_maker() as session:
            result = await session.execute(select(Asset).where(Asset.symbol == symbol))
            asset = result.scalar_one_or_none()
            if not asset:
                asset = Asset(
                    symbol=symbol,
                    name=name,
                    asset_class="EQUITY",
                    market="NASDAQ",
                    sector=sector,
                    country_code="IR",
                    currency="IRR",
                    active=True,
                    is_nerk_constituent=True,
                    nerk_weight=nerk_weight,
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
                if sector and not asset.sector:
                    asset.sector = sector
                    updated = True
                if not asset.is_nerk_constituent:
                    asset.is_nerk_constituent = True
                    updated = True
                if nerk_weight is not None and asset.nerk_weight is None:
                    asset.nerk_weight = nerk_weight
                    updated = True
                if updated:
                    await session.commit()
                    await session.refresh(asset)
            return asset

    async def _bulk_upsert_candles(self, candles: list[IntlPriceCandle]) -> int:
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
                        "source": c.source,
                        "data_quality": c.data_quality,
                        "adjusted_close": float(c.adjusted_close) if c.adjusted_close else None,
                        "split_ratio": float(c.split_ratio) if c.split_ratio else 1.0,
                    })

                stmt = pg_insert(IntlPriceCandle).values(rows)
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
                inserted = len(rows)
            except IntegrityError:
                await session.rollback()
                raise
            except Exception as exc:
                await session.rollback()
                self.logger.error(f"Bulk candle upsert failed: {exc}")
                raise IngestionException(f"Neark candle upsert failed: {exc}") from exc
        return inserted

    async def _fetch_from_yfinance(self, symbol: str, period: str = "2y") -> tuple[Any, Any]:
        """Fetch data from yfinance with .IR suffix fallback."""
        import yfinance as yf
        candidates = [symbol, f"{symbol}.IR", f"{symbol}.IRAN"]
        for candidate in candidates:
            try:
                async with self._semaphore:
                    ticker = yf.Ticker(candidate)
                    info = ticker.info or {}
                    hist = ticker.history(period=period, interval="1d", auto_adjust=True)
                    if not hist.empty:
                        return info, hist
            except Exception:
                continue
        raise IngestionException(f"No yfinance data for {symbol}")

    async def _fetch_from_tsetmc(self, symbol: str) -> tuple[dict, list[dict]]:
        """Fallback: scrape price history from TSETMC public endpoints."""
        try:
            async with self._semaphore:
                response = await self._http_client.get(
                    f"http://www.tsetmc.com/tsev2/data/Export-txt.aspx?a=1&t=i&b=0&s=0&c={symbol}",
                    timeout=15.0,
                )
                text = response.text
            rows = []
            for line in text.splitlines()[1:]:
                parts = line.split(",")
                if len(parts) >= 7:
                    rows.append({
                        "date": parts[0],
                        "open": float(parts[1]),
                        "high": float(parts[2]),
                        "low": float(parts[3]),
                        "close": float(parts[4]),
                        "volume": int(float(parts[5])),
                        "count": int(float(parts[6])),
                    })
            return {}, rows
        except Exception as exc:
            self.logger.warning(f"TSETMC fetch failed for {symbol}: {exc}")
            return {}, []

    async def ingest_price_history(self, symbol: str, period: str = "2y") -> int:
        """Fetch and store price history for a Neark constituent."""
        try:
            try:
                info, hist = await self._fetch_from_yfinance(symbol, period=period)
            except Exception:
                _, rows = await self._fetch_from_tsetmc(symbol)
                if not rows:
                    return 0
                asset = await self._ensure_asset(symbol, symbol)
                candles = []
                for row in rows:
                    ts = datetime.strptime(row["date"], "%Y%m%d").replace(tzinfo=None)
                    candles.append(IntlPriceCandle(
                        asset_id=asset.id,
                        timestamp=ts,
                        timeframe="1d",
                        open=row["open"],
                        high=row["high"],
                        low=row["low"],
                        close=row["close"],
                        volume=row["volume"],
                        turnover=row["close"] * row["volume"],
                        source="tsetmc",
                        data_quality="PROVISIONAL",
                    ))
                    if len(candles) >= CANDLE_BATCH_SIZE:
                        await self._bulk_upsert_candles(candles)
                        candles = []
                if candles:
                    await self._bulk_upsert_candles(candles)
                return len(rows)

            asset = await self._ensure_asset(
                symbol,
                info.get("longName", symbol),
                sector=info.get("sector", ""),
            )

            candles = []
            for timestamp, row in hist.iterrows():
                ts = timestamp.to_pydatetime().replace(tzinfo=None) if hasattr(timestamp, 'to_pydatetime') else timestamp
                open_p = float(row["Open"])
                high_p = float(row["High"])
                low_p = float(row["Low"])
                close_p = float(row["Close"])
                low_p = min(open_p, high_p, low_p, close_p)
                high_p = max(open_p, high_p, low_p, close_p)
                candle = IntlPriceCandle(
                    asset_id=asset.id,
                    timestamp=ts,
                    timeframe="1d",
                    open=open_p,
                    high=high_p,
                    low=low_p,
                    close=close_p,
                    volume=int(row["Volume"]),
                    turnover=float(row["Volume"]) * float(row["Close"]),
                    source="yfinance",
                    data_quality="CONFIRMED",
                )
                candles.append(candle)

                if len(candles) >= CANDLE_BATCH_SIZE:
                    count = await self._bulk_upsert_candles(candles)
                    candles = []

            if candles:
                count = await self._bulk_upsert_candles(candles)
            return len(candles)
        except Exception as exc:
            self.logger.error(f"Failed to ingest prices for {symbol}: {exc}")
            raise IngestionException(f"Neark price ingestion failed for {symbol}: {exc}") from exc

    async def ingest_fundamentals(self, symbol: str) -> bool:
        """Fetch and store fundamental data for a Neark constituent."""
        try:
            info, _ = await self._fetch_from_yfinance(symbol, period="1y")
        except Exception as exc:
            self.logger.warning(f"Fundamentals fetch failed for {symbol}: {exc}")
            return False

        try:
            asset = await self._ensure_asset(
                symbol,
                info.get("longName", symbol),
                sector=info.get("sector", ""),
            )

            async with async_session_maker() as session:
                ratio = FundamentalRatio(
                    asset_id=asset.id,
                    market="NASDAQ",
                    period="LATEST",
                    eps=self._clean_nan(info.get("trailingEps")),
                    pe=self._clean_nan(info.get("trailingPE")),
                    pb=self._clean_nan(info.get("priceToBook")),
                    dps=self._clean_nan(info.get("dividendRate")),
                    roe=self._clean_nan(info.get("returnOnEquity")),
                    profit_margin=self._clean_nan(info.get("profitMargins")),
                    market_cap=self._clean_nan(info.get("marketCap")),
                    book_value=self._clean_nan(info.get("bookValue")),
                    as_of=datetime.now(UTC).date(),
                )
                session.add(ratio)
                await session.commit()
            return True
        except Exception as exc:
            self.logger.error(f"Failed to ingest fundamentals for {symbol}: {exc}")
            return False

    async def bulk_ingest(self, symbols: list[str] | None = None, include_fundamentals: bool = False) -> dict[str, Any]:
        """Bulk-ingest price history for Neark constituents."""
        symbols = symbols or self.DEFAULT_CONSTITUENTS
        self.logger.info(f"Starting Neark bulk ingestion for {len(symbols)} symbols")

        results = {"prices": 0, "fundamentals": 0, "errors": []}
        chunk_size = 20

        for i in range(0, len(symbols), chunk_size):
            chunk = symbols[i:i + chunk_size]
            self.logger.info(f"Nerk bulk chunk {i // chunk_size + 1}/{(len(symbols) + chunk_size - 1) // chunk_size}")

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

        self.logger.info(f"Nerk bulk ingestion complete: {results}")
        return results

    async def daily_update(self, symbols: list[str] | None = None) -> dict[str, Any]:
        """Run daily incremental update for Neark constituents."""
        symbols = symbols or self.DEFAULT_CONSTITUENTS
        self.logger.info(f"Starting Neark daily update for {len(symbols)} symbols")

        results = {"prices": 0, "errors": []}
        chunk_size = 20

        for i in range(0, len(symbols), chunk_size):
            chunk = symbols[i:i + chunk_size]
            price_tasks = [self.ingest_price_history(sym, period="5d") for sym in chunk]
            price_results = await asyncio.gather(*price_tasks, return_exceptions=True)
            for r in price_results:
                if isinstance(r, int):
                    results["prices"] += r
                else:
                    results["errors"].append(str(r))
            await asyncio.sleep(1)

        self.logger.info(f"Nerk daily update complete: {results}")
        return results

    async def get_constituents(self) -> list[dict[str, Any]]:
        """Get all Neark index constituents with latest stored data."""
        constituents = []
        async with async_session_maker() as session:
            result = await session.execute(
                select(Asset)
                .where(Asset.is_nerk_constituent == True)
                .where(Asset.active)
                .order_by(Asset.symbol)
            )
            assets = result.scalars().all()

            for asset in assets:
                candle_result = await session.execute(
                    select(IntlPriceCandle)
                    .where(IntlPriceCandle.asset_id == asset.id)
                    .where(IntlPriceCandle.timeframe == "1d")
                    .order_by(IntlPriceCandle.timestamp.desc())
                    .limit(2)
                )
                candles = candle_result.scalars().all()

                change_pct = 0.0
                price = 0.0
                if len(candles) >= 1:
                    price = float(candles[0].close)
                if len(candles) >= 2:
                    prev = float(candles[1].close)
                    if prev > 0:
                        change_pct = ((price - prev) / prev) * 100

                constituents.append({
                    "id": str(asset.id),
                    "symbol": asset.symbol,
                    "name": asset.name,
                    "sector": asset.sector,
                    "asset_class": asset.asset_class,
                    "market": asset.market,
                    "active": asset.active,
                    "price": price,
                    "change_pct": round(change_pct, 2),
                    "nerk_weight": float(asset.nerk_weight) if asset.nerk_weight else None,
                })

        return constituents

    async def get_market_overview(self) -> dict[str, Any]:
        """Get Neark index market overview."""
        constituents = await self.get_constituents()
        active = sum(1 for c in constituents if c["active"])
        gainers = [c for c in constituents if c["change_pct"] > 0]
        losers = [c for c in constituents if c["change_pct"] < 0]
        avg_change = 0.0
        if constituents:
            avg_change = sum(c["change_pct"] for c in constituents) / len(constituents)

        return {
            "market": "NEARK",
            "total_symbols": len(constituents),
            "active_symbols": active,
            "currency": "IRR",
            "timezone": "Asia/Tehran",
            "index": "Nerek (نزدک)",
            "last_updated": datetime.now(UTC).isoformat(),
            "constituents_count": len(constituents),
            "avg_change_pct": round(avg_change, 2),
            "gainers_count": len(gainers),
            "losers_count": len(losers),
        }
