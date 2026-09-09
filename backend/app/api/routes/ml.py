"""ML Routes"""

import logging
from datetime import UTC

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.utils import utc_now_iso
from app.db.base import get_async_session
from app.models.models import Asset, candle_model_for_market
from app.schemas.schemas import (
    MLAnomalyResponse,
    MLForecastResponse,
    MLOptimizeResponse,
    MLPatternsResponse,
    MLPredictResponse,
)
from app.services.ml.anomaly_detection_service import AnomalyDetectionService
from app.services.ml.pattern_recognition_service import PatternRecognitionService
from app.services.ml.portfolio_optimization_service import PortfolioOptimizationService
from app.services.ml.prediction_service import PredictionService
from app.services.ml.time_series_forecasting_service import TimeSeriesForecastingService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["ml"])


def _load_service(svc_cls):
    svc = svc_cls()
    return svc


@router.get("/predict/{symbol}", response_model=MLPredictResponse)
async def predict(
    symbol: str,
    horizon: int = Query(1, ge=1, le=30),
    db: AsyncSession = Depends(get_async_session),
) -> MLPredictResponse:
    """
    Predict future price movement for a symbol using ML models.

    Requires at least 10 daily candles. Returns the model's prediction
    along with metadata for the requested horizon.
    """
    asset = (await db.execute(select(Asset).where(func.lower(Asset.symbol) == func.lower(symbol)))).scalars().first()
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset {symbol} not found")
    candles = (await db.execute(select(candle_model_for_market(asset.market)).where(candle_model_for_market(asset.market).asset_id == asset.id, candle_model_for_market(asset.market).timeframe == "1d").order_by(candle_model_for_market(asset.market).timestamp.asc()))).scalars().all()
    if len(candles) < 10:
        raise HTTPException(status_code=400, detail="Insufficient candle data")
    prices = [float(c.close) for c in candles]
    service = _load_service(PredictionService)
    await service.initialize()
    result = await service.predict({"ticker": symbol, "prices": prices, "horizon": horizon})
    return {
        "status": "success",
        "symbol": symbol,
        "prediction": result,
        "timestamp": utc_now_iso(),
    }


@router.get("/patterns/{symbol}", response_model=MLPatternsResponse)
async def patterns(symbol: str, db: AsyncSession = Depends(get_async_session)) -> MLPatternsResponse:
    """
    Detect recurring chart patterns for a symbol.

    Requires at least 20 daily candles. Returns identified patterns
    with confidence scores and occurrence counts.
    """
    asset = (await db.execute(select(Asset).where(func.lower(Asset.symbol) == func.lower(symbol)))).scalars().first()
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset {symbol} not found")
    candles = (await db.execute(select(candle_model_for_market(asset.market)).where(candle_model_for_market(asset.market).asset_id == asset.id, candle_model_for_market(asset.market).timeframe == "1d").order_by(candle_model_for_market(asset.market).timestamp.asc()))).scalars().all()
    if len(candles) < 20:
        raise HTTPException(status_code=400, detail="Insufficient candle data")
    prices = [float(c.close) for c in candles]
    service = _load_service(PatternRecognitionService)
    await service.initialize()
    result = await service.detect_patterns(prices)
    return {
        "status": "success",
        "symbol": symbol,
        "patterns": result,
        "timestamp": utc_now_iso(),
    }


@router.get("/anomaly/{symbol}", response_model=MLAnomalyResponse)
async def anomaly(symbol: str, db: AsyncSession = Depends(get_async_session)) -> MLAnomalyResponse:
    """
    Detect price anomalies and outliers for a symbol.

    Requires at least 5 daily candles. Returns anomaly scores and
    detected outlier events.
    """
    asset = (await db.execute(select(Asset).where(func.lower(Asset.symbol) == func.lower(symbol)))).scalars().first()
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset {symbol} not found")
    candles = (await db.execute(select(candle_model_for_market(asset.market)).where(candle_model_for_market(asset.market).asset_id == asset.id, candle_model_for_market(asset.market).timeframe == "1d").order_by(candle_model_for_market(asset.market).timestamp.asc()))).scalars().all()
    if len(candles) < 5:
        raise HTTPException(status_code=400, detail="Insufficient candle data")
    prices = [float(c.close) for c in candles]
    returns = [(prices[i] - prices[i - 1]) / prices[i - 1] for i in range(1, len(prices))]
    service = _load_service(AnomalyDetectionService)
    await service.initialize()
    await service.train({"values": returns})
    result = await service.predict({"ticker": symbol, "prices": prices, "returns": returns})
    return {
        "status": "success",
        "symbol": symbol,
        "anomaly": result,
        "timestamp": utc_now_iso(),
    }


@router.post("/optimize", response_model=MLOptimizeResponse)
async def optimize(data: dict) -> MLOptimizeResponse:
    """
    Run portfolio optimization over provided assets.

    Body must include `assets` (list of asset dicts) and optional
    `risk_tolerance`, `target_return`, and `constraints`.
    """
    service = _load_service(PortfolioOptimizationService)
    await service.initialize()
    result = await service.predict(data)
    return {
        "status": "success",
        "result": result,
        "timestamp": utc_now_iso(),
    }


@router.post("/forecast", response_model=MLForecastResponse)
async def forecast(data: dict) -> MLForecastResponse:
    """
    Generate a time-series forecast for the provided ticker.

    Body should include `ticker` and optional `horizon` and `model` fields.
    """
    data.get("ticker", "UNKNOWN")
    service = _load_service(TimeSeriesForecastingService)
    await service.initialize()
    result = await service.predict(data)
    return {
        "status": "success",
        "forecast": result,
        "timestamp": utc_now_iso(),
    }
