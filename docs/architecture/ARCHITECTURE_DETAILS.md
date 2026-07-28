# Architecture Details: Technical Specifications

---

## Table of Contents

1. [Unified Database Schema](#unified-database-schema)
2. [API Specification](#api-specification)
3. [Backend Services](#backend-services)
4. [Frontend Architecture](#frontend-architecture)
5. [Integration Patterns](#integration-patterns)
6. [Deployment & DevOps](#deployment--devops)

---

## Unified Database Schema

### Schema Design Principles

1. **Normalization**: Reduce data redundancy while maintaining queryability
2. **Partitioning**: Time-based partitioning for time-series data (price candles)
3. **Denormalization**: Strategic denormalization for frequently accessed aggregates
4. **Versioning**: Schema versioning with migration tracking
5. **Audit Trail**: Track all data changes for compliance

### Core Tables

#### 1. Assets Table
```sql
CREATE TABLE assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    
    -- Classification
    asset_class VARCHAR(20) NOT NULL CHECK (asset_class IN (
        'EQUITY', 'ETF', 'CRYPTO', 'COMMODITY', 'BOND', 'INDEX'
    )),
    market VARCHAR(20) NOT NULL CHECK (market IN (
        'TSE', 'OTC', 'BINANCE', 'KRAKEN', 'NYSE', 'NASDAQ'
    )),
    
    -- Hierarchy
    sector VARCHAR(100),
    sub_sector VARCHAR(100),
    industry VARCHAR(100),
    
    -- Geographic
    country_code CHAR(2),
    currency VARCHAR(3) NOT NULL DEFAULT 'IRR',
    
    -- Metadata
    isin_code VARCHAR(12),
    cusip_code VARCHAR(9),
    ticker_alternative VARCHAR(50),
    
    -- Status
    active BOOLEAN DEFAULT TRUE,
    listing_date DATE,
    delisting_date DATE,
    
    -- Tracking
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_classification CHECK (
        (asset_class = 'EQUITY' AND market IN ('TSE', 'OTC')) OR
        (asset_class = 'CRYPTO' AND market IN ('BINANCE', 'KRAKEN')) OR
        (asset_class = 'ETF' AND market IN ('TSE', 'NYSE')) OR
        true
    )
);

CREATE INDEX idx_assets_symbol ON assets(symbol);
CREATE INDEX idx_assets_market ON assets(market, asset_class);
CREATE INDEX idx_assets_active ON assets(active) WHERE active = TRUE;
CREATE INDEX idx_assets_sector ON assets(sector) WHERE sector IS NOT NULL;
```

#### 2. Price Candles Table (Partitioned)
```sql
CREATE TABLE price_candles (
    id UUID DEFAULT gen_random_uuid(),
    asset_id UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    timestamp TIMESTAMP NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    
    -- OHLC data
    open DECIMAL(20, 8) NOT NULL,
    high DECIMAL(20, 8) NOT NULL,
    low DECIMAL(20, 8) NOT NULL,
    close DECIMAL(20, 8) NOT NULL,
    
    -- Volume metrics
    volume BIGINT NOT NULL,
    turnover DECIMAL(25, 2),
    transactions INTEGER,
    
    -- Adjusted prices
    adjusted_close DECIMAL(20, 8),
    split_ratio DECIMAL(10, 4) DEFAULT 1.0,
    
    -- Quality indicators
    source VARCHAR(20) NOT NULL,
    data_quality VARCHAR(10) CHECK (data_quality IN ('CONFIRMED', 'PROVISIONAL', 'ESTIMATED')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (id, timestamp),
    UNIQUE (asset_id, timestamp, timeframe),
    CONSTRAINT valid_timeframe CHECK (
        timeframe IN ('1m', '5m', '15m', '1h', '4h', '1d', '1w', '1M')
    ),
    CONSTRAINT valid_ohlc CHECK (
        open > 0 AND high > 0 AND low > 0 AND close > 0 AND
        high >= open AND high >= close AND low <= open AND low <= close
    )
) PARTITION BY RANGE (timestamp);

-- Create partitions for recent and rolling window
CREATE TABLE price_candles_2026_h1 PARTITION OF price_candles
    FOR VALUES FROM ('2026-01-01') TO ('2026-07-01');

CREATE TABLE price_candles_2026_h2 PARTITION OF price_candles
    FOR VALUES FROM ('2026-07-01') TO ('2027-01-01');

CREATE INDEX idx_price_asset_timestamp ON price_candles(asset_id, timestamp DESC);
CREATE INDEX idx_price_timeframe ON price_candles(timeframe, timestamp DESC);
```

#### 3. ML Signals Table
```sql
CREATE TABLE ml_signals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID NOT NULL REFERENCES assets(id),
    
    -- Signal details
    signal_type VARCHAR(10) NOT NULL CHECK (
        signal_type IN ('BUY', 'SELL', 'HOLD', 'STRONG_BUY', 'STRONG_SELL')
    ),
    confidence DECIMAL(5, 2) NOT NULL CHECK (confidence >= 0 AND confidence <= 100),
    
    -- Expected performance
    expected_return DECIMAL(8, 2),
    expected_volatility DECIMAL(8, 2),
    risk_score DECIMAL(5, 2) CHECK (risk_score >= 0 AND risk_score <= 100),
    risk_rating VARCHAR(10) CHECK (
        risk_rating IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')
    ),
    
    -- Supporting data
    reasoning TEXT,
    technical_factors JSONB DEFAULT '{}',
    fundamental_factors JSONB DEFAULT '{}',
    sentiment_factors JSONB DEFAULT '{}',
    
    -- Model information
    ml_model_version VARCHAR(50) NOT NULL,
    model_name VARCHAR(100),
    model_confidence DECIMAL(5, 2),
    
    -- Validity
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    valid_from TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    valid_until TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Performance tracking
    actual_return DECIMAL(8, 2),
    win_rate DECIMAL(5, 2),
    
    CONSTRAINT signal_validity CHECK (valid_until > valid_from)
);

CREATE INDEX idx_signal_asset ON ml_signals(asset_id);
CREATE INDEX idx_signal_active ON ml_signals(is_active, generated_at DESC);
CREATE INDEX idx_signal_model ON ml_signals(ml_model_version, generated_at DESC);
```

#### 4. User Portfolio Tables
```sql
CREATE TABLE portfolios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    
    -- Portfolio details
    name VARCHAR(255) NOT NULL,
    description TEXT,
    portfolio_type VARCHAR(20) CHECK (
        portfolio_type IN ('PERSONAL', 'WATCHLIST', 'PAPER_TRADING', 'ALGO')
    ),
    
    -- Settings
    base_currency VARCHAR(3) DEFAULT 'IRR',
    rebalance_frequency VARCHAR(20),
    target_allocation JSONB DEFAULT '{}',
    
    -- Visibility
    is_public BOOLEAN DEFAULT FALSE,
    public_token VARCHAR(50),
    
    -- Tracking
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(user_id, name)
);

CREATE TABLE positions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    asset_id UUID NOT NULL REFERENCES assets(id),
    
    -- Position details
    quantity DECIMAL(20, 8) NOT NULL,
    entry_price DECIMAL(20, 8) NOT NULL,
    entry_date DATE NOT NULL,
    
    -- Current status
    current_price DECIMAL(20, 8),
    current_value DECIMAL(25, 2),
    unrealized_pnl DECIMAL(25, 2),
    unrealized_pnl_pct DECIMAL(8, 2),
    
    -- Exit strategy
    stop_loss DECIMAL(20, 8),
    take_profit DECIMAL(20, 8),
    
    -- Notes
    notes TEXT,
    tags JSONB DEFAULT '[]',
    
    -- Tracking
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(portfolio_id, asset_id),
    CONSTRAINT positive_quantity CHECK (quantity > 0)
);

CREATE INDEX idx_position_portfolio ON positions(portfolio_id);
CREATE INDEX idx_position_current_value ON positions(portfolio_id, current_value DESC);
```

#### 5. User Alerts Table
```sql
CREATE TABLE user_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    asset_id UUID REFERENCES assets(id),
    
    -- Alert configuration
    alert_type VARCHAR(20) NOT NULL CHECK (
        alert_type IN (
            'PRICE_THRESHOLD', 'PRICE_CHANGE', 'SIGNAL_CHANGE',
            'NEWS', 'VOLUME_SPIKE', 'INDICATOR', 'PORTFOLIO_CHANGE'
        )
    ),
    
    -- Condition specification
    condition JSONB NOT NULL,
    threshold_value DECIMAL(20, 8),
    threshold_direction VARCHAR(10) CHECK (
        threshold_direction IN ('ABOVE', 'BELOW', 'BETWEEN', 'CHANGE')
    ),
    
    -- Notification
    notification_channel VARCHAR(20) CHECK (
        notification_channel IN ('EMAIL', 'SMS', 'PUSH', 'WEBHOOK')
    ),
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    triggered_at TIMESTAMP,
    triggered_count INTEGER DEFAULT 0
);

CREATE INDEX idx_alert_user ON user_alerts(user_id, is_active);
CREATE INDEX idx_alert_asset ON user_alerts(asset_id) WHERE is_active = TRUE;
```

### Schema Evolution & Migrations

```python
# backend/database/migrations/migration_001_unified_schema.py
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    # Step 1: Create new unified tables
    op.create_table('assets', ...)
    op.create_table('price_candles', ...)
    op.create_table('ml_signals', ...)
    
    # Step 2: Migrate data from old tables
    op.execute("""
        INSERT INTO assets (symbol, name, asset_class, market, active, created_at, updated_at)
        SELECT ticker, name, 'EQUITY', 'TSE', true, created_at, updated_at
        FROM bedaan4d_ml.stocks
        WHERE active = true
    """)
    
    # Step 3: Create compatibility views
    op.execute("""
        CREATE VIEW bedaan4d_ml.stocks AS
        SELECT symbol as ticker, name, market, sector, active, created_at, updated_at
        FROM assets
        WHERE asset_class = 'EQUITY' AND market = 'TSE'
    """)
    
    # Step 4: Add indexes and constraints
    op.create_index('idx_assets_symbol', 'assets', ['symbol'])
    ...

def downgrade():
    # Reverse migration with proper cleanup
    op.drop_index('idx_assets_symbol')
    op.drop_table('assets')
    ...
```

---

## API Specification

### RESTful API Design

#### Base URL
```
http://api.bedaan.local/v1
```

#### Authentication
```
Authorization: Bearer {JWT_TOKEN}
Content-Type: application/json
```

### Market Data Endpoints

#### GET /market/symbols
Retrieve available trading symbols with metadata.

**Parameters:**
```json
{
  "asset_class": "EQUITY|CRYPTO|ETF",
  "market": "TSE|OTC|BINANCE",
  "sector": "string (optional)",
  "limit": 100,
  "offset": 0,
  "active_only": true
}
```

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "id": "uuid",
      "symbol": "FSPD",
      "name": "فولاد",
      "asset_class": "EQUITY",
      "market": "TSE",
      "sector": "Metals & Mining",
      "country_code": "IR",
      "currency": "IRR",
      "active": true,
      "listing_date": "1990-01-01"
    }
  ],
  "pagination": {
    "total": 500,
    "limit": 100,
    "offset": 0
  }
}
```

**Status Codes:**
- 200 OK
- 400 Bad Request (invalid parameters)
- 401 Unauthorized
- 429 Too Many Requests (rate limited)

#### GET /market/price-history
Retrieve historical OHLCV data.

**Parameters:**
```json
{
  "symbol": "FSPD" (required),
  "timeframe": "1m|5m|15m|1h|1d|1w" (default: 1d),
  "start_date": "2024-01-01" (ISO8601, optional),
  "end_date": "2024-12-31" (ISO8601, optional),
  "limit": 500
}
```

**Response:**
```json
{
  "status": "success",
  "symbol": "FSPD",
  "timeframe": "1d",
  "data": [
    {
      "timestamp": "2024-01-01T00:00:00Z",
      "open": 65000.0,
      "high": 66000.0,
      "low": 64500.0,
      "close": 65500.0,
      "volume": 1000000,
      "turnover": 65500000000.0,
      "transactions": 1250
    }
  ]
}
```

#### GET /market/latest-prices
Get latest prices for multiple symbols (real-time or near real-time).

**Parameters:**
```json
{
  "symbols": ["FSPD", "MAPNA", "SHTEL"],
  "include_change": true
}
```

**Response:**
```json
{
  "status": "success",
  "timestamp": "2026-07-09T12:30:00Z",
  "data": {
    "FSPD": {
      "price": 65500.0,
      "change": 500.0,
      "change_pct": 0.77,
      "volume": 1000000,
      "volume_change_pct": 5.2
    },
    "MAPNA": {
      "price": 42000.0,
      "change": -200.0,
      "change_pct": -0.47,
      "volume": 500000,
      "volume_change_pct": -10.5
    }
  }
}
```

### Analysis Endpoints

#### GET /analysis/signals/{symbol}
Retrieve ML-generated trading signals.

**Response:**
```json
{
  "status": "success",
  "symbol": "FSPD",
  "signal": {
    "type": "BUY",
    "confidence": 87.5,
    "expected_return": 5.2,
    "risk_score": 45,
    "reasoning": "Technical breakout with bullish divergence",
    "technical_factors": {
      "rsi": 65,
      "macd_signal": "bullish_crossover",
      "trend": "uptrend"
    },
    "fundamental_factors": {
      "pe_ratio": 12.5,
      "eps_growth": 8.5,
      "dividend_yield": 3.2
    },
    "generated_at": "2026-07-09T12:00:00Z",
    "valid_until": "2026-07-10T12:00:00Z"
  }
}
```

#### POST /analysis/backtest
Run backtesting on a trading strategy.

**Request:**
```json
{
  "strategy": {
    "name": "Moving Average Crossover",
    "description": "Buy when SMA20 > SMA50",
    "rules": [
      {
        "type": "entry",
        "condition": "sma_20 > sma_50",
        "signal": "BUY"
      }
    ]
  },
  "symbols": ["FSPD", "MAPNA"],
  "start_date": "2023-01-01",
  "end_date": "2024-12-31",
  "initial_capital": 1000000000
}
```

**Response:**
```json
{
  "status": "success",
  "results": {
    "total_return": 18.5,
    "annual_return": 10.2,
    "sharpe_ratio": 1.45,
    "max_drawdown": -15.3,
    "win_rate": 65.5,
    "profit_factor": 2.1,
    "trades": 45,
    "winning_trades": 29,
    "losing_trades": 16
  }
}
```

### Portfolio Endpoints

#### POST /portfolio/create
Create a new portfolio.

**Request:**
```json
{
  "name": "My Growth Portfolio",
  "description": "Growth-focused tech stocks",
  "portfolio_type": "PERSONAL",
  "base_currency": "IRR",
  "is_public": false
}
```

**Response:**
```json
{
  "status": "success",
  "portfolio": {
    "id": "uuid",
    "name": "My Growth Portfolio",
    "created_at": "2026-07-09T12:00:00Z",
    "public_token": "..."
  }
}
```

#### POST /portfolio/{portfolio_id}/positions
Add position to portfolio.

**Request:**
```json
{
  "symbol": "FSPD",
  "quantity": 100,
  "entry_price": 65500.0,
  "entry_date": "2026-07-09",
  "stop_loss": 60000.0,
  "take_profit": 75000.0
}
```

#### GET /portfolio/{portfolio_id}/analysis
Get portfolio analytics.

**Response:**
```json
{
  "status": "success",
  "portfolio": {
    "total_value": 10000000,
    "total_cost": 9500000,
    "total_return": 500000,
    "total_return_pct": 5.26,
    "allocation": {
      "by_sector": {...},
      "by_market": {...},
      "by_risk": {...}
    },
    "metrics": {
      "sharpe_ratio": 1.2,
      "beta": 0.95,
      "correlation_with_market": 0.87
    }
  }
}
```

### User & Authentication Endpoints

#### POST /auth/register
Register new user.

#### POST /auth/login
User login.

#### POST /auth/refresh
Refresh JWT token.

#### GET /user/profile
Get user profile.

#### GET /user/alerts
Get user's configured alerts.

#### POST /user/alerts
Create new alert.

---

## Backend Services

### Service Decomposition

#### 1. Market Data Service

**Responsibilities:**
- Fetch data from external APIs (BRS, Binance, etc.)
- Normalize and validate data
- Store in PostgreSQL
- Provide data query API

**Technology:** Python + FastAPI

**Key Components:**
```python
# backend/services/market_data/provider.py
from abc import ABC, abstractmethod

class DataProvider(ABC):
    @abstractmethod
    async def get_symbols(self) -> List[Symbol]:
        pass
    
    @abstractmethod
    async def get_price_history(
        self,
        symbol: str,
        timeframe: str,
        start_date: Date,
        end_date: Date
    ) -> List[Candle]:
        pass

class BRSProvider(DataProvider):
    def __init__(self, api_key: str):
        self.client = BRSAPIClient(api_key)
    
    async def get_symbols(self) -> List[Symbol]:
        # Fetch from BRS API and normalize
        pass
    
    async def get_price_history(...) -> List[Candle]:
        # Fetch OHLCV and normalize
        pass

class CryptoProvider(DataProvider):
    def __init__(self):
        self.exchanges = {
            'BINANCE': BinanceClient(),
            'KRAKEN': KrakenClient()
        }
    
    async def get_symbols(self) -> List[Symbol]:
        # Aggregate from multiple exchanges
        pass

class DataAggregator:
    def __init__(self, providers: List[DataProvider]):
        self.providers = providers
    
    async def aggregate_symbols(self) -> List[Symbol]:
        all_symbols = []
        for provider in self.providers:
            symbols = await provider.get_symbols()
            all_symbols.extend(symbols)
        return deduplicate(all_symbols)
```

#### 2. Analysis Service

**Responsibilities:**
- Generate ML-based trading signals
- Perform technical analysis
- Compute fundamental metrics
- Sentiment analysis

**Technology:** Python + scikit-learn/TensorFlow

**Key Components:**
```python
# backend/services/analysis/signal_generator.py
class AnalysisEngine:
    def __init__(self, model_path: str):
        self.technical_analyzer = TechnicalAnalyzer()
        self.fundamental_analyzer = FundamentalAnalyzer()
        self.ml_model = load_model(model_path)
        self.sentiment_analyzer = SentimentAnalyzer()
    
    async def generate_signal(self, symbol: str) -> MLSignal:
        # Gather input data
        price_data = await self.get_price_history(symbol)
        fundamental_data = await self.get_fundamental_data(symbol)
        sentiment = await self.sentiment_analyzer.analyze(symbol)
        
        # Run analysis
        technical_factors = self.technical_analyzer.analyze(price_data)
        fundamental_factors = self.fundamental_analyzer.analyze(fundamental_data)
        
        # Feed to ML model
        features = self.prepare_features(
            technical_factors,
            fundamental_factors,
            sentiment
        )
        
        prediction = self.ml_model.predict(features)
        confidence = self.ml_model.predict_proba(features).max()
        
        return MLSignal(
            symbol=symbol,
            signal=prediction,
            confidence=confidence,
            technical_factors=technical_factors,
            fundamental_factors=fundamental_factors
        )
```

#### 3. Portfolio Service

**Responsibilities:**
- CRUD operations on portfolios
- Position management
- Performance calculations
- Rebalancing recommendations

**Technology:** Python/Node.js + FastAPI/Express

```python
# backend/services/portfolio/portfolio_manager.py
class PortfolioManager:
    async def create_portfolio(self, user_id: str, data: dict) -> Portfolio:
        portfolio = Portfolio(user_id=user_id, **data)
        await db.add(portfolio)
        return portfolio
    
    async def add_position(
        self,
        portfolio_id: str,
        asset_id: str,
        quantity: float,
        entry_price: float
    ) -> Position:
        position = Position(
            portfolio_id=portfolio_id,
            asset_id=asset_id,
            quantity=quantity,
            entry_price=entry_price,
            entry_date=datetime.now().date()
        )
        await db.add(position)
        return position
    
    async def calculate_portfolio_metrics(self, portfolio_id: str) -> dict:
        positions = await self.get_positions(portfolio_id)
        
        metrics = {
            'total_value': sum(p.current_value for p in positions),
            'total_cost': sum(p.quantity * p.entry_price for p in positions),
            'allocation': self.calculate_allocation(positions),
            'risk_metrics': self.calculate_risk(positions)
        }
        
        return metrics
```

---

## Frontend Architecture

### Component Library Structure

```
src/components/
├── ui/                           # Primitives from shadcn/ui
│   ├── button.tsx
│   ├── card.tsx
│   ├── dialog.tsx
│   └── ...
├── market/                       # Market data components
│   ├── SymbolSearchBar.tsx
│   ├── PriceChart.tsx
│   ├── OrderBook.tsx
│   └── MarketHeatmap.tsx
├── analysis/                     # Analysis components
│   ├── SignalCard.tsx
│   ├── TechnicalAnalysisPanel.tsx
│   ├── BacktestResults.tsx
│   └── ModelMetrics.tsx
├── portfolio/                    # Portfolio components
│   ├── PortfolioSummary.tsx
│   ├── AllocationChart.tsx
│   ├── PositionList.tsx
│   └── RiskDashboard.tsx
├── layout/                       # Layout components
│   ├── Header.tsx
│   ├── Sidebar.tsx
│   ├── MainLayout.tsx
│   └── DashboardLayout.tsx
└── common/                       # Shared utilities
    ├── Loading.tsx
    ├── ErrorBoundary.tsx
    └── NotFound.tsx
```

### State Management Pattern

```typescript
// src/stores/index.ts
import { create } from 'zustand';
import { persist, subscribeWithSelector } from 'zustand/middleware';

// Market Store
export const useMarketStore = create<MarketState>()(
  subscribeWithSelector(
    persist(
      (set, get) => ({
        symbols: [],
        selectedSymbol: null,
        priceHistory: [],
        
        setSymbols: (symbols) => set({ symbols }),
        selectSymbol: (symbol) => set({ selectedSymbol: symbol }),
        setPriceHistory: (data) => set({ priceHistory: data }),
      }),
      { name: 'market-storage' }
    )
  )
);

// Portfolio Store
export const usePortfolioStore = create<PortfolioState>()(
  persist(
    (set) => ({
      portfolios: [],
      selectedPortfolio: null,
      
      addPortfolio: (portfolio) =>
        set((state) => ({
          portfolios: [...state.portfolios, portfolio],
        })),
      
      selectPortfolio: (id) =>
        set((state) => ({
          selectedPortfolio: state.portfolios.find((p) => p.id === id) || null,
        })),
    }),
    { name: 'portfolio-storage' }
  )
);

// UI Store (non-persistent)
export const useUIStore = create<UIState>((set) => ({
  isDarkMode: false,
  isSidebarOpen: true,
  notifications: [],
  
  toggleDarkMode: () => set((state) => ({ isDarkMode: !state.isDarkMode })),
  toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),
}));
```

### Server Components vs Client Components

```typescript
// app/dashboard/page.tsx (Server Component)
import { MarketDataServer } from '@/components/market/MarketDataServer';

export default async function DashboardPage() {
  // Fetch data on server
  const symbols = await fetchSymbols();
  
  return (
    <div>
      <MarketDataServer symbols={symbols} />
    </div>
  );
}

// components/market/MarketDataServer.tsx
async function MarketDataServer({ symbols }: Props) {
  return (
    <div>
      {/* Server-side rendered content */}
      <MarketDataClient symbols={symbols} />
    </div>
  );
}

// components/market/MarketDataClient.tsx ('use client')
'use client';

import { useMarketStore } from '@/stores';
import { PriceChart } from './PriceChart';

export function MarketDataClient({ symbols }: Props) {
  const { selectedSymbol } = useMarketStore();
  
  return (
    <div>
      <PriceChart symbol={selectedSymbol} />
    </div>
  );
}
```

---

## Integration Patterns

### API Communication Pattern

```typescript
// src/services/api/client.ts
export class APIClient {
  private baseURL: string;
  private token: string | null = null;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }

  setToken(token: string) {
    this.token = token;
  }

  private async request<T>(
    method: string,
    path: string,
    options?: RequestOptions
  ): Promise<T> {
    const url = `${this.baseURL}${path}`;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const response = await fetch(url, {
      method,
      headers,
      body: options?.body ? JSON.stringify(options.body) : undefined,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new APIError(error.message, response.status);
    }

    return response.json();
  }

  async get<T>(path: string): Promise<T> {
    return this.request<T>('GET', path);
  }

  async post<T>(path: string, body: any): Promise<T> {
    return this.request<T>('POST', path, { body });
  }

  async put<T>(path: string, body: any): Promise<T> {
    return this.request<T>('PUT', path, { body });
  }

  async delete<T>(path: string): Promise<T> {
    return this.request<T>('DELETE', path);
  }
}
```

### Data Synchronization Pattern

```typescript
// src/hooks/useDataSync.ts
export function useDataSync(
  queryKey: string[],
  fetchFn: () => Promise<any>,
  options?: UseSyncOptions
) {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey,
    queryFn: fetchFn,
    staleTime: options?.staleTime || 5 * 60 * 1000,
    gcTime: options?.gcTime || 10 * 60 * 1000,
    retry: options?.retry !== false,
  });

  // Subscribe to WebSocket updates
  useEffect(() => {
    const unsubscribe = useWebSocketStore.subscribe(
      (updates) => {
        if (updates.affectsKey(queryKey)) {
          refetch();
        }
      }
    );

    return unsubscribe;
  }, [queryKey, refetch]);

  return { data, isLoading, error };
}
```

### Error Handling Strategy

```typescript
// src/lib/error-handler.ts
export class AppError extends Error {
  constructor(
    public code: string,
    public statusCode: number,
    message: string,
    public context?: Record<string, any>
  ) {
    super(message);
  }
}

export function handleAPIError(error: unknown): never {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data;
    throw new AppError(
      data?.code || 'UNKNOWN_ERROR',
      error.response?.status || 500,
      data?.message || 'An unexpected error occurred',
      { url: error.config?.url }
    );
  }

  if (error instanceof AppError) {
    throw error;
  }

  throw new AppError('UNKNOWN_ERROR', 500, String(error));
}

// Usage in components
'use client';
export function MyComponent() {
  const { data, error } = useQuery({
    queryFn: async () => {
      try {
        return await apiClient.get('/data');
      } catch (err) {
        handleAPIError(err);
      }
    },
  });

  if (error) {
    return <ErrorBoundary error={error} />;
  }

  return <div>{data}</div>;
}
```

---

## Deployment & DevOps

### Docker Containerization

```dockerfile
# Dockerfile for API Service
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 3000
ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "3000"]
```

```dockerfile
# Dockerfile for Frontend
FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

EXPOSE 3005

CMD ["npm", "start"]
```

### Kubernetes Deployment

```yaml
# k8s/api-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: bedaan-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: bedaan-api
  template:
    metadata:
      labels:
        app: bedaan-api
    spec:
      containers:
      - name: api
        image: bedaan/api:latest
        ports:
        - containerPort: 3000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
        - name: BRS_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-secret
              key: brs-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 30
          periodSeconds: 10
```

### CI/CD Pipeline

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: postgres

    steps:
    - uses: actions/checkout@v3
    
    - name: Run tests
      run: npm test
    
    - name: Run linter
      run: npm run lint
    
    - name: Build
      run: npm run build

  deploy:
    needs: test
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Build and push Docker image
      run: |
        docker build -t bedaan/api:latest .
        docker push bedaan/api:latest
    
    - name: Deploy to Kubernetes
      run: |
        kubectl apply -f k8s/
        kubectl rollout status deployment/bedaan-api
```

---

## Monitoring & Observability

### Metrics Collection

```python
# backend/monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# API metrics
api_requests = Counter(
    'bedaan_api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status']
)

api_duration = Histogram(
    'bedaan_api_request_duration_seconds',
    'API request duration',
    ['method', 'endpoint']
)

# Database metrics
db_query_duration = Histogram(
    'bedaan_db_query_duration_seconds',
    'Database query duration',
    ['query_type']
)

# ML metrics
signal_generation_time = Histogram(
    'bedaan_signal_generation_duration_seconds',
    'Time to generate signals',
    ['model_version']
)

model_accuracy = Gauge(
    'bedaan_model_accuracy',
    'Model accuracy score',
    ['model_version']
)
```

### Logging Strategy

```python
# backend/logging/logger.py
import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'context': getattr(record, 'context', {}),
        }
        
        if record.exc_info:
            log_obj['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_obj)

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)

# Usage
logger.info('Market data updated', extra={
    'context': {
        'symbol': 'FSPD',
        'records_processed': 1000,
        'duration_ms': 234
    }
})
```

This technical specification document provides implementation guidance for all three components of your integration framework. It should be used in conjunction with the main INTEGRATION_FRAMEWORK.md for a complete understanding of the ecosystem design.
