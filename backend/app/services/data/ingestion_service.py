"""
TSE Ingestion Service - feeds PostgreSQL from BrsApi.ir (Tehran Stock Exchange).

IMPORTANT (per project requirement): Tehran Stock Exchange (TSE) data is
kept strictly separate from international exchanges and cryptocurrencies.
Every row written here is tagged with market='TSE'. The analysis built on top
of this data is also TSE-specific (Persian market conventions, IRR pricing,
Jalali calendar). Do NOT mix crypto/international feeds into these tables.

Field mappings follow docs/BourseApi.txt exactly:
  AllSymbols -> assets   (l18=symbol, l30=name, isin=isin_code)
  History    -> price_candles (pf=open, pc=close, pmin/pmax, tvol/tval/tno)
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, time

import jdatetime
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from ..core import DataService
from app.db.base import AsyncSession
from app.models.models import Asset, PriceCandle

# Tehran market close time used for daily candle timestamps.
_MARKET_CLOSE = time(12, 30)


def _jalali_to_gregorian(jalali_date: str) -> Optional[datetime]:
    """Convert a Jalali 'YYYY-MM-DD' string to a Gregorian datetime (market close)."""
    if not jalali_date:
        return None
    try:
        y, m, d = (int(x) for x in jalali_date.split("-"))
        g = jdatetime.date(y, m, d).togregorian()
        return datetime(g.year, g.month, g.day, _MARKET_CLOSE.hour, _MARKET_CLOSE.minute)
    except Exception:
        return None


class TSEIngestionService(DataService):
    """
    Ingests Tehran Stock Exchange market data from brsapi.ir into PostgreSQL.

    Designed for TSE only. Use separate services for crypto / international.
    """

    def __init__(self, service_name: str = "TSEIngestionService", brs_client=None):
        super().__init__(service_name)
        self.brs_client = brs_client

    async def initialize(self) -> None:
        self.logger.info("TSEIngestionService initialized (market=TSE)")

    async def shutdown(self) -> None:
        self.logger.info("TSEIngestionService shutdown")

    # ------------------------------------------------------------------ #
    # Symbols
    # ------------------------------------------------------------------ #
    @staticmethod
    def _asset_row(item: Dict[str, Any]) -> Dict[str, Any]:
        """Map one AllSymbols record to an assets table row (TSE)."""
        # Industry group: prefer an explicit field, fall back to group code name.
        industry = (
            item.get("industry")
            or item.get("cg_name")
            or item.get("group_name")
        )
        return {
            "symbol": item.get("l18"),
            "name": item.get("l30") or item.get("l18"),
            "isin_code": item.get("isin"),
            "market": "TSE",
            "asset_class": "ETF" if "ای تی اف" in str(item.get("cg", "")).lower() else "EQUITY",
            "currency": "IRR",
            "active": True,
            "industry": industry,
            "meta": item,
        }

    async def upsert_symbols(
        self, session: AsyncSession, records: List[Dict[str, Any]]
    ) -> int:
        """Upsert TSE symbols into assets (ON CONFLICT DO UPDATE by symbol)."""
        rows = [self._asset_row(r) for r in records if r.get("l18")]
        if not rows:
            return 0
        stmt = pg_insert(Asset).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=["symbol"],
            set_={
                "name": stmt.excluded.name,
                "isin_code": stmt.excluded.isin_code,
                "market": stmt.excluded.market,
                "asset_class": stmt.excluded.asset_class,
                "currency": stmt.excluded.currency,
                "active": stmt.excluded.active,
                "industry": stmt.excluded.industry,
                "meta": stmt.excluded.meta,
                "updated_at": datetime.utcnow(),
            },
        )
        await session.execute(stmt)
        await session.commit()
        self.logger.info(f"Upserted {len(rows)} TSE symbols")
        return len(rows)

    async def ingest_symbols(
        self, session: AsyncSession, market_type: int = 1, limit: Optional[int] = None
    ) -> int:
        """Fetch AllSymbols from BRS and store them (TSE)."""
        if not self.brs_client:
            raise RuntimeError("BRS client not initialized")
        records = await self.brs_client.get_all_symbols(market_type=market_type)
        if limit:
            records = records[:limit]
        return await self.upsert_symbols(session, records)

    # ------------------------------------------------------------------ #
    # History / candles
    # ------------------------------------------------------------------ #
    async def _resolve_asset_id(self, session: AsyncSession, symbol: str) -> Optional[str]:
        result = await session.execute(select(Asset.id).where(Asset.symbol == symbol))
        return result.scalar_first()

    async def upsert_candles(
        self, session: AsyncSession, asset_id: str, candles: List[Dict[str, Any]]
    ) -> int:
        """Upsert daily candles for one TSE symbol into price_candles."""
        rows = []
        for c in candles:
            ts = _jalali_to_gregorian(c.get("date"))
            if not ts:
                continue
            rows.append(
                {
                    "asset_id": asset_id,
                    "timestamp": ts,
                    "timeframe": "1d",
                    "open": float(c.get("pf") or 0),
                    "high": float(c.get("pmax") or c.get("pf") or 0),
                    "low": float(c.get("pmin") or c.get("pf") or 0),
                    "close": float(c.get("pc") or 0),
                    "volume": int(c.get("tvol") or 0),
                    "turnover": float(c.get("tval") or 0),
                    "transactions": int(c.get("tno") or 0),
                    "source": "BRS",
                    "data_quality": "CONFIRMED",
                }
            )
        if not rows:
            return 0
        stmt = pg_insert(PriceCandle).values(rows)
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
            },
        )
        await session.execute(stmt)
        await session.commit()
        return len(rows)

    async def ingest_history(
        self, session: AsyncSession, symbol: str, days: int = 365
    ) -> int:
        """Fetch History for one symbol from BRS and store candles (TSE)."""
        if not self.brs_client:
            raise RuntimeError("BRS client not initialized")
        asset_id = await self._resolve_asset_id(session, symbol)
        if not asset_id:
            self.logger.warning(f"Symbol {symbol} not found in assets; skipping history")
            return 0
        candles = await self.brs_client.get_history(l18=symbol)
        if days:
            candles = candles[-days:]
        return await self.upsert_candles(session, asset_id, candles)

    async def ingest_all(
        self,
        session: AsyncSession,
        market_type: int = 1,
        symbols_limit: Optional[int] = None,
        history_per_symbol: bool = True,
        history_days: int = 365,
    ) -> Dict[str, int]:
        """Ingest all TSE symbols and (optionally) their history."""
        n_symbols = await self.ingest_symbols(session, market_type, limit=symbols_limit)
        n_candles = 0
        if history_per_symbol:
            result = await session.execute(select(Asset.symbol).where(Asset.market == "TSE"))
            symbols = result.scalars().all()
            for sym in symbols:
                n_candles += await self.ingest_history(session, sym, days=history_days)
        self.logger.info(f"TSE ingest complete: {n_symbols} symbols, {n_candles} candles")
        return {"symbols": n_symbols, "candles": n_candles}
