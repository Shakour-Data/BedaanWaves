/**
 * Compare API Router
 * ---------------------------------------------------------------------------
 * API endpoints for comparing multiple stocks side-by-side.
 * 
 * FEATURES:
 * - Compare 2-5 stocks simultaneously
 * - Compare by dimensions (6D scores)
 * - Compare by financial metrics
 * - Compare by technical indicators
 * - Historical performance comparison
 * 
 * USAGE:
 * - POST /api/v1/compare/stocks - Compare specific stocks
 * - GET /api/v1/compare/dimensions/{symbol1}/{symbol2} - Compare dimensions
 * - GET /api/v1/compare/metrics/{symbol1}/{symbol2} - Compare metrics
 * - POST /api/v1/compare/historical - Compare historical performance
 */

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ....core.config import get_settings
from ....services.core.cache_service import CacheService
from ....services.data.stock_service import StockService
from ....services.analysis.scoring_service import ScoringService

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
    pass


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
    pass


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
    pass


@router.post("/historical")
async def compare_historical(
    symbols: List[str] = Field(..., min_items=2, max_items=5),
    days: int = Field(30, ge=1, le=365),
    stock_service: StockService = Depends(),
):
    """
    Compare historical performance of multiple stocks.
    
    Returns price data, change percentages, and volume for the specified period.
    """
    # Implementation here
    pass


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
