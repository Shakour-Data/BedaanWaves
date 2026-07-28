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
-- 3. کندل‌های قیمت — سه جدول مجزا بر اساس بازار
-- ===============================================

-- 3.1 بازار ایران (TSE/فرابورس): 1h, 1d, 1w, 1M
CREATE TABLE IF NOT EXISTS ir_price_candles (
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
    CONSTRAINT chk_ir_high_values CHECK (high >= open AND high >= close),
    CONSTRAINT chk_ir_low_values CHECK (low <= open AND low <= close)
);
CREATE INDEX IF NOT EXISTS idx_ir_candle_asset ON ir_price_candles(asset_id);
CREATE INDEX IF NOT EXISTS idx_ir_candle_timestamp ON ir_price_candles(timestamp);
CREATE INDEX IF NOT EXISTS idx_ir_candle_asset_time ON ir_price_candles(asset_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_ir_candle_tf_ts ON ir_price_candles(timeframe, timestamp);

-- 3.2 بورس‌های خارج از ایران: 15m, 1h, 4h, 1d, 1w, 1M
CREATE TABLE IF NOT EXISTS intl_price_candles (
    LIKE ir_price_candles INCLUDING ALL
);

-- 3.3 رمزارز (۲۴/۷): 5m, 15m, 1h, 4h, 1d, 1w, 1M
CREATE TABLE IF NOT EXISTS crypto_price_candles (
    LIKE ir_price_candles INCLUDING ALL
);

-- ===============================================
-- 4. عمق بازار / مظنه برتر — هر ۱۵ دقیقه، ۵ مظنه برتر
-- ===============================================
CREATE TABLE IF NOT EXISTS ir_order_book (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset_id UUID NOT NULL REFERENCES assets(id),
    snapshot_time TIMESTAMP NOT NULL,
    rank INTEGER NOT NULL,
    bid_price NUMERIC(20, 8),
    bid_volume BIGINT,
    ask_price NUMERIC(20, 8),
    ask_volume BIGINT,
    source VARCHAR(20) DEFAULT 'BRS',
    UNIQUE(asset_id, snapshot_time, rank)
);
CREATE INDEX IF NOT EXISTS idx_ir_orderbook_asset ON ir_order_book(asset_id);
CREATE INDEX IF NOT EXISTS idx_ir_orderbook_asset_snap ON ir_order_book(asset_id, snapshot_time);

CREATE TABLE IF NOT EXISTS intl_order_book ( LIKE ir_order_book INCLUDING ALL );
CREATE TABLE IF NOT EXISTS crypto_order_book ( LIKE ir_order_book INCLUDING ALL );

-- ===============================================
-- 5. جداول اختصاصی بازار ایران
-- ===============================================

-- 5.1 سهامداران عمده
CREATE TABLE IF NOT EXISTS ir_major_shareholders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset_id UUID NOT NULL REFERENCES assets(id),
    shareholder_name VARCHAR(255) NOT NULL,
    shareholder_type VARCHAR(10) NOT NULL,
    rank INTEGER,
    share_count BIGINT,
    share_pct NUMERIC(8, 4),
    change_count BIGINT DEFAULT 0,
    change_pct NUMERIC(8, 4) DEFAULT 0,
    report_date DATE NOT NULL,
    source VARCHAR(20) DEFAULT 'BRS',
    UNIQUE(asset_id, shareholder_name, report_date)
);
CREATE INDEX IF NOT EXISTS idx_ir_shareholder_asset ON ir_major_shareholders(asset_id);

-- 5.2 سهام شناور آزاد
CREATE TABLE IF NOT EXISTS ir_free_float (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset_id UUID NOT NULL REFERENCES assets(id),
    free_float_pct NUMERIC(8, 4),
    base_volume BIGINT,
    as_of_date DATE NOT NULL,
    source VARCHAR(20) DEFAULT 'BRS',
    UNIQUE(asset_id, as_of_date)
);
CREATE INDEX IF NOT EXISTS idx_ir_free_float_asset ON ir_free_float(asset_id);

-- 5.3 جریان حقیقی/حقوقی (هر ۱۵ دقیقه)
CREATE TABLE IF NOT EXISTS ir_retail_institutional (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset_id UUID NOT NULL REFERENCES assets(id),
    snapshot_time TIMESTAMP NOT NULL,
    retail_buy_volume BIGINT DEFAULT 0,
    retail_sell_volume BIGINT DEFAULT 0,
    institutional_buy_volume BIGINT DEFAULT 0,
    institutional_sell_volume BIGINT DEFAULT 0,
    net_flow NUMERIC(25, 2) DEFAULT 0,
    source VARCHAR(20) DEFAULT 'BRS',
    UNIQUE(asset_id, snapshot_time)
);
CREATE INDEX IF NOT EXISTS idx_ir_retail_inst_asset ON ir_retail_institutional(asset_id);

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
    period VARCHAR(20) NOT NULL,
    statement_type VARCHAR(20) NOT NULL,
    fiscal_year INTEGER,
    data JSONB DEFAULT '{}',
    as_of DATE,
    UNIQUE(asset_id, period, statement_type)
);
CREATE INDEX IF NOT EXISTS idx_ir_fin_stmt_asset ON ir_financial_statements(asset_id);

CREATE TABLE IF NOT EXISTS ir_fundamental_ratios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset_id UUID NOT NULL REFERENCES assets(id),
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
    UNIQUE(asset_id, period)
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
FROM ir_price_candles
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
-- 18. اطلاعات اولیه (Sample Data)
-- ===============================================
INSERT INTO assets (symbol, name, asset_class, market, sector) VALUES
('FSPD', 'فولاد', 'EQUITY', 'TSE', 'معادن'),
('MAPNA', 'مپنا', 'EQUITY', 'TSE', 'ماشین‌آلات'),
('SHTEL', 'شتل', 'EQUITY', 'TSE', 'مخابرات'),
('SAIPA', 'سایپا', 'EQUITY', 'TSE', 'خودروساز'),
('PETR', 'نفت', 'EQUITY', 'TSE', 'انرژی')
ON CONFLICT (symbol) DO NOTHING;

-- ===============================================
-- پایان
-- ===============================================
SELECT COUNT(*) AS total_assets FROM assets;
