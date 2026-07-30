# === Database Schema for User Preferences and Data Sources ===

-- Create user preferences table
CREATE TABLE IF NOT EXISTS user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    countries JSONB DEFAULT '[]',
    indices JSONB DEFAULT '[]',
    industries JSONB DEFAULT '[]',
    crypto JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_validated TIMESTAMP WITH TIME ZONE,
    validation_hash VARCHAR(64)
);

-- Create historical data storage with source tracking
CREATE TABLE IF NOT EXISTS historical_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source VARCHAR(100) NOT NULL,
    symbol VARCHAR(50) NOT NULL,
    data_type VARCHAR(50) NOT NULL,
    country VARCHAR(50),
    industry VARCHAR(50),
    exchange VARCHAR(50),
    data_date DATE NOT NULL,
    open_price DECIMAL(18,8),
    high_price DECIMAL(18,8),
    low_price DECIMAL(18,8),
    close_price DECIMAL(18,8),
    volume DECIMAL(18,8),
    market_cap DECIMAL(20,8),
    change_percent DECIMAL(10,6),
    raw_data JSONB,
    source_verified BOOLEAN DEFAULT FALSE,
    source_authenticity VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_source_symbol_date UNIQUE (source, symbol, data_date)
);

-- Create user market configurations table
CREATE TABLE IF NOT EXISTS user_market_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    config_name VARCHAR(100) NOT NULL,
    country VARCHAR(50),
    country_indices JSONB DEFAULT '[]',
    selected_industries JSONB DEFAULT '[]',
    included_symbols JSONB DEFAULT '[]',
    price_range JSONB,
    volume_range JSONB,
    change_filter JSONB,
    market_cap_filter JSONB,
    last_calc TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create user crypto configurations table
CREATE TABLE IF NOT EXISTS user_crypto_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    config_name VARCHAR(100) NOT NULL,
    included_symbols JSONB DEFAULT '[]',
    excluded_symbols JSONB DEFAULT '[]',
    exchange_source VARCHAR(50) DEFAULT 'binance',
    min_volume_24h DECIMAL(20,8),
    min_market_cap DECIMAL(20,8),
    price_range JSONB,
    change_filter JSONB,
    last_calc TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create scoring results table (based on user preferences)
CREATE TABLE IF NOT EXISTS user_scoring_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    source VARCHAR(100) NOT NULL,
    symbol VARCHAR(50) NOT NULL,
    country VARCHAR(50),
    industry VARCHAR(50),
    exchange VARCHAR(50),
    score DECIMAL(10,6),
    rank INT,
    data_date DATE NOT NULL,
    criteria_scores JSONB,
    user_preferences JSONB,
    recommendations JSONB,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_user_symbol_date UNIQUE (user_id, symbol, data_date)
);

-- Create data sources validation table
CREATE TABLE IF NOT EXISTS data_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_name VARCHAR(100) NOT NULL,
    source_type VARCHAR(50) NOT NULL,
    base_url VARCHAR(500),
    api_key_required BOOLEAN DEFAULT FALSE,
    auth_token VARCHAR(500),
    data_format VARCHAR(50),
    last_verification TIMESTAMP WITH TIME ZONE,
    verification_count INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create historical data import logs
CREATE TABLE IF NOT EXISTS historical_data_import_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    import_batch_id VARCHAR(100) NOT NULL,
    source_id UUID REFERENCES data_sources(id),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    records_imported INT DEFAULT 0,
    records_updated INT DEFAULT 0,
    validation_results JSONB,
    import_status VARCHAR(50) DEFAULT 'pending',
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create cryptocurrency master list table
CREATE TABLE IF NOT EXISTS cryptocurrencies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    exchange VARCHAR(50),
    market_cap DECIMAL(20,8),
    volume_24h DECIMAL(20,8),
    price_usd DECIMAL(20,8),
    price_change_24h DECIMAL(10,6),
    price_change_7d DECIMAL(10,6),
    market_cap_rank INT,
    circulating_supply DECIMAL(20,8),
    max_supply DECIMAL(20,8),
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB
);

-- Create countries list table
CREATE TABLE IF NOT EXISTS countries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    iso_code VARCHAR(10) NOT NULL,
    stock_exchange VARCHAR(100),
    currency_code VARCHAR(10),
    timezone VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB,
    last_verified TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create industries list table
CREATE TABLE IF NOT EXISTS industries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    sector VARCHAR(100),
    etf_ticker VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB,
    last_verified TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create market indices table
CREATE TABLE IF NOT EXISTS market_indices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    exchange VARCHAR(100),
    country VARCHAR(50),
    base_value DECIMAL(20,8),
    current_value DECIMAL(20,8),
    change_percent DECIMAL(10,6),
    volume DECIMAL(18,8),
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB,
    is_active BOOLEAN DEFAULT TRUE
);

-- Create indices_industries mapping table
CREATE TABLE IF NOT EXISTS indices_industries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    index_id UUID REFERENCES market_indices(id),
    industry_id UUID REFERENCES industries(id),
    weight DECIMAL(10,6),
    is_active BOOLEAN DEFAULT TRUE
);

-- Create stock_industries mapping table
CREATE TABLE IF NOT EXISTS stock_industries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol VARCHAR(50) NOT NULL,
    industry_id UUID REFERENCES industries(id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create country stock mapping table
CREATE TABLE IF NOT EXISTS country_stocks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol VARCHAR(50) NOT NULL UNIQUE,
    country_id UUID REFERENCES countries(id),
    exchange VARCHAR(100),
    stock_type VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_verified TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create user favorites table
CREATE TABLE IF NOT EXISTS user_favorites (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    source VARCHAR(100) NOT NULL,
    symbol VARCHAR(50) NOT NULL,
    category VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create user alerts table
CREATE TABLE IF NOT EXISTS user_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    symbol VARCHAR(50) NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    alert_condition JSONB NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    notify_method JSONB DEFAULT '{"email": true, "push": true, "sms": false}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_triggered TIMESTAMP WITH TIME ZONE
);