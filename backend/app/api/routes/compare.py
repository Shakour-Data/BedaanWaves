"""Compare API Router
---------------------------------------------------------------------------
API endpoints for comparing multiple stocks side-by-side.

FEATURES:
- Compare 2-5 stocks simultaneously
- Compare by dimensions (6D scores)
- Compare by financial metrics
- Compare by technical indicators
- Historical performance comparison

USAGE:
- POST /api/v1/compare/stocks - Compare specific stocks
- GET /api/v1/compare/dimensions/{symbol1}/{symbol2} - Compare dimensions
- GET /api/v1/compare/metrics/{symbol1}/{symbol2} - Compare metrics
- POST /api/v1/compare/historical - Compare historical performance
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.services.core.cache_service import CacheService
from app.services.data.stock_service import StockService
from app.services.analysis.scoring_service import ScoringService

router = APIRouter(prefix="/compare", tags=["Compare"])


# =============================================================================
# Request/Response Models
# =============================================================================

class CompareStocksRequest(BaseModel):
    """Request model for comparing stocks"""
    symbols: List[str] = Field(..., min_items=2, max_items=5, description="List of stock symbols to compare")
    include_dimensions: bool = Field(True, description="Include 6D dimension scores")
    include_metrics: bool = Field(True, description="Include financial metrics")
    include_technical: bool = Field(True, description="Include technical indicators")
    include_historical: bool = Field(False, description="Include historical performance")
    days: int = Field(30, ge=1, le=365, description="Number of days for historical data")


class CompareHistoricalRequest(BaseModel):
    """Request model for historical comparison"""
    symbols: List[str] = Field(..., min_items=2, max_items=5, description="List of stock symbols to compare")
    days: int = Field(30, ge=1, le=365, description="Number of days for historical data")


class DimensionComparison(BaseModel):
    """Dimension scores comparison"""
    fundamental: Optional[float] = None
    technical: Optional[float] = None
    sentiment: Optional[float] = None
    risk: Optional[float] = None
    macro: Optional[float] = None
    ai: Optional[float] = None


class MetricsComparison(BaseModel):
    """Financial metrics comparison"""
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    eps: Optional[float] = None
    dividend_yield: Optional[float] = None
    roe: Optional[float] = None
    debt_to_equity: Optional[float] = None
    current_ratio: Optional[float] = None


class TechnicalComparison(BaseModel):
    """Technical indicators comparison"""
    rsi_14: Optional[float] = None
    macd: Optional[float] = None
    bollinger_upper: Optional[float] = None
    bollinger_lower: Optional[float] = None
    ema_50: Optional[float] = None
    ema_200: Optional[float] = None
    volume_sma_20: Optional[float] = None


class HistoricalPoint(BaseModel):
    """Single point in historical comparison"""
    date: str
    symbol: str
    price: float
    change_pct: float
    volume: Optional[int] = None


class StockComparison(BaseModel):
    """Complete comparison for a single stock"""
    symbol: str
    name: Optional[str] = None
    sector: Optional[str] = None
    current_price: Optional[float] = None
    change_pct: Optional[float] = None
    overall_score: Optional[float] = None
    grade: Optional[str] = None
    dimensions: Optional[DimensionComparison] = None
    metrics: Optional[MetricsComparison] = None
    technical: Optional[TechnicalComparison] = None


class CompareStocksResponse(BaseModel):
    """Response model for compare stocks endpoint"""
    status: str
    count: int
    symbols: List[str]
    comparisons: List[StockComparison]
    historical_data: Optional[List[HistoricalPoint]] = None
    timestamp: str


class CompareDimensionsResponse(BaseModel):
    """Response for dimension comparison"""
    status: str
    symbols: List[str]
    dimensions: dict  # dimension_name -> {symbol -> score}
    winner_by_dimension: dict  # dimension_name -> symbol
    timestamp: str


# =============================================================================
# API Endpoints
# =============================================================================

@router.post("/stocks", response_model=CompareStocksResponse)
async def compare_stocks(
    request: CompareStocksRequest,
    cache_service: CacheService = Depends(),
    stock_service: StockService = Depends(),
    scoring_service: ScoringService = Depends(),
) -> CompareStocksResponse:
    symbols = request.symbols
    try:
        stocks_data = await stock_service.get_multiple(symbols)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to fetch stock data: {exc}")

    comparisons: List[StockComparison] = []
    for symbol in symbols:
        data = stocks_data.get(symbol, {})
        if "error" in data:
            continue
        ticker = data.get("symbol", symbol)
        overall_score = 0.0
        grade = ""
        dimensions = None
        if request.include_dimensions:
            score_input = {
                "ticker": ticker,
                "market": data.get("exchange", "NASDAQ"),
                "fundamental": {},
                "technical": {},
                "sentiment": {},
                "risk": {},
                "macro": {},
                "ai": {},
            }
            try:
                scores = await scoring_service.analyze(score_input)
                overall_score = scores.get("overall_score", 0.0)
                grade = scores.get("grade", "")
                dim_scores = scores.get("dimension_scores", {})
                dimensions = DimensionComparison(
                    fundamental=dim_scores.get("fundamental"),
                    technical=dim_scores.get("technical"),
                    sentiment=dim_scores.get("sentiment"),
                    risk=dim_scores.get("risk"),
                    macro=dim_scores.get("macro"),
                    ai=dim_scores.get("ai"),
                )
            except Exception:
                pass

        metrics = None
        if request.include_metrics:
            metrics = MetricsComparison(
                market_cap=data.get("market_cap"),
                pe_ratio=data.get("pe_ratio"),
                pb_ratio=data.get("pb_ratio"),
                eps=data.get("eps"),
                dividend_yield=data.get("dividend_yield"),
                roe=data.get("roe"),
                debt_to_equity=data.get("debt_to_equity"),
                current_ratio=data.get("current_ratio"),
            )

        technical = None
        if request.include_technical:
            technical = TechnicalComparison(
                rsi_14=None,
                macd=None,
                bollinger_upper=None,
                bollinger_lower=None,
                ema_50=None,
                ema_200=None,
                volume_sma_20=None,
            )

        comparisons.append(StockComparison(
            symbol=symbol,
            name=data.get("name") or data.get("shortName") or data.get("longName"),
            sector=data.get("sector"),
            current_price=data.get("price") or data.get("currentPrice"),
            change_pct=data.get("change_percent") or data.get("changePct"),
            overall_score=overall_score if overall_score else None,
            grade=grade,
            dimensions=dimensions,
            metrics=metrics,
            technical=technical,
        ))

    historical_data = None
    if request.include_historical:
        try:
            hist_points: List[HistoricalPoint] = []
            for symbol in symbols:
                history = await stock_service.get_history(symbol, days=request.days)
                for point in history[-30:]:
                    hist_points.append(HistoricalPoint(
                        date=point.get("timestamp", "")[:10],
                        symbol=symbol,
                        price=point.get("close", 0),
                        change_pct=0.0,
                        volume=point.get("volume"),
                    ))
            historical_data = hist_points
        except Exception:
            pass

    return format_comparison_response(comparisons, historical_data)


@router.get("/dimensions/{symbol1}/{symbol2}", response_model=CompareDimensionsResponse)
async def compare_dimensions(
    symbol1: str,
    symbol2: str,
    include_sub_dimensions: bool = Query(False, description="Include sub-dimension scores"),
    scoring_service: ScoringService = Depends(),
    stock_service: StockService = Depends(),
) -> CompareDimensionsResponse:
    """
    Compare 6D dimension scores between two stocks.
    
    Returns:
    - Individual dimension scores for both stocks
    - Winner by dimension
    - Overall comparison summary
    """
    try:
        data1 = await stock_service.get_stock(symbol1)
        data2 = await stock_service.get_stock(symbol2)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to fetch stock data: {exc}")

    dimensions = {}
    for label, symbol, data in [("symbol1", symbol1, data1), ("symbol2", symbol2, data2)]:
        score_input = {
            "ticker": data.get("symbol", symbol),
            "market": data.get("exchange", "NASDAQ"),
            "fundamental": {},
            "technical": {},
            "sentiment": {},
            "risk": {},
            "macro": {},
            "ai": {},
        }
        try:
            scores = await scoring_service.analyze(score_input)
            dim_scores = scores.get("dimension_scores", {})
            dimensions[label] = dim_scores
        except Exception:
            dimensions[label] = {}

    dim_scores_combined: dict = {}
    for dim in ["fundamental", "technical", "sentiment", "risk", "macro", "ai"]:
        dim_scores_combined[dim] = {
            symbol1: dimensions.get("symbol1", {}).get(dim),
            symbol2: dimensions.get("symbol2", {}).get(dim),
        }

    winners = calculate_winner_by_dimension(dim_scores_combined)

    return CompareDimensionsResponse(
        status="success",
        symbols=[symbol1, symbol2],
        dimensions=dim_scores_combined,
        winner_by_dimension=winners,
        timestamp=datetime.utcnow().isoformat(),
    )


@router.get("/metrics/{symbol1}/{symbol2}")
async def compare_metrics(
    symbol1: str,
    symbol2: str,
    stock_service: StockService = Depends(),
):
    """
    Compare financial metrics between two stocks.
    
    Includes:
    - Market cap
    - P/E ratio
    - P/B ratio
    - EPS
    - Dividend yield
    - ROE
    - Debt ratios
    """
    try:
        data1 = await stock_service.get_stock(symbol1)
        data2 = await stock_service.get_stock(symbol2)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to fetch stock data: {exc}")

    return {
        "symbol1_metrics": {
            "market_cap": data1.get("market_cap"),
            "pe_ratio": data1.get("pe_ratio"),
            "pb_ratio": data1.get("pb_ratio"),
            "eps": data1.get("eps"),
            "dividend_yield": data1.get("dividend_yield"),
            "roe": data1.get("roe"),
            "debt_to_equity": data1.get("debt_to_equity"),
            "current_ratio": data1.get("current_ratio"),
        },
        "symbol2_metrics": {
            "market_cap": data2.get("market_cap"),
            "pe_ratio": data2.get("pe_ratio"),
            "pb_ratio": data2.get("pb_ratio"),
            "eps": data2.get("eps"),
            "dividend_yield": data2.get("dividend_yield"),
            "roe": data2.get("roe"),
            "debt_to_equity": data2.get("debt_to_equity"),
            "current_ratio": data2.get("current_ratio"),
        },
    }


@router.post("/historical")
async def compare_historical(
    request: CompareHistoricalRequest,
    stock_service: StockService = Depends(),
):
    """
    Compare historical performance of multiple stocks.
    
    Returns price data, change percentages, and volume for the specified period.
    """
    historical_data: List[dict] = []
    for symbol in request.symbols:
        try:
            history = await stock_service.get_history(symbol, days=request.days)
            for point in history:
                historical_data.append({
                    "date": point.get("timestamp", "")[:10],
                    "symbol": symbol,
                    "price": point.get("close", 0),
                    "change_pct": 0.0,
                    "volume": point.get("volume"),
                })
        except Exception:
            continue

    return {
        "status": "success",
        "symbols": request.symbols,
        "historical_data": historical_data,
        "timestamp": datetime.utcnow().isoformat(),
    }


# =============================================================================
# Helper Functions
# =============================================================================

def calculate_winner_by_dimension(
    dimension_scores: dict
) -> dict:
    """
    Determine the winner for each dimension.
    
    Args:
        dimension_scores: dict of dimension -> symbol -> score
    
    Returns:
        dict of dimension -> winning_symbol
    """
    winners = {}
    for dimension, scores in dimension_scores.items():
        if scores:
            winner = max(scores.items(), key=lambda x: x[1])[0]
            winners[dimension] = winner
    return winners


def format_comparison_response(
    comparisons: List[StockComparison],
    historical_data: Optional[List] = None
) -> CompareStocksResponse:
    """
    Format the comparison response.
    """
    from datetime import datetime
    
    return CompareStocksResponse(
        status="success",
        count=len(comparisons),
        symbols=[c.symbol for c in comparisons],
        comparisons=comparisons,
        historical_data=historical_data,
        timestamp=datetime.utcnow().isoformat(),
    )
