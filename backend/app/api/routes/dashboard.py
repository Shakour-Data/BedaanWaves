"""Dashboard API Routes"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import logging

from app.db.base import get_async_session
from app.services.analysis.dashboard_service import DashboardService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["dashboard"])


@router.get("/dashboard/general", response_model=dict)
async def get_general_dashboard(
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """
    Get general/overall dashboard data for all symbols.
    
    Returns:
        Overall scores, dimension summaries, top/bottom performers
    """
    service = DashboardService()
    try:
        result = await service.get_general_dashboard(db)
        return result
    except Exception as exc:
        logger.error(f"General dashboard error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/dashboard/technical", response_model=dict)
async def get_technical_dashboard(
    limit: int = Query(50, ge=10, le=200),
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """
    Get technical dashboard data for all symbols.
    
    Returns:
        Technical scores, sub-dimensions, aspects, sub-aspects, distribution
    """
    service = DashboardService()
    try:
        result = await service.get_dimension_dashboard(db, dimension="technical", limit=limit)
        return result
    except Exception as exc:
        logger.error(f"Technical dashboard error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/dashboard/fundamental", response_model=dict)
async def get_fundamental_dashboard(
    limit: int = Query(50, ge=10, le=200),
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """
    Get fundamental dashboard data for all symbols.
    
    Returns:
        Fundamental scores, sub-dimensions, aspects, sub-aspects, distribution
    """
    service = DashboardService()
    try:
        result = await service.get_dimension_dashboard(db, dimension="fundamental", limit=limit)
        return result
    except Exception as exc:
        logger.error(f"Fundamental dashboard error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/dashboard/news", response_model=dict)
async def get_news_dashboard(
    limit: int = Query(50, ge=10, le=200),
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """
    Get news/sentiment dashboard data for all symbols.
    
    Returns:
        News sentiment scores, news counts, positive/negative/neutral breakdown
    """
    service = DashboardService()
    try:
        result = await service.get_news_dashboard(db, limit=limit)
        return result
    except Exception as exc:
        logger.error(f"News dashboard error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/dashboard/risk", response_model=dict)
async def get_risk_dashboard(
    limit: int = Query(50, ge=10, le=200),
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """
    Get risk dashboard data for all symbols.
    
    Returns:
        Risk scores, sub-dimensions, aspects, sub-aspects, distribution
    """
    service = DashboardService()
    try:
        result = await service.get_dimension_dashboard(db, dimension="risk", limit=limit)
        return result
    except Exception as exc:
        logger.error(f"Risk dashboard error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/dashboard/board", response_model=dict)
async def get_board_dashboard(
    limit: int = Query(50, ge=10, le=200),
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """
    Get board/governance dashboard data for all symbols.
    
    Returns:
        Board scores, board member counts, officer counts, governance metrics
    """
    service = DashboardService()
    try:
        result = await service.get_board_dashboard(db, limit=limit)
        return result
    except Exception as exc:
        logger.error(f"Board dashboard error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/dashboard/ai", response_model=dict)
async def get_ai_dashboard(
    limit: int = Query(50, ge=10, le=200),
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """
    Get AI/ML dashboard data for all symbols.
    
    Returns:
        AI scores, ML signals, confidence, expected returns, risk scores
    """
    service = DashboardService()
    try:
        result = await service.get_ai_dashboard(db, limit=limit)
        return result
    except Exception as exc:
        logger.error(f"AI dashboard error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))
