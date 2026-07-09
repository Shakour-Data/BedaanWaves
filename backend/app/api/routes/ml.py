"""ML Routes"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import logging

from app.db.base import get_async_session
from app.models.models import Asset, PriceCandle
from app.services.ml.prediction_service import PredictionService
from app.services.ml.pattern_recognition_service import PatternRecognitionService
from app.services.ml.anomaly_detection_service import AnomalyDetectionService
from app.services.ml.recommendation_service import RecommendationService
from app.services.ml.portfolio_optimization_service import PortfolioOptimizationService
from app.services.ml.time_series_forecasting_service import TimeSeriesForecastingService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ml", tags=["ml"])


def _load_service(svc_cls):
    svc = svc_cls()
    return svc


@router.get("/predict/{symbol}")
async def predict(symbol: str, horizon: int = Query(1, ge=1, le=30), db: AsyncSession = Depends(get_async_session)):
    asset = (await db.execute(select(Asset).where(Asset.symbol == symbol.upper()))).scalars().first()
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset {symbol} not found")
    candles = (await db.execute(select(PriceCandle).where(PriceCandle.asset_id == asset.id, PriceCandle.timeframe == "1d").order_by(PriceCandle.timestamp.asc()))).scalars().all()
    if len(candles) < 10:
        raise HTTPException(status_code=400, detail="Insufficient candle data")
    prices = [float(c.close) for c in candles]
    service = _load_service(PredictionService)
    await service.initialize()
    result = await service.predict({"ticker": symbol, "prices": prices, "horizon": horizon})
    return {"status": "success", "data": result}


@router.get("/patterns/{symbol}")
async def patterns(symbol: str, db: AsyncSession = Depends(get_async_session)):
    asset = (await db.execute(select(Asset).where(Asset.symbol == symbol.upper()))).scalars().first()
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset {symbol} not found")
    candles = (await db.execute(select(PriceCandle).where(PriceCandle.asset_id == asset.id, PriceCandle.timeframe == "1d").order_by(PriceCandle.timestamp.asc()))).scalars().all()
    if len(candles) < 20:
        raise HTTPException(status_code=400, detail="Insufficient candle data")
    prices = [float(c.close) for c in candles]
    service = _load_service(PatternRecognitionService)
    await service.initialize()
    result = await service.detect_patterns(prices)
    return {"status": "success", "symbol": symbol, "patterns": result}


@router.get("/anomaly/{symbol}")
async def anomaly(symbol: str, db: AsyncSession = Depends(get_async_session)):
    asset = (await db.execute(select(Asset).where(Asset.symbol == symbol.upper()))).scalars().first()
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset {symbol} not found")
    candles = (await db.execute(select(PriceCandle).where(PriceCandle.asset_id == asset.id, PriceCandle.timeframe == "1d").order_by(PriceCandle.timestamp.asc()))).scalars().all()
    if len(candles) < 5:
        raise HTTPException(status_code=400, detail="Insufficient candle data")
    prices = [float(c.close) for c in candles]
    returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
    service = _load_service(AnomalyDetectionService)
    await service.initialize()
    train = await service.train({"values": returns})
    result = await service.predict({"ticker": symbol, "prices": prices, "returns": returns})
    return {"status": "success", "data": result}


@router.post("/recommendation")
async def recommendation(data: dict):
    ticker = data.get("ticker", "UNKNOWN")
    service = _load_service(RecommendationService)
    await service.initialize()
    result = await service.predict(data)
    return {"status": "success", "data": result}


@router.post("/optimize")
async def optimize(data: dict):
    service = _load_service(PortfolioOptimizationService)
    await service.initialize()
    result = await service.predict(data)
    return {"status": "success", "data": result}


@router.post("/forecast")
async def forecast(data: dict):
    ticker = data.get("ticker", "UNKNOWN")
    service = _load_service(TimeSeriesForecastingService)
    await service.initialize()
    result = await service.predict(data)
    return {"status": "success", "data": result}
