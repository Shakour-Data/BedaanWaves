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


from fastapi import APIRouter, Body, Depends, Query
from pydantic import BaseModel, Field

from ...services.analysis.scoring_service import ScoringService
from ...services.core.cache_service import CacheService
from ...services.data.stock_service import StockService

router = APIRouter(prefix="/compare", tags=["Compare"])


# =============================================================================
# Request/Response Models
# =============================================================================

class CompareStocksRequest(BaseModel):
    """Request model for comparing stocks"""
    symbols: list[str] = Field(..., min_items=2, max_items=5, description="List of stock symbols to compare")
    include_dimensions: bool = Field(True, description="Include 6D dimension scores")
    include_metrics: bool = Field(True, description="Include financial metrics")
    include_technical: bool = Field(True, description="Include technical indicators")
    include_historical: bool = Field(False, description="Include historical performance")
    days: int = Field(30, ge=1, le=365, description="Number of days for historical data")


class DimensionComparison(BaseModel):
    """Dimension scores comparison"""
    fundamental: float | None = None
    technical: float | None = None
    sentiment: float | None = None
    risk: float | None = None
    macro: float | None = None
    ai: float | None = None


class MetricsComparison(BaseModel):
    """Financial metrics comparison"""
    market_cap: float | None = None
    pe_ratio: float | None = None
    pb_ratio: float | None = None
    eps: float | None = None
    dividend_yield: float | None = None
    roe: float | None = None
    debt_to_equity: float | None = None
    current_ratio: float | None = None


class TechnicalComparison(BaseModel):
    """Technical indicators comparison"""
    rsi_14: float | None = None
    macd: float | None = None
    bollinger_upper: float | None = None
    bollinger_lower: float | None = None
    ema_50: float | None = None
    ema_200: float | None = None
    volume_sma_20: float | None = None


class HistoricalPoint(BaseModel):
    """Single point in historical comparison"""
    date: str
    symbol: str
    price: float
    change_pct: float
    volume: int | None = None


class StockComparison(BaseModel):
    """Complete comparison for a single stock"""
    symbol: str
    name: str | None = None
    sector: str | None = None
    current_price: float | None = None
    change_pct: float | None = None
    overall_score: float | None = None
    grade: str | None = None
    dimensions: DimensionComparison | None = None
    metrics: MetricsComparison | None = None
    technical: TechnicalComparison | None = None


class CompareStocksResponse(BaseModel):
    """Response model for compare stocks endpoint"""
    status: str
    count: int
    symbols: list[str]
    comparisons: list[StockComparison]
    historical_data: list[HistoricalPoint] | None = None
    timestamp: str


class CompareDimensionsResponse(BaseModel):
    """Response for dimension comparison"""
    status: str
    symbols: list[str]
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
) -> CompareStocksResponse:
    """
    Compare multiple stocks side-by-side.

    Supports 2-5 stocks comparison with:
    - 6D dimension scores
    - Financial metrics
    - Technical indicators
    - Historical performance
    """
    # Implementation here


@router.get("/dimensions/{symbol1}/{symbol2}", response_model=CompareDimensionsResponse)
async def compare_dimensions(
    symbol1: str,
    symbol2: str,
    include_sub_dimensions: bool = Query(False, description="Include sub-dimension scores"),
    scoring_service: ScoringService = Depends(),
) -> CompareDimensionsResponse:
    """
    Compare 6D dimension scores between two stocks.

    Returns:
    - Individual dimension scores for both stocks
    - Winner by dimension
    - Overall comparison summary
    """
    # Implementation here


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
    # Implementation here


@router.post("/historical")
async def compare_historical(
    symbols: list[str] = Body(..., min_items=2, max_items=5),
    days: int = Body(30, ge=1, le=365),
    stock_service: StockService = Depends(),
):
    """
    Compare historical performance of multiple stocks.

    Returns price data, change percentages, and volume for the specified period.
    """
    # Implementation here


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
    comparisons: list[StockComparison],
    historical_data: list | None = None
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
        timestamp=utc_now_iso(),
    )
