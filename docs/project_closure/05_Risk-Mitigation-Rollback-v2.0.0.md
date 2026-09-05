# BEDAANWAVES v2.0.0 — RISK MITIGATION & PRE-DEPLOYMENT ROLLBACK STRATEGY
## Three Highest Residual Risks — Concrete Mitigation Plans + Step-by-Step Rollback Procedures

**Document ID:** BW-RISK-ROLLBACK-v2.0.0  
**Assumption:** Deployment goes live tomorrow at 06:00 UTC (before US market pre-open).  
**Deployment Window:** 06:00 UTC – 07:00 UTC (60-minute maintenance window).  
**Rollback Decision Deadline:** 06:30 UTC. After that, we commit to v2.0.0 and roll forward through patching (since market opens at 09:30 ET / 13:30 UTC).  
**Incident Commander (IC):** On-call SRE or Senior DevOps / Project Closure Manager proxy.  
**Classification:** INTERNAL CONFIDENTIAL — DEPLOYMENT TEAM ONLY

---

## RISK REGISTER (TOP 3 RESIDUAL RISKS — PRE-DEPLOYMENT)

| Rank | Risk ID | Short Title | Likelihood (Pre-Mitigation) | Impact (Pre-Mitigation) | Risk Score (L×I) | Likelihood (Post-Mitigation) | Impact (Post-Mitigation) | Residual Risk Score |
|------|---------|-------------|-----------------------------|-------------------------|------------------|------------------------------|-------------------------|---------------------|
| 1 | R-01 | **Database schema migration failure during upgrade — score_history table large (4.2M rows) ALTER TABLE locks production** | Medium (25%) | Critical | 75 / 100 | Low (<5%) | Medium | 15 / 100 |
| 2 | R-02 | **Frontend JWT-breaking change — HS256 key rotation causes 100% active-session logout storm on cutover** | High (80%) | High | 72 / 100 | Medium (30%) | Medium | 30 / 100 |
| 3 | R-03 | **ML Forecast Engine cold-start — serialized LSTM scalers mismatch; forecast endpoint HTTP 500 on first ~20 requests** | Medium (40%) | High | 56 / 100 | Low (<10%) | Low | 9 / 100 |

---

## R-01: Database Schema Migration Failure — DETAILED

### Risk Description
Migrations `0007_20260902_PURGE_ENTITY_NON_NASDAQ.py` and `0008_20260903_ALTER_TABLE_MARKET_SCORE_TREND.py` perform heavy DDL on tables containing 4.2M + 600K rows respectively. A `ALTER TABLE ... ADD COLUMN ...` with default value on PostgreSQL < 14 can trigger a full-table rewrite, acquiring an `ACCESS EXCLUSIVE` lock for minutes. If the migration exceeds the maintenance window (60 min), the deployment times out and the platform stays in v1/v2 schema-mixed state.

### Mitigation Plan (Execute 24 hours BEFORE deployment)
```
CHECKLIST — PRE-MITIGATION R-01 (Execute 2026-09-04 06:00 UTC)
  ☐ 1. Restore latest production pg_dump to staging cluster.
  ☐ 2. Run exact migration path on staging WITH TIMING:
        $ alembic upgrade head 2>&1 | tee staging-migration-timing.log
        → Confirm: Each individual migration < 60 seconds.
        → Confirm: No ACCESS EXCLUSIVE > 30 seconds (pg_locks monitoring query in parallel).
  ☐ 3. Take FINAL pre-deployment base backup:
        $ pg_dump -Fc -Z 9 -U postgres bedaanwaves_db > bedaanwaves-db-v1.0.0-20260904T055000Z-base.dump
        Expected filesize: ~800-1200 MB. Checksum with sha256sum → store in /backups/offline.
  ☐ 4. Confirm PostgreSQL wal_level = replica + archive_command is working.
  ☐ 5. Deploy "read-only mode" middleware switch to backend:
        $ curl -X POST localhost:3000/api/v1/admin/maintenance-mode -d '{"enabled":true}'
        → returns HTTP 503 with Retry-After for all write endpoints.
  ☐ 6. Create 3 additional PostgreSQL REPLICA SLOTs for manual point-in-time recovery (PITR):
        SELECT pg_create_physical_replication_slot('pitr_slot_v1_rollback');
  ☐ 7. Set maintenance_work_mem = 2GB, max_parallel_maintenance_workers = 4 ONLY for this session via alembic template.
```

### Rollback Procedure R-01 (TRIGGER: migration time > 30 min elapsed OR ANY error in alembic output)
```
ROLLBACK R-01 — EXECUTE IN ORDER, ONE STEP AT A TIME.
Total estimated duration: 14 minutes.

STEP 1 (T+0:00 — Incident Commander DECISION & ANNOUNCEMENT)
  • IC announces: "R-01 rollback triggered" on deployment voice channel.
  • IC records rollback start timestamp: ______ UTC.
  • IC opens Rollback Runbook in shared editor; every step gets ✅ or ❌ with real-time.

STEP 2 (T+0:30 — Halt mid-migration, kill DDL if hung)
  • psql into primary: SELECT pid, query FROM pg_stat_activity WHERE state = 'active' ORDER BY query_start;
  • SELECT pg_terminate_backend(<pid_of_alembic_migration>);
  • Run: DROP TABLE IF EXISTS score_history CASCADE;  (this is NEW table — safe to drop)
  • Verify: No ACCESS EXCLUSIVE locks remain on users/portfolios/watchlists tables.

STEP 3 (T+3:00 — Restore v1.0.0 backup to a STAGING PARALLEL DB first)
  • createdb -T template0 bedaanwaves_db_rollback_preview ENCODING 'UTF8' LC_COLLATE 'English_US';
  • time pg_restore -j 4 -d bedaanwaves_db_rollback_preview -U postgres bedaanwaves-db-v1.0.0-20260904T055000Z-base.dump
  • EXPECTED: Restore completes in < 11 minutes (8 cores, NVMe).
  • While restore runs: STEP 4 runs in parallel.

STEP 4 (T+3:00 parallel — Swap backend to v1.0.0 source tree)
  • cd E:\BedaanWaves\src\backend
  • git stash (to drop any v2.0 local changes if uncommitted on box)
  • git checkout v1.0.0  (commit hash 0a1b2c3... — verify: git rev-parse HEAD → 0a1b2c3)
  • pip install -r requirements.txt  # Ensures all v1 dep versions match exactly (notably sqlalchemy<2.0 strict)
  • Validate: python -c "import app; print(app.__version__)" → 1.0.0
  • Rollback env variable DATABASE_URL → DB_URL (v1 naming):
        .env: Comment out DATABASE_URL, uncomment old DB_URL line
  • Restart backend service: nssm restart BW-Backend-v1  (or systemctl restart bedaanwaves-backend)

STEP 5 (T+5:00 — Swap frontend to v1.0.0 build)
  • cd E:\BedaanWaves\src\frontend
  • git checkout v1.0.0
  • Verify package.json version: "version": "1.0.0"
  • NEXT_TELEMETRY_DISABLED=1 npm run build  (expect 90-120 seconds)
  • nssm restart BW-Frontend-v1  (or systemctl restart bedaanwaves-frontend)

STEP 6 (T+11:00 — Restore production DB from v1.0.0 backup)
  • First, sanity-check rollback_preview DB: psql -d bedaanwaves_db_rollback_preview -c "SELECT COUNT(*) FROM users; SELECT COUNT(*) FROM assets;" → non-zero counts.
  • Put platform into OFFLINE splash: (frontend already shows maintenance)
  • Terminate ALL connections to production:
        psql -U postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'bedaanwaves_db' AND pid <> pg_backend_pid();"
  • DROP DATABASE bedaanwaves_db WITH (FORCE);
  • CREATE DATABASE bedaanwaves_db WITH ENCODING = 'UTF8' LC_COLLATE = 'English_US' ... template0;
  • time pg_restore -j 4 -d bedaanwaves_db -U postgres bedaanwaves-db-v1.0.0-20260904T055000Z-base.dump
  • EXPECTED: < 11 minutes (same as staging)
  • Run ANALYZE on all tables: psql -d bedaanwaves_db -c "ANALYZE VERBOSE;" (~1 min)

STEP 7 (T+13:00 — Smoke-test platform on v1.0.0)
  • curl http://localhost:3000/api/v1/health → status: "healthy", version: "1.0.0"
  • Login via Playwright test run: npx playwright test e2e/auth.spec.ts --project=chromium → 8/8 pass
  • Browse dashboard, ranking, AAPL detail → confirm v1 UI (no forecast, no comparison tabs)
  • Disable maintenance-mode middleware: curl -X POST /api/v1/admin/maintenance-mode -d '{"enabled":false}'

STEP 8 (T+14:00 — CLOSE ROLLBACK)
  • IC announces "Rollback R-01 complete"
  • IC records rollback end timestamp: ______ UTC. Total duration: ______ minutes.
  • Generate post-mortem template in JIRA/Linear; assign DBA + Backend Tech Lead.
  • Communicate to stakeholders: "Deployment rolled back — root cause analysis within 48 hours; v2 rescheduled no earlier than +7 business days."
```

---

## R-02: JWT Breaking Change — Session Logout Storm

### Risk Description
v2.0.0 rotates JWT signing algorithm RS256 → HS256 and re-keys with a fresh `JWT_SECRET`. Every v1-issued access token and refresh token becomes invalid at the moment backend v2 boots. If 400+ active users send their stale tokens within 30 seconds after cutover, it triggers a Redis-auth-event thundering herd. Additionally, any frontend tab that was idle overnight sends a burst of 401s.

### Mitigation Plan (Execute during Deployment Window)
```
CHECKLIST — PRE-MITIGATION R-02 (Day-of-deployment, before backend swap)
  ☐ 1. Dual-token acceptance window on v2 backend for first 30 minutes only:
        Patch app/core/config.py get_settings() with TEMPORARY compatibility:
          def legacy_verify(token):
              # Accept v1 RS256 tokens signed by OLD public key for 30 minutes.
              # Return (username, user_id, exp) or None.
        → In JWT dependency: try HS256(v2) first; on JWTError fall back to legacy_verify.
        → ENVIRONMENT variable: V2_LEGACY_JWT_ACCEPT_UNTIL = <epoch + 1800s>
  ☐ 2. Frontend deploy a 30-second "logout splash" on uncaught 401.
        In axios response interceptor:
          if (401 && location.pathname !== '/login') {
            // Instead of throwing user to /login instantly, show:
            // "We upgraded the platform. You will be re-signed in automatically."
            // Then silently POST /auth/refresh using v2 refresh token from cookie fallback below.
          }
  ☐ 3. Rate-limit on /auth/login + /auth/refresh temporarily relaxed for cutover window:
        RATE_LIMIT_REQUESTS_PER_MINUTE = 400 (for 10 minutes only, then revert to 100)
  ☐ 4. Pre-warm Redis token-revocation cache with v1 token blacklist (bulk SETEX batch 4096 bytes pipelined).
  ☐ 5. CDN / reverse proxy sends "Cache-Control: no-store" on /login route to avoid 301 caching that would lock users out.
```

### Rollback Procedure R-02 (TRIGGER: > 5% of hourly login HTTP 5xx rate, OR login error rate > 15% sustained 60 seconds)
```
ROLLBACK R-02 — JWT — TOTAL ESTIMATED DURATION: 9 minutes.

STEP 1 (T+0:00 — Decision)
  • IC calls: "R-02 rollback triggered — JWT auth failure storm."
  • Slack/Teams message to all users via status page banner:
    "We are experiencing intermittent sign-in issues due to a security key rotation. Platform remains in read-only mode for logged-in users. We will restore in ~9 minutes. Thank you for your patience."

STEP 2 (T+1:00 — Revert JWT signing back to RS256 + v1 secret)
  • cd E:\BedaanWaves\src\backend
  • git stash drop (if any)
  • git checkout v1.0.0 -- app/core/config.py  # Restores v1 JWT_ALGORITHM=RS256 + JWT_PUBLIC_KEY/JWT_PRIVATE_KEY
  • ALSO revert .env variables:
        comment out v2 JWT_SECRET; uncomment v1 JWT_PUBLIC_KEY_PATH + JWT_PRIVATE_KEY_PATH
  • Restart backend service. Wait 10 seconds for workers.
  • curl -X POST /api/v1/auth/login -u test_user1:known_password → expect 200 OK with token

STEP 3 (T+4:00 — Revert frontend axios interceptor to v1 behavior)
  • cd frontend
  • git checkout v1.0.0 -- src/lib/api.ts  # Removes v2 401 auto-refresh splash
  • (Faster alternative — push out a hotfix static JSON to CDN with v1 auth config)

STEP 4 (T+5:00 — Invalidate any v2 tokens already issued in the 5-min window)
  • redis-cli KEYS "jwt:access:*" | xargs redis-cli DEL   (bulk delete v2 issued tokens from revocation cache)
  • Refresh tokens rotation table v2 rows → set revoked=true WHERE issued_at > v2 deploy_start_ts

STEP 5 (T+7:00 — Scale-out if needed)
  • If Redis auth-load looks > 80%, run:
        uvicorn app.main:app --workers 8 (increase from 4 temporarily)

STEP 6 (T+8:30 — Validate)
  • Playwright auth.spec.ts 8/8 pass
  • Grafana dashboard login 5xx error rate < 0.1% sustained for 60 seconds
  • Frontend smoke: dashboard, ranking, AAPL page all load.

STEP 7 (T+9:00 — Close)
  • IC announces "R-02 rollback complete"; remove status page banner.
  • Post-mortem: Investigate root cause — was legacy_verify TTL feature incomplete when deploy went out?
  • Communication: Email blast to all users acknowledging issue + apology.
```

---

## R-03: ML Forecast Engine Cold-Start Scaler Mismatch

### Risk Description
The LSTM model at `assets/models/scalers/aapl_lstm_std_scaler_v2.joblib` was serialized on a developer machine with a scikit-learn 1.4.2dev build, while v2.0.0 ships scikit-learn==1.3.2 (exact pin for production stability). Joblib unpickles the scaler successfully (no ImportError), but `.transform()` silently produces NaN columns → NaN propagates through forecast series → HTTP 500 for first ~20 forecast requests of the day until model-warmup routine catches it.

### Mitigation Plan (Execute 12 hours BEFORE deployment via smoke tests)
```
CHECKLIST — PRE-MITIGATION R-03 (Execute 2026-09-04 18:00 UTC)
  ☐ 1. Re-generate ALL scalers and model artifacts with EXACT scikit-learn==1.3.2 in a clean venv:
        $ cd backend
        $ .\venv\Scripts\Activate.ps1
        $ pip install --force-reinstall scikit-learn==1.3.2 joblib==1.3.2
        $ python -c "import sklearn; print(sklearn.__version__)"  → MUST BE: 1.3.2
        $ python scripts/shared/retrain_scalers_production.py  # re-fits all per-symbol scalers on 2y lookback
  ☐ 2. Compute SHA-256 of regenerated scalers:
        sha256sum assets/models/scalers/*.joblib > /tmp/scaler-sha256sums-after.txt
        Compare with /tmp/scaler-sha256sums-before.txt → expect: at least 40% of hashes change
  ☐ 3. Run forecast warm-up test suite against staging (not production) — 30 requests × 7 symbols × 3 horizons:
        python tests/integration/test_forecast_engine_coldstart.py
        → Expected: 630/630 HTTP 200, 0 NaN in any series[*].forecast_usd field
  ☐ 4. Add defensive middleware: forecast route pre-checks scaler version tag before inference:
        scaler_meta = joblib.load(scaler_path).metadata  # Add sklearn_version field to artifacts
        if scaler_meta['sklearn_version'] != sklearn.__version__: raise HTTP_503_FORECAST_WARMUP_REQUIRED
  ☐ 5. Add a "Forecast Engine Warmup" POST endpoint (ADMIN only):
        curl -X POST /admin/forecast/warmup -d '{"symbols":["AAPL","MSFT","NVDA","GOOGL","AMZN","META","TSLA"],"horizons":["1d","7d","14d"],"model":"ensemble"}'
        → Kicks off 21 inference calls on deployment startup, guarantees warmed cache before users login.
```

### Rollback Procedure R-03 (TRIGGER: Forecast endpoint HTTP 5xx rate > 2% for 30 consecutive seconds)
```
ROLLBACK R-03 — ML SCALER — TOTAL ESTIMATED DURATION: 6 minutes.

STEP 1 (T+0:00 — Decision + Feature Flag)
  • IC calls: "R-03 triggered - Forecast endpoint 5xx rate > 2%".
  • First action — DISABLE FORECAST FEATURE via env (no code deploy needed):
        backend .env: ENABLE_FORECASTING=False
        Restart backend service (fast hot-reload of uvicorn workers: ~8 seconds)
        curl /health → forecast_engine_component: degraded (OK — expected)
        Frontend detects via config endpoint: hides "Forecast" tab + returns "Feature temporarily unavailable" message inline (instead of 500).

STEP 2 (T+1:00 — Rollback scaler artifacts ONLY — keep code at v2.0.0)
  • Restore v1.0.0-compatible scalers:
        cd E:\BedaanWaves\assets\models\scalers
        git checkout v1.0.0 -- .
  • VALIDATE (critical before re-enable):
        python -c "
        import joblib, sklearn
        s = joblib.load('aapl_lstm_std_scaler_v1.joblib')
        import numpy as np
        out = s.transform(np.random.rand(60, 12))  # 60 lookback x 12 features
        assert np.isnan(out).sum() == 0, 'NaN columns present'
        print('SCALER TRANSFORM OK, shape:', out.shape)
        "
        → Must print: SCALER TRANSFORM OK, shape: (60, 12). If ANY NaN → skip to STEP 4b.

STEP 3 (T+4:00 — Re-enable Forecast + Warmup)
  • .env ENABLE_FORECASTING=True
  • Restart backend
  • Warmup call: curl -X POST /admin/forecast/warmup ... (21 pre-flight requests)
  • Verify: Prometheus bw_forecast_requests_total{status="500"} rate stays 0 / 10s

STEP 4a (T+5:30 — Validate end-to-end)
  • curl -X POST /api/v1/forecast/price -d '{"symbol":"AAPL","model":"ensemble","horizon":"14d"}'
    → HTTP 200, forecast_value_usd present AND numeric AND within 2σ of recent price range.
  • Playwright test subset: 4 critical forecast scenarios pass.

STEP 4b (ALTERNATE FAILURE PATH — If STEP 2 still NaN)
  • IC escalates: "Rollback scalers did not fix NaN columns — Fallback ARIMA-ONLY mode."
  • .env: ENABLE_FORECASTING=True; FORECAST_FORCE_MODEL=arima; DISABLE_LSTM=True
  • Restart backend; warmup calls → ARIMA path uses no scikit-learn scalers (statmodels tsa model).
  • Verify curl /forecast/price AAPL 14d ARIMA → 200 OK with sane values.
  • Communicate to users: "Deep-learning forecasts temporarily disabled; statistical forecasts available."
  • LSTM scaler rebuild scheduled offline for next-day patch release v2.0.1.

STEP 5 (T+6:00 — Close)
  • IC closes rollback.
  • Post-mortem: Fix MLOps pipeline to re-generate scalers in the CI build container (not dev machines) and reject deployment if scaler_sklearn_version != runtime_sklearn_version (gate in §2.1 QA suites for v2.0.1).
```

---

## CROSS-CUTTING ROLLBACK GUARANTEES (APPLY TO ALL 3 ROLLBACKS)

| # | Rollback Step | Why It Exists | Validation |
|---|---------------|---------------|------------|
| G-1 | **Pre-deployment backup mandatory, staging-restored BEFORE production swap** | Guarantees rollback path exists in tested state, not just on paper | Snapshot of staging post-restore SELECT counts match prod pre-deploy counts within transactional delta |
| G-2 | **"Feature flag off" ALWAYS precedes "code rollback"** | 80% of rollbacks can be resolved by a 10-second flag toggle — no user session disruption | Feature-flag change > rollback-code in the runbook order for every risk |
| G-3 | **Two-person rule on destructive DB steps** | DROP DATABASE, `DELETE * FROM ...` — must have second pair of eyes type command into shared terminal AND sign off | Audit log records both usernames + timestamp |
| G-4 | **Automatic rollback on timeout** | If deployment steps > 60% elapsed window and haven't reached "health check 100% green" milestone → IC auto-triggers rollback | Project Closure Manager enforces the 60% rule in every deployment playbook |
| G-5 | **Rollback smoke-test = Playwright auth.spec.ts FULL run** | No "works on my machine" — 8 scenarios in auth.spec.ts must pass before platform is reopened to users | Result file: tests/e2e/playwright-report-rollback.html archived for audit |
| G-6 | **Post-rollback communication SLA** | Stakeholders get public status-page update within 5 minutes of rollback decision; customers get email within 30 minutes; internal RCA within 48 hours | Status page updated at 5-min intervals during active incident |

---

*Document ID: BW-RISK-ROLLBACK-v2.0.0 | Rollback Owner: Project Closure Manager / Incident Commander | Go-live Date Assumed: 2026-09-06T06:00:00Z*
