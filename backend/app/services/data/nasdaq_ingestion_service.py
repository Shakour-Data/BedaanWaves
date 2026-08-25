"""
Nasdaq Ingestion Service - Fetches Nasdaq Composite index and ALL constituent data.

Data sources:
- Price history: yfinance (Yahoo Finance)
- Fundamentals: yfinance
- Board/Officers: yfinance companyOfficers + SEC EDGAR
- News: yfinance ticker.news
- Macro: yfinance macro tickers (^GSPC, ^VIX, ^TNX, DX-Y.NYB, GC=F, CL=F)

Features:
- Full universe ingestion from nasdaq_symbols.csv (5569 symbols)
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
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError
from app.core.exceptions import DataParsingException, IngestionException

from app.services.core.base_service import DataService
from app.core.config import get_settings
from app.models.models import (
    Asset,
    IntlPriceCandle,
    IRFinancialStatement,
    IRFundamentalRatio,
    CompanyLeadership,
    News,
    MacroIndicator,
)
from app.db.base import async_session_maker

logger = logging.getLogger(__name__)

# Path to Nasdaq symbols CSV
NASDAQ_CSV_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "nasdaq_symbols.csv"
)

# Macro tickers to track
MACRO_TICKERS = {
    "^GSPC": ("S&P 500", "Index"),
    "^VIX": ("CBOE Volatility Index", "Index"),
    "^TNX": ("10-Year Treasury Yield", "Percent"),
    "DX-Y.NYB": ("US Dollar Index", "Index"),
    "GC=F": ("Gold Futures", "USD/oz"),
    "CL=F": ("Crude Oil Futures", "USD/barrel"),
}

# Max concurrent yfinance requests
MAX_CONCURRENT = 5
# Batch size for DB inserts
CANDLE_BATCH_SIZE = 1000
NEWS_BATCH_SIZE = 500


class NasdaqIngestionService(DataService):
    """Service for ingesting Nasdaq Composite index and ALL constituent data."""

    def __init__(self, service_name: str = "NasdaqIngestionService"):
        super().__init__(service_name)
        self.settings = get_settings()
        self._symbols: List[str] = []
        self._semaphore = asyncio.Semaphore(MAX_CONCURRENT)

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
            return {k: NasdaqIngestionService._clean_nan(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [NasdaqIngestionService._clean_nan(v) for v in obj]
        return obj

    def _load_symbols_from_csv(self) -> List[str]:
        """Load all Nasdaq symbols from the CSV file."""
        symbols = []
        try:
            with open(NASDAQ_CSV_PATH, newline="", encoding="utf-8") as f:
                reader = csv.reader(f)
                next(reader, None)
                for row in reader:
                    if row and len(row) >= 1 and row[0] and not row[0].startswith("File Creation"):
                        symbols.append(row[0].strip())
            logger.info(f"Loaded {len(symbols)} symbols from {NASDAQ_CSV_PATH}")
        except (FileNotFoundError, PermissionError, csv.Error) as exc:
            logger.error(f"Failed to load Nasdaq symbols from CSV: {exc}")
            raise IngestionException(f"Nasdaq symbol CSV load failed: {exc}") from exc
        return symbols

    @property
    def DEFAULT_CONSTITUENTS(self) -> List[str]:
        if not self._symbols:
            self._symbols = self._load_symbols_from_csv()
        return self._symbols

    async def initialize(self) -> None:
        self.logger.info("NasdaqIngestionService initialized")
        # Pre-load symbols
        _ = self.DEFAULT_CONSTITUENTS

    async def shutdown(self) -> None:
        self.logger.info("NasdaqIngestionService shutdown")

    async def _ensure_asset(self, symbol: str, name: str, asset_class: str = "EQUITY",
                            market: str = "NASDAQ", sector: str = "", industry: str = "") -> Asset:
        """Get or create asset record."""
        async with async_session_maker() as session:
            result = await session.execute(select(Asset).where(Asset.symbol == symbol))
            asset = result.scalar_one_or_none()
            if not asset:
                asset = Asset(
                    symbol=symbol,
                    name=name,
                    asset_class=asset_class,
                    market=market,
                    sector=sector,
                    industry=industry,
                    country_code="US",
                    currency="USD",
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
            return asset

    async def _bulk_upsert_candles(self, candles: List[IntlPriceCandle]) -> int:
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
                raise IngestionException(f"Nasdaq candle upsert failed: {exc}") from exc
        return inserted

    async def ingest_price_history(self, symbol: str, period: str = "5y") -> int:
        """Fetch and store price history for a symbol."""
        import yfinance as yf
        try:
            async with self._semaphore:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period=period, interval="1d", auto_adjust=True)
                if hist.empty:
                    return 0

                asset = await self._ensure_asset(symbol, ticker.info.get("longName", symbol), "EQUITY")
                
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

                # Batch insert
                count = await self._bulk_upsert_candles(candles)
                return count
        except IngestionException:
            raise
        except Exception as exc:
            self.logger.error(f"Failed to ingest prices for {symbol}: {exc}")
            raise IngestionException(f"Nasdaq price ingestion failed for {symbol}: {exc}") from exc

    async def ingest_fundamentals(self, symbol: str) -> bool:
        """Fetch and store fundamental data for a symbol."""
        import yfinance as yf
        try:
            async with self._semaphore:
                ticker = yf.Ticker(symbol)
                asset = await self._ensure_asset(symbol, ticker.info.get("longName", symbol), "EQUITY")

                income_stmt = ticker.quarterly_financials
                balance_sheet = ticker.quarterly_balance_sheet
                cashflow = ticker.quarterly_cashflow
                info = ticker.info or {}

                statements = []
                ratios = []

                if not income_stmt.empty:
                    for period_end in income_stmt.columns:
                        quarter = (period_end.month - 1) // 3 + 1
                        period_str = f"{period_end.year}Q{quarter}"
                        fiscal_year = period_end.year
                        as_of = period_end.date() if hasattr(period_end, "date") else None

                        # Income statement
                        stmt = IRFinancialStatement(
                            asset_id=asset.id,
                            market="NASDAQ",
                            period=period_str,
                            statement_type="INCOME",
                            fiscal_year=fiscal_year,
                            data=self._clean_nan(income_stmt[period_end].to_dict()),
                            as_of=as_of,
                        )
                        statements.append(stmt)

                        # Balance sheet
                        if not balance_sheet.empty and period_end in balance_sheet.columns:
                            bs_stmt = IRFinancialStatement(
                                asset_id=asset.id,
                                market="NASDAQ",
                                period=period_str,
                                statement_type="BALANCE_SHEET",
                                fiscal_year=fiscal_year,
                                data=self._clean_nan(balance_sheet[period_end].to_dict()),
                                as_of=as_of,
                            )
                            statements.append(bs_stmt)

                        # Cash flow
                        if not cashflow.empty and period_end in cashflow.columns:
                            cf_stmt = IRFinancialStatement(
                                asset_id=asset.id,
                                market="NASDAQ",
                                period=period_str,
                                statement_type="CASH_FLOW",
                                fiscal_year=fiscal_year,
                                data=self._clean_nan(cashflow[period_end].to_dict()),
                                as_of=as_of,
                            )
                            statements.append(cf_stmt)

                        # Ratios
                        ratio = IRFundamentalRatio(
                            asset_id=asset.id,
                            market="NASDAQ",
                            period=period_str,
                            eps=self._clean_nan(info.get("trailingEps")),
                            pe=self._clean_nan(info.get("trailingPE")),
                            pb=self._clean_nan(info.get("priceToBook")),
                            dps=self._clean_nan(info.get("dividendRate")),
                            roe=self._clean_nan(info.get("returnOnEquity")),
                            profit_margin=self._clean_nan(info.get("profitMargins")),
                            market_cap=self._clean_nan(info.get("marketCap")),
                            book_value=self._clean_nan(info.get("bookValue")),
                            as_of=as_of,
                        )
                        ratios.append(ratio)

                async with async_session_maker() as session:
                    # Batch upsert statements
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
                        upsert = pg_insert(IRFinancialStatement).values(stmt_data)
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
                        upsert = pg_insert(IRFundamentalRatio).values(ratio_data)
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
                return True
        except Exception as e:
            self.logger.error(f"Failed to ingest fundamentals for {symbol}: {e}")
            return False

    async def ingest_board_members(self, symbol: str) -> int:
        """Fetch board members and officers from yfinance."""
        import yfinance as yf
        try:
            async with self._semaphore:
                ticker = yf.Ticker(symbol)
                asset = await self._ensure_asset(symbol, ticker.info.get("longName", symbol), "EQUITY")
                info = ticker.info or {}
                officers = info.get("companyOfficers", [])

                leaders = []
                for officer in officers:
                    name = officer.get("name", "")
                    title = officer.get("title", "")
                    if not name or not title:
                        continue

                    start_date = None
                    if officer.get("startDate"):
                        try:
                            start_date = datetime.strptime(officer["startDate"], "%Y-%m-%d").date()
                        except (ValueError, TypeError):
                            pass

                    leader = CompanyLeadership(
                        asset_id=asset.id,
                        name=name,
                        title=title,
                        leadership_type="officer",
                        start_date=start_date,
                        source="yfinance",
                    )
                    leaders.append(leader)

                if leaders:
                    async with async_session_maker() as session:
                        session.add_all(leaders)
                        await session.commit()
                return len(leaders)
        except Exception as e:
            self.logger.error(f"Failed to ingest board for {symbol}: {e}")
            return 0

    async def ingest_news_for_symbol(self, symbol: str, days: int = 7) -> int:
        """Fetch recent news for a symbol from yfinance."""
        import yfinance as yf
        try:
            async with self._semaphore:
                ticker = yf.Ticker(symbol)
                raw_news = ticker.news
                if not raw_news:
                    return 0

                asset = await self._ensure_asset(symbol, ticker.info.get("longName", symbol), "EQUITY")
                
                cutoff = datetime.now(timezone.utc) - timedelta(days=days)
                news_items = []
                
                for item in raw_news:
                    published_str = item.get("published")
                    published_dt = None
                    if published_str:
                        try:
                            published_dt = datetime.fromisoformat(published_str.replace("Z", "+00:00"))
                        except (ValueError, TypeError):
                            published_dt = datetime.now(timezone.utc)
                    
                    if published_dt and published_dt < cutoff:
                        continue

                    news_item = News(
                        source=item.get("publisher", "yfinance"),
                        title=item.get("title", ""),
                        body=item.get("summary", ""),
                        url=item.get("link", ""),
                        published_at=published_dt.replace(tzinfo=None) if published_dt else None,
                        asset_id=asset.id,
                        language="en",
                    )
                    news_items.append(news_item)

                if news_items:
                    async with async_session_maker() as session:
                        # Batch upsert news (avoid duplicates by url)
                        for item in news_items:
                            if not item.url:
                                continue
                            existing = await session.execute(
                                select(News).where(News.url == item.url, News.asset_id == item.asset_id)
                            )
                            if not existing.scalar_one_or_none():
                                session.add(item)
                        await session.commit()
                return len(news_items)
        except Exception as e:
            self.logger.error(f"Failed to ingest news for {symbol}: {e}")
            return 0

    async def ingest_macro_indicators(self) -> bool:
        """Fetch macro indicators from yfinance macro tickers."""
        import yfinance as yf
        try:
            macro_data = []
            for ticker_sym, (name, unit) in MACRO_TICKERS.items():
                try:
                    async with self._semaphore:
                        ticker = yf.Ticker(ticker_sym)
                        hist = ticker.history(period="5d", interval="1d")
                        if hist.empty:
                            continue
                        latest = hist.iloc[-1]
                        latest_date = hist.index[-1]
                        period_str = latest_date.strftime("%Y-%m-%d")
                        value = float(latest["Close"])
                        
                        macro_data.append({
                            "indicator_code": ticker_sym,
                            "name": name,
                            "value": value,
                            "period": period_str,
                            "unit": unit,
                            "source": "yfinance",
                            "as_of": latest_date.date(),
                        })
                except Exception as e:
                    self.logger.warning(f"Failed to fetch macro {ticker_sym}: {e}")

            if macro_data:
                async with async_session_maker() as session:
                    for m in macro_data:
                        existing = await session.execute(
                            select(MacroIndicator).where(
                                MacroIndicator.indicator_code == m["indicator_code"],
                                MacroIndicator.period == m["period"],
                            )
                        )
                        if not existing.scalar_one_or_none():
                            macro = MacroIndicator(**m)
                            session.add(macro)
                    await session.commit()
            return True
        except Exception as e:
            self.logger.error(f"Failed to ingest macro indicators: {e}")
            return False

    async def backfill_nasdaq(self, symbols: Optional[List[str]] = None, years: int = 5):
        """Run full backfill for Nasdaq constituents."""
        symbols = symbols or self.DEFAULT_CONSTITUENTS
        self.logger.info(f"Starting Nasdaq backfill for {len(symbols)} symbols, {years} years")

        # Filter out symbols that already have sufficient history
        async with async_session_maker() as session:
            result = await session.execute(
                select(Asset.symbol, Asset.id)
                .where(Asset.symbol.in_(symbols))
                .where(Asset.active)
            )
            asset_map = {r[0]: r[1] for r in result.all()}

        symbols_with_data = set()
        for sym, asset_id in asset_map.items():
            async with async_session_maker() as session:
                count_result = await session.execute(
                    select(func.count(IntlPriceCandle.id))
                    .where(IntlPriceCandle.asset_id == asset_id)
                    .where(IntlPriceCandle.timeframe == "1d")
                )
                count = count_result.scalar_one_or_none() or 0
                if count > 1000:  # Already has ~4 years of data
                    symbols_with_data.add(sym)

        symbols_to_process = [s for s in symbols if s not in symbols_with_data]
        self.logger.info(f"Symbols with existing data: {len(symbols_with_data)}, to process: {len(symbols_to_process)}")

        # Ensure index asset exists
        await self._ensure_asset("^IXIC", "Nasdaq Composite", "INDEX")

        # Ingest macro first
        await self.ingest_macro_indicators()

        results = {"prices": 0, "fundamentals": 0, "board": 0, "news": 0, "errors": []}

        # Process in chunks to avoid memory issues
        chunk_size = 50
        for i in range(0, len(symbols_to_process), chunk_size):
            chunk = symbols_to_process[i:i + chunk_size]
            self.logger.info(f"Processing chunk {i // chunk_size + 1}/{(len(symbols_to_process) + chunk_size - 1) // chunk_size}: {chunk[0]}..{chunk[-1]}")

            # Concurrent price ingestion for chunk
            price_tasks = [self.ingest_price_history(sym, period=f"{years}y") for sym in chunk]
            price_results = await asyncio.gather(*price_tasks, return_exceptions=True)
            for r in price_results:
                if isinstance(r, int):
                    results["prices"] += r
                else:
                    results["errors"].append(str(r))

            # Concurrent fundamentals for chunk
            fund_tasks = [self.ingest_fundamentals(sym) for sym in chunk]
            fund_results = await asyncio.gather(*fund_tasks, return_exceptions=True)
            for r in fund_results:
                if isinstance(r, bool) and r:
                    results["fundamentals"] += 1
                elif isinstance(r, Exception):
                    results["errors"].append(str(r))

            # Board members
            board_tasks = [self.ingest_board_members(sym) for sym in chunk]
            board_results = await asyncio.gather(*board_tasks, return_exceptions=True)
            for r in board_results:
                if isinstance(r, int):
                    results["board"] += r
                elif isinstance(r, Exception):
                    results["errors"].append(str(r))

            # News for chunk
            news_tasks = [self.ingest_news_for_symbol(sym, days=7) for sym in chunk]
            news_results = await asyncio.gather(*news_tasks, return_exceptions=True)
            for r in news_results:
                if isinstance(r, int):
                    results["news"] += r
                elif isinstance(r, Exception):
                    results["errors"].append(str(r))

            # Small delay between chunks
            await asyncio.sleep(1)

        self.logger.info(f"Backfill complete: {results}")
        return results

    async def daily_update(self, symbols: Optional[List[str]] = None):
        """Run daily incremental update."""
        symbols = symbols or self.DEFAULT_CONSTITUENTS
        self.logger.info(f"Starting daily update for {len(symbols)} symbols")

        # Update macro
        await self.ingest_macro_indicators()

        results = {"prices": 0, "news": 0, "errors": []}

        chunk_size = 50
        for i in range(0, len(symbols), chunk_size):
            chunk = symbols[i:i + chunk_size]
            self.logger.info(f"Daily update chunk {i // chunk_size + 1}/{(len(symbols) + chunk_size - 1) // chunk_size}")

            # Price update: last 5 days
            price_tasks = [self.ingest_price_history(sym, period="5d") for sym in chunk]
            price_results = await asyncio.gather(*price_tasks, return_exceptions=True)
            for r in price_results:
                if isinstance(r, int):
                    results["prices"] += r
                else:
                    results["errors"].append(str(r))

            # News update: last 24 hours
            news_tasks = [self.ingest_news_for_symbol(sym, days=1) for sym in chunk]
            news_results = await asyncio.gather(*news_tasks, return_exceptions=True)
            for r in news_results:
                if isinstance(r, int):
                    results["news"] += r
                elif isinstance(r, Exception):
                    results["errors"].append(str(r))

            await asyncio.sleep(1)

        self.logger.info(f"Daily update complete: {results}")
        return results

    async def ingest_symbol_batch(self, symbols: List[str], include_news: bool = True,
                                  include_fundamentals: bool = False) -> Dict[str, Any]:
        """Ingest a batch of symbols with configurable data types."""
        results = {"prices": 0, "fundamentals": 0, "board": 0, "news": 0, "errors": []}

        chunk_size = 50
        for i in range(0, len(symbols), chunk_size):
            chunk = symbols[i:i + chunk_size]

            price_tasks = [self.ingest_price_history(sym, period="5d") for sym in chunk]
            price_results = await asyncio.gather(*price_tasks, return_exceptions=True)
            for r in price_results:
                if isinstance(r, int):
                    results["prices"] += r
                elif isinstance(r, Exception):
                    results["errors"].append(str(r))

            if include_fundamentals:
                fund_tasks = [self.ingest_fundamentals(sym) for sym in chunk]
                fund_results = await asyncio.gather(*fund_tasks, return_exceptions=True)
                for r in fund_results:
                    if isinstance(r, bool) and r:
                        results["fundamentals"] += 1
                    elif isinstance(r, Exception):
                        results["errors"].append(str(r))

                board_tasks = [self.ingest_board_members(sym) for sym in chunk]
                board_results = await asyncio.gather(*board_tasks, return_exceptions=True)
                for r in board_results:
                    if isinstance(r, int):
                        results["board"] += r
                    elif isinstance(r, Exception):
                        results["errors"].append(str(r))

            if include_news:
                news_tasks = [self.ingest_news_for_symbol(sym, days=1) for sym in chunk]
                news_results = await asyncio.gather(*news_tasks, return_exceptions=True)
                for r in news_results:
                    if isinstance(r, int):
                        results["news"] += r
                    elif isinstance(r, Exception):
                        results["errors"].append(str(r))

            await asyncio.sleep(1)

        return results
