"""Portfolio Routes"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, and_
from typing import List
import logging
from datetime import datetime, timezone

from app.db.base import get_async_session
from app.models.models import Portfolio, Position, Asset
from app.schemas.schemas import (
    PortfolioCreate, PortfolioUpdate, PortfolioResponse,
    PositionCreate, PositionResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/portfolios", tags=["portfolios"])


@router.post("/", response_model=PortfolioResponse)
async def create_portfolio(
    portfolio: PortfolioCreate,
    user_id: str = Query(...),
    db: AsyncSession = Depends(get_async_session),
) -> PortfolioResponse:
    """Create a new portfolio."""
    new_portfolio = Portfolio(
        user_id=user_id,
        name=portfolio.name,
        description=portfolio.description,
        portfolio_type=portfolio.portfolio_type,
        base_currency=portfolio.base_currency,
    )
    db.add(new_portfolio)
    await db.commit()
    await db.refresh(new_portfolio)
    return new_portfolio


@router.get("/", response_model=List[PortfolioResponse])
async def get_portfolios(
    user_id: str = Query(...),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_async_session),
) -> List[PortfolioResponse]:
    """Get all portfolios for a user."""
    query = (
        select(Portfolio)
        .where(Portfolio.user_id == user_id)
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{portfolio_id}", response_model=PortfolioResponse)
async def get_portfolio(
    portfolio_id: str,
    db: AsyncSession = Depends(get_async_session),
) -> PortfolioResponse:
    """Get portfolio by ID."""
    query = select(Portfolio).where(Portfolio.id == portfolio_id)
    result = await db.execute(query)
    portfolio = result.scalars().first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return portfolio


@router.put("/{portfolio_id}", response_model=PortfolioResponse)
async def update_portfolio(
    portfolio_id: str,
    portfolio_update: PortfolioUpdate,
    db: AsyncSession = Depends(get_async_session),
) -> PortfolioResponse:
    """Update portfolio."""
    query = select(Portfolio).where(Portfolio.id == portfolio_id)
    result = await db.execute(query)
    portfolio = result.scalars().first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    if portfolio_update.name is not None:
        portfolio.name = portfolio_update.name
    if portfolio_update.description is not None:
        portfolio.description = portfolio_update.description
    if portfolio_update.portfolio_type is not None:
        portfolio.portfolio_type = portfolio_update.portfolio_type

    portfolio.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(portfolio)
    return portfolio


@router.delete("/{portfolio_id}")
async def delete_portfolio(
    portfolio_id: str,
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """Delete portfolio."""
    query = select(Portfolio).where(Portfolio.id == portfolio_id)
    result = await db.execute(query)
    portfolio = result.scalars().first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    await db.delete(portfolio)
    await db.commit()
    return {"status": "success", "message": "Portfolio deleted"}


@router.post("/{portfolio_id}/holdings", response_model=PositionResponse)
async def add_holding(
    portfolio_id: str,
    holding: PositionCreate,
    db: AsyncSession = Depends(get_async_session),
) -> PositionResponse:
    """Add holding to portfolio."""
    portfolio_query = select(Portfolio).where(Portfolio.id == portfolio_id)
    portfolio_result = await db.execute(portfolio_query)
    portfolio = portfolio_result.scalars().first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    asset_query = select(Asset).where(Asset.id == holding.asset_id)
    asset_result = await db.execute(asset_query)
    asset = asset_result.scalars().first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    existing = (
        await db.execute(
            select(Position).where(
                and_(
                    Position.portfolio_id == portfolio_id,
                    Position.asset_id == holding.asset_id,
                )
            )
        )
    ).scalars().first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Holding already exists for this asset"
        )

    new_position = Position(
        portfolio_id=portfolio_id,
        asset_id=holding.asset_id,
        quantity=holding.quantity,
        entry_price=holding.entry_price,
        entry_date=holding.entry_date,
        stop_loss=holding.stop_loss,
        take_profit=holding.take_profit,
        notes=holding.notes,
    )
    db.add(new_position)
    await db.commit()
    await db.refresh(new_position)
    return new_position


@router.get("/{portfolio_id}/holdings", response_model=List[PositionResponse])
async def get_holdings(
    portfolio_id: str,
    db: AsyncSession = Depends(get_async_session),
) -> List[PositionResponse]:
    """Get portfolio holdings."""
    query = select(Position).where(Position.portfolio_id == portfolio_id)
    result = await db.execute(query)
    return result.scalars().all()


@router.delete("/{portfolio_id}/holdings/{holding_id}")
async def remove_holding(
    portfolio_id: str,
    holding_id: str,
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """Remove holding from portfolio."""
    query = select(Position).where(
        and_(
            Position.id == holding_id,
            Position.portfolio_id == portfolio_id,
        )
    )
    result = await db.execute(query)
    position = result.scalars().first()
    if not position:
        raise HTTPException(status_code=404, detail="Holding not found")

    await db.delete(position)
    await db.commit()
    return {"status": "success", "message": "Holding removed"}
