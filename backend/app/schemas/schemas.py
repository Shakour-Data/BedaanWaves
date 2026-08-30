"""Pydantic Schemas for API"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Any, Dict
from datetime import datetime
from enum import Enum
from decimal import Decimal
import uuid


# Enums
class AssetClassEnum(str, Enum):
    EQUITY = "EQUITY"
    ETF = "ETF"
    CRYPTO = "CRYPTO"
    COMMODITY = "COMMODITY"
    BOND = "BOND"
    INDEX = "INDEX"


class MarketEnum(str, Enum):
    BINANCE = "BINANCE"
    KRAKEN = "KRAKEN"
    COINBASE = "COINBASE"
    NYSE = "NYSE"
    NASDAQ = "NASDAQ"
    TSE = "TSE"


class SignalTypeEnum(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    STRONG_BUY = "STRONG_BUY"
    STRONG_SELL = "STRONG_SELL"


class TimeframeEnum(str, Enum):
    ONE_MIN = "1m"
    FIVE_MIN = "5m"
    FIFTEEN_MIN = "15m"
    ONE_HOUR = "1h"
    FOUR_HOUR = "4h"
    ONE_DAY = "1d"
    ONE_WEEK = "1w"
    ONE_MONTH = "1M"


# Asset Schemas
class AssetBase(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    asset_class: AssetClassEnum
    market: MarketEnum
    sector: Optional[str] = None
    sub_sector: Optional[str] = None
    country_code: Optional[str] = None
    currency: str = "IRR"
    active: bool = True


class AssetCreate(AssetBase):
    pass


class AssetUpdate(BaseModel):
    name: Optional[str] = None
    sector: Optional[str] = None
    sub_sector: Optional[str] = None
    active: Optional[bool] = None


class AssetResponse(AssetBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Price Candle Schemas
class PriceCandleBase(BaseModel):
    timestamp: datetime
    timeframe: TimeframeEnum
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    turnover: Optional[Decimal] = None
    transactions: Optional[int] = None


class PriceCandleCreate(PriceCandleBase):
    asset_id: uuid.UUID
    source: str = "BRS"
    data_quality: str = "CONFIRMED"


class PriceCandleResponse(PriceCandleBase):
    id: uuid.UUID
    asset_id: uuid.UUID
    source: str
    data_quality: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# ML Signal Schemas
class MLSignalBase(BaseModel):
    signal_type: SignalTypeEnum
    confidence: Decimal = Field(..., ge=0, le=100)
    expected_return: Optional[Decimal] = None
    risk_score: Optional[Decimal] = None
    reasoning: Optional[str] = None


class MLSignalCreate(MLSignalBase):
    asset_id: uuid.UUID
    ml_model_version: str
    valid_until: datetime
    technical_factors: dict = {}
    fundamental_factors: dict = {}


class MLSignalResponse(MLSignalBase):
    id: uuid.UUID
    asset_id: uuid.UUID
    ml_model_version: str
    generated_at: datetime
    valid_until: datetime
    is_active: bool
    
    class Config:
        from_attributes = True


# Portfolio Schemas
class PortfolioBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    portfolio_type: str = "PERSONAL"
    base_currency: str = "IRR"


class PortfolioCreate(PortfolioBase):
    pass


class PortfolioUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    portfolio_type: Optional[str] = None


class PortfolioResponse(PortfolioBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Position Schemas
class PositionBase(BaseModel):
    quantity: Decimal = Field(..., gt=0)
    entry_price: Decimal = Field(..., gt=0)
    entry_date: datetime
    stop_loss: Optional[Decimal] = None
    take_profit: Optional[Decimal] = None
    notes: Optional[str] = None


class PositionCreate(PositionBase):
    asset_id: uuid.UUID


class PositionUpdate(BaseModel):
    quantity: Optional[Decimal] = None
    stop_loss: Optional[Decimal] = None
    take_profit: Optional[Decimal] = None
    notes: Optional[str] = None


class PositionResponse(PositionBase):
    id: uuid.UUID
    asset_id: uuid.UUID
    portfolio_id: uuid.UUID
    current_price: Optional[Decimal] = None
    current_value: Optional[Decimal] = None
    unrealized_pnl: Optional[Decimal] = None
    unrealized_pnl_pct: Optional[Decimal] = None
    
    class Config:
        from_attributes = True


# User Schemas
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    preferred_language: Optional[str] = None
    theme: Optional[str] = None


class UserResponse(UserBase):
    id: uuid.UUID
    is_active: bool
    is_admin: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# Response Models
class SuccessResponse(BaseModel):
    status: str = "success"
    data: Optional[dict] = None
    message: Optional[str] = None


class ErrorResponse(BaseModel):
    status: str = "error"
    error_code: str
    message: str
    details: Optional[dict] = None


class PaginationParams(BaseModel):
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)


class PaginatedResponse(BaseModel):
    data: List[dict]
    total: int
    skip: int
    limit: int
    
    class Config:
        from_attributes = True


# Market Data Schemas
class MarketDataResponse(BaseModel):
    symbol: str
    current_price: Decimal
    change_value: Decimal
    change_percent: Decimal
    high: Decimal
    low: Decimal
    volume: int
    timestamp: datetime


class PortfolioAnalysisResponse(BaseModel):
    total_value: Decimal
    total_cost: Decimal
    total_return: Decimal
    total_return_pct: Decimal
    allocation: dict
    metrics: dict
    positions_count: int


# Auth Schemas
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=3)
    full_name: Optional[str] = None


# Password Reset Schemas
class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetVerifyRequest(BaseModel):
    token: str


class PasswordResetVerifyResponse(BaseModel):
    valid: bool
    email_hint: Optional[str] = None


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)


class PasswordResetResponse(BaseModel):
    status: str = "success"
    message: str


# User Profile Schemas
class UserProfileUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    preferred_language: Optional[str] = None
    theme: Optional[str] = None
    notifications_enabled: Optional[bool] = None


# Watchlist Schemas
class WatchlistItemCreate(BaseModel):
    asset_id: uuid.UUID
    note: Optional[str] = None
    alert_threshold_pct: Optional[Decimal] = Field(None, ge=0, le=100)


class WatchlistItemResponse(BaseModel):
    id: uuid.UUID
    watchlist_id: uuid.UUID
    asset_id: uuid.UUID
    note: Optional[str] = None
    alert_threshold_pct: Optional[Decimal] = None
    created_at: datetime

    class Config:
        from_attributes = True


class WatchlistCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    is_default: bool = False


class WatchlistResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    description: Optional[str] = None
    is_default: bool
    items: List[WatchlistItemResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Notification Schemas
class NotificationResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    type: str
    title: str
    message: str
    channel: str
    priority: str
    read: bool
    metadata: dict = Field(default={}, validation_alias="extra", serialization_alias="metadata")
    created_at: datetime
    read_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        populate_by_name = True


# Preference Schemas
class PreferenceUpdate(BaseModel):
    value: Any


class PreferenceResponse(BaseModel):
    key: str
    value: Any


class FundamentalAnalysisRequest(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=50)
    financials: Optional[Dict[str, Any]] = Field(default=None)


class ScoringAnalysisRequest(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=50)
    fundamental: Optional[Dict[str, Any]] = None
    technical: Optional[Dict[str, Any]] = None
    sentiment: Optional[Dict[str, Any]] = None
    risk: Optional[Dict[str, Any]] = None
    macro: Optional[Dict[str, Any]] = None
    ai: Optional[Dict[str, Any]] = None
    growth: Optional[Dict[str, Any]] = Field(default=None, alias="growth")
    momentum: Optional[Dict[str, Any]] = Field(default=None, alias="momentum")

    class Config:
        populate_by_name = True


class RecommendationRequest(BaseModel):
    ticker: Optional[str] = None
    market: Optional[str] = None
    sector: Optional[str] = None
    asset_class: Optional[str] = None
    risk_tolerance: Optional[str] = None
    investment_horizon: Optional[int] = None
    budget: Optional[Decimal] = None


class OptimizeRequest(BaseModel):
    assets: List[Dict[str, Any]] = Field(..., min_length=1)
    risk_tolerance: Optional[str] = None
    target_return: Optional[Decimal] = None
    constraints: Optional[Dict[str, Any]] = None


class ForecastRequest(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=50)
    horizon: int = Field(default=30, ge=1, le=365)
    model: Optional[str] = None


class ScreenRequest(BaseModel):
    criteria: Dict[str, Any] = Field(default_factory=dict)
    universe: Optional[List[Dict[str, Any]]] = None
    market: Optional[str] = None


class CompareRequest(BaseModel):
    symbols: List[Dict[str, Any]] = Field(..., min_length=1)


class CorrelationRequest(BaseModel):
    returns_map: Dict[str, List[float]] = Field(..., min_length=1)
    high_threshold: float = Field(default=0.7, ge=-1, le=1)
    low_threshold: float = Field(default=-0.7, ge=-1, le=1)


class CalendarEventCreate(BaseModel):
    date: str = Field(..., description="ISO date (YYYY-MM-DD)")
    type: str = Field(..., min_length=1, max_length=50)
    title: str = Field(..., min_length=1, max_length=255)
    symbol: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


# ===========================================================================
# Real-Time Market Data Schemas (Live / Historical / Intraday)
# ===========================================================================

class RealtimeQuoteResponse(BaseModel):
    symbol: str
    current_price: float
    change_value: float
    change_percent: float
    open: float
    high: float
    low: float
    previous_close: float
    volume: int
    timestamp: datetime
    market_status: str
    freshness_label: str
    is_delayed: bool
    data_source: str
    adjusted_close: Optional[float] = None


class HistoricalCandleResponse(BaseModel):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    adjusted_close: float
    volume: int
    split_ratio: Optional[float] = None
    source: str = "yfinance"


class HistoricalDataResponse(BaseModel):
    symbol: str
    interval: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    candles: List[HistoricalCandleResponse]
    data_source: str
    fetched_at: datetime


class IntradayDataResponse(BaseModel):
    symbol: str
    interval: str
    candles: List[HistoricalCandleResponse]
    market_status: str
    freshness_label: str
    data_source: str
    fetched_at: datetime


class DataProviderHealthResponse(BaseModel):
    provider: str
    status: str
    last_successful_fetch: Optional[datetime] = None
    last_error: Optional[str] = None
    latency_ms: Optional[float] = None
    details: Optional[Dict[str, Any]] = None


