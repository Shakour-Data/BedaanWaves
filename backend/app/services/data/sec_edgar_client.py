"""
SEC EDGAR API Integration for historical financial data.
Fetches quarterly (10-Q) and annual (10-K) financial statements for US companies.
"""
import asyncio
import json
import logging
import re
from datetime import datetime, date
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp
from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import get_settings
from app.db.base import async_session_maker
from app.models.models import Asset, IRFinancialStatement, IRFundamentalRatio
from app.services.core.base_service import DataService

logger = logging.getLogger(__name__)

SEC_BASE_URL = "https://data.sec.gov"
SEARCH_URL = "https://efts.sec.gov/LATEST/search-index"
COMPANY_FACTS_URL = f"{SEC_BASE_URL}/api/xbrl/companyfacts"
SUBMISSIONS_URL = f"{SEC_BASE_URL}/submissions"

SEC_HEADERS = {
    "User-Agent": "BedaanWaves-SEC-Client/1.0 (bedaanwaves@finance)",
    "Accept": "application/json",
}

CIK_CACHE_PATH = Path(__file__).parent.parent.parent.parent / "sec_cik_cache.json"
RATE_LIMIT_DELAY = 0.6


class SEDGARFinancialService(DataService):
    """Service for fetching historical financial data from SEC EDGAR."""

    def __init__(self):
        super().__init__("SEDGARFinancialService")
        self.settings = get_settings()
        self._cik_cache: Dict[str, str] = {}
        self._session: Optional[aiohttp.ClientSession] = None
        self._load_cik_cache()

    def _load_cik_cache(self) -> None:
        if CIK_CACHE_PATH.exists():
            try:
                self._cik_cache = json.loads(CIK_CACHE_PATH.read_text())
            except Exception:
                self._cik_cache = {}

    def _save_cik_cache(self) -> None:
        try:
            CIK_CACHE_PATH.write_text(json.dumps(self._cik_cache))
        except Exception:
            pass

    async def initialize(self) -> None:
        if not self._session:
            self._session = aiohttp.ClientSession(headers=SEC_HEADERS)

    async def shutdown(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    async def _rate_limit(self) -> None:
        await asyncio.sleep(RATE_LIMIT_DELAY)

    async def lookup_cik(self, symbol: str, company_name: str = "") -> Optional[str]:
        if symbol in self._cik_cache:
            return self._cik_cache[symbol]

        if not self._session:
            await self.initialize()

        queries = [symbol]
        if company_name:
            queries.append(company_name)

        for query in queries:
            await self._rate_limit()
            try:
                url = f"{SEARCH_URL}?q=%22{query}%22&forms=10-Q"
                async with self._session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status != 200:
                        continue
                    text = await resp.text()
                    data = json.loads(text)
                    hits = data.get("hits", {}).get("hits", [])
                    for hit in hits[:20]:
                        source = hit.get("_source", {})
                        display_names = source.get("display_names", [])
                        for display in display_names:
                            match = re.search(
                                rf'\(\s*[^)]*\b{re.escape(symbol)}\b[^)]*\)\s*\(CIK\s+(\d+)\)',
                                display,
                                re.IGNORECASE,
                            )
                            if match:
                                cik = match.group(1).zfill(10)
                                self._cik_cache[symbol] = cik
                                self._save_cik_cache()
                                return cik
            except Exception as exc:
                logger.debug(f"CIK lookup failed for {symbol} with query {query}: {exc}")
        return None

    async def fetch_company_facts(self, cik: str) -> Optional[Dict[str, Any]]:
        if not self._session:
            await self.initialize()
        await self._rate_limit()
        url = f"{COMPANY_FACTS_URL}/CIK{cik}.json"
        try:
            async with self._session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status != 200:
                    logger.warning(f"Company facts failed for CIK {cik}: {resp.status}")
                    return None
                return await resp.json()
        except Exception as exc:
            logger.error(f"Company facts error for CIK {cik}: {exc}")
            return None

    async def ingest_sec_financials(self, symbol: str, asset_id: str) -> Dict[str, int]:
        asset_uuid = asset_id if isinstance(asset_id, str) else str(asset_id)
        company_name = ""
        ticker = None

        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            info = ticker.info or {}
            company_name = info.get("longName", "")
        except Exception:
            pass

        cik = await self.lookup_cik(symbol, company_name)
        if not cik:
            logger.warning(f"No CIK found for {symbol}")
            return {"statements": 0, "ratios": 0, "errors": 1}

        facts_data = await self.fetch_company_facts(cik)
        if not facts_data:
            return {"statements": 0, "ratios": 0, "errors": 1}

        facts = facts_data.get("facts", {})
        us_gaap = facts.get("us-gaap", {})
        if not us_gaap:
            return {"statements": 0, "ratios": 0, "errors": 0}

        statements: List[IRFinancialStatement] = []
        ratios: List[IRFundamentalRatio] = []

        income_keys = [
            "Revenues",
            "RevenueFromContractWithCustomerExcludingAssessedTax",
            "SalesRevenueNet",
            "OperatingIncomeLoss",
            "NetIncomeLoss",
            "NetIncomeLossAvailableToCommonStockholdersDiluted",
            "EarningsPerShareDiluted",
            "EarningsPerShareBasic",
            "CostOfRevenue",
            "GrossProfit",
        ]
        balance_keys = [
            "Assets",
            "AssetsCurrent",
            "Liabilities",
            "LiabilitiesCurrent",
            "StockholdersEquity",
            "CashAndCashEquivalentsAtCarryingValue",
            "PropertyPlantAndEquipmentNet",
            "LongTermDebt",
            "LongTermDebtCurrent",
            "CommonStockSharesOutstanding",
            "CommonStockValue",
        ]
        cashflow_keys = [
            "NetCashProvidedByUsedInOperatingActivities",
            "NetCashProvidedByUsedInInvestingActivities",
            "NetCashProvidedByUsedInFinancingActivities",
            "PaymentsToAcquirePropertyPlantAndEquipment",
            "PaymentsOfDividends",
            "PaymentsForRepurchaseOfCommonStock",
        ]

        def _to_period(fp: str, fy: int, end: str) -> str:
            if fp and fp.startswith("Q"):
                quarter = fp[1]
                return f"{fy}Q{quarter}"
            if fp == "FY":
                return f"{fy}Annual"
            if end:
                try:
                    dt = datetime.strptime(end, "%Y-%m-%d")
                    quarter = (dt.month - 1) // 3 + 1
                    return f"{dt.year}Q{quarter}"
                except Exception:
                    pass
            return str(fy)

        def _extract_entries(fact_name: str, form_type: str):
            fact = us_gaap.get(fact_name)
            if not fact:
                return []
            units = fact.get("units", {})
            return [e for e in units.get("USD", []) if e.get("form") == form_type]

        for key in income_keys:
            for entry in _extract_entries(key, "10-Q"):
                period = _to_period(entry.get("fp", ""), entry.get("fy"), entry.get("end"))
                try:
                    as_of = datetime.strptime(entry["end"], "%Y-%m-%d").date()
                except Exception:
                    as_of = None
                statements.append(
                    IRFinancialStatement(
                        asset_id=asset_uuid,
                        market="NASDAQ",
                        period=period,
                        statement_type="INCOME",
                        fiscal_year=entry.get("fy"),
                        data={key: entry.get("val")},
                        as_of=as_of,
                    )
                )
            for entry in _extract_entries(key, "10-K"):
                period = _to_period("FY", entry.get("fy"), entry.get("end"))
                try:
                    as_of = datetime.strptime(entry["end"], "%Y-%m-%d").date()
                except Exception:
                    as_of = None
                statements.append(
                    IRFinancialStatement(
                        asset_id=asset_uuid,
                        market="NASDAQ",
                        period=period,
                        statement_type="INCOME",
                        fiscal_year=entry.get("fy"),
                        data={key: entry.get("val")},
                        as_of=as_of,
                    )
                )

        for key in balance_keys:
            for entry in _extract_entries(key, "10-Q"):
                period = _to_period(entry.get("fp", ""), entry.get("fy"), entry.get("end"))
                try:
                    as_of = datetime.strptime(entry["end"], "%Y-%m-%d").date()
                except Exception:
                    as_of = None
                statements.append(
                    IRFinancialStatement(
                        asset_id=asset_uuid,
                        market="NASDAQ",
                        period=period,
                        statement_type="BALANCE_SHEET",
                        fiscal_year=entry.get("fy"),
                        data={key: entry.get("val")},
                        as_of=as_of,
                    )
                )
            for entry in _extract_entries(key, "10-K"):
                period = _to_period("FY", entry.get("fy"), entry.get("end"))
                try:
                    as_of = datetime.strptime(entry["end"], "%Y-%m-%d").date()
                except Exception:
                    as_of = None
                statements.append(
                    IRFinancialStatement(
                        asset_id=asset_uuid,
                        market="NASDAQ",
                        period=period,
                        statement_type="BALANCE_SHEET",
                        fiscal_year=entry.get("fy"),
                        data={key: entry.get("val")},
                        as_of=as_of,
                    )
                )

        for key in cashflow_keys:
            for entry in _extract_entries(key, "10-Q"):
                period = _to_period(entry.get("fp", ""), entry.get("fy"), entry.get("end"))
                try:
                    as_of = datetime.strptime(entry["end"], "%Y-%m-%d").date()
                except Exception:
                    as_of = None
                statements.append(
                    IRFinancialStatement(
                        asset_id=asset_uuid,
                        market="NASDAQ",
                        period=period,
                        statement_type="CASH_FLOW",
                        fiscal_year=entry.get("fy"),
                        data={key: entry.get("val")},
                        as_of=as_of,
                    )
                )
            for entry in _extract_entries(key, "10-K"):
                period = _to_period("FY", entry.get("fy"), entry.get("end"))
                try:
                    as_of = datetime.strptime(entry["end"], "%Y-%m-%d").date()
                except Exception:
                    as_of = None
                statements.append(
                    IRFinancialStatement(
                        asset_id=asset_uuid,
                        market="NASDAQ",
                        period=period,
                        statement_type="CASH_FLOW",
                        fiscal_year=entry.get("fy"),
                        data={key: entry.get("val")},
                        as_of=as_of,
                    )
                )

        if statements:
            async with async_session_maker() as session:
                for stmt in statements:
                    stmt_data = {
                        "asset_id": asset_uuid,
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
                await session.commit()

        eps_entry = next(iter(_extract_entries("EarningsPerShareDiluted", "10-Q")), None)
        if eps_entry:
            period = _to_period(eps_entry.get("fp", ""), eps_entry.get("fy"), eps_entry.get("end"))
            try:
                as_of = datetime.strptime(eps_entry["end"], "%Y-%m-%d").date()
            except Exception:
                as_of = None
            ratios.append(
                IRFundamentalRatio(
                    asset_id=asset_uuid,
                    market="NASDAQ",
                    period=period,
                    eps=eps_entry.get("val"),
                    as_of=as_of,
                )
            )

        if ratios:
            async with async_session_maker() as session:
                for ratio in ratios:
                    ratio_data = {
                        "asset_id": asset_uuid,
                        "market": ratio.market,
                        "period": ratio.period,
                        "eps": ratio.eps,
                        "as_of": ratio.as_of,
                    }
                    upsert = pg_insert(IRFundamentalRatio).values(ratio_data)
                    upsert = upsert.on_conflict_do_update(
                        index_elements=["asset_id", "period", "market"],
                        set_={"eps": upsert.excluded.eps, "as_of": upsert.excluded.as_of},
                    )
                    await session.execute(upsert)
                await session.commit()

        return {"statements": len(statements), "ratios": len(ratios), "errors": 0}
