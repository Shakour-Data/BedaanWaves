# طرح جامع ارتقای سطح اهمیت (Criticality) وظایف مربوط به پایگاه داده

**پروژه:** BedaanWaves  
**تاریخ:** 2026-07-27  
**نسخه:** 1.0  
**وضعیت:** پیش‌نویس برای بازبینی و تأیید

---

## ۱. مقدمه و اهداف

این سند یک طرح جامع برای ارتقای سطح اهمیت (Criticality) وظایف مربوط به پایگاه داده تدوین کرده است. هدف تضمین پایداری، امنیت، عملکرد و مقیاس‌پذیری داده‌ها در سطح تولید (Production) است.

### ۱.۱ پرینسیپ‌های هدایت‌کننده

| اصل | توضیح |
|------|-------|
| **ACID Compliance** | تمام تراکنش‌های حیاتی باید اتمیک، سازگار، ایزوله و پایدار باشند |
| **Defense in Depth** | لایه‌های امنیتی متعدد: شبکه، دیتابیس، اپلیکیشن، کد |
| **Observability First** | لاگینگ، متریک‌ها، و ردیابی (Tracing) از روز اول |
| **Immutable Infrastructure** | مهاجرتی‌ها (Migrations) غیرقابل‌تغییر، نسخه‌بندی شده، و قابل‌بازگشت |
| **Zero-Downtime Evolution** | تغییرات اسکیمای بدون قطع خدمت (Online DDL، Blue/Green) |
| **Data Governance** | طبقه‌بندی داده‌ها، نگهداری (Retention)، و حذف امن (Purging) |

### ۱.۲ سطح بحرانیت هدف

| سطح | تعریف | مثال |
|------|-------|------|
| **P0 (Critical)** | قطع خدمت کل سیستم، از دست رفتن داده، نقض امنیتی | Migration ناموفق،.inject SQL، خرابی WAL |
| **P1 (High)** | تدهور عملکرد شدید، خطای داده در گزارش‌دهی | N+1 Query، ایندکس گم‌شده، Connection Leak |
| **P2 (Medium)** | بدهی فنی، عدم پ conformance با استانداردها | نام‌گذاری ناسازگار، مستندات گم‌شده |
| **P3 (Low)** | بهینه‌سازی‌های آینده، ویژگی‌های Nice-to-have | Partitioning پیشرفته، Materialized Views |

---

## ۲. فاز ۰: پایه‌سازی امنیتی و عملیات (Security & Ops Foundation) — P0

### ۲.۱ مدیریت رازها و اعتبارنامه‌ها (Secrets Management)

| وظیفه | وضعیت | اولویت | مالک | معیار پذیرش |
|-------|-------|--------|------|-------------|
| چرخش `DATABASE_URL` / رمز دیتابیس | ⬜ انجام نشده | P0 | DevOps | رمز جدید در Vault/Secrets Manager، `.env` به‌روزرسانی شده |
| چرخش `SECRET_KEY` JWT | ⬜ انجام نشده | P0 | Backend | توکن‌های قدیمی منقضی، کاربران لاگ‌اут اجباری |
| چرخش `BRS_API_KEY` | ⬜ انجام نشده | P0 | Data Team | کلید جدید در سرویس برسی، تست اتصال موفق |
| حذف رازها از تاریخچه Git | ⬜ انجام نشده | P0 | DevOps | `git-filter-repo` یا `bfg` اجرا شده، force-push با احتیاط |
| افزودن `trufflehog` / `git-secrets` به CI | ⬜ انجام نشده | P0 | DevOps | Pipeline با خطا متوقف می‌شود اگر راز پیدا شود |

### ۲.۲ سخت‌سازی PostgreSQL (PostgreSQL Hardening)

| وظیفه | توضیح | اولویت | معیار پذیرش |
|-------|---------|--------|-------------|
| فعال‌سازی `sslmode=require` | تمام اتصالات TLS 1.2+ | P0 | `psql "sslmode=require"` موفق |
| غیرفعال‌سازی `trust` authentication | فقط `scram-sha-256` یا `md5` | P0 | `pg_hba.conf` بازبینی شده |
| محدود کردن `listen_addresses` | فقط IPهای مجاز (App servers، Bastion) | P0 | فایروال + `postgresql.conf` |
| تنظیم `password_encryption = scram-sha-256` | هش مدرن رمزها | P0 | `SHOW password_encryption` |
| ایجاد Roleهای به تفکیک: `app_readonly`، `app_readwrite`، `migration_runner`، `admin` | اصل کمینه‌امتیاز (Least Privilege) | P0 | `GRANT` دقیق روی اسکیماها |
| فعال‌سازی `log_statement = 'ddl'` + `log_min_duration_statement = 1000` | ردیابی کوئری‌های کند و DDL | P0 | لاگ‌های `pg_log` بررسی شده |
| تنظیم `shared_preload_libraries = 'pg_stat_statements, auto_explain'` | مانیتورینگ کوئری | P1 | Extensionها فعال |

### ۲.۳ پشتیبان‌گیری و بازیابی (Backup & Recovery)

| وظیفه | ابزار / روش | RPO | RTO | اولویت |
|-------|-------------|-----|-----|--------|
| پشتیبان‌گیری فیزیکی روزانه (Base Backup) | `pg_basebackup` + WAL Archiving | 24h | < 4h | P0 |
| پشتیبان‌گیری منطقی ساعتی (Logical) | `pg_dump --format=custom` | 1h | < 1h | P1 |
| تست بازیابی ماهانه (Fire Drill) | Restore به استیجینگ، چک‌سام داده‌ها | - | - | P0 |
| نگهداری WAL برای PITR | `wal_keep_segments` / `max_slot_wal_keep_size` | 7 days | - | P0 |
| رمزنگاری پشتیبان‌ها | `gpg` یا S3 SSE-KMS | - | - | P0 |

---

## ۳. فاز ۱: معماری داده و اسکیمای استاندارد (Data Architecture & Schema Standards) — P0/P1

### ۳.۱ استانداردهای نام‌گذاری و طراحی (Naming & Design Conventions)

```sql
-- جداول: snake_case، جمع، توصیف‌گر
-- مثال: ir_price_candles, user_preferences, ml_signals

-- ستون‌ها: snake_case، واحد مشخص در نام (اختیاری)
-- مثال: volume_24h_usd, price_irr, timestamp_utc

-- ایندکس‌ها: idx_<table>_<col(s)>
-- محدودیت‌های یکتا: uix_<table>_<col(s)>
-- چک‌ها: chk_<table>_<rule>
-- کلیدهای خارجی: fk_<table>_<ref_table>

-- UUID v4 برای تمام Primary Keys (عمدتاً)
-- BigInteger برای حجم/مبلغ‌های بزرگ
-- NUMERIC(p, s) برای مقادیر مالی (p=20, s=8 برای قیمت)
-- TIMESTAMPTZ برای تمام زمان‌ها (UTC ذخیره، TZ در اپلیکیشن)
-- JSONB برای متادیتا / انعطاف‌پذیر
```

| استاندارد | اعمال شده؟ | اقدام لازم |
|-----------|------------|------------|
| نام‌گذاری جداول/ستونها |  بیشتر | بررسی کامل در Migration بعدی |
| نوع داده مالی (NUMERIC) |  | - |
| TIMESTAMPTZ به جای TIMESTAMP |  برخی TIMESTAMP | Migration تبدیل به TIMESTAMPTZ |
| UUID PK همه جا |  | - |
| Soft Delete Pattern (`deleted_at`) |  بیشتر جداول | افزودن به جداول حساس |
| Audit Columns (`created_by`, `updated_by`) |  | افزودن به مدل پایه (Base Mixin) |

### ۳.۲ مدل پایه و Mixinها (Base Model & Mixins)

```python
# app/db/base_model.py — پیشنهادی
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
    created_by = Column(PG_UUID(as_uuid=True), nullable=True)  # FK به users.id
    updated_by = Column(PG_UUID(as_uuid=True), nullable=True)
```

| کار | وضعیت | اولویت |
|------|-------|--------|
| ایجاد `BaseModel` با Mixinهای بالا | ⬜ | P1 |
| مهاجرت مدل‌های موجود به BaseModel جدید | ⬜ | P1 |
| افزودن `created_by`/`updated_by` به جداول حساس (portfolio, position, order) | ⬜ | P1 |

### ۳.۳ استراتژی پارتیشن‌بندی (Partitioning Strategy)

| جدول | حجم پیش‌بینی‌شده | استراتژی پارتیشن | کلید پارتیشن | اولویت |
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

**نکته:** استفاده از `pg_partman` برای مدیریت خودکار پارتیشن‌ها.

### ۳.۴ استراتژی ایندکس‌گذاری پیشرفته (Advanced Indexing)

| نوع ایندکس | کاربرد | جداول هدف |
|------------|--------|-----------|
| **BRIN** | جداول بسیار بزرگ، داده‌های زمانی (Append-only) | `*_candles`, `*_order_book`, `api_logs` |
| **Partial Index** | فیلترهای متداول (مثل `active=true`, `is_deleted=false`) | `assets`, `portfolios`, `ml_signals` |
| **Covering Index (INCLUDE)** | کوئری‌های Read-Heavy که فقط ستون‌های خاص می‌خوانند | `positions` (portfolio_id, asset_id INCLUDE quantity, current_value) |
| **Expression Index** | جستجوی Case-insensitive، محاسبه‌محور | `assets` (lower(symbol)), `users` (lower(email)) |
| **GIN (JSONB)** | جستجو در متادیتا JSONB | `assets.meta`, `ml_signals.technical_factors`, `alerts.condition` |
| **GIST (tsvector)** | جستجوی متن کامل (Full-text Search) | `news.title`, `news.body` |

---

## ۴. فاز ۲: مهاجرتی‌ها و مدیریت تغییر اسکیمای (Migrations & Schema Evolution) — P0

### ۴.۱ چارچوب مهاجرتی (Migration Framework)

| اصل | اجرا شده؟ | اقدام |
|------|-----------|-------|
| همه تغییرات از طریق Alembic |  | - |
| `alembic revision --autogenerate` برای مدل‌های جدید |  | - |
| **بدون `create_all` در استارتاپ** | ️ در `base.py:65` هست | حذف کامل، فقط `alembic upgrade head` |
| Migrationها **Non-destructive** (بدون DROP COLUMN در P0) | ⬜ | یادداشت در PR Template |
| Migrationهای **Backward Compatible** (Add column nullable، بعد NOT NULL) | ⬜ | استانداردسازی در CONTRIBUTING |
| هر Migration با **Transaction** (Prevent Partial) |  پیش‌فرض Alembic | - |
| **Rollback Plan** در هر PR توصیف شود | ⬜ | قالب PR اضافه شود |

### ۴.۲ خط لوله CI/CD برای دیتابیس (Database CI/CD Pipeline)

```yaml
# .github/workflows/database.yml — پیشنهادی
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

| گیت‌هوک / چک | توضیح | اولویت |
|---------------|--------|--------|
| `pre-commit`: `alembic check` | جلوگیری از commit مدل بدون migration | P1 |
| `CI`: `alembic upgrade head` + Test | تست مهاجرتی روی DB خالی | P0 |
| `CI`: Schema Drift Detection | مقایسه metadata با migrationهای اعمالی | P1 |
| `CD`: Blue/Green Migration | اعمال migration روی standby، سويچ ترافیک | P2 |

---

## ۵. فاز ۳: عملکرد و مقیاس‌پذیری (Performance & Scalability) — P1

### ۵.۱ بهینه‌سازی کوئری و Connection Pooling

| ناحیه | وضعیت کنونی | هدف | ابزار / اقدام |
|--------|-------------|-----|--------------|
| **N+1 Queries** |  در `market.py:139-174` | ۰ N+1 | `selectinload` / `joinedload` / LATERAL JOIN |
| **Connection Pool** | `pool_size=10, max_overflow=20` | تنظیم بر اساس Load Test | `pgbouncer` (Transaction mode) برای Production |
| **Prepared Statements** |  غیرفعال | فعال برای کوئری‌های تکراری | `statement_cache_size` در asyncpg |
| **Read Replicas** |  | Master/Replica برای خواندن | `async_session_maker` جدا برای Read |
| **Query Timeout** |  | `statement_timeout = '30s'` | در `postgresql.conf` و Session-level |

### ۵.۲ کش‌سازی استراتژیک (Caching Strategy)

| لایه | ابزار | TTL | Invalidation | داده‌های هدف |
|------|-------|-----|--------------|--------------|
| **L1: In-Process** | `cachetools.LRU` / `aiocache` | 60s | TTL + Event-driven | Asset metadata, User preferences |
| **L2: Distributed** | Redis Cluster | 5m - 1h | Pub/Sub + Keyspace Notifications | Market data snapshots, ML signals, Screening results |
| **L3: Materialized Views** | PostgreSQL | 1h - 24h | `REFRESH MATERIALIZED VIEW CONCURRENTLY` | Aggregated scores, Sector rankings, Top gainers/losers |

### ۵.۳ مانیتورینگ و هشداردهی (Observability & Alerting)

| متریک | آستانه هشدار (Warning) | آستانه بحرانی (Critical) | ابزار |
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

## ۶. فاز ۴: مدیریت داده‌های حساس و انطباق (Data Governance & Compliance) — P1

### ۶.۱ طبقه‌بندی داده‌ها (Data Classification)

| سطح | مثال‌ها | رمزنگاری در حالت استراحت | رمزنگاری در ترانزیت | دسترسی |
|------|---------|------------------------|-------------------|--------|
| **Public** | Asset metadata, Market data |  | TLS | همه |
| **Internal** | ML signals, Screening results |  | TLS | App services |
| **Confidential** | User PII (email, name), Portfolio holdings |  (Column-level) | TLS + mTLS | Need-to-know |
| **Restricted** | Password hashes, Refresh tokens, API keys |  (App-level) | TLS + mTLS | فقط Auth Service |

### ۶.۲ نگهداری و حذف داده‌ها (Retention & Purging)

| جدول / دسته | دوره نگهداری | روش حذف | اولویت |
|-------------|--------------|---------|--------|
| `api_logs` | 90 روز | Partition Drop + `pg_cron` | P1 |
| `audit_logs` | 7 سال (انطباق) | Archive to Cold Storage (S3/Glacier) | P0 |
| `refresh_tokens` | تا انقضا + 30 روز | Background Job | P1 |
| `news` / `news_sentiment` | 2 سال | Partition Drop | P2 |
| `ml_predictions` / `anomalies` | 1 سال | Partition Drop | P2 |
| `price_candles` / `order_book` | 10 سال (تحلیل تاریخی) | Tiered Storage (TimescaleDB / Hypertable) | P3 |

### ۶.۳ انطباق GDPR / قانون حفظ حریم خصوصی ایران

| الزام | پیاده‌سازی | وضعیت |
|--------|-------------|-------|
| حق حذف (Right to Erasure) | Soft Delete + Anonymization Job | ⬜ |
| حق دسترسی (Data Portability) | Export API (JSON/CSV) | ⬜ |
| Minimization | فقط داده‌های لازم جمع‌آوری شود |  بیشتر |
| DPIA (Data Protection Impact Assessment) | مستندسازی برای پردازش‌های پرریسک | ⬜ |

---

## ۷. فاز ۵: ویژگی‌های پیشرفته دیتابیس (Advanced Database Features) — P2/P3

### ۷.۱ TimescaleDB / Hypertables برای داده‌های سری‌زمانی

```sql
-- اگر TimescaleDB در دسترس باشد:
SELECT create_hypertable('crypto_price_candles', 'timestamp', 
    chunk_time_interval => INTERVAL '1 week',
    if_not_exists => TRUE);

-- Compression برای chunkهای قدیمی
ALTER TABLE crypto_price_candles SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'asset_id, timeframe'
);
SELECT add_compression_policy('crypto_price_candles', INTERVAL '30 days');
```

### ۷۲ Materialized Views برای داشبوردها

```sql
-- مثال: Top Gainers/Losers روزانه
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
-- Refresh CONCURRENTLY هر ۱۵ دقیقه در ساعات معاملاتی
```

### ۷.۳ Row Level Security (RLS) برای Multi-Tenancy

```sql
-- فعال‌سازی RLS روی پورتفولیو
ALTER TABLE portfolios ENABLE ROW LEVEL SECURITY;

CREATE POLICY portfolio_isolation ON portfolios
    USING (user_id = current_setting('app.current_user_id')::uuid);

-- در اپلیکیشن: SET LOCAL app.current_user_id = '...';
```

### ۷.۴ Logical Replication برای CDC (Change Data Capture)

| کاربرد | ابزار | جداول هدف |
|--------|-------|-----------|
| Sync به Data Warehouse (ClickHouse/BigQuery) | `pgoutput` + Debezium / Airbyte | `assets`, `ml_signals`, `positions`, `portfolios` |
| Real-time Notifications | `pg_notify` + LISTEN/NOTIFY | `ml_signals`, `alerts`, `notifications` |
| Audit Trail immutable | `pgaudit` + Logical Replication to Append-only store | `audit_logs`, sensitive tables |

---

## ۸. فاز ۶: تست، اعتبارسنجی و تضمین کیفیت (Testing & Quality Assurance) — P1

### ۸.۱ استراتژی تست دیتابیس

| سطح تست | ابزار | پوشش هدف | مثال |
|----------|-------|-----------|------|
| **Unit (Model)** | `pytest` + `sqlalchemy` | ۱۰۰٪ مدل‌ها | Validation constraints, relationships |
| **Integration (Repository)** | `pytest-asyncio` + Testcontainers | ۹۰٪ کوئری‌های پیچیده | Repository methods, complex joins |
| **Migration** | `alembic upgrade/downgrade` | ۱۰۰٪ migrations | Upgrade head, downgrade -1, data integrity |
| **Contract (API)** | `pytest` + `httpx` | ۱۰۰٪ endpoints | Response schema, status codes |
| **Performance (Load)** | `locust` / `k6` | Critical paths | ۱۰۰۰ RPS، p99 < 200ms |
| **Chaos (Resilience)** | `chaostoolkit` / `pg_chaos` | Failure scenarios | Connection loss, replica lag, disk full |

### ۸.۲ داده‌های تست (Test Data Management)

```python
# tests/factories.py — Factory Pattern با factory_boy
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

### ۸.۳ Property-Based Testing برای Constraints

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

## ۹. فاز ۷: مستندات، دانش‌نامه و انتقال دانش (Documentation & Knowledge Transfer) — P2

### ۹.۱ مستندات الزامی

| سند | مخاطب | به‌روزرسانی | وضعیت |
|------|--------|-------------|-------|
| **Data Dictionary** (Excel/Notion) | Dev, QA, BA, Ops | هر Migration | ⬜ |
| **ER Diagram** (dbdiagram.io / Mermaid) | همه | ماهانه | ⬜ |
| **Migration Runbook** | DevOps, SRE | هر Release | ⬜ |
| **Incident Runbook (DB)** | SRE, On-call | ربع‌ساله | ⬜ |
| **Capacity Planning Doc** | Architecture, Ops | دوماهه | ⬜ |
| **Security Hardening Checklist** | Security, DevOps | هر Major Version | ⬜ |

### ۹.۲ Data Dictionary Template

| Table | Column | Type | Nullable | Default | Description | Business Rule | Sensitivity | Retention | Indexes |
|-------|--------|------|----------|---------|-------------|---------------|-------------|-----------|---------|
| assets | symbol | VARCHAR(50) | NO | - | نماد یکتا | Unique, Uppercase | Public | Permanent | PK, UQ, IX |
| portfolios | user_id | UUID | NO | - | مالک پورتفولیو | FK users.id | Confidential | User lifetime | IX, FK |

---

## ۱۰. نقشه‌یول اجرا (Implementation Roadmap)

### ۱۰.۱ اولویت‌بندی و تایم‌لاین

| هفته | فاز | تحویل‌ها (Deliverables) | مالک |
|------|-----|------------------------|------|
| **۱-۲** | ۰ | چرخش تمام رازها، Hardening PostgreSQL، Backup Strategy | DevOps + Backend |
| **۳-۴** | ۱ | BaseModel با Mixinها، Migration تبدیل TIMESTAMPTZ، Soft Delete | Backend |
| **۵-۶** | ۱ | Partitioning جداول بزرگ (pg_partman)، Advanced Indexes | Backend + DBA |
| **۷-۸** | ۲ | CI/CD Pipeline کامل (Migration Check, Schema Drift, Load Test) | DevOps |
| **۹-۱۰** | ۳ | Connection Pooling (PgBouncer)، Read Replicas، Caching Layer (Redis) | Backend + DevOps |
| **۱۱-۱۲** | ۳ | Observability Stack (Prometheus/Grafana/Alertmanager)، Dashboards | DevOps + SRE |
| **۱۳-۱۴** | ۴ | Data Classification، Column-level Encryption، Retention Jobs (pg_cron) | Backend + Security |
| **۱۵-۱۶** | ۵ | TimescaleDB / Hypertables، Materialized Views، RLS | Backend + DBA |
| **۱۷-۱۸** | ۶ | Test Suite کامل (Unit, Integration, Migration, Load, Chaos) | QA + Backend |
| **۱۹-۲۰** | ۷ | مستندات کامل، Data Dictionary، Runbooks، Knowledge Transfer Sessions | Tech Lead + Team |

### ۱۰.۲ معیارهای موفقیت (Success Criteria)

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

## ۱۱. ریسک‌ها و استراتژی کاهش (Risks & Mitigation)

| ریسک | احتمال | تأثیر | استراتژی کاهش |
|------|--------|-------|---------------|
| Migration ناموفق در Production | متوسط | بالا | Blue/Green Deploy، Canary Migration، Rollback Plan تست‌شده |
| از دست رفتن داده در Partition Drop | کم | بحرانی | Dry-run، Backup قبل از Drop، Soft Delete اول |
| Performance Regression پس از Index | متوسط | متوسط | Load Test در Staging، HypoPG برای شبیه‌سازی ایندکس |
| Secrets Leak از طریق Logs | متوسط | بالا | Log Redaction، Structured Logging، No PII in Logs |
| Replication Lag باعث Stale Read | بالا | متوسط | Read-after-write Consistency برایCritical paths، Retry Logic |
| Disk Full در Production | کم | بالا | Monitoring + Alerting، Auto-scaling Storage، Archiving Policy |
| Team Knowledge Silo | بالا | متوسط | Pair Programming، Documentation، Cross-training |

---

## ۱۲. پیوست‌ها

### پیوست الف: چک‌لیست hardened `postgresql.conf`

```ini
# Connection & Security
listen_addresses = '10.0.0.0/8'          # فقط شبکه داخلی
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

### پیوست ب: اسکریپت چک‌لیست Schema Drift

```python
# scripts/check_schema_sync.py
"""مقایسه متادیتای SQLAlchemy با Migrationهای اعمالی"""
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

### پیوست ج: RACI Matrix

| فعالیت | Backend Lead | DevOps | DBA | Security | QA | Tech Lead |
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

## ۱۳. تأیید و امضا

| نقش | نام | امضا | تاریخ |
|------|-----|------|-------|
| Backend Tech Lead | | | |
| DevOps Lead | | | |
| DBA / Platform Engineer | | | |
| Security Engineer | | | |
| Engineering Manager | | | |

---

**نکته:** این سند یک سند زنده (Living Document) است و باید در هر Sprint بازبینی و به‌روزرسانی شود. تمام تغییرات باید از طریق PR با بررسی کد (Code Review) اعمال گردند.
