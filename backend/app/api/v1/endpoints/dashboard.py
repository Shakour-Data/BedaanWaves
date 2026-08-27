"""
Dashboard API endpoints for NASDAQ market overview and analytics.
"""

from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.stock import Stock
from app.models.price import Price
from app.schemas.dashboard import (
    MarketIndex,
    TopStock,
    MarketMover,
    MarketSummary,
    SectorPerformance,
    DashboardOverview
)

router = APIRouter()


@router.get("/indices", response_model=List[MarketIndex])
async def get_market_indices(
    db: AsyncSession = Depends(get_db)
) -> List[MarketIndex]:
    """
    Get major market indices (NASDAQ, S&P 500, Dow Jones).
    """
    # Mock data for market indices - in production, fetch from external API
    indices = [
        MarketIndex(
            symbol="IXIC",
            name="NASDAQ Composite",
            price=17713.52,
            change=125.38,
            change_percent=0.71,
            is_open=True,
            updated_at=datetime.utcnow()
        ),
        MarketIndex(
            symbol="NDX",
            name="NASDAQ-100",
            price=20412.18,
            change=142.65,
            change_percent=0.70,
            is_open=True,
            updated_at=datetime.utcnow()
        ),
        MarketIndex(
            symbol="SPX",
            name="S&P 500",
            price=5980.36,
            change=28.44,
            change_percent=0.48,
            is_open=True,
            updated_at=datetime.utcnow()
        ),
        MarketIndex(
            symbol="DJI",
            name="Dow Jones",
            price=44148.32,
            change=68.92,
            change_percent=0.16,
            is_open=True,
            updated_at=datetime.utcnow()
        ),
    ]
    return indices


@router.get("/top-stocks", response_model=List[TopStock])
async def get_top_stocks(
    limit: int = Query(10, ge=1, le=50),
    sort_by: str = Query("score", regex="^(score|market_cap|volume|change_percent)$"),
    db: AsyncSession = Depends(get_db)
) -> List[TopStock]:
    """
    Get top NASDAQ stocks sorted by various criteria.
    """
    # In production, fetch from database with proper joins
    # For now, return mock data representing top NASDAQ stocks
    top_stocks = [
        TopStock(
            symbol="NVDA",
            name="NVIDIA Corporation",
            price=138.25,
            change=4.87,
            change_percent=3.65,
            volume="312.5M",
            market_cap="3.39T",
            pe_ratio=62.8,
            sector="Technology",
            score=96,
            ai_recommendation="Strong Buy"
        ),
        TopStock(
            symbol="MSFT",
            name="Microsoft Corporation",
            price=432.05,
            change=5.12,
            change_percent=1.20,
            volume="21.8M",
            market_cap="3.21T",
            pe_ratio=35.1,
            sector="Technology",
            score=94,
            ai_recommendation="Strong Buy"
        ),
        TopStock(
            symbol="AAPL",
            name="Apple Inc.",
            price=233.67,
            change=3.45,
            change_percent=1.50,
            volume="52.3M",
            market_cap="3.56T",
            pe_ratio=32.4,
            sector="Technology",
            score=92,
            ai_recommendation="Buy"
        ),
        TopStock(
            symbol="GOOGL",
            name="Alphabet Inc.",
            price=178.35,
            change=1.25,
            change_percent=0.71,
            volume="19.2M",
            market_cap="2.21T",
            pe_ratio=25.6,
            sector="Communication Services",
            score=90,
            ai_recommendation="Buy"
        ),
        TopStock(
            symbol="AMZN",
            name="Amazon.com Inc.",
            price=197.83,
            change=2.14,
            change_percent=1.09,
            volume="38.9M",
            market_cap="2.05T",
            pe_ratio=58.3,
            sector="Consumer Cyclical",
            score=88,
            ai_recommendation="Buy"
        ),
    ]
    
    # Sort based on sort_by parameter
    if sort_by == "score":
        top_stocks.sort(key=lambda x: x.score, reverse=True)
    elif sort_by == "market_cap":
        # Parse market cap for sorting (simplified)
        top_stocks.sort(key=lambda x: x.market_cap, reverse=True)
    elif sort_by == "change_percent":
        top_stocks.sort(key=lambda x: x.change_percent, reverse=True)
    
    return top_stocks[:limit]


@router.get("/movers", response_model=List[MarketMover])
async def get_market_movers(
    limit: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db)
) -> List[MarketMover]:
    """
    Get top market gainers and losers.
    """
    movers = [
        MarketMover(symbol="NVDA", name="NVIDIA Corporation", change_percent=3.65, type="gainer"),
        MarketMover(symbol="META", name="Meta Platforms Inc.", change_percent=2.89, type="gainer"),
        MarketMover(symbol="AMD", name="Advanced Micro Devices", change_percent=2.45, type="gainer"),
        MarketMover(symbol="TSLA", name="Tesla Inc.", change_percent=-2.07, type="loser"),
        MarketMover(symbol="INTC", name="Intel Corporation", change_percent=-1.85, type="loser"),
    ]
    return movers[:limit]


@router.get("/overview", response_model=DashboardOverview)
async def get_dashboard_overview(
    db: AsyncSession = Depends(get_db)
) -> DashboardOverview:
    """
    Get complete dashboard overview combining all metrics.
    """
    # In production, this would fetch from database and external APIs
    return DashboardOverview(
        indices=await get_market_indices(db),
        top_stocks=await get_top_stocks(limit=6, sort_by="score", db=db),
        market_movers=await get_market_movers(limit=5, db=db),
        market_summary=MarketSummary(
            total_market_cap="$58.4T",
            total_volume="8.2B",
            advancing_stocks=3245,
            declining_stocks=1892,
            new_highs=742,
            new_lows=128,
            vix=14.32,
            vix_change=-2.1
        ),
        last_updated=datetime.utcnow()
    )