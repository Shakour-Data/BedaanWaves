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


class HierarchyScores(BaseModel):
    """Scores at a specific snapshot tier (daily/hourly/current)."""
    overall: Optional[float] = None
    dimensions: Optional[dict] = None
    sub_dimensions: Optional[dict] = None
    aspects: Optional[dict] = None
    sub_aspects: Optional[dict] = None

    class Config:
        from_attributes = True


class DeltaFrame(BaseModel):
    """Deltas between two snapshot tiers."""
    overall: Optional[float] = None
    overall_pct: Optional[float] = None
    dimensions: Optional[dict] = None
    sub_dimensions: Optional[dict] = None
    aspects: Optional[dict] = None
    sub_aspects: Optional[dict] = None

    class Config:
        from_attributes = True


class WeightSnapshot(BaseModel):
    """Current weights across 4 hierarchy levels."""
    dimension: Optional[dict] = None
    sub_dimension: Optional[dict] = None
    aspect: Optional[dict] = None
    sub_aspect: Optional[dict] = None

    class Config:
        from_attributes = True


class WeightTrendPoint(BaseModel):
    """Historical weight for one day / hour."""
    date: str
    weights: dict

    class Config:
        from_attributes = True


class WeightDeltaPoint(BaseModel):
    """Weight delta vs. prior reference."""
    key: str
    value: float

    class Config:
        from_attributes = True


class TrendPoint(BaseModel):
    """Historical trend point (daily or intraday cadence)."""
    timestamp: str
    avg_score: Optional[float] = None
    dimensions: Optional[dict] = None
    symbol_count: Optional[int] = None

    class Config:
        from_attributes = True


class SnapshotResponse(BaseModel):
    """Unified temporal snapshot payload per FR1."""
    snapshotId: str
    tier: str
    effectiveAt: str
    fetchedAt: str
    scores: dict  # {daily, hourly, current} -> HierarchyScores
    deltas: dict  # {hourly_vs_daily, current_vs_hourly, current_vs_daily} -> DeltaFrame
    weights: WeightSnapshot
    weightTrends: List[WeightTrendPoint]
    weightDeltas: List[WeightDeltaPoint]
    trends: dict  # {daily: [...], intraday: [...]}
    universe: dict  # {total, market: "NASDAQ"}
    symbol: Optional[str] = None

    class Config:
        from_attributes = True


class SnapshotIndexEntry(BaseModel):
    """Enumerated past snapshot entry for time-slider."""
    snapshotId: Optional[str] = None
    tier: str
    effectiveAt: str
    label: str
    symbolCount: Optional[int] = None

    class Config:
        from_attributes = True


class SnapshotIndexResponse(BaseModel):
    """Paginated index of snapshots."""
    status: str = "success"
    count: int
    entries: List[SnapshotIndexEntry]
    timestamp: str

    class Config:
        from_attributes = True