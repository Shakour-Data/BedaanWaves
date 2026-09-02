# Comprehensive Database Criticality Upgrade Plan

**Project:** BedaanWaves
**Date:** 2026-07-27
**Version:** 1.0
**Status:** Draft for review and approval

---

## 1. Introduction and Objectives

This document outlines a comprehensive plan for upgrading the criticality level of database-related tasks. The goal is to ensure data reliability, security, performance, and scalability in production.

### 1.1 Guiding Principles

| Principle | Description |
|------|-------|
| **ACID Compliance** | All critical transactions must be atomic, consistent, isolated, and durable |
| **Defense in Depth** | Multiple security layers: network, database, application, code |
| **Observability First** | Logging, metrics, and tracing from day one |
| **Immutable Infrastructure** | Migrations are immutable, versioned, and reversible |
| **Zero-Downtime Evolution** | Schema changes without service interruption (Online DDL, Blue/Green) |
| **Data Governance** | Data classification, retention, and secure purging |

### 1.2 Target Criticality Levels

| Level | Definition | Example |
|------|-------|------|
| **P0 (Critical)** | Full system outage, data loss, security breach | Failed migration, SQL injection, WAL corruption |
| **P1 (High)** | Severe performance degradation, data errors in reporting | N+1 queries, missing index, connection leak |
| **P2 (Medium)** | Technical debt, non-conformance with standards | Inconsistent naming, missing documentation |
| **P3 (Low)** | Future optimizations, nice-to-have features | Advanced partitioning, materialized views |

---

## 2. Phase 0: Security and Operations Foundation — P0

### 2.1 Secrets and Credentials Management (Secrets Management)

| Task | Status | Priority | Owner | Acceptance Criteria |
|-------|-------|--------|------|-------------|
| Rotate `DATABASE_URL` / database password | ⬜ Not done | P0 | DevOps | New password in Vault/Secrets Manager, `.env` updated |
| Rotate JWT `SECRET_KEY` | ⬜ Not done | P0 | Backend | Old tokens invalidated, users forced to log out |
| Rotate `BRS_API_KEY` | ⬜ Not done | P0 | Data Team | New key in BRS service, connection test successful |
| Remove secrets from Git history | ⬜ Not done | P0 | DevOps | `git-filter-repo` or `bfg` executed, force-push with caution |
| Add `trufflehog` / `git-secrets` to CI | ⬜ Not done | P0 | DevOps | Pipeline fails if secret is found |

### 2.2 PostgreSQL Hardening

| Task | Description | Priority | Acceptance Criteria |
|-------|---------|--------|-------------|
| Enable `sslmode=require` | All TLS 1.2+ connections | P0 | `psql "sslmode=require"` succeeds |
| Disable `trust` authentication | Only `scram-sha-256` or `md5` | P0 | `pg_hba.conf` reviewed |
| Restrict `listen_addresses` | Only allowed IPs (App servers, Bastion) | P0 | Firewall + `postgresql.conf` |
| Set `password_encryption = scram-sha-256` | Modern password hashing | P0 | `SHOW password_encryption` |
| Create separated roles: `app_readonly`, `app_readwrite`, `migration_runner`, `admin` | Least privilege principle | P0 | Precise `GRANT` on schemas |
| Enable `log_statement = 'ddl'` + `log_min_duration_statement = 1000` | Track slow queries and DDL | P0 | `pg_log` logs reviewed |
| Set `shared_preload_libraries = 'pg_stat_statements, auto_explain'` | Query monitoring | P1 | Extensions enabled |

### 2.3 Backup and Recovery (Backup & Recovery)

| Task | Tool / Method | RPO | RTO | Priority |
|-------|-------------|-----|-----|--------|
| Daily physical base backup | `pg_basebackup` + WAL Archiving | 24h | < 4h | P0 |
| Hourly logical backup | `pg_dump --format=custom` | 1h | < 1h | P1 |
| Monthly restore test (Fire Drill) | Restore to staging, data check | - | - | P0 |
| WAL retention for PITR | `wal_keep_segments` / `max_slot_wal_keep_size` | 7 days | - | P0 |
| Backup encryption | `gpg` or S3 SSE-KMS | - | - | P0 |

---

## 3. Phase 1: Data Architecture and Schema Standards — P0/P1

### 3.1 Naming and Design Conventions (Naming & Design Conventions)

```sql
-- Tables: snake_case, plural, descriptive
-- Example: ir_price_candles, user_preferences, ml_signals

-- Columns: snake_case, explicit unit in name (optional)
-- Example: volume_24h_usd, price_irr, timestamp_utc

-- Indexes: idx_<table>_<col(s)>
-- Unique constraints: uix_<table>_<col(s)>
-- Checks: chk_<table>_<rule>
-- Foreign keys: fk_<table>_<ref_table>

-- UUID v4 for all Primary Keys (mostly)
-- BigInteger for large volumes/amounts
-- NUMERIC(p, s) for financial values (p=20, s=8 for price)
-- TIMESTAMPTZ for all timestamps (UTC stored, TZ in app)
-- JSONB for metadata / flexible data
```

| Standard | Applied? | Required Action |
|-----------|------------|------------|
| Table/column naming | Mostly | Full review in next Migration |
| Financial data type (NUMERIC) |  | - |
| TIMESTAMPTZ instead of TIMESTAMP | Some TIMESTAMP | Migration to TIMESTAMPTZ |
| UUID PK everywhere |  | - |
| Soft Delete Pattern (`deleted_at`) | Most tables | Add to sensitive tables |
| Audit Columns (`created_by`, `updated_by`) |  | Add to base model (Base Mixin) |

### 3.2 Base Model and Mixins (Base Model & Mixins)

```python
# app/db/base_model.py — proposed
from sqlalchemy import Column, DateTime, UUID
from sqlalchemy.orm import declared_attr
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
import uuid
from datetime import datetime, timezone

class TimestampMixin:
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

class SoftDeleteMixin:
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)

    @declared_attr
    def __table_args__(cls):
        return (Index(f'idx_{cls.__tablename__}_soft_delete', 'deleted_at', 'is_deleted'),)

class AuditMixin:
    created_by = Column(PG_UUID(as_uuid=True), nullable=True)  # FK to users.id
    updated_by = Column(PG_UUID(as_uuid=True), nullable=True)
```

| Task | Status | Priority |
|------|-------|--------|
| Create `BaseModel` with above Mixins | ⬜ | P1 |
| Migrate existing models to new BaseModel | ⬜ | P1 |
| Add `created_by`/`updated_by` to sensitive tables (portfolio, position, order) | ⬜ | P1 |

### 3.3 Partitioning Strategy (Partitioning Strategy)

| Table | Estimated Volume | Partition Strategy | Partition Key | Priority |
|-------|-----------------|------------------|---------------|--------|
| `ir_price_candles` | > 100M rows/year | Range (Monthly) | `timestamp` | P1 |
| `intl_price_candles` | > 50M rows/year | Range (Monthly) | `timestamp` | P1 |
| `crypto_price_candles` | > 200M rows/year | Range (Weekly) | `timestamp` | P0 |
| `ir_order_book` | > 50M rows/year | Range (Monthly) | `snapshot_time` | P1 |
| `ir_retail_institutional` | > 30M rows/year | Range (Monthly) | `snapshot_time` | P1 |
| `api_logs` | > 10M rows/month | Range (Daily) | `created_at` | P2 |
| `audit_logs` | > 5M rows/month | Range (Monthly) | `created_at` | P1 |
| `ml_signals` | > 1M rows/month | Range (Monthly) | `generated_at` | P2 |
| `news` / `news_sentiment` | > 10M rows/month | Range (Monthly) | `published_at` / `created_at` | P2 |

**Note:** Use `pg_partman` for automatic partition management.

### 3.4 Advanced Indexing Strategy (Advanced Indexing)

| Index Type | Use Case | Target Tables |
|------------|--------|-----------|
| **BRIN** | Very large tables, time-series data (Append-only) | `*_candles`, `*_order_book`, `api_logs` |
| **Partial Index** | Common filters (like `active=true`, `is_deleted=false`) | `assets`, `portfolios`, `ml_signals` |
| **Covering Index (INCLUDE)** | Read-heavy queries that only read specific columns | `positions` (portfolio_id, asset_id INCLUDE quantity, current_value) |
| **Expression Index** | Case-insensitive search, computation-heavy | `assets` (lower(symbol)), `users` (lower(email)) |
| **GIN (JSONB)** | Search in JSONB metadata | `assets.meta`, `ml_signals.technical_factors`, `alerts.condition` |
| **GIST (tsvector)** | Full-text search | `news.title`, `news.body` |

---

## 4. Phase 2: Migrations and Schema Change Management (Migrations & Schema Evolution) — P0

### 4.1 Migration Framework (Migration Framework)

| Principle | Implemented? | Action |
|------|-----------|-------|
| All changes through Alembic |  | - |
| `alembic revision --autogenerate` for new models |  | - |
| **No `create_all` in startup** | ⚠️ Present in `base.py:65` | Full removal, only `alembic upgrade head` |
| Migrations **Non-destructive** (no DROP COLUMN in P0) | ⬜ | Note in PR Template |
| Migrations **Backward Compatible** (Add column nullable, then NOT NULL) | ⬜ | Standardize in CONTRIBUTING |
| Every Migration with **Transaction** (Prevent Partial) | Alembic default | - |
| **Rollback Plan** described in every PR | ⬜ | Add PR template |

### 4.2 Database CI/CD Pipeline (Database CI/CD Pipeline)

```yaml
# .github/workflows/database.yml — proposed
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
          alembic check  # Exit code 0 if no pending changes
      - name: Run tests with migrated DB
        run: pytest tests/ -x -v

  schema-diff:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Compare models vs migrations
        run: |
          # Custom script to diff SQLAlchemy metadata vs applied migrations
          python scripts/check_schema_sync.py
```

| Git Hook / Check | Description | Priority |
|---------------|--------|--------|
| `pre-commit`: `alembic check` | Prevent committing models without migration | P1 |
| `CI`: `alembic upgrade head` + Test | Migration test on empty DB | P0 |
| `CI`: Schema Drift Detection | Compare metadata with applied migrations | P1 |
| `CD`: Blue/Green Migration | Apply migration on standby, switch traffic | P2 |

---

## 5. Phase 3: Performance and Scalability — P1

### 5.1 Query Optimization and Connection Pooling

| Area | Current Status | Target | Tool / Action |
|--------|-------------|-----|--------------|
| **N+1 Queries** | In `market.py:139-174` | Zero N+1 | `selectinload` / `joinedload` / LATERAL JOIN |
| **Connection Pool** | `pool_size=10, max_overflow=20` | Configure based on Load Test | `pgbouncer` (Transaction mode) for Production |
| **Prepared Statements** | Disabled | Enable for repeated queries | `statement_cache_size` in asyncpg |
| **Read Replicas** |  | Master/Replica for reads | Separate `async_session_maker` for reads |
| **Query Timeout** |  | `statement_timeout = '30s'` | In `postgresql.conf` and Session-level |

### 5.2 Strategic Caching (Caching Strategy)

| Layer | Tool | TTL | Invalidation | Target Data |
|------|-------|-----|--------------|--------------|
| **L1: In-Process** | `cachetools.LRU` / `aiocache` | 60s | TTL + Event-driven | Asset metadata, User preferences |
| **L2: Distributed** | Redis Cluster | 5m - 1h | Pub/Sub + Keyspace Notifications | Market data snapshots, ML signals, Screening results |
| **L3: Materialized Views** | PostgreSQL | 1h - 24h | `REFRESH MATERIALIZED VIEW CONCURRENTLY` | Aggregated scores, Sector rankings, Top gainers/losers |

### 5.3 Monitoring and Alerting (Observability & Alerting)

| Metric | Warning Threshold | Critical Threshold | Tool |
|-------|------------------------|---------------------------|-------|
| `pg_stat_activity` count | > 80% `max_connections` | > 95% | Prometheus + Grafana |
| `pg_stat_database` deadlocks | > 0/min | > 5/min | |
| `pg_stat_statements` mean_time | > 500ms | > 2s | |
| Replication Lag | > 10s | > 60s | |
| WAL Archiving Lag | > 5min | > 30min | |
| Disk Usage | > 70% | > 85% | |
| Backup Age | > 25h | > 48h | |
| `idx_scan / seq_scan` ratio | < 0.9 | < 0.7 | |

---

## 6. Phase 4: Sensitive Data Management and Compliance (Data Governance & Compliance) — P1

### 6.1 Data Classification (Data Classification)

| Level | Examples | Encryption at Rest | Encryption in Transit | Access |
|------|---------|------------------------|-------------------|--------|
| **Public** | Asset metadata, Market data |  | TLS | Everyone |
| **Internal** | ML signals, Screening results |  | TLS | App services |
| **Confidential** | User PII (email, name), Portfolio holdings | (Column-level) | TLS + mTLS | Need-to-know |
| **Restricted** | Password hashes, Refresh tokens, API keys | (App-level) | TLS + mTLS | Auth Service only |

### 6.2 Data Retention and Purging (Retention & Purging)

| Table / Category | Retention Period | Deletion Method | Priority |
|-------------|--------------|---------|--------|
| `api_logs` | 90 days | Partition Drop + `pg_cron` | P1 |
| `audit_logs` | 7 years (compliance) | Archive to Cold Storage (S3/Glacier) | P0 |
| `refresh_tokens` | Until expiration + 30 days | Background Job | P1 |
| `news` / `news_sentiment` | 2 years | Partition Drop | P2 |
| `ml_predictions` / `anomalies` | 1 year | Partition Drop | P2 |
| `price_candles` / `order_book` | 10 years (historical analysis) | Tiered Storage (TimescaleDB / Hypertable) | P3 |

### 6.3 GDPR / Iranian Data Privacy Law Compliance

| Requirement | Implementation | Status |
|--------|-------------|-------|
| Right to Erasure | Soft Delete + Anonymization Job | ⬜ |
| Right to Access (Data Portability) | Export API (JSON/CSV) | ⬜ |
| Minimization | Only necessary data collected | Mostly |
| DPIA (Data Protection Impact Assessment) | Documentation for high-risk processing | ⬜ |

---

## 7. Phase 5: Advanced Database Features — P2/P3

### 7.1 TimescaleDB / Hypertables for Time-Series Data

```sql
-- If TimescaleDB is available:
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

### 7.2 Materialized Views for Dashboards

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
-- Refresh CONCURRENTLY every 15 minutes during trading hours
```

### 7.3 Row Level Security (RLS) for Multi-Tenancy

```sql
-- Enable RLS on portfolio
ALTER TABLE portfolios ENABLE ROW LEVEL SECURITY;

CREATE POLICY portfolio_isolation ON portfolios
    USING (user_id = current_setting('app.current_user_id')::uuid);

-- In application: SET LOCAL app.current_user_id = '...';
```

### 7.4 Logical Replication for CDC (Change Data Capture)

| Use Case | Tool | Target Tables |
|--------|-------|-----------|
| Sync to Data Warehouse (ClickHouse/BigQuery) | `pgoutput` + Debezium / Airbyte | `assets`, `ml_signals`, `positions`, `portfolios` |
| Real-time Notifications | `pg_notify` + LISTEN/NOTIFY | `ml_signals`, `alerts`, `notifications` |
| Immutable Audit Trail | `pgaudit` + Logical Replication to Append-only store | `audit_logs`, sensitive tables |

---

## 8. Phase 6: Testing, Validation, and Quality Assurance — P1

### 8.1 Database Test Strategy

| Test Level | Tool | Target Coverage | Example |
|----------|-------|-----------|------|
| **Unit (Model)** | `pytest` + `sqlalchemy` | 100% models | Validation constraints, relationships |
| **Integration (Repository)** | `pytest-asyncio` + Testcontainers | 90% complex queries | Repository methods, complex joins |
| **Migration** | `alembic upgrade/downgrade` | 100% migrations | Upgrade head, downgrade -1, data integrity |
| **Contract (API)** | `pytest` + `httpx` | 100% endpoints | Response schema, status codes |
| **Performance (Load)** | `locust` / `k6` | Critical paths | 1000 RPS, p99 < 200ms |
| **Chaos (Resilience)** | `chaostoolkit` / `pg_chaos` | Failure scenarios | Connection loss, replica lag, disk full |

### 8.2 Test Data Management (Test Data Management)

```python
# tests/factories.py — Factory Pattern with factory_boy
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

### 8.3 Property-Based Testing for Constraints

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

---

## 9. Phase 7: Documentation, Knowledge Base, and Knowledge Transfer — P2

### 9.1 Required Documentation

| Document | Audience | Update Frequency | Status |
|------|--------|-------------|-------|
| **Data Dictionary** (Excel/Notion) | Dev, QA, BA, Ops | Every Migration | ⬜ |
| **ER Diagram** (dbdiagram.io / Mermaid) | Everyone | Monthly | ⬜ |
| **Migration Runbook** | DevOps, SRE | Every Release | ⬜ |
| **Incident Runbook (DB)** | SRE, On-call | Quarterly | ⬜ |
| **Capacity Planning Doc** | Architecture, Ops | Bi-monthly | ⬜ |
| **Security Hardening Checklist** | Security, DevOps | Every Major Version | ⬜ |

### 9.2 Data Dictionary Template

| Table | Column | Type | Nullable | Default | Description | Business Rule | Sensitivity | Retention | Indexes |
|-------|--------|------|----------|---------|-------------|---------------|-------------|-----------|---------|
| assets | symbol | VARCHAR(50) | NO | - | Unique symbol | Unique, Uppercase | Public | Permanent | PK, UQ, IX |
| portfolios | user_id | UUID | NO | - | Portfolio owner | FK users.id | Confidential | User lifetime | IX, FK |

---

## 10. Implementation Roadmap

### 10.1 Prioritization and Timeline

| Week | Phase | Deliverables | Owner |
|------|-----|------------------------|------|
| **1-2** | 0 | Rotate all secrets, Harden PostgreSQL, Backup Strategy | DevOps + Backend |
| **3-4** | 1 | BaseModel with Mixins, TIMESTAMPTZ Migration, Soft Delete | Backend |
| **5-6** | 1 | Partitioning large tables (pg_partman), Advanced Indexes | Backend + DBA |
| **7-8** | 2 | Full CI/CD Pipeline (Migration Check, Schema Drift, Load Test) | DevOps |
| **9-10** | 3 | Connection Pooling (PgBouncer), Read Replicas, Caching Layer (Redis) | Backend + DevOps |
| **11-12** | 3 | Observability Stack (Prometheus/Grafana/Alertmanager), Dashboards | DevOps + SRE |
| **13-14** | 4 | Data Classification, Column-level Encryption, Retention Jobs (pg_cron) | Backend + Security |
| **15-16** | 5 | TimescaleDB / Hypertables, Materialized Views, RLS | Backend + DBA |
| **17-18** | 6 | Complete Test Suite (Unit, Integration, Migration, Load, Chaos) | QA + Backend |
| **19-20** | 7 | Complete documentation, Data Dictionary, Runbooks, Knowledge Transfer Sessions | Tech Lead + Team |

### 10.2 Success Criteria (Success Criteria)

| KPI | Baseline | Target | Measurement |
|-----|----------|--------|-------------|
| **Migration Success Rate** | ~90% | 100% (Zero failed deploys) | CI/CD Pipeline |
| **Query p99 Latency** | > 500ms | < 100ms (cached), < 200ms (uncached) | pg_stat_statements / APM |
| **Connection Pool Utilization** | N/A | < 70% peak | PgBouncer stats |
| **Backup Restore Test** | Never tested | Monthly, RTO < 4h | Fire Drill Log |
| **Security Findings (DB)** | Unknown | 0 Critical, 0 High | Trivy, pg_audit, Manual Review |
| **Schema Drift Incidents** | Occasional | 0 | CI Check |
| **Test Coverage (DB Layer)** | ~40% | > 90% | Coverage.py |

---

## 11. Risks and Mitigation Strategies (Risks & Mitigation)

| Risk | Probability | Impact | Mitigation Strategy |
|------|--------|-------|---------------|
| Failed migration in Production | Medium | High | Blue/Green Deploy, Canary Migration, tested Rollback Plan |
| Data loss in Partition Drop | Low | Critical | Dry-run, Backup before Drop, Soft Delete first |
| Performance Regression after Index | Medium | Medium | Load Test in Staging, HypoPG for index simulation |
| Secrets Leak via Logs | Medium | High | Log Redaction, Structured Logging, No PII in Logs |
| Replication Lag causing Stale Read | High | Medium | Read-after-write Consistency for critical paths, Retry Logic |
| Disk Full in Production | Low | High | Monitoring + Alerting, Auto-scaling Storage, Archiving Policy |
| Team Knowledge Silo | High | Medium | Pair Programming, Documentation, Cross-training |

---

## 12. Appendices

### Appendix A: Hardened `postgresql.conf` Checklist

```ini
# Connection & Security
listen_addresses = '10.0.0.0/8'          # internal network only
ssl = on
ssl_min_protocol_version = 'TLSv1.2'
password_encryption = scram-sha-256
row_security = on

# Logging & Auditing
log_destination = 'stderr'
logging_collector = on
log_directory = 'pg_log'
log_filename = 'postgresql-%Y-%m-%d.log'
log_statement = 'ddl'
log_min_duration_statement = 1000
log_connections = on
log_disconnections = on
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '

# Performance
shared_buffers = '25%RAM'
effective_cache_size = '75%RAM'
work_mem = '64MB'
maintenance_work_mem = '512MB'
max_parallel_workers_per_gather = 4
max_worker_processes = 8
max_parallel_workers = 8

# WAL & Replication
wal_level = replica
max_wal_senders = 10
wal_keep_size = '2GB'
max_slot_wal_keep_size = '4GB'
archive_mode = on
archive_command = 'cp %p /mnt/wal_archive/%f'

# Autovacuum
autovacuum = on
autovacuum_max_workers = 4
autovacuum_naptime = '30s'
autovacuum_vacuum_threshold = 50
autovacuum_analyze_threshold = 50

# Extensions
shared_preload_libraries = 'pg_stat_statements, auto_explain, pg_partman, pgaudit'
pg_stat_statements.track = 'all'
auto_explain.log_min_duration = '1s'
auto_explain.log_analyze = on
pgaudit.log = 'ddl, role, write'
```

### Appendix B: Schema Drift Checklist Script

```python
# scripts/check_schema_sync.py
"""Compare SQLAlchemy metadata with applied migrations"""
import sys
from sqlalchemy import create_engine, inspect
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.migration import MigrationContext

def check_schema_sync():
    # 1. Get current DB revision
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        context = MigrationContext.configure(conn)
        current_rev = context.get_current_revision()
    
    # 2. Get head revision from migrations
    alembic_cfg = Config("alembic.ini")
    script = ScriptDirectory.from_config(alembic_cfg)
    head_rev = script.get_current_head()
    
    if current_rev != head_rev:
        print(f" SCHEMA DRIFT: DB at {current_rev}, migrations at {head_rev}")
        return 1
    
    # 3. Compare metadata (optional deep check)
    # ...
    print(" Schema in sync")
    return 0

if __name__ == "__main__":
    sys.exit(check_schema_sync())
```

### Appendix C: RACI Matrix

| Activity | Backend Lead | DevOps | DBA | Security | QA | Tech Lead |
|--------|:------------:|:------:|:---:|:--------:|:--:|:---------:|
| Secrets Rotation | R | A | C | I | I | I |
| PostgreSQL Hardening | C | R | A | C | I | I |
| Migration Development | R | I | C | I | C | A |
| CI/CD Pipeline | C | R | C | I | C | A |
| Performance Tuning | R | C | A | I | C | I |
| Backup/Restore Test | I | R | A | I | C | I |
| Data Classification | R | I | C | A | I | C |
| Documentation | R | C | C | I | C | A |

**R=Responsible, A=Accountable, C=Consulted, I=Informed**

---

## 13. Approval and Signatures

| Role | Name | Signature | Date |
|------|-----|------|-------|
| Backend Tech Lead | | | |
| DevOps Lead | | | |
| DBA / Platform Engineer | | | |
| Security Engineer | | | |
| Engineering Manager | | | |

---

**Note:** This document is a living document and should be reviewed and updated every sprint. All changes must be made through PRs with code review.
