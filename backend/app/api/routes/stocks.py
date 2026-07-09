"""Stock Data Routes"""

from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List
import logging

from app.services.data.stock_service import StockService
from app.services.data.brs_api_client import BrsApiClient
from app.api.routes.live import get_brs_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/stocks", tags=["stocks"])


@router.get("/{ticker}", response_model=dict)
async def get_stock(
    ticker: str,
    client: BrsApiClient = Depends(get_brs_client),
) -> dict:
    """Get stock information by ticker."""
    service = StockService(brs_client=client)
    await service.initialize()
    data = await service.get_stock(ticker)
    return {
        "status": "success",
        "ticker": ticker.upper(),
        "data": data,
    }


@router.get("/search", response_model=dict)
async def search_stocks(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    client: BrsApiClient = Depends(get_brs_client),
) -> dict:
    """Search stocks by query."""
    service = StockService(brs_client=client)
    await service.initialize()
    results = await service.search(q)
    return {
        "status": "success",
        "query": q,
        "count": len(results),
        "data": results[:limit],
    }


@router.post("/batch", response_model=dict)
async def get_multiple_stocks(
    tickers: List[str],
    client: BrsApiClient = Depends(get_brs_client),
) -> dict:
    """Get multiple stocks by tickers."""
    service = StockService(brs_client=client)
    await service.initialize()
    results = await service.get_multiple(tickers)
    successful = sum(1 for v in results.values() if "error" not in v)
    failed = len(tickers) - successful
    return {
        "status": "success",
        "total": len(tickers),
        "successful": successful,
        "failed": failed,
        "data": results,
    }
