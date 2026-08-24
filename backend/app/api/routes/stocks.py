"""Stock Data Routes - v1 and v2 with versioning"""

from fastapi import APIRouter, Depends, Query, HTTPException, Header, Response
from typing import List, Optional
from datetime import datetime
import logging
import json
import csv
import io
import tempfile
import os

from app.services.data.stock_service import StockService
from app.services.data.brs_api_client import BrsApiClient
from app.api.routes.live import get_brs_client
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(tags=["stocks"])


def _add_version_header(response: Response, version: str = "v1"):
    """Add API version header to response."""
    response.headers["X-API-Version"] = version
    response.headers["X-API-Version-Deprecated"] = "false" if version == "v2" else "false"
    response.headers["X-Rate-Limit-Remaining"] = "60"


@router.get("/search", response_model=dict)
async def search_stocks(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    client: BrsApiClient = Depends(get_brs_client),
    response: Response = None
) -> dict:
    """Search stocks by query."""
    if response:
        _add_version_header(response, "v1")
    
    service = StockService(brs_client=client)
    await service.initialize()
    results = await service.search(q)
    return {
        "status": "success",
        "query": q,
        "count": len(results),
        "data": results[:limit],
        "api_version": "v1"
    }


@router.get("/{ticker}", response_model=dict)
async def get_stock(
    ticker: str,
    version: str = Query("v1", alias="api_version"),
    client: BrsApiClient = Depends(get_brs_client),
    response: Response = None
) -> dict:
    """Get stock information by ticker."""
    if response:
        _add_version_header(response, version)
    
    service = StockService(brs_client=client)
    await service.initialize()
    data = await service.get_stock(ticker, use_cache=False)
    
    result = {
        "status": "success",
        "ticker": ticker,
        "data": data,
        "api_version": version,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if version == "v1":
        result["deprecated"] = False
        result["migrated_to"] = "v2 has same endpoint"
    
    return result


@router.post("/batch", response_model=dict)
async def get_multiple_stocks(
    tickers: List[str],
    client: BrsApiClient = Depends(get_brs_client),
    response: Response = None
) -> dict:
    """Get multiple stocks by tickers."""
    if response:
        _add_version_header(response, "v1")
    
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
        "api_version": "v1"
    }


# ============================================================================
# V2 Endpoints with Enhanced Features
# ============================================================================

@router.post("/v2/batch", response_model=dict)
async def get_multiple_stocks_v2(
    tickers: List[str],
    include_history: bool = Query(False, description="Include historical data"),
    client: BrsApiClient = Depends(get_brs_client),
    response: Response = None
) -> dict:
    """Get multiple stocks by tickers (v2 with enhanced features)."""
    if response:
        _add_version_header(response, "v2")
    
    service = StockService(brs_client=client)
    await service.initialize()
    results = await service.get_multiple(tickers)
    
    if include_history:
        for ticker in tickers:
            if ticker in results and "error" not in results[ticker]:
                try:
                    history = await client.get_history(ticker)
                    results[ticker]["history"] = history[:50]
                except Exception:
                    results[ticker]["history"] = []
    
    successful = sum(1 for v in results.values() if "error" not in v)
    return {
        "status": "success",
        "total": len(tickers),
        "successful": successful,
        "failed_count": len(tickers) - successful,
        "data": results,
        "api_version": "v2",
        "features": ["batch", "historical_inclusion"] if include_history else ["batch"]
    }


# ============================================================================
# Data Export/Import Endpoints
# ============================================================================

@router.post("/export", response_model=dict)
async def export_portfolio_data(
    tickers: Optional[List[str]] = None,
    format: str = Query("json", pattern="^(json|csv)$"),
    client: BrsApiClient = Depends(get_brs_client),
    response: Response = None
) -> dict:
    """Export portfolio data in JSON or CSV format."""
    if response:
        _add_version_header(response, "v1")
    
    service = StockService(brs_client=client)
    await service.initialize()
    
    if not tickers:
        symbols_data = await client.get_all_symbols(market_type=1)
        tickers = [s.get("l18") for s in symbols_data if s.get("l18")][:100]
    
    data = await service.get_multiple(tickers)
    
    export_result = {
        "export_timestamp": datetime.utcnow().isoformat(),
        "total_records": len(tickers),
        "successful_exports": sum(1 for v in data.values() if "error" not in v),
        "format": format,
        "data": data
    }
    
    if format == "csv":
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerow(["ticker", "symbol", "price", "volume", "change", "timestamp"])
        for ticker, d in data.items():
            if "error" not in d:
                writer.writerow([
                    ticker,
                    d.get("symbol", ""),
                    d.get("price", ""),
                    d.get("volume", ""),
                    d.get("change", ""),
                    datetime.utcnow().isoformat()
                ])
        export_result["csv_content"] = csv_buffer.getvalue()
    
    return export_result


@router.post("/import", response_model=dict)
async def import_portfolio_data(
    file: str,
    client: BrsApiClient = Depends(get_brs_client),
    response: Response = None
) -> dict:
    """Import portfolio data from JSON or CSV format."""
    if response:
        _add_version_header(response, "v1")
    
    try:
        if file.startswith('[{') or file.startswith('['):
            data = json.loads(file)
        elif file.startswith('{'):
            data = json.loads(file)
        else:
            csv_buffer = io.StringIO(file)
            reader = csv.DictReader(csv_buffer)
            data = list(reader) if reader.fieldnames else []
        
        imported = []
        errors = []
        
        for item in data if isinstance(data, list) else [data]:
            if isinstance(item, dict) and "ticker" in item:
                ticker = item.get("ticker")
                if ticker:
                    try:
                        imported.append(ticker)
                    except Exception as e:
                        errors.append({"ticker": ticker, "error": str(e)})
        
        return {
            "status": "success",
            "imported_count": len(imported),
            "imported_tickers": imported,
            "errors": errors,
            "api_version": "v1",
            "timestamp": datetime.utcnow().isoformat()
        }
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Import failed: {str(e)}")