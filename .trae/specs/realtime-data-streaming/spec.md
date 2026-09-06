# Real-Time Live Data Streaming System - Specification

## Problem

The BedaanWaves NASDAQ platform currently relies on REST endpoints with cached, periodically-fetched market data. The live streaming endpoints (`/api/v1/live/*`, `/api/v1/live-sse/*`) are stubbed (HTTP 501 / informational messages only). The `RealTimeMarketDataService` layers cache reads and writes around every provider call, meaning analytical consumers, dashboard views, and scoring engines may operate on stale data without visibility into data age. No end-to-end mechanism exists to validate data freshness, detect pipeline interruptions, alert on delays, or guarantee that core features consume continuously-updated live data.

## Users

- **Authenticated platform users**: Require live prices, live scores, live ranking, and live news on dashboard/stock/ranking pages with zero manual refresh.
- **Scoring & analysis engines**: Must consume always-current market data (quotes, intraday bars, adjusted closes) without cached fallbacks, so derived scores and rankings reflect the latest trading state.
- **Platform operators / SRE**: Need pipeline health metrics, alerting on source failures, freshness SLO violation tracking, and recovery evidence.

## Goals

1. Implement always-on, real-time data streaming for all market data consumed by core application features.
2. Eliminate any reliance on static cached or stale historical data for live views and live-derived computations.
3. Establish persistent, reconnecting data source connections with comprehensive error, fallback, and circuit-breaker handling.
4. Validate the freshness of every incoming data payload and reject/flag anything outside SLO windows.
5. Build observability and monitoring that surfaces pipeline latency, disconnections, reconnection events, and freshness violations.
6. Migrate all core UI features (Dashboard, Stock Detail, Ranking, Watchlist, News, Alerts) to exclusively consume the live stream.
7. Run end-to-end tests (including network-fault injection) that prove uninterrupted access to up-to-date data under variable conditions.

## Non-Goals

- Replacing PostgreSQL as the durable system-of-record for historical data.
- Rewriting the financial data ingestion batch pipeline (only the live streaming surface is in scope).
- Integrating a paid real-time market data feed; continue using yfinance as primary provider with SSE-backed polling push-model.
- Modifying ML model training logic or stored historical coefficients.
- Replacing the auth system or user management flows.

## Functional Requirements

### FR1: Live Streaming Transport

- SSE endpoints shall be implemented under `/api/v1/live-sse/` replacing existing stubs:
  - `GET /api/v1/live-sse/quote/{symbol}/stream` — per-symbol realtime quote stream (price, change, volume, timestamp).
  - `GET /api/v1/live-sse/intraday/{symbol}/stream` — per-symbol intraday bar stream (1m/5m granularity with freshness stamp).
  - `GET /api/v1/live-sse/market/stream` — market-wide pulse stream (composite index snapshots, active symbols count, top movers deltas, overall market pulse timestamp).
  - `GET /api/v1/live-sse/scores/stream` — live scoring delta stream (symbol-level score changes pushed within 2 polling cycles of a quote change).
  - `GET /api/v1/live-sse/news/stream` — live news item stream (new headlines as ingested).
- Every SSE payload SHALL include:
  - `event` field: `quote` | `intraday` | `market_pulse` | `score_delta` | `news_item` | `health` | `ping`
  - `data.freshness_ts` (UTC ISO) - the moment the source data was fetched.
  - `data.received_ts` (UTC ISO) - the moment the server enqueued the event.
  - `data.sequence` (monotonic integer per stream key) - gap detection.
- Heartbeat ping events SHALL be emitted every 10 seconds of silence so clients can detect dead TCP connections.

### FR2: Persistent Data Source Connections

- A `LiveDataOrchestrator` background service shall:
  - Maintain a persistent worker loop for each active stream subscription symbol.
  - Re-use the yfinance provider (via bounded executor) with per-symbol polling intervals: quotes = 3–5s market-open / 30s market-closed; intraday bars = 15s market-open / paused market-closed.
  - Use jitter (±15%) on polling intervals to avoid thundering-herd provider rate-limiting.
  - Implement exponential backoff + jitter on provider failures: base 1s, max 60s, reset after 3 consecutive successful polls.
  - Support per-symbol subscription reference counting — idle symbols are unsubscribed after 60s without any SSE client.

### FR3: Zero Reliance on Stale/Cached Data for Live Flows

- The existing `CacheService` TTL cache layer in `RealTimeMarketDataService` SHALL be BYPASSED for all live-stream-originating reads.
  - Introduce a `LiveReadThrough` flag / separate method set that ALWAYS fetches from provider on each live tick.
  - Existing historical REST endpoints (`/api/v1/market/*`, `/api/v1/history/*`) may retain caching; live streams MUST NOT share those cache keys for write.
- Each data payload emitted by the orchestrator SHALL carry `data_age_ms` = `now() - freshness_ts`.
- No component in the live path (SSE generator, score delta producer, market pulse producer) SHALL return "the last good value" older than SLO without explicitly tagging it as `stale: true` and firing a pipeline health event.

### FR4: Data Freshness Validation

- Every incoming data payload from provider SHALL be validated before emission:
  - `timestamp` within `MAX_QUOTE_AGE_S` = 120s during market hours, `MAX_QUOTE_AGE_CLOSED_S` = 900s outside hours — else mark `stale: true` + increment freshness counter.
  - Non-null `current_price` / `adjusted_close`; numeric sanity: `high >= max(open, close, low, adj_close)`, `low <= min(open, close, high, adj_close)`.
  - Intraday bars monotonic timestamp check vs. last emitted for same (symbol, interval).
- Failure of any validation check SHALL:
  1. NOT emit the bad payload to clients.
  2. Increment validation failure metric + log structured error (symbol, rule_violated, raw_payload_sha256).
  3. If 3 consecutive failures occur for a symbol, publish a `health:degraded` event for that stream.

### FR5: Data Source Interruption & Error Handling

- Circuit breaker per provider-symbol (half-open after 30s; 5 consecutive failures trip).
  - State: `closed -> open (skip polls) -> half-open (single probe) -> closed/open`.
- On provider outage / circuit-open:
  1. Emit `event:health` with `state: disconnected`, `retry_after_s`, `last_good_freshness_ts`.
  2. The SSE stream stays open (no disconnect); client-side `LiveDataConnectionManager` tracks health state and surfaces UI indicators.
  3. Scheduler backoff applies per FR2.
- Graceful degradation: When non-critical stream (news) source is down, other streams (quotes, scores) continue unaffected; health event per stream key.
- Structured logs for: connect, disconnect, reconnect attempt N, provider error, validation reject, circuit state change.

### FR6: Pipeline Monitoring & Alerting

- New `LivePipelineMetrics` service exposes (and integrates with existing `MetricsService`):
  - Per stream key: `messages_emitted_total`, `messages_dropped_validation_total`, `last_freshness_ts`, `last_data_age_ms`, `last_sequence`.
  - Per provider symbol: `poll_success_total`, `poll_error_total`, `poll_latency_ms_p50/p95`, `circuit_state`.
  - Global: `active_subscriptions`, `active_sse_connections`, `reconnects_total`, `freshness_slo_violations_total`.
- `GET /api/v1/data-health` enhanced to include:
  - Per-stream status (live / degraded / stale / disconnected).
  - SLO summary: % of events over the trailing 5 minutes meeting freshness threshold.
  - Current SSE client count and top 10 subscribed symbols by active connections.
- Alert thresholds (internal; surfaced via health payload + platform notifications):
  - WARN: data age exceeds 1.5× SLO threshold for >30s.
  - ERROR: data age exceeds 3× SLO threshold, or stream gap >2min.
  - Alert events are routed to `notification_dispatcher_service` as system-level notifications (in-app toast + user notifications table).

### FR7: Core Features Consume Live Streams (Frontend)

- Frontend components SHALL migrate from REST pull (React Query REST fetches) to SSE push-driven local state for:
  - Dashboard page: market pulse, 6D score spider live deltas, top movers list, stat cards.
  - Stock detail `[symbol]/page.tsx`: quote panel, intraday chart, live score badge.
  - Ranking page: `live` mode toggle (default ON) that applies score-delta patches to the ranking list in place.
  - Watchlist: per-row live price + change% updates.
  - News page: prepend incoming `news_item` events to the feed.
  - Alerts page: trigger UI-highlight of affected symbol when a quote crosses a watch threshold.
- A new `useLiveData(symbol | 'market' | 'scores' | 'news')` hook composes `useSSE` and:
  - Auto-reconnects with the same exponential backoff.
  - Tracks `lastDataAgeMs`, `isStale`, `connectionHealth` states.
  - Validates sequence gaps; on gap requests a `resync` single REST snapshot to re-establish baseline.
- React Query `staleTime` for all affected queries SHALL be set to `0` in the provider; live-streamed views MUST NOT rely on RQ cache as primary data source (RQ still used for historical time-series loads, not live tiles).

### FR8: End-to-End Resilience Testing

- Unit tests (pytest + vitest) for:
  - Freshness validator rules, boundary values, market-hours-aware thresholds.
  - Circuit breaker state transitions, half-open probe behavior.
  - Orchestrator reference counting (subscribe / last unsubscribe garbage collection).
  - SSE payload formatter: correct event types, fields, monotonic sequence.
  - Frontend `useLiveData` hook: reconnect logic, stale detection, gap resync trigger.
- Integration tests:
  - Provider failure injection (monkey-patch yfinance fetch → raise for N calls → recover) → SSE clients receive `health` events → eventual recovery, zero stale-data consumption in strict mode.
  - Simulated intermittent latency (add random sleep 0–5000ms) → freshness SLO tracked correctly, alert fires / clears.
- E2E (Playwright) tests:
  - Dashboard open + keep open for 2 minutes → at least 8 quote updates visible on a tracked symbol.
  - Network throttle (Fast 3G / offline toggled 3× 10s each) → SSE reconnects, final dashboard values match server-side latest.
  - Ranking live toggle → live patch updates scores inside a 5-second window without page reload.
- All tests MUST pass on CI (`pytest`, `vitest run`, `playwright test`) with evidence stored.

## Non-Functional Requirements

### NFR1: Performance / Scalability

- Single server node supports ≥500 concurrent SSE connections with ≤5% event delivery lag (measured `received_ts` on server vs. `onmessage` timestamp on browser) ≤150ms p95 for intra-region deployment.
- Per-symbol polling MUST NOT exceed 8 concurrent yfinance calls (bounded `ThreadPoolExecutor` already exists; reuse + cap).
- In-memory subscription state eviction LRU ≥10,000 symbols.

### NFR2: Availability / Reliability

- Live streaming endpoints SHALL return HTTP 200 within 3s of request (SSE headers sent immediately; events flow after).
- Mean time to recover from transient provider error ≤30s (backoff bounded).
- No crash propagation: any exception inside per-symbol poll loop is logged and the loop continues.

### NFR3: Security

- SSE endpoints require valid JWT (either `Authorization: Bearer` or `?token=` query param validated by existing auth middleware).
- `?token=` MUST not appear in access logs; sanitize in any request logging.
- SSE payloads MUST NOT leak internal provider error messages to clients (generic `provider_error` code).
- CORS headers preserved for configured origins only.

### NFR4: Observability

- Structured JSON logs (existing logger) for every live pipeline event; fields: stream_key, symbol, event_type, sequence, data_age_ms, poll_latency_ms, client_id.
- Metrics published at 10s granularity; consumable by existing `/system/metrics` endpoint.
- Traceable correlation: pass `correlation_id` from each SSE client connect through poll cycles → logs.

### NFR5: Maintainability

- All code changes MUST follow existing conventions: English-only comments, no hard-coded configuration (new configs in `Settings`), use `AsyncSession` for any DB writes (score history persistence, etc.).
- Add type hints everywhere; no `Any` escapes in public interfaces of the new live pipeline modules.
- No dependencies added without explicit justification in task evidence; prefer `stdlib` + already-installed packages (`FastAPI`, `pydantic`, `pytest`, `vitest`, `playwright`).

## Constraints

- Existing FastAPI + Next.js 16 + React 19 + SQLAlchemy 2.0 + Redis stack preserved.
- No Docker reliance or changes.
- English-only code, comments, logging messages (no Persian).
- No icon libraries used for any new UI indicators; use text labels (LIVE / STALE / DISCONNECTED / RECONNECTING, →, +, −, ✓, ×).
- All DB interactions Async with `pool_recycle` respected (no sync sessions in live writer paths).
- yfinance remains the sole market data source (no paid feed integration).

## Dependencies

- Backend: FastAPI StreamingResponse/SSE, existing `RealTimeMarketDataService` (refactored), `MetricsService`, `MarketHoursService`, `SchedulerService` (for orchestrator lifecycle).
- Frontend: existing `EventSource`-based `lib/sse.ts` and `hooks/useSSE.ts` (extended), Zustand stores (`useDateStore`, `useAppStore`), Playwright + Vitest.

## Assumptions

- Users have modern browsers with native `EventSource` support (all evergreen); no fallback transport (WebSocket) is required.
- yfinance rate limits allow per-symbol polling cadence described in FR2 for ≤~500 active subscriptions per node; horizontal scale-out is out of scope but architecture MUST allow it.
- Market status (open/closed/pre/after) is obtained from `MarketHoursService` and is accurate enough for polling cadence switching.

## Open Questions

1. Alert notification channels: Is in-app toast + user notifications table sufficient, or is email/SMS integration required for pipeline outages? (Default: in-app only for v1.)
2. SLO threshold values: Are `MAX_QUOTE_AGE_S = 120s (market open) / 900s (market closed)` acceptable, or do stakeholders require tighter (e.g., 30s / 300s)? (Default: values as stated.)
3. Score delta computation frequency: "within 2 polling cycles of quote change" — is this acceptable, or should score deltas be synchronous on each quote tick? (Default: 2-cycle batching to limit load on scoring engine.)

---

## Acceptance Criteria

### AC1 — Live SSE Endpoints Implemented
**Type:** rule
**Pass condition:** All 5 SSE streams from FR1 return `Content-Type: text/event-stream` and emit structured events (including `freshness_ts`, `received_ts`, `sequence`, `ping` every 10s) when called with valid auth; the old stub "endpoint removed" message is absent.
**Evidence source:** `pytest tests/test_live_sse_endpoints.py` HTTP assertions + stream content parse.

### AC2 — Polling Orchestrator Persistent + Subscriber Reference Counting
**Type:** rule
**Pass condition:** `LiveDataOrchestrator` maintains per-symbol poll loop with described cadence; subscribing 3 clients for same symbol runs 1 poll loop; last client unsubscribed → loop stopped within 65s.
**Evidence source:** `pytest tests/test_orchestrator_subscriptions.py` counter assertions + timing.

### AC3 — Zero Live Cache Dependency
**Type:** rule
**Pass condition:** Code inspection + test prove the live data path never reads the quote/intraday TTL cache keys used by historical REST endpoints. A test disabling cache completely still produces SSE quote events with incrementing `sequence` and fresh `freshness_ts`.
**Evidence source:** Static assertion in test suite + `test_live_no_cache_dependency.py` run with `CACHE_ENABLED=false`.

### AC4 — Freshness Validator Enforces SLO
**Type:** rule
**Pass condition:** Hard rule violations (null price, high<low, missing/null freshness_ts, non-monotonic intraday bar timestamps) → payload rejected, rule_violated log produced, `messages_dropped_validation_total` counter increments, no SSE event released. Soft freshness breach (age_s > SLO threshold) → payload **emitted as `stale:true`** with data_age_ms annotated, `stale_flagged_total` increments; the SSE event is delivered so UI can degrade gracefully rather than silence.
**Evidence source:** `pytest tests/test_freshness_validator.py` boundary-value matrix + `messages_dropped_validation_total` counter read from metrics service after injecting hard-vs-soft violations.

### AC5 — Provider Interruption Graceful Recovery
**Type:** rule
**Pass condition:** Monkey-patched provider raises for 10 consecutive polls → circuit opens, `health:disconnected` events emitted; provider recovers → circuit half-open probe → closes → streams resume; SSE client never disconnects at HTTP layer.
**Evidence source:** `pytest tests/test_circuit_breaker_recovery.py` state trace + event sequence.

### AC6 — Pipeline Monitoring & Alerts
**Type:** rule
**Pass condition:** Enhanced `/data-health` response includes per-stream status + freshness SLO attainment % + active SSE count. Freshness SLO violation → `notification_dispatcher_service` enqueues at least 1 system notification with severity ≥ WARN.
**Evidence source:** `pytest tests/test_data_health_enhanced.py` response schema assert + dispatched notifications spy.

### AC7 — Core UI Features Consume Live Streams
**Type:** rubric
**Dimension:** Coverage + UX fidelity of live stream integration in UI
**Scale (0-4):**
- 0: No UI feature uses SSE push; all still REST-poll.
- 1: 1–2 minor features use live push; no health/stale indicators visible.
- 2: Dashboard + Stock Detail migrated; basic LIVE/STALE badge visible, no ranking/watchlist live.
- 3: Dashboard, Stock Detail, Ranking, Watchlist, News all on SSE; connection state indicators present and intelligible.
- 4: All in FR7 migrated; connection state indicators (LIVE/STALE/DISCONNECTED/RECONNECTING + data-age seconds) present on each affected section with accessible aria-labels; scoring/alert features visibly update within promised windows.
**Threshold:** ≥3
**Evidence source:** Playwright screenshots + `playwright test e2e/live-stream-dashboard.spec.ts` run log + source review of `hooks/useLiveData.ts`.

### AC8 — E2E Resilience Under Network Degradation
**Type:** rubric
**Dimension:** Uninterrupted access + data correctness during variable network conditions
**Scale (0-4):**
- 0: E2E suite absent or fails on normal network.
- 1: Normal-network path passes but no fault-injection tests.
- 2: 1 fault-injection scenario exists and passes; no post-recovery correctness check.
- 3: All 3 scenarios (latency, throttle, offline toggles) run; dashboard visually updates; minor timing drift tolerated.
- 4: All E2E scenarios pass; final browser-side values for tracked symbols match server latest within tolerance; ranking live patch score deltas verified correct within 2× promised window.
**Threshold:** ≥3
**Evidence source:** `playwright show-trace` artifacts + CI test results.

### AC9 — Performance P95 Event Lag ≤150ms
**Type:** rule
**Pass condition:** Under load-test of 100 concurrent SSE clients × 20 symbols, p95 `(browser_onmessage_ts - server_received_ts) ≤ 150ms`.
**Evidence source:** `tests/perf/test_sse_lag.py` (or Playwright script) aggregated p95 report.

### AC10 — Auth & Sanitization
**Type:** rule
**Pass condition:** Unauthenticated SSE request → HTTP 401 (not streaming). `?token=` param works but never appears in any `logger.*` call output (asserted via log-capture test). Error payloads to client contain generic codes, not provider internals.
**Evidence source:** `pytest tests/test_live_sse_security.py`.
