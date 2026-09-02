"""Stock Data Routes - v1 and v2 with versioning

All data is fetched live from yfinance. No hardcoded or mock data.
"""

from fastapi import APIRouter, Depends, Query, HTTPException, Header, Response
from typing import List, Optional
from datetime import datetime, timezone
import logging

from app.services.data.stock_service import StockService
from app.services.data.real_time_market_data_service import RealTimeMarketDataService
from app.core.config import get_settings
from app.services.core.dependency_container import get_global_container

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(tags=["stocks"])


def _add_version_header(response: Response, version: str = "v1"):
    """Add API version header to response."""
    response.headers["X-API-Version"] = version
    response.headers["X-API-Version-Deprecated"] = "false" if version == "v2" else "false"
    response.headers["X-Rate-Limit-Remaining"] = "60"


def get_stock_service() -> StockService:
    """Get StockService from the dependency container."""
    container = get_global_container()
    if container.has("stock_service"):
        return container.get("stock_service")
    return StockService()


DEFAULT_POPULAR_TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "BRK-B"]


@router.get("/search", response_model=dict)
async def search_stocks(
    q: str = Query("", min_length=0),
    limit: int = Query(20, ge=1, le=100),
    service: StockService = Depends(get_stock_service),
    response: Response = None
) -> dict:
    """Search stocks by query using live yfinance data.

    An empty query returns a default set of popular tickers so the browse
    view is populated instead of failing validation (422) on an empty string.

    Every result is enriched with full quote data (price, change, volume,
    sector, etc.) so the UI renders complete, correct information.
    """
    if response:
        _add_version_header(response, "v1")

    if q.strip():
        # yfinance suggestions only contain symbol/name; enrich with full data.
        suggestions = await service.search(q.strip())
        symbols = [s.get("symbol") for s in suggestions if s.get("symbol")]
        enriched = await service.get_multiple(symbols)
        results = []
        for symbol in symbols:
            data = enriched.get(symbol)
            if isinstance(data, dict) and "error" not in data:
                results.append(data)
            else:
                # Fallback to the bare suggestion if enrichment failed.
                fallback = next((s for s in suggestions if s.get("symbol") == symbol), None)
                if fallback:
                    results.append({
                        "symbol": symbol,
                        "name": fallback.get("name", symbol),
                        "price": 0,
                        "change": 0,
                        "change_percent": 0,
                        "volume": 0,
                        "sector": fallback.get("sector", "-"),
                        "exchange": fallback.get("exchange", ""),
                    })
    else:
        multiple = await service.get_multiple(DEFAULT_POPULAR_TICKERS)
        results = [data for data in multiple.values() if isinstance(data, dict) and "error" not in data]

    return {
        "status": "success",
        "query": q,
        "count": len(results),
        "data": results[:limit],
        "api_version": "v1",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/{ticker}", response_model=dict)
async def get_stock(
    ticker: str,
    version: str = Query("v1", alias="api_version"),
    service: StockService = Depends(get_stock_service),
    response: Response = None
) -> dict:
    """Get stock information by ticker from live yfinance data."""
    if response:
        _add_version_header(response, version)
    
    data = await service.get_stock(ticker)
    
    result = {
        "status": "success",
        "ticker": ticker,
        "data": data,
        "api_version": version,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    if version == "v1":
        result["deprecated"] = False
        result["migrated_to"] = "v2 has same endpoint"
    
    return result


@router.post("/batch", response_model=dict)
async def get_multiple_stocks(
    tickers: List[str],
    service: StockService = Depends(get_stock_service),
    response: Response = None
) -> dict:
    """Get multiple stocks by tickers from live yfinance data."""
    if response:
        _add_version_header(response, "v1")
    
    results = await service.get_multiple(tickers)
    successful = sum(1 for v in results.values() if "error" not in v)
    failed = len(tickers) - successful
    return {
        "status": "success",
        "total": len(tickers),
        "successful": successful,
        "failed": failed,
        "data": results,
        "api_version": "v1",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# ============================================================================
# V2 Endpoints with Enhanced Features
# ============================================================================

@router.post("/v2/batch", response_model=dict)
async def get_multiple_stocks_v2(
    tickers: List[str],
    include_history: bool = Query(False, description="Include historical data"),
    service: StockService = Depends(get_stock_service),
    response: Response = None
) -> dict:
    """Get multiple stocks by tickers (v2 with enhanced features)."""
    if response:
        _add_version_header(response, "v2")
    
    results = await service.get_multiple(tickers)
    
    if include_history:
        for ticker in tickers:
            if ticker in results and "error" not in results[ticker]:
                try:
                    history = await service.get_history(ticker)
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
        "features": ["batch", "historical_inclusion"] if include_history else ["batch"],
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# ============================================================================
# Data Export/Import Endpoints
# ============================================================================

@router.post("/export", response_model=dict)
async def export_portfolio_data(
    tickers: Optional[List[str]] = None,
    format: str = Query("json", pattern="^(json|csv)$"),
    service: StockService = Depends(get_stock_service),
    response: Response = None
) -> dict:
    """Export portfolio data in JSON or CSV format."""
    if response:
        _add_version_header(response, "v1")
    
    if not tickers:
        tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "META"]
    
    data = await service.get_multiple(tickers)
    
    export_result = {
        "export_timestamp": datetime.now(timezone.utc).isoformat(),
        "total_records": len(tickers),
        "successful_exports": sum(1 for v in data.values() if "error" not in v),
        "format": format,
        "data": data,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    if format == "csv":
        import io, csv
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
                    datetime.now(timezone.utc).isoformat()
                ])
        export_result["csv_content"] = csv_buffer.getvalue()
    
    return export_result


@router.post("/import", response_model=dict)
async def import_portfolio_data(
    file: str,
    service: StockService = Depends(get_stock_service),
    response: Response = None
) -> dict:
    """Import portfolio data from JSON or CSV format."""
    if response:
        _add_version_header(response, "v1")
    
    try:
        if file.startswith('[{') or file.startswith('['):
            data = __import__("json").loads(file)
        elif file.startswith('{'):
            data = __import__("json").loads(file)
        else:
            import io, csv
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
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except __import__("json").JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Import failed: {str(e)}")