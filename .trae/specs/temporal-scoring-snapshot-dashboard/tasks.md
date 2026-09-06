# Temporal Scoring Snapshot & Dashboard Data Consistency - Implementation Tasks

Each task maps to at least one Acceptance Criterion in `spec.md`. All tasks include Test Requirements (TRs) typed as `rule` or `rubric`.

Status legend: `pending → in_progress → completed | cancelled | blocked`

---

## Task 1: ScoringSnapshot Schema Migration (Tier + Effective_at)

**Priority:** high
**Depends on:** (none)
**AC Coverage:** AC4

**Description:**
Extend the existing `ScoringSnapshot` model (and DB table) to support hourly vs. daily tiers with precise `effective_at` timestamps, plus a unique composite key that ensures idempotent writes. Add an Alembic migration that (a) adds the two new columns non-destructively (nullable first → backfill → non-null), (b) adds the unique composite index, and (c) backfills existing rows with `snapshot_tier='daily'` and `effective_at = date::timestamptz`.

**Files to modify/create:**
- `backend/app/models/scoring_snapshot.py` — add `snapshot_tier` enum column, `effective_at` column, unique constraint table args, `__table_args__` update.
- `backend/database/alembic/versions/YYYYMMDD_add_snapshot_tier_and_effective_at.py` — new migration with safe for upgrade + downgrade.

**Implementation steps:**
1. Add `SnapshotTier` enum (`daily`, `hourly`) Enum in `scoring_snapshot.py` alongside existing `SnapshotLevel`.
2. Add columns: `snapshot_tier` (Enum, default daily, eventually non-null) and `effective_at` (DateTime(timezone=True), nullable initially)).
3. Add unique constraint `uq_snapshot_asset_tier_effective` over `(asset_id, snapshot_tier, effective_at)` with `postgresql_include` if useful).
4. Write migration as two-phase (add-nullable → backfill → set non-null).
5. Verify: `alembic upgrade head` succeeds on fresh DB copy.

### Test Requirements
- **TR1.1 (rule):** Applying the migration on an empty DB (seed baseline) succeeds without exceptions, `information_schema` shows both columns and unique index present.
- **TR1.2 (rule):** Applying the migration on a DB pre-populated with 1000 legacy `ScoringSnapshot` rows (daily-only) results in every row having `snapshot_tier='daily'` and `effective_at` equal to its `date` at 00:00 UTC.
- **TR1.3 (rule):** Attempting to INSERT two rows with identical `(asset_id, tier, effective_at)` raises `IntegrityError` (unique constraint works).

### Completion Evidence
- Migration applied successfully on dev DB; `SELECT count(*) FROM scoring_snapshots` backfilled; unit test enforcing unique constraint on double-insert passes.

---

## Task 2: TemporalSnapshotService — Three-Tier Composer (Backend)

**Priority:** high
**Depends on:** Task 1
**AC Coverage:** AC1, AC2, part of AC10

**Description:**
Create a new `TemporalSnapshotService` (under `backend/app/services/analysis/`) that knows how to:
- Resolve the three temporal roots of trust: `daily` (latest 00:00 UTC tier), `hourly` (latest top-of-hour tier), `current` (freshest available — either latest hourly if <5m old else on-the-fly mini-recompute per FR open question).
- Compose the unified snapshot payload from `ScoringSnapshot` rows + `ScoreHistory`, coefficient/weight history, market-vs-symbol breakdown.
- Persist the full snapshot JSON into Redis cache with `snapshot:{id}` key.
- Accept optional `symbol` filter to produce per-symbol view.
- Enumerate past 168h + 365d snapshots via `GET /analysis/dashboard/snapshots`.

**Files to modify/create:**
- `backend/app/services/analysis/temporal_snapshot_service.py` — new service.
- `backend/app/api/routes/analysis.py` or a new router file (register new endpoints.
- `backend/app/schemas/dashboard.py` — new Pydantic schemas for snapshot response.

**Implementation steps:**
1. Define Pydantic schemas matching FR1 payload (`SnapshotResponse`, `SnapshotDeltas`, `HierarchyScores`, `WeightSnapshot`, etc.).
2. Implement `TemporalSnapshotService.get_market_snapshot(window_daily, window_intraday, symbol?, snapshotId?)`.
3. Implement `resolve_tier_roots()` helper that queries latest `ScoringSnapshot` rows per tier + optional mini current-tie recompute.
4. Implement weight/coefficient composition from existing coefficient tables.
5. Implement trend composition by query helpers.
6. Implement snapshot enumeration endpoint.
7. Register new endpoints in the FastAPI app.
8. Wire Redis cache read-through.

### Test Requirements
- **TR2.1 (rule):** Calling `get_market_snapshot()` on a populated dev DB returns 3-tier payload with `scores.daily.overall`, `hourly.overall`, `current.overall` all numeric 0–100 and deltas computed correctly (current − daily).
- **TR2.2 (rule):** `resolve_tier_roots()` on repeated calls for same `(asset_id, tier, effective_at)` produce the same byte-identical response; cache hit returns ≤100 ms later.
- **TR2.3 (rule):** snapshot enumeration returns correct array with last 24h hourly + 30d daily.

### Completion Evidence
- pytest `test_temporal_snapshot_service.py` tests pass; API manual `curl /analysis/dashboard/snapshot` returns payload matching schema.

---

## Task 3: Scheduler Jobs — 5m Fast Indicators + Hourly Scoring + Daily Coefficient Snapshots

**Priority:** high
**Depends on:** Task 1, Task 2
**AC Coverage:** AC3, AC10

**Description:**
Register and implement the four new/upgraded scheduler jobs in `SchedulerService._register_default_jobs`:

- `FastIndicators5m` (300s): RSI/MACD/BB%/Volatility write to MarketDataSnapshot 5m interval.
- `HourlyScoreRecompute` (3600s, aligned to top-of-hour effective_at): full hierarchy 4-level score compute, write `tier=hourly`.
- Upgrade `DailyScoreRecalculation`: explicitly writes tier=daily, 00:00 UTC effective_at.
- `CoefficientSnapshotDaily` (00:10 UTC): daily weight snapshot persisted to coefficient history or weight table.

All jobs idempotent via unique constraint; each job logs structured `written_rows`, `duration_ms`, `skip_reason`.

**Files to modify/create:**
- `backend/app/services/system/scheduler_service.py` — register 4 jobs + job-runner idempotency guard.
- `backend/app/services/data/market_data_processing.py` (or equivalent): `FastIndicators5m` worker.
- `backend/app/services/analysis/score_history_pipeline.py` — add hourly writer mode.

**Implementation steps:**
1. Implement a generic `@idempotent_job(tier, effective_at_resolver)` decorator/helper that checks the unique-constraint row existence before starting work → returns `skip_reason='already_computed'` if present.
2. Implement `FastIndicators5m` job: fetch latest 1m/5m bars per active NASDAQ asset, compute indicators, write `MarketDataSnapshot interval='5m'`.
3. Implement `HourlyScoreRecompute` job: call into scoring engine, write `ScoringSnapshot` rows with `tier=hourly, effective_at=floor_1h(now UTC)`.
4. Upgrade daily scoring to write tier=daily effective_at=00:00 UTC.
5. Implement coefficient-snapshot job.
6. Add structured start/end logs with counts/duration.

### Test Requirements
- **TR3.1 (rule):** Trigger `HourlyScoreRecompute` twice for same hour → first run written_rows=N > 0 → second run: `written_rows=0, skip_reason=already_computed` → no IntegrityError thrown anywhere.
- **TR3.2 (rule):** Scheduler registration step: after service init, `_jobs` dict contains keys: `FastIndicators5m`, `HourlyScoreRecompute`, `DailyScoreRecalculation`, `CoefficientSnapshotDaily` with correct intervals (300, 3600, 86400, 86400).
- **TR3.3 (rule):** Market closed (e.g. weekend invocation → `FastIndicators5m` returns success with skip_reason='market_closed', writes zero rows, no exception.

### Completion Evidence
- pytest: idempotence tests pass; scheduler logs captured and show structured counts after manual job runs.

---

## Task 4: New Unified Snapshot Endpoints + Legacy Endpoint Alignment

**Priority:** high
**Depends on:** Task 2
**AC Coverage:** AC1, AC2, AC9

**Description:**
Implement the new endpoints and ensure legacy endpoints delegate to the snapshot service to prevent drift.

**New endpoints:**
- `GET /analysis/dashboard/snapshot` — FR1 unified payload.
- `GET /analysis/dashboard/snapshots` — enumeration index.
- `GET /analysis/dashboard/snapshot?symbol=AAPL` — per symbol filter.
- `GET /analysis/dashboard/snapshot?snapshotId=<id>` — exact replay.

**Legacy alignment:** Refactor existing `/dashboard/score-trend`, `/dashboard/hierarchical-trend`, `/dashboard/sub-dimension-trend`, `/dashboard/aspect-trend`, `/dashboard/coefficient-history`, `/dashboard/coefficient-history-by-level` to internally call TemporalSnapshotService and return the same numeric values the new unified payload exposes. No new schemas preserved wiret compatibility.

**Files to modify/create:**
- `backend/app/api/routes/dashboard.py` — add new endpoints + refactor legacy ones through TemporalSnapshotService calls.

### Test Requirements
- **TR4.1 (rule):** `/snapshot endpoint 200 OK with JSON matching schema; symbol filter returns per-symbol scores.
- **TR4.2 (rule):** Replay by `snapshotId` returns byte-identical score values to the original snapshotId's persisted values.
- **TR4.3 (rule):** Legacy score-trend series last-point value vs new snapshot trend last-point match within 1e-6.

### Completion Evidence
- pytest parity test showing legacy vs new endpoint value equality; OpenAPI docs visible in swagger.

---

## Task 5: Frontend Snapshot Fetcher + Zustand Integration

**Priority:** high
**Depends on:** Task 4
**AC Coverage:** AC5, AC6

**Description:**
Build the frontend integration layer:
- New `fetchDashboardSnapshot(params)` fetcher in `@/lib/api/dashboard.ts` matching new endpoint.
- `useDateStore` extended with `snapshot`, `setSnapshot()`.
- `SnapshotTimeSlider` component enumerating last 24h+30d snapshots and calling fetcher with snapshotId.
- All old dashboard REST fetches go through the new snapshot path for analytical scores.

**Files to modify/create:**
- `frontend/src/lib/api/dashboard.ts` — add fetcher + types.
- `frontend/src/store/useDateStore.ts` — add snapshot state slice.
- `frontend/src/components/ux/SnapshotTimeSlider.tsx` — new component.
- `frontend/src/components/charts/` — update callers.

### Test Requirements
- **TR5.1 (rule):** `fetchDashboardSnapshot()` returns typed SnapshotResponse shape; TS strict mode compiles without errors.
- **TR5.2 (rule):** After calling `setSnapshot()`, all 6 dimensions are readable from Zustand store snapshot state slice.
- **TR5.3 (rule):** Selecting an entry in the slider re-renders consuming components with the snapshotId payload.

### Completion Evidence
- Vitest tests on fetcher and store state; Storybook or component test for slider.

---

## Task 6: Six Core Parameterized Chart Components + Level/Parent Selectors

**Priority:** medium
**Depends on:** Task 5
**AC Coverage:** AC6

**Description:**
Ship six chart wrappers and the selector components:

1. **SpiderScoreChart(level, parent?)
2. **TrendScoreChart(level, window=daily|intraday, parent?)
3. **DeltaScoreChart(level, window=day|hour, parent?)
4. **WeightCurrentChart(level, parent?)
5. **WeightTrendChart()** — dimension-only
6. **WeightDeltaChart()** — dimension-only

Shared components:
- **LevelSelector** with labels: DIMENSION, SUB-DIMENSION, ASPECT, SUB-ASPECT
- **ParentSelector** — selects a dimension/sub-dimension when level requires a parent.
- **ViewModeToggle** — SIMPLE | EXPERT.

All components use only existing chart components; no icons. All titles/headers are English-only text labels. No lucide-react icons; use SHOW/HIDE instead, + ≡ × etc.

**Files to modify/create:**
- `frontend/src/components/charts/SpiderScoreChart.tsx`
- `frontend/src/components/charts/TrendScoreChart.tsx`
- `frontend/src/components/charts/DeltaScoreChart.tsx`
- `frontend/src/components/charts/WeightCurrentChart.tsx` — wrap existing CoefficientChart.
- `frontend/src/components/charts/WeightTrendChart.tsx`
- `frontend/src/components/charts/WeightDeltaChart.tsx`
- `frontend/src/components/charts/LevelSelector.tsx`, `ParentSelector.tsx`, `ViewModeToggle.tsx`

### Test Requirements
- **TR6.1 (rule):** Each of 6 chart wrappers renders 1 svg/canvas without JS error when fed mocked snapshot.
- **TR6.2 (rule):** Changing LevelSelector from DIMENSION → SUB-DIMENSION → ASPECT → SUB-ASPECT changes the props sent into the wrapped chart (different data arrays).
- **TR6.3 (rule):** EXPERT mode toggle turns on 18 simultaneous chart containers (no JS errors).

### Completion Evidence
- Vitest smoke-test renders; Playwright visual checks of selector-driven re-render behavior.

---

## Task 7: Three-Score ScoreTripleBadge Component + AS OF Tile Stamps

**Priority:** high
**Depends on:** Task 5
**AC Coverage:** AC5, AC12

**Description:**
- New `ScoreTripleBadge` showing PREV DAY / PREV HOUR / CURRENT badges with UP/DOWN/FLAT arrows (text + chars ↑ ↓ →; between tiles include a and arrows and arrow indicators.
- A tiny `AsOfStamp` widget component that renders `AS OF HH:MM UTC on every tile and participates in aria-live region.

**Files to modify/create:**
- `frontend/src/components/shared/ScoreTripleBadge.tsx`, `AsOfStamp.tsx`
- Apply AsOfStamp added inside Card/tile headers of every score-holding widget across dashboard + stock pages.

### Test Requirements
- **TR7.1 (rule):** `ScoreTripleBadge({daily: 71.4, hourly: 72.0, current: 73.8})` renders "PREV DAY 71.4", "PREV HOUR 72.0", "CURRENT 73.8", "↑ +1.8", "↑ +2.4" DOM strings visible (numbers, arrow).
- **TR7.2 (rule):** Every chart/tile header includes AS OF stamp with correct time stamp text; aria-live attribute set on wrapper.
- **TR7.3 (rule):** axe-core zero violations when run on a page containing the badges (no color-only states — UP/DOWN text present).

### Completion Evidence
- axe-core 0 violations; DOM assertions of stamp presence; Vitest render tests.

---

## Task 8: Dashboard General Page Rewrite — Single Snapshot Consumption

**Priority:** high
**Depends on:** Task 5, 6, 7
**AC Coverage:** AC5, AC6, AC7

**Description:**
Refactor `/dashboard?tab=general page (or the page and its shell to issue ONE `fetchDashboardSnapshot()` call on mount + single `setSnapshot()`. All widgets (spider, trend, deltas, movers, weights, stat boxes) pull analytical scores from Zustand. Watchlist and user-private data can be fetched separately. Optional SSE price overlay on prices only.

**Files to modify/create:**
- `frontend/src/app/scoring/page.tsx` or the actual dashboard page shell referenced in the page `frontend/src/components/layout/NewDashboardShell.tsx

### Test Requirements
- **TR8.1 (rule):** Network tab: 1 /analysis/dashboard/snapshot on initial load; no other /analysis/dashboard/* calls except snapshot.
- **TR8.2 (rule):** All tiles show AS OF stamp matching snapshot effectiveAt.
- **TR8.3 (rubric, AC7 ≥3):** Widget parity script (compare top badge overall score vs spider vs trend last point — all ≤ 0.05 diff.

### Completion Evidence
- Playwright dashboard.spec parity assertions pass; network call count assertions; screen recording of mount showing single call then full render.

---

## Task 9: Stock Detail Scoring Page — HISTORICAL / INTRADAY Tabs + Time Slider + Expert Toggle

**Priority:** high
**Depends on:** Task 6, 7, 8
**AC Coverage:** AC6, AC8, AC9

**Description:**
- Rework `frontend/src/app/stocks/[symbol]/scoring/page.tsx with 2 tabs: HISTORICAL / INTRADAY.
- Add snapshot time slider on both tabs; default tab remembered in localStorage.
- Add EXPERT/SIMPLE toggle; show 6 components (SIMPLE) or 18-expanded (EXPERT).

**Files to modify/create:**
- `frontend/src/app/stocks/[symbol]/scoring/page.tsx` — layout wrapper with tab state.

### Test Requirements
- **TR9.1 (rule):** HISTORICAL tab active; click INTRADAY → window selector 6H/24H/7D visible; three-score badges above charts; X-axis hourly ticks.
- **TR9.2 (rule):** Switch symbol → tab state persists (localStorage read returns same tab).
- **TR9.3 (rule):** Time-slider pick past snapshot → spider re-renders; header shows SNAPSHOT: YYYY-MM-DD HH:MM UTC; return LIVE clears banner.

### Completion Evidence
- Playwright state traversal passes; DOM axis labels correct; banner on-history banner text.

---

## Task 10: Backend + Frontend E2E + Perf + Accessibility Test Suites

**Priority:** medium
**Depends on:** All tasks 1–9
**AC Coverage:** AC11, AC12

**Description:**
- pytest perf tests for NFR1 (snapshot P95 ≤ 2s / 600ms / 100ms).
- Playwright parity script over 20 symbols (AC7 ≥ 3).
- axe-core runs (AC12).

**Files to modify/create:**
- Backend tests, frontend tests under tests/api, playwright tests.

### Test Requirements
- **TR10.1 (rubric, AC11 ≥3):** Perf test results meet or exceed NFR1 thresholds.
- **TR10.2 (rule, AC12):** axe-core zero AA violations on 2 key pages.
- **TR10.3 (rubric, AC7 ≥3):** 20-symbol parity pass; ≤0 mismatches.

### Completion Evidence
- Perf report summary, axe-core report, parity script log — all attached as evidence.

---

## Task 11: Documentation + Code Cleanup Pass (English Only / No Icons)

**Priority:** medium
**Depends on:** All prior tasks
**AC Coverage:** (project convention rules)

**Description:**
- Final pass ensuring: all NEW files English-only comments (no Persian), NO new icon-library imports (check package.json + imports), text-only labels where needed.
- Remove any accidental lucide-react or icon-font imports added during dev.
- Check scheduler_service.py no Persian.

**Files to modify/create:**
- Grep audit + fix only where violating.

### Test Requirements
- **TR11.1 (rule):** Grep project for `lucide-react|@heroicons|fa-` → zero hits in added files.
- **TR11.2 (rule):** Grep new files for Persian characters (range check) → zero non-comment Persian.
- **TR11.3 (rule):** package.json unchanged (no new deps).

### Completion Evidence
- Grep logs; package.json diff (empty for deps section); CI diff review.
