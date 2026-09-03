# BedaanWaves Tier 2: Data Services

## Overview

Tier 2 Data Services handle external data acquisition, normalization, storage, and management across multiple asset classes. These services integrate with external APIs, process raw data into unified formats, and provide database operations for market data, stocks, portfolios, and news.

**Implementation Status**: 6/13 Complete (46%)
**Service Count**: 13 services
**Location**: `backend/app/services/data/`

## YahooFinanceClient (NASDAQ API)

**File**: `app/services/data/yahoo_finance_client.py`

### Purpose
Integration with the NASDAQ API for retrieving market data, stock information, and financial data from US markets.

### Key Features
- RESTful API integration with Yahoo Finance endpoints
- Symbol list retrieval and search
- Historical price data with OHLCV format
- Financial statement data extraction
- Rate limiting and error handling
- Automatic data normalization to BedaanWaves unified schema

### API Endpoints Integration
| Endpoint | Description | Parameters |
|----------|-------------|------------|
| `/symbols` | List available symbols | market, active_only |
| `/symbol/{symbol}` | Get symbol details | symbol |
| `/history/{symbol}` | Historical price data | symbol, start_date, end_date, interval |
| `/fundamentals/{symbol}` | Financial statements | symbol |
| `/indices` | Market indices | index_type |
| `/search` | Search symbols | query, exchange |

### Authentication
  - API key in header: `X-API-Key: <your-yahoo-finance-key>`
- Rate limit: 50,000 requests per 300 seconds (configurable)

### Data Normalization
Raw Yahoo Finance data is normalized to the unified schema:
```python
# Example: Normalize price candle
candle = {
    "asset_id": asset_uuid,
    "timestamp": datetime.utcnow(),
    "timeframe": "1d",
    "open": Decimal(open_price),
    "high": Decimal(high_price),
    "low": Decimal(low_price),
    "close": Decimal(close_price),
    "volume": int(volume),
    "turnover": Decimal(turnover),
    "source": "YAHOO_FINANCE"
}
```

### Usage
```python
from app.services.data.yahoo_finance_client import YahooFinanceClient

client = YahooFinanceClient(
    api_key="your-yahoo-finance-key",
    base_url="https://api.yahoofinance.com",
    timeout=30
)

# Get symbols
symbols = await client.get_symbols(market="NASDAQ", active_only=True)

# Get historical data
history = await client.get_historical_data(
    symbol="FSPD",
    start_date="2024-01-01",
    end_date="2024-08-17",
    interval="1d"
)
```

### Key Methods
| Method | Description |
|--------|-------------|
| `get_symbols(market, active_only)` | Get symbols from exchange |
| `get_symbol_detail(symbol)` | Get symbol metadata |
| `get_historical_data(symbol, start, end, interval)` | Historical OHLCV data |
| `get_fundamentals(symbol)` | Financial statement data |
| `get_indices(index_type)` | Market indices |
| `search_symbols(query, exchange)` | Search symbols |

---

## StockService (Stock Data Management)

**File**: `app/services/data/stock_service.py`

### Purpose
Manages stock data operations including CRUD operations, symbol management, and portfolio integration. Core service for stock-related data lifecycle.

### Key Features
- Database-backed stock data management
- Symbol metadata operations
- Portfolio integration
- Historical data retrieval
- Symbol search and filtering
- Active/inactive status management

### Database Operations
```python
# Create or update symbol
stock = await stock_service.create_or_update({
    "symbol": "AAPL",
    "name": "Apple Inc.",
    "asset_class": "EQUITY",
    "market": "NASDAQ",
    "sector": "Technology",
    "is_active": True
})

# Get symbol by ID
stock = await stock_service.get_by_id(symbol_id)

# Search symbols
results = await stock_service.search({
    "query": "bank",
    "sector": "Banking",
    "active_only": True,
    "limit": 20
})

# Get latest price
latest = await stock_service.get_latest_price(symbol_id)

# Check if active
is_active = await stock_service.is_active(symbol_id)
```

### Portfolio Integration
StockService integrates with PortfolioService:
- Tracks which stocks are held in which portfolios
- Updates market values based on current prices
- Calculates portfolio performance metrics

### Usage
```python
from app.services.data.stock_service import StockService

service = StockService()

# Add new stock to database
await service.create_or_update({
    "symbol": "AAPL",
    "name": "Apple Inc.",
    "asset_class": "EQUITY",
    "market": "NASDAQ",
    "sector": "Technology"
})

# Search for stocks
results = await service.search(query="auto", sector="Automotive")

# Get active stocks only
active = await service.list_active(limit=100)
```

### Key Methods
| Method | Description |
|--------|-------------|
| `create_or_update(data)` | Upsert symbol with metadata |
| `get_by_id(symbol_id)` | Get symbol by database ID |
| `search(query, filters)` | Search symbols with filters |
| `list_active(limit, offset)` | List active symbols |
| `get_latest_price(symbol_id)` | Get most recent price |
| `is_active(symbol_id)` | Check if symbol is active |

---

## MarketService (Market Data Aggregation)

**File**: `app/services/data/market_service.py`

### Purpose
Aggregates market-wide data including indices, sector performance, market statistics, and provides market-level analytics. Central point for market overview data.

### Key Features
- Market index calculation and tracking
- Sector performance analysis
- Market statistics (gainers, losers, most active)
- Market sentiment indicators
- Comparative market analysis
- Time-series market data

### Market Index Calculation
```python
# Example: Calculate NASDAQ 100 index
def calculate_nasdaq100(symbols):
    """Calculate weighted index from 100 largest companies"""
    weights = get_market_cap_weights(symbols[:100])
    prices = [get_latest_price(s) for s in symbols[:100]]
    index_value = sum(w * p for w, p in zip(weights, prices)) / sum(weights)
    return index_value
```

### Sector Performance
```python
# Calculate sector performance
sector_stats = await market_service.get_sector_performance({
    "timeframe": "1d",
    "market": "NASDAQ"
})

# Returns: {sector: {"return_pct": 2.3, "change": 56.7, "count": 12}}
```

### Market Statistics
```python
# Get market overview
overview = await market_service.get_overview({
    "market": "NASDAQ",
    "timeframe": "1d"
})

# Returns: {
#   "gainers": [...],
#   "losers": [...],
#   "most_active": [...],
#   "volume_total": 1250000000,
#   "advances": 450,
#   "declines": 320
# }
```

### Usage
```python
from app.services.data.market_service import MarketService

service = MarketService()

# Get NASDAQ overview
overview = await service.get_overview(market="NASDAQ")

# Sector performance
sector = await service.get_sector_performance(market="NASDAQ", timeframe="1w")

# Market indices
indices = await service.get_indices(market="NASDAQ", index_types=["NASDAQ100", "S&P_500"])
```

### Key Methods
| Method | Description |
|--------|-------------|
| `get_overview(market, timeframe)` | Market-wide statistics |
| `get_sector_performance(market, timeframe)` | Sector analysis |
| `get_indices(market, index_types)` | Index values |
| `get_gainers_losers(market, timeframe)` | Top performers |
| `get_most_active(market, timeframe)` | Most traded |
| `get_sector_constituents(sector, market)` | Companies in sector |

---

## PortfolioService (Portfolio Operations)

**File**: `app/services/data/portfolio_service.py`

### Purpose
Handles portfolio creation, modification, holdings management, and portfolio performance calculations. User-facing portfolio management system.

### Key Features
- Portfolio CRUD operations (create, read, update, delete)
- Holdings management (add, modify, remove positions)
- Position tracking with cost basis
- Performance attribution and analytics
- Portfolio rebalancing recommendations
- Public/private portfolio support
- Portfolio sharing and permissions

### Portfolio Lifecycle
```python
# Create new portfolio
portfolio = await portfolio_service.create({
    "user_id": user_uuid,
    "name": "My Conservative Portfolio",
    "description": "Balanced allocation across sectors",
    "is_public": False,
    "risk_level": "moderate",
    "target_return": 0.12  # 12% annual target
})

# Add holdings
position = await portfolio_service.add_holding({
    "portfolio_id": portfolio.id,
    "symbol": "FSPD",
    "quantity": 1000,
    "entry_price": 15000.0
})

# Update holdings
await portfolio_service.update_holding({
    "position_id": position.id,
    "quantity": 1500,
    "current_price": 15500.0
})

# Get performance
performance = await portfolio_service.get_performance(portfolio.id)
```

### Performance Calculation
```python
# Calculate portfolio metrics
metrics = await portfolio_service.calculate_metrics({
    "portfolio_id": portfolio.id,
    "start_date": "2024-01-01",
    "end_date": "2024-08-17"
})

# Returns: {
#   "total_return_pct": 8.5,
#   "absolute_return": 1020000,
#   "daily_return_pct": 0.12,
#   "sharpe_ratio": 1.23,
#   "max_drawdown": -3.4,
#   "volatility": 0.15
# }
```

### Usage
```python
from app.services.data.portfolio_service import PortfolioService

service = PortfolioService(user_id=user_uuid)

# Create portfolio
portfolio = await service.create_portfolio({
    "name": "Tech Growth",
    "description": "Technology sector focus",
    "risk_level": "aggressive"
})

# Add AAPL position
await service.add_holding({
    "portfolio_id": portfolio.id,
    "symbol": "AAPL",
    "quantity": 10,
    "entry_price": 185.50
})

# Remove position
await service.remove_holding({
    "portfolio_id": portfolio.id,
    "symbol": "MSFT"
})

# Get performance
perf = await service.get_performance(portfolio.id)
```

### Key Methods
| Method | Description |
|--------|-------------|
| `create_portfolio(data)` | Create new portfolio |
| `get_portfolio(portfolio_id)` | Get portfolio details |
| `update_portfolio(portfolio_id, data)` | Update portfolio |
| `delete_portfolio(portfolio_id)` | Delete portfolio |
| `add_holding(data)` | Add position to portfolio |
| `update_holding(data)` | Update position |
| `remove_holding(portfolio_id, symbol)` | Remove position |
| `get_performance(portfolio_id)` | Calculate performance metrics |
| `get_allocation(portfolio_id)` | Asset allocation breakdown |

---

## HistoryService (Historical Data)

**File**: `app/services/data/history_service.py`

### Purpose
Manages historical price data, score history, signal history, and prediction history retrieval. Time-series data access layer for analytical computations.

### Key Features
- Historical price data retrieval
- Score and signal history
- Prediction and model output history
- Date range filtering
- Timeframe support (1m, 5m, 15m, 1h, 1d, 1w, 1M)
- Data pagination and optimization
- Cache integration for frequent queries

### Date Range Queries
```python
# Get price history for a symbol
history = await history_service.get_price_history({
    "symbol_id": symbol_uuid,
    "start_date": "2024-01-01",
    "end_date": "2024-08-17",
    "timeframe": "1d",
    "limit": 252  # Trading days
})

# Example result structure
{
    "symbol": "FSPD",
    "data": [
        {
            "timestamp": "2024-01-02T00:00:00Z",
            "open": 14500.0,
            "high": 14750.0,
            "low": 14400.0,
            "close": 14650.0,
            "volume": 1500000,
            "turnover": 22000000000.0
        },
        # ... more entries
    ]
}
```

### Timeframe Support
| Timeframe | Resolution | Use Case |
|-----------|------------|----------|
| `1m` | 1 minute | Intraday scalping |
| `5m` | 5 minutes | Intraday trading |
| `15m` | 15 minutes | Short-term trading |
| `1h` | 1 hour | Intraday trend |
| `4h` | 4 hours | Short-term trend |
| `1d` | 1 day | Daily analysis |
| `1w` | 1 week | Weekly trends |
| `1M` | 1 month | Monthly analysis |

### Usage
```python
from app.services.data.history_service import HistoryService

service = HistoryService()

# Get 1-year daily history
history = await service.get_price_history({
    "symbol_id": symbol_uuid,
    "start_date": "2023-08-17",
    "end_date": "2024-08-17",
    "timeframe": "1d"
})

# Get recent 30 days
recent = await service.get_price_history({
    "symbol_id": symbol_uuid,
    "start_date": "2024-07-18",
    "end_date": "2024-08-17",
    "timeframe": "1d",
    "limit": 30
})

# Get hourly data for intraday
hourly = await service.get_price_history({
    "symbol_id": symbol_uuid,
    "start_date": "2024-08-17T09:00:00Z",
    "end_date": "2024-08-17T17:00:00Z",
    "timeframe": "1h"
})
```

### Key Methods
| Method | Description |
|--------|-------------|
| `get_price_history(symbol_id, start, end, timeframe, limit)` | Historical price data |
| `get_score_history(symbol_id, start, end)` | Score history |
| `get_signal_history(symbol_id, start, end)` | Signal history |
| `get_prediction_history(symbol_id, start, end)` | Prediction history |
| `get_daily_vwap(symbol_id, start, end)` | Volume-weighted average price |
| `get_dividend_history(symbol_id, start, end)` | Dividend payments |

---

## NewsService (News Integration)

**File**: `app/services/data/news_service.py`

### Purpose
Integrates with news APIs for market news aggregation, sentiment analysis, and categorization. Provides news retrieval, filtering, and processing capabilities.

### Key Features
- Multi-source news aggregation
- News categorization (earnings, mergers, analysis, etc.)
- Sentiment scoring and storage
- Symbol extraction from news content
- Deduplication and filtering
- Priority-based ranking
- Archive and retention policies

### News Sources Integration
| Source | Type | Coverage |
|--------|------|----------|
| Yahoo Finance News | US market | NASDAQ-listed companies |
| Financial APIs | Global | International markets |
| RSS Feeds | Configurable | Custom sources |
| Social Media | Twitter/X | Market sentiment |
| Press Releases | Corporate | Company announcements |

### Sentiment Processing
```python
# Process news sentiment
news_item = {
    "title": "Company X reports record profits",
    "content": "...",
    "source": "reuters",
    "published_at": datetime.utcnow(),
    "symbols": ["X"],
    "sentiment_score": 0.85,  # -100 to 100 scale
    "sentiment_label": "positive"
}

# Store with sentiment analysis
await news_service.process_and_store(news_item)
```

### Symbol Extraction
Automatic extraction of stock tickers from news content:
```python
# Extract tickers from news
tickers = await news_service.extract_tickers({
    "title": "Apple reports strong earnings",
    "content": "AAPL stock rose 5% on strong iPhone sales..."
})

# Returns: ["AAPL"]
```

### News Filtering
```python
# Filter news by criteria
filtered = await news_service.filter_news({
    "symbol": "AAPL",
    "sentiment_min": 0.5,  # Only positive
    "source": ["reuters", "bloomberg"],
    "date_from": "2024-01-01",
    "date_to": "2024-08-17",
    "limit": 20
})
```

### Usage
```python
from app.services.data.news_service import NewsService

service = NewsService()

# Get news for symbol
news = await service.get_by_symbol({
    "symbol": "AAPL",
    "limit": 10,
    "sentiment_min": 0.3
})

# Search news by query
results = await service.search({
    "query": "earnings report",
    "symbol": "AAPL",
    "date_from": "2024-01-01"
})

# Get top news
top = await service.get_top_news({
    "limit": 5,
    "timeframe": "24h"
})
```

### Key Methods
| Method | Description |
|--------|-------------|
| `get_by_symbol(symbol, limit, sentiment_min)` | News for specific symbol |
| `search(query, symbol, date_from, date_to)` | Search news |
| `get_top_news(limit, timeframe)` | Top/trending news |
| `extract_tickers(text)` | Extract stock tickers |
| `filter_news(filters)` | Filter news by criteria |
| `process_and_store(news_item)` | Process and persist news |

---

## IngestionService (Data Ingestion Pipelines)

**File**: `app/services/data/ingestion_service.py`

### Purpose
Orchestrates data ingestion pipelines from multiple external sources into the unified BedaanWaves database. Pipeline management and scheduling.

### Key Features
- Multi-source pipeline orchestration
- Scheduled data ingestion
- Progress tracking and reporting
- Error handling and retry logic
- Parallel data source ingestion
- Pipeline status monitoring
- Dependency management between data sources

### Pipeline Architecture
```python
# Example: Daily ingestion pipeline
pipeline_steps = [
    {"source": "yahoo", "task": "fetch_symbols"},
    {"source": "yahoo", "task": "fetch_price_data"},
    {"source": "yahoo", "task": "fetch_fundamentals"},
    {"source": "news", "task": "fetch_market_news"},
    {"source": "processing", "task": "normalize_and_store"}
]

# Run pipeline
result = await ingestion_service.run_pipeline(pipeline_steps)
```

### Pipeline Status Tracking
```python
# Get pipeline status
status = await ingestion_service.get_pipeline_status("daily_ingestion")

# Returns:
{
    "pipeline": "daily_ingestion",
    "status": "running|completed|failed",
    "progress": 75,  # percentage
    "last_run": "2024-08-16T23:00:00Z",
    "records_processed": 15000,
    "errors": []
}
```

### Retry Logic
```python
# Automatic retry configuration
retry_config = {
    "max_retries": 3,
    "backoff_factor": 2,  # Exponential backoff
    "initial_delay": 30,  # seconds
    "max_delay": 300  # seconds
}
```

### Usage
```python
from app.services.data.ingestion_service import IngestionService

service = IngestionService()

# Run single pipeline step
result = await service.run_step({
    "source": "yahoo",
    "task": "fetch_price_data",
    "symbols": ["AAPL", "MSFT", "GOOGL"],
    "timeframe": "1d",
    "start_date": "2024-01-01"
})

# Get pipeline history
history = await service.get_history({
    "pipeline": "daily_ingestion",
    "date_from": "2024-08-01",
    "date_to": "2024-08-17"
})

# Trigger manual ingestion
result = await service.trigger_manual({
    "pipeline": "daily_ingestion",
    "force": True  # Bypass schedules
})
```

### Key Methods
| Method | Description |
|--------|-------------|
| `run_pipeline(steps)` | Execute pipeline steps sequentially |
| `run_step(step)` | Execute single pipeline step |
| `get_status(pipeline_name)` | Get pipeline status |
| `get_history(filters)` | Get pipeline execution history |
| `trigger_manual(options)` | Force manual pipeline execution |
| `get_progress(pipeline_name)` | Get current progress percentage |

---

## MarketDataProcessing (Data Cleaning Pipelines)

**File**: `app/services/data/market_data_processing.py`

### Purpose
Data cleaning and normalization pipelines for market data. Ensures data quality, consistency, and completeness across all asset classes and sources.

### Key Features
- OHLCV data validation and correction
- Missing data interpolation
- Duplicate detection and removal
- Data format normalization
- Outlier detection and handling
- Timezone standardization
- Data quality scoring
- Batch and real-time processing modes

### Data Validation Rules
```python
# Validation rules applied
validation_rules = {
    "ohlcv": {
        "high >= open AND high >= close": "High must be >= open and close",
        "low <= open AND low <= close": "Low must be <= open and close",
        "volume >= 0": "Volume cannot be negative",
        "high >= low": "High must be >= Low",
        "price_range_reasonable": "Price spikes > 50% flagged"
    },
    "timestamps": {
        "timezone_utc": "All timestamps must be UTC",
        "no_future_dates": "Cannot have future timestamps",
        "no_duplicates": "No duplicate timestamps per symbol"
    },
    "price_ranges": {
        "min_price": 0.01,  # Minimum valid price
        "max_price": 1e10,  # Maximum valid price
        "daily_change_limit": 0.5  # 50% max daily change
    }
}
```

### Data Normalization
```python
# Normalize data from different sources
normalized = await market_data_processing.normalize({
    "source": "yahoo",
    "data": raw_yahoo_data,
    "target_schema": "bedaanwaves"
})

# Result includes:
# - Unified timestamp format (UTC)
# - Standardized OHLCV structure
# - Consistent decimal precision
# - Source attribution metadata
# - Quality score
```

### Data Quality Scoring
```python
# Calculate quality score
score = await market_data_processing.quality_score({
    "data_points": 252,  # Number of data points
    "missing_values": 0,  # Count of missing
    "outliers": 3,  # Count of outliers
    "format_errors": 0  # Count of format errors
})

# Returns: score 0-100 (higher is better)
# Thresholds: 
#   90-100: Excellent
#   70-89: Good
#   50-69: Fair
#   0-49: Poor - requires review
```

### Processing Modes
- **Batch**: Full dataset processing (scheduled)
- **Streaming**: Real-time data validation
- **Incremental**: Update existing data only

### Usage
```python
from app.services.data.market_data_processing import MarketDataProcessing

processor = MarketDataProcessing()

# Validate price data
validation = await processor.validate_ohlcv({
    "data": price_candle_data,
    "symbol_id": symbol_uuid,
    "timeframe": "1d"
})

# Check quality
score = await processor.quality_score({
    "dataset": large_dataset,
    "checks": ["completeness", "accuracy", "consistency"]
})

# Normalize from source
normalized = await processor.normalize({
    "source": "yahoo",
    "data": raw_yahoo_data,
    "target": "bedaanwaves_normalized"
})

# Detect outliers
outliers = await processor.detect_outliers({
    "prices": price_series,
    "method": "z_score",  # or "iqr"
    "threshold": 3.0
})
```

### Key Methods
| Method | Description |
|--------|-------------|
| `validate_ohlcv(data, symbol_id, timeframe)` | Validate OHLCV data integrity |
| `quality_score(dataset, checks)` | Calculate data quality score |
| `normalize(data, source, target)` | Normalize to unified schema |
| `detect_outliers(prices, method, threshold)` | Detect statistical outliers |
| `interpolate_missing(data, method)` | Fill missing data points |
| `standardize_timestamps(data)` | Ensure UTC timezone |

---

## IntlApiClient (International Market APIs)

**File**: `app/services/data/intl_api_client.py`

### Purpose
Integration with international market APIs including NYSE, NASDAQ, and other global exchanges. Provides access to international stock data, indices, and financial instruments.

### Key Features
- NYSE/NASDAQ API integration
- International symbol lookup
- Cross-market comparison
- Currency conversion data
- Global indices tracking
- Multi-currency support

### API Integration
| Provider | Endpoints | Coverage |
|----------|-----------|----------|
| Yahoo Finance | Historical, quotes | Global stocks |
| Alpha Vantage | Technical, forex | International |
| Twelve Data | Real-time, historical | 50+ exchanges |
| IEX Cloud | Real-time, markets | US equities |

### Currency Support
```python
# Currency conversion
conversion = await intl_client.get_conversion({
    "from": "USD",
    "to": "IRR",
    "amount": 100,
    "date": "2024-08-17"
})

# Returns: {"converted_amount": 5200000000, "rate": 52000000.0}

# Supported currencies
currencies = await intl_client.get_supported_currencies()

# Returns: ["USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", ...]
```

### Cross-Market Symbol Lookup
```python
# Find international equivalent
equivalent = await intl_client.find_equivalent({
    "symbol": "AAPL",  # NASDAQ symbol
    "target_markets": ["NYSE", "NASDAQ", "LSE"]
})

# Returns: equivalent symbols or None
```

### Usage
```python
from app.services.data.intl_api_client import IntlApiClient

client = IntlApiClient(
    api_key="your-alpha-vantage-key",
    providers=["yahoo", "alpha_vantage", "twelve_data"]
)

# Get international symbol
symbol = await client.get_international_symbol({
    "ticker": "FSPD",
    "exchanges": ["NYSE", "NASDAQ"]
})

# Get historical data
history = await client.get_historical({
    "symbol": "AAPL",
    "start": "2024-01-01",
    "end": "2024-08-17",
    "interval": "1d",
    "provider": "yahoo"
})

# Get currency conversion
conv = await client.get_conversion({
    "from": "USD",
    "to": "EUR",
    "amount": 1000
})
```

### Key Methods
| Method | Description |
|--------|-------------|
| `get_international_symbol(ticker, exchanges)` | Find symbol across exchanges |
| `get_historical(symbol, start, end, interval, provider)` | Historical price data |
| `get_conversion(from, to, amount, date)` | Currency conversion |
| `get_supported_currencies()` | List supported currencies |
| `get_indices(provider)` | Global indices data |
| `compare_markets(symbol, target_markets)` | Cross-market comparison |

---

## DataValidationService (Data Integrity Validation)

**File**: `app/services/data/data_validation_service.py`

### Purpose
Validates data integrity across all databases and external sources. Ensures consistency, detects anomalies, and provides data quality reports.

### Key Features
- Cross-table consistency checks
- Referential integrity validation
- Data completeness assessment
- Anomaly detection
- Data drift detection
- Automated repair suggestions
- Scheduled validation runs

### Validation Types
```python
# Types of validation checks
validation_checks = [
    "referential_integrity",       # FK constraints satisfied
    "completeness",                # No missing required fields
    "uniqueness",                  # Unique constraints OK
    "range_checks",               # Values within expected ranges
    "format_validation",           # Correct data formats
    "cross_table_consistency",     # Related tables consistent
    "trend_consistency",           # Temporal consistency
    "anomaly_detection"            # Statistical anomaly detection
]
```

### Example Validation Report
```python
report = await data_validation_service.run_validation({
    "checks": ["referential_integrity", "completeness", "anomaly_detection"],
    "tables": ["price_candles", "ml_signals", "positions"]
})

# Returns structure:
{
    "validation_id": "val_20240817_001",
    "timestamp": "2024-08-17T10:00:00Z",
    "overall_score": 94.5,  # 0-100
    "checks": {
        "referential_integrity": {
            "status": "pass",
            "issues": 0,
            "details": "All FK constraints satisfied"
        },
        "completeness": {
            "status": "warn",
            "issues": 12,  # 12 rows with NULL required fields
            "details": "12 rows need attention"
        },
        "anomaly_detection": {
            "status": "pass",
            "anomalies": 0,
            "details": "No statistical anomalies detected"
        }
    },
    "recommendations": [
        "Consider cleaning 12 rows with NULL portfolio_id",
        "Review sudden price spike in FSPD on 2024-06-15"
    ]
}
```

### Data Drift Detection
```python
# Detect data drift between sources
drift = await data_validation_service.detect_drift({
    "table": "price_candles",
    "source_a": "yahoo_finance",
    "source_b": "yahoo_finance",
    "timeframe": "1d",
    "comparison_period": "30d"
})

# Returns drift statistics
{
    "drift_percentage": 2.3,  # % of records with differences
    "detailed_diffs": [
        {
            "asset_id": "...",
            "timestamp": "2024-06-15",
            "source_a_close": 150.20,
            "source_b_close": 149.80,
            "difference": 0.40
        }
    ]
}
```

### Usage
```python
from app.services.data.data_validation_service import DataValidationService

service = DataValidationService()

# Run comprehensive validation
report = await service.run_validation({
    "checks": ["all"],  # Run all check types
    "tables": ["assets", "price_candles", "users", "portfolios"]
})

# Check specific table
table_report = await service.validate_table("price_candles")

# Detect drift between periods
drift = await service.detect_drift({
    "table": "ml_signals",
    "period_from": "2024-07-01",
    "period_to": "2024-08-01",
    "new_period": "2024-08-01",
    "current_period": "2024-08-17"
})
```

### Key Methods
| Method | Description |
|--------|-------------|
| `run_validation(filters)` | Run comprehensive validation |
| `validate_table(table_name)` | Validate specific table |
| `detect_drift(filters)` | Detect data drift between periods |
| `check_referential_integrity(table)` | Check FK constraints |
| `check_completeness(table)` | Check required fields |
| `check_uniqueness(table)` | Check unique constraints |
| `generate_report(report_id)` | Generate validation report |

---

## FinancialDataIngestService (Multi-Source Financial Statement Ingestion)

**File**: `app/services/data/financial_data_ingest_service.py`

### Purpose
Ingests financial statements from multiple sources including SEC EDGAR (US), Yahoo Finance, and Alpha Vantage. Normalizes and stores financial metrics for fundamental analysis.

### Key Features
- Multi-source financial data ingestion
- SEC EDGAR (US financial disclosures) integration
- Yahoo Finance financial statements
- Alpha Vantage financial data
- Financial ratio calculation and storage
- Scheduled ingestion pipelines
- Data normalization to unified schema
- Source tracking and audit trail

### Source Integration
| Source | Data Type | Coverage |
|--------|-----------|----------|
| SEC EDGAR | US financial statements | NASDAQ-listed companies |
| Yahoo Finance | Income statement, balance sheet | Global stocks |
| Alpha Vantage | Financial ratios, key metrics | International |

### SEC EDGAR Integration (US)
```python
# Fetch from SEC EDGAR API
financial_data = await ingest_service.fetch_sec_edgar_data({
    "company_code": "0000320193",  # SEC CIK
    "report_type": "yearly",  # yearly, quarterly, semi_annual
    "year": 2024
})

# Example SEC EDGAR response structure
{
    "company_name": "Apple Inc.",
    "report_period": "2024-03-20",
    "financials": {
        "total_assets": 350000000000,  # USD
        "total_equity": 150000000000,
        "net_income": 97000000000,
        "total_liabilities": 200000000000,
        "revenue": 383000000000
    },
    "ratios": {
        "roe": 1.26,  # 126%
        "roa": 0.28,
        "current_ratio": 0.86,
        "debt_to_equity": 1.32
    }
}
```

### Yahoo Finance Integration
```python
# Fetch from Yahoo Finance
financial_data = await ingest_service.fetch_yahoo_finance({
    "symbol": "AAPL",
    "statements": ["income_statement", "balance_sheet", "cash_flow"],
    "period": "annual"
})

# Returns standardized financial statements
```

### Data Normalization
```python
# Normalize to unified schema
normalized = await ingest_service.normalize({
    "source": "sec_edgar",
    "data": raw_sec_edgar_data,
    "company_id": company_uuid,
    "financial_year": 2024
})

# Result structure:
# {
#   "company_id": "...",
#   "financial_year": 2024,
#   "total_assets": Decimal("125000000000000"),
#   "total_equity": Decimal("45000000000000"),
#   "net_income": Decimal("18000000000000"),
#   "revenue": Decimal("35000000000000"),
#   "ratios": {
#     "roe": Decimal("0.04"),
#     "current_ratio": Decimal("1.25"),
#     "debt_to_equity": Decimal("1.78")
#   },
#   "source": "SEC_EDGAR",
#   "ingested_at": "2024-08-17T10:00:00Z"
# }
```

### Financial Ratios Calculation
```python
# Calculate derived ratios
ratios = await ingest_service.calculate_ratios({
    "financial_data": normalized_data,
    "ratios_to_calculate": ["roe", "roa", "current_ratio", "debt_to_equity", "pe_ratio"]
})

# Automatic calculation from raw financials
# ROE = net_income / total_equity
# Current Ratio = current_assets / current_liabilities
# Debt-to-Equity = total_liabilities / total_equity
# P/E Ratio = market_price / earnings_per_share
```

### Scheduled Ingestion
```python
# Daily ingestion schedule
await ingest_service.schedule_daily({
    "sources": ["sec_edgar", "yahoo", "alpha_vantage"],
    "companies": ["all_nasdaq_listed"],  # or specific list
    "time": "02:00",  # 2 AM daily
    "force": False  # Skip if already ingested today
})
```

### Usage
```python
from app.services.data.financial_data_ingest_service import FinancialDataIngestService

service = FinancialDataIngestService()

# Ingest SEC EDGAR data for specific company
result = await service.ingest_sec_edgar({
    "company_code": "0000320193",
    "report_type": "yearly",
    "year": 2024
})

# Ingest Yahoo Finance data
result = await service.ingest_yahoo_finance({
    "symbol": "AAPL",
    "statements": ["income_statement", "balance_sheet"],
    "force": True  # Force re-ingestion
})

# Get latest financial data for company
data = await service.get_latest({
    "company_id": company_uuid,
    "statement_type": "balance_sheet"
})
```

### Key Methods
| Method | Description |
|--------|-------------|
| `ingest_sec_edgar(company_code, report_type, year)` | Ingest from SEC EDGAR |
| `ingest_yahoo_finance(symbol, statements, period)` | Ingest from Yahoo Finance |
| `ingest_alpha_vantage(symbol, function)` | Ingest from Alpha Vantage |
| `normalize(source, data, company_id)` | Normalize to unified schema |
| `calculate_ratios(financial_data, ratios)` | Calculate financial ratios |
| `get_latest(company_id, statement_type)` | Get latest financial data |
| `schedule_daily(options)` | Schedule daily ingestion |

---

## StockFundamentalDataIngestionService (Fundamental Data Pipeline)

**File**: `app.services.data.stock_fundamental_ingestion_service.py`

### Purpose
Stock fundamental data pipeline for US/International markets. Specialized pipeline for comprehensive fundamental analysis data across multiple market regions.

### Key Features
- Region-specific fundamental data pipelines
  - US market (NASDAQ) fundamental data
- International market fundamental data
- Multi-currency support
- Fundamental ratio standardization
- Comparative analysis across regions
- Scheduled pipeline execution

### Market Data Refresh Pipeline
```python
# US market fundamental data ingestion
result = await fundamental_service.ingest_us_fundamentals({
    "symbols": ["0123456789", "0987654321"],  # Company tickers
    "report_types": ["yearly", "quarterly"],
    "years": [2023, 2024],
    "force": False
})

# Returns processed fundamental data for companies
```

### US Market Pipeline
```python
# US market fundamental data
result = await fundamental_service.ingest_us_fundamentals({
    "symbols": ["AAPL", "MSFT", "GOOGL"],
    "sources": ["yahoo", "alpha_vantage"],
    "force": False
})
```

### International Pipeline
```python
# International market data
result = await fundamental_service.ingest_international_fundamentals({
    "symbols": ["SIE.DE", "ASML.AS"],  # European/Asian symbols
    "exchanges": ["XETRA", "EURONEXT"],
    "currencies": ["EUR", "USD"]
})
```

### Fundamental Ratio Standardization
```python
# Standardize ratios across regions
standardized = await fundamental_service.standardize_ratios({
    "data": raw_fundamental_data,
    "region": "us",  # "us", "international"
    "target_standards": ["us Gaap", "ifrs"]
})

# Ensures consistent ratio calculation:
# - All values in consistent currency (USD where applicable)
# - Standardized calculation methods
# - Comparable across regions
```

### Cross-Region Comparative Analysis
```python
# Compare companies across regions
comparison = await fundamental_service.compare_across_regions({
    "us_companies": ["jpmorgan", "bank_of_america"],
    "international_companies": ["sie.de", "asml.as"]
    "metrics": ["roe", "roa", "current_ratio", "growth_rate"],
    "currency_conversion": True
})

# Returns comparable metrics across regions
```

### Usage
```python
from app.services.data.stock_fundamental_ingestion_service import StockFundamentalDataIngestionService

service = StockFundamentalDataIngestionService()

# Ingest US fundamentals
result = await service.ingest_us_fundamentals({
    "symbols": ["AAPL", "MSFT"],
    "sources": ["yahoo"],
    "force": True
})

# Get fundamental data for analysis
data = await service.get_fundamental_data({
    "company_id": company_uuid,
    "metric": "roe",
    "region": "us",
    "year": 2024
})

# Cross-region comparison
comparison = await service.compare_across_regions({
    "us_companies": ["jpmorgan", "bank_of_america"],
    "metrics": ["roe", "current_ratio"]
})
```

### Key Methods
| Method | Description |
|--------|-------------|
  | `ingest_us_fundamentals(symbols, sources, force)` | Ingest US market fundamentals |
| `ingest_international_fundamentals(symbols, exchanges, currencies)` | Ingest international fundamentals |
| `standardize_ratios(data, region, target_standards)` | Standardize financial ratios |
  | `compare_across_regions(us_companies, international_companies, metrics)` | Cross-region comparison |
| `get_fundamental_data(company_id, metric, region, year)` | Get fundamental data |

---
*Last Updated: 2026-08-17*
*Status: Tier 2 Data Services - 6/13 Complete (46% Implemented)*