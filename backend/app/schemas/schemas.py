"""Pydantic Schemas for API"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
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
    TSE = "TSE"
    OTC = "OTC"
    BINANCE = "BINANCE"
    KRAKEN = "KRAKEN"
    COINBASE = "COINBASE"
    NYSE = "NYSE"
    NASDAQ = "NASDAQ"


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
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None

