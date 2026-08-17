# BedaanWaves Architecture

## System Overview

BedaanWaves is a unified capital market analysis platform consolidating 5 legacy projects into a single, optimized system with a layered architecture approach.

### Project Portfolio
- **.kilo** - Configuration and agent management layer
- **Bedaan_4D_AI** - Data archive (SQLite databases)
- **Bedaan4D-ML** - Python backend with FastAPI and 50+ services
- **Bedaan6D-project** - React/Next.js frontend with magic design system
- **CryptoAndStocks** - Full-stack crypto dashboard

## Technical Architecture

### Architecture Layers

#### Layer 1: Application Entry Points
- FastAPI application factory
- Application startup
- Server configuration
- Runner script

#### Layer 2: Middleware Stack
1. CORS Middleware - Cross-origin requests
2. GZip Compression - Response compression
3. Rate Limiting - DDoS protection (100 req/min)
4. Security Headers - HSTS, CSP, X-Frame-Options
5. Authentication - JWT token validation
6. Request Logging - Audit trail
7. Performance Monitoring - Metrics collection
8. Error Handling - Exception processing

#### Layer 3: API Routes (16+ Routers)
- Authentication: `/auth/*` (register, login, refresh)
- Stocks: `/stocks/*` (list, details, history, analysis, fundamental)
- Portfolio: `/portfolio/*` (create, details, add holdings)
- Alerts: `/alerts/*` (create, get, update, delete)
- Ranking: `/ranking/*` (general, sector, by-score)
- Market: `/market/*` (overview, indices, sectors)
- News: `/news/*` (search, symbol, sentiment)
- Analysis: `/analysis/*` (scores, signals, predict, backtest)

#### Layer 4: Services (50+ Services)
**Data Services:**
- BrsApiClient - Tehran Stock Exchange API
- CryptoApiClient - Cryptocurrency data
- NewsApiClient - News aggregation
- StockService - Stock data management
- MarketService - Market-wide analysis
- PortfolioService - Portfolio operations
- HistoryService - Time-series data

**Analysis Services:**
- ScoringService - 6D scoring calculation (305-node hierarchy)
- TechnicalAnalysisService - 50+ technical indicators
- FundamentalAnalysisService - Fundamental metrics
- RiskAnalysisService - Risk assessment
- MomentumService - Momentum analysis
- VolatilityService - Volatility calculation

**ML Services:**
- MLService - Model training/inference
- PricePredictionService - Time-series forecasting
- AnomalyDetectionService - Outlier detection
- ClusteringService - Pattern clustering
- ReinforcementLearnerService - RL models
- EnsembleService - Model ensemble voting

**NLP Services:**
- SentimentAnalysisService - Persian sentiment
- NewsAnalysisService - News processing
- NLPService - Natural language processing
- EntityExtractionService - Named entity extraction
- SummarizationService - Text summarization

**User Services:**
- UserService - User management
- AuthService - Authentication/JWT
- SubscriptionService - Subscription management
- PreferenceService - User preferences
- AlertService - Alert management
- NotificationService - Multi-channel notifications

**Specialized Services:**
- HierarchyService - 305-node hierarchy management
- AssistantService - AI recommendations
- BacktestService - Strategy backtesting
- PortfolioOptimizationService - Portfolio optimization
- RegressionAnalysisService - Statistical regression
- CorrelationService - Correlation analysis

**Crypto Services:**
- CryptoPriceService - Cryptocurrency price tracking (✅ Implemented)
- CryptoPortfolioService - Crypto portfolio management (✅ Implemented)
- CryptoAnalysisService - Cryptocurrency market analysis (🔧 Pending)
- ChainAnalysisService - Blockchain transaction analysis (🔧 Pending)
- DeFiService - DeFi protocol analysis (🔧 Pending)
- TransactionService - On-chain transaction processing (🔧 Pending)
- WalletService - Wallet monitoring (🔧 Pending)

**System Services:**
- DataRecoveryService - Data recovery
- BackupService - Backup management
- AuditService - Audit logging
- PerformanceMonitor - Performance tracking
- ErrorHandler - Exception handling
- RateLimiter - Rate limiting
- SchedulerService - Task scheduling
- NotificationDispatcher - Multi-channel notifications

#### Layer 5: Core Components (20+ Components)
- DependencyContainer - Dependency injection
- ErrorHandler - Error management
- HooksSystem - Event hooks
- CachingManager - Cache management
- ResponseFormatter - API responses
- HealthChecker - Health checks
- RateLimiter - Rate limiting
- JWTService - JWT handling
- DatabasePool - Connection pooling
- Logger - Structured logging

#### Layer 6: Data Access Layer
**Database (PostgreSQL)**
- assets - Stock/crypto universe
- symbols - Symbol metadata
- exchanges - Exchange information
- market_data - OHLCV candles
- technical_signals - Technical indicators
- fundamental_data - Fundamental metrics
- sentiment_scores - News sentiment
- ml_signals - ML predictions
- scores - Scoring results
- predictions - ML predictions
- anomalies - Detected anomalies
- correlations - Asset correlations
- users - User accounts
- portfolios - Portfolio definitions
- holdings - Portfolio holdings
- transactions - Transaction history
- alerts - User alerts
- subscriptions - Subscription info
- audit_log - Audit trail
- error_log - Error tracking
- performance_metrics - System metrics

**Cache Layer (Redis)**
- Session data
- User preferences
- Score cache (TTL: 24 hours)
- API responses (TTL: 5 mins)
- Rate limit counters

#### Layer 7: External Integrations
- **BRS API** - Stock market data
- **Crypto Exchanges** - Binance, Kraken, Coinbase
- **Codal API** - Financial disclosures
- **News APIs** - Multiple sources
- **Email Service** - Alert notifications
- **SMS Provider** - High-priority alerts

## Database Schema Design

### Unified Data Model

#### Core asset information
```sql
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
```

#### OHLCV price data (normalized across all markets)
```sql
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
```

#### ML-generated trading signals
```sql
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
```

#### User portfolios
```sql
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
```

#### Portfolio positions
```sql
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
```

#### User alerts
```sql
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
```

### Performance Optimization

#### Materialized views for common queries
```sql
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
```

#### Partitioning for large tables
```sql
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

## Criticality Upgrade Plan

### Security & Ops Foundation — P0

#### Secrets Management
- Database URL/password rotation in Vault/Secrets Manager
- JWT SECRET_KEY rotation with forced logout
- BRS API key rotation with service validation
- Git history cleanup using git-filter-repo
- CI pipeline integration with trufflehog/git-secrets

#### PostgreSQL Hardening
- SSL enforcement with sslmode=require
- Authentication restricted to scram-sha-256/md5
- Network access limited to authorized IPs
- Password encryption using scram-sha-256
- Role-based access control with least privilege
- DDL logging and slow query monitoring
- Extension preloading for monitoring

#### Backup & Recovery
- Daily physical base backup with WAL archiving
- Hourly logical backups with pg_dump
- Monthly recovery testing (fire drill)
- WAL retention for 7-day PITR capability
- Backup encryption via GPG or SSE-KMS

### Data Architecture & Schema Standards — P0/P1

#### Naming & Design Conventions
- Tables: snake_case, plural, descriptive (ir_price_candles, user_preferences)
- Columns: snake_case, with units when applicable (volume_24h_usd, price_irr)
- Indexes: idx_<table>_<col(s)>
- Unique constraints: uix_<table>_<col(s)>
- Checks: chk_<table>_<rule>
- Foreign keys: fk_<table>_<ref_table>
- UUID v4 for Primary Keys
- BigInteger for large volumes/amounts
- NUMERIC(p,s) for financial data (p=20, s=8)
- TIMESTAMPTZ for all timestamps (UTC storage)
- JSONB for metadata/flexibility

#### Base Model & Mixins
```python
class TimestampMixin:
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

class SoftDeleteMixin:
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)

class AuditMixin:
    created_by = Column(PG_UUID(as_uuid=True), nullable=True)  # FK to users.id
    updated_by = Column(PG_UUID(as_uuid=True), nullable=True)
```

#### Partitioning Strategy
- ir_price_candles: Monthly (>100M rows/year)
- intl_price_candles: Monthly (>50M rows/year)
- crypto_price_candles: Weekly (>200M rows/year)
- ir_order_book: Monthly (>50M rows/year)
- ir_retail_institutional: Monthly (>30M rows/year)
- api_logs: Daily (>10M rows/month)
- audit_logs: Monthly (>5M rows/month)
- ml_signals: Monthly (>1M rows/month)
- news/news_sentiment: Monthly (>10M rows/month)

#### Advanced Indexing
- BRIN for time-series append-only tables
- Partial indexes for common filters (active=true)
- Covering indexes (INCLUDE) for read-heavy queries
- Expression indexes for case-insensitive searches
- GIN for JSONB metadata queries
- GIST for full-text search on news content

### Migrations & Schema Evolution — P0

#### Migration Framework
- All schema changes via Alembic
- Autogenerate for new models
- No create_all in startup - only alembic upgrade head
- Non-destructive migrations (avoid DROP COLUMN in P0)
- Backward compatible migrations (add nullable, then NOT NULL)
- Transactional migrations (default Alembic behavior)
- Rollback plan documentation in every PR

#### Database CI/CD Pipeline
```yaml
name: Database CI
on: [push, pull_request]
jobs:
  migration-check:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: test_db
          POSTGRES_PASSWORD: test
        ports: ["5432:5432"]
    steps:
      - uses: actions/checkout@v4
      - name: Run migrations
        run: |
          cd backend
          alembic upgrade head
      - name: Check for pending migrations
        run: |
          alembic check
      - name: Run tests with migrated DB
        run: pytest tests/ -x -v
```

### Performance & Scalability — P1

#### Query Optimization & Connection Pooling
- Eliminate N+1 queries using selectinload/joinedload
- Connection pool sizing based on load testing
- Prepared statements for repeated queries
- Read replicas for scaling read workloads
- Query timeouts (statement_timeout = '30s')

#### Strategic Caching
- L1: In-process cache (cachetools.LRU/aiocache) - 60s TTL
- L2: Distributed Redis Cluster - 5min-1h TTL
- L3: Materialized Views - 1h-24h TTL with concurrent refresh

#### Observability & Alerting
| Metric | Warning Threshold | Critical Threshold |
|--------|-------------------|-------------------|
| pg_stat_activity count | >80% max_connections | >95% max_connections |
| pg_stat_database deadlocks | >0/min | >5/min |
| pg_stat_statements mean_time | >500ms | >2s |
| Replication Lag | >10s | >60s |
| WAL Archiving Lag | >5min | >30min |
| Disk Usage | >70% | >85% |
| Backup Age | >25h | >48h |
| idx_scan/seq_scan ratio | <0.9 | <0.7 |

### Data Governance & Compliance — P1

#### Data Classification
| Level | Examples | Encryption at Rest | Encryption in Transit | Access |
|-------|----------|-------------------|----------------------|--------|
| Public | Asset metadata, Market data | ❌ | TLS | Everyone |
| Internal | ML signals, Screening results | ❌ | TLS | App services |
| Confidential | User PII, Portfolio holdings | ✅ (Column-level) | TLS + mTLS | Need-to-know |
| Restricted | Password hashes, API keys | ✅ (App-level) | TLS + mTLS | Auth Service only |

#### Retention & Purging
| Table/Category | Retention Period | Deletion Method | Priority |
|----------------|------------------|-----------------|----------|
| api_logs | 90 days | Partition Drop + pg_cron | P1 |
| audit_logs | 7 years | Archive to Cold Storage (S3/Glacier) | P0 |
| refresh_tokens | Until expiry + 30 days | Background Job | P1 |
| news/news_sentiment | 2 years | Partition Drop | P2 |
| ml_predictions/anomalies | 1 year | Partition Drop | P2 |
| price_candles/order_book | 10 years | Tiered Storage (TimescaleDB/Hypertable) | P3 |

#### GDPR/Iran Privacy Compliance
- Right to Erasure: Soft Delete + Anonymization Job
- Data Portability: Export API (JSON/CSV)
- Data Minimization: Collect only necessary data
- DPIA: Documentation for high-risk processing

### Advanced Database Features — P2/P3

#### TimescaleDB/Hypertables for Time-Series
```sql
-- If TimescaleDB available:
SELECT create_hypertable('crypto_price_candles', 'timestamp', 
    chunk_time_interval => INTERVAL '1 week',
    if_not_exists => TRUE);

-- Compression for old chunks
ALTER TABLE crypto_price_candles SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'asset_id, timeframe'
);
SELECT add_compression_policy('crypto_price_candles', INTERVAL '30 days');
```

#### Materialized Views for Dashboards
```sql
-- Example: Daily Top Gainers/Losers
CREATE MATERIALIZED VIEW mv_daily_top_movers AS
SELECT 
    a.symbol,
    a.market,
    c.close,
    LAG(c.close) OVER (PARTITION BY a.id ORDER BY c.timestamp) as prev_close,
    (c.close - LAG(c.close) OVER (PARTITION BY a.id ORDER BY c.timestamp)) 
        / LAG(c.close) OVER (PARTITION BY a.id ORDER BY c.timestamp) * 100 as change_pct
FROM assets a
JOIN LATERAL (
    SELECT * FROM ir_price_candles 
    WHERE asset_id = a.id AND timeframe = '1d' 
    ORDER BY timestamp DESC LIMIT 2
) c ON true
WHERE a.active = true;

CREATE UNIQUE INDEX ON mv_daily_top_movers (symbol, market);
-- Refresh CONCURRENTLY every 15 minutes during market hours
```

#### Row Level Security for Multi-Tenancy
```sql
-- Enable RLS on portfolios
ALTER TABLE portfolios ENABLE ROW LEVEL SECURITY;

CREATE POLICY portfolio_isolation ON portfolios
    USING (user_id = current_setting('app.current_user_id')::uuid);

-- In application: SET LOCAL app.current_user_id = '...';
```

#### Logical Replication for CDC
| Purpose | Tool | Target Tables |
|---------|------|---------------|
| Sync to Data Warehouse | pgoutput + Debezium/Airbyte | assets, ml_signals, positions, portfolios |
| Real-time Notifications | pg_notify + LISTEN/NOTIFY | ml_signals, alerts, notifications |
| Immutable Audit Trail | pgaudit + Logical Replication | audit_logs, sensitive tables |

## Testing & Quality Assurance — P1

### Database Testing Strategy
| Test Level | Tool | Target Coverage | Example |
|------------|------|-----------------|---------|
| Unit (Model) | pytest + sqlalchemy | 100% models | Validation constraints |
| Integration (Repository) | pytest-asyncio + Testcontainers | 90% complex queries | Repository methods |
| Migration | alembic upgrade/downgrade | 100% migrations | Upgrade head, downgrade -1 |
| Contract (API) | pytest + httpx | 100% endpoints | Response schema, status codes |
| Performance (Load) | locust / k6 | Critical paths | 1000 RPS, p99 < 200ms |
| Chaos (Resilience) | chaostoolkit / pg_chaos | Failure scenarios | Connection loss, replica lag |

### Test Data Management
```python
# tests/factories.py
import factory
from factory.alchemy import SQLAlchemyModelFactory
from app.models.models import Asset, User, Portfolio

class AssetFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Asset
        sqlalchemy_session_persistence = "flush"
    
    symbol = factory.Sequence(lambda n: f"TEST{n:04d}")
    name = factory.Faker("company")
    asset_class = "EQUITY"
    market = "TSE"
    active = True

class UserFactory(SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session_persistence = "flush"
    
    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda o: f"{o.username}@test.com")
    hashed_password = "hashed"
    is_active = True
```

### Property-Based Testing for Constraints
```python
# tests/test_db_constraints.py
from hypothesis import given, strategies as st
import pytest

@given(st.decimals(min_value=0, max_value=1000000, places=8))
def test_price_positive(price):
    candle = IRPriceCandle(open=price, high=price, low=price, close=price, volume=1000)
    assert candle.open > 0

@given(st.integers(min_value=1, max_value=5))
def test_order_book_rank_valid(rank):
    ob = IROrderBook(rank=rank, asset_id=..., snapshot_time=...)
    assert 1 <= ob.rank <= 5
```

## Documentation & Knowledge Transfer — P2

### Required Documentation
| Document | Audience | Update Frequency | Status |
|----------|----------|------------------|--------|
| Data Dictionary | Dev, QA, BA, Ops | Every Migration | ⬜ |
| ER Diagram | All | Monthly | ⬜ |
| Migration Runbook | DevOps, SRE | Every Release | ⬜ |
| Incident Runbook (DB) | SRE, On-call | Quarterly | ⬜ |
| Capacity Planning Doc | Architecture, Ops | Bi-monthly | ⬜ |
| Security Hardening Checklist | Security, DevOps | Major Version | ⬜ |

### Data Dictionary Template
| Table | Column | Type | Nullable | Default | Description | Business Rule | Sensitivity | Retention | Indexes |
|-------|--------|------|----------|---------|-------------|---------------|-------------|-----------|---------|
| assets | symbol | VARCHAR(50) | NO | - | Unique symbol | Unique, Uppercase | Public | Permanent | PK, UQ, IX |
| portfolios | user_id | UUID | NO | - | Portfolio owner | FK users.id | Confidential | User lifetime | IX, FK |

## Implementation Roadmap

### Priority-Based Timeline
| Week | Phase | Deliverables | Owner |
|------|-------|--------------|-------|
| 1-2 | 0 | Rotate all secrets, PostgreSQL hardening, backup strategy | DevOps + Backend |
| 3-4 | 1 | BaseModel with Mixins, TIMESTAMPTZ migration, Soft Delete | Backend |
| 5-6 | 1 | Partition large tables (pg_partman), Advanced indexes | Backend + DBA |
| 7-8 | 2 | Complete CI/CD pipeline (Migration Check, Schema Drift, Load Test) | DevOps |
| 9-10 | 3 | Connection pooling (PgBouncer), Read replicas, Caching layer (Redis) | Backend + DevOps |
| 11-12 | 3 | Observability stack (Prometheus/Grafana/Alertmanager), Dashboards | DevOps + SRE |
| 13-14 | 4 | Data classification, Column-level encryption, Retention jobs (pg_cron) | Backend + Security |
| 15-16 | 5 | TimescaleDB/Hypertables, Materialized Views, RLS | Backend + DBA |
| 17-18 | 6 | Complete test suite (Unit, Integration, Migration, Load, Chaos) | QA + Backend |
| 19-20 | 7 | Complete documentation, Data dictionary, Runbooks, Knowledge transfer | Tech Lead + Team |

### Success Criteria
| KPI | Baseline | Target | Measurement |
|-----|----------|--------|-------------|
| Migration Success Rate | ~90% | 100% (Zero failed deploys) | CI/CD Pipeline |
| Query p99 Latency | >500ms | <100ms (cached), <200ms (uncached) | pg_stat_statements / APM |
| Connection Pool Utilization | N/A | <70% peak | PgBouncer stats |
| Backup Restore Test | Never tested | Monthly, RTO < 4h | Fire Drill Log |
| Security Findings (DB) | Unknown | 0 Critical, 0 High | Trivy, pg_audit, Manual Review |
| Schema Drift Incidents | Occasional | 0 | CI Check |
| Test Coverage (DB Layer) | ~40% | >90% | Coverage.py |

## Risks & Mitigation

| Risk | Probability | Impact | Mitigation Strategy |
|------|-------------|--------|---------------------|
| Production migration failure | Medium | High | Blue/Green deployment, Canary migration, Tested rollback plan |
| Data loss during partition drop | Low | Critical | Dry-run, Pre-drop backup, Soft delete first |
| Performance regression post-index | Medium | Medium | Staging load test, HypoPG for index simulation |
| Secrets leakage via logs | Medium | High | Log redaction, Structured logging, No PII in logs |
| Replication lag causing stale reads | High | Medium | Read-after-write consistency for critical paths, Retry logic |
| Disk full in production | Low | High | Monitoring + alerting, Auto-scaling storage, Archiving policy |
| Team knowledge silo | High | Medium | Pair programming, Documentation, Cross-training sessions |

## RACI Matrix
| Activity | Backend Lead | DevOps | DBA | Security | QA | Tech Lead |
|----------|--------------|--------|-----|----------|----|-----------|
| Secrets Rotation | R | A | C | I | I | I |
| PostgreSQL Hardening | C | R | A | C | I | I |
| Migration Development | R | I | C | I | C | A |
| CI/CD Pipeline | C | R | C | I | C | A |
| Performance Tuning | R | C | A | I | C | I |
| Backup/Restore Test | I | R | A | I | C | I |
| Data Classification | R | I | C | A | I | C |
| Documentation | R | C | C | I | C | A |

*R=Responsible, A=Accountable, C=Consulted, I=Informed*

## Approval & Sign-off
| Role | Name | Signature | Date |
|------|------|-----------|------|
| Backend Tech Lead | | | |
| DevOps Lead | | | |
| DBA / Platform Engineer | | | |
| Security Engineer | | | |
| Engineering Manager | | | |

---
*Note: This is a living document that should be reviewed and updated every sprint. All changes must be made via PR with code review.*