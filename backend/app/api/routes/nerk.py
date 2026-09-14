"""Nasdaq Index ("Neark") API Routes.

The feature keeps its historical ``nerk`` URL namespace, but everything it
exposes describes the **Nasdaq** listing universe: USD prices, daily bars from
``intl_price_candles``, ``America/New_York`` trading timezone.

Endpoints
---------
- ``GET /nerk/constituents``           every tracked Nasdaq instrument with its
                                       latest close and 1-day change.
- ``GET /nerk/overview``               market roll-up plus top gainers/losers.
- ``GET /nerk/price-history/{symbol}`` daily OHLCV history for one symbol.
- ``GET /nerk/market-overview``        the roll-up on its own.

Implementation notes
--------------------
The previous version of this module delegated to ``NerkIngestionService``, a
service carried over from an earlier Tehran Stock Exchange product. That
service reported ``currency='IRR'``, ``timezone='Asia/Tehran'`` and
``exchange='Tehran Stock Exchange'`` for Nasdaq data, and it filtered on
``Asset.is_nerk_constituent`` — a column no migration ever populated — so the
price-history endpoint 404'd for every symbol. This module queries the
database directly instead, so the numbers on the page are the numbers in the
tables.

The two aggregate endpoints are served from a short TTL cache: pairing several
thousand symbols with their latest bars is not work to repeat per request.
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db.base import async_session_maker
from app.schemas.schemas import (
    NearkConstituentResponse,
    NearkConstituentsResponse,
    NearkMarketOverviewResponse,
    NearkMover,
    NearkOverviewResponse,
    NearkPriceHistoryResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["nerk"])

INDEX_NAME = "Nasdaq Composite"
EXCHANGE = "NASDAQ"
CURRENCY = "USD"
TIMEZONE = "America/New_York"

# How far back to look when pairing each symbol with its two most recent daily
# bars. Ten calendar days comfortably covers a long weekend plus a market
# holiday while keeping the window small enough to stay index-friendly.
RECENT_WINDOW_DAYS = 10

# Constituents / overview are aggregate reads over millions of candle rows.
# Prices only move once per trading day, so a five minute TTL costs nothing in
# freshness and keeps the page responsive.
CACHE_TTL_SECONDS = 300

PERIOD_DAYS = {
    "1m": 30,
    "3m": 90,
    "6m": 180,
    "1y": 365,
    "2y": 730,
    "5y": 1825,
}

_constituents_cache: Dict[str, Any] = {"value": None, "expires_at": 0.0}


def _now_iso() -> str:
    """Current UTC time as an ISO-8601 string."""
    return datetime.now(UTC).isoformat()


def _naive_utc_cutoff(days: int) -> datetime:
    """A naive UTC cutoff — ``intl_price_candles.timestamp`` has no timezone."""
    return datetime.now(UTC).replace(tzinfo=None) - timedelta(days=days)


async def _fetch_constituents() -> List[Dict[str, Any]]:
    """Return every active Nasdaq instrument with its latest close and change.

    One window-function query pairs each asset with its two most recent daily
    bars. The change percentage is derived in Python so that symbols with only
    a single bar still appear (at zero change) rather than disappearing.
    """
    cutoff = _naive_utc_cutoff(RECENT_WINDOW_DAYS)

    query = text(
        """
        WITH recent AS (
            SELECT c.asset_id,
                   c.close,
                   c.timestamp,
                   row_number() OVER (
                       PARTITION BY c.asset_id
                       ORDER BY c.timestamp DESC
                   ) AS rn
            FROM intl_price_candles c
            WHERE c.timeframe = '1d'
              AND c.timestamp >= :cutoff
        )
        SELECT a.id,
               a.symbol,
               a.name,
               a.sector,
               a.asset_class,
               a.market,
               a.active,
               a.nerk_weight,
               a.is_nerk_constituent,
               last.close     AS price,
               prev.close     AS prev_close,
               last.timestamp AS last_ts
        FROM assets a
        LEFT JOIN recent last ON last.asset_id = a.id AND last.rn = 1
        LEFT JOIN recent prev ON prev.asset_id = a.id AND prev.rn = 2
        WHERE a.market = 'NASDAQ'
          AND a.active IS TRUE
        ORDER BY a.symbol
        """
    )

    async with async_session_maker() as session:
        rows = (await session.execute(query, {"cutoff": cutoff})).mappings().all()

    constituents: List[Dict[str, Any]] = []
    for row in rows:
        price = float(row["price"]) if row["price"] is not None else 0.0
        prev_close = float(row["prev_close"]) if row["prev_close"] is not None else None

        if prev_close and prev_close > 0 and price > 0:
            change_pct = round((price - prev_close) / prev_close * 100.0, 2)
        else:
            change_pct = 0.0

        constituents.append(
            {
                "id": row["id"],
                "symbol": row["symbol"],
                "name": row["name"],
                "sector": row["sector"],
                "asset_class": row["asset_class"],
                "market": row["market"],
                "active": bool(row["active"]),
                "price": price,
                "change_pct": change_pct,
                "nerk_weight": row["nerk_weight"],
                "last_trade": row["last_ts"].isoformat() if row["last_ts"] else None,
            }
        )

    return constituents


async def _get_constituents_cached() -> List[Dict[str, Any]]:
    """Serve the constituent list from a short-lived in-process cache."""
    now = datetime.now(UTC).timestamp()
    cached = _constituents_cache["value"]
    if cached is not None and _constituents_cache["expires_at"] > now:
        return cached

    constituents = await _fetch_constituents()
    _constituents_cache["value"] = constituents
    _constituents_cache["expires_at"] = now + CACHE_TTL_SECONDS
    return constituents


def _build_market_overview(constituents: List[Dict[str, Any]]) -> NearkMarketOverviewResponse:
    """Roll the constituent list up into market-wide statistics."""
    priced = [c for c in constituents if c["price"] > 0]
    changes = [c["change_pct"] for c in priced]
    gainers = [c for c in priced if c["change_pct"] > 0]
    losers = [c for c in priced if c["change_pct"] < 0]

    last_trade = max(
        (c["last_trade"] for c in constituents if c.get("last_trade")),
        default=None,
    )

    return NearkMarketOverviewResponse(
        market="NASDAQ",
        total_symbols=len(constituents),
        active_symbols=len(priced),
        currency=CURRENCY,
        timezone=TIMEZONE,
        index=INDEX_NAME,
        last_updated=last_trade or _now_iso(),
        constituents_count=len(constituents),
        avg_change_pct=round(sum(changes) / len(changes), 2) if changes else 0.0,
        gainers_count=len(gainers),
        losers_count=len(losers),
    )


@router.get("/constituents", response_model=NearkConstituentsResponse)
async def get_nerk_constituents() -> NearkConstituentsResponse:
    """List every tracked Nasdaq instrument with its latest price and change."""
    try:
        constituents = await _get_constituents_cached()
        return NearkConstituentsResponse(
            status="ok",
            index=INDEX_NAME,
            exchange=EXCHANGE,
            currency=CURRENCY,
            count=len(constituents),
            data=[NearkConstituentResponse(**c) for c in constituents],
            timestamp=_now_iso(),
        )
    except SQLAlchemyError as exc:
        logger.error("Database error fetching Nasdaq constituents: %s", exc)
        raise HTTPException(status_code=500, detail="Database error") from exc
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Error fetching Nasdaq constituents: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/overview", response_model=NearkOverviewResponse)
async def get_nerk_overview(
    limit: int = Query(10, ge=1, le=100, description="Number of movers per side"),
) -> NearkOverviewResponse:
    """Return the market roll-up plus the top gainers and top losers."""
    try:
        constituents = await _get_constituents_cached()
        priced = [c for c in constituents if c["price"] > 0]

        ranked_desc = sorted(priced, key=lambda c: c["change_pct"], reverse=True)
        ranked_asc = sorted(priced, key=lambda c: c["change_pct"])

        def to_mover(item: Dict[str, Any]) -> NearkMover:
            return NearkMover(
                symbol=item["symbol"],
                name=item["name"],
                price=item["price"],
                change_pct=item["change_pct"],
            )

        market_overview = _build_market_overview(constituents)

        return NearkOverviewResponse(
            status="ok",
            index=INDEX_NAME,
            exchange=EXCHANGE,
            market_overview=market_overview,
            constituents_count=len(constituents),
            top_gainers=[to_mover(c) for c in ranked_desc[:limit]],
            top_losers=[to_mover(c) for c in ranked_asc[:limit]],
            avg_change_pct=market_overview.avg_change_pct,
            timestamp=_now_iso(),
        )
    except SQLAlchemyError as exc:
        logger.error("Database error fetching Nasdaq overview: %s", exc)
        raise HTTPException(status_code=500, detail="Database error") from exc
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Error fetching Nasdaq overview: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/market-overview", response_model=NearkMarketOverviewResponse)
async def get_nerk_market_overview() -> NearkMarketOverviewResponse:
    """Return the market-wide roll-up on its own."""
    try:
        constituents = await _get_constituents_cached()
        return _build_market_overview(constituents)
    except SQLAlchemyError as exc:
        logger.error("Database error fetching Nasdaq market overview: %s", exc)
        raise HTTPException(status_code=500, detail="Database error") from exc
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Error fetching Nasdaq market overview: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/price-history/{symbol}", response_model=NearkPriceHistoryResponse)
async def get_nerk_price_history(
    symbol: str,
    period: str = Query("1y", description="One of 1m, 3m, 6m, 1y, 2y, 5y"),
) -> NearkPriceHistoryResponse:
    """Return daily OHLCV history for one Nasdaq symbol."""
    days = PERIOD_DAYS.get(period)
    if days is None:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported period '{period}'. "
                f"Use one of: {', '.join(sorted(PERIOD_DAYS))}"
            ),
        )

    normalized = symbol.strip().upper()
    cutoff = _naive_utc_cutoff(days)

    try:
        async with async_session_maker() as session:
            asset_row = (
                await session.execute(
                    text("SELECT id, symbol, name, market FROM assets WHERE upper(symbol) = :symbol"),
                    {"symbol": normalized},
                )
            ).mappings().first()

            if not asset_row:
                raise HTTPException(status_code=404, detail=f"Symbol {normalized} not found")

            candles = (
                await session.execute(
                    text(
                        """
                        SELECT timestamp, open, high, low, close, volume,
                               turnover, adjusted_close
                        FROM intl_price_candles
                        WHERE asset_id = :asset_id
                          AND timeframe = '1d'
                          AND timestamp >= :cutoff
                        ORDER BY timestamp ASC
                        """
                    ),
                    {"asset_id": asset_row["id"], "cutoff": cutoff},
                )
            ).mappings().all()

        data = [
            {
                "timestamp": c["timestamp"].isoformat(),
                "open": float(c["open"]),
                "high": float(c["high"]),
                "low": float(c["low"]),
                "close": float(c["close"]),
                "volume": int(c["volume"]) if c["volume"] is not None else 0,
                "turnover": float(c["turnover"]) if c["turnover"] is not None else None,
                "adjusted_close": (
                    float(c["adjusted_close"]) if c["adjusted_close"] is not None else None
                ),
            }
            for c in candles
        ]

        return NearkPriceHistoryResponse(
            status="ok",
            symbol=asset_row["symbol"],
            name=asset_row["name"],
            market=asset_row["market"] or "NASDAQ",
            period=period,
            count=len(data),
            data=data,
            timestamp=_now_iso(),
        )
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        logger.error("Database error fetching price history for %s: %s", normalized, exc)
        raise HTTPException(status_code=500, detail="Database error") from exc
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Error fetching price history for %s: %s", normalized, exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
