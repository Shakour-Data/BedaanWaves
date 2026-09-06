# Temporal Scoring Snapshot & Dashboard Data Consistency - Specification

## Problem

The BedaanWaves NASDAQ platform currently suffers from critical data consistency and temporal granularity gaps:

1. **Dashboard Inconsistency**: Widgets on the General dashboard (`/dashboard?tab=general`) and stock detail pages pull data from independent REST endpoints that query at different times, hit different caches, and aggregate over mismatched time windows (trend charts show "all history" while spider charts show "latest snapshot"). This creates visually contradictory values — the same dimension can render 62 in one card and 74 in another for the same symbol.

2. **24-Hour Staleness**: The only scoring recomputation job registered in `SchedulerService` runs once per day (`DailyScoreRecalculation`, 86400s). For a financial platform with live prices and streaming news, a 24-hour cadence completely misses intraday opportunities, sentiment shocks, and technical breakouts. Users see yesterday's scores while live prices move.

3. **No Unified Snapshot Contract**: No single `snapshotId` ties all dashboard tiles together. There is no mechanism to say "every widget on this page reflects the market state at exactly 14:30 UTC on 2026-09-06." The `ScoringSnapshot` table exists (per asset, per date, per level, per key) but only stores daily-granularity rows with no hourly or intraday tier.

4. **Temporal Chart Gaps**: The frontend supports daily (30/90/365-day) trends via `/score-trend` and `/hierarchical-trend`, but lacks:
   - **Intraday** trend views (6h / 24h / 1w) at 1-hour resolution.
   - Three-score comparison cards (previous day / previous hour / current).
   - Weight/coefficient trend + delta charts at all four hierarchy levels.
   - A coherent "Historical vs. Intraday" tab split on the stock detail page.

5. **Scheduler Misalignment**: `SignalUpdate` runs every 15 min but scoring only every 24h. Price/news ingestion can run every 6h but downstream derived scores never reflect those intermediate inputs. The cadence table promised to the user (1m prices → 5m indicators → 1h scores → 24h weights) does not exist in the current `_register_default_jobs`.

## Users

- **Authenticated Traders / Investors**: Need to trust that spider, trend, bar, weight, and score cards on dashboard/stock pages all describe the same temporal snapshot. Require "previous hour / current / previous day" comparisons and intraday trend lines so they can react to today's moves.
- **Expert / Power Users**: Require all 18 chart types (4 spider × 4 levels, 4 trend lines, 4 delta bars, 2 weight current, 2 weight trend/delta) either through level-selector dropdowns or an Expert Mode toggle.
- **Platform Operators / SRE**: Need the scheduler to actually run hourly scoring + daily weight jobs with auditability (written rows, run duration, skip reason if market closed).
- **QA / Reviewers**: Need deterministic acceptance evidence — given two requests 5s apart with the same `snapshotId`, every API response must return byte-identical numbers.

## Goals

1. **Unified Snapshot Contract**: Introduce a market-wide `snapshotId` (UUID + timestamp tier) so a single API call returns scores, weights, trends, and metadata all keyed to the same temporal anchor. Dashboard widgets consume this one response; no more independent fetches per tile.

2. **Multi-Tier Scoring Cadence**: Implement the four-tier schedule the user specified:
   - **1 min**: Price / volume / last trade (covered by existing live SSE spec; reused here).
   - **5 min**: Fast indicators (RSI, MACD, BB%) persisted to `MarketDataSnapshot` interval="5m".
   - **1 hour**: Full 6D + sub-dimension / aspect / sub-aspect scores recomputed for every active NASDAQ asset and written as `ScoringSnapshot` rows with tier="hourly".
   - **24 hours (00:00 UTC)**: Daily score + coefficient/weight recompute (preserves existing job, but promoted to idempotent daily tier).

3. **Three-Score Reference Frame**: Every stock score card and dashboard summary exposes exactly three scalar scores:
   - `scores.daily` = previous midnight (24h tier) snapshot
   - `scores.hourly` = previous top-of-hour (1h tier) snapshot
   - `scores.current` = most recent snapshot (<5 min old)
   — along with explicit deltas and percent-changes between each pair.

4. **18 Chart Types Delivered**: Ship the chart matrix the user listed:
   - Spider (Radar): dimension / sub-dimension / aspect / sub-aspect (4).
   - Trend (Line): same four levels over a user-selectable window (4).
   - Delta (Bar): same four levels vs. prior reference period (4).
   - Weights Current: dimension / sub-dimension / aspect / sub-aspect via selector (4, rendered through one component with a level dropdown).
   - Weight Trend (Line): per-dimension weight vs. time (1).
   - Weight Delta (Bar): per-dimension weight change vs. prior day (1).
   (The user originally listed 18; the selector pattern collapses 4 weight-current tiles into one configurable component without reducing coverage.)

5. **Dashboard Consistency Hardening**: Rewrite the General dashboard page and stock detail scoring page to fetch ONE unified-snapshot payload on mount, pass the single `snapshotId` through all chart components, and render everything from that single response (plus optional live SSE price overlay that never changes the snapshot's analytical scores).

6. **Scheduler Idempotency + Audit**: Make hourly and daily scoring jobs idempotent — running twice in the same hour must not double-write; a `(asset_id, snapshot_tier, effective_at)` unique key in `ScoringSnapshot` enforces this. Track runs in `scheduler_service` logs with counts written, time elapsed, and skip reason (market closed / already computed / no data).

## Non-Goals

- **No paid real-time feed**: Continue using yfinance as the only provider; do not integrate Polygon, IEX, Finnhub, or any paid key.
- **No new DB engine or Docker work**: Keep PostgreSQL + existing Redis cache; no schema-wide migration strategy change.
- **No ML retraining or stored coefficient refit in this spec**: Coefficients are still read from JSON or existing `coefficient_history` rows; we only snapshot what exists and compute trend/delta from it.
- **No auth / user-preference changes**: Existing JWT middleware and watchlist/alert features are untouched.
- **No icon library additions**: All new UI indicators stay text-only (`LIVE`, `SNAPSHOT 14:00`, `← PREV HOUR`, `↑ +2.4`, etc.).
- **No replacing the realtime-data-streaming spec**: This spec extends it (reuses SSE prices), not supersedes it.

## Functional Requirements

### FR1: Unified Snapshot API (Temporal Root of Trust)

- `GET /analysis/dashboard/snapshot` SHALL return a single response with:
  ```ts
  {
    snapshotId: string;            // UUID
    tier: "current" | "hourly" | "daily";
    effectiveAt: string;           // ISO UTC
    fetchedAt: string;             // ISO UTC
    scores: {
      daily:   HierarchyScores;    // previous midnight
      hourly:  HierarchyScores;    // previous top-of-hour
      current: HierarchyScores;    // freshest available
    };
    deltas: {
      hourly_vs_daily:  DeltaFrame;
      current_vs_hourly: DeltaFrame;
      current_vs_daily:  DeltaFrame;
    };
    weights: WeightSnapshot;       // current weights across 4 levels
    weightTrends: WeightTrendPoint[];
    weightDeltas: WeightDeltaPoint[];
    trends: {
      daily:    TrendPoint[];      // up to 365 days, daily points
      intraday: TrendPoint[];      // up to 7 days, hourly points
    };
    universe: { total: number; market: "NASDAQ" };
  }
  ```
  where `HierarchyScores` contains keys for `overall`, then per `dimension`, per `sub_dimension[parent]`, per `aspect[parent]`, per `sub_aspect[parent]` (all numeric 0–100, with symbol-level breakdown when a `symbol` query param is provided).
- Endpoint supports optional query params:
  - `symbol?` — if present, scores/weights/trends are filtered to that single NASDAQ asset; if absent, returns market-aggregated (median/mean) values.
  - `snapshotId?` — if present, rehydrates that exact historical snapshot; never recomputes. Enables "time slider" to show past spiders on demand.
  - `window_daily=30|90|365` and `window_intraday=6h|24h|7d` control trend series lengths.
- `GET /analysis/dashboard/snapshots` SHALL return a paginated index of the last 168 hourly + 365 daily snapshots so a slider can enumerate options.

### FR2: ScoringSnapshot Table Extended for Hourly Tier

- `ScoringSnapshot` model (currently only `date`) SHALL gain two new columns:
  - `snapshot_tier` — enum `daily | hourly` (nullable default `daily` for existing rows; non-null going forward).
  - `effective_at` — `timestamptz` — the exact UTC moment the snapshot represents (top-of-hour for hourly, 00:00 UTC for daily, latest-run for current).
  - Unique constraint `uq_snapshot_asset_tier_effective` on `(asset_id, snapshot_tier, effective_at)` so re-runs don't double-write.
- A new migration file under `backend/database/alembic/versions/` adds these columns and backfills `snapshot_tier='daily'`, `effective_at = date::timestamptz` for existing rows.

### FR3: Four-Tier Scheduler Jobs (1m → 5m → 1h → 24h)

`SchedulerService._register_default_jobs` SHALL register the following (on top of what already exists):

| Job name | Interval | What it does |
|---|---|---|
| `FastIndicators5m` | 300 s | Runs RSI/MACD/BB%/volatility/momentum over the last 20 1m candles (or 5m candles, whichever available) for every active NASDAQ asset, writes to `MarketDataSnapshot` with `interval='5m'`. Skips if market closed. |
| `HourlyScoreRecompute` | 3600 s | Recomputes full hierarchy (dimension → sub-dimension → aspect → sub-aspect) scores for every active NASDAQ asset. Writes rows with `snapshot_tier='hourly'` and `effective_at = now_floor_1h_utc`. Idempotent via unique key. |
| `DailyScoreRecalculation` (existing, upgraded) | 86400 s + run_at 00:05 UTC | Preserves existing behavior; now explicitly writes `snapshot_tier='daily'`, `effective_at = today_00_utc`. Also writes the day's first (00:00) hourly snapshot as a side effect so hourly_vs_daily comparison always has a pair. |
| `CoefficientSnapshotDaily` | 86400 s (00:10 UTC) | Persists current 4-level weights into a new `weight_snapshots` table or new rows in the existing coefficient history (one row per level, per dimension/subkey). Used by weightTrends + weightDeltas. |

Every job SHALL:
- Emit structured start/end logs with `written_rows`, `skipped_rows`, `duration_ms`, `skip_reason` when applicable.
- Skip cleanly (no exception, success log) when market closed + outside extended hours (use existing `MarketHoursService`).

### FR4: Three-Score Comparison Cards

- **Dashboard Summary tiles**: Three numeric badges (`PREV DAY`, `PREV HOUR`, `CURRENT`) per dimension, plus an arrow indicator (`↑ N.N`, `↓ N.N`, `→ 0.0`) between each pair.
- **Stock detail page**: Same three-badge layout per dimension + overall. Percentages relative to prior reference, not absolute 0–100.
- Badges use text-only indicators (e.g. `PREV DAY 71.4`, `CURRENT 73.8 [↑ +2.4]`) — no icon library.
- When a user drills into one specific level (say `sub_dimension: valuation`), the three-score pattern is preserved for that sub-key too.

### FR5: Eighteen Charts Shipped Via Level-Selector Pattern

The frontend ships **6 core chart components with a level dropdown** that collectively provide all 18 user-listed views. Each is parameterized by `(chartType, level, parentKey?)`:

1. `SpiderScoreChart(level=dimension|sub_dimension|aspect|sub_aspect, parent?)` — current snapshot spider.
2. `TrendScoreChart(level=..., window=daily|intraday, parent?)` — line chart of scores vs. time.
3. `DeltaScoreChart(level=..., window=day|hour, parent?)` — bar chart of `current − prior_day` or `current − prior_hour`.
4. `WeightCurrentChart(level=...)` — doughnut/horizontal bars of current weights at the chosen level.
5. `WeightTrendChart()` — line chart of dimension weights over the last 30/90/365 days.
6. `WeightDeltaChart()` — bar chart of today's dimension weights minus yesterday's.

A `LevelSelector` dropdown + (optionally) `ParentSelector` is rendered next to every multi-level chart. The selector has labels matching canonical dimension names: `DIMENSION`, `SUB-DIMENSION`, `ASPECT`, `SUB-ASPECT`.

**Expert Mode**: A toggle at the top of the stock-detail charts page that, when ON, renders all 6 components simultaneously with all four levels pre-expanded (i.e. 4 spiders stacked, 4 trend lines stacked, 4 delta bars stacked) plus the two weight-specific charts — matching the full 18-tile view the user enumerated. Default = OFF (collapsed 6-chart selector view).

### FR6: Dashboard General Widgets All Consume One snapshotId

On mount, the dashboard page (`/dashboard?tab=general`) SHALL issue exactly ONE fetch:

```ts
const snap = await fetchDashboardSnapshot({ window_daily: 30, window_intraday: "24h" });
```

The returned `snap.snapshotId` is written to Zustand (`useDateStore.setSnapshot(snap)`). Every widget — Spider of dimensions, trend line for the last 24h, current movers list, stat badges, coefficient bars, news sentiment summary — is rendered from the fields of `snap` and never issues an independent REST call for analytical scores. The ONLY additional fetches allowed are (a) user-private data (watchlist, alerts) and (b) optional SSE live-price overlay that mutates only price/change% tiles, never scores.

If a user clicks the 30-day / 90-day / 365-day button on the trend chart, the page issues ONE new `fetchDashboardSnapshot` with the new `window_daily` and re-renders all tiles from the new response (same `snapshotId` family, new trend series only).

### FR7: Historical / Intraday Tab Split on Stock Detail Page

`/stocks/[symbol]/scoring` page SHALL render two top-level tabs:

- **HISTORICAL** (default first visit): window defaults 30 days, trend series daily cadence, spider = daily tier.
- **INTRADAY** (hourly / 6h / 24h / 7d selector): trend series hourly cadence, spider = hourly / current tier, three-score badges (prev day / prev hour / current) are emphasized and placed above the charts.

The tab state is remembered locally so switching symbols retains the user's last tab choice.

### FR8: Snapshot Time-Slider on Spider Charts

Every `SpiderScoreChart` (dashboard + stock pages) SHALL have a compact time slider / dropdown that enumerates the last 24 hourly snapshots + last 30 daily snapshots. Selecting a past entry hydrates the chart via `fetchDashboardSnapshot({ snapshotId })`. A clear one-line indicator shows `SNAPSHOT: 2026-09-06 13:00 UTC` whenever the user is viewing a historical (non-current) spider.

### FR9: Cache Strategy and Stale-Tag Discipline

- Redis cache keys for snapshot data are `snapshot:{id}` (full payload, TTL = snapshot tier lifetime: hourly 2h, daily 30d).
- `fetchDashboardSnapshot` always returns the same bytes for the same `snapshotId`; it is a pure read-through.
- Non-snapshot legacy endpoints (`/analysis/dashboard/score-trend`, etc.) remain for backward compatibility but internally call through to the snapshot service to guarantee the same numbers render. (No drift between legacy and new paths.)
- Any UI tile rendering a score value MUST display a small tag like `AS OF 14:00 UTC` in the tile's top-right (text only) so the user can visually verify all tiles share the same stamp. No tile renders without it.

## Non-Functional Requirements

### NFR1: Snapshot Response Performance

- Market-wide snapshot (no symbol filter, 30d trend) response P95 ≤ 2.0 s under production load.
- Single-symbol snapshot response P95 ≤ 600 ms.
- `snapshotId` replay (cache hit) ≤ 100 ms P95.

### NFR2: Scoring Job Throughput

- `HourlyScoreRecompute` processes the full active NASDAQ universe (current ~3000 active EQUITY/ETF) in ≤ 18 minutes wall-clock on a single node so it reliably finishes before the next hour. If it can't, the batching strategy used in `ScoreHistoryPipeline` (batch_size=100) is applied, with parallelism capped at 4 concurrent DB writers.
- Idempotency guarantee: two concurrent `HourlyScoreRecompute` invocations for the same top-of-hour produce the same written-row counts, no duplicates, no constraint violations.

### NFR3: Correctness / Determinism

- For a given `(asset_id, snapshot_tier, effective_at)`, re-running the scoring pipeline with identical market data inputs MUST produce byte-identical scores (RMS difference across all 4-level scores < 1e-9). Random-seeded ML helper calls are frozen at job start and passed as explicit inputs so runs are reproducible.
- Dashboard widget numeric parity: a `overall_score=73.8` rendered in the top badge MUST equal the spider chart's center value and the trend chart's last point. Any difference ≥ 0.1 between any two representations of the same `(symbol, level, effectiveAt)` is a P0 bug.

### NFR4: Availability / Reliability

- If `HourlyScoreRecompute` fails one hour, the next hour's job MUST still run and write cleanly; failed hours show as gaps in the snapshot index (with `skip_reason: job_failed`) and the three-score UI degrades to `[NO DATA]` for that hour (instead of silently falling back to previous-hour data mislabelled as current).
- Scheduler jobs never crash the service loop; exceptions are captured and logged with traceback, then `error_count` on the job increments.

### NFR5: Security & Access Control

- All snapshot endpoints require valid JWT auth (existing middleware). `symbol`-specific snapshots never leak watchlist/private data; they are pure market-data aggregation responses.
- `snapshotId` values are UUIDv4; they are not guessable. No endpoint accepts a raw SQL date; only `snapshotId` OR canonical window parameters.

### NFR6: Accessibility (WCAG 2.1 Level AA)

- Every chart's three-score badges use text (not color alone) to convey direction: `UP +2.4`, `DOWN -1.1`, `FLAT 0.0`.
- Sliders, dropdowns, and tabs have explicit `aria-label` values.
- The `AS OF` timestamp on every tile is an `aria-live=polite` region so screen readers announce when a new snapshot arrives (including through SSE overlay events, which only update price tiles).

### NFR7: Maintainability / Conventions

- All new code: English-only comments, type-hinted public interfaces (Python `Optional` / Pydantic models; TypeScript strict types), no `Any` in public function signatures.
- Async DB access exclusively through `AsyncSession` with `pool_recycle` respected; no sync DB sessions introduced in scheduler writer paths.
- UI new indicators are 100% text + HTML characters (`↑`, `↓`, `→`, `[`, `]`, `SNAPSHOT`, `LIVE`, `EXPERT`, `HISTORICAL`, `INTRADAY`). Absolutely no lucide-react / icon-library imports added.

## Constraints

- Existing stack preserved exactly: FastAPI, Next.js 16 (App Router), React 19, SQLAlchemy 2.0 AsyncSession, PostgreSQL, Redis, Zustand, Playwright, Vitest, pytest.
- No Docker changes or docker-compose work.
- No Persian/Farsi in code, comments, logs, new UI strings — all new text English LTR.
- No paid data feeds; yfinance remains the provider.
- No icon libraries; text-only UI per project memory rules.
- Score range always 0–100, dimensions always the canonical six: `fundamental`, `technical`, `sentiment`, `risk`, `macro`, `ai`.
- UI typography: Inter font; 8 px design system (multiples of 8 for padding, spacing, radii).

## Dependencies

### Backend
- Reuses existing: `SchedulerService`, `ScoreHistoryPipeline`, `ScoringService` (or `scoring_engine_v2.py` whichever is active), `MarketScoreTrendService`, `CoefficientHistoryService`, `HierarchicalScoreTrendService`, `MarketHoursService`, `MetricsService`.
- New: migration for `ScoringSnapshot` tier + `effective_at`; `snapshotId` generator; a new `TemporalSnapshotService` that orchestrates querying the three tiers (daily/hourly/current) and composing the unified payload.
- Redis: new cache keys `snapshot:{id}` and `snapshot_index:{page}`.

### Frontend
- Reuses existing: `apiClient` (`@/lib/api`), existing chart components (`SpiderChart`, `LineChart`, `BarChart`, `ColumnChart`, `CoefficientChart`), Zustand stores (`useDateStore`, `useLiveStore`), `useSSE` + `useLiveData` hooks from the live-streaming spec.
- New: `fetchDashboardSnapshot` fetcher in `@/lib/api/dashboard.ts`; 6 parameterized chart wrappers; `LevelSelector` + `ParentSelector` dropdowns; three-score `ScoreTripleBadge` component; snapshot slider `SnapshotTimeSlider`; Expert/Simple toggle `ViewModeToggle`; HISTORICAL/INTRADAY tab wrapper.

### Test
- pytest: new `tests/api/test_snapshot_api.py`, `tests/services/test_temporal_snapshot_service.py`, `tests/services/test_hourly_score_job.py`.
- Vitest: new frontend tests for all 6 chart wrappers + `ScoreTripleBadge` + `ViewModeToggle`.
- Playwright: extend dashboard + stock-detail specs with parity-check assertions for three-score badges vs. spider-chart values.

## Assumptions

1. `ScoringService` / `scoring_engine_v2.py` produces numeric 0–100 scores for four levels today; no algorithm changes are needed — only schedule/wrapping changes. If any level (aspect/sub-aspect) is currently partial, we snapshot whatever is produced and mark missing keys with `null` in the API + UI shows `—`.
2. The NASDAQ market schedule (open/close) is accurate enough via existing `MarketHoursService` for job-skip decisions.
3. Redis is reachable (already used by the existing cache infrastructure); if unreachable, the snapshot endpoint falls through to direct DB (degraded perf, still correct).
4. A single server node can run HourlyScoreRecompute for ~3000 assets in <18 minutes. If measured time is longer, we split batching before launch.
5. Acceptance threshold AC7 (parity) is enforced by QA; post-launch any detected drift is a hotfix, not a feature.

## Open Questions

1. **Current-tier freshness**: Should "current" snapshot be recomputed on every `/snapshot` call if the latest is >5 min old, or only on hourly schedule? (Default per user: "less than 5 minutes old" — implies ad-hoc mini-compute path on request if stale.) User input requested if the default is too aggressive.
2. **Expert-mode storage**: Should the Expert/Simple toggle state be persisted to user settings (DB) or only `localStorage`? (Default: `localStorage` v1, user settings v2 if requested.)
3. **Weight snapshot storage**: New `weight_snapshots` table or extend `coefficient_history` rows with `snapshot_tier` + `effective_at`? (Default: extend existing coefficient history to avoid doubling table count; migrate + backfill once.)

---

## Acceptance Criteria

### AC1 — Unified Snapshot API Returns Tiered Scores + Deltas + Weights + Trends
**Type:** rule
**Pass condition:** `GET /analysis/dashboard/snapshot` (no symbol) returns a JSON object with `snapshotId`, `effectiveAt`, `scores.{daily,hourly,current}.overall` all numeric 0–100, `deltas.current_vs_daily.overall` numeric (difference of the two), `weights.dimension` keys exactly the six canonical dims, `trends.{daily,intraday}` both non-empty arrays of points with a monotonic date/timestamp field.
**Evidence source:** `pytest backend/tests/api/test_snapshot_api.py` schema + value assertions.

### AC2 — Same snapshotId → Identical Bytes
**Type:** rule
**Pass condition:** Two consecutive calls to `GET /analysis/dashboard/snapshot?snapshotId=<id>` return byte-identical response bodies (modulo request-id headers). Specifically, every `score`, `delta`, `weight` number is equal within 1e-9.
**Evidence source:** pytest response-bytes comparison test + Redis cache-hit duration measurement ≤ 100 ms.

### AC3 — Hourly + Daily Scoring Jobs Run Idempotently
**Type:** rule
**Pass condition:** Triggering `HourlyScoreRecompute` twice for the same top-of-hour `effective_at` writes the same `ScoringSnapshot` row count in both runs, raises no `IntegrityError`, and the second run logs `written_rows=0` + `skip_reason=already_computed`. Daily job the same for a 00:00 UTC date.
**Evidence source:** pytest `backend/tests/services/test_hourly_score_job.py` idempotence scenario.

### AC4 — ScoringSnapshot Has Tier + Effective_at + Unique Key
**Type:** rule
**Pass condition:** Migration runs cleanly (`alembic upgrade head`) on an empty seed DB + on the existing staging DB. Existing rows have `snapshot_tier='daily'` and `effective_at` populated; new `HourlyScoreRecompute` writes rows with `snapshot_tier='hourly'` and a top-of-hour `effective_at`.
**Evidence source:** `alembic` command output + row-count SQL query asserting `count where tier='hourly' > 0` after one hourly run.

### AC5 — Three-Score Badges Display + Parity With Spider
**Type:** rule
**Pass condition:** On both dashboard and `/stocks/[symbol]/scoring` pages, three numeric badges (PREV DAY / PREV HOUR / CURRENT) are rendered for the overall score and each of the six dimensions. The CURRENT badge value equals the spider chart's center/overall value to within 0.05, and a visible `AS OF HH:MM UTC` text stamp is rendered on every score-holding tile (spot-checked across 10 tiles per page).
**Evidence source:** Playwright `dashboard.spec.ts` + `stock-scoring.spec.ts` DOM attribute and number-parity assertions.

### AC6 — Eighteen Charts Reachable Via Selectors + Expert Toggle
**Type:** rule
**Pass condition:** Manual navigation:
- In **SIMPLE mode**: 6 chart components render, each with a 4-option level dropdown; selecting each level changes the rendered data (4 distinct spider payloads, 4 distinct trend series, 4 distinct delta bars, 4 distinct weight-current views, plus weight-trend + weight-delta = 4+4+4+4+1+1 = 18 distinct data views through selector navigation).
- In **EXPERT mode**: All selector-expanded tiles render simultaneously on the page without scroll-breaks or JS errors; DOM contains 4 spider, 4 trend, 4 delta, 4 weight-current, 1 weight-trend, 1 weight-delta = 18 `<svg>` (or canvas) chart containers.
**Evidence source:** Playwright state toggles + DOM count assertions + screenshot comparison for both modes.

### AC7 — No In-Page Score Drift (Widget Parity)
**Type:** rubric
**Dimension:** Cross-widget numerical parity for the same snapshot, same level, same asset.
**Scale (0–4):**
- 0: Parity not measured; obvious mismatches visible (e.g. 62 in tile, 74 in spider).
- 1: Parity checked for overall score only; 1–2 dimension mismatches exist.
- 2: All 6 dimensions checked on one page (dashboard); 0 mismatches ≥ 0.1, but stock page not checked.
- 3: Dashboard + stock page both checked; overall + 6 dims + 1 sub-dim sample all match within 0.05.
- 4: Dashboard + stock + ranking pages checked; automated Playwright parity script runs over 20 random symbols, 0 mismatches at any level for which data exists.
**Threshold:** ≥ 3
**Evidence source:** Automated parity script run log + failing-case screenshots if any (must be none at threshold 3).

### AC8 — Historical vs. Intraday Tabs Behave as Specified
**Type:** rule
**Pass condition:** `/stocks/AAPL/scoring` page loads → HISTORICAL tab active (30d, daily trend spider = daily tier). Click INTRADAY tab → window selector shows 6H, 24H, 7D; three-score badges render at the top of the chart section; trend chart X-axis shows hourly ticks. Switching symbols (AAPL → MSFT → back to AAPL) preserves the previously-selected tab.
**Evidence source:** Playwright state-traversal test + DOM inspection of axis labels in each tab.

### AC9 — Snapshot Time-Slider Replays Past Spiders
**Type:** rule
**Pass condition:** Spider chart on stock page exposes a `<select>` (or equivalent accessible control) with ≥ 24 past hourly + 30 past daily options. Selecting a 2-hour-old snapshot re-renders the spider with that past snapshot's values; the header shows `SNAPSHOT: YYYY-MM-DD HH:00 UTC`. Choosing the "LIVE" entry restores the current tier spider and removes the historical stamp (shows `AS OF` only).
**Evidence source:** Playwright action → DOM readback + API `?snapshotId=...` call response cross-reference.

### AC10 — Scheduler Jobs Register Correctly + Write Logs
**Type:** rule
**Pass condition:** After app startup, `SchedulerService` logs indicate four new jobs registered: `FastIndicators5m` (300s), `HourlyScoreRecompute` (3600s), upgraded `DailyScoreRecalculation` (86400s with 00:05 run hint), `CoefficientSnapshotDaily` (86400s with 00:10 run hint). Triggering each (via test hook) produces structured start/end logs with `written_rows` and `duration_ms` fields.
**Evidence source:** pytest `backend/tests/test_scheduler_service.py` — register + trigger assertions + log capture parsing.

### AC11 — Performance Within NFR1 Targets
**Type:** rubric
**Dimension:** Snapshot API latency under real load.
**Scale (0–4):**
- 0: No perf test; unmeasured.
- 1: Basic timing only; market-wide > 5 s common.
- 2: Market-wide ≤ 3.0 s, symbol ≤ 1 s (fails 2.0 / 0.6 target).
- 3: Market-wide ≤ 2.0 s P95, symbol ≤ 0.6 s P95; snapshotId cache-hit ≤ 150 ms.
- 4: All of 3 + 30-min soak test (100 concurrent users making mixed requests) shows no error rate > 0.5% and no OOM growth.
**Threshold:** ≥ 3
**Evidence source:** pytest perf-module results + soak-test Grafana / stdout report.

### AC12 — Accessibility Conformance Spot-Check
**Type:** rule
**Pass condition:** axe-core (Playwright integration) run on `/dashboard?tab=general` and `/stocks/AAPL/scoring` → no WCAG 2.1 Level AA failures. In particular:
- Three-score badges have explicit text (`UP +2.4`) not just color.
- All new toggles/dropdowns/sliders have `aria-label`.
- `AS OF` tiles participate in an `aria-live` region.
- No pure-icon controls introduced (all controls text-only).
**Evidence source:** axe-core report JSON with 0 violations.
