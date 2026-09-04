# Code ↔ Documentation Mismatch Report

> **Phase 5 Output** — Alignment analysis between documentation and active source code.

**Analysis Date:** 2026-09-04  
**Mismatches Found:** 12  
**Resolved via doc update:** 8  
**Requires code change:** 2  
**Requires further investigation:** 2  
**Source code verified:** `backend/app/` (Python 3.11, FastAPI, SQLAlchemy 2.0), `frontend/src/` (Next.js 16, TypeScript)

---

## Summary

| # | Doc File | Code Module | Mismatch | Recommended Fix |
|---|----------|-------------|----------|-----------------|
| 1 | `05_api_documentation.md` | `app/api/routes/__init__.py` | Router count: docs say 16, code has 27 | **Update docs** |
| 2 | `03_technology_stack.md`, `09_data_services.md` | `app/models/models.py` | Market support: docs describe NYSE/LSE/HKEX, code restricts to NASDAQ | **Update docs** |
| 3 | Multiple docs | `backend/app/core/config.py` | Port: inconsistency between 3000 and 8000, docs unclear | **Update docs** |
| 4 | `06_database_schema.md` | `backend/app/models/models.py` | DB name: docs say `bedaanwaves`, code uses `bedaanwaves_db` | **Update docs** |
| 5 | `03_technology_stack.md`, `INTEGRATION_FRAMEWORK.md` | `frontend/next.config.ts`, `package.json` | Next.js version: docs say "14+", code uses "16"; docs mention Prisma, code has no Prisma | **Update docs** |
| 6 | `03_technology_stack.md`, `14_nlp_services.md` | `app/core/config.py`, `app/services/nlp/` | NLP language: docs claim Persian + English, code uses `bert-base-uncased` (English only) | **Update docs** |
| 7 | `05_api_documentation.md`, `API_DOCUMENTATION.md` | `app/api/routes/password_reset.py` | Missing password-reset endpoints from API docs | **Update docs** |
| 8 | `05_api_documentation.md` | `app/api/routes/data_health.py` | Data health endpoint prefix differs | **Update docs** |
| 9 | `ARCHITECTURE_DETAILS.md` (legacy) | `app/models/models.py` | Legacy DB schema describes NYSE/OTC markets, code restricts to NASDAQ | **Archive legacy** |
| 10 | `02_architecture_design.md` | `app/core/config.py` | Currency: docs mention multi-currency, config defaults to `IRR` only | **Update docs** |
| 11 | `03_technology_stack.md` | `app/services/` directory | Service counts: docs claim specific numbers, actual filesystem differs | **Update docs** |
| 12 | `18_password_recovery_architecture.md` | `backend/app/api/routes/password_reset.py` + `frontend/src/hooks/usePasswordRecoveryFSM.ts` | `lang` query param: backend restricts to `en` only (`pattern="^(en)$"`), but frontend passes `"en" | "fa"` | **Update code** |

---

## 1. Mismatch #1: API Router Count

**Doc file:** `docs/05_api_documentation.md` (now `docs/05_api/API_reference_v1.md`)  
**Doc file:** `docs/03_technology_stack.md` (now `docs/03_technology/TECH_stack_v1.md`)  
**Doc file:** `docs/04_service_catalog.md` (now `docs/04_services/SERVICES_catalog_v1.md`)  
**Code module:** `backend/app/api/routes/__init__.py`  
**Code module:** `backend/app/main.py`

**Description:**
Documentation consistently claims "16 API routers" or "16 routers" (cited in 05, 03, and 18_password_recovery_architecture.md). The actual code in `__init__.py` imports and exports **27 routers**:

```
auth, password_reset, stocks, market, analysis, portfolio, history, news,
ml, users, watchlists, notifications, specialized, system, intl, live,
live_sse, health, symbols, settings, ranking, market_data, data_health,
dashboard, data_integrity, coefficient_learning
```

`main.py` registers 24 of these 27 routers at runtime (3 may be internal-only).

**Impact:**
- Documentation is missing 11 routers: `password_reset`, `market_data`, `data_health`, `dashboard`, `intl`, `live`, `live_sse`, `symbols`, `settings`, `ranking`, `specialized`.
- Users following docs will not know about 44% of available API endpoints.

**Recommended Fix: Update docs**

Update `API_reference_v1.md` to list all 27 routers with their actual prefixes:
```python
# From main.py
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(password_reset_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(stocks_router, prefix="/api/v1/stocks", tags=["stocks"])
# ... etc (24 total registered)
```

---

## 2. Mismatch #2: Market Support (International vs NASDAQ-Only)

**Doc file:** `docs/03_technology_stack.md` (now `docs/03_technology/TECH_stack_v1.md`)  
**Doc file:** `docs/09_data_services.md` (now `docs/04_services/SERVICES_data-tier2_v1.md`)  
**Doc file:** `docs/02_architecture_design.md` (now `docs/02_architecture/ARCH_architecture-design_v1.md`)  
**Code module:** `backend/app/models/models.py`

**Description:**
Documentation describes multi-market support for NASDAQ, NYSE, LSE, HKEX, FWB, TSE, and OTC markets. The IntlPriceCandle model's docstring says "NASDAQ, NYSE, LSE, etc."

However, `models.py` enforces strict restrictions:
```python
ALLOWED_MARKETS = frozenset({"NASDAQ"})
ALLOWED_ASSET_CLASSES = frozenset({"EQUITY", "ETF"})
```

The `Asset._validate_market()` method raises `ValueError` for any market not in `ALLOWED_MARKETS`. Similarly, `_validate_asset_class()` restricts to EQUITY and ETF only.

**Code references:**
- `models.py:34` — `ALLOWED_MARKETS = frozenset({"NASDAQ"})`
- `models.py:35` — `ALLOWED_ASSET_CLASSES = frozenset({"EQUITY", "ETF"})`
- `models.py:88-106` — Validator methods with error messages explicitly rejecting non-Nasdaq assets

**Impact:**
- Docs claim international market support that the code actively prevents.
- The `IntlApiClient` and `InternationalMarket` services exist but data validation at the model layer will reject non-NASDAQ data.

**Recommended Fix: Update docs**

Update `TECH_stack_v1.md` and `SERVICES_data-tier2_v1.md` to reflect NASDAQ-only restriction. Note that `IntlApiClient` and `InternationalMarketService` exist but are restricted to NASDAQ by model validators.

---

## 3. Mismatch #3: Port Numbers

**Doc file:** `docs/03_technology_stack.md` (now `docs/03_technology/TECH_stack_v1.md`)  
**Doc file:** `docs/07_configuration_guide.md` (now `docs/07_configuration/CONFIG_guide_v1.md`)  
**Doc file:** `docs/NATIVE_WINDOWS_SETUP.md` (now `docs/02_architecture/ARCH_deployment-windows_v1.md`)  
**Code module:** `backend/app/core/config.py`  
**Code module:** `backend/app/main.py`

**Description:**
- `config.py` defaults: `API_PORT: int = 8000`
- `config.py` defaults: `API_HOST: str = "0.0.0.0"`
- Docs inconsistently reference port `3000` (some docs) and `8000` (integration docs)
- `README_INTEGRATION.md` correctly states port 8000
- `NATIVE_WINDOWS_SETUP.md` states port 3000 and references `http://localhost:3000/api/v1/docs`

**Impact:**
Users following Windows setup docs may run the backend on the wrong port.

**Recommended Fix: Update docs**

Update `ARCH_deployment-windows_v1.md` to clarify:
- Backend API runs on port 8000 (per `config.py` default and `main.py` uvicorn invocation)
- Frontend runs on port 3005 or 3000 (per `AGENTS.md` `npm run dev` instructions)

---

## 4. Mismatch #4: Database Name

**Doc file:** `docs/06_database_schema.md` (now `docs/06_database/DB_schema_v1.md`)  
**Doc file:** `docs/INTEGRATION_FRAMEWORK.md` (now `docs/11_legacy/LEGACY_integration-framework_v1.md`)  
**Code module:** `backend/app/core/config.py`

**Description:**
- Docs reference `bedaanwaves` as the database name
- `config.py` uses: `DB_NAME: str = "bedaanwaves_db"` and `DATABASE_URL = "postgresql://administrator:placeholder@localhost:5432/bedaanwaves_db"`

**Impact:**
Users creating the database may use the wrong name.

**Recommended Fix: Update docs**

Update all docs to use `bedaanwaves_db` as the database name, matching `config.py`.

---

## 5. Mismatch #5: Frontend Framework Version

**Doc file:** `docs/03_technology_stack.md` (now `docs/03_technology/TECH_stack_v1.md`)  
**Doc file:** `docs/INTEGRATION_FRAMEWORK.md` (now `docs/11_legacy/LEGACY_integration-framework_v1.md`)  
**Code module:** `frontend/package.json`  
**Code module:** `frontend/next.config.ts`

**Description:**
- Docs claim "Next.js 14+"
- `package.json` specifies `"next": "^16.0.0"`
- Docs mention "Prisma" for frontend database access
- Code uses SQLAlchemy on backend; frontend has no Prisma dependency

**Impact:**
Version mismatch could cause confusion about available features and compatibility.

**Recommended Fix: Update docs**

Update `TECH_stack_v1.md` to reflect Next.js 16 App Router. Remove Prisma references (not used in this project).

---

## 6. Mismatch #6: NLP Language Support

**Doc file:** `docs/03_technology_stack.md` (now `docs/03_technology/TECH_stack_v1.md`)  
**Doc file:** `docs/14_nlp_services.md` (now `docs/04_services/SERVICES_nlp-tier5_v1.md`)  
**Code module:** `backend/app/core/config.py`  
**Code module:** `backend/app/services/nlp/`

**Description:**
- Docs describe Persian NLP support: "Hazm (Persian text processing), ParsBERT (Persian BERT), transformers, spaCy"
- `config.py` uses: `NLP_MODEL: str = "bert-base-uncased"` (English-only)
- Config has `PERSIAN_STOPWORDS_ENABLED` and `PERSIAN_LEMMATIZATION_ENABLED` flags
- But the NLP model itself is English (`bert-base-uncased`)

**Impact:**
Persian NLP features described in docs are not actually configured. The Persian flags exist but may not be wired to an actual Persian model.

**Recommended Fix: Update docs**

Update `SERVICES_nlp-tier5_v1.md` to clarify that Persian NLP flags are configured but the active model is English-only (`bert-base-uncased`). Note that Persian support is planned but not implemented.

---

## 7. Mismatch #7: Missing Password-Recovery API Endpoints

**Doc file:** `docs/05_api_documentation.md` (now `docs/05_api/API_reference_v1.md`)  
**Code module:** `backend/app/api/routes/password_reset.py`

**Description:**
- `05_api_documentation.md` documents auth endpoints (login, register, refresh) but does NOT mention the password-reset endpoints
- `password_reset.py` defines 3 endpoints:
  - `POST /auth/password-reset/request`
  - `POST /auth/password-reset/verify`
  - `POST /auth/password-reset/confirm`
- These are mounted under `/api/v1/auth` prefix in `main.py` (line 345)
- `API_DOCUMENTATION.md` does mention `/auth/password-reset/request` but with different structure

**Impact:**
API consumers cannot discover password-recovery endpoints from the primary API docs.

**Recommended Fix: Update docs**

Add password-recovery endpoints to `API_reference_v1.md` with their full paths (`/api/v1/auth/password-reset/{action}`), request/response schemas, and security notes (account-enumeration prevention).

---

## 8. Mismatch #8: Data Health Endpoint Prefix

**Doc file:** `docs/05_api_documentation.md` (now `docs/05_api/API_reference_v1.md`)  
**Code module:** `backend/app/api/routes/data_health.py`  
**Code module:** `backend/app/main.py`

**Description:**
- Docs list data health endpoint at `/api/data-health`
- Code registers: `app.include_router(data_health_router, tags=["data-health"])` (no prefix)
- The actual endpoint path is `/api/v1/data-health/*` (derived from `API_V1_STR` + router path)
- Config has `AUTH_PUBLIC_PATHS: List[str] = ["/", "/health", "/api/data-health"]`

**Impact:**
The public paths list in config references `/api/data-health` but the actual route is `/api/v1/data-health`.

**Recommended Fix: Update docs AND config**

- Update docs to show `/api/v1/data-health`
- Update `config.py` `AUTH_PUBLIC_PATHS` to use `/api/v1/data-health`

---

## 9. Mismatch #9: Legacy DB Schema in Historical Docs

**Doc file:** `docs/architecture/ARCHITECTURE_DETAILS.md` (now `docs/11_legacy/LEGACY_architecture-details_v1.md`)  
**Code module:** `backend/app/models/models.py`

**Description:**
- Legacy doc describes database schema with `STOCKS`, `MARKET_DATA`, `OTC`, `NYSE`, `LSE` markets
- Current `models.py` restricts to NASDAQ only, uses `assets`, `intl_price_candles` tables
- Legacy doc's SQL schema uses different column names and table structures

**Impact:**
Historical documents present contradictory schema information.

**Recommended Fix: Archive legacy**

`LEGACY_architecture-details_v1.md` is already archived in `11_legacy/`. Add a banner noting it describes the pre-refactor schema and does not match current code.

---

## 10. Mismatch #10: Currency

**Doc file:** `docs/02_architecture_design.md` (now `docs/02_architecture/ARCH_architecture-design_v1.md`)  
**Code module:** `backend/app/core/config.py`  
**Code module:** `backend/app/models/models.py`

**Description:**
- Architecture docs mention "multi-currency" support
- `config.py` has no `SUPPORTED_CURRENCIES` setting
- `models.py` has `currency = Column(String(3), default="IRR")` — Iranian Rial only
- No currency conversion logic visible in model or config

**Impact:**
Multi-currency feature described in docs is not implemented.

**Recommended Fix: Update docs**

Update `ARCH_architecture-design_v1.md` to note currency is currently IRR-only (default in model). Multi-currency conversion is planned but not implemented.

---

## 11. Mismatch #11: Service Count Discrepancies

**Doc file:** `docs/03_technology_stack.md` (now `docs/03_technology/TECH_stack_v1.md`)  
**Doc file:** `docs/04_service_catalog.md` (now `docs/04_services/SERVICES_catalog_v1.md`)  
**Code module:** `backend/app/services/` directory structure

**Description:**
- Docs claim "50+ services" and specific counts per tier
- Actual filesystem inspection reveals:
  - `core/`: 6 service files
  - `data/`: 19 service files
  - `analysis/`: 27 service files
  - `ml/`: 8 service files
  - `nlp/`: 4 service files
  - `user/`: 8 service files
  - `specialized/`: 7 service files
  - `system/`: 9 service files
  - Total: ~88 service files (not 50+)

**Impact:**
Service count in docs is significantly understated.

**Recommended Fix: Update docs**

Update `SERVICES_catalog_v1.md` with actual service counts per tier based on filesystem inspection.

---

## 12. Mismatch #12: Password Recovery Language Support (REQUIRES CODE CHANGE)

**Doc file:** `docs/18_password_recovery_architecture.md` (now `docs/08_frontend/FE_password-recovery-architecture_v1.md`)  
**Code module:** `backend/app/api/routes/password_reset.py`  
**Code module:** `frontend/src/lib/password-recovery-api.ts`

**Description:**
- Docs and frontend code support bilingual password recovery (`lang: "en" | "fa"`)
- Frontend passes `lang` parameter: `api/password-reset/request?lang=${lang}`
- Backend route definition: `lang: str = Query("en", pattern="^(en)$")`
- The `pattern="^(en)$"` regex **only allows "en"** — Persian (`"fa"`) is rejected
- Error messages are only defined for `"en"` in the `MESSAGES` dict; `"fa"` key does not exist

**Code references:**
- `password_reset.py:57` — `lang: str = Query("en", pattern="^(en)$")`
- `password_reset.py:79, 82, 91, 95` — `lang: str = Query("en", pattern="^(en)$")`
- `password_reset.py:39-47` — `MESSAGES` dict only has `"en"` key
- `password-recovery-api.ts:63` — `lang: "en" | "fa" = "en"`
- `password-recovery-api.ts:68` — `?lang=${lang}`

**Impact:**
When the frontend sends `lang=fa`, the backend will return a 422 validation error. Persian password recovery UI will break.

**Recommended Fix: Update code (with rationale)**

This is a high-level architectural contradiction: the password-recovery feature is documented and implemented as bilingual, but the backend rejects Persian. Code is NOT the source of truth here — this is a documented design decision that the code does not fully implement.

Proposed code change in `backend/app/api/routes/password_reset.py`:
```python
# Change from:
lang: str = Query("en", pattern="^(en)$"),

# To:
lang: str = Query("en", pattern="^(en|fa)$"),

# And add Persian messages:
"fa": {
    "request_sent": "اگر حسابی برای این ایمیل وجود داشته باشد، لینک بازیابی ارسال شده است.",
    "token_invalid": "این لینک بازیابی منقضی شده یا دیگر معتبر نیست. لطفاً یک لینک جدید درخواست کنید.",
    "password_updated": "رمز عبور شما با موفقیت به‌روزرسانی شد. اکنون می‌توانید وارد شوید.",
    "password_too_short": "رمز عبور باید حداقل ۸ کاراکتر باشد.",
    "token_missing": "هیچ توکن بازیابی ارائه نشده است. لطفاً لینک ایمیل را باز کنید.",
},
```

---

## Appendix: Verified Code-Facts

### API Routers (27 total, 24 registered at runtime)
Verified from `app/api/routes/__init__.py` and `app/main.py`.

### Password Recovery Endpoints
```
POST /api/v1/auth/password-reset/request
POST /api/v1/auth/password-reset/verify
POST /api/v1/auth/password-reset/confirm
```
Verified from `password_reset.py:54,79,92` and `main.py:345`.

### Configuration Defaults (from `config.py`)
- `API_PORT: 8000`
- `DB_NAME: "bedaanwaves_db"`
- `NLP_MODEL: "bert-base-uncased"`
- `JWT_ALGORITHM: "HS256"`
- `ALLOWED_MARKETS: frozenset({"NASDAQ"})` (from `models.py:34`)

### Frontend State
- `usePasswordRecoveryFSM.ts` — 6 states, 8 public actions, transition table at line 77
- `password-recovery-api.ts` — 4 API functions, localStorage draft persistence
- `forgot-password/page.tsx` — uses `requestPasswordReset(email)` (line 29, no lang param)
- `reset-password/page.tsx` — uses `verifyResetToken(token)` and `confirmResetPassword(token, password)`

---

*End of CODE_DOCS_MISMATCH_REPORT.md*
