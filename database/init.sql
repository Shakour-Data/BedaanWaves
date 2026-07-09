-- BedaanWaves Database Initialization Script
-- تهیه‌سازی پایگاه‌داده برای BedaanWaves

-- ===============================================
-- 1. Extension‌ها
-- ===============================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ===============================================
-- 2. Schema اصلی
-- ===============================================

CREATE SCHEMA IF NOT EXISTS bedaan_data;
CREATE SCHEMA IF NOT EXISTS bedaan_analysis;
CREATE SCHEMA IF NOT EXISTS bedaan_user;

-- ===============================================
-- 3. جداول اصلی (bedaan_data schema)
-- ===============================================

-- 3.1 جدول دارایی‌ها (Assets)
CREATE TABLE IF NOT EXISTS bedaan_data.assets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    asset_class VARCHAR(20) NOT NULL,
    market VARCHAR(20) NOT NULL,
    sector VARCHAR(100),
    sub_sector VARCHAR(100),
    country_code VARCHAR(2),
    currency VARCHAR(3) DEFAULT 'IRR',
    active BOOLEAN DEFAULT TRUE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_assets_symbol ON bedaan_data.assets(symbol);
CREATE INDEX idx_assets_active ON bedaan_data.assets(active);
CREATE INDEX idx_assets_market ON bedaan_data.assets(market);

-- 3.2 جدول کندل‌های قیمت (Price Candles)
CREATE TABLE IF NOT EXISTS bedaan_data.price_candles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset_id UUID NOT NULL REFERENCES bedaan_data.assets(id),
    timestamp TIMESTAMP NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    open NUMERIC(20, 8) NOT NULL,
    high NUMERIC(20, 8) NOT NULL,
    low NUMERIC(20, 8) NOT NULL,
    close NUMERIC(20, 8) NOT NULL,
    volume BIGINT NOT NULL,
    turnover NUMERIC(25, 2),
    transactions INTEGER,
    source VARCHAR(20) DEFAULT 'BRS',
    data_quality VARCHAR(10) DEFAULT 'CONFIRMED',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(asset_id, timestamp, timeframe)
);

CREATE INDEX idx_candles_asset ON bedaan_data.price_candles(asset_id);
CREATE INDEX idx_candles_timestamp ON bedaan_data.price_candles(timestamp);
CREATE INDEX idx_candles_asset_time ON bedaan_data.price_candles(asset_id, timestamp DESC);

-- 3.3 جدول سیگنال‌های ML (ML Signals)
CREATE TABLE IF NOT EXISTS bedaan_analysis.ml_signals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset_id UUID NOT NULL REFERENCES bedaan_data.assets(id),
    signal_type VARCHAR(20) NOT NULL,
    confidence NUMERIC(5, 2) NOT NULL,
    expected_return NUMERIC(8, 2),
    risk_score NUMERIC(5, 2),
    reasoning TEXT,
    technical_factors JSONB DEFAULT '{}',
    fundamental_factors JSONB DEFAULT '{}',
    ml_model_version VARCHAR(50) NOT NULL,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    valid_until TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_signals_asset ON bedaan_analysis.ml_signals(asset_id);
CREATE INDEX idx_signals_active ON bedaan_analysis.ml_signals(is_active);
CREATE INDEX idx_signals_model ON bedaan_analysis.ml_signals(ml_model_version);

-- ===============================================
-- 4. جداول کاربر (bedaan_user schema)
-- ===============================================

-- 4.1 جدول کاربران
CREATE TABLE IF NOT EXISTS bedaan_user.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    preferred_language VARCHAR(10) DEFAULT 'fa',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

CREATE INDEX idx_users_username ON bedaan_user.users(username);
CREATE INDEX idx_users_email ON bedaan_user.users(email);

-- 4.2 جدول پورتفولیوها
CREATE TABLE IF NOT EXISTS bedaan_user.portfolios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES bedaan_user.users(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    portfolio_type VARCHAR(20) DEFAULT 'PERSONAL',
    base_currency VARCHAR(3) DEFAULT 'IRR',
    is_public BOOLEAN DEFAULT FALSE,
    public_token VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, name)
);

CREATE INDEX idx_portfolios_user ON bedaan_user.portfolios(user_id);

-- 4.3 جدول موضع‌های پورتفولیو
CREATE TABLE IF NOT EXISTS bedaan_user.positions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    portfolio_id UUID NOT NULL REFERENCES bedaan_user.portfolios(id),
    asset_id UUID NOT NULL REFERENCES bedaan_data.assets(id),
    quantity NUMERIC(20, 8) NOT NULL,
    entry_price NUMERIC(20, 8) NOT NULL,
    entry_date DATE NOT NULL,
    stop_loss NUMERIC(20, 8),
    take_profit NUMERIC(20, 8),
    notes TEXT,
    tags JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(portfolio_id, asset_id)
);

CREATE INDEX idx_positions_portfolio ON bedaan_user.positions(portfolio_id);
CREATE INDEX idx_positions_asset ON bedaan_user.positions(asset_id);

-- 4.4 جدول هشدارها
CREATE TABLE IF NOT EXISTS bedaan_user.alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES bedaan_user.users(id),
    asset_id UUID REFERENCES bedaan_data.assets(id),
    alert_type VARCHAR(20) NOT NULL,
    condition JSONB NOT NULL,
    threshold_value NUMERIC(20, 8),
    notification_channel VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    triggered_at TIMESTAMP,
    triggered_count INTEGER DEFAULT 0
);

CREATE INDEX idx_alerts_user ON bedaan_user.alerts(user_id);
CREATE INDEX idx_alerts_active ON bedaan_user.alerts(is_active);

-- ===============================================
-- 5. جداول لاگ و مانیتورینگ
-- ===============================================

-- 5.1 جدول لاگ درخواست‌های API
CREATE TABLE IF NOT EXISTS bedaan_data.api_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID,
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INTEGER,
    response_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_logs_endpoint ON bedaan_data.api_logs(endpoint);
CREATE INDEX idx_logs_timestamp ON bedaan_data.api_logs(created_at);

-- ===============================================
-- 6. بخش‌های محدود دسترسی
-- ===============================================

-- 6.1 View برای آخرین قیمت‌ها
CREATE OR REPLACE VIEW bedaan_data.latest_prices AS
SELECT DISTINCT ON (asset_id)
    asset_id,
    timestamp,
    close as current_price,
    (close - open) as day_change,
    ((close - open) / open * 100) as day_change_pct
FROM bedaan_data.price_candles
WHERE timeframe = '1d'
ORDER BY asset_id, timestamp DESC;

-- 6.2 View برای شاخص‌های عملکرد
CREATE OR REPLACE VIEW bedaan_user.portfolio_performance AS
SELECT 
    p.id as portfolio_id,
    p.user_id,
    SUM(pos.quantity * lp.current_price) as total_value,
    SUM(pos.quantity * pos.entry_price) as total_cost,
    SUM(pos.quantity * lp.current_price) - SUM(pos.quantity * pos.entry_price) as total_return
FROM bedaan_user.portfolios p
LEFT JOIN bedaan_user.positions pos ON p.id = pos.portfolio_id
LEFT JOIN bedaan_data.latest_prices lp ON pos.asset_id = lp.asset_id
GROUP BY p.id, p.user_id;

-- ===============================================
-- 7. تابع‌های کمکی
-- ===============================================

-- 7.1 تابع برای به‌روزرسانی updated_at
CREATE OR REPLACE FUNCTION bedaan_data.update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- تطبیق trigger برای جدول assets
CREATE TRIGGER assets_update_timestamp
BEFORE UPDATE ON bedaan_data.assets
FOR EACH ROW
EXECUTE FUNCTION bedaan_data.update_timestamp();

-- ===============================================
-- 8. مجوزات و کنترل دسترسی
-- ===============================================

-- 8.1 نقش read-only برای عمومی
CREATE ROLE bedaan_readonly;
GRANT CONNECT ON DATABASE bedaanwaves_db TO bedaan_readonly;
GRANT USAGE ON SCHEMA bedaan_data, bedaan_analysis TO bedaan_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA bedaan_data, bedaan_analysis TO bedaan_readonly;

-- 8.2 نقش read-write برای درخواست‌های API
CREATE ROLE bedaan_api;
GRANT CONNECT ON DATABASE bedaanwaves_db TO bedaan_api;
GRANT USAGE ON SCHEMA bedaan_data, bedaan_analysis, bedaan_user TO bedaan_api;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA bedaan_data, bedaan_analysis, bedaan_user TO bedaan_api;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA bedaan_data, bedaan_analysis, bedaan_user TO bedaan_api;

-- ===============================================
-- 9. اطلاعات اولیه (Sample Data)
-- ===============================================

-- 9.1 درج برخی نمادهای معروف بورسی
INSERT INTO bedaan_data.assets (symbol, name, asset_class, market, sector) VALUES
('FSPD', 'فولاد', 'EQUITY', 'TSE', 'معادن'),
('MAPNA', 'مپنا', 'EQUITY', 'TSE', 'ماشین‌آلات'),
('SHTEL', 'شتل', 'EQUITY', 'TSE', 'مخابرات'),
('SAIPA', 'سایپا', 'EQUITY', 'TSE', 'خودروساز'),
('PETR', 'نفت', 'EQUITY', 'TSE', 'انرژی')
ON CONFLICT (symbol) DO NOTHING;

-- ===============================================
-- 10. آمار شروع
-- ===============================================

-- تعداد دارایی‌های وارد شده
SELECT COUNT(*) as total_assets FROM bedaan_data.assets;

-- تأیید ایجاد schema‌ها
SELECT schema_name FROM information_schema.schemata 
WHERE schema_name IN ('bedaan_data', 'bedaan_analysis', 'bedaan_user');

-- ===============================================
-- پایان Script اولیه‌سازی
-- ===============================================

-- نتیجه: پایگاه‌داده آماده برای استفاده است!
-- اکنون می‌توانید Frontend و Backend را شروع کنید.
