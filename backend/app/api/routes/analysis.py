"""Analysis and Signals Routes"""

from fastapi import APIRouter, Depends, Query, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from datetime import datetime
from typing import List
import logging

from app.db.base import get_async_session
from app.models.models import Asset, MLSignal, candle_model_for_market
from app.schemas.schemas import MLSignalResponse, SignalTypeEnum
from app.services.analysis.technical_service import TechnicalAnalysisService
from app.services.analysis.risk_service import RiskAnalysisService
from app.services.analysis.fundamental_service import FundamentalAnalysisService
from app.services.analysis.momentum_service import MomentumService
from app.services.analysis.volatility_service import VolatilityService
from app.services.analysis.scoring_service import ScoringService
from app.services.analysis.crypto_fundamental_service import CryptoFundamentalAnalysisService
from app.services.data.financial_data_ingest_service import (
    FinancialDataIngestService,
    MarketType,
    FinancialStatementType,
)
from app.services.data.stock_fundamental_ingestion_service import StockFundamentalDataIngestionService
from app.core.rate_limiting import RateLimiter, rate_limit

logger = logging.getLogger(__name__)
router = APIRouter(tags=["analysis"])


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
    asset_query = select(Asset).where(func.lower(Asset.symbol) == func.lower(symbol))
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
    Candle = candle_model_for_market(market or "TSE")
    query = select(Asset, Candle).where(
        and_(
            Asset.active == True,
            Candle.timeframe == timeframe,
        )
    ).outerjoin(
        Candle,
        and_(
            Asset.id == Candle.asset_id,
            Candle.timestamp == (
                select(Candle.timestamp)
                .where(Candle.asset_id == Asset.id)
                .order_by(Candle.timestamp.desc())
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
    asset_query = select(Asset).where(func.lower(Asset.symbol) == func.lower(symbol))
    asset_result = await db.execute(asset_query)
    asset = asset_result.scalars().first()
    
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset {symbol} not found")
    
    # Calculate returns
    from datetime import timedelta
    start_date = datetime.utcnow() - timedelta(days=period_days)
    
    candle_query = (
        select(candle_model_for_market(asset.market))
        .where(
            and_(
                candle_model_for_market(asset.market).asset_id == asset.id,
                candle_model_for_market(asset.market).timeframe == "1d",
                candle_model_for_market(asset.market).timestamp >= start_date,
            )
        )
        .order_by(candle_model_for_market(asset.market).timestamp.asc())
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
    asset = (
        await db.execute(select(Asset).where(func.lower(Asset.symbol) == func.lower(symbol)))
    ).scalars().first()

    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset {symbol} not found")

    candles = (
        await db.execute(
            select(candle_model_for_market(asset.market))
            .where(candle_model_for_market(asset.market).asset_id == asset.id, candle_model_for_market(asset.market).timeframe == "1d")
            .order_by(candle_model_for_market(asset.market).timestamp.asc())
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
        await db.execute(select(Asset).where(func.lower(Asset.symbol) == func.lower(symbol)))
    ).scalars().first()

    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset {symbol} not found")

    candles = (
        await db.execute(
            select(candle_model_for_market(asset.market))
            .where(candle_model_for_market(asset.market).asset_id == asset.id, candle_model_for_market(asset.market).timeframe == "1d")
            .order_by(candle_model_for_market(asset.market).timestamp.asc())
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


@router.get("/fundamental/{symbol}", response_model=dict)
@rate_limit(limit=10, window=60)  # 10 requests per minute
async def fundamental_analysis(
    symbol: str,
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """
    Perform fundamental analysis for a ticker.
    
    Path parameter:
        symbol: Asset symbol (e.g., 'AAPL', 'MSFT', 'فملی')
    """
    # Look up asset by symbol
    asset_result = await db.execute(select(Asset).where(func.lower(Asset.symbol) == func.lower(symbol)))
    asset = asset_result.scalars().first()
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset {symbol} not found")
    
    # Determine market from asset data
    market_type = None
    if asset.market:
        try:
            market_type = MarketType(asset.market)
        except ValueError:
            market_type = MarketType.US  # fallback
    
    # Fetch financial data using FinancialDataIngestService
    financial_ingest_service = FinancialDataIngestService()
    await financial_ingest_service.initialize()
    
    try:
        # Get financial data for the asset
        financial_data = await financial_ingest_service.get_latest_fundamentals(
            asset_id=asset.symbol,
            market=market_type or MarketType.US,
        )
        financials = financial_data.get("financials", {})
        
        # Perform fundamental analysis
        service = FundamentalAnalysisService(data_ingest_service=financial_ingest_service)
        await service.initialize()
        result = await service.analyze({
            "ticker": symbol,
            "market": market_type.value if market_type else None,
            "financials": financials,
            "use_ingestion": False  # Already fetched above
        })
        
        return {
            "status": "success",
            "symbol": symbol,
            "fundamental": result,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    finally:
        await financial_ingest_service.shutdown()


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
        await db.execute(select(Asset).where(func.lower(Asset.symbol) == func.lower(symbol)))
    ).scalars().first()
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset {symbol} not found")

    candles = (
        await db.execute(
            select(candle_model_for_market(asset.market))
            .where(candle_model_for_market(asset.market).asset_id == asset.id, candle_model_for_market(asset.market).timeframe == "1d")
            .order_by(candle_model_for_market(asset.market).timestamp.asc())
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
        await db.execute(select(Asset).where(func.lower(Asset.symbol) == func.lower(symbol)))
    ).scalars().first()
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset {symbol} not found")

    candles = (
        await db.execute(
            select(candle_model_for_market(asset.market))
            .where(candle_model_for_market(asset.market).asset_id == asset.id, candle_model_for_market(asset.market).timeframe == "1d")
            .order_by(candle_model_for_market(asset.market).timestamp.asc())
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

    Input can provide either:
    - 6D keys: fundamental, technical, sentiment, risk, macro, ai

    OR the legacy names:
    - growth -> macro
    - momentum -> ai

    Request body must include:
        ticker: str
        technical: dict (optional)
        fundamental: dict (optional)
        sentiment: dict (optional)
        risk: dict (optional)
        macro: dict (optional)
        ai: dict (optional)

    Legacy compatibility:
        momentum: dict (optional) will be mapped to ai if ai is missing
        growth: dict (optional) will be mapped to macro if macro is missing
    """
    ticker = data.get("ticker", "UNKNOWN")

    # Map legacy keys to scoring dimensions so macro/ai are populated.
    data = dict(data)  # shallow copy to avoid mutating caller payload
    if "macro" not in data and "growth" in data:
        data["macro"] = data.get("growth")
    if "ai" not in data and "momentum" in data:
        data["ai"] = data.get("momentum")

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


@router.post("/scoring/rank", response_model=dict)
async def score_and_rank_stocks(
    data: dict = Body(...),
) -> dict:
    """
    Score and rank multiple stocks based on 6D criteria.
    
    Request body must include:
        stocks: List[Dict] - List of stock data objects, each containing:
            - ticker: str
            - technical: dict (optional)
            - fundamental: dict (optional)
            - sentiment: dict (optional)
            - risk: dict (optional)
            - macro: dict (optional)
            - ai: dict (optional)
        dimension: str (optional) - Specific dimension to rank by (fundamental, technical, sentiment, risk, macro, ai)
                     If not provided, ranks by overall score
        limit: int (optional, default: 10) - Number of top stocks to return
    
    Legacy compatibility:
        - growth: dict (optional) will be mapped to macro if macro is missing
        - momentum: dict (optional) will be mapped to ai if ai is missing
        
    Returns:
        List of scored and ranked stocks with their scores, grades, and hierarchy info
    """
    stocks_data = data.get("stocks", [])
    dimension = data.get("dimension")
    limit = data.get("limit", 10)
    
    if not stocks_data:
        raise HTTPException(status_code=400, detail="No stocks provided")
        
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 100")
    
    # Map legacy keys for each stock
    processed_stocks = []
    for stock_data in stocks_data:
        stock_data = dict(stock_data)  # shallow copy
        if "macro" not in stock_data and "growth" in stock_data:
            stock_data["macro"] = stock_data.get("growth")
        if "ai" not in stock_data and "momentum" in stock_data:
            stock_data["ai"] = stock_data.get("momentum")
        processed_stocks.append(stock_data)
    
    service = ScoringService()
    await service.initialize()
    ranked_stocks = await service.rank_stocks(processed_stocks, dimension=dimension, limit=limit)
    
    return {
        "status": "success",
        "count": len(ranked_stocks),
        "dimension": dimension or "overall_score",
        "limit": limit,
        "stocks": ranked_stocks,
        "hierarchy": service.get_hierarchy_info(),
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/fundamental/batch", response_model=dict)
@rate_limit(limit=5, window=60)  # 5 batch requests per minute
async def batch_fundamental_analysis(
    symbols: str = Query(..., description="Comma-separated list of symbols"),
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """
    Perform batch fundamental analysis for multiple symbols.
    
    Query parameter:
        symbols: Comma-separated list of stock symbols (e.g., 'AAPL,MSFT,GOOGL')
        
    Returns:
        Fundamental analysis results for each symbol
    """
    symbol_list = [s.strip() for s in symbols.split(",") if s.strip()]
    
    if len(symbol_list) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 symbols per batch request")
    
    results = {}
    errors = {}
    
    for symbol in symbol_list:
        try:
            asset_result = await db.execute(
                select(Asset).where(func.lower(Asset.symbol) == func.lower(symbol))
            )
            asset = asset_result.scalars().first()
            
            if not asset:
                errors[symbol] = f"Asset {symbol} not found"
                continue
            
            from app.services.data.stock_fundamental_ingestion_service import StockFundamentalDataIngestionService
            stock_service = StockFundamentalDataIngestionService()
            await stock_service.initialize()
            
            try:
                financial_data = await stock_service.fetch_financial_data(symbol)
                
                service = FundamentalAnalysisService()
                await service.initialize()
                result = await service.analyze({
                    "ticker": symbol,
                    "financials": financial_data
                })
                
                results[symbol] = {
                    "status": "success",
                    "fundamental": result,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            finally:
                await stock_service.shutdown()
                
        except Exception as exc:
            errors[symbol] = str(exc)
    
    return {
        "status": "success",
        "total_requested": len(symbol_list),
        "successful": len(results),
        "failed": len(errors),
        "results": results,
        "errors": errors,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/fundamental/crypto/{crypto_id}", response_model=dict)
async def crypto_fundamental_analysis(
    crypto_id: str,
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """
    Perform fundamental analysis for a cryptocurrency.
    
    Path parameter:
        crypto_id: CoinGecko crypto ID (e.g., 'bitcoin', 'ethereum')
        
    Returns:
        Fundamental analysis for the cryptocurrency
    """
    try:
        service = CryptoFundamentalAnalysisService()
        await service.initialize()
        result = await service.analyze({"ticker": crypto_id, "use_cache": True})
        
        return {
            "status": "success",
            "crypto_id": crypto_id,
            "fundamental": result,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.get("/fundamentals/health", response_model=dict)
async def fundamental_analysis_health() -> dict:
    """Health check for fundamental analysis services."""
    return {
        "status": "healthy",
        "services": {
            "fundamental_analysis": True,
            "crypto_fundamental": True,
            "stock_fundamental_ingestion": True,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }
