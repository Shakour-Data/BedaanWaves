# Raw Data Storage in Database

This document describes how raw data received from various data sources is stored in the PostgreSQL database.

## 1. Database Schema Overview

### Core Tables

#### `raw_data`
Stores raw, unprocessed data received from external APIs.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| source | VARCHAR(50) | Data source name (nasdaq, tehran, coinbase, etc.) |
| market_type | VARCHAR(20) | Market type (stock, index, crypto, forex) |
| symbol | VARCHAR(20) | Ticker or symbol identifier |
| raw_payload | JSONB | Complete raw response from API |
| received_at | TIMESTAMPTZ | Timestamp when data was received |
| status | VARCHAR(20) | Status: pending, validated, processed, failed |
| retry_count | INT | Number of retry attempts |
| error_message | TEXT | Error details if processing failed |
| created_at | TIMESTAMPTZ | Record creation timestamp |
| updated_at | TIMESTAMPTZ | Record update timestamp |

#### `processed_data`
Stores validated and normalized data ready for analysis.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| raw_data_id | UUID | Foreign key to raw_data |
| source | VARCHAR(50) | Data source name |
| market_type | VARCHAR(20) | Market type |
| symbol | VARCHAR(20) | Ticker or symbol |
| data_type | VARCHAR(50) | Type of data (price, volume, index, fundamental) |
| normalized_payload | JSONB | Normalized data structure |
| currency | VARCHAR(10) | Currency of the data (USD, IRR, etc.) |
| processed_at | TIMESTAMPTZ | Timestamp when data was processed |
| quality_score | FLOAT | Data quality score (0.0 - 1.0) |
| created_at | TIMESTAMPTZ | Record creation timestamp |

#### `market_indices`
Stores index-level data from all markets.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| index_code | VARCHAR(20) | Index identifier (^IXIC, TSE-ALL, etc.) |
| market_type | VARCHAR(20) | Market type |
| exchange | VARCHAR(50) | Exchange name |
| name | VARCHAR(100) | Index full name |
| current_value | FLOAT | Current index value |
| change_percent | FLOAT | Percent change |
| change_absolute | FLOAT | Absolute change |
| high | FLOAT | Day high |
| low | FLOAT | Day low |
| volume | BIGINT | Trading volume |
| timestamp | TIMESTAMPTZ | Data timestamp |
| source | VARCHAR(50) | Data source |
| created_at | TIMESTAMPTZ | Record creation timestamp |

#### `stock_prices`
Stores individual stock price data.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| symbol | VARCHAR(20) | Stock ticker |
| market_type | VARCHAR(20) | Market type |
| exchange | VARCHAR(50) | Exchange name |
| open | FLOAT | Opening price |
| high | FLOAT | Day high |
| low | FLOAT | Day low |
| close | FLOAT | Closing price |
| volume | BIGINT | Trading volume |
| adjusted_close | FLOAT | Adjusted closing price |
| currency | VARCHAR(10) | Currency |
| timestamp | TIMESTAMPTZ | Price timestamp |
| source | VARCHAR(50) | Data source |
| created_at | TIMESTAMPTZ | Record creation timestamp |

#### `fundamental_data`
Stores fundamental financial data.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| symbol | VARCHAR(20) | Stock ticker |
| market_type | VARCHAR(20) | Market type |
| report_type | VARCHAR(50) | Report type (income_statement, balance_sheet, cash_flow) |
| fiscal_period | VARCHAR(20) | Fiscal period (Q1, Q2, FY, etc.) |
| fiscal_year | INT | Fiscal year |
| metric_name | VARCHAR(100) | Metric identifier |
| metric_value | FLOAT | Metric value |
| unit | VARCHAR(20) | Unit of measurement |
| source | VARCHAR(50) | Data source |
| reported_date | DATE | Date reported in source |
| created_at | TIMESTAMPTZ | Record creation timestamp |

#### `crypto_prices`
Stores cryptocurrency price data.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| symbol | VARCHAR(20) | Crypto symbol (BTC, ETH, etc.) |
| price | FLOAT | Current price |
| market_cap | BIGINT | Market capitalization |
| volume_24h | BIGINT | 24-hour trading volume |
| high_24h | FLOAT | 24-hour high |
| low_24h | FLOAT | 24-hour low |
| change_percent | FLOAT | Percent change |
| timestamp | TIMESTAMPTZ | Price timestamp |
| source | VARCHAR(50) | Data source |
| created_at | TIMESTAMPTZ | Record creation timestamp |

#### `forex_rates`
Stores foreign exchange rate data.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| base_currency | VARCHAR(10) | Base currency code (USD, IRR, etc.) |
| target_currency | VARCHAR(10) | Target currency code |
| rate | FLOAT | Exchange rate |
| inverse_rate | FLOAT | Inverse exchange rate |
| timestamp | TIMESTAMPTZ | Rate timestamp |
| source | VARCHAR(50) | Data source |
| created_at | TIMESTAMPTZ | Record creation timestamp |

## 2. Data Ingestion Pipeline

### Step 1: Data Reception
```
[External API] → [API Client] → [raw_data table]
```
- API clients (NasdaqApiClient, TehranApiClient, CryptoApiClient, ForexClient) fetch data
- Raw responses are stored in `raw_data` table with `status = 'pending'`
- Each record includes the complete API response in `raw_payload`

### Step 2: Validation
```
[raw_data] → [DataValidationService] → [processed_data table]
```
- `DataValidationService` validates raw data structure and completeness
- Invalid records are marked `status = 'failed'` with error details
- Valid records proceed to normalization

### Step 3: Normalization
```
[processed_data] → [Normalization Pipeline] → Market-specific tables
```
- Data is normalized to a unified format
- Currency conversion applied via `CurrencyConversionService`
- Normalized records stored in `processed_data` table

### Step 4: Distribution
```
[processed_data] → [Market-specific tables]
```
- Processed data is distributed to appropriate tables:
  - Stock prices → `stock_prices`
  - Index data → `market_indices`
  - Fundamentals → `fundamental_data`
  - Crypto → `crypto_prices`
  - Forex → `forex_rates`

## 3. Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        EXTERNAL APIs                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
│  │ Nasdaq   │  │ Tehran   │  │ CoinGecko│  │ Forex APIs   │   │
│  │ (yfinance)│  │ (BRS)    │  │ Binance  │  │ (ECB, FRED)  │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──────┬───────┘   │
│       │              │              │                │           │
└───────┼──────────────┼──────────────┼────────────────┼───────────┘
        │              │              │                │
        ▼              ▼              ▼                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    raw_data Table                               │
│  (All incoming data stored here with status = 'pending')        │
└─────────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│                  DataValidationService                          │
│  (Validates structure, completeness, and data types)            │
└─────────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│                  CurrencyConversionService                      │
│  (Normalizes all monetary values to base currency)              │
└─────────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│                  processed_data Table                           │
│  (Validated and normalized data ready for distribution)         │
└─────────────────────────────────────────────────────────────────┘
        │
        ├──────────────┬──────────────┬──────────────┬────────────┐
        ▼              ▼              ▼              ▼            ▼
┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌──────────┐
│stock_prices│ │market_indices│ │fundamental │ │crypto_prices│ │forex_rates│
│            │ │             │ │_data       │ │            │ │          │
└────────────┘ └────────────┘ └────────────┘ └────────────┘ └──────────┘
```

## 4. Storage Strategies

### 4.1 Raw Data Retention
- Raw data retained for 90 days by default
- Configurable via `RAW_DATA_RETENTION_DAYS` setting
- Archived data moved to cold storage after retention period

### 4.2 Processed Data Retention
- Processed data retained indefinitely for analysis
- Aggregated data summarized daily for performance
- Historical data partitioned by date for efficient querying

### 4.3 Index Data
- Index values stored at 1-minute intervals during trading hours
- End-of-day summaries stored for historical analysis
- Index constituents updated daily

### 4.4 Fundamental Data
- Quarterly reports stored with fiscal period metadata
- Annual reports retained permanently
- Data versioning tracks changes over time

## 5. Data Quality Framework

### Quality Checks
1. **Completeness**: All required fields present
2. **Type Validation**: Data types match expected schema
3. **Range Validation**: Values within expected ranges
4. **Temporal Consistency**: Timestamps are sequential and valid
5. **Currency Consistency**: All monetary values in expected currency

### Quality Scoring
- Each processed record receives a quality score (0.0 - 1.0)
- Scores based on:
  - Source reliability
  - Data completeness
  - Validation pass rate
  - Temporal freshness

### Quality Thresholds
- `quality_score >= 0.9`: High confidence, used for analysis
- `quality_score >= 0.7`: Medium confidence, flagged for review
- `quality_score < 0.7`: Low confidence, excluded from analysis

## 6. Database Indexes

### Performance Indexes
```sql
-- Raw data indexes
CREATE INDEX idx_raw_data_source_symbol ON raw_data(source, symbol, received_at);
CREATE INDEX idx_raw_data_status ON raw_data(status, received_at);

-- Stock prices indexes
CREATE INDEX idx_stock_prices_symbol_time ON stock_prices(symbol, market_type, timestamp);
CREATE INDEX idx_stock_prices_exchange ON stock_prices(exchange, timestamp);

-- Market indices indexes
CREATE INDEX idx_market_indices_code_time ON market_indices(index_code, timestamp);
CREATE INDEX idx_market_indices_exchange ON market_indices(exchange, timestamp);

-- Fundamental data indexes
CREATE INDEX idx_fundamental_symbol_period ON fundamental_data(symbol, fiscal_period, fiscal_year);
CREATE INDEX idx_fundamental_metric ON fundamental_data(metric_name, symbol);

-- Crypto prices indexes
CREATE INDEX idx_crypto_prices_symbol_time ON crypto_prices(symbol, timestamp);

-- Forex rates indexes
CREATE INDEX idx_forex_rates_pair_time ON forex_rates(base_currency, target_currency, timestamp);
```

## 7. Data Archival Strategy

### Archival Tiers
| Tier | Data Type | Retention | Storage |
|------|-----------|-----------|---------|
| Hot | Real-time prices | 30 days | PostgreSQL (active) |
| Warm | Daily aggregates | 1 year | PostgreSQL (partitioned) |
| Cold | Historical raw data | 5 years | Compressed archives |
| Archive | Regulatory data | 7+ years | Cold storage |

### Archival Process
1. Daily job identifies records exceeding retention period
2. Records compressed and moved to archival storage
3. Metadata retained in database for query routing
4. Archived data accessible via API with increased latency

## 8. Backup Strategy

### Backup Schedule
- **Full backup**: Daily at 02:00 UTC
- **Incremental backup**: Every 4 hours
- **WAL archiving**: Continuous

### Recovery Procedures
1. Identify recovery point (timestamp or transaction ID)
2. Restore from latest full backup
3. Apply incremental backups in sequence
4. Replay WAL logs to desired point in time
5. Verify data integrity and consistency

## 9. Configuration Settings

### Storage Configuration (config.py)
```python
# Raw data retention
RAW_DATA_RETENTION_DAYS: int = 90

# Processed data retention
PROCESSED_DATA_RETENTION_DAYS: int = None  # Indefinite

# Index data granularity
INDEX_DATA_INTERVAL_MINUTES: int = 1

# Quality thresholds
QUALITY_SCORE_HIGH: float = 0.9
QUALITY_SCORE_MEDIUM: float = 0.7

# Archive settings
ARCHIVE_COMPRESSION_ENABLED: bool = True
ARCHIVE_STORAGE_PATH: str = "./archive"
```

## 10. API Endpoints for Data Access

### Raw Data Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/data/raw` | GET | Query raw data by source, symbol, date range |
| `/api/v1/data/raw/{id}` | GET | Get specific raw data record |
| `/api/v1/data/raw/stats` | GET | Get raw data statistics |

### Processed Data Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/data/processed` | GET | Query processed data |
| `/api/v1/data/processed/{id}` | GET | Get specific processed record |
| `/api/v1/data/processed/quality` | GET | Get data quality metrics |

### Market-Specific Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/stocks/{symbol}/prices` | GET | Get stock price history |
| `/api/v1/indices/{code}` | GET | Get index data |
| `/api/v1/crypto/{symbol}/prices` | GET | Get crypto price history |
| `/api/v1/forex/{base}/{target}` | GET | Get forex rate history |
| `/api/v1/fundamental/{symbol}` | GET | Get fundamental data |

## 11. Data Lineage Tracking

Every record in `processed_data` tracks its lineage:
- Source API and endpoint
- Raw data record ID
- Processing timestamp
- Validation checks performed
- Currency conversion applied
- Quality score and validation status

This enables full traceability from raw API response to analysis-ready data.