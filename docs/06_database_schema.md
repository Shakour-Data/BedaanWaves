# BedaanWaves Database Schema & Migrations

## Overview

BedaanWaves uses PostgreSQL as the primary database with SQLAlchemy 2.0 ORM for object-relational mapping. The schema supports multi-asset financial data including stocks, ETFs, and derivatives.

## Database Connection

```env
DB_DRIVER=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_NAME=bedaanwaves
DB_USER=postgres
DB_PASSWORD=your_secure_password
DATABASE_URL=postgresql://postgres:password@localhost:5432/bedaanwaves
```

## Schema Design Principles

### Naming Conventions
- **Tables**: snake_case, plural (`assets`, `price_candles`, `users`)
- **Columns**: snake_case (`symbol`, `created_at`, `is_active`)
- **Primary Keys**: UUID v4 (`id`)
- **Foreign Keys**: `fk_<table>_<column>`
- **Indexes**: `idx_<table>_<column(s)>`
- **Unique Constraints**: `uix_<table>_<column(s)>`
- **Check Constraints**: `chk_<table>_<rule>`

### Data Types
- **UUID**: Primary keys, foreign keys
- **VARCHAR(n)**: Symbols, names, codes
- **TEXT**: Descriptions, JSON metadata
- **DECIMAL(p,s)**: Financial values (p=20, s=8 for prices)
- **BIGINT**: Large integers (volume, turnover)
- **TIMESTAMP/TIMESTAMPTZ**: All timestamps in UTC
- **JSONB**: Flexible metadata, technical indicators
- **BOOLEAN**: Status flags

## Core Tables

### 1. Assets Table
Central table for all tradable instruments.

```sql
CREATE TABLE assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    asset_class VARCHAR(20) NOT NULL, -- EQUITY, ETF, NEWS
    market VARCHAR(20) NOT NULL, -- NASDAQ, NYSE, TSE, OTC
    sector VARCHAR(100),
    sub_sector VARCHAR(100),
    country_code VARCHAR(2), -- ISO 3166-1 alpha-2
    exchange VARCHAR(50), -- Specific exchange
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB, -- Flexible field for additional info
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Indexes
    INDEX idx_assets_symbol (symbol),
    INDEX idx_assets_class (asset_class),
    INDEX idx_assets_market (market),
    INDEX idx_assets_sector (sector),
    INDEX idx_assets_active (is_active)
);
```

### 2. Price Candles Table
OHLCV price data normalized across all markets.

```sql
CREATE TABLE price_candles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    timestamp TIMESTAMPTZ NOT NULL,
    timeframe VARCHAR(10) NOT NULL, -- 1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, 1m, 3m, 6m, 1y
    open DECIMAL(20, 8) NOT NULL,
    high DECIMAL(20, 8) NOT NULL,
    low DECIMAL(20, 8) NOT NULL,
    close DECIMAL(20, 8) NOT NULL,
    volume BIGINT NOT NULL,
    turnover DECIMAL(20, 2),
    transactions INTEGER,
    adjusted_close DECIMAL(20, 8),
    source VARCHAR(50), -- YahooFinance, BRS, etc.
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT uq_candle UNIQUE (asset_id, timestamp, timeframe),
    
    -- Indexes
    INDEX idx_candle_asset (asset_id),
    INDEX idx_candle_timestamp (timestamp),
    INDEX idx_candle_timeframe (timeframe),
    INDEX idx_candle_asset_timestamp (asset_id, timestamp DESC),
    INDEX idx_candle_timestamp_timeframe (timestamp, timeframe)
);

-- Partitioning for large tables (monthly)
CREATE TABLE price_candles_2024_01 PARTITION OF price_candles
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

### 3. ML Signals Table
Machine learning generated trading signals.

```sql
CREATE TABLE ml_signals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    model_name VARCHAR(100) NOT NULL, -- prediction_service, pattern_recognition_service, etc.
    signal_type VARCHAR(10) NOT NULL, -- BUY, SELL, HOLD
    confidence DECIMAL(5, 2) NOT NULL CHECK (confidence >= 0 AND confidence <= 100),
    expected_return DECIMAL(8, 4), -- percentage
    risk_score DECIMAL(5, 2) CHECK (risk_score >= 0 AND risk_score <= 100),
    reasoning TEXT,
    technical_factors JSONB,
    fundamental_factors JSONB,
    model_version VARCHAR(50),
    generated_at TIMESTAMPTZ DEFAULT NOW(),
    valid_until TIMESTAMPTZ NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Indexes
    INDEX idx_signal_asset (asset_id),
    INDEX idx_signal_model (model_name),
    INDEX idx_signal_type (signal_type),
    INDEX idx_signal_generated (generated_at DESC),
    INDEX idx_signal_active (is_active),
    INDEX idx_signal_valid_until (valid_until)
);
```

### 4. Users Table
User account information.

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    username VARCHAR(100) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    phone VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    role VARCHAR(50) DEFAULT 'user', -- user, moderator, admin
    preferences JSONB, -- Language, timezone, settings
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Indexes
    INDEX idx_users_email (email),
    INDEX idx_users_username (username),
    INDEX idx_users_active (is_active),
    INDEX idx_users_role (role)
);
```

### 5. Portfolios Table
User portfolio definitions.

```sql
CREATE TABLE portfolios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    type VARCHAR(20) DEFAULT 'custom', -- custom, recommendation, watchlist
    is_public BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    risk_level VARCHAR(20), -- conservative, moderate, aggressive
    target_return DECIMAL(8, 4),
    settings JSONB, -- Allocation constraints, rebalancing rules
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Indexes
    INDEX idx_portfolios_user (user_id),
    INDEX idx_portfolios_type (type),
    INDEX idx_portfolios_public (is_public),
    INDEX idx_portfolios_active (is_active)
);
```

### 6. Positions Table
Individual holdings within portfolios.

```sql
CREATE TABLE positions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    asset_id UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    symbol VARCHAR(50) NOT NULL,
    quantity DECIMAL(20, 8) NOT NULL,
    entry_price DECIMAL(20, 8) NOT NULL,
    entry_date DATE NOT NULL,
    current_price DECIMAL(20, 8),
    market_value DECIMAL(20, 2) GENERATED ALWAYS AS (quantity * current_price) STORED,
    pnl DECIMAL(20, 2) GENERATED ALWAYS AS ((current_price - entry_price) * quantity) STORED,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT uq_position UNIQUE (portfolio_id, asset_id),
    
    -- Indexes
    INDEX idx_position_portfolio (portfolio_id),
    INDEX idx_position_asset (asset_id),
    INDEX idx_position_symbol (symbol)
);
```

### 7. Alerts Table
User-defined price/condition alerts.

```sql
CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    asset_id UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    alert_type VARCHAR(20) NOT NULL, -- PRICE, SIGNAL, NEWS, PERFORMANCE
    condition JSONB NOT NULL, -- {operator: '>', value: 100}
    threshold_value DECIMAL(20, 8),
    threshold_percent DECIMAL(8, 4),
    is_active BOOLEAN DEFAULT TRUE,
    triggered_at TIMESTAMPTZ,
    triggered BOOLEAN DEFAULT FALSE,
    notification_sent BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Indexes
    INDEX idx_alert_user_active (user_id, is_active),
    INDEX idx_alert_asset (asset_id),
    INDEX idx_alert_type (alert_type),
    INDEX idx_alert_triggered (triggered)
);
```

### 8. News Articles Table
Aggregated news from multiple sources.

```sql
CREATE TABLE news (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    content TEXT,
    summary TEXT,
    source VARCHAR(100),
    url VARCHAR(1000),
    author VARCHAR(255),
    published_at TIMESTAMPTZ,
    sentiment_score DECIMAL(5, 2), -- -100 to 100
    sentiment_label VARCHAR(20), -- positive, negative, neutral
    entities JSONB, -- Mentioned companies, people, etc.
    related_assets JSONB, -- Array of asset_id references
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Indexes
    INDEX idx_news_published (published_at DESC),
    INDEX idx_news_source (source),
    INDEX idx_news_sentiment (sentiment_score),
    INDEX idx_news_related_assets ((metadata->>'related_assets'))
);
```

### 9. ML Models Table
Machine learning model information and metrics.

```sql
CREATE TABLE ml_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    model_type VARCHAR(50) NOT NULL, -- regression, classification, clustering
    version VARCHAR(50) NOT NULL,
    accuracy DECIMAL(6, 4),
    precision DECIMAL(6, 4),
    recall DECIMAL(6, 4),
    f1_score DECIMAL(6, 4),
    training_date TIMESTAMPTZ,
    last_updated TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB, -- Hyperparameters, training data info
    
    -- Indexes
    INDEX idx_ml_models_name (name),
    INDEX idx_ml_models_type (model_type),
    INDEX idx_ml_models_active (is_active),
    UNIQUE(name, version)
);
```

## Additional Tables

### Symbols Table
Symbol metadata and exchange information.

```sql
CREATE TABLE symbols (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    exchange VARCHAR(50),
    market VARCHAR(20),
    asset_class VARCHAR(20),
    sector VARCHAR(100),
    industry VARCHAR(100),
    country VARCHAR(2),
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    INDEX idx_symbols_exchange (exchange),
    INDEX idx_symbols_market (market)
);
```

### Technical Indicators Table
Pre-computed technical indicators.

```sql
CREATE TABLE technical_indicators (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    timestamp TIMESTAMPTZ NOT NULL,
    indicator_name VARCHAR(100) NOT NULL,
    value DECIMAL(20, 8),
    signal VARCHAR(10), -- BUY, SELL, NEUTRAL
    parameters JSONB, -- Input parameters for calculation
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT uq_indicator UNIQUE (asset_id, timestamp, indicator_name),
    INDEX idx_ti_asset (asset_id),
    INDEX idx_ti_indicator (indicator_name),
    INDEX idx_ti_timestamp (timestamp)
);
```

### User Preferences Table
User customization and settings.

```sql
CREATE TABLE user_preferences (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    default_market VARCHAR(20) DEFAULT 'NASDAQ',
    favorite_sectors JSONB, -- Array of sector strings
    display_settings JSONB, -- Theme, language, timezone
    notification_settings JSONB, -- Email, SMS, push preferences
    analysis_settings JSONB, -- Default indicators, timeframes
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Indexes & Performance

### Primary Key Indexes
All tables have UUID primary key indexes (automatically created).

### Foreign Key Indexes
All foreign key columns are indexed for join performance.

### Search Indexes
```sql
-- Text search for news
CREATE INDEX idx_news_search ON news USING gin(to_tsvector('english', title || ' ' || content));

-- JSONB queries for filters
CREATE INDEX idx_assets_metadata ON assets USING gin(metadata);
```

### Materialized Views
```sql
-- Asset latest prices view
CREATE MATERIALIZED VIEW asset_latest_prices AS
SELECT DISTINCT ON (asset_id)
    asset_id,
    timestamp,
    close AS current_price,
    volume,
    (close - LAG(close) OVER (PARTITION BY asset_id ORDER BY timestamp)) /
        LAG(close) OVER (PARTITION BY asset_id ORDER BY timestamp) * 100 AS day_change_pct
FROM price_candles
WHERE timeframe = '1d'
ORDER BY asset_id, timestamp DESC;
```

## Partitioning Strategy

### Time-Series Tables
- `price_candles`: Monthly partitions
- `news`: Monthly partitions
- `ml_signals`: Monthly partitions
- `api_logs`: Daily partitions

### Example Partition Creation
```sql
-- Master table
CREATE TABLE price_candles (
    LIKE price_candles_template INCLUDING ALL
) PARTITION BY RANGE (timestamp);

-- Monthly partitions
CREATE TABLE price_candles_2024_01 PARTITION OF price_candles
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
    
CREATE TABLE price_candles_2024_02 PARTITION OF price_candles
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');
```

## Alembic Migration Structure

```
database/
└── alembic/
    ├── env.py              # Migration environment
    ├── script.py.mako      # Template for new migrations
    ├── alembic.ini         # Alembic configuration
    └── versions/
        ├── 20240101000000_initial_schema.py
        ├── 20240102000000_add_portfolio_tables.py
        ├── 20240103000000_add_technical_indicators.py
        └── ...             # Version-specific migrations
```

### Migration Commands
```bash
# Create new migration
alembic revision -m "Add new table" --autogenerate

# Apply migrations
alembic upgrade head

# Check for pending migrations
alembic history --verbose

# Rollback
alembic downgrade -1

# Show current version
alembic current
```

## Data Retention & Archiving

### Retention Policies
| Table | Retention | Action |
|-------|-----------|--------|
| price_candles | 10 years | Archive to cold storage |
| news | 2 years | Delete old partitions |
| ml_signals | 1 year | Delete old partitions |
| api_logs | 90 days | Delete old partitions |
| audit_logs | 7 years | Archive to cold storage |
| users | Lifetime | Anonymize on deletion |
| portfolios | Lifetime | Archive on user deletion |

### Archival Process
```sql
-- Export to archive table
CREATE TABLE price_candles_archive (LIKE price_candles INCLUDING ALL);

-- Archive old data
INSERT INTO price_candles_archive 
SELECT * FROM price_candles_2020_01;

DELETE FROM price_candles_2020_01;
```

## Backup & Recovery

### Backup Strategy
```bash
# Daily logical backup
pg_dump -U postgres -d bedaanwaves > /backups/bedaanwaves_$(date +%Y%m%d).sql

# Hourly WAL archiving (postgresql.conf)
archive_mode = on
archive_command = 'cp %p /wal_archive/%f'

# Point-in-time recovery setup
restore_command = 'cp /wal_archive/%f %p'
recovery_target_time = '2024-01-01 12:00:00'
```

### Recovery Process
```bash
# Stop PostgreSQL
systemctl stop postgresql

# Restore base backup
pg_restore -U postgres -d bedaanwaves_restore /backups/base_backup.dump

# Apply WAL logs
pg_waldump /wal_archive/ | pg_rewind --target-pgdata=/var/lib/postgresql/16/main

# Start PostgreSQL
systemctl start postgresql
```

## Read Replicas (Optional)

### Replication Setup
```sql
-- On master
wal_level = replica
max_wal_senders = 10
max_replication_slots = 10

-- On replica
primary_conninfo = 'host=master port=5432 user=replicator password=pass'
hot_standby = on
```

### Connection Configuration
```python
# Use read replica for SELECT queries
if query_type == 'SELECT':
    engine = create_engine('postgresql://replica')
else:
    engine = create_engine('postgresql://master')
```

---
*Last Updated: 2026-08-28*
*Status: Production Ready - Schema Defined and Migrations Ready*