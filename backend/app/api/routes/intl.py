"""International Stock Market Data Routes"""

import logging
from typing import Any, Dict, List, Optional

import yfinance as yf
from fastapi import APIRouter, Depends, Query, HTTPException

from app.services.data.nasdaq_ingestion_service import NasdaqIngestionService
from app.services.data.intl_api_client import IntlApiClient

logger = logging.getLogger(__name__)
router = APIRouter(tags=["intl"])


@router.get("/quote/{symbol}", response_model=dict)
async def get_intl_quote(symbol: str):
    """Get real-time quote for an international stock."""
    nasdaq_service = NasdaqIngestionService()
    await nasdaq_service.initialize()
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        if not info or not info.get("regularMarketPrice"):
            raise HTTPException(status_code=404, detail=f"No data found for {symbol}")
        return {
            "status": "success",
            "symbol": symbol,
            "data": {
                "price": info.get("regularMarketPrice"),
                "change": info.get("regularMarketChange"),
                "change_percent": info.get("regularMarketChangePercent"),
                "volume": info.get("regularMarketVolume"),
                "market_cap": info.get("marketCap"),
                "pe_ratio": info.get("trailingPE"),
                "name": info.get("longName", symbol),
            },
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    finally:
        await nasdaq_service.shutdown()


@router.get("/history/{symbol}", response_model=dict)
async def get_intl_history(symbol: str, interval: str = Query("1d"), days: int = Query(365, ge=1, le=3650)):
    """Get historical data for an international stock."""
    nasdaq_service = NasdaqIngestionService()
    await nasdaq_service.initialize()
    try:
        asset = await nasdaq_service._ensure_asset(symbol, symbol)
        from app.db.base import async_session_maker
        from sqlalchemy import select, desc
        from app.models.models import IntlPriceCandle
        
        async with async_session_maker() as session:
            result = await session.execute(
                select(IntlPriceCandle)
                .where(IntlPriceCandle.asset_id == asset.id)
                .where(IntlPriceCandle.timeframe == interval)
                .order_by(desc(IntlPriceCandle.timestamp))
                .limit(days)
            )
            candles = result.scalars().all()
            data = [
                {
                    "timestamp": c.timestamp.isoformat(),
                    "open": float(c.open),
                    "high": float(c.high),
                    "low": float(c.low),
                    "close": float(c.close),
                    "volume": int(c.volume),
                }
                for c in reversed(candles)
            ]
            return {"status": "success", "symbol": symbol, "count": len(data), "data": data}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    finally:
        await nasdaq_service.shutdown()


@router.get("/search", response_model=dict)
async def search_intl(query: str = Query(..., min_length=1)):
    """Search international stock symbols."""
    nasdaq_service = NasdaqIngestionService()
    await nasdaq_service.initialize()
    try:
        symbols = [s for s in nasdaq_service.DEFAULT_CONSTITUENTS if query.upper() in s]
        if len(symbols) > 50:
            symbols = symbols[:50]
        return {
            "status": "success",
            "query": query,
            "count": len(symbols),
            "data": [{"symbol": s} for s in symbols],
        }
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    finally:
        await nasdaq_service.shutdown()
