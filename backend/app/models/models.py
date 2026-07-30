"""Database Models

طرح دیتابیس BedaanWaves:
- سه جدول کندل مجزا بر اساس بازار (ایران / بین‌الملل / رمزارز) به دلیل تقویم و
  ساعت کاری متفاوت و تایم‌فریم‌های متفاوت.
- جداول عمق بازار (مظنه برتر)، سهامداران عمده، شناور آزاد و جریان حقیقی/حقوقی
  اختصاصی بازار ایران.
- جداول بنیادی، خبری، ML و احراز هویت/امنیت.
"""

from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Boolean, JSON, ForeignKey,
    BigInteger, Numeric, Index, UniqueConstraint, CheckConstraint, Text, Date, Time,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, declared_attr
from datetime import datetime, date, timezone
import uuid

from app.db.base import Base


# ---------------------------------------------------------------------------
# دسته‌بندی بازارها (برای انتخاب جدول صحیح کندل / عمق بازار)
# ---------------------------------------------------------------------------
CRYPTO_MARKETS = {"BINANCE", "KRAKEN", "COINBASE"}
INTL_MARKETS = {"NYSE", "NASDAQ", "LSE", "XETRA", "FWB", "HKEX"}


# ===========================================================================
# 1. دارایی‌ها (Assets)
# ===========================================================================
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
    meta = Column("metadata", JSONB, default={})

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    ml_signals = relationship("MLSignal", back_populates="asset", cascade="all, delete-orphan")
    positions = relationship("Position", back_populates="asset", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_asset_active_market', 'active', 'market'),
        Index('idx_asset_sector', 'sector'),
    )


# ===========================================================================
# 2. کندل‌های قیمت — سه جدول مجزا بر اساس بازار
# ===========================================================================
class CandleMixin:
    """ستون‌های مشترک کندل‌های OHLCV (برای سه جدول مجزا)."""

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    timeframe = Column(String(10), nullable=False)  # 1h, 1d, 1w, 1M, 5m, 15m, 4h ...

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

    @declared_attr
    def asset(cls):
        return relationship("Asset")

    @declared_attr
    def __table_args__(cls):
        t = cls.__tablename__
        return (
            UniqueConstraint('asset_id', 'timestamp', 'timeframe', name=f'uix_{t}_asset_ts_tf'),
            Index(f'idx_{t}_asset_ts', 'asset_id', 'timestamp'),
            Index(f'idx_{t}_tf_ts', 'timeframe', 'timestamp'),
            CheckConstraint('high >= open AND high >= close AND high >= low', name=f'chk_{t}_high'),
            CheckConstraint('low <= open AND low <= close AND low <= high', name=f'chk_{t}_low'),
            CheckConstraint('volume >= 0', name=f'chk_{t}_volume_non_negative'),
            CheckConstraint('open >= 0 AND close >= 0', name=f'chk_{t}_price_non_negative'),
        )


class IRPriceCandle(CandleMixin, Base):
    """کندل‌های بازار ایران (TSE/فرابورس): 1h, 1d, 1w, 1M"""
    __tablename__ = "ir_price_candles"


class IntlPriceCandle(CandleMixin, Base):
    """کندل‌های بورس‌های خارج از ایران: 15m, 1h, 4h, 1d, 1w, 1M"""
    __tablename__ = "intl_price_candles"


class CryptoPriceCandle(CandleMixin, Base):
    """کندل‌های رمزارز (۲۴/۷): 5m, 15m, 1h, 4h, 1d, 1w, 1M"""
    __tablename__ = "crypto_price_candles"


def candle_model_for_market(market: str):
    """بازگرداندن مدل کندل مناسب بر اساس بازار."""
    if market in CRYPTO_MARKETS:
        return CryptoPriceCandle
    if market in INTL_MARKETS:
        return IntlPriceCandle
    return IRPriceCandle  # پیش‌فرض: بازار ایران (TSE/OTC)


# ===========================================================================
# 3. عمق بازار / مظنه برتر — هر ۱۵ دقیقه، ۵ مظنه برتر
# ===========================================================================
class OrderBookMixin:
    """ستون‌های مشترک عمق بازار (۵ سطح برتر)."""

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False, index=True)
    snapshot_time = Column(DateTime, nullable=False, index=True)
    rank = Column(Integer, nullable=False)  # 1..5 (بهترین مظنه)

    bid_price = Column(Numeric(20, 8))
    bid_volume = Column(BigInteger)
    ask_price = Column(Numeric(20, 8))
    ask_volume = Column(BigInteger)

    source = Column(String(20), default="BRS")

    @declared_attr
    def asset(cls):
        return relationship("Asset")

    @declared_attr
    def __table_args__(cls):
        t = cls.__tablename__
        return (
            UniqueConstraint('asset_id', 'snapshot_time', 'rank', name=f'uix_{t}_snap_rank'),
            Index(f'idx_{t}_asset_snap', 'asset_id', 'snapshot_time'),
        )


class IROrderBook(OrderBookMixin, Base):
    """عمق بازار بازار ایران (هر ۱۵ دقیقه، ۵ مظنه برتر)"""
    __tablename__ = "ir_order_book"


class IntlOrderBook(OrderBookMixin, Base):
    """عمق بازار بورس‌های خارجی (هر ۱۵ دقیقه، ۵ مظنه برتر)"""
    __tablename__ = "intl_order_book"


class CryptoOrderBook(OrderBookMixin, Base):
    """عمق بازار رمزارز (هر ۱۵ دقیقه، ۵ مظنه برتر)"""
    __tablename__ = "crypto_order_book"


def order_book_model_for_market(market: str):
    """بازگرداندن مدل عمق بازار مناسب بر اساس بازار."""
    if market in CRYPTO_MARKETS:
        return CryptoOrderBook
    if market in INTL_MARKETS:
        return IntlOrderBook
    return IROrderBook


# ===========================================================================
# 4. جداول اختصاصی بازار ایران
# ===========================================================================
class IRMajorShareholder(Base):
    """سهامداران عمده بازار ایران"""
    __tablename__ = "ir_major_shareholders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False, index=True)

    shareholder_name = Column(String(255), nullable=False)
    shareholder_type = Column(String(10), nullable=False)  # REAL / LEGAL
    rank = Column(Integer)

    share_count = Column(BigInteger)
    share_pct = Column(Numeric(8, 4))
    change_count = Column(BigInteger, default=0)
    change_pct = Column(Numeric(8, 4), default=0)

    report_date = Column(Date, nullable=False)
    source = Column(String(20), default="BRS")

    __table_args__ = (
        UniqueConstraint('asset_id', 'shareholder_name', 'report_date', name='uix_ir_shareholder'),
        Index('idx_ir_shareholder_asset', 'asset_id'),
    )


class IRFreeFloat(Base):
    """سهام شناور آزاد بازار ایران"""
    __tablename__ = "ir_free_float"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False, index=True)

    free_float_pct = Column(Numeric(8, 4))
    base_volume = Column(BigInteger)
    as_of_date = Column(Date, nullable=False)
    source = Column(String(20), default="BRS")

    __table_args__ = (
        UniqueConstraint('asset_id', 'as_of_date', name='uix_ir_free_float'),
        Index('idx_ir_free_float_asset', 'asset_id'),
    )


class IRRetailInstitutional(Base):
    """جریان حقیقی/حقوقی بازار ایران (هر ۱۵ دقیقه)"""
    __tablename__ = "ir_retail_institutional"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False, index=True)
    snapshot_time = Column(DateTime, nullable=False, index=True)

    retail_buy_volume = Column(BigInteger, default=0)
    retail_sell_volume = Column(BigInteger, default=0)
    institutional_buy_volume = Column(BigInteger, default=0)
    institutional_sell_volume = Column(BigInteger, default=0)

    net_flow = Column(Numeric(25, 2), default=0)  # (حقیقی خرید-فروش) - (حقوقی خرید-فروش)
    source = Column(String(20), default="BRS")

    __table_args__ = (
        UniqueConstraint('asset_id', 'snapshot_time', name='uix_ir_retail_inst'),
        Index('idx_ir_retail_inst_asset', 'asset_id'),
    )


# ===========================================================================
# 5. سیگنال‌های ML
# ===========================================================================
class MLSignal(Base):
    """ML-Generated Trading Signals"""
    __tablename__ = "ml_signals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False, index=True)

    signal_type = Column(String(20), nullable=False)  # BUY, SELL, HOLD, etc.
    confidence = Column(Numeric(5, 2), nullable=False)  # 0-100

    expected_return = Column(Numeric(8, 2))
    expected_volatility = Column(Numeric(8, 2))
    risk_score = Column(Numeric(5, 2))  # 0-100

    reasoning = Column(Text)
    technical_factors = Column(JSONB, default={})
    fundamental_factors = Column(JSONB, default={})
    sentiment_factors = Column(JSONB, default={})

    ml_model_version = Column(String(50), nullable=False, index=True)
    model_name = Column(String(100))
    model_confidence = Column(Numeric(5, 2))

    generated_at = Column(DateTime, default=datetime.utcnow)
    valid_from = Column(DateTime, default=datetime.utcnow)
    valid_until = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True, index=True)

    actual_return = Column(Numeric(8, 2))
    win_rate = Column(Numeric(5, 2))

    asset = relationship("Asset", back_populates="ml_signals")

    __table_args__ = (
        Index('idx_signal_active_generated', 'is_active', 'generated_at'),
        Index('idx_signal_model', 'ml_model_version'),
    )


# ===========================================================================
# 6. پورتفولیو و موضع‌ها
# ===========================================================================
class Portfolio(Base):
    """User Portfolio"""
    __tablename__ = "portfolios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    description = Column(Text)
    portfolio_type = Column(String(20), default="PERSONAL")  # PERSONAL, WATCHLIST, PAPER_TRADING

    base_currency = Column(String(3), default="IRR")
    rebalance_frequency = Column(String(20))
    target_allocation = Column(JSONB, default={})

    is_public = Column(Boolean, default=False)
    public_token = Column(String(50))

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

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

    quantity = Column(Numeric(20, 8), nullable=False)
    entry_price = Column(Numeric(20, 8), nullable=False)
    entry_date = Column(DateTime, nullable=False)

    current_price = Column(Numeric(20, 8))
    current_value = Column(Numeric(25, 2))
    unrealized_pnl = Column(Numeric(25, 2))
    unrealized_pnl_pct = Column(Numeric(8, 2))

    stop_loss = Column(Numeric(20, 8))
    take_profit = Column(Numeric(20, 8))

    notes = Column(Text)
    tags = Column(JSONB, default=[])

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    portfolio = relationship("Portfolio", back_populates="positions")
    asset = relationship("Asset", back_populates="positions")

    __table_args__ = (
        UniqueConstraint('portfolio_id', 'asset_id', name='uix_portfolio_asset'),
        CheckConstraint('quantity > 0', name='chk_positive_quantity'),
    )


# ===========================================================================
# 7. کاربران، احراز هویت و امنیت
# ===========================================================================
class User(Base):
    """User Account"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(100), nullable=False, unique=True, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    hashed_password = Column(String(255), nullable=False)

    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)

    preferred_language = Column(String(10), default="fa")
    theme = Column(String(20), default="light")
    notifications_enabled = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)


class RefreshToken(Base):
    """توکن‌های تازه‌سازی برای نشست‌های کاربر"""
    __tablename__ = "refresh_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    token_hash = Column(String(255), nullable=False, unique=True)
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(Boolean, default=False)
    user_agent = Column(String(512))
    ip_address = Column(String(64))

    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (Index('idx_refresh_user', 'user_id'),)


class AuditLog(Base):
    """لاگ تغییرات حساس (ورود، تغییر پورتفولیو، دسترسی ادمین)"""
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)

    action = Column(String(100), nullable=False)
    entity = Column(String(100))
    entity_id = Column(String(100))
    details = Column(JSONB, default={})
    ip_address = Column(String(64))

    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class Alert(Base):
    """User Alert Configuration"""
    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"))

    alert_type = Column(String(20), nullable=False)  # PRICE, SIGNAL, NEWS, etc.
    condition = Column(JSONB, nullable=False)
    threshold_value = Column(Numeric(20, 8))
    threshold_direction = Column(String(10))  # ABOVE, BELOW, BETWEEN, etc.

    notification_channel = Column(String(20))  # EMAIL, SMS, PUSH, WEBHOOK

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


# ===========================================================================
# 8. لیست نظارت، اعلان‌ها و ترجیحات
# ===========================================================================
class Watchlist(Base):
    """User watchlist (collection of watched assets)"""
    __tablename__ = "watchlists"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_default = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    items = relationship(
        "WatchlistItem",
        back_populates="watchlist",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (Index('idx_watchlist_user', 'user_id'),)


class WatchlistItem(Base):
    """A single asset entry within a watchlist"""
    __tablename__ = "watchlist_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    watchlist_id = Column(UUID(as_uuid=True), ForeignKey("watchlists.id"), nullable=False, index=True)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False, index=True)

    note = Column(Text, nullable=True)
    alert_threshold_pct = Column(Numeric(8, 4), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    watchlist = relationship("Watchlist", back_populates="items")

    __table_args__ = (
        UniqueConstraint('watchlist_id', 'asset_id', name='uix_watchlist_asset'),
    )


class Notification(Base):
    """In-app (and channel) notification for a user"""
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    type = Column(String(30), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)

    channel = Column(String(20), default="IN_APP")  # IN_APP, EMAIL, SMS, PUSH, WEBHOOK
    priority = Column(String(10), default="NORMAL")  # LOW, NORMAL, HIGH, CRITICAL

    read = Column(Boolean, default=False, index=True)
    extra = Column("metadata", JSONB, default={})

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    read_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index('idx_notification_user_read', 'user_id', 'read'),
    )


class UserPreference(Base):
    """Generic key/value user preference"""
    __tablename__ = "user_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    key = Column(String(100), nullable=False)
    value = Column(JSONB, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('user_id', 'key', name='uix_user_pref'),
    )


# ===========================================================================
# 9. تقویم معاملاتی، رویدادهای شرکتی و مرجع
# ===========================================================================
class MarketSession(Base):
    """تقویم و ساعت کاری هر بازار"""
    __tablename__ = "market_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    market = Column(String(20), nullable=False, index=True)
    session_date = Column(Date, nullable=False)

    is_open = Column(Boolean, default=True)
    open_time = Column(Time)
    close_time = Column(Time)
    note = Column(Text)

    __table_args__ = (
        UniqueConstraint('market', 'session_date', name='uix_market_session'),
    )


class CorporateEvent(Base):
    """رویدادهای شرکتی (مجامع، افزایش سرمایه، تقسیم سود، توقف نماد)"""
    __tablename__ = "corporate_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=True, index=True)

    event_type = Column(String(30), nullable=False)  # DIVIDEND, CAPITAL_INCREASE, AGM, SUSPENSION
    event_date = Column(Date, nullable=False, index=True)
    details = Column(JSONB, default={})
    description = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)


class Sector(Base):
    """درخت بخش/صنعت (برای تحلیل بخشی)"""
    __tablename__ = "sectors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(50), nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("sectors.id"), nullable=True, index=True)
    level = Column(Integer, default=0)

    parent = relationship("Sector", remote_side=[id])


class CurrencyRate(Base):
    """نرخ ارز برای تبدیل چندارزی"""
    __tablename__ = "currency_rates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    base_currency = Column(String(3), nullable=False)
    quote_currency = Column(String(3), nullable=False)
    rate = Column(Numeric(20, 8), nullable=False)
    rate_date = Column(Date, nullable=False, index=True)
    source = Column(String(20), default="ECB")

    __table_args__ = (
        UniqueConstraint('base_currency', 'quote_currency', 'rate_date', name='uix_currency_rate'),
    )


class MacroIndicator(Base):
    """شاخص‌های کلان اقتصادی (تورم، نرخ بهره، نفت و ...)"""
    __tablename__ = "macro_indicators"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    indicator_code = Column(String(50), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    value = Column(Numeric(20, 6))
    period = Column(String(20))  # 1402Q1 / 2024-01
    unit = Column(String(20))
    source = Column(String(50))
    as_of = Column(Date, index=True)


# ===========================================================================
# 10. داده‌های بنیادی بازار ایران
# ===========================================================================
class IRFinancialStatement(Base):
    """صورت‌های مالی بازار ایران (ترازنامه/سودزیان/جریان وجوه نقد)"""
    __tablename__ = "ir_financial_statements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False, index=True)

    period = Column(String(20), nullable=False)  # 1402Q1
    statement_type = Column(String(20), nullable=False)  # BALANCE / INCOME / CASHFLOW
    fiscal_year = Column(Integer)
    data = Column(JSONB, default={})  # سرفصل‌ها و مقادیر
    as_of = Column(Date)

    __table_args__ = (
        UniqueConstraint('asset_id', 'period', 'statement_type', name='uix_ir_fin_stmt'),
    )


class IRFundamentalRatio(Base):
    """نسبت‌های بنیادی بازار ایران (EPS, P/E, P/B, DPS, ROE و ...)"""
    __tablename__ = "ir_fundamental_ratios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False, index=True)

    period = Column(String(20), nullable=False)
    eps = Column(Numeric(20, 4))
    pe = Column(Numeric(12, 2))
    pb = Column(Numeric(12, 2))
    dps = Column(Numeric(20, 4))
    roe = Column(Numeric(8, 4))
    profit_margin = Column(Numeric(8, 4))
    market_cap = Column(Numeric(25, 2))
    book_value = Column(Numeric(20, 4))
    as_of = Column(Date)

    __table_args__ = (
        UniqueConstraint('asset_id', 'period', name='uix_ir_fund_ratio'),
    )


# ===========================================================================
# 11. خبر و NLP
# ===========================================================================
class News(Base):
    """آیتم‌های خبری"""
    __tablename__ = "news"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source = Column(String(100), nullable=False)
    title = Column(String(512), nullable=False)
    body = Column(Text)
    url = Column(String(1024))

    published_at = Column(DateTime, index=True)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=True, index=True)
    language = Column(String(5), default="fa")
    fetched_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (Index('idx_news_published', 'published_at'),)


class NewsSentiment(Base):
    """نتایج تحلیل احساسات (Sentimenet Analysis) خبرها"""
    __tablename__ = "news_sentiment"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    news_id = Column(UUID(as_uuid=True), ForeignKey("news.id"), nullable=False, index=True)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=True, index=True)

    sentiment_label = Column(String(20))  # POSITIVE / NEGATIVE / NEUTRAL
    sentiment_score = Column(Numeric(5, 2))
    model_version = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class NewsSummary(Base):
    """خلاصه‌های تولیدشده از خبرها"""
    __tablename__ = "news_summaries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    news_id = Column(UUID(as_uuid=True), ForeignKey("news.id"), nullable=False, index=True)
    summary_text = Column(Text)
    model_version = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)


# ===========================================================================
# 12. ML / پیش‌بینی / ناهنجاری
# ===========================================================================
class MLModel(Base):
    """نسخه‌ها و متادیتای مدل‌های ML"""
    __tablename__ = "ml_models"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    version = Column(String(50), nullable=False)
    model_type = Column(String(50))  # PREDICTION / PATTERN / ANOMALY / RECOMMEND
    trained_at = Column(DateTime, default=datetime.utcnow)
    metrics = Column(JSONB, default={})
    is_active = Column(Boolean, default=True)
    description = Column(Text)

    __table_args__ = (UniqueConstraint('name', 'version', name='uix_ml_model'),)


class MLPrediction(Base):
    """خروجی پیش‌بینی سری‌زمانی / مدل‌ها"""
    __tablename__ = "ml_predictions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False, index=True)
    model_id = Column(UUID(as_uuid=True), ForeignKey("ml_models.id"), nullable=True, index=True)

    model_version = Column(String(50), nullable=False)
    horizon = Column(String(20), nullable=False)  # 7d / 30d
    predicted_value = Column(Numeric(20, 8))
    lower_bound = Column(Numeric(20, 8))
    upper_bound = Column(Numeric(20, 8))
    confidence = Column(Numeric(5, 2))

    as_of = Column(DateTime, default=datetime.utcnow, index=True)
    target_date = Column(DateTime, nullable=False, index=True)

    __table_args__ = (Index('idx_ml_pred_asset_target', 'asset_id', 'target_date'),)


class Anomaly(Base):
    """نتایج تشخیص ناهنجاری"""
    __tablename__ = "anomalies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False, index=True)

    detected_at = Column(DateTime, default=datetime.utcnow, index=True)
    score = Column(Numeric(10, 4))
    anomaly_type = Column(String(50))  # PRICE_SPIKE / VOLUME_SURGE / ...
    description = Column(Text)
    severity = Column(String(20), default="LOW")  # LOW / MEDIUM / HIGH / CRITICAL

    __table_args__ = (Index('idx_anomaly_asset_detected', 'asset_id', 'detected_at'),)


# ===========================================================================
# 13. ذخیره نتایج تحلیل (Screening)
# ===========================================================================
class ScreeningResult(Base):
    """معیارها و خروجی فیلتر کردن (ScreeningService)"""
    __tablename__ = "screening_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)

    name = Column(String(255), nullable=False)
    criteria = Column(JSONB, default={})
    universe = Column(JSONB, default=[])
    result_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


# ===========================================================================
# 14. داده‌های خام بازار (Raw Market Data) — Crypto & International
# ===========================================================================
class RawMarketData(Base):
    """ذخیره داده‌های خام از سرویس‌های خارجی (Crypto, International)"""
    __tablename__ = "raw_market_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=True, index=True)

    # Symbol in raw form (e.g. "BTCUSD", "BTCUSDT", "ETHUSDT")
    raw_symbol = Column(String(50), nullable=False, index=True)

    # Market classification
    market = Column(String(20), nullable=False, index=True)  # CRYPTO, INTL
    exchange = Column(String(50))  # BINANCE, COINBASE, KRAKEN, NYSE, etc.

    # Data type
    data_type = Column(String(30), nullable=False, index=True)  # PRICE, VOLUME, DEPTH, ORDERBOOK

    # Raw payload (complete JSON from source)
    raw_payload = Column(JSONB, nullable=False)

    # Common fields extracted for convenience
    price = Column(Numeric(20, 8))
    volume = Column(Numeric(25, 2))
    quote_volume = Column(Numeric(25, 2))

    # Timestamp from source
    source_timestamp = Column(DateTime(timezone=True), nullable=False, index=True)

    # Ingestion metadata
    ingested_at = Column(DateTime(timezone=True), default=datetime.now(timezone=utc))
    updated_at = Column(DateTime(timezone=True), default=datetime.now(timezone=utc), onupdate=datetime.now(timezone=utc))
    ingestion_id = Column(String(100))  # idempotency key


    # Quality
    data_quality = Column(String(10), default="RAW")  # RAW, VALIDATED

    __table_args__ = (
        UniqueConstraint('raw_symbol', 'market', 'exchange', 'data_type', 'source_timestamp', name='uix_raw_market'),
        Index('idx_raw_asset', 'asset_id'),
        Index('idx_raw_market_type', 'market', 'data_type'),
        Index('idx_raw_ingested', 'ingested_at'),
        CheckConstraint("data_quality IN ('RAW', 'VALIDATED')", name='chk_raw_data_quality'),
        CheckConstraint("market IN ('CRYPTO', 'INTL', 'TSE')", name='chk_raw_market_type'),
        CheckConstraint('volume >= 0', name='chk_raw_volume_non_negative'),
    )


# ===========================================================================
# 15. اسنپ‌شات داده‌های پردازش‌شده (Market Data Snapshot)
# ===========================================================================
class MarketDataSnapshot(Base):
    """اسنپ‌شات پردازش‌شده داده‌های بازار — برای ML و تحلیل"""
    __tablename__ = "market_data_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False, index=True)

    # Snapshot time (UTC, aligned to interval)
    snapshot_time = Column(DateTime(timezone=True), nullable=False, index=True)

    # Interval (1m, 5m, 15m, 1h, 4h, 1d)
    interval = Column(String(10), nullable=False, index=True)

    # Price data
    open = Column(Numeric(20, 8))
    high = Column(Numeric(20, 8))
    low = Column(Numeric(20, 8))
    close = Column(Numeric(20, 8))
    volume = Column(Numeric(25, 2))
    turnover = Column(Numeric(25, 2))

    # Derived features (processed at snapshot time)
    rsi = Column(Numeric(8, 4))
    macd = Column(Numeric(20, 8))
    macd_signal = Column(Numeric(20, 8))
    macd_histogram = Column(Numeric(20, 8))
    bb_upper = Column(Numeric(20, 8))
    bb_middle = Column(Numeric(20, 8))
    bb_lower = Column(Numeric(20, 8))
    atr = Column(Numeric(20, 8))
    ma_7 = Column(Numeric(20, 8))
    ma_14 = Column(Numeric(20, 8))
    ma_30 = Column(Numeric(20, 8))
    volatility = Column(Numeric(20, 8))

    # Volume features
    volume_ma_7 = Column(Numeric(25, 2))
    volume_ratio = Column(Numeric(8, 4))  # current volume / volume_ma_7

    # ML features (JSONB for flexibility)
    ml_features = Column("features", JSONB, server_default=sa.text("'{}'::jsonb"))

    # Source
    source = Column(String(20), default="BRS")  # BRS, COINGECKO, BINANCE

    # Quality flag
    is_fresh = Column(Boolean, default=True, index=True)
    freshness_score = Column(Numeric(5, 2))  # 0-100

    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

    asset = relationship("Asset")

    __table_args__ = (
        UniqueConstraint('asset_id', 'snapshot_time', 'interval', name='uix_snapshot'),
        Index('idx_snapshot_fresh', 'asset_id', 'is_fresh', 'snapshot_time'),
        Index('idx_snapshot_interval', 'asset_id', 'interval', 'snapshot_time'),
        CheckConstraint('freshness_score >= 0 AND freshness_score <= 100', name='chk_freshness_score_range'),
        CheckConstraint('high >= low', name='chk_snapshot_high_low'),
        CheckConstraint('volume >= 0', name='chk_snapshot_volume_non_negative'),
    )


# ===========================================================================
# 16. سیگنال‌ها و پیش‌بینی‌های کریپتو (Crypto MLSignals)
# ===========================================================================
class CryptoMLSignal(Base):
    """ML سیگنال‌های مخصوص دارایی‌های کریپتو"""
    __tablename__ = "crypto_ml_signals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False, index=True)
    snapshot_id = Column(UUID(as_uuid=True), ForeignKey("market_data_snapshots.id"), nullable=True, index=True)

    signal_type = Column(String(20), nullable=False, index=True)  # BUY, SELL, HOLD, STRONG_BUY, STRONG_SELL
    confidence = Column(Numeric(5, 2), nullable=False)

    expected_return = Column(Numeric(8, 2))
    expected_volatility = Column(Numeric(8, 2))
    risk_score = Column(Numeric(5, 2))

    # Which model produced this signal
    model_name = Column(String(100))
    model_version = Column(String(50), index=True)

    # Features used
    features_used = Column(JSONB, default={})
    technical_indicators = Column(JSONB, default={})

    generated_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    valid_from = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    valid_until = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, default=True, index=True)

    asset = relationship("Asset")
    snapshot = relationship("MarketDataSnapshot")

    __table_args__ = (
        Index('idx_crypto_signal_active', 'asset_id', 'is_active', 'valid_until'),
        Index('idx_crypto_signal_model', 'model_version'),
    )


# ===========================================================================
# 17. Coefficient Learning Pipeline - Raw Performance Data
# ===========================================================================
class RawPerformanceScore(Base):
    """Raw performance data for ML coefficient learning.
    
    Stores dimension/sub-dimension/aspect/sub-aspect scores and market outcomes
    used to train hierarchical coefficient models.
    """
    __tablename__ = "raw_performance_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Timestamp when data was captured
    captured_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), index=True)
    
    # Asset reference
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=True, index=True)
    
    # Market classification (TSE, INTL, CRYPTO)
    market = Column(String(20), nullable=False, index=True)
    
    # Exchange identifier (TEHRAN_STOCK, NASDAQ, BINANCE, etc.)
    exchange = Column(String(50), nullable=False, index=True)
    
    # Performance context/metadata
    context = Column(JSONB, default={})  # Market regime, volatility regime, etc.
    
    # Dimension scores (from ScoringService)
    dimension_scores = Column(JSONB, nullable=False)  # {fundamental: 0.8, technical: 0.7, ...}
    sub_dimension_scores = Column(JSONB, nullable=False)  # {fundamental_price_history: 0.9, ...}
    aspect_scores = Column(JSONB, nullable=False)  # {fundamental_aspect_1: 0.85, ...}
    sub_aspect_scores = Column(JSONB, nullable=False)  # Detailed scores
    
    # Target performance metrics (future period returns)
    target_return = Column(Numeric(20, 8))  # Next period return
    target_volatility = Column(Numeric(10, 6))  # Future realized volatility
    target_sharpe = Column(Numeric(8, 4))  # Future Sharpe ratio
    
    # Market-specific target metrics
    target_price_change = Column(Numeric(10, 6))  # For all markets
    target_volume_change = Column(Numeric(10, 4))  # Volume change
    
    # Crypto-specific metrics
    target_bitcoin_correlation = Column(Numeric(8, 6))  # BTC correlation
    target_market_sentiment = Column(Numeric(5, 2))  # Market sentiment score
    
    # Data quality flags
    data_quality = Column(String(20), default="VALIDATED", 
                         comment="RAW, VALIDATED, CLEANED, EXCLUDED")
    validation_status = Column(String(20), default="PENDING")
    validation_notes = Column(Text)
    
    # Processing flags
    is_processed = Column(Boolean, default=False, index=True)
    processing_errors = Column(JSONB, default={})
    
    # Metadata
    ingestion_id = Column(String(100), index=True)
    source_system = Column(String(50), default="SCORING_SERVICE")
    
    __table_args__ = (
        UniqueConstraint('asset_id', 'captured_at', 'market', name='uix_raw_perf_unique',
                        deferrable=True),
        Index('idx_raw_perf_asset_time', 'asset_id', 'captured_at'),
        Index('idx_raw_perf_market', 'market', 'exchange'),
        Index('idx_raw_perf_captured', 'captured_at'),
        Index('idx_raw_perf_processed', 'is_processed'),
    )


class ProcessedFeatureData(Base):
    """Processed feature data for ML model training.
    
    Contains feature-engineered data ready for coefficient learning models.
    """
    __tablename__ = "processed_feature_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # References
    raw_data_id = Column(UUID(as_uuid=True), ForeignKey("raw_performance_scores.id"), nullable=False)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=True)
    
    # Processing timestamp
    processed_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), index=True)
    
    # Market info
    market = Column(String(20), nullable=False, index=True)
    exchange = Column(String(50), nullable=False)
    
    # Feature vector (L2-normalized, fixed length for model compatibility)
    feature_vector = Column(Array(Numeric(20, 8)), nullable=False)
    
    # Processed/restructured scores by hierarchy level
    dimension_features = Column(JSONB, nullable=False)  # Processed dimension scores
    sub_dimension_features = Column(JSONB, nullable=False)  # Processed sub-dimension features
    aspect_features = Column(JSONB, nullable=False)  # Processed aspect features
    sub_aspect_features = Column(JSONB, nullable=False)  # Processed sub-aspect features
    
    # Target values (what we're trying to predict)
    target_values = Column(JSONB, nullable=False)
    
    # Feature engineering metadata
    features_used = Column(JSONB, default={})  # Which features were selected
    preprocessing_steps = Column(JSONB, default={})  # Transformations applied
    normalization_params = Column(JSONB, default={})  # Mean, std, min, max used
    
    # Quality metrics
    is_valid = Column(Boolean, default=True, index=True)
    quality_score = Column(Numeric(5, 2), default=100.0)  # 0-100 quality rating
    validation_errors = Column(JSONB, default={})
    
    # Model metadata
    model_version = Column(String(50), default="v1.0.0")
    feature_schema_version = Column(String(20), default="1.0")
    
    __table_args__ = (
        UniqueConstraint('raw_data_id', 'processed_at', name='uix_processed_unique'),
        Index('idx_proc_asset_market', 'asset_id', 'market'),
        Index('idx_proc_feature_vector', 'feature_vector'),
        Index('idx_proc_valid', 'is_valid'),
        Index('idx_proc_processed_at', 'processed_at'),
    )


class CoefficientAdjustment(Base):
    """Tracks coefficient adjustments over time for audit and analysis."""
    __tablename__ = "coefficient_adjustments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Adjustment cycle/timestamp
    adjustment_cycle = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), index=True)
    
    # Asset context (nullable for global adjustments)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=True, index=True)
    
    # Hierarchy level
    level = Column(String(20), nullable=False, index=True)  # dimensions, sub_dimensions, aspects, sub_aspects
    
    # Feature key (name of the weight being adjusted)
    feature_key = Column(String(100), nullable=False)
    
    # Weight values
    old_weight = Column(Numeric(8, 6), nullable=False)
    new_weight = Column(Numeric(8, 6), nullable=False)
    weight_change = Column(Numeric(8, 6))  # new - old
    
    # Adjustment reason
    adjustment_code = Column(String(50), nullable=False)  # PERFORMANCE, DRIFT, MANUAL, etc.
    adjustment_reason = Column(Text)
    
    # Confidence in the adjustment
    confidence_score = Column(Numeric(5, 2), default=100.0)
    
    # Implementation details
    model_version = Column(String(50))
    training_samples = Column(Integer)
    performance_improvement = Column(Numeric(8, 6))
    
    # Metadata
    created_by = Column(String(50), default="system")
    implementation_version = Column(String(20), nullable=False)
    
    __table_args__ = (
        Index('idx_adj_cycle_level', 'adjustment_cycle', 'level'),
        Index('idx_adj_feature_key', 'feature_key'),
        Index('idx_adj_asset', 'asset_id'),
    )


class CoefficientHistory(Base):
    """Historical record of all coefficient changes for auditing."""
    __tablename__ = "coefficient_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Timestamp of coefficient state
    effective_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), index=True)
    
    # Asset context
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=True, index=True)
    
    # Market context
    market = Column(String(20), nullable=False)
    exchange = Column(String(50), nullable=False)
    
    # Complete coefficient snapshot
    coefficients = Column(JSONB, nullable=False)  # Full weight dictionary
    
    # Source
    source = Column(String(50), default="ML_TRAINING")  # ML_TRAINING, MANUAL, FALLBACK
    model_version = Column(String(50))
    
    # Validation
    is_valid = Column(Boolean, default=True)
    validation_notes = Column(Text)
    
    __table_args__ = (
        Index('idx_hist_asset_time', 'asset_id', 'effective_at'),
        Index('idx_hist_market', 'market'),
        Index('idx_hist_effective', 'effective_at'),
    )


# ===========================================================================
# 18. User Market Settings (Country/Index/Industry Selection)
# ===========================================================================
class UserMarketSetting(Base):
    """User market settings for country, index, and industry selection."""
    __tablename__ = "user_market_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Selection fields
    countries = Column(JSONB, default=[])
    indices = Column(JSONB, default=[])
    industries = Column(JSONB, default=[])
    regions = Column(JSONB, default=[])
    exchanges = Column(JSONB, default=[])
    currencies = Column(JSONB, default=[])

    # Metadata
    last_validated = Column(DateTime, default=datetime.utcnow)
    validation_hash = Column(String(64))
    is_default = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('user_id', name='uix_user_market_settings'),
        Index('idx_market_settings_user', 'user_id'),
    )


class UserMarketConfig(Base):
    """User market configuration for specific filtering scenarios."""
    __tablename__ = "user_market_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    config_name = Column(String(100), nullable=False)
    country = Column(String(50))
    country_indices = Column(JSONB, default=[])
    selected_industries = Column(JSONB, default=[])
    included_symbols = Column(JSONB, default=[])

    # Filters
    price_range = Column(JSONB)
    volume_range = Column(JSONB)
    change_filter = Column(JSONB)
    market_cap_filter = Column(JSONB)

    # Metadata
    last_calc = Column(DateTime, default=datetime.utcnow)
    is_default = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('user_id', 'config_name', name='uix_user_market_config'),
        Index('idx_market_config_user', 'user_id'),
    )


# ===========================================================================
# 19. User Crypto Settings (Custom Selection from Top 300)
# ===========================================================================
class UserCryptoSetting(Base):
    """User cryptocurrency settings for custom selection."""
    __tablename__ = "user_crypto_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Selection fields
    selected_cryptos = Column(JSONB, default=[])
    excluded_cryptos = Column(JSONB, default=[])
    custom_watchlist = Column(JSONB, default=[])

    # Exchange and filters
    exchange_source = Column(String(50), default="binance")
    min_volume_24h = Column(Numeric(20, 8), default=1000000)
    min_market_cap = Column(Numeric(20, 8), default=50000000)
    price_change_filter = Column(String(20), default="all")

    # Metadata
    last_validated = Column(DateTime, default=datetime.utcnow)
    validation_hash = Column(String(64))
    is_default = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('user_id', name='uix_user_crypto_settings'),
        Index('idx_crypto_settings_user', 'user_id'),
    )


class UserCryptoConfig(Base):
    """User crypto configuration for specific filtering scenarios."""
    __tablename__ = "user_crypto_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    config_name = Column(String(100), nullable=False)
    included_symbols = Column(JSONB, default=[])
    excluded_symbols = Column(JSONB, default=[])

    # Exchange and filters
    exchange_source = Column(String(50), default="binance")
    min_volume_24h = Column(Numeric(20, 8))
    min_market_cap = Column(Numeric(20, 8))
    price_range = Column(JSONB)
    change_filter = Column(JSONB)

    # Metadata
    last_calc = Column(DateTime, default=datetime.utcnow)
    is_default = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('user_id', 'config_name', name='uix_user_crypto_config'),
        Index('idx_crypto_config_user', 'user_id'),
    )


# ===========================================================================
# 20. User Filtered Scoring Results
# ===========================================================================
class UserScoringResult(Base):
    """Scoring results filtered by user preferences."""
    __tablename__ = "user_scoring_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    source = Column(String(100), nullable=False)
    symbol = Column(String(50), nullable=False)
    country = Column(String(50))
    industry = Column(String(50))
    exchange = Column(String(50))

    score = Column(Numeric(10, 6))
    rank = Column(Integer)
    data_date = Column(Date, nullable=False)

    criteria_scores = Column(JSONB)
    user_preferences = Column(JSONB)
    recommendations = Column(JSONB)
    metadata = Column(JSONB)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('user_id', 'symbol', 'data_date', name='uix_user_scoring'),
        Index('idx_scoring_user', 'user_id'),
        Index('idx_scoring_user_date', 'user_id', 'data_date'),
        Index('idx_scoring_user_rank', 'user_id', 'rank'),
    )


# ===========================================================================
# 21. Data Validation Records
# ===========================================================================
class ValidationRecord(Base):
    """Data validation record."""
    __tablename__ = "validation_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(String(100), nullable=False, index=True)
    validation_date = Column(DateTime, nullable=False, index=True)
    validation_type = Column(String(50), nullable=False)
    is_valid = Column(Boolean, nullable=False)
    details = Column(JSONB)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_validation_source', 'source_id'),
        Index('idx_validation_type', 'validation_type'),
    )


class SourceAuthenticity(Base):
    """Data source authenticity record."""
    __tablename__ = "source_authenticity"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_name = Column(String(100), nullable=False, index=True)
    authenticity_score = Column(Numeric(5, 2), nullable=False)
    verification_status = Column(String(50), nullable=False)
    verification_timestamp = Column(DateTime, nullable=False, index=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_authenticity_source', 'source_name'),
        Index('idx_authenticity_timestamp', 'verification_timestamp'),
    )


class CrossSourceConsistency(Base):
    """Cross-source consistency record."""
    __tablename__ = "cross_source_consistency"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_a_id = Column(String(100), nullable=False, index=True)
    source_b_id = Column(String(100), nullable=False, index=True)
    data_type = Column(String(50), nullable=False)
    consistency_metric = Column(Numeric(5, 2), nullable=False)
    validation_timestamp = Column(DateTime, nullable=False, index=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_consistency_sources', 'source_a_id', 'source_b_id'),
        Index('idx_consistency_timestamp', 'validation_timestamp'),
    )


# ===========================================================================
# 22. Data Sources Registry
# ===========================================================================
class DataSource(Base):
    """Data source registry."""
    __tablename__ = "data_sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_name = Column(String(100), nullable=False, unique=True)
    source_type = Column(String(50), nullable=False)
    base_url = Column(String(500))
    api_key_required = Column(Boolean, default=False)
    auth_token = Column(String(500))
    data_format = Column(String(50))
    last_verification = Column(DateTime)
    verification_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    metadata = Column(JSONB)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_datasource_type', 'source_type'),
        Index('idx_datasource_active', 'is_active'),
    )


# ===========================================================================
# 23. Historical Data Import Log
# ===========================================================================
class HistoricalDataImportLog(Base):
    """Historical data import log."""
    __tablename__ = "historical_data_import_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    import_batch_id = Column(String(100), nullable=False, index=True)
    source_id = Column(UUID(as_uuid=True), ForeignKey("data_sources.id"))
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    records_imported = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)
    validation_results = Column(JSONB)
    import_status = Column(String(50), default="pending")
    error_message = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_import_batch', 'import_batch_id'),
        Index('idx_import_status', 'import_status'),
    )


# ===========================================================================
# 24. Cryptocurrencies Master List
# ===========================================================================
class Cryptocurrency(Base):
    """Cryptocurrency master list."""
    __tablename__ = "cryptocurrencies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol = Column(String(20), nullable=False, unique=True, index=True)
    name = Column(String(200), nullable=False)
    exchange = Column(String(50))
    market_cap = Column(Numeric(20, 8))
    volume_24h = Column(Numeric(20, 8))
    price_usd = Column(Numeric(20, 8))
    price_change_24h = Column(Numeric(10, 6))
    price_change_7d = Column(Numeric(10, 6))
    market_cap_rank = Column(Integer)
    circulating_supply = Column(Numeric(20, 8))
    max_supply = Column(Numeric(20, 8))
    last_updated = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSONB)

    __table_args__ = (
        Index('idx_crypto_symbol', 'symbol'),
        Index('idx_crypto_market_cap_rank', 'market_cap_rank'),
        Index('idx_crypto_market_cap', 'market_cap'),
    )


# ===========================================================================
# 25. Countries List
# ===========================================================================
class Country(Base):
    """Countries list for market selection."""
    __tablename__ = "countries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)
    iso_code = Column(String(10), nullable=False, unique=True)
    stock_exchange = Column(String(100))
    currency_code = Column(String(10))
    timezone = Column(String(50))
    is_active = Column(Boolean, default=True)
    metadata = Column(JSONB)
    last_verified = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_country_code', 'iso_code'),
        Index('idx_country_active', 'is_active'),
    )


# ===========================================================================
# 26. Industries List
# ===========================================================================
class Industry(Base):
    """Industries list for sector filtering."""
    __tablename__ = "industries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)
    sector = Column(String(100))
    etf_ticker = Column(String(20))
    is_active = Column(Boolean, default=True)
    metadata = Column(JSONB)
    last_verified = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_industry_sector', 'sector'),
        Index('idx_industry_active', 'is_active'),
    )


# ===========================================================================
# 27. Market Indices
# ===========================================================================
class MarketIndex(Base):
    """Market indices for stock market tracking."""
    __tablename__ = "market_indices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol = Column(String(50), nullable=False, unique=True, index=True)
    name = Column(String(200), nullable=False)
    exchange = Column(String(100))
    country = Column(String(50))
    base_value = Column(Numeric(20, 8))
    current_value = Column(Numeric(20, 8))
    change_percent = Column(Numeric(10, 6))
    volume = Column(Numeric(18, 8))
    last_updated = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSONB)
    is_active = Column(Boolean, default=True)

    __table_args__ = (
        Index('idx_index_country', 'country'),
        Index('idx_index_exchange', 'exchange'),
        Index('idx_index_active', 'is_active'),
    )


# ===========================================================================
# 28. User Favorites
# ===========================================================================
class UserFavorite(Base):
    """User favorite assets."""
    __tablename__ = "user_favorites"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    source = Column(String(100), nullable=False)
    symbol = Column(String(50), nullable=False)
    category = Column(String(50))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('user_id', 'source', 'symbol', name='uix_user_favorite'),
        Index('idx_favorite_user', 'user_id'),
        Index('idx_favorite_category', 'category'),
    )


# ===========================================================================
# 29. User Alerts
# ===========================================================================
class UserAlert(Base):
    """User alert configuration."""
    __tablename__ = "user_alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    symbol = Column(String(50), nullable=False)
    alert_type = Column(String(50), nullable=False)
    alert_condition = Column(JSONB, nullable=False)
    is_active = Column(Boolean, default=True)
    notify_method = Column(JSONB, default={"email": True, "push": True, "sms": False})
    created_at = Column(DateTime, default=datetime.utcnow)
    last_triggered = Column(DateTime)

    __table_args__ = (
        Index('idx_alert_user', 'user_id'),
        Index('idx_alert_symbol', 'symbol'),
        Index('idx_alert_active', 'is_active'),
    )
