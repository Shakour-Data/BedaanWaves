"""Analysis and Signals Routes"""

from fastapi import APIRouter, Depends, Query, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime
from typing import List
import logging

from app.db.base import get_async_session
from app.models.models import Asset, MLSignal, PriceCandle
from app.schemas.schemas import MLSignalResponse, SignalTypeEnum
from app.services.analysis.technical_service import TechnicalAnalysisService
from app.services.analysis.risk_service import RiskAnalysisService
from app.services.analysis.fundamental_service import FundamentalAnalysisService
from app.services.analysis.momentum_service import MomentumService
from app.services.analysis.volatility_service import VolatilityService
from app.services.analysis.scoring_service import ScoringService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.get("/signals/{symbol}", response_model=MLSignalResponse)
async def get_signal(
    symbol: str,
    db: AsyncSession = Depends(get_async_session),
) -> MLSignalResponse:
    """
    Get latest ML signal for a symbol
    
    Args:
        symbol: Asset symbol
        
    Returns:
        Latest ML signal
    """
    # Get asset
    asset_query = select(Asset).where(Asset.symbol == symbol.upper())
    asset_result = await db.execute(asset_query)
    asset = asset_result.scalars().first()
    
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset {symbol} not found")
    
    # Get latest active signal
    signal_query = (
        select(MLSignal)
        .where(
            and_(
                MLSignal.asset_id == asset.id,
                MLSignal.is_active == True,
                MLSignal.valid_until >= datetime.utcnow(),
            )
        )
        .order_by(MLSignal.generated_at.desc())
        .limit(1)
    )
    
    result = await db.execute(signal_query)
    signal = result.scalars().first()
    
    if not signal:
        raise HTTPException(
            status_code=404,
            detail=f"No active signal found for {symbol}"
        )
    
    logger.info(f"Retrieved signal for {symbol}: {signal.signal_type}")
    return signal


@router.get("/signals-summary", response_model=dict)
async def get_signals_summary(
    market: str = Query(None),
    min_confidence: float = Query(0.6, ge=0, le=1),
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """
    Get summary of all active signals
    
    Args:
        market: Filter by market (optional)
        min_confidence: Minimum confidence threshold
        
    Returns:
        Summary of signals by type
    """
    query = select(MLSignal).where(
        and_(
            MLSignal.is_active == True,
            MLSignal.valid_until >= datetime.utcnow(),
            MLSignal.confidence >= min_confidence * 100,
        )
    )
    
    if market:
        query = query.join(Asset).where(Asset.market == market)
    
    result = await db.execute(query)
    signals = result.scalars().all()
    
    # Aggregate by signal type
    summary = {
        "BUY": 0,
        "SELL": 0,
        "HOLD": 0,
        "STRONG_BUY": 0,
        "STRONG_SELL": 0,
    }
    
    confidence_sum = {signal_type: 0 for signal_type in summary.keys()}
    
    for signal in signals:
        summary[signal.signal_type] += 1
        confidence_sum[signal.signal_type] += float(signal.confidence)
    
    # Calculate average confidence
    avg_confidence = {}
    for signal_type in summary.keys():
        if summary[signal_type] > 0:
            avg_confidence[signal_type] = round(
                confidence_sum[signal_type] / summary[signal_type], 2
            )
    
    return {
        "status": "success",
        "timestamp": datetime.utcnow().isoformat(),
        "total_signals": len(signals),
        "summary": summary,
        "average_confidence": avg_confidence,
    }


@router.get("/top-performers", response_model=dict)
async def get_top_performers(
    limit: int = Query(10, ge=1, le=100),
    timeframe: str = Query("1d"),
    market: str = Query(None),
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """
    Get top performing assets by return percentage
    
    Args:
        limit: Number of top performers
        timeframe: Candle timeframe
        market: Filter by market
        
    Returns:
        List of top performers with performance metrics
    """
    # Get latest candles for all assets
    query = select(Asset, PriceCandle).where(
        and_(
            Asset.active == True,
            PriceCandle.timeframe == timeframe,
        )
    ).outerjoin(
        PriceCandle,
        and_(
            Asset.id == PriceCandle.asset_id,
            PriceCandle.timestamp == (
                select(PriceCandle.timestamp)
                .where(PriceCandle.asset_id == Asset.id)
                .order_by(PriceCandle.timestamp.desc())
                .limit(1)
                .correlate(Asset)
                .scalar_subquery()
            )
        )
    )
    
    if market:
        query = query.where(Asset.market == market)
    
    result = await db.execute(query)
    results = result.all()
    
    performers = []
    for asset, candle in results:
        if candle:
            change_pct = (
                (float(candle.close) - float(candle.open)) / float(candle.open) * 100
                if float(candle.open) > 0
                else 0
            )
            performers.append({
                "symbol": asset.symbol,
                "name": asset.name,
                "change_percent": round(change_pct, 2),
                "current_price": float(candle.close),
                "volume": candle.volume,
            })
    
    # Sort by performance
    performers.sort(key=lambda x: x["change_percent"], reverse=True)
    top = performers[:limit]
    
    return {
        "status": "success",
        "timestamp": datetime.utcnow().isoformat(),
        "data": top,
    }


@router.get("/risk-analysis/{symbol}", response_model=dict)
async def get_risk_analysis(
    symbol: str,
    period_days: int = Query(252, ge=1, le=1000),
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """
    Get risk analysis for a symbol
    
    Args:
        symbol: Asset symbol
        period_days: Analysis period in days
        
    Returns:
        Risk metrics (volatility, VaR, Sharpe ratio, etc.)
    """
    # Get asset
    asset_query = select(Asset).where(Asset.symbol == symbol.upper())
    asset_result = await db.execute(asset_query)
    asset = asset_result.scalars().first()
    
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset {symbol} not found")
    
    # Get price history
    from datetime import timedelta
    start_date = datetime.utcnow() - timedelta(days=period_days)
    
    candle_query = (
        select(PriceCandle)
        .where(
            and_(
                PriceCandle.asset_id == asset.id,
                PriceCandle.timeframe == "1d",
                PriceCandle.timestamp >= start_date,
            )
        )
        .order_by(PriceCandle.timestamp.asc())
    )
    
    result = await db.execute(candle_query)
    candles = result.scalars().all()
    
    if len(candles) < 2:
        raise HTTPException(
            status_code=400,
            detail="Insufficient data for risk analysis"
        )
    
    # Calculate returns
    import numpy as np
    prices = np.array([float(c.close) for c in candles])
    returns = np.diff(prices) / prices[:-1]
    
    # Calculate metrics
    volatility = np.std(returns) * np.sqrt(252)  # Annualized
    sharpe_ratio = (np.mean(returns) * 252) / volatility if volatility > 0 else 0
    
    # VaR (95%)
    var_95 = np.percentile(returns, 5)
    
    # Max drawdown
    cumulative = np.cumprod(1 + returns)
    running_max = np.maximum.accumulate(cumulative)
    drawdown = (cumulative - running_max) / running_max
    max_drawdown = np.min(drawdown)
    
    return {
        "status": "success",
        "symbol": symbol,
        "period_days": period_days,
        "metrics": {
            "volatility": round(float(volatility), 4),
            "sharpe_ratio": round(float(sharpe_ratio), 4),
            "var_95": round(float(var_95) * 100, 2),
            "max_drawdown": round(float(max_drawdown) * 100, 2),
            "avg_return": round(float(np.mean(returns)) * 100, 4),
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/technical/{symbol}", response_model=dict)
async def technical_analysis(
    symbol: str,
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """
    TSE-specific technical analysis for a stored symbol.

    Loads daily candles from the database (market='TSE') and runs the
    TechnicalAnalysisService (moving averages, momentum, volatility, volume).
    Crypto / international feeds are intentionally NOT mixed in here.

    Args:
        symbol: TSE symbol (e.g. فملی، خودرو)

    Returns:
        Computed technical indicators for the symbol
    """
    # Exact match first, then case-insensitive fallback.
    asset = (
        await db.execute(select(Asset).where(Asset.symbol == symbol))
    ).scalars().first()
    if not asset:
        asset = (
            await db.execute(select(Asset).where(Asset.symbol == symbol.upper()))
        ).scalars().first()

    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset {symbol} not found")

    candles = (
        await db.execute(
            select(PriceCandle)
            .where(PriceCandle.asset_id == asset.id, PriceCandle.timeframe == "1d")
            .order_by(PriceCandle.timestamp.asc())
        )
    ).scalars().all()

    if len(candles) < 20:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient candle data for {symbol} (need >= 20, have {len(candles)})",
        )

    prices = [float(c.close) for c in candles]
    volumes = [float(c.volume) for c in candles]

    service = TechnicalAnalysisService()
    await service.initialize()
    result = await service.analyze(
        {"ticker": asset.symbol, "prices": prices, "volumes": volumes}
    )

    return {
        "status": "success",
        "symbol": asset.symbol,
        "name": asset.name,
        "market": asset.market,
        "data_points": len(candles),
        "indicators": result,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/risk/{symbol}", response_model=dict)
async def risk_analysis(
    symbol: str,
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """
    TSE-specific risk analysis for a stored symbol.

    Computes daily returns from the stored daily candles (market='TSE') and runs
    the RiskAnalysisService (volatility, VaR 95/99, CVaR, Sharpe, Sortino,
    max drawdown). Crypto / international feeds are intentionally excluded.

    Args:
        symbol: TSE symbol (e.g. فملی، خودرو)

    Returns:
        Risk metrics for the symbol
    """
    asset = (
        await db.execute(select(Asset).where(Asset.symbol == symbol))
    ).scalars().first()
    if not asset:
        asset = (
            await db.execute(select(Asset).where(Asset.symbol == symbol.upper()))
        ).scalars().first()

    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset {symbol} not found")

    candles = (
        await db.execute(
            select(PriceCandle)
            .where(PriceCandle.asset_id == asset.id, PriceCandle.timeframe == "1d")
            .order_by(PriceCandle.timestamp.asc())
        )
    ).scalars().all()

    if len(candles) < 20:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient candle data for {symbol} (need >= 20, have {len(candles)})",
        )

    closes = [float(c.close) for c in candles]
    returns = [
        (closes[i] - closes[i - 1]) / closes[i - 1]
        for i in range(1, len(closes))
        if closes[i - 1] != 0
    ]

    service = RiskAnalysisService()
    await service.initialize()
    result = await service.analyze(
        {"ticker": asset.symbol, "returns": returns, "prices": closes}
    )

    return {
        "status": "success",
        "symbol": asset.symbol,
        "name": asset.name,
        "market": asset.market,
        "data_points": len(returns),
        "risk": result,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.post("/fundamental", response_model=dict)
async def fundamental_analysis(
    data: dict = Body(...),
) -> dict:
    """
    Perform fundamental analysis for a ticker.
    
    Request body:
        ticker: Asset symbol
        financials: Financial data dict
    """
    ticker = data.get("ticker", "UNKNOWN")
    financials = data.get("financials", {})

    service = FundamentalAnalysisService()
    await service.initialize()
    result = await service.analyze({"ticker": ticker, "financials": financials})

    return {
        "status": "success",
        "symbol": ticker,
        "fundamental": result,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/momentum/{symbol}", response_model=dict)
async def momentum_analysis(
    symbol: str,
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """
    Momentum analysis for a stored symbol.
    
    Loads daily candles from the database and runs the MomentumService.
    """
    asset = (
        await db.execute(select(Asset).where(Asset.symbol == symbol.upper()))
    ).scalars().first()
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset {symbol} not found")

    candles = (
        await db.execute(
            select(PriceCandle)
            .where(PriceCandle.asset_id == asset.id, PriceCandle.timeframe == "1d")
            .order_by(PriceCandle.timestamp.asc())
        )
    ).scalars().all()

    if len(candles) < 30:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient candle data for {symbol} (need >= 30, have {len(candles)})",
        )

    prices = [float(c.close) for c in candles]

    service = MomentumService()
    await service.initialize()
    result = await service.analyze({"ticker": symbol, "prices": prices})

    return {
        "status": "success",
        "symbol": asset.symbol,
        "name": asset.name,
        "market": asset.market,
        "data_points": len(candles),
        "momentum": result.get("momentum", {}),
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/volatility/{symbol}", response_model=dict)
async def volatility_analysis(
    symbol: str,
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """
    Volatility analysis for a stored symbol.
    
    Loads daily candles from the database and runs the VolatilityService.
    """
    asset = (
        await db.execute(select(Asset).where(Asset.symbol == symbol.upper()))
    ).scalars().first()
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset {symbol} not found")

    candles = (
        await db.execute(
            select(PriceCandle)
            .where(PriceCandle.asset_id == asset.id, PriceCandle.timeframe == "1d")
            .order_by(PriceCandle.timestamp.asc())
        )
    ).scalars().all()

    if len(candles) < 20:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient candle data for {symbol} (need >= 20, have {len(candles)})",
        )

    prices = [float(c.close) for c in candles]

    service = VolatilityService()
    await service.initialize()
    result = await service.analyze({"ticker": symbol, "prices": prices})

    return {
        "status": "success",
        "symbol": asset.symbol,
        "name": asset.name,
        "market": asset.market,
        "data_points": len(candles),
        "volatility": result.get("volatility", {}),
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.post("/scoring", response_model=dict)
async def scoring_analysis(
    data: dict = Body(...),
) -> dict:
    """
    Comprehensive 6D scoring for a ticker.
    
    Request body must include:
        ticker: str
        technical: dict (optional)
        fundamental: dict (optional)
        sentiment: dict (optional)
        momentum: dict (optional)
        risk: dict (optional)
        growth: dict (optional)
    """
    ticker = data.get("ticker", "UNKNOWN")

    service = ScoringService()
    await service.initialize()
    result = await service.analyze(data)

    return {
        "status": "success",
        "symbol": ticker,
        "scoring": result,
        "hierarchy": service.get_hierarchy_info(),
        "timestamp": datetime.utcnow().isoformat(),
    }
