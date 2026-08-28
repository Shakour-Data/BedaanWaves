-- BedaanWaves Database Initialization Script
-- تهیه‌سازی پایگاه‌داده برای BedaanWaves
-- نگارش ۲: جداول کندل و عمق بازار به تفکیک بازار + جداول بنیادی/خبری/ML/امنیت

-- ===============================================
-- 1. Extension‌ها
-- ===============================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ===============================================
-- 2. جدول دارایی‌ها (Assets)
-- ===============================================
CREATE TABLE IF NOT EXISTS assets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    asset_class VARCHAR(20) NOT NULL,
    market VARCHAR(20) NOT NULL,
    sector VARCHAR(100),
    sub_sector VARCHAR(100),
    industry VARCHAR(100),
    country_code VARCHAR(2),
    currency VARCHAR(3) DEFAULT 'IRR',
    isin_code VARCHAR(12),
    cusip_code VARCHAR(9),
    active BOOLEAN DEFAULT TRUE,
    listing_date TIMESTAMP,
    delisting_date TIMESTAMP,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_assets_symbol ON assets(symbol);
CREATE INDEX IF NOT EXISTS idx_assets_active ON assets(active);
CREATE INDEX IF NOT EXISTS idx_assets_market ON assets(market);
CREATE INDEX IF NOT EXISTS idx_assets_active_market ON assets(active, market);
CREATE INDEX IF NOT EXISTS idx_assets_sector ON assets(sector);

-- ===============================================
-- 3. Price Candles — market-specific tables
-- Separate tables because International (NASDAQ/NYSE) and Crypto markets
-- have different trading calendars, hours, and timeframe granularity.
-- ===============================================

-- 3.1 International markets (NASDAQ/NYSE/LSE/etc): 15m, 1h, 4h, 1d, 1w, 1M
CREATE TABLE IF NOT EXISTS intl_price_candles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset_id UUID NOT NULL REFERENCES assets(id),
    timestamp TIMESTAMP NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    open NUMERIC(20, 8) NOT NULL,
    high NUMERIC(20, 8) NOT NULL,
    low NUMERIC(20, 8) NOT NULL,
    close NUMERIC(20, 8) NOT NULL,
    volume BIGINT NOT NULL,
    turnover NUMERIC(25, 2),
    transactions INTEGER,
    adjusted_close NUMERIC(20, 8),
    split_ratio NUMERIC(10, 4) DEFAULT 1.0,
    source VARCHAR(20) NOT NULL,
    data_quality VARCHAR(10) DEFAULT 'CONFIRMED',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(asset_id, timestamp, timeframe),
    CONSTRAINT chk_intl_high_values CHECK (high >= open AND high >= close),
    CONSTRAINT chk_intl_low_values CHECK (low <= open AND low <= close),
    CONSTRAINT chk_intl_volume CHECK (volume >= 0)
);
CREATE INDEX IF NOT EXISTS idx_intl_candle_asset ON intl_price_candles(asset_id);
CREATE INDEX IF NOT EXISTS idx_intl_candle_timestamp ON intl_price_candles(timestamp);
CREATE INDEX IF NOT EXISTS idx_intl_candle_asset_time ON intl_price_candles(asset_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_intl_candle_tf_ts ON intl_price_candles(timeframe, timestamp);
CREATE INDEX IF NOT EXISTS idx_intl_candle_asset_tftp ON intl_price_candles(asset_id, timeframe, timestamp);

-- 3.2 Crypto (24/7): 5m, 15m, 1h, 4h, 1d, 1w, 1M
CREATE TABLE IF NOT EXISTS crypto_price_candles (
    LIKE intl_price_candles INCLUDING ALL
);
CREATE INDEX IF NOT EXISTS idx_crypto_candle_asset ON crypto_price_candles(asset_id);
CREATE INDEX IF NOT EXISTS idx_crypto_candle_timestamp ON crypto_price_candles(timestamp);
CREATE INDEX IF NOT EXISTS idx_crypto_candle_tf_ts ON crypto_price_candles(timeframe, timestamp);

-- 3.3 Market Depth — 5 best levels (intl & crypto only)
CREATE TABLE IF NOT EXISTS intl_order_book (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset_id UUID NOT NULL REFERENCES assets(id),
    snapshot_time TIMESTAMP NOT NULL,
    rank INTEGER NOT NULL, -- 1..5 (best level)
    bid_price NUMERIC(20, 8),
    bid_volume BIGINT,
    ask_price NUMERIC(20, 8),
    ask_volume BIGINT,
    source VARCHAR(20) DEFAULT 'BINANCE',
    UNIQUE(asset_id, snapshot_time, rank)
);
CREATE INDEX IF NOT EXISTS idx_intl_orderbook_asset ON intl_order_book(asset_id);
CREATE INDEX IF NOT EXISTS idx_intl_orderbook_asset_snap ON intl_order_book(asset_id, snapshot_time);

CREATE TABLE IF NOT EXISTS crypto_order_book (LIKE intl_order_book INCLUDING ALL);

-- ===============================================
-- 6. سیگنال‌های ML
-- ===============================================
CREATE TABLE IF NOT EXISTS ml_signals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset_id UUID NOT NULL REFERENCES assets(id),
    signal_type VARCHAR(20) NOT NULL,
    confidence NUMERIC(5, 2) NOT NULL,
    expected_return NUMERIC(8, 2),
    expected_volatility NUMERIC(8, 2),
    risk_score NUMERIC(5, 2),
    reasoning TEXT,
    technical_factors JSONB DEFAULT '{}',
    fundamental_factors JSONB DEFAULT '{}',
    sentiment_factors JSONB DEFAULT '{}',
    ml_model_version VARCHAR(50) NOT NULL,
    model_name VARCHAR(100),
    model_confidence NUMERIC(5, 2),
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    valid_from TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    valid_until TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    actual_return NUMERIC(8, 2),
    win_rate NUMERIC(5, 2)
);
CREATE INDEX IF NOT EXISTS idx_signals_asset ON ml_signals(asset_id);
CREATE INDEX IF NOT EXISTS idx_signals_active ON ml_signals(is_active);
CREATE INDEX IF NOT EXISTS idx_signals_model ON ml_signals(ml_model_version);
CREATE INDEX IF NOT EXISTS idx_signals_active_gen ON ml_signals(is_active, generated_at);

-- ===============================================
-- 7. پورتفولیو و موضع‌ها
-- ===============================================
CREATE TABLE IF NOT EXISTS portfolios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    portfolio_type VARCHAR(20) DEFAULT 'PERSONAL',
    base_currency VARCHAR(3) DEFAULT 'IRR',
    rebalance_frequency VARCHAR(20),
    target_allocation JSONB DEFAULT '{}',
    is_public BOOLEAN DEFAULT FALSE,
    public_token VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, name)
);
CREATE INDEX IF NOT EXISTS idx_portfolios_user ON portfolios(user_id);

CREATE TABLE IF NOT EXISTS positions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    portfolio_id UUID NOT NULL REFERENCES portfolios(id),
    asset_id UUID NOT NULL REFERENCES assets(id),
    quantity NUMERIC(20, 8) NOT NULL,
    entry_price NUMERIC(20, 8) NOT NULL,
    entry_date TIMESTAMP NOT NULL,
    current_price NUMERIC(20, 8),
    current_value NUMERIC(25, 2),
    unrealized_pnl NUMERIC(25, 2),
    unrealized_pnl_pct NUMERIC(8, 2),
    stop_loss NUMERIC(20, 8),
    take_profit NUMERIC(20, 8),
    notes TEXT,
    tags JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(portfolio_id, asset_id),
    CONSTRAINT chk_positive_quantity CHECK (quantity > 0)
);
CREATE INDEX IF NOT EXISTS idx_positions_portfolio ON positions(portfolio_id);
CREATE INDEX IF NOT EXISTS idx_positions_asset ON positions(asset_id);

-- ===============================================
-- 8. کاربران، احراز هویت و امنیت
-- ===============================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    preferred_language VARCHAR(10) DEFAULT 'fa',
    theme VARCHAR(20) DEFAULT 'light',
    notifications_enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

CREATE TABLE IF NOT EXISTS refresh_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    token_hash VARCHAR(255) NOT NULL UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    revoked BOOLEAN DEFAULT FALSE,
    user_agent VARCHAR(512),
    ip_address VARCHAR(64),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_refresh_user ON refresh_tokens(user_id);

CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    entity VARCHAR(100),
    entity_id VARCHAR(100),
    details JSONB DEFAULT '{}',
    ip_address VARCHAR(64),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_logs(user_id);

CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    asset_id UUID REFERENCES assets(id),
    alert_type VARCHAR(20) NOT NULL,
    condition JSONB NOT NULL,
    threshold_value NUMERIC(20, 8),
    threshold_direction VARCHAR(10),
    notification_channel VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    triggered_at TIMESTAMP,
    triggered_count INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_alerts_user ON alerts(user_id);
CREATE INDEX IF NOT EXISTS idx_alerts_active ON alerts(is_active);

CREATE TABLE IF NOT EXISTS api_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID,
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INTEGER,
    response_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_logs_endpoint ON api_logs(endpoint);
CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON api_logs(created_at);

-- ===============================================
-- 9. لیست نظارت، اعلان‌ها و ترجیحات
-- ===============================================
CREATE TABLE IF NOT EXISTS watchlists (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_watchlist_user ON watchlists(user_id);

CREATE TABLE IF NOT EXISTS watchlist_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    watchlist_id UUID NOT NULL REFERENCES watchlists(id),
    asset_id UUID NOT NULL REFERENCES assets(id),
    note TEXT,
    alert_threshold_pct NUMERIC(8, 4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(watchlist_id, asset_id)
);
CREATE INDEX IF NOT EXISTS idx_watchlist_item_wl ON watchlist_items(watchlist_id);
CREATE INDEX IF NOT EXISTS idx_watchlist_item_asset ON watchlist_items(asset_id);

CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    type VARCHAR(30) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    channel VARCHAR(20) DEFAULT 'IN_APP',
    priority VARCHAR(10) DEFAULT 'NORMAL',
    read BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_notification_user ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notification_user_read ON notifications(user_id, read);

CREATE TABLE IF NOT EXISTS user_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    key VARCHAR(100) NOT NULL,
    value JSONB,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, key)
);
CREATE INDEX IF NOT EXISTS idx_user_pref_user ON user_preferences(user_id);

-- ===============================================
-- 10. تقویم معاملاتی، رویدادهای شرکتی و مرجع
-- ===============================================
CREATE TABLE IF NOT EXISTS market_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    market VARCHAR(20) NOT NULL,
    session_date DATE NOT NULL,
    is_open BOOLEAN DEFAULT TRUE,
    open_time TIME,
    close_time TIME,
    note TEXT,
    UNIQUE(market, session_date)
);
CREATE INDEX IF NOT EXISTS idx_market_session_market ON market_sessions(market);

CREATE TABLE IF NOT EXISTS corporate_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset_id UUID REFERENCES assets(id),
    event_type VARCHAR(30) NOT NULL,
    event_date DATE NOT NULL,
    details JSONB DEFAULT '{}',
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_corporate_event_asset ON corporate_events(asset_id);
CREATE INDEX IF NOT EXISTS idx_corporate_event_date ON corporate_events(event_date);

CREATE TABLE IF NOT EXISTS sectors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    parent_id UUID REFERENCES sectors(id),
    level INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_sectors_parent ON sectors(parent_id);

CREATE TABLE IF NOT EXISTS currency_rates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    base_currency VARCHAR(3) NOT NULL,
    quote_currency VARCHAR(3) NOT NULL,
    rate NUMERIC(20, 8) NOT NULL,
    rate_date DATE NOT NULL,
    source VARCHAR(20) DEFAULT 'ECB',
    UNIQUE(base_currency, quote_currency, rate_date)
);
CREATE INDEX IF NOT EXISTS idx_currency_rate_date ON currency_rates(rate_date);

CREATE TABLE IF NOT EXISTS macro_indicators (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    indicator_code VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    value NUMERIC(20, 6),
    period VARCHAR(20),
    unit VARCHAR(20),
    source VARCHAR(50),
    as_of DATE
);
CREATE INDEX IF NOT EXISTS idx_macro_code ON macro_indicators(indicator_code);
CREATE INDEX IF NOT EXISTS idx_macro_as_of ON macro_indicators(as_of);

-- ===============================================
-- 11. داده‌های بنیادی بازار ایران
-- ===============================================
CREATE TABLE IF NOT EXISTS ir_financial_statements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset_id UUID NOT NULL REFERENCES assets(id),
    market VARCHAR(20) NOT NULL DEFAULT 'TSE',
    period VARCHAR(20) NOT NULL,
    statement_type VARCHAR(20) NOT NULL,
    fiscal_year INTEGER,
    data JSONB DEFAULT '{}',
    as_of DATE,
    UNIQUE(asset_id, period, statement_type, market)
);
CREATE INDEX IF NOT EXISTS idx_ir_fin_stmt_asset ON ir_financial_statements(asset_id);
CREATE INDEX IF NOT EXISTS idx_ir_fin_stmt_market ON ir_financial_statements(market);

CREATE TABLE IF NOT EXISTS ir_fundamental_ratios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset_id UUID NOT NULL REFERENCES assets(id),
    market VARCHAR(20) NOT NULL DEFAULT 'TSE',
    period VARCHAR(20) NOT NULL,
    eps NUMERIC(20, 4),
    pe NUMERIC(12, 2),
    pb NUMERIC(12, 2),
    dps NUMERIC(20, 4),
    roe NUMERIC(8, 4),
    profit_margin NUMERIC(8, 4),
    market_cap NUMERIC(25, 2),
    book_value NUMERIC(20, 4),
    as_of DATE,
    UNIQUE(asset_id, period, market)
);
CREATE INDEX IF NOT EXISTS idx_ir_fund_ratio_asset ON ir_fundamental_ratios(asset_id);

-- ===============================================
-- 12. خبر و NLP
-- ===============================================
CREATE TABLE IF NOT EXISTS news (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source VARCHAR(100) NOT NULL,
    title VARCHAR(512) NOT NULL,
    body TEXT,
    url VARCHAR(1024),
    published_at TIMESTAMP,
    asset_id UUID REFERENCES assets(id),
    language VARCHAR(5) DEFAULT 'fa',
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_news_published ON news(published_at);
CREATE INDEX IF NOT EXISTS idx_news_asset ON news(asset_id);

CREATE TABLE IF NOT EXISTS news_sentiment (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    news_id UUID NOT NULL REFERENCES news(id),
    asset_id UUID REFERENCES assets(id),
    sentiment_label VARCHAR(20),
    sentiment_score NUMERIC(5, 2),
    model_version VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_news_sentiment_news ON news_sentiment(news_id);
CREATE INDEX IF NOT EXISTS idx_news_sentiment_asset ON news_sentiment(asset_id);
CREATE INDEX IF NOT EXISTS idx_news_sentiment_created ON news_sentiment(created_at);

CREATE TABLE IF NOT EXISTS news_summaries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    news_id UUID NOT NULL REFERENCES news(id),
    summary_text TEXT,
    model_version VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_news_summaries_news ON news_summaries(news_id);

-- ===============================================
-- 13. ML / پیش‌بینی / ناهنجاری
-- ===============================================
CREATE TABLE IF NOT EXISTS ml_models (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    version VARCHAR(50) NOT NULL,
    model_type VARCHAR(50),
    trained_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metrics JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    description TEXT,
    UNIQUE(name, version)
);

CREATE TABLE IF NOT EXISTS ml_predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset_id UUID NOT NULL REFERENCES assets(id),
    model_id UUID REFERENCES ml_models(id),
    model_version VARCHAR(50) NOT NULL,
    horizon VARCHAR(20) NOT NULL,
    predicted_value NUMERIC(20, 8),
    lower_bound NUMERIC(20, 8),
    upper_bound NUMERIC(20, 8),
    confidence NUMERIC(5, 2),
    as_of TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    target_date TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_ml_pred_asset ON ml_predictions(asset_id);
CREATE INDEX IF NOT EXISTS idx_ml_pred_target ON ml_predictions(target_date);
CREATE INDEX IF NOT EXISTS idx_ml_pred_asset_target ON ml_predictions(asset_id, target_date);

CREATE TABLE IF NOT EXISTS anomalies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset_id UUID NOT NULL REFERENCES assets(id),
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    score NUMERIC(10, 4),
    anomaly_type VARCHAR(50),
    description TEXT,
    severity VARCHAR(20) DEFAULT 'LOW'
);
CREATE INDEX IF NOT EXISTS idx_anomaly_asset ON anomalies(asset_id);
CREATE INDEX IF NOT EXISTS idx_anomaly_detected ON anomalies(detected_at);
CREATE INDEX IF NOT EXISTS idx_anomaly_asset_detected ON anomalies(asset_id, detected_at);

-- ===============================================
-- 14. ذخیره نتایج تحلیل (Screening)
-- ===============================================
CREATE TABLE IF NOT EXISTS screening_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    criteria JSONB DEFAULT '{}',
    universe JSONB DEFAULT '[]',
    result_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_screening_user ON screening_results(user_id);
CREATE INDEX IF NOT EXISTS idx_screening_created ON screening_results(created_at);

-- ===============================================
-- 15. View‌ها
-- ===============================================

-- آخرین قیمت‌های روزانه (محور بازار ایران)
CREATE OR REPLACE VIEW latest_prices AS
SELECT DISTINCT ON (asset_id)
    asset_id,
    timestamp,
    close AS current_price,
    (close - open) AS day_change,
    ((close - open) / open * 100) AS day_change_pct
FROM intl_price_candles
WHERE timeframe = '1d'
ORDER BY asset_id, timestamp DESC;

-- عملکرد پورتفولیوها
CREATE OR REPLACE VIEW portfolio_performance AS
SELECT
    p.id AS portfolio_id,
    p.user_id,
    SUM(pos.quantity * lp.current_price) AS total_value,
    SUM(pos.quantity * pos.entry_price) AS total_cost,
    SUM(pos.quantity * lp.current_price) - SUM(pos.quantity * pos.entry_price) AS total_return
FROM portfolios p
LEFT JOIN positions pos ON p.id = pos.portfolio_id
LEFT JOIN latest_prices lp ON pos.asset_id = lp.asset_id
GROUP BY p.id, p.user_id;

-- ===============================================
-- 16. تابع به‌روزرسانی updated_at
-- ===============================================
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS assets_update_timestamp ON assets;
CREATE TRIGGER assets_update_timestamp
BEFORE UPDATE ON assets
FOR EACH ROW
EXECUTE FUNCTION update_timestamp();

-- ===============================================
-- 17. مجوزات و کنترل دسترسی
-- ===============================================
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'bedaan_readonly') THEN
        CREATE ROLE bedaan_readonly;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'bedaan_api') THEN
        CREATE ROLE bedaan_api;
    END IF;
END
$$;

GRANT CONNECT ON DATABASE bedaanwaves_db TO bedaan_readonly, bedaan_api;
GRANT USAGE ON SCHEMA public TO bedaan_readonly, bedaan_api;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO bedaan_readonly;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO bedaan_api;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO bedaan_api;

-- ===============================================
-- 18. Additional Tables (ML, Crypto, User Settings, etc.)
-- ===============================================

-- Company Leadership
CREATE TABLE IF NOT EXISTS company_leadership (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset_id UUID NOT NULL REFERENCES assets(id),
    name VARCHAR(255) NOT NULL,
    title VARCHAR(255) NOT NULL,
    leadership_type VARCHAR(50) NOT NULL,
    start_date DATE,
    end_date DATE,
    source VARCHAR(50) DEFAULT 'SEC',
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_company_leadership_asset ON company_leadership(asset_id);

-- Raw Market Data (Crypto & International)
CREATE TABLE IF NOT EXISTS raw_market_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset_id UUID REFERENCES assets(id),
    raw_symbol VARCHAR(50) NOT NULL,
    market VARCHAR(20) NOT NULL,
    exchange VARCHAR(50),
    data_type VARCHAR(30) NOT NULL,
    raw_payload JSONB NOT NULL,
    price NUMERIC(20, 8),
    volume NUMERIC(25, 2),
    quote_volume NUMERIC(25, 2),
    source_timestamp TIMESTAMPTZ NOT NULL,
    ingested_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    ingestion_id VARCHAR(100),
    data_quality VARCHAR(10) DEFAULT 'RAW',
    UNIQUE(raw_symbol, market, exchange, data_type, source_timestamp),
    CONSTRAINT chk_raw_data_quality CHECK (data_quality IN ('RAW', 'VALIDATED')),
    CONSTRAINT chk_raw_market_type CHECK (market IN ('CRYPTO', 'INTL', 'TSE')),
    CONSTRAINT chk_raw_volume_non_negative CHECK (volume >= 0)
);
CREATE INDEX IF NOT EXISTS idx_raw_asset ON raw_market_data(asset_id);
CREATE INDEX IF NOT EXISTS idx_raw_market_type ON raw_market_data(market, data_type);
CREATE INDEX IF NOT EXISTS idx_raw_ingested ON raw_market_data(ingested_at);
CREATE INDEX IF NOT EXISTS idx_raw_symbol ON raw_market_data(raw_symbol);

-- Market Data Snapshots
CREATE TABLE IF NOT EXISTS market_data_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset_id UUID NOT NULL REFERENCES assets(id),
    snapshot_time TIMESTAMPTZ NOT NULL,
    interval VARCHAR(10) NOT NULL,
    open NUMERIC(20, 8),
    high NUMERIC(20, 8),
    low NUMERIC(20, 8),
    close NUMERIC(20, 8),
    volume NUMERIC(25, 2),
    turnover NUMERIC(25, 2),
    rsi NUMERIC(8, 4),
    macd NUMERIC(20, 8),
    macd_signal NUMERIC(20, 8),
    macd_histogram NUMERIC(20, 8),
    bb_upper NUMERIC(20, 8),
    bb_middle NUMERIC(20, 8),
    bb_lower NUMERIC(20, 8),
    atr NUMERIC(20, 8),
    ma_7 NUMERIC(20, 8),
    ma_14 NUMERIC(20, 8),
    ma_30 NUMERIC(20, 8),
    volatility NUMERIC(20, 8),
    volume_ma_7 NUMERIC(25, 2),
    volume_ratio NUMERIC(8, 4),
    features JSONB DEFAULT '{}',
    source VARCHAR(20) DEFAULT 'BRS',
    is_fresh BOOLEAN DEFAULT TRUE,
    freshness_score NUMERIC(5, 2),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(asset_id, snapshot_time, interval),
    CONSTRAINT chk_freshness_score_range CHECK (freshness_score >= 0 AND freshness_score <= 100),
    CONSTRAINT chk_snapshot_high_low CHECK (high >= low),
    CONSTRAINT chk_snapshot_volume_non_negative CHECK (volume >= 0)
);
CREATE INDEX IF NOT EXISTS idx_snapshot_fresh ON market_data_snapshots(asset_id, is_fresh, snapshot_time);
CREATE INDEX IF NOT EXISTS idx_snapshot_interval ON market_data_snapshots(asset_id, interval, snapshot_time);

-- Crypto ML Signals
CREATE TABLE IF NOT EXISTS crypto_ml_signals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset_id UUID NOT NULL REFERENCES assets(id),
    snapshot_id UUID REFERENCES market_data_snapshots(id),
    signal_type VARCHAR(20) NOT NULL,
    confidence NUMERIC(5, 2) NOT NULL,
    expected_return NUMERIC(8, 2),
    expected_volatility NUMERIC(8, 2),
    risk_score NUMERIC(5, 2),
    model_name VARCHAR(100),
    model_version VARCHAR(50),
    features_used JSONB DEFAULT '{}',
    technical_indicators JSONB DEFAULT '{}',
    generated_at TIMESTAMPTZ DEFAULT NOW(),
    valid_from TIMESTAMPTZ DEFAULT NOW(),
    valid_until TIMESTAMPTZ NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);
CREATE INDEX IF NOT EXISTS idx_crypto_signal_active ON crypto_ml_signals(asset_id, is_active, valid_until);
CREATE INDEX IF NOT EXISTS idx_crypto_signal_model ON crypto_ml_signals(model_version);

-- Raw Performance Scores (Coefficient Learning)
CREATE TABLE IF NOT EXISTS raw_performance_scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    captured_at TIMESTAMPTZ DEFAULT NOW(),
    asset_id UUID REFERENCES assets(id),
    market VARCHAR(20) NOT NULL,
    exchange VARCHAR(50) NOT NULL,
    context JSONB DEFAULT '{}',
    dimension_scores JSONB NOT NULL,
    sub_dimension_scores JSONB NOT NULL,
    aspect_scores JSONB NOT NULL,
    sub_aspect_scores JSONB NOT NULL,
    target_return NUMERIC(20, 8),
    target_volatility NUMERIC(10, 6),
    target_sharpe NUMERIC(8, 4),
    target_price_change NUMERIC(10, 6),
    target_volume_change NUMERIC(10, 4),
    target_bitcoin_correlation NUMERIC(8, 6),
    target_market_sentiment NUMERIC(5, 2),
    data_quality VARCHAR(20) DEFAULT 'VALIDATED',
    validation_status VARCHAR(20) DEFAULT 'PENDING',
    validation_notes TEXT,
    is_processed BOOLEAN DEFAULT FALSE,
    processing_errors JSONB DEFAULT '{}',
    ingestion_id VARCHAR(100),
    source_system VARCHAR(50) DEFAULT 'SCORING_SERVICE',
    UNIQUE(asset_id, captured_at, market)
);
CREATE INDEX IF NOT EXISTS idx_raw_perf_asset_time ON raw_performance_scores(asset_id, captured_at);
CREATE INDEX IF NOT EXISTS idx_raw_perf_market ON raw_performance_scores(market, exchange);
CREATE INDEX IF NOT EXISTS idx_raw_perf_processed ON raw_performance_scores(is_processed);

-- Processed Feature Data
CREATE TABLE IF NOT EXISTS processed_feature_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    raw_data_id UUID NOT NULL REFERENCES raw_performance_scores(id),
    asset_id UUID REFERENCES assets(id),
    processed_at TIMESTAMPTZ DEFAULT NOW(),
    market VARCHAR(20) NOT NULL,
    exchange VARCHAR(50) NOT NULL,
    feature_vector NUMERIC(20, 8)[] NOT NULL,
    dimension_features JSONB NOT NULL,
    sub_dimension_features JSONB NOT NULL,
    aspect_features JSONB NOT NULL,
    sub_aspect_features JSONB NOT NULL,
    target_values JSONB NOT NULL,
    features_used JSONB DEFAULT '{}',
    preprocessing_steps JSONB DEFAULT '{}',
    normalization_params JSONB DEFAULT '{}',
    is_valid BOOLEAN DEFAULT TRUE,
    quality_score NUMERIC(5, 2) DEFAULT 100.0,
    validation_errors JSONB DEFAULT '{}',
    model_version VARCHAR(50) DEFAULT 'v1.0.0',
    feature_schema_version VARCHAR(20) DEFAULT '1.0',
    UNIQUE(raw_data_id, processed_at)
);
CREATE INDEX IF NOT EXISTS idx_proc_asset_market ON processed_feature_data(asset_id, market);
CREATE INDEX IF NOT EXISTS idx_proc_valid ON processed_feature_data(is_valid);
CREATE INDEX IF NOT EXISTS idx_proc_processed_at ON processed_feature_data(processed_at);

-- Coefficient Adjustments
CREATE TABLE IF NOT EXISTS coefficient_adjustments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    adjustment_cycle TIMESTAMPTZ DEFAULT NOW(),
    asset_id UUID REFERENCES assets(id),
    level VARCHAR(20) NOT NULL,
    feature_key VARCHAR(100) NOT NULL,
    old_weight NUMERIC(8, 6) NOT NULL,
    new_weight NUMERIC(8, 6) NOT NULL,
    weight_change NUMERIC(8, 6),
    adjustment_code VARCHAR(50) NOT NULL,
    adjustment_reason TEXT,
    confidence_score NUMERIC(5, 2) DEFAULT 100.0,
    model_version VARCHAR(50),
    training_samples INTEGER,
    performance_improvement NUMERIC(8, 6),
    created_by VARCHAR(50) DEFAULT 'system',
    implementation_version VARCHAR(20) NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_adj_cycle_level ON coefficient_adjustments(adjustment_cycle, level);
CREATE INDEX IF NOT EXISTS idx_adj_feature_key ON coefficient_adjustments(feature_key);

-- Coefficient History
CREATE TABLE IF NOT EXISTS coefficient_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    effective_at TIMESTAMPTZ DEFAULT NOW(),
    asset_id UUID REFERENCES assets(id),
    market VARCHAR(20) NOT NULL,
    exchange VARCHAR(50) NOT NULL,
    coefficients JSONB NOT NULL,
    source VARCHAR(50) DEFAULT 'ML_TRAINING',
    model_version VARCHAR(50),
    is_valid BOOLEAN DEFAULT TRUE,
    validation_notes TEXT
);
CREATE INDEX IF NOT EXISTS idx_hist_asset_time ON coefficient_history(asset_id, effective_at);
CREATE INDEX IF NOT EXISTS idx_hist_effective ON coefficient_history(effective_at);

-- User Market Settings
CREATE TABLE IF NOT EXISTS user_market_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    countries JSONB DEFAULT '[]',
    indices JSONB DEFAULT '[]',
    industries JSONB DEFAULT '[]',
    regions JSONB DEFAULT '[]',
    exchanges JSONB DEFAULT '[]',
    currencies JSONB DEFAULT '[]',
    last_validated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    validation_hash VARCHAR(64),
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);
CREATE INDEX IF NOT EXISTS idx_market_settings_user ON user_market_settings(user_id);

-- User Market Configs
CREATE TABLE IF NOT EXISTS user_market_configs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    config_name VARCHAR(100) NOT NULL,
    country VARCHAR(50),
    country_indices JSONB DEFAULT '[]',
    selected_industries JSONB DEFAULT '[]',
    included_symbols JSONB DEFAULT '[]',
    price_range JSONB,
    volume_range JSONB,
    change_filter JSONB,
    market_cap_filter JSONB,
    last_calc TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, config_name)
);
CREATE INDEX IF NOT EXISTS idx_market_config_user ON user_market_configs(user_id);

-- User Crypto Settings
CREATE TABLE IF NOT EXISTS user_crypto_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    selected_cryptos JSONB DEFAULT '[]',
    excluded_cryptos JSONB DEFAULT '[]',
    custom_watchlist JSONB DEFAULT '[]',
    exchange_source VARCHAR(50) DEFAULT 'binance',
    min_volume_24h NUMERIC(20, 8) DEFAULT 1000000,
    min_market_cap NUMERIC(20, 8) DEFAULT 50000000,
    price_change_filter VARCHAR(20) DEFAULT 'all',
    last_validated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    validation_hash VARCHAR(64),
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);
CREATE INDEX IF NOT EXISTS idx_crypto_settings_user ON user_crypto_settings(user_id);

-- User Crypto Configs
CREATE TABLE IF NOT EXISTS user_crypto_configs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    config_name VARCHAR(100) NOT NULL,
    included_symbols JSONB DEFAULT '[]',
    excluded_symbols JSONB DEFAULT '[]',
    exchange_source VARCHAR(50) DEFAULT 'binance',
    min_volume_24h NUMERIC(20, 8),
    min_market_cap NUMERIC(20, 8),
    price_range JSONB,
    change_filter JSONB,
    last_calc TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, config_name)
);
CREATE INDEX IF NOT EXISTS idx_crypto_config_user ON user_crypto_configs(user_id);

-- User Scoring Results
CREATE TABLE IF NOT EXISTS user_scoring_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    source VARCHAR(100) NOT NULL,
    symbol VARCHAR(50) NOT NULL,
    country VARCHAR(50),
    industry VARCHAR(50),
    exchange VARCHAR(50),
    score NUMERIC(10, 6),
    rank INTEGER,
    data_date DATE NOT NULL,
    criteria_scores JSONB,
    user_preferences JSONB,
    recommendations JSONB,
    description JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, symbol, data_date)
);
CREATE INDEX IF NOT EXISTS idx_scoring_user ON user_scoring_results(user_id);
CREATE INDEX IF NOT EXISTS idx_scoring_user_date ON user_scoring_results(user_id, data_date);

-- Validation Records
CREATE TABLE IF NOT EXISTS validation_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id VARCHAR(100) NOT NULL,
    validation_date TIMESTAMP NOT NULL,
    validation_type VARCHAR(50) NOT NULL,
    is_valid BOOLEAN NOT NULL,
    details JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_validation_source ON validation_records(source_id);
CREATE INDEX IF NOT EXISTS idx_validation_type ON validation_records(validation_type);

-- Source Authenticity
CREATE TABLE IF NOT EXISTS source_authenticity (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_name VARCHAR(100) NOT NULL,
    authenticity_score NUMERIC(5, 2) NOT NULL,
    verification_status VARCHAR(50) NOT NULL,
    verification_timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_authenticity_source ON source_authenticity(source_name);

-- Cross Source Consistency
CREATE TABLE IF NOT EXISTS cross_source_consistency (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_a_id VARCHAR(100) NOT NULL,
    source_b_id VARCHAR(100) NOT NULL,
    data_type VARCHAR(50) NOT NULL,
    consistency_metric NUMERIC(5, 2) NOT NULL,
    validation_timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_consistency_sources ON cross_source_consistency(source_a_id, source_b_id);

-- Data Sources Registry
CREATE TABLE IF NOT EXISTS data_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_name VARCHAR(100) NOT NULL UNIQUE,
    source_type VARCHAR(50) NOT NULL,
    base_url VARCHAR(500),
    api_key_required BOOLEAN DEFAULT FALSE,
    auth_token VARCHAR(500),
    data_format VARCHAR(50),
    last_verification TIMESTAMP,
    verification_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    info JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_datasource_type ON data_sources(source_type);
CREATE INDEX IF NOT EXISTS idx_datasource_active ON data_sources(is_active);

-- Historical Data Import Log
CREATE TABLE IF NOT EXISTS historical_data_import_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    import_batch_id VARCHAR(100) NOT NULL,
    source_id UUID REFERENCES data_sources(id),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    records_imported INTEGER DEFAULT 0,
    records_updated INTEGER DEFAULT 0,
    validation_results JSONB,
    import_status VARCHAR(50) DEFAULT 'pending',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_import_batch ON historical_data_import_log(import_batch_id);
CREATE INDEX IF NOT EXISTS idx_import_status ON historical_data_import_log(import_status);

-- Cryptocurrencies Master List
CREATE TABLE IF NOT EXISTS cryptocurrencies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    exchange VARCHAR(50),
    market_cap NUMERIC(20, 8),
    volume_24h NUMERIC(20, 8),
    price_usd NUMERIC(20, 8),
    price_change_24h NUMERIC(10, 6),
    price_change_7d NUMERIC(10, 6),
    market_cap_rank INTEGER,
    circulating_supply NUMERIC(20, 8),
    max_supply NUMERIC(20, 8),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    extra_data JSONB
);
CREATE INDEX IF NOT EXISTS idx_crypto_symbol ON cryptocurrencies(symbol);
CREATE INDEX IF NOT EXISTS idx_crypto_market_cap_rank ON cryptocurrencies(market_cap_rank);

-- Countries List
CREATE TABLE IF NOT EXISTS countries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    iso_code VARCHAR(10) NOT NULL UNIQUE,
    stock_exchange VARCHAR(100),
    currency_code VARCHAR(10),
    timezone VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    extra_data JSONB,
    last_verified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_country_code ON countries(iso_code);
CREATE INDEX IF NOT EXISTS idx_country_active ON countries(is_active);

-- Industries List
CREATE TABLE IF NOT EXISTS industries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    sector VARCHAR(100),
    etf_ticker VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    extra_data JSONB,
    last_verified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_industry_sector ON industries(sector);
CREATE INDEX IF NOT EXISTS idx_industry_active ON industries(is_active);

-- Market Indices
CREATE TABLE IF NOT EXISTS market_indices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    exchange VARCHAR(100),
    country VARCHAR(50),
    base_value NUMERIC(20, 8),
    current_value NUMERIC(20, 8),
    change_percent NUMERIC(10, 6),
    volume NUMERIC(18, 8),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    extra_data JSONB,
    is_active BOOLEAN DEFAULT TRUE
);
CREATE INDEX IF NOT EXISTS idx_index_country ON market_indices(country);
CREATE INDEX IF NOT EXISTS idx_index_active ON market_indices(is_active);

-- User Favorites
CREATE TABLE IF NOT EXISTS user_favorites (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    source VARCHAR(100) NOT NULL,
    symbol VARCHAR(50) NOT NULL,
    category VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, source, symbol)
);
CREATE INDEX IF NOT EXISTS idx_favorite_user ON user_favorites(user_id);

-- User Alerts
CREATE TABLE IF NOT EXISTS user_alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    symbol VARCHAR(50) NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    alert_condition JSONB NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    notify_method JSONB DEFAULT '{"email": true, "push": true, "sms": false}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_triggered TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_alert_user ON user_alerts(user_id);
CREATE INDEX IF NOT EXISTS idx_alert_symbol ON user_alerts(symbol);
CREATE INDEX IF NOT EXISTS idx_alert_active ON user_alerts(is_active);

-- Symbol Market Settings
CREATE TABLE IF NOT EXISTS symbol_market_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol_id INTEGER NOT NULL REFERENCES symbol_data(symbol_id),
    user_id UUID NOT NULL,
    country VARCHAR(50),
    index_code VARCHAR(50),
    industry_code VARCHAR(50),
    region VARCHAR(50),
    is_visible BOOLEAN DEFAULT TRUE,
    display_order INTEGER DEFAULT 0,
    custom_label VARCHAR(255),
    price_min NUMERIC(20, 8),
    price_max NUMERIC(20, 8),
    volume_min NUMERIC(25, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol_id, user_id)
);
CREATE INDEX IF NOT EXISTS idx_symbol_market_settings_user ON symbol_market_settings(user_id);
CREATE INDEX IF NOT EXISTS idx_symbol_market_settings_symbol ON symbol_market_settings(symbol_id);

-- ===============================================
-- 19. نمادهای کلیدی ناسداک (Full list in insert_nasdaq_symbols.sql)
-- ===============================================
INSERT INTO assets (symbol, name, asset_class, market, sector, country_code, currency, active) VALUES
('^IXIC', 'Nasdaq Composite', 'INDEX', 'NASDAQ', 'Technology', 'US', 'USD', TRUE),
('AAPL', 'Apple Inc.', 'EQUITY', 'NASDAQ', 'Technology', 'US', 'USD', TRUE),
('MSFT', 'Microsoft Corporation', 'EQUITY', 'NASDAQ', 'Technology', 'US', 'USD', TRUE),
('AMZN', 'Amazon.com Inc.', 'EQUITY', 'NASDAQ', 'Consumer Discretionary', 'US', 'USD', TRUE),
('GOOGL', 'Alphabet Inc. Class A', 'EQUITY', 'NASDAQ', 'Communication Services', 'US', 'USD', TRUE),
('GOOG', 'Alphabet Inc. Class C', 'EQUITY', 'NASDAQ', 'Communication Services', 'US', 'USD', TRUE),
('META', 'Meta Platforms Inc.', 'EQUITY', 'NASDAQ', 'Communication Services', 'US', 'USD', TRUE),
('NVDA', 'NVIDIA Corporation', 'EQUITY', 'NASDAQ', 'Technology', 'US', 'USD', TRUE),
('TSLA', 'Tesla Inc.', 'EQUITY', 'NASDAQ', 'Consumer Discretionary', 'US', 'USD', TRUE),
('PEP', 'PepsiCo Inc.', 'EQUITY', 'NASDAQ', 'Consumer Staples', 'US', 'USD', TRUE),
('AVGO', 'Broadcom Inc.', 'EQUITY', 'NASDAQ', 'Technology', 'US', 'USD', TRUE),
('COST', 'Costco Wholesale Corporation', 'EQUITY', 'NASDAQ', 'Consumer Staples', 'US', 'USD', TRUE),
('CSCO', 'Cisco Systems Inc.', 'EQUITY', 'NASDAQ', 'Technology', 'US', 'USD', TRUE),
('TMUS', 'T-Mobile US Inc.', 'EQUITY', 'NASDAQ', 'Communication Services', 'US', 'USD', TRUE),
('ADBE', 'Adobe Inc.', 'EQUITY', 'NASDAQ', 'Technology', 'US', 'USD', TRUE),
('NFLX', 'Netflix Inc.', 'EQUITY', 'NASDAQ', 'Communication Services', 'US', 'USD', TRUE),
('AMD', 'Advanced Micro Devices Inc.', 'EQUITY', 'NASDAQ', 'Technology', 'US', 'USD', TRUE),
('INTC', 'Intel Corporation', 'EQUITY', 'NASDAQ', 'Technology', 'US', 'USD', TRUE),
('QCOM', 'Qualcomm Incorporated', 'EQUITY', 'NASDAQ', 'Technology', 'US', 'USD', TRUE),
('TXN', 'Texas Instruments Incorporated', 'EQUITY', 'NASDAQ', 'Technology', 'US', 'USD', TRUE),
('AMGN', 'Amgen Inc.', 'EQUITY', 'NASDAQ', 'Healthcare', 'US', 'USD', TRUE),
('HON', 'Honeywell International Inc.', 'EQUITY', 'NASDAQ', 'Industrials', 'US', 'USD', TRUE),
('INTU', 'Intuit Inc.', 'EQUITY', 'NASDAQ', 'Technology', 'US', 'USD', TRUE),
('BKNG', 'Booking Holdings Inc.', 'EQUITY', 'NASDAQ', 'Consumer Discretionary', 'US', 'USD', TRUE),
('SBUX', 'Starbucks Corporation', 'EQUITY', 'NASDAQ', 'Consumer Discretionary', 'US', 'USD', TRUE)
ON CONFLICT (symbol) DO NOTHING;

-- Load all NASDAQ symbols from database/insert_nasdaq_symbols.sql
-- Run: psql -U postgres -d bedaanwaves_db -f database/insert_nasdaq_symbols.sql

-- ===============================================
-- پایان
-- ===============================================
SELECT COUNT(*) AS total_assets FROM assets;
