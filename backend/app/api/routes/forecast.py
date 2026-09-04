"""Forecast API Router
---------------------------------------------------------------------------
API endpoints for forecasting stock prices and trends using ML models.

FEATURES:
- Price forecasting (ARIMA, LSTM, Prophet)
- Trend direction prediction (Up/Down/Sideways)
- Confidence intervals for predictions
- Multi-horizon forecasting (1d, 7d, 30d, 90d)
- Feature importance analysis
- Model performance metrics

USAGE:
- POST /api/v1/forecast/price - Price forecast for a symbol
- POST /api/v1/forecast/trend - Trend direction prediction
- POST /api/v1/forecast/batch - Batch forecast for multiple symbols
- GET /api/v1/forecast/models - List available models
- GET /api/v1/forecast/models/{model_id} - Get model details
- GET /api/v1/forecast/performance/{model_id} - Model performance metrics
- POST /api/v1/forecast/backtest - Backtest a forecasting model
"""

from typing import List, Optional, Literal
from datetime import datetime, timedelta
from enum import Enum
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field, validator

from ....core.config import get_settings
from ....services.ml.prediction_service import PredictionService
from ....services.ml.time_series_service import TimeSeriesService
from ....services.data.stock_service import StockService
from ....services.user.auth_service import get_current_user

router = APIRouter(prefix="/forecast", tags=["Forecast"])


# =============================================================================
# Enums and Types
# =============================================================================

class ForecastModel(str, Enum):
    """Available forecasting models"""
    ARIMA = "arima"                    # AutoRegressive Integrated Moving Average
    LSTM = "lstm"                      # Long Short-Term Memory neural network
    PROPHET = "prophet"                # Facebook Prophet
    XGBOOST = "xgboost"                # XGBoost regressor
    ENSEMBLE = "ensemble"              # Ensemble of multiple models


class ForecastHorizon(str, Enum):
    """Forecast time horizons"""
    ONE_DAY = "1d"
    THREE_DAYS = "3d"
    ONE_WEEK = "7d"
    TWO_WEEKS = "14d"
    ONE_MONTH = "30d"
    THREE_MONTHS = "90d"
    SIX_MONTHS = "180d"
    ONE_YEAR = "365d"


class TrendDirection(str, Enum):
    """Predicted trend direction"""
    UP = "up"
    DOWN = "down"
    SIDEWAYS = "sideways"
    VOLATILE = "volatile"


class ConfidenceLevel(float, Enum):
    """Confidence levels for predictions"""
    NINETY = 0.90
    NINETY_FIVE = 0.95
    NINETY_NINE = 0.99


# =============================================================================
# Request/Response Models
# =============================================================================

class ForecastFeatures(BaseModel):
    """Features to include in forecast"""
    technical_indicators: bool = Field(True, description="Include technical indicators")
    fundamental_data: bool = Field(True, description="Include fundamental metrics")
    sentiment_scores: bool = Field(True, description="Include sentiment scores")
    market_context: bool = Field(True, description="Include broader market data")
    sector_performance: bool = Field(False, description="Include sector performance")


class PriceForecastRequest(BaseModel):
    """Request for price forecasting"""
    symbol: str = Field(..., min_length=1, max_length=20, description="Stock symbol")
    model: ForecastModel = Field(ForecastModel.ENSEMBLE, description="Forecasting model")
    horizon: ForecastHorizon = Field(ForecastHorizon.ONE_WEEK, description="Forecast horizon")
    confidence_level: ConfidenceLevel = Field(ConfidenceLevel.NINETY_FIVE)
    include_history: bool = Field(True, description="Include historical data in response")
    features: ForecastFeatures = Field(default_factory=ForecastFeatures)
    
    @validator('symbol')
    def validate_symbol(cls, v):
        return v.upper().strip()


class PriceForecastPoint(BaseModel):
    """Single point in price forecast"""
    date: datetime
    predicted_price: float
    lower_bound: float
    upper_bound: float
    confidence: float


class HistoricalPoint(BaseModel):
    """Historical price point"""
    date: datetime
    price: float
    volume: Optional[int]


class ModelContribution(BaseModel):
    """Individual model contribution in ensemble"""
    model: str
    weight: float
    rmse: float
    mape: float


class FeatureImportance(BaseModel):
    """Feature importance in forecast"""
    feature: str
    importance: float
    category: str  # technical, fundamental, sentiment, etc.


class PriceForecastResponse(BaseModel):
    """Response for price forecast"""
    status: str
    symbol: str
    model: str
    horizon: str
    generated_at: datetime
    last_price: float
    last_updated: datetime
    
    # Forecast data
    forecast: List[PriceForecastPoint]
    historical: Optional[List[HistoricalPoint]]
    
    # Model performance
    model_accuracy: Optional[float]
    rmse: Optional[float]
    mape: Optional[float]
    
    # Ensemble details (if applicable)
    model_contributions: Optional[List[ModelContribution]]
    
    # Feature analysis
    feature_importance: Optional[List[FeatureImportance]]
    
    # Metadata
    data_points_used: int
    confidence_level: float


class TrendForecastRequest(BaseModel):
    """Request for trend direction forecasting"""
    symbol: str = Field(..., description="Stock symbol")
    model: ForecastModel = Field(ForecastModel.LSTM)
    horizon: ForecastHorizon = Field(ForecastHorizon.ONE_WEEK)
    confidence_threshold: float = Field(0.75, ge=0.5, le=0.99)


class TrendForecastResponse(BaseModel):
    """Response for trend forecast"""
    status: str
    symbol: str
    predicted_direction: TrendDirection
    confidence: float
    probability_up: float
    probability_down: float
    probability_sideways: float
    horizon: str
    key_drivers: List[str]
    generated_at: datetime


class BatchForecastRequest(BaseModel):
    """Request for batch forecasting multiple symbols"""
    symbols: List[str] = Field(..., min_items=1, max_items=20)
    model: ForecastModel = Field(ForecastModel.ENSEMBLE)
    horizon: ForecastHorizon = Field(ForecastHorizon.ONE_WEEK)
    include_history: bool = Field(False)


class BatchForecastResponse(BaseModel):
    """Response for batch forecast"""
    status: str
    total: int
    successful: int
    failed: int
    results: List[PriceForecastResponse]
    errors: List[dict]
    generated_at: datetime
    processing_time_ms: int


# =============================================================================
# API Endpoints
# =============================================================================

@router.post("/price", response_model=PriceForecastResponse)
async def forecast_price(
    request: PriceForecastRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    prediction_service: PredictionService = Depends(),
    cache_service: CacheService = Depends(),
):
    """
    Generate price forecast for a stock.
    
    Supports multiple forecasting models including:
    - ARIMA: Traditional time series model
    - LSTM: Deep learning approach
    - Prophet: Facebook's forecasting tool
    - XGBoost: Gradient boosting
    - Ensemble: Combination of all models
    
    Returns forecast with confidence intervals and model accuracy metrics.
    """
    try:
        # Check cache first
        cache_key = f"forecast:price:{request.symbol}:{request.model}:{request.horizon}"
        cached = await cache_service.get(cache_key)
        
        if cached and not request.include_history:
            return PriceForecastResponse(**cached)
        
        # Generate forecast
        forecast = await prediction_service.forecast_price(
            symbol=request.symbol,
            model=request.model,
            horizon=request.horizon,
            confidence_level=request.confidence_level,
            features=request.features,
        )
        
        # Cache the result
        await cache_service.set(
            cache_key,
            forecast.dict(),
            ttl=1800  # 30 minutes
        )
        
        return forecast
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/trend", response_model=TrendForecastResponse)
async def forecast_trend(
    request: TrendForecastRequest,
    current_user: dict = Depends(get_current_user),
    prediction_service: PredictionService = Depends(),
):
    """
    Predict trend direction for a stock.
    
    Uses LSTM model to predict:
    - Upward trend
    - Downward trend
    - Sideways movement
    - Volatile conditions
    
    Returns confidence scores for each direction.
    """
    try:
        forecast = await prediction_service.forecast_trend(
            symbol=request.symbol,
            model=request.model,
            horizon=request.horizon,
            confidence_threshold=request.confidence_threshold,
        )
        return forecast
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/batch", response_model=BatchForecastResponse)
async def batch_forecast(
    request: BatchForecastRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    prediction_service: PredictionService = Depends(),
):
    """
    Generate forecasts for multiple stocks in batch.
    
    Efficiently processes up to 20 symbols simultaneously.
    Returns aggregated results with success/failure breakdown.
    """
    try:
        import time
        start_time = time.time()
        
        results = await prediction_service.batch_forecast(
            symbols=request.symbols,
            model=request.model,
            horizon=request.horizon,
            include_history=request.include_history,
        )
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return BatchForecastResponse(
            status="success",
            total=len(request.symbols),
            successful=len([r for r in results if r.status == "success"]),
            failed=len([r for r in results if r.status == "error"]),
            results=[r for r in results if r.status == "success"],
            errors=[{"symbol": r.symbol, "error": r.error} for r in results if r.status == "error"],
            generated_at=datetime.utcnow(),
            processing_time_ms=processing_time,
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/models", response_model=List[dict])
async def list_models(
    current_user: dict = Depends(get_current_user),
):
    """
    List available forecasting models with descriptions.
    
    Returns details about each model including:
    - Use cases
    - Performance characteristics
    - Recommended scenarios
    """
    return [
        {
            "id": "arima",
            "name": "ARIMA",
            "description": "AutoRegressive Integrated Moving Average",
            "type": "statistical",
            "best_for": ["short_term", "stationary_data"],
            "strengths": ["interpretable", "fast", "good_for_linear_trends"],
            "weaknesses": ["limited_nonlinear", "requires_stationarity"],
            "recommended_horizon": ["1d", "7d"],
        },
        {
            "id": "lstm",
            "name": "LSTM",
            "description": "Long Short-Term Memory Neural Network",
            "type": "deep_learning",
            "best_for": ["long_term", "complex_patterns"],
            "strengths": ["captures_complex_patterns", "handles_nonlinearity", "good_for_sequences"],
            "weaknesses": ["requires_more_data", "slower_training", "black_box"],
            "recommended_horizon": ["7d", "30d", "90d"],
        },
        {
            "id": "prophet",
            "name": "Prophet",
            "description": "Facebook Prophet forecasting tool",
            "type": "additive_regression",
            "best_for": ["seasonal_data", "missing_data"],
            "strengths": ["handles_missing_data", "robust_to_outliers", "interpretable"],
            "weaknesses": ["limited_complex_patterns", "assumes_additive"],
            "recommended_horizon": ["30d", "90d", "180d"],
        },
        {
            "id": "xgboost",
            "name": "XGBoost",
            "description": "Extreme Gradient Boosting",
            "type": "gradient_boosting",
            "best_for": ["feature_rich_data", "tabular_data"],
            "strengths": ["handles_feature_importance", "fast_prediction", "regularized"],
            "weaknesses": ["requires_feature_engineering", "limited_sequential_patterns"],
            "recommended_horizon": ["1d", "7d"],
        },
        {
            "id": "ensemble",
            "name": "Ensemble",
            "description": "Weighted ensemble of all models",
            "type": "ensemble",
            "best_for": ["production", "robust_predictions"],
            "strengths": ["combines_strengths", "reduces_variance", "more_robust"],
            "weaknesses": ["more_complex", "slower", "harder_to_debug"],
            "recommended_horizon": ["1d", "7d", "30d", "90d"],
            "models_included": ["arima", "lstm", "prophet", "xgboost"],
        },
    ]


@router.get("/models/{model_id}", response_model=dict)
async def get_model_details(
    model_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Get detailed information about a specific forecasting model.
    
    Includes hyperparameters, performance metrics, and usage recommendations.
    """
    models = await list_models(current_user)
    
    for model in models:
        if model["id"] == model_id:
            # Add additional details
            model["hyperparameters"] = get_model_hyperparameters(model_id)
            model["training_requirements"] = get_model_training_requirements(model_id)
            model["inference_time_ms"] = get_model_inference_time(model_id)
            return model
    
    raise HTTPException(status_code=404, detail=f"Model {model_id} not found")


@router.get("/performance/{model_id}", response_model=dict)
async def get_model_performance(
    model_id: str,
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: dict = Depends(get_current_user),
    prediction_service: PredictionService = Depends(),
):
    """
    Get performance metrics for a forecasting model.
    
    Metrics include:
    - RMSE (Root Mean Square Error)
    - MAE (Mean Absolute Error)
    - MAPE (Mean Absolute Percentage Error)
    - Directional accuracy
    - Sharpe ratio of predictions
    """
    try:
        performance = await prediction_service.get_model_performance(
            model_id=model_id,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
        )
        
        return {
            "status": "success",
            "model_id": model_id,
            "symbol": symbol,
            "period": {
                "start": start_date,
                "end": end_date,
            },
            "metrics": performance,
            "generated_at": datetime.utcnow().isoformat(),
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/backtest", response_model=dict)
async def backtest_model(
    model_id: ForecastModel = Field(..., description="Model to backtest"),
    symbol: str = Field(..., description="Symbol to backtest on"),
    start_date: datetime = Field(..., description="Backtest start date"),
    end_date: datetime = Field(..., description="Backtest end date"),
    initial_capital: float = Field(10000.0, ge=1000, description="Initial capital for trading simulation"),
    position_size_pct: float = Field(0.1, ge=0.01, le=1.0, description="Position size as % of capital"),
    take_profit_pct: Optional[float] = Field(None, description="Take profit percentage"),
    stop_loss_pct: Optional[float] = Field(None, description="Stop loss percentage"),
    current_user: dict = Depends(get_current_user),
    prediction_service: PredictionService = Depends(),
):
    """
    Backtest a forecasting model with trading simulation.
    
    Simulates trading based on model predictions and calculates:
    - Total return
    - Sharpe ratio
    - Maximum drawdown
    - Win rate
    - Profit factor
    
    This helps evaluate the practical value of forecasting models.
    """
    try:
        backtest_result = await prediction_service.backtest_model(
            model_id=model_id,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            position_size_pct=position_size_pct,
            take_profit_pct=take_profit_pct,
            stop_loss_pct=stop_loss_pct,
        )
        
        return {
            "status": "success",
            "model_id": model_id,
            "symbol": symbol,
            "backtest_period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "trading_parameters": {
                "initial_capital": initial_capital,
                "position_size_pct": position_size_pct,
                "take_profit_pct": take_profit_pct,
                "stop_loss_pct": stop_loss_pct,
            },
            "results": backtest_result,
            "generated_at": datetime.utcnow().isoformat(),
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# Helper Functions
# =============================================================================

def get_model_hyperparameters(model_id: str) -> dict:
    """Get hyperparameters for a model"""
    hyperparameters = {
        "arima": {
            "p": "Auto-selected (0-5)",
            "d": "Auto-selected (0-2)",
            "q": "Auto-selected (0-5)",
            "seasonal": False,
            "auto_arima": True,
        },
        "lstm": {
            "layers": 3,
            "units_per_layer": [128, 64, 32],
            "dropout": 0.2,
            "sequence_length": 60,
            "learning_rate": 0.001,
            "batch_size": 32,
            "epochs": 100,
            "early_stopping_patience": 10,
        },
        "prophet": {
            "changepoint_prior_scale": 0.05,
            "seasonality_prior_scale": 10.0,
            "holidays_prior_scale": 10.0,
            "daily_seasonality": False,
            "weekly_seasonality": True,
            "yearly_seasonality": True,
        },
        "xgboost": {
            "n_estimators": 1000,
            "max_depth": 6,
            "learning_rate": 0.01,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "early_stopping_rounds": 50,
        },
        "ensemble": {
            "models": ["arima", "lstm", "prophet", "xgboost"],
            "weighting_method": "performance_based",
            "rebalancing_frequency": "weekly",
        },
    }
    
    return hyperparameters.get(model_id, {})


def get_model_training_requirements(model_id: str) -> dict:
    """Get training requirements for a model"""
    requirements = {
        "arima": {
            "min_data_points": 30,
            "recommended_data_points": 252,  # 1 year
            "training_time": "< 1 minute",
            "hardware_requirements": "CPU only",
        },
        "lstm": {
            "min_data_points": 252,
            "recommended_data_points": 1260,  # 5 years
            "training_time": "5-30 minutes",
            "hardware_requirements": "GPU recommended (can use CPU)",
        },
        "prophet": {
            "min_data_points": 30,
            "recommended_data_points": 730,  # 2 years
            "training_time": "< 2 minutes",
            "hardware_requirements": "CPU only",
        },
        "xgboost": {
            "min_data_points": 100,
            "recommended_data_points": 1000,
            "training_time": "1-5 minutes",
            "hardware_requirements": "CPU (GPU optional)",
        },
        "ensemble": {
            "min_data_points": 252,
            "recommended_data_points": 1260,
            "training_time": "15-60 minutes",
            "hardware_requirements": "GPU recommended",
        },
    }
    
    return requirements.get(model_id, {})


def get_model_inference_time(model_id: str) -> str:
    """Get typical inference time for a model"""
    inference_times = {
        "arima": "< 100ms",
        "lstm": "< 500ms",
        "prophet": "< 200ms",
        "xgboost": "< 50ms",
        "ensemble": "< 1s",
    }
    
    return inference_times.get(model_id, "< 1s")
