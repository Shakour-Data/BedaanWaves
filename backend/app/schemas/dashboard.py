"""
Dashboard schema definitions for API responses.
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel


class MarketIndex(BaseModel):
    """Market index data model."""
    symbol: str
    name: str
    price: float
    change: float
    change_percent: float
    is_open: bool
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TopStock(BaseModel):
    """Top stock data model with AI scoring."""
    symbol: str
    name: str
    price: float
    change: float
    change_percent: float
    volume: str
    market_cap: str
    pe_ratio: float
    sector: str
    score: Optional[int] = None
    ai_recommendation: Optional[str] = None

    class Config:
        from_attributes = True


class MarketMover(BaseModel):
    """Market gainer or loser data model."""
    symbol: str
    name: str
    change_percent: float
    type: str  # "gainer" or "loser"

    class Config:
        from_attributes = True


class SectorPerformance(BaseModel):
    """Sector performance data model."""
    name: str
    change_percent: float
    volume: str
    top_gainer: str

    class Config:
        from_attributes = True


class MarketSummary(BaseModel):
    """Overall market summary statistics."""
    total_market_cap: str
    total_volume: str
    advancing_stocks: int
    declining_stocks: int
    new_highs: int
    new_lows: int
    vix: float
    vix_change: float

    class Config:
        from_attributes = True


class DashboardOverview(BaseModel):
    """Complete dashboard overview combining all metrics."""
    indices: List[MarketIndex]
    top_stocks: List[TopStock]
    market_movers: List[MarketMover]
    market_summary: MarketSummary
    last_updated: datetime

    class Config:
        from_attributes = True