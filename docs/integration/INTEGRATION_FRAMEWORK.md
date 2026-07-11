# Comprehensive Software Ecosystem Integration Framework

**Project Portfolio Analysis**: Bedaan4D-ML, Bedaan6D-project, Bedaan_4D_AI, CryptoAndStocks

**Document Version**: 1.0  
**Last Updated**: July 2026  
**Status**: Strategic Planning Phase

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Phase 1: Documentation Strategy](#phase-1-documentation-strategy)
3. [Phase 2: Strategic Planning & Roadmap](#phase-2-strategic-planning--roadmap)
4. [Phase 3: Technical Architecture Design](#phase-3-technical-architecture-design)
5. [Implementation Timeline](#implementation-timeline)
6. [Risk Management](#risk-management)

---

## Executive Summary

Your portfolio comprises four complementary projects focused on financial market analysis and AI-driven insights:

| Project | Tech Stack | Primary Purpose | Current Status |
|---------|-----------|-----------------|-----------------|
| **Bedaan4D-ML** | Python, PostgreSQL/SQLite, BRS API | Market data acquisition, ML analysis | Backend core system |
| **Bedaan6D-project** | Next.js, TypeScript, Prisma, PostgreSQL | UI/Dashboard, Real-time analytics | Frontend framework |
| **Bedaan_4D_AI** | AI/ML data processing | Data enrichment, 4D/6D analysis | Data transformation |
| **CryptoAndStocks** | Financial intelligence | Multi-asset analysis | Nascent module |

**Integration Vision**: Create a unified platform that seamlessly combines real-time market data acquisition, advanced ML analysis, multi-asset support (stocks, crypto, ETFs), and an intuitive analytics dashboard with AI-powered insights.

---

# Phase 1: Documentation Strategy

## 1.1 Documentation Objectives

Establish a single source of truth for:
- System architecture and design decisions
- Module responsibilities and dependencies
- Data flow and integration points
- API contracts and service boundaries
- Deployment and operations procedures

## 1.2 Documentation Structure

### 1.2.1 Architecture Documentation

Create a comprehensive `docs/ARCHITECTURE.md` covering:

```
ARCHITECTURE.md
├── System Overview
│   ├── Component diagram (Mermaid)
│   ├── High-level data flow
│   └── Integration points
├── Core Components
│   ├── Data Acquisition Layer (Bedaan4D-ML)
│   ├── Analysis Layer (Bedaan_4D_AI)
│   ├── Presentation Layer (Bedaan6D-project)
│   └── Extensions (CryptoAndStocks)
├── Data Models
│   ├── Unified schema definition
│   ├── Cross-service relationships
│   └── Migration strategy
└── Communication Protocols
    ├── API specifications
    ├── Event schemas
    └── Message contracts
```

**Content Template:**

```markdown
## [Component Name]

### Purpose
Single paragraph describing the component's role

### Responsibilities
- Responsibility 1
- Responsibility 2
- Dependency: [upstream component]
- Dependents: [downstream components]

### Technology Stack
- Language/Framework: [version]
- Database: [type and version]
- Key Libraries: [list with purposes]

### Key Interfaces
- REST Endpoints: [list with methods]
- Event Topics: [list with payloads]
- Database Tables: [list with primary keys]

### Integration Points
- Receives data from: [component]
- Provides data to: [component]
- Shared resources: [databases/caches/queues]

### Deployment
- Container/Process: [details]
- Environment: [details]
- Dependencies: [list]
```

### 1.2.2 Data Flow Documentation

Create `docs/DATA_FLOW.md` with:

```
Market Data Flow Diagram:

BRS API → Data Acquisition (Bedaan4D-ML)
    ↓
Data Validation & Storage (PostgreSQL)
    ↓
ML Processing (Bedaan_4D_AI)
    ↓
Enriched Data & Signals
    ↓
API & Real-time Events
    ↓
Frontend Consumption (Bedaan6D-project)
    ↓
User Dashboard & Analytics
```

Document each stage:
- **Input Format**: Source data structure
- **Processing**: Transformations applied
- **Output Format**: Resulting data structure
- **Error Handling**: Fallback strategies
- **SLA**: Latency and availability requirements

### 1.2.3 API Documentation

Create `docs/APIs.md` with OpenAPI specifications:

```yaml
# Backend API Specification
/api/v1/market/symbols:
  GET:
    description: List available symbols with metadata
    parameters:
      - type: string (stock|crypto|etf)
      - limit: integer
    response:
      - symbol: string
      - name: string
      - market: string
      - active: boolean

/api/v1/market/price-history:
  GET:
    description: Historical OHLCV data
    parameters:
      - symbol: string (required)
      - start_date: ISO8601
      - end_date: ISO8601
      - interval: 1m|5m|15m|1h|1d
    response:
      - timestamp: ISO8601
      - open: number
      - high: number
      - low: number
      - close: number
      - volume: integer

/api/v1/analysis/signals:
  GET:
    description: ML-generated trading signals
    parameters:
      - symbol: string
      - signal_type: buy|sell|hold
    response:
      - signal: enum
      - confidence: 0-100
      - reasoning: string
      - updated_at: ISO8601
```

### 1.2.4 Dependency Map

Create `docs/DEPENDENCIES.md`:

```
Direct Dependencies:

Bedaan4D-ML (Core Backend)
├── PostgreSQL 14+
├── Python 3.9+
├── Libraries:
│   ├── requests (API calls)
│   ├── psycopg2 (Database)
│   └── pandas (Data processing)
└── External APIs:
    └── BRS API

Bedaan_4D_AI (Analysis Engine)
├── Bedaan4D-ML (data source)
├── Python 3.9+
├── Libraries:
│   ├── scikit-learn (ML)
│   ├── pandas (Processing)
│   └── numpy (Computation)
└── Data Input:
    └── PostgreSQL

Bedaan6D-project (Frontend)
├── Node.js 18+
├── Next.js 16+
├── PostgreSQL 14+ (via Prisma)
├── UI Libraries:
│   ├── Radix UI (Components)
│   ├── TailwindCSS (Styling)
│   └── Recharts (Visualization)
└── Data Source:
    └── Backend API

Shared Resources:
├── PostgreSQL Database (single instance)
├── Redis Cache (optional, future)
├── Environment Configuration (.env)
└── Authentication System
```

### 1.2.5 Configuration Documentation

Create `docs/CONFIGURATION.md`:

```ini
# Environment Variables Schema

## Database Configuration
DATABASE_URL=postgresql://user:pass@localhost:5432/bedaan_unified
DATABASE_POOL_SIZE=20
DATABASE_TIMEOUT=30

## API Configuration
API_PORT=3000
API_HOST=0.0.0.0
BRS_API_KEY=<secret>
BRS_API_BASE_URL=https://api.brsapi.ir

## Frontend Configuration
NEXT_PUBLIC_API_URL=http://localhost:3000/api
NEXT_PUBLIC_APP_NAME=Bedaan Unified Analytics

## ML Configuration
ML_MODEL_PATH=/models/latest
ML_UPDATE_INTERVAL=3600
ML_SIGNAL_THRESHOLD=0.75

## Logging
LOG_LEVEL=info
LOG_FORMAT=json
LOG_STORAGE=/var/log/bedaan

## Security
JWT_SECRET=<secret>
CORS_ORIGINS=http://localhost:3000,http://localhost:3005
```

### 1.2.6 Maintenance Documentation

Create `docs/MAINTENANCE.md`:

```
Database Maintenance
- Backup Strategy: Daily full, hourly incremental
- Retention: 30 days
- Backup Location: S3://bedaan-backups/
- Restore Procedure: [detailed steps]

API Rate Limiting
- BRS API: 1000 requests/hour
- Internal Cache: TTL 5 minutes for symbol list
- Fallback Strategy: Serve stale cache if API unavailable

ML Model Updates
- Retraining Schedule: Weekly
- Validation: Backtest on 252-day lookback
- Deployment: Canary (5% traffic) → Full
- Rollback: If accuracy drops >2%

Performance Monitoring
- API Response Time: <200ms p95
- Database Query Time: <100ms p95
- Frontend Load: <3s Core Web Vitals
- Uptime Target: 99.5%
```

---

# Phase 2: Strategic Planning & Roadmap

## 2.1 Current State Assessment

### Portfolio Composition

**Bedaan4D-ML** (Backend Core)
- ✅ Mature data acquisition pipeline
- ✅ Comprehensive error handling
- ✅ Multiple DB support (PostgreSQL, SQLite)
- ⚠️ No REST API layer yet
- ⚠️ Limited to domestic market (BRS)
- ⚠️ Monolithic Python structure

**Bedaan6D-project** (Frontend)
- ✅ Modern Next.js framework
- ✅ TypeScript for type safety
- ✅ Component library (Radix UI + shadcn/ui)
- ✅ Database integration (Prisma)
- ⚠️ No backend API integration
- ⚠️ Limited data sources
- ⚠️ Dashboard incomplete

**Bedaan_4D_AI** (Analysis)
- ✅ ML processing capability
- ⚠️ Minimal documentation
- ⚠️ Integration points unclear

**CryptoAndStocks** (Expansion)
- ⚠️ Early stage
- ⚠️ Unclear architecture
- ✅ Potential for multi-asset support

### Integration Challenges

| Challenge | Impact | Mitigation |
|-----------|--------|-----------|
| Separate databases | Data silos, inconsistent state | Unified schema migration |
| No API layer | Direct DB coupling | API abstraction layer |
| Python + Node.js | Operational complexity | Clear service boundaries |
| Unstructured data flow | System fragility | Event-driven architecture |
| Shared resources conflict | Performance degradation | Resource pooling & monitoring |

## 2.2 Phased Integration Roadmap

### Phase 2a: Foundation (Weeks 1-4)

**Objective**: Establish unified infrastructure and communication layer

#### Week 1-2: API Layer Creation

Create `backend/api/` directory in Bedaan4D-ML:

```
backend/api/
├── __init__.py
├── main.py                          # FastAPI application
├── routes/
│   ├── market.py                    # Market data endpoints
│   ├── analysis.py                  # ML analysis endpoints
│   ├── portfolio.py                 # Portfolio management
│   └── health.py                    # Health checks
├── models/
│   ├── schemas.py                   # Pydantic models
│   ├── responses.py                 # Response schemas
│   └── errors.py                    # Error models
├── middleware/
│   ├── auth.py                      # JWT authentication
│   ├── logging.py                   # Request logging
│   └── cors.py                      # CORS configuration
├── config/
│   ├── settings.py                  # Environment config
│   └── database.py                  # DB connection pool
└── utils/
    ├── rate_limiter.py              # API rate limiting
    └── cache.py                     # Response caching
```

**Implementation Details:**

```python
# backend/api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import market, analysis
from .middleware import auth, logging

app = FastAPI(
    title="Bedaan Unified API",
    version="1.0.0",
    docs_url="/api/v1/docs"
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3005", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(logging.LoggingMiddleware)

# Include routers
app.include_router(market.router, prefix="/api/v1/market")
app.include_router(analysis.router, prefix="/api/v1/analysis")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}
```

**Deliverables**:
- [ ] FastAPI application scaffold
- [ ] Core endpoint implementations (symbols, price history)
- [ ] Pydantic schemas for data validation
- [ ] Authentication/authorization framework
- [ ] OpenAPI documentation

#### Week 2-3: Database Schema Unification

Create unified schema migration:

```sql
-- Create unified bedaan schema
CREATE SCHEMA IF NOT EXISTS bedaan_unified;

-- Tables mapping
-- bedaan_unified.symbols (from existing stocks)
-- bedaan_unified.price_candles (from existing price_data)
-- bedaan_unified.ml_signals (new from Bedaan_4D_AI)
-- bedaan_unified.portfolios (new for user portfolios)
-- bedaan_unified.alerts (new for user alerts)

-- Create view for backward compatibility
CREATE VIEW bedaan4d_ml.stocks AS
SELECT * FROM bedaan_unified.symbols
WHERE market = 'TSE';
```

**Deliverables**:
- [ ] Unified schema design
- [ ] Migration scripts
- [ ] Backward compatibility views
- [ ] Index optimization plan
- [ ] Schema versioning strategy

#### Week 3-4: Integration Testing

```python
# tests/integration/test_data_flow.py
import pytest
from api.main import app
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_symbol_retrieval():
    """Test data flow from DB → API → Frontend"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/market/symbols")
        assert response.status_code == 200
        assert len(response.json()["data"]) > 0

@pytest.mark.asyncio
async def test_price_history_retrieval():
    """Test OHLCV data retrieval pipeline"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/market/price-history",
            params={"symbol": "FSPD", "interval": "1d"}
        )
        assert response.status_code == 200
        assert all(k in response.json()[0] for k in ["open", "high", "low", "close"])
```

**Deliverables**:
- [ ] Integration test suite
- [ ] Test coverage reports
- [ ] Performance benchmarks
- [ ] Load test results

### Phase 2b: Frontend Integration (Weeks 5-8)

**Objective**: Connect Bedaan6D-project frontend to unified API

#### Week 5-6: API Client Integration

Create `src/services/api/bedaan-client.ts`:

```typescript
// src/services/api/bedaan-client.ts
import axios, { AxiosInstance } from 'axios';

export interface Symbol {
  symbol: string;
  name: string;
  market: 'TSE' | 'OTC' | 'ETF' | 'CRYPTO';
  sector: string;
  active: boolean;
}

export interface Candle {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  turnover: number;
}

export interface Signal {
  symbol: string;
  signal: 'BUY' | 'SELL' | 'HOLD';
  confidence: number;
  reasoning: string;
  updatedAt: string;
}

export class BedaanClient {
  private client: AxiosInstance;

  constructor(baseURL: string = process.env.NEXT_PUBLIC_API_URL) {
    this.client = axios.create({
      baseURL,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  async getSymbols(type?: string): Promise<Symbol[]> {
    const response = await this.client.get<{ data: Symbol[] }>(
      '/market/symbols',
      { params: { type } }
    );
    return response.data.data;
  }

  async getPriceHistory(
    symbol: string,
    interval: '1m' | '5m' | '15m' | '1h' | '1d' = '1d',
    days: number = 252
  ): Promise<Candle[]> {
    const response = await this.client.get<{ data: Candle[] }>(
      '/market/price-history',
      {
        params: {
          symbol,
          interval,
          days,
        },
      }
    );
    return response.data.data;
  }

  async getSignals(symbol: string): Promise<Signal> {
    const response = await this.client.get<{ data: Signal }>(
      `/analysis/signals/${symbol}`
    );
    return response.data.data;
  }
}
```

**Deliverables**:
- [ ] TypeScript API client
- [ ] Service layer abstraction
- [ ] Error handling utilities
- [ ] Type definitions
- [ ] Request/response interceptors

#### Week 6-7: Component Refactoring

Update existing components to use unified API:

```typescript
// src/components/MarketDashboard.tsx
import { useQuery } from '@tanstack/react-query';
import { BedaanClient } from '@/services/api/bedaan-client';

const client = new BedaanClient();

export function MarketDashboard() {
  const { data: symbols } = useQuery({
    queryKey: ['symbols'],
    queryFn: () => client.getSymbols(),
  });

  const { data: priceHistory } = useQuery({
    queryKey: ['price-history', selectedSymbol],
    queryFn: () => client.getPriceHistory(selectedSymbol),
    enabled: !!selectedSymbol,
  });

  const { data: signal } = useQuery({
    queryKey: ['signals', selectedSymbol],
    queryFn: () => client.getSignals(selectedSymbol),
    enabled: !!selectedSymbol,
  });

  return (
    <div className="space-y-4">
      <SymbolSelector symbols={symbols} />
      <PriceChart data={priceHistory} />
      <SignalIndicator signal={signal} />
    </div>
  );
}
```

**Deliverables**:
- [ ] Refactored components
- [ ] React Query integration
- [ ] Error boundaries
- [ ] Loading states
- [ ] Component test updates

#### Week 7-8: Real-time Updates

Implement WebSocket support for live data:

```typescript
// src/services/websocket/market-stream.ts
import { useEffect, useState } from 'react';

export function useMarketStream(symbols: string[]) {
  const [prices, setPrices] = useState<Map<string, number>>(new Map());

  useEffect(() => {
    const ws = new WebSocket(
      `${process.env.NEXT_PUBLIC_WS_URL}/market/stream`
    );

    ws.onopen = () => {
      ws.send(JSON.stringify({ action: 'subscribe', symbols }));
    };

    ws.onmessage = (event) => {
      const { symbol, price } = JSON.parse(event.data);
      setPrices((prev) => new Map(prev).set(symbol, price));
    };

    return () => ws.close();
  }, [symbols]);

  return prices;
}
```

**Deliverables**:
- [ ] WebSocket implementation
- [ ] Live price updates
- [ ] Signal notifications
- [ ] Connection recovery
- [ ] Performance optimization

### Phase 2c: ML Analysis Integration (Weeks 9-12)

**Objective**: Integrate Bedaan_4D_AI outputs into API and frontend

#### Week 9: Signal Generation Pipeline

Create standardized ML signal output format:

```python
# backend/ml/signal_generator.py
from enum import Enum
from datetime import datetime
from pydantic import BaseModel

class SignalType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

class MLSignal(BaseModel):
    symbol: str
    signal: SignalType
    confidence: float  # 0-100
    expected_return: float  # percentage
    risk_score: float  # 0-100
    reasoning: str
    technical_factors: dict
    fundamental_factors: dict
    generated_at: datetime
    valid_until: datetime

class SignalGenerator:
    def __init__(self, model_path: str):
        self.model = self._load_model(model_path)

    def generate_signal(self, symbol: str, lookback_days: int = 252) -> MLSignal:
        """Generate ML-based trading signal"""
        # Implementation combines:
        # - Technical analysis (Bedaan4D-ML)
        # - Fundamental analysis (Financial data)
        # - Sentiment analysis (Bedaan_4D_AI)
        # - Pattern recognition (ML models)
        
        signal = self.model.predict(symbol, lookback_days)
        return MLSignal(
            symbol=symbol,
            signal=SignalType(signal['type']),
            confidence=float(signal['confidence']),
            expected_return=float(signal['expected_return']),
            risk_score=float(signal['risk_score']),
            reasoning=signal['reasoning'],
            technical_factors=signal['technical'],
            fundamental_factors=signal['fundamental'],
            generated_at=datetime.utcnow(),
            valid_until=datetime.utcnow() + timedelta(hours=24)
        )
```

**Deliverables**:
- [ ] Signal schema definition
- [ ] Model integration layer
- [ ] Signal persistence
- [ ] Signal validation tests

#### Week 10-11: Analytics Dashboard

Create advanced analytics views:

```typescript
// src/app/analytics/page.tsx
export default function AnalyticsDashboard() {
  const { data: symbols } = useSymbols();
  const { data: signals } = useSignals();
  const { data: portfolioStats } = usePortfolioStats();

  return (
    <div className="grid grid-cols-4 gap-4">
      {/* Top performers */}
      <TopPerformers signals={signals} />
      
      {/* Signal distribution */}
      <SignalDistribution signals={signals} />
      
      {/* Risk heatmap */}
      <RiskHeatmap symbols={symbols} />
      
      {/* Portfolio allocation */}
      <PortfolioAllocation stats={portfolioStats} />
      
      {/* ML model performance */}
      <ModelPerformance />
    </div>
  );
}
```

**Deliverables**:
- [ ] Analytics page implementation
- [ ] Advanced visualizations
- [ ] Performance metrics
- [ ] Risk dashboards
- [ ] Custom reports

#### Week 12: Model Monitoring

Implement ML model performance tracking:

```python
# backend/monitoring/model_monitor.py
from sqlalchemy import Column, String, Float, DateTime
from datetime import datetime

class ModelMetric(Base):
    __tablename__ = "model_metrics"
    
    id = Column(UUID, primary_key=True, default=uuid4)
    model_version = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    accuracy = Column(Float)
    precision = Column(Float)
    recall = Column(Float)
    f1_score = Column(Float)
    backtest_return = Column(Float)
    sharpe_ratio = Column(Float)
    max_drawdown = Column(Float)

class ModelMonitor:
    def log_performance(self, metrics: dict):
        """Log model performance metrics"""
        db.add(ModelMetric(**metrics))
        db.commit()
        
        # Alert if performance degrades
        if metrics['accuracy'] < 0.65:
            self.trigger_alert(
                "model_degradation",
                f"Accuracy dropped to {metrics['accuracy']}"
            )
```

**Deliverables**:
- [ ] Performance metrics schema
- [ ] Automated monitoring
- [ ] Alert system
- [ ] Model versioning
- [ ] Automated rollback logic

### Phase 2d: Multi-Asset Support (Weeks 13-16)

**Objective**: Extend to crypto, commodities, and global markets

#### Week 13-14: Crypto Integration

```python
# backend/sources/crypto_provider.py
from abc import ABC, abstractmethod
from enum import Enum

class CryptoExchange(str, Enum):
    BINANCE = "BINANCE"
    KRAKEN = "KRAKEN"
    COINBASE = "COINBASE"

class CryptoProvider(ABC):
    @abstractmethod
    async def get_symbols(self) -> List[str]:
        pass

    @abstractmethod
    async def get_price_history(
        self, 
        symbol: str, 
        interval: str
    ) -> List[Candle]:
        pass

class BinanceProvider(CryptoProvider):
    def __init__(self, api_key: str, api_secret: str):
        self.client = Client(api_key, api_secret)

    async def get_symbols(self) -> List[str]:
        """Fetch available trading pairs"""
        # Implementation

    async def get_price_history(
        self, 
        symbol: str, 
        interval: str
    ) -> List[Candle]:
        """Fetch OHLCV data"""
        # Implementation
```

**Deliverables**:
- [ ] Crypto data provider interface
- [ ] Multi-exchange support
- [ ] Data normalization
- [ ] Price aggregation
- [ ] Volume analysis

#### Week 15-16: Portfolio & Risk Management

```python
# backend/portfolio/portfolio_manager.py
class Portfolio(Base):
    __tablename__ = "portfolios"
    
    id = Column(UUID, primary_key=True)
    user_id = Column(UUID, ForeignKey("users.id"))
    name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class Position(Base):
    __tablename__ = "positions"
    
    id = Column(UUID, primary_key=True)
    portfolio_id = Column(UUID, ForeignKey("portfolios.id"))
    symbol = Column(String)
    quantity = Column(Float)
    entry_price = Column(Float)
    current_price = Column(Float)
    market = Column(String)  # TSE, CRYPTO, etc.

class PortfolioAnalyzer:
    def calculate_allocation(self, portfolio: Portfolio) -> dict:
        """Calculate portfolio allocation percentages"""
        # Sector allocation
        # Asset class allocation
        # Geographic distribution
        return {
            "by_sector": {...},
            "by_market": {...},
            "by_risk": {...}
        }

    def calculate_metrics(self, portfolio: Portfolio) -> dict:
        """Calculate portfolio performance metrics"""
        return {
            "total_value": float,
            "total_return": float,
            "ytd_return": float,
            "sharpe_ratio": float,
            "max_drawdown": float,
            "correlation_matrix": dict
        }
```

**Deliverables**:
- [ ] Portfolio management system
- [ ] Risk metrics calculation
- [ ] Performance attribution
- [ ] Rebalancing recommendations
- [ ] Tax-loss harvesting suggestions

## 2.3 Risk Assessment

### Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| Database migration failure | Medium | High | Comprehensive backup, dry-run tests, rollback plan |
| API bottleneck | Medium | Medium | Load testing, caching layer, rate limiting |
| Data inconsistency | Low | Critical | Transactions, audit logs, verification queries |
| Performance regression | Medium | High | Automated benchmarks in CI/CD |

### Operational Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| Service outage | Low | High | Monitoring, alerts, failover mechanisms |
| External API downtime (BRS) | Medium | Medium | Fallback cache, graceful degradation |
| Model accuracy degradation | Medium | Medium | Performance monitoring, automated alerts |

### Timeline Risks

| Risk | Mitigation |
|------|-----------|
| Dependency delays | Start API and Frontend integration in parallel (Weeks 5-8) |
| Integration complexity | Use mock data initially, gradual integration |
| Team capacity | Prioritize Foundation phase, defer nice-to-haves |

---

# Phase 3: Technical Architecture Design

## 3.1 System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     Frontend Layer (Bedaan6D)                    │
│  Next.js 16 + TypeScript + Radix UI + TailwindCSS             │
│  - Dashboard, Analytics, Portfolio Management, Alerts          │
└────────────┬──────────────────────────────────────────────────┘
             │ HTTP/WebSocket
┌────────────▼──────────────────────────────────────────────────┐
│              API Gateway & Load Balancer                        │
│  - Request routing, rate limiting, authentication              │
└────────────┬──────────────────────────────────────────────────┘
             │
    ┌────────┴────────┬─────────────┬──────────────┐
    │                 │             │              │
┌───▼────────┐  ┌─────▼──────┐  ┌──▼─────┐  ┌────▼──────┐
│  Market    │  │  Analysis  │  │Portfolio│  │Auth/User  │
│  Service   │  │  Service   │  │Service  │  │Service    │
└───┬────────┘  └─────┬──────┘  └──┬─────┘  └────┬──────┘
    │                 │             │             │
    │ ┌───────────────┴─────────────┴─────────────┘
    │ │
┌───▼─┴──────────────────────────────────────────────────┐
│         PostgreSQL Unified Database                     │
│  - Market Data, ML Signals, User Data, Analytics      │
└──────────────────────────────────────────────────────┘
    │
    ├─ ┌──────────────────────────────┐
    ├─▶│ Data Providers               │
    │  │ - BRS API (Domestic Markets) │
    │  │ - Crypto Exchanges           │
    │  │ - International APIs         │
    │  └──────────────────────────────┘
    │
    └─ ┌──────────────────────────────┐
       │ Analysis Engines              │
       │ - ML Models (Bedaan_4D_AI)    │
       │ - Technical Analysis          │
       │ - Fundamental Analysis        │
       └──────────────────────────────┘
```

## 3.2 Database Schema Design

### 3.2.1 Unified Data Model

```sql
-- Core asset information
CREATE TABLE assets (
    id UUID PRIMARY KEY,
    symbol VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    asset_class VARCHAR(20) NOT NULL,  -- EQUITY, CRYPTO, ETF, COMMODITY
    market VARCHAR(20) NOT NULL,        -- TSE, OTC, BINANCE, NYSE
    sector VARCHAR(100),
    sub_sector VARCHAR(100),
    country_code VARCHAR(2),
    active BOOLEAN DEFAULT TRUE,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_asset_symbol (symbol),
    INDEX idx_asset_class (asset_class),
    INDEX idx_asset_market (market)
);

-- OHLCV price data (normalized across all markets)
CREATE TABLE price_candles (
    id UUID PRIMARY KEY,
    asset_id UUID NOT NULL REFERENCES assets(id),
    timestamp TIMESTAMP NOT NULL,
    timeframe VARCHAR(10) NOT NULL,    -- 1m, 5m, 15m, 1h, 1d, 1w
    open DECIMAL(20, 8) NOT NULL,
    high DECIMAL(20, 8) NOT NULL,
    low DECIMAL(20, 8) NOT NULL,
    close DECIMAL(20, 8) NOT NULL,
    volume BIGINT NOT NULL,
    turnover DECIMAL(20, 2),
    transactions INTEGER,
    adjusted_close DECIMAL(20, 8),
    source VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(asset_id, timestamp, timeframe),
    INDEX idx_candle_timestamp (timestamp),
    INDEX idx_candle_asset_timestamp (asset_id, timestamp DESC)
);

-- ML-generated trading signals
CREATE TABLE ml_signals (
    id UUID PRIMARY KEY,
    asset_id UUID NOT NULL REFERENCES assets(id),
    signal_type VARCHAR(10) NOT NULL,  -- BUY, SELL, HOLD
    confidence DECIMAL(5, 2) NOT NULL,  -- 0-100
    expected_return DECIMAL(8, 2),      -- percentage
    risk_score DECIMAL(5, 2),           -- 0-100
    reasoning TEXT,
    technical_factors JSONB,
    fundamental_factors JSONB,
    ml_model_version VARCHAR(50),
    generated_at TIMESTAMP DEFAULT NOW(),
    valid_until TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    INDEX idx_signal_asset (asset_id),
    INDEX idx_signal_generated (generated_at DESC),
    INDEX idx_signal_active (is_active)
);

-- User portfolios
CREATE TABLE portfolios (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    is_public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_portfolio_user (user_id)
);

-- Portfolio positions
CREATE TABLE positions (
    id UUID PRIMARY KEY,
    portfolio_id UUID NOT NULL REFERENCES portfolios(id),
    asset_id UUID NOT NULL REFERENCES assets(id),
    quantity DECIMAL(20, 8) NOT NULL,
    entry_price DECIMAL(20, 8) NOT NULL,
    entry_date DATE NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_position_portfolio (portfolio_id),
    INDEX idx_position_asset (asset_id),
    UNIQUE(portfolio_id, asset_id)
);

-- User alerts
CREATE TABLE alerts (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    asset_id UUID NOT NULL REFERENCES assets(id),
    alert_type VARCHAR(20) NOT NULL,  -- PRICE, SIGNAL, NEWS, PERFORMANCE
    condition JSONB NOT NULL,
    threshold_value DECIMAL(20, 8),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    triggered_at TIMESTAMP,
    INDEX idx_alert_user (user_id),
    INDEX idx_alert_active (is_active)
);

-- API request logging
CREATE TABLE api_request_logs (
    id UUID PRIMARY KEY,
    user_id UUID,
    endpoint VARCHAR(255),
    method VARCHAR(10),
    status_code INTEGER,
    response_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_log_user (user_id),
    INDEX idx_log_timestamp (created_at)
);
```

### 3.2.2 Performance Optimization

```sql
-- Materialized views for common queries
CREATE MATERIALIZED VIEW asset_latest_prices AS
SELECT DISTINCT ON (asset_id)
    asset_id,
    timestamp,
    close AS current_price,
    (close - LAG(close) OVER (PARTITION BY asset_id ORDER BY timestamp)) / 
    LAG(close) OVER (PARTITION BY asset_id ORDER BY timestamp) * 100 AS day_change_pct
FROM price_candles
WHERE timeframe = '1d'
ORDER BY asset_id, timestamp DESC;

CREATE INDEX idx_latest_prices ON asset_latest_prices(asset_id);

-- Partitioning for large tables
CREATE TABLE price_candles_partitioned (
    id UUID,
    asset_id UUID,
    timestamp TIMESTAMP,
    ...
) PARTITION BY RANGE (timestamp);

CREATE TABLE price_candles_2024_q1 PARTITION OF price_candles_partitioned
    FOR VALUES FROM ('2024-01-01') TO ('2024-04-01');

CREATE TABLE price_candles_2024_q2 PARTITION OF price_candles_partitioned
    FOR VALUES FROM ('2024-04-01') TO ('2024-07-01');
```

## 3.3 Backend Infrastructure Design

### 3.3.1 Microservices Architecture

```
Service Decomposition:

1. Market Data Service (Python)
   ├── Responsibilities:
   │   ├── Data acquisition from providers
   │   ├── Data normalization
   │   └── Storage in database
   ├── External Dependencies:
   │   ├── BRS API
   │   ├── Crypto exchanges (Binance, Kraken)
   │   └── International market APIs
   └── Port: 3001

2. Analysis Service (Python)
   ├── Responsibilities:
   │   ├── ML signal generation
   │   ├── Technical analysis
   │   ├── Fundamental analysis
   │   └── Sentiment analysis
   ├── Dependencies:
   │   ├── Market Data Service (via API)
   │   └── ML models (trained models)
   └── Port: 3002

3. Portfolio Service (Python or Node.js)
   ├── Responsibilities:
   │   ├── Portfolio CRUD operations
   │   ├── Position management
   │   ├── Performance calculations
   │   └── Recommendations
   ├── Dependencies:
   │   ├── Market Data Service
   │   ├── Analysis Service
   │   └── User Service
   └── Port: 3003

4. User Service (Node.js)
   ├── Responsibilities:
   │   ├── Authentication
   │   ├── User profiles
   │   ├── Alerts management
   │   └── Preferences
   ├── External:
   │   └── Auth provider (optional)
   └── Port: 3004

5. API Gateway (Node.js)
   ├── Responsibilities:
   │   ├── Request routing
   │   ├── Rate limiting
   │   ├── Caching
   │   └── Monitoring
   └── Port: 3000
```

### 3.3.2 Data Pipeline Architecture

```python
# backend/pipeline/orchestration.py
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'bedaan',
    'start_date': datetime(2024, 1, 1),
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

with DAG('market_data_pipeline', default_args=default_args) as dag:
    
    # 1. Data Acquisition
    fetch_brs_data = PythonOperator(
        task_id='fetch_brs_data',
        python_callable=fetch_brs_market_data,
        retries=3
    )
    
    # 2. Data Validation
    validate_data = PythonOperator(
        task_id='validate_data',
        python_callable=validate_price_data,
        depends_on_past=False
    )
    
    # 3. Data Storage
    store_data = PythonOperator(
        task_id='store_data',
        python_callable=store_to_database
    )
    
    # 4. ML Signal Generation
    generate_signals = PythonOperator(
        task_id='generate_signals',
        python_callable=generate_ml_signals,
        depends_on_past=False
    )
    
    # 5. Notification
    send_alerts = PythonOperator(
        task_id='send_alerts',
        python_callable=notify_users
    )
    
    # Define dependencies
    fetch_brs_data >> validate_data >> store_data >> [generate_signals, send_alerts]
```

### 3.3.3 Caching Strategy

```python
# backend/cache/cache_manager.py
from redis import Redis
from typing import Optional, Any

class CacheManager:
    def __init__(self, redis_url: str):
        self.redis = Redis.from_url(redis_url)
    
    def set_symbol_cache(self, symbols: List[str], ttl: int = 3600):
        """Cache symbol list with 1-hour TTL"""
        self.redis.setex(
            'symbols:all',
            ttl,
            json.dumps(symbols)
        )
    
    def set_price_cache(self, symbol: str, data: dict, ttl: int = 300):
        """Cache recent prices with 5-minute TTL"""
        self.redis.setex(
            f'price:{symbol}',
            ttl,
            json.dumps(data)
        )
    
    def get_or_fetch(self, key: str, fetch_fn, ttl: int = 3600):
        """Get from cache or fetch and cache"""
        cached = self.redis.get(key)
        if cached:
            return json.loads(cached)
        
        data = fetch_fn()
        self.redis.setex(key, ttl, json.dumps(data))
        return data
```

## 3.4 Frontend Integration Design

### 3.4.1 Application Architecture

```
src/
├── app/                          # Next.js app router
│   ├── dashboard/                # Main dashboard
│   │   ├── page.tsx
│   │   ├── layout.tsx
│   │   └── components/
│   ├── analytics/                # Advanced analytics
│   │   ├── page.tsx
│   │   └── components/
│   ├── portfolio/                # Portfolio management
│   │   ├── [id]/
│   │   └── components/
│   ├── alerts/                   # Alert management
│   └── api/                      # Route handlers
│
├── components/                   # Reusable components
│   ├── common/
│   │   ├── Header.tsx
│   │   ├── Sidebar.tsx
│   │   └── Footer.tsx
│   ├── market/
│   │   ├── SymbolSearch.tsx
│   │   ├── PriceChart.tsx
│   │   └── MarketNews.tsx
│   ├── analysis/
│   │   ├── SignalIndicator.tsx
│   │   ├── TechnicalAnalysis.tsx
│   │   └── FundamentalMetrics.tsx
│   └── portfolio/
│       ├── AllocationChart.tsx
│       ├── PerformanceMetrics.tsx
│       └── RiskAnalysis.tsx
│
├── services/                     # API clients
│   ├── api/
│   │   ├── bedaan-client.ts
│   │   └── interceptors.ts
│   ├── websocket/
│   │   └── market-stream.ts
│   └── auth/
│       └── auth-service.ts
│
├── stores/                       # State management (Zustand)
│   ├── market-store.ts
│   ├── portfolio-store.ts
│   ├── ui-store.ts
│   └── auth-store.ts
│
├── hooks/                        # Custom React hooks
│   ├── useMarketData.ts
│   ├── usePortfolio.ts
│   ├── useSignals.ts
│   └── useWebSocket.ts
│
├── lib/                          # Utilities
│   ├── utils.ts
│   ├── format.ts
│   ├── calculations.ts
│   └── validators.ts
│
└── styles/                       # Global styles
    └── globals.css
```

### 3.4.2 State Management

```typescript
// src/stores/market-store.ts
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

interface MarketState {
  // State
  selectedSymbol: string | null;
  symbols: Symbol[];
  priceHistory: Candle[];
  currentPrice: number | null;
  
  // Actions
  setSelectedSymbol: (symbol: string) => void;
  setSymbols: (symbols: Symbol[]) => void;
  setPriceHistory: (history: Candle[]) => void;
  updatePrice: (price: number) => void;
}

export const useMarketStore = create<MarketState>()(
  devtools(
    persist(
      (set) => ({
        selectedSymbol: null,
        symbols: [],
        priceHistory: [],
        currentPrice: null,
        
        setSelectedSymbol: (symbol) =>
          set({ selectedSymbol: symbol }),
        
        setSymbols: (symbols) =>
          set({ symbols }),
        
        setPriceHistory: (history) =>
          set({ priceHistory: history }),
        
        updatePrice: (price) =>
          set({ currentPrice: price }),
      }),
      {
        name: 'market-storage',
        partialize: (state) => ({
          selectedSymbol: state.selectedSymbol,
        }),
      }
    )
  )
);
```

### 3.4.3 Component Example: Market Dashboard

```typescript
// src/components/market/MarketDashboard.tsx
'use client';

import { useCallback, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useMarketStore } from '@/stores/market-store';
import { BedaanClient } from '@/services/api/bedaan-client';
import { SymbolSearch } from './SymbolSearch';
import { PriceChart } from './PriceChart';
import { SignalIndicator } from '@/components/analysis/SignalIndicator';
import { MarketNews } from './MarketNews';

const client = new BedaanClient();

export function MarketDashboard() {
  const { selectedSymbol, setSelectedSymbol } = useMarketStore();

  // Fetch available symbols
  const { data: symbols = [] } = useQuery({
    queryKey: ['symbols'],
    queryFn: () => client.getSymbols(),
    staleTime: 1000 * 60 * 60, // 1 hour
  });

  // Fetch price history for selected symbol
  const { data: priceHistory = [] } = useQuery({
    queryKey: ['price-history', selectedSymbol],
    queryFn: () =>
      client.getPriceHistory(selectedSymbol!, '1d', 252),
    enabled: !!selectedSymbol,
  });

  // Fetch ML signal
  const { data: signal } = useQuery({
    queryKey: ['signal', selectedSymbol],
    queryFn: () => client.getSignals(selectedSymbol!),
    enabled: !!selectedSymbol,
  });

  const handleSymbolSelect = useCallback((symbol: string) => {
    setSelectedSymbol(symbol);
  }, [setSelectedSymbol]);

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-3 gap-4">
        <div className="col-span-3">
          <SymbolSearch
            symbols={symbols}
            onSelect={handleSymbolSelect}
          />
        </div>

        {selectedSymbol && (
          <>
            <div className="col-span-2">
              <PriceChart data={priceHistory} />
            </div>

            <div>
              <SignalIndicator signal={signal} />
            </div>

            <div className="col-span-3">
              <MarketNews symbol={selectedSymbol} />
            </div>
          </>
        )}
      </div>
    </div>
  );
}
```

## 3.5 Real-time Data Architecture

### 3.5.1 WebSocket Implementation

```python
# backend/websocket/market_stream.py
from fastapi import WebSocket, WebSocketDisconnect
from typing import Set
import json
import asyncio

class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.subscribed_symbols: dict[WebSocket, set] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        self.subscribed_symbols[websocket] = set()

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        self.subscribed_symbols.pop(websocket, None)

    async def subscribe(self, websocket: WebSocket, symbols: list[str]):
        self.subscribed_symbols[websocket].update(symbols)

    async def broadcast_price_update(self, symbol: str, price_data: dict):
        """Broadcast price update to all subscribers"""
        message = json.dumps({
            'type': 'price_update',
            'symbol': symbol,
            'data': price_data
        })

        disconnected_clients = set()
        for websocket in self.active_connections:
            if symbol in self.subscribed_symbols.get(websocket, set()):
                try:
                    await websocket.send_text(message)
                except Exception as e:
                    disconnected_clients.add(websocket)

        for websocket in disconnected_clients:
            self.disconnect(websocket)

manager = ConnectionManager()

@app.websocket("/ws/market/stream")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            if data['action'] == 'subscribe':
                await manager.subscribe(websocket, data['symbols'])
            elif data['action'] == 'unsubscribe':
                manager.subscribed_symbols[websocket].difference_update(
                    data['symbols']
                )
    except WebSocketDisconnect:
        manager.disconnect(websocket)
```

### 3.5.2 Frontend WebSocket Hook

```typescript
// src/hooks/useMarketStream.ts
import { useEffect, useCallback } from 'react';
import { useMarketStore } from '@/stores/market-store';

export function useMarketStream(symbols: string[]) {
  const { updatePrice } = useMarketStore();

  useEffect(() => {
    const ws = new WebSocket(
      process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:3000/ws'
    );

    const handleOpen = () => {
      ws.send(
        JSON.stringify({
          action: 'subscribe',
          symbols,
        })
      );
    };

    const handleMessage = (event: MessageEvent) => {
      const { type, symbol, data } = JSON.parse(event.data);

      if (type === 'price_update') {
        updatePrice(data.close);
      }
    };

    const handleError = (error: Event) => {
      console.error('WebSocket error:', error);
    };

    const handleClose = () => {
      console.log('WebSocket disconnected, reconnecting in 5s...');
      setTimeout(() => {
        // Reconnect logic
      }, 5000);
    };

    ws.addEventListener('open', handleOpen);
    ws.addEventListener('message', handleMessage);
    ws.addEventListener('error', handleError);
    ws.addEventListener('close', handleClose);

    return () => {
      ws.close();
      ws.removeEventListener('open', handleOpen);
      ws.removeEventListener('message', handleMessage);
      ws.removeEventListener('error', handleError);
      ws.removeEventListener('close', handleClose);
    };
  }, [symbols, updatePrice]);
}
```

---

# Implementation Timeline

## Overall Project Timeline

| Phase | Duration | Key Milestones | Status |
|-------|----------|-----------------|--------|
| **Foundation** | Weeks 1-4 | API layer, unified schema, integration tests | Planning |
| **Frontend Integration** | Weeks 5-8 | Component refactoring, API connection, real-time | Planning |
| **ML Integration** | Weeks 9-12 | Signal generation, analytics, monitoring | Planning |
| **Multi-Asset Support** | Weeks 13-16 | Crypto, portfolio, risk management | Planning |
| **Optimization & Hardening** | Weeks 17-20 | Performance tuning, security, documentation | Planning |

## Critical Path

```
Week 1-2: API Foundation
    ↓
Week 2-3: Database Unification (parallel)
    ↓
Week 3-4: Integration Testing
    ↓
Week 5-6: Frontend API Client (blocks Weeks 7-8)
    ↓
Week 7-8: Real-time Updates
    ↓
Week 9-10: ML Signal Generation
    ↓
Week 11-12: Analytics Dashboard & Monitoring
    ↓
Week 13-14: Crypto Integration
    ↓
Week 15-16: Portfolio & Risk Management
```

---

# Risk Management

## Mitigation Strategies

### Data Migration Risk
- **Strategy**: Implement CDC (Change Data Capture) pattern
- **Validation**: Run dual-write system for 2 weeks before cutover
- **Rollback**: Keep old schema available for 30 days post-migration

### API Performance
- **Strategy**: Implement circuit breaker pattern
- **Monitoring**: Real-time latency tracking, automatic scaling
- **Fallback**: Redis cache with 5-minute staleness acceptable

### ML Model Accuracy
- **Strategy**: Automated backtest pipeline before deployment
- **Monitoring**: A/B testing with canary deployments
- **Rollback**: Automatic revert if F1 score drops >5%

---

# Conclusion

This comprehensive framework provides:

1. ✅ **Clear documentation strategy** ensuring all components are well-documented
2. ✅ **Phased integration roadmap** with realistic timelines and dependencies
3. ✅ **Scalable technical architecture** supporting multiple asset classes and real-time data
4. ✅ **Risk assessment and mitigation** for smooth execution
5. ✅ **Actionable implementation details** for immediate development

**Next Steps**:
1. Review and approve this framework
2. Assign teams to each phase
3. Set up monitoring and CI/CD pipeline
4. Begin Foundation Phase (Week 1)
5. Conduct architecture review with stakeholders
