"""
Nasdaq Ingestion Service - Fetches Nasdaq Composite index and constituent data.

Data sources:
- Price history: yfinance (Yahoo Finance)
- Fundamentals: yfinance
- Board/Officers: yfinance companyOfficers + SEC EDGAR
- Macro: Static seed data + Alpha Vantage (optional)
"""

import asyncio
import logging
import math
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import yfinance as yf
from sqlalchemy import select, insert
from sqlalchemy.exc import IntegrityError

from app.services.core.base_service import DataService
from app.core.config import get_settings
from app.models.models import (
    Asset,
    IntlPriceCandle,
    IRFinancialStatement,
    IRFundamentalRatio,
    CompanyLeadership,
    News,
    NewsSentiment,
    MacroIndicator,
    MLSignal,
    MLModel,
)
from app.db.base import async_session_maker

logger = logging.getLogger(__name__)


class NasdaqIngestionService(DataService):
    """Service for ingesting Nasdaq Composite index and constituent data."""

    def __init__(self, service_name: str = "NasdaqIngestionService"):
        super().__init__(service_name)
        self.settings = get_settings()

        # Top 100 Nasdaq constituents by market cap (seed list)
        self.DEFAULT_CONSTITUENTS = [
            "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AVGO", "COST", "NFLX",
            "PLTR", "ASML", "TMUS", "CSCO", "ADBE", "CMCSA", "PEP", "INTC", "INTU", "TXN",
            "QCOM", "AMD", "AMAT", "BKNG", "GILD", "LRCX", "ADI", "VRTX", "ISRG", "REGN",
            "PANW", "KLAC", "MELI", "SNPS", "CDNS", "WDAY", "CRWD", "DXCM", "PYPL", "FTNT",
            "MAR", "ORLY", "CPRT", "ROST", "PAYX", "ADSK", "CHTR", "DASH", "NXPI", "AZN",
            "TEAM", "MRVL", "ABNB", "DDOG", "IDXX", "MCHP", "LULU", "ZS", "EXC", "FAST",
            "CTAS", "EA", "CTSH", "WBD", "ODFL", "BIIB", "KDP", "ON", "GFS", "CRWD",
            "TTWO", "ROKU", "UPST", "SMCI", "ARM", "HOOD", "C", "WFC", "JPM", "BAC",
            "GS", "MS", "SCHW", "BLK", "SPGI", "ICE", "CME", "AON", "MMC", "PGR",
            "TFC", "USB", "PNC", "BK", "STT", "COF", "AXP", "DFS", "SYF", "ALLY",
        ]

    @staticmethod
    def _clean_nan(obj):
        """Replace NaN/Inf values with None for JSON serialization."""
        if isinstance(obj, float):
            if math.isnan(obj) or math.isinf(obj):
                return None
            return obj
        elif isinstance(obj, dict):
            return {k: NasdaqIngestionService._clean_nan(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [NasdaqIngestionService._clean_nan(v) for v in obj]
        return obj

    async def initialize(self) -> None:
        self.logger.info("NasdaqIngestionService initialized")

    async def shutdown(self) -> None:
        self.logger.info("NasdaqIngestionService shutdown")

    async def _ensure_asset(self, symbol: str, name: str, asset_class: str, market: str = "NASDAQ",
                            sector: str = "", industry: str = "") -> Asset:
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

    async def ingest_price_history(self, symbol: str, period: str = "5y") -> int:
        """Fetch and store price history for a symbol."""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period, interval="1d", auto_adjust=True)
            if hist.empty:
                return 0

            asset = await self._ensure_asset(symbol, ticker.info.get("longName", symbol), "EQUITY")
            count = 0

            async with async_session_maker() as session:
                for timestamp, row in hist.iterrows():
                    ts = timestamp.to_pydatetime().replace(tzinfo=None) if hasattr(timestamp, 'to_pydatetime') else timestamp
                    candle = IntlPriceCandle(
                        asset_id=asset.id,
                        timestamp=ts,
                        timeframe="1d",
                        open=float(row["Open"]),
                        high=float(row["High"]),
                        low=float(row["Low"]),
                        close=float(row["Close"]),
                        volume=int(row["Volume"]),
                        turnover=float(row["Volume"]) * float(row["Close"]),
                        source="yfinance",
                        data_quality="CONFIRMED",
                    )
                    session.add(candle)
                    count += 1
                    await session.commit()
                return count
        except Exception as e:
            self.logger.error(f"Failed to ingest prices for {symbol}: {e}")
            return 0

    async def ingest_fundamentals(self, symbol: str) -> bool:
        """Fetch and store fundamental data for a symbol."""
        try:
            ticker = yf.Ticker(symbol)
            asset = await self._ensure_asset(symbol, ticker.info.get("longName", symbol), "EQUITY")

            # Get quarterly financials
            income_stmt = ticker.quarterly_financials
            balance_sheet = ticker.quarterly_balance_sheet
            cashflow = ticker.quarterly_cashflow

            async with async_session_maker() as session:
                if not income_stmt.empty:
                    for period_end in income_stmt.columns:
                        quarter = (period_end.month - 1) // 3 + 1
                        period_str = f"{period_end.year}Q{quarter}"
                        fiscal_year = period_end.year

                        stmt = IRFinancialStatement(
                            asset_id=asset.id,
                            market="NASDAQ",
                            period=period_str,
                            statement_type="INCOME",
                            fiscal_year=fiscal_year,
                            data=self._clean_nan(income_stmt[period_end].to_dict()),
                            as_of=period_end.date() if hasattr(period_end, "date") else None,
                        )
                        session.add(stmt)

                        info = ticker.info or {}
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
                            as_of=period_end.date() if hasattr(period_end, "date") else None,
                        )
                        session.add(ratio)

                await session.commit()
            return True
        except Exception as e:
            self.logger.error(f"Failed to ingest fundamentals for {symbol}: {e}")
            return False

    async def ingest_board_members(self, symbol: str) -> int:
        """Fetch board members and officers from yfinance."""
        try:
            ticker = yf.Ticker(symbol)
            asset = await self._ensure_asset(symbol, ticker.info.get("longName", symbol), "EQUITY")
            info = ticker.info or {}
            officers = info.get("companyOfficers", [])
            count = 0

            async with async_session_maker() as session:
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

                    leadership = CompanyLeadership(
                        asset_id=asset.id,
                        name=name,
                        title=title,
                        leadership_type="officer",
                        start_date=start_date,
                        source="yfinance",
                    )
                    session.add(leadership)
                    count += 1

                await session.commit()
            return count
        except Exception as e:
            self.logger.error(f"Failed to ingest board for {symbol}: {e}")
            return 0

    async def ingest_macro_indicators(self) -> bool:
        """Insert sample macro indicators."""
        try:
            sample_macro = [
                ("GDP", "Gross Domestic Product", 27835.0, "2026Q2", "USD Billions", "FRED", "2026-07-30"),
                ("UNRATE", "Unemployment Rate", 4.1, "2026-07", "Percent", "FRED", "2026-08-01"),
                ("CPIAUCSL", "Consumer Price Index", 313.5, "2026-07", "Index 1982-84=100", "FRED", "2026-08-01"),
                ("FEDFUNDS", "Federal Funds Rate", 5.33, "2026-07", "Percent", "FRED", "2026-08-01"),
                ("DEXUSEU", "USD/EUR Exchange Rate", 0.92, "2026-07", "USD per EUR", "FRED", "2026-08-01"),
            ]
            async with async_session_maker() as session:
                for code, name, value, period, unit, source, as_of in sample_macro:
                    result = await session.execute(
                        select(MacroIndicator).where(
                            MacroIndicator.indicator_code == code,
                            MacroIndicator.period == period,
                        )
                    )
                    existing = result.scalar_one_or_none()
                    if not existing:
                        macro = MacroIndicator(
                            indicator_code=code,
                            name=name,
                            value=value,
                            period=period,
                            unit=unit,
                            source=source,
                            as_of=datetime.strptime(as_of, "%Y-%m-%d").date(),
                        )
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

        # Ensure index asset exists
        await self._ensure_asset("^IXIC", "Nasdaq Composite", "INDEX")

        # Ingest macro first
        await self.ingest_macro_indicators()

        results = {"prices": 0, "fundamentals": 0, "board": 0, "errors": []}

        for i, symbol in enumerate(symbols, 1):
            self.logger.info(f"[{i}/{len(symbols)}] Processing {symbol}")

            prices = await self.ingest_price_history(symbol, period=f"{years}y")
            results["prices"] += prices

            fundamentals = await self.ingest_fundamentals(symbol)
            results["fundamentals"] += 1 if fundamentals else 0

            board = await self.ingest_board_members(symbol)
            results["board"] += board

            # Small delay to avoid rate limiting
            await asyncio.sleep(0.5)

        self.logger.info(f"Backfill complete: {results}")
        return results

    async def daily_update(self, symbols: Optional[List[str]] = None):
        """Run daily incremental update."""
        symbols = symbols or self.DEFAULT_CONSTITUENTS
        for symbol in symbols:
            await self.ingest_price_history(symbol, period="5d")
            await asyncio.sleep(0.2)

