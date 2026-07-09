"""Database Models"""

from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, JSON, ForeignKey, BigInteger, Numeric, Index, UniqueConstraint, CheckConstraint, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.db.base import Base


class Asset(Base):
    """Asset/Symbol Information"""
    __tablename__ = "assets"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol = Column(String(50), nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=False)
    
    # Classification
    asset_class = Column(String(20), nullable=False, index=True)  # EQUITY, ETF, CRYPTO, etc.
    market = Column(String(20), nullable=False, index=True)  # TSE, OTC, BINANCE, etc.
    
    # Hierarchy
    sector = Column(String(100))
    sub_sector = Column(String(100))
    industry = Column(String(100))
    
    # Geographic
    country_code = Column(String(2))
    currency = Column(String(3), default="IRR")
    
    # Identifiers
    isin_code = Column(String(12))
    cusip_code = Column(String(9))
    
    # Status
    active = Column(Boolean, default=True, index=True)
    listing_date = Column(DateTime)
    delisting_date = Column(DateTime)
    
    # Metadata
    metadata = Column(JSONB, default={})
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    price_candles = relationship("PriceCandle", back_populates="asset", cascade="all, delete-orphan")
    ml_signals = relationship("MLSignal", back_populates="asset", cascade="all, delete-orphan")
    positions = relationship("Position", back_populates="asset", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_asset_active_market', 'active', 'market'),
        Index('idx_asset_sector', 'sector'),
    )


class PriceCandle(Base):
    """OHLCV Price Data"""
    __tablename__ = "price_candles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    timeframe = Column(String(10), nullable=False)  # 1m, 5m, 1h, 1d, etc.
    
    # OHLC
    open = Column(Numeric(20, 8), nullable=False)
    high = Column(Numeric(20, 8), nullable=False)
    low = Column(Numeric(20, 8), nullable=False)
    close = Column(Numeric(20, 8), nullable=False)
    
    # Volume
    volume = Column(BigInteger, nullable=False)
    turnover = Column(Numeric(25, 2))
    transactions = Column(Integer)
    
    # Adjusted
    adjusted_close = Column(Numeric(20, 8))
    split_ratio = Column(Numeric(10, 4), default=1.0)
    
    # Quality
    source = Column(String(20), nullable=False)
    data_quality = Column(String(10), default="CONFIRMED")  # CONFIRMED, PROVISIONAL
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    asset = relationship("Asset", back_populates="price_candles")
    
    __table_args__ = (
        UniqueConstraint('asset_id', 'timestamp', 'timeframe', name='uix_price_asset_timestamp'),
        Index('idx_price_asset_timestamp', 'asset_id', 'timestamp'),
        Index('idx_price_timeframe', 'timeframe', 'timestamp'),
        CheckConstraint('high >= open AND high >= close', name='chk_high_values'),
        CheckConstraint('low <= open AND low <= close', name='chk_low_values'),
    )


class MLSignal(Base):
    """ML-Generated Trading Signals"""
    __tablename__ = "ml_signals"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False, index=True)
    
    # Signal Details
    signal_type = Column(String(20), nullable=False)  # BUY, SELL, HOLD, etc.
    confidence = Column(Numeric(5, 2), nullable=False)  # 0-100
    
    # Performance Metrics
    expected_return = Column(Numeric(8, 2))
    expected_volatility = Column(Numeric(8, 2))
    risk_score = Column(Numeric(5, 2))  # 0-100
    
    # Analysis
    reasoning = Column(Text)
    technical_factors = Column(JSONB, default={})
    fundamental_factors = Column(JSONB, default={})
    sentiment_factors = Column(JSONB, default={})
    
    # Model Info
    ml_model_version = Column(String(50), nullable=False, index=True)
    model_name = Column(String(100))
    model_confidence = Column(Numeric(5, 2))
    
    # Validity
    generated_at = Column(DateTime, default=datetime.utcnow)
    valid_from = Column(DateTime, default=datetime.utcnow)
    valid_until = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    
    # Actual Performance
    actual_return = Column(Numeric(8, 2))
    win_rate = Column(Numeric(5, 2))
    
    # Relationships
    asset = relationship("Asset", back_populates="ml_signals")
    
    __table_args__ = (
        Index('idx_signal_active_generated', 'is_active', 'generated_at'),
        Index('idx_signal_model', 'ml_model_version'),
    )


class Portfolio(Base):
    """User Portfolio"""
    __tablename__ = "portfolios"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Details
    name = Column(String(255), nullable=False)
    description = Column(Text)
    portfolio_type = Column(String(20), default="PERSONAL")  # PERSONAL, WATCHLIST, PAPER_TRADING
    
    # Settings
    base_currency = Column(String(3), default="IRR")
    rebalance_frequency = Column(String(20))
    target_allocation = Column(JSONB, default={})
    
    # Visibility
    is_public = Column(Boolean, default=False)
    public_token = Column(String(50))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    positions = relationship("Position", back_populates="portfolio", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_portfolio_user', 'user_id'),
        UniqueConstraint('user_id', 'name', name='uix_portfolio_user_name'),
    )


class Position(Base):
    """Portfolio Position"""
    __tablename__ = "positions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id"), nullable=False, index=True)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False)
    
    # Position Details
    quantity = Column(Numeric(20, 8), nullable=False)
    entry_price = Column(Numeric(20, 8), nullable=False)
    entry_date = Column(DateTime, nullable=False)
    
    # Current Status
    current_price = Column(Numeric(20, 8))
    current_value = Column(Numeric(25, 2))
    unrealized_pnl = Column(Numeric(25, 2))
    unrealized_pnl_pct = Column(Numeric(8, 2))
    
    # Exit Strategy
    stop_loss = Column(Numeric(20, 8))
    take_profit = Column(Numeric(20, 8))
    
    # Notes
    notes = Column(Text)
    tags = Column(JSONB, default=[])
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="positions")
    asset = relationship("Asset", back_populates="positions")
    
    __table_args__ = (
        UniqueConstraint('portfolio_id', 'asset_id', name='uix_portfolio_asset'),
        CheckConstraint('quantity > 0', name='chk_positive_quantity'),
    )


class User(Base):
    """User Account"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(100), nullable=False, unique=True, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    
    # Profile
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    
    # Preferences
    preferred_language = Column(String(10), default="fa")
    theme = Column(String(20), default="light")
    notifications_enabled = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)


class Alert(Base):
    """User Alert Configuration"""
    __tablename__ = "alerts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"))
    
    # Configuration
    alert_type = Column(String(20), nullable=False)  # PRICE, SIGNAL, NEWS, etc.
    condition = Column(JSONB, nullable=False)
    threshold_value = Column(Numeric(20, 8))
    threshold_direction = Column(String(10))  # ABOVE, BELOW, BETWEEN, etc.
    
    # Notification
    notification_channel = Column(String(20))  # EMAIL, SMS, PUSH, WEBHOOK
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    triggered_at = Column(DateTime)
    triggered_count = Column(Integer, default=0)


class APILog(Base):
    """API Request Log for Monitoring"""
    __tablename__ = "api_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True))
    endpoint = Column(String(255), nullable=False, index=True)
    method = Column(String(10), nullable=False)
    status_code = Column(Integer)
    response_time_ms = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index('idx_log_endpoint', 'endpoint'),
        Index('idx_log_timestamp', 'created_at'),
    )
