# Dashboard Charts — Spec & Delivery Roadmap

> Status: live
> Owner: frontend / analytics
> Last updated: 2026-09-04

This document is the single source of truth for the chart set on
`/dashboard?tab=*` and the per-share page (`/stocks/{symbol}/scoring`).
It exists so we never re-introduce inconsistencies between the
"current" view (spider) and the "trend" views (line + column).

---

## 1. The 20 charts

Every chart below must be present on **both** the dashboard *and* the
per-share scoring page, with one rule that keeps them honest:

> The **last data point** in every line/column chart must equal the
> data point rendered by the matching spider chart.

### A. Spider (current) — pull from the `latest=true` endpoint

| # | Chart | Source |
|---|-------|--------|
| 1 | Dimension scores (current) | `/analysis/dashboard/general?latest=true` |
| 2 | Sub-dimension scores of each dimension | `/analysis/dashboard/{dimension}?latest=true` |
| 3 | Aspect scores of each sub-dimension | `/analysis/dashboard/{dimension}/aspects?latest=true` (TODO) |
| 4 | Sub-aspect scores of each aspect | `/analysis/dashboard/{dimension}/sub-aspects?latest=true` (TODO) |

### B. Line trend — 30-day window ending on `latest_date`

| # | Chart | Source |
|---|-------|--------|
| 5 | Dimension scores trend | `/analysis/dashboard/score-trend?days=30&market=NASDAQ&end_date={latest_date}` |
| 6 | Sub-dimension scores trend (per dimension) | TODO: aggregate `ScoreHistory` per sub-dimension |
| 7 | Aspect scores trend | TODO |
| 8 | Sub-aspect scores trend | TODO |

### C. Column (delta) — `value[t] - value[t-1]`

| # | Chart | Source |
|---|-------|--------|
| 9 | Dimension score change | computed from chart #5 |
| 10 | Sub-dimension score change | computed from chart #6 |
| 11 | Aspect score change | computed from chart #7 |
| 12 | Sub-aspect score change | computed from chart #8 |

### D. Weight (coefficient) trend — line

| # | Chart | Source |
|---|-------|--------|
| 13 | Dimension weights trend | `/analysis/dashboard/coefficient-history` |
| 14 | Sub-dimension weights trend | TODO: extend `coefficient_history` schema |
| 15 | Aspect weights trend | TODO |
| 16 | Sub-aspect weights trend | TODO |

### E. Weight (coefficient) delta — column

| # | Chart | Source |
|---|-------|--------|
| 17 | Dimension weight change | computed from chart #13 |
| 18 | Sub-dimension weight change | computed from chart #14 |
| 19 | Aspect weight change | computed from chart #15 |
| 20 | Sub-aspect weight change | computed from chart #16 |

---

## 2. Data-synchronization contract

These rules are enforced by the regression tests in
`backend/app/tests/api/test_market_score_trend_service.py` and
`frontend/src/tests/dashboard-api.test.ts`.

1. The spider chart must always pass `?latest=true` so the backend
   resolves the most-recent data date.
2. The trend charts must **always send `end_date={spider_latest_date}`**
   and **never combine it with `latest=true`**. The backend honours an
   explicit `end_date` even if `latest=true` is also set.
3. The trend window is the 30 days *ending* on `latest_date`, inclusive.
4. A regression test must exist for each new chart family so the
   spider/trend sync cannot silently break again.

---

## 3. What is already live (commit 2026-09-04)

* Spider chart #1 (general dashboard) — `frontend/src/components/charts/SpiderChart.tsx`
* Score-trend line + daily-change column charts (general dashboard) —
  `frontend/src/app/dashboard/page.tsx`
* Coefficient history line + daily-delta column (general dashboard)
* Spider chart #2 per dimension — `frontend/src/components/dashboard/DimensionDashboard.tsx`

## 4. What is still pending

* Charts #3, #4 (aspects / sub-aspects spider) — backend endpoints not yet shipped
* Charts #6, #7, #8 (sub-dim / aspect / sub-aspect line trends) — aggregation jobs not yet
* Charts #10, #11, #12 (delta columns for the above)
* Charts #14-#20 (per-level weight history) — `coefficient_history` schema currently only stores top-level dimensions

## 5. UX / design rules

* Color palette is locked in `frontend/src/app/dashboard/page.tsx`:
  Fundamental `#2563EB`, Technical `#10B981`, Sentiment `#F59E0B`,
  Risk `#EF4444`, Macro `#8B5CF6`, AI `#EC4899`. Sub-levels inherit
  their parent's hue but with varying lightness.
* Every chart renders a skeleton loader during fetch (see
  `frontend/src/components/ux/SkeletonLoaders.tsx`).
* Clicking a dimension chip in chart #1 must drill into the matching
  tab via `?tab=fundamental|technical|...` (`handleDimensionClick`).
* Sub-dimension chips in `DimensionDashboard` must drill into
  `?tab=...&sub={key}`.