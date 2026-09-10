"""Pydantic Schemas for API"""

import re
import uuid
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, EmailStr, Field, field_validator


# Enums
# Only instruments that participate in the formation of the Nasdaq index
# are allowed. Crypto, forex, commodities, bonds, and non-Nasdaq equities
# (NYSE, etc.) are intentionally excluded.
class AssetClassEnum(StrEnum):
    EQUITY = "EQUITY"
    ETF = "ETF"


class MarketEnum(StrEnum):
    NASDAQ = "NASDAQ"


class ScoreTierEnum(StrEnum):
    STRONG = "STRONG"
    MODERATE = "MODERATE"
    WEAK = "WEAK"


class SignalTypeEnum(StrEnum):
    STRONG_BULLISH = "STRONG_BULLISH"
    BULLISH = "BULLISH"
    NEUTRAL = "NEUTRAL"
    BEARISH = "BEARISH"
    STRONG_BEARISH = "STRONG_BEARISH"


class TimeframeEnum(StrEnum):
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
    sector: str | None = None
    sub_sector: str | None = None
    country_code: str | None = None
    currency: str = "IRR"
    active: bool = True


class AssetCreate(AssetBase):
    pass


class AssetUpdate(BaseModel):
    name: str | None = None
    sector: str | None = None
    sub_sector: str | None = None
    active: bool | None = None


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
    turnover: Decimal | None = None
    transactions: int | None = None


class PriceCandleCreate(PriceCandleBase):
    asset_id: uuid.UUID
    source: str = "YFINANCE"
    data_quality: str = "CONFIRMED"


class PriceCandleResponse(PriceCandleBase):
    id: uuid.UUID
    asset_id: uuid.UUID
    source: str
    data_quality: str
    created_at: datetime

    class Config:
        from_attributes = True


# ML Signal Schemas (analytics only, no buy/sell/hold classification)
class MLSignalBase(BaseModel):
    confidence: Decimal = Field(..., ge=0, le=100)
    expected_return: Decimal | None = None
    risk_score: Decimal | None = None
    reasoning: str | None = None


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
    description: str | None = None
    portfolio_type: str = "PERSONAL"
    base_currency: str = "IRR"


class PortfolioCreate(PortfolioBase):
    pass


class PortfolioUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    portfolio_type: str | None = None


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
    stop_loss: Decimal | None = None
    take_profit: Decimal | None = None
    notes: str | None = None


class PositionCreate(PositionBase):
    asset_id: uuid.UUID


class PositionUpdate(BaseModel):
    quantity: Decimal | None = None
    stop_loss: Decimal | None = None
    take_profit: Decimal | None = None
    notes: str | None = None


class PositionResponse(PositionBase):
    id: uuid.UUID
    asset_id: uuid.UUID
    portfolio_id: uuid.UUID
    current_price: Decimal | None = None
    current_value: Decimal | None = None
    unrealized_pnl: Decimal | None = None
    unrealized_pnl_pct: Decimal | None = None

    class Config:
        from_attributes = True


# User Schemas
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    full_name: str | None = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = None
    preferred_language: str | None = None
    theme: str | None = None


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
    data: dict | None = None
    message: str | None = None


class ErrorResponse(BaseModel):
    status: str = "error"
    error_code: str
    message: str
    details: dict | None = None


class PaginationParams(BaseModel):
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)


class PaginatedResponse(BaseModel):
    data: list[dict]
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
    username: str | None = None
    user_id: str | None = None


class LoginRequest(BaseModel):
    username: str
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str | None = None

    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character")
        return v


# Password Reset Schemas
class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetVerifyRequest(BaseModel):
    token: str


class PasswordResetVerifyResponse(BaseModel):
    valid: bool
    email_hint: str | None = None


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)


class PasswordResetResponse(BaseModel):
    status: str = "success"
    message: str


# User Profile Schemas
class UserProfileUpdate(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = None
    preferred_language: str | None = None
    theme: str | None = None
    notifications_enabled: bool | None = None


# Watchlist Schemas
class WatchlistItemCreate(BaseModel):
    asset_id: uuid.UUID
    note: str | None = None
    alert_threshold_pct: Decimal | None = Field(None, ge=0, le=100)


class AssetSummary(BaseModel):
    symbol: str
    name: str
    market: str

    class Config:
        from_attributes = True


class WatchlistItemResponse(BaseModel):
    id: uuid.UUID
    watchlist_id: uuid.UUID
    asset_id: uuid.UUID
    note: str | None = None
    alert_threshold_pct: Decimal | None = None
    created_at: datetime
    asset: AssetSummary | None = None

    class Config:
        from_attributes = True


class WatchlistCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    is_default: bool = False


class WatchlistUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    is_default: bool | None = None


class WatchlistResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    description: str | None = None
    is_default: bool
    items: list[WatchlistItemResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WatchlistItemUpdate(BaseModel):
    note: str | None = None
    alert_threshold_pct: Decimal | None = Field(None, ge=0, le=100)


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
    read_at: datetime | None = None

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
    financials: dict[str, Any] | None = Field(default=None)


class ScoringAnalysisRequest(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=50)
    fundamental: dict[str, Any] | None = None
    technical: dict[str, Any] | None = None
    sentiment: dict[str, Any] | None = None
    risk: dict[str, Any] | None = None
    macro: dict[str, Any] | None = None
    ai: dict[str, Any] | None = None
    growth: dict[str, Any] | None = Field(default=None, alias="growth")
    momentum: dict[str, Any] | None = Field(default=None, alias="momentum")

    class Config:
        populate_by_name = True


class RecommendationRequest(BaseModel):
    ticker: str | None = None
    market: str | None = None
    sector: str | None = None
    asset_class: str | None = None
    risk_tolerance: str | None = None
    investment_horizon: int | None = None
    budget: Decimal | None = None


class OptimizeRequest(BaseModel):
    assets: list[dict[str, Any]] = Field(..., min_length=1)
    risk_tolerance: str | None = None
    target_return: Decimal | None = None
    constraints: dict[str, Any] | None = None


class ForecastRequest(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=50)
    horizon: int = Field(default=30, ge=1, le=365)
    model: str | None = None


class ScreenRequest(BaseModel):
    criteria: dict[str, Any] = Field(default_factory=dict)
    universe: list[dict[str, Any]] | None = None
    market: str | None = None


class CompareRequest(BaseModel):
    symbols: list[dict[str, Any]] = Field(..., min_length=1)


class CorrelationRequest(BaseModel):
    returns_map: dict[str, list[float]] = Field(..., min_length=1)
    high_threshold: float = Field(default=0.7, ge=-1, le=1)
    low_threshold: float = Field(default=-0.7, ge=-1, le=1)


class CalendarEventCreate(BaseModel):
    date: str = Field(..., description="ISO date (YYYY-MM-DD)")
    type: str = Field(..., min_length=1, max_length=50)
    title: str = Field(..., min_length=1, max_length=255)
    symbol: str | None = None
    description: str | None = None
    metadata: dict[str, Any] | None = None


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
    adjusted_close: float | None = None


class HistoricalCandleResponse(BaseModel):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    adjusted_close: float
    volume: int
    split_ratio: float | None = None
    source: str = "yfinance"


class HistoricalDataResponse(BaseModel):
    symbol: str
    interval: str
    start_date: datetime | None = None
    end_date: datetime | None = None
    candles: list[HistoricalCandleResponse]
    data_source: str
    fetched_at: datetime


class IntradayDataResponse(BaseModel):
    symbol: str
    interval: str
    candles: list[HistoricalCandleResponse]
    market_status: str
    freshness_label: str
    data_source: str
    fetched_at: datetime


class DataProviderHealthResponse(BaseModel):
    provider: str
    status: str
    last_successful_fetch: datetime | None = None
    last_error: str | None = None
    latency_ms: float | None = None
    details: dict[str, Any] | None = None


# Neark (نزدک) Index Response Schemas
class NearkConstituentResponse(BaseModel):
    symbol: str
    name: str
    sector: str | None = None
    asset_class: str
    market: str
    is_nerk_constituent: bool
    nerk_weight: Decimal | None = None
    active: bool


class NearkOverviewResponse(BaseModel):
    index: str
    exchange: str
    market_overview: dict[str, Any]
    constituents_count: int
    top_gainers: list[dict[str, Any]]
    top_losers: list[dict[str, Any]]
    avg_change_pct: float


class NearkMarketOverviewResponse(BaseModel):
    market: str
    total_symbols: int
    active_symbols: int
    currency: str
    timezone: str
    index: str
    last_updated: str


class NearkPriceHistoryResponse(BaseModel):
    symbol: str
    name: str
    market: str
    period: str
    count: int
    data: list[dict[str, Any]]


class TopPerformerResponse(BaseModel):
    symbol: str
    name: str
    change_percent: float
    current_price: float
    volume: int


class TopPerformersResponse(BaseModel):
    status: str = "success"
    timestamp: str
    data: list[TopPerformerResponse]


class RiskMetricsResponse(BaseModel):
    volatility: float
    sharpe_ratio: float
    var_95: float
    max_drawdown: float
    avg_return: float


class RiskAnalysisResponse(BaseModel):
    status: str = "success"
    symbol: str
    period_days: int
    metrics: RiskMetricsResponse
    timestamp: str


class TechnicalIndicatorsResponse(BaseModel):
    rsi: float | None = None
    macd: float | None = None
    macd_histogram: float | None = None
    bb_percent_b: float | None = None
    volume_ratio: float | None = None
    volatility: float | None = None
    momentum: float | None = None
    stoch_k: float | None = None
    atr: float | None = None
    price_vs_sma20: float | None = None
    price_vs_sma50: float | None = None


class TechnicalAnalysisResponse(BaseModel):
    status: str = "success"
    symbol: str
    name: str
    market: str
    data_points: int
    indicators: TechnicalIndicatorsResponse
    timestamp: str


class MomentumResponse(BaseModel):
    momentum: float | None = None
    rsi: float | None = None
    macd: float | None = None
    trend: str | None = None


class MomentumAnalysisResponse(BaseModel):
    status: str = "success"
    symbol: str
    name: str
    market: str
    data_points: int
    momentum: MomentumResponse
    timestamp: str


class VolatilityMetricsResponse(BaseModel):
    volatility: float | None = None
    atr: float | None = None
    beta: float | None = None
    std_dev: float | None = None


class VolatilityAnalysisResponse(BaseModel):
    status: str = "success"
    symbol: str
    name: str
    market: str
    data_points: int
    volatility: VolatilityMetricsResponse
    timestamp: str


class SentimentAnalysisResponse(BaseModel):
    status: str = "success"
    symbol: str
    sentiment: dict[str, Any]
    timestamp: str


class MacroIndicatorsResponse(BaseModel):
    indicators: dict[str, Any]
    count: int


class MacroForecastResponse(BaseModel):
    forecasts: dict[str, list[dict[str, Any]]]
    count: int


class ScoreHistoryResponse(BaseModel):
    status: str = "success"
    symbol: str
    history: list[dict[str, Any]]


class ScoringHierarchyResponse(BaseModel):
    status: str = "success"
    symbol: str
    hierarchy: dict[str, Any]


class ScoringCoefficientsResponse(BaseModel):
    status: str = "success"
    symbol: str
    coefficients: dict[str, Any]


class FundamentalAnalysisResponse(BaseModel):
    status: str = "success"
    symbol: str
    fundamental: dict[str, Any]
    timestamp: str


class BatchFundamentalResponse(BaseModel):
    status: str = "success"
    total_requested: int
    successful: int
    failed: int
    results: dict[str, Any]
    errors: dict[str, str]
    timestamp: str


class FundamentalHealthResponse(BaseModel):
    status: str = "healthy"
    services: dict[str, bool]
    timestamp: str


class ScoringRankResponse(BaseModel):
    status: str = "success"
    count: int
    dimension: str
    limit: int
    stocks: list[dict[str, Any]]
    hierarchy: dict[str, Any]
    timestamp: str


class ScoringResponse(BaseModel):
    status: str = "success"
    symbol: str
    scoring: dict[str, Any]
    hierarchy: dict[str, Any]
    timestamp: str


class StockSearchResponse(BaseModel):
    status: str = "success"
    query: str
    count: int
    data: list[dict[str, Any]]
    api_version: str
    timestamp: str


class StockDetailResponse(BaseModel):
    status: str = "success"
    ticker: str
    data: dict[str, Any]
    api_version: str
    timestamp: str
    deprecated: bool = False
    migrated_to: str | None = None


class BatchStocksResponse(BaseModel):
    status: str = "success"
    total: int
    successful: int
    failed: int
    data: dict[str, Any]
    api_version: str
    timestamp: str


class MarketSymbolsResponse(BaseModel):
    status: str = "success"
    data: list[dict[str, Any]]
    count: int
    timestamp: str


class LatestPricesResponse(BaseModel):
    status: str = "success"
    data: dict[str, Any]
    timestamp: str


class MarketOverviewResponse(BaseModel):
    status: str = "success"
    market: str
    data: dict[str, Any]
    timestamp: str


class NasdaqDashboardResponse(BaseModel):
    status: str = "success"
    data: dict[str, Any]
    timestamp: str


class IndicesResponse(BaseModel):
    status: str = "success"
    data: dict[str, Any]
    timestamp: str


class IndustryRankingResponse(BaseModel):
    status: str = "success"
    data: dict[str, Any]
    timestamp: str


class OrderBookResponse(BaseModel):
    status: str = "success"
    symbol: str
    data: dict[str, Any]
    timestamp: str


class OrderBookHistoryResponse(BaseModel):
    status: str = "success"
    symbol: str
    data: list[dict[str, Any]]
    count: int
    timestamp: str


class PriceHistoryResponse(BaseModel):
    status: str = "success"
    symbol: str
    data: list[dict[str, Any]]
    count: int
    timestamp: str


class MLPredictResponse(BaseModel):
    status: str = "success"
    symbol: str
    prediction: dict[str, Any]
    timestamp: str


class MLPatternsResponse(BaseModel):
    status: str = "success"
    symbol: str
    patterns: list[dict[str, Any]]
    timestamp: str


class MLAnomalyResponse(BaseModel):
    status: str = "success"
    symbol: str
    anomaly: dict[str, Any]
    timestamp: str


class MLOptimizeResponse(BaseModel):
    status: str = "success"
    result: dict[str, Any]
    timestamp: str


class MLForecastResponse(BaseModel):
    status: str = "success"
    forecast: dict[str, Any]
    timestamp: str


class NewsMarketResponse(BaseModel):
    status: str = "success"
    data: list[dict[str, Any]]
    count: int
    timestamp: str


class NewsTickerResponse(BaseModel):
    status: str = "success"
    symbol: str
    data: list[dict[str, Any]]
    count: int
    timestamp: str


class NewsSearchResponse(BaseModel):
    status: str = "success"
    query: str
    data: list[dict[str, Any]]
    count: int
    timestamp: str


class NewsCategoryResponse(BaseModel):
    status: str = "success"
    category: str
    data: list[dict[str, Any]]
    count: int
    timestamp: str


class NewsCategoriesResponse(BaseModel):
    status: str = "success"
    categories: list[str]
    count: int


class NewsRegionsResponse(BaseModel):
    status: str = "success"
    regions: list[str]
    count: int


class NewsMarketMovingResponse(BaseModel):
    status: str = "success"
    data: list[dict[str, Any]]
    count: int
    timestamp: str


class SectorSummaryResponse(BaseModel):
    status: str = "success"
    data: list[dict[str, Any]]
    timestamp: str


class ScreenResponse(BaseModel):
    status: str = "success"
    results: list[dict[str, Any]]
    count: int
    timestamp: str


class CompareStocksResponse(BaseModel):
    status: str = "success"
    data: dict[str, Any]
    timestamp: str


class CorrelationResponse(BaseModel):
    status: str = "success"
    correlation_matrix: dict[str, Any]
    timestamp: str


class CalendarMonthResponse(BaseModel):
    status: str = "success"
    year: int
    month: int
    events: list[dict[str, Any]]
    count: int


class CalendarEventResponse(BaseModel):
    status: str = "success"
    event: dict[str, Any]
    timestamp: str


class CalendarEventsResponse(BaseModel):
    status: str = "success"
    events: list[dict[str, Any]]
    count: int
    timestamp: str


class SymbolSearchResponse(BaseModel):
    status: str = "success"
    query: str
    data: list[dict[str, Any]]
    count: int
    timestamp: str


class ExchangesResponse(BaseModel):
    status: str = "success"
    exchanges: list[str]
    count: int


class MarketTypesResponse(BaseModel):
    status: str = "success"
    market_types: list[str]
    count: int


class SymbolDetailResponse(BaseModel):
    status: str = "success"
    symbol: str
    data: dict[str, Any]
    timestamp: str


class ExchangeCountResponse(BaseModel):
    status: str = "success"
    exchange: str
    count: int
    data: list[dict[str, Any]]
    timestamp: str


class MarketTypeCountResponse(BaseModel):
    status: str = "success"
    market_type: str
    count: int
    data: list[dict[str, Any]]
    timestamp: str


class StatsResponse(BaseModel):
    status: str = "success"
    stats: dict[str, Any]
    timestamp: str


class MarketPreferencesResponse(BaseModel):
    status: str = "success"
    preferences: dict[str, Any]
    timestamp: str


class RecentSearchesResponse(BaseModel):
    status: str = "success"
    searches: list[str]
    count: int
    timestamp: str


class RankingResponse(BaseModel):
    status: str = "success"
    data: list[dict[str, Any]]
    count: int
    timestamp: str


class AdvancedFilterResponse(BaseModel):
    status: str = "success"
    total: int
    limit: int
    offset: int
    results: list[dict[str, Any]]
    applied_filters: list[dict[str, Any]]
    execution_time_ms: float


class FilterFieldsResponse(BaseModel):
    status: str = "success"
    fields: list[dict[str, Any]]
    count: int


class LiveQuoteResponse(BaseModel):
    stream_key: str | None = None
    event: str | None = None
    data: dict[str, Any] | None = None
    sequence: int | None = None
    data_age_ms: float | None = None
    error: str | None = None
    timestamp: str | None = None


class LiveScoresResponse(BaseModel):
    stream_key: str | None = None
    event: str | None = None
    data: dict[str, Any] | None = None
    sequence: int | None = None
    data_age_ms: float | None = None
    error: str | None = None
    timestamp: str | None = None


class LiveNewsResponse(BaseModel):
    stream_key: str | None = None
    event: str | None = None
    data: dict[str, Any] | None = None
    sequence: int | None = None
    data_age_ms: float | None = None
    error: str | None = None
    timestamp: str | None = None


class LiveOrderbookResponse(BaseModel):
    stream_key: str | None = None
    event: str | None = None
    data: dict[str, Any] | None = None
    sequence: int | None = None
    data_age_ms: float | None = None
    error: str | None = None
    timestamp: str | None = None


class LiveMarketResponse(BaseModel):
    stream_key: str | None = None
    event: str | None = None
    data: dict[str, Any] | None = None
    sequence: int | None = None
    data_age_ms: float | None = None
    error: str | None = None
    timestamp: str | None = None


class AlertHistoryEntryResponse(BaseModel):
    id: str
    alert_id: str
    event_type: str
    timestamp: str
    details: dict[str, Any]


class AlertHistoryResponse(BaseModel):
    status: str = "success"
    history: list[AlertHistoryEntryResponse]
    count: int


class AlertStatsResponse(BaseModel):
    total: int
    active: int
    triggered: int
    by_type: dict[str, int]


class BulkCreateAlertsResponse(BaseModel):
    status: str = "success"
    created: list[dict[str, Any]]
    count: int
    errors: list[str] | None = None


class ForecastModelResponse(BaseModel):
    id: str
    name: str
    type: str
    accuracy: float
    last_trained: str
    status: str


class ForecastPerformanceResponse(BaseModel):
    model_id: str
    metrics: dict[str, Any]
    timestamp: str


class PriceForecastPoint(BaseModel):
    date: str
    predicted: float
    lower_ci: float
    upper_ci: float
    confidence: float


class PriceForecastResponse(BaseModel):
    status: str = "success"
    symbol: str
    horizon: int
    model: str
    points: list[PriceForecastPoint]
    timestamp: str


class TrendForecastResponse(BaseModel):
    status: str = "success"
    symbol: str
    trend: str
    confidence: float
    supporting_factors: list[str]
    timestamp: str


class BatchForecastResponse(BaseModel):
    status: str = "success"
    results: list[dict[str, Any]]
    count: int
    timestamp: str


class ModelPerformanceResponse(BaseModel):
    model_id: str
    metrics: dict[str, Any]
    timestamp: str


class BacktestResponse(BaseModel):
    status: str = "success"
    model_id: str
    results: dict[str, Any]
    timestamp: str


class PrivacyExportResponse(BaseModel):
    exported_at: str
    user: dict[str, Any]
    watchlists: list[dict[str, Any]]
    portfolios: list[dict[str, Any]]
    preferences: list[dict[str, Any]]
    notifications: list[dict[str, Any]]
    alerts: list[dict[str, Any]]
    market_settings: list[dict[str, Any]]
    audit_logs: list[dict[str, Any]]


class ConsentUpdate(BaseModel):
    consents: dict[str, bool]

