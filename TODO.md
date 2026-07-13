# TODO - پروژه BedaanWaves

---

## فاز ۰ — امنیت و باگ‌های بحرانی (Critical Security & Bug Fixes)

### ۰.۱) فعال‌سازی پیش‌فرض احراز هویت (C1)
- [x] تغییر پیش‌فرض `REQUIRE_AUTH` در `config.py` به `True`
- [x] افزودن شرط `ENVIRONMENT=development` برای غیرفعال‌سازی اختیاری در محیط توسعه
- [x] افزودن fail-fast در startup: اگر `ENVIRONMENT=production` و `REQUIRE_AUTH=False` → خطا و خروج
- [x] تست: با `REQUIRE_AUTH=True`، درخواست بدون توکن به اندپوینت‌های محافظت‌شده → 401

### ۰.۲) رفع IDOR در اندپوینت‌های پورتفولیو (C2)
- [x] افزودن شرط `Portfolio.user_id == user_id` به تمام کوئری‌های خواندن/ویرایش/حذف در `routes/portfolios.py`:
  - `get_portfolio`
  - `update_portfolio`
  - `delete_portfolio`
  - `add_holding`
  - `get_holdings`
  - `remove_holding`
- [x] بازگرداندن 404 (نه 403) وقتی پورتفولیو متعلق به کاربر فعلی نیست (جلوگیری از information disclosure)
- [x] تست: کاربر A پورتفولیو کاربر B را بخواند → 404

### ۰.۳) چرخش و پاکسازی رازهای کامیت شده (C3)
- [ ] چرخش فوری `BRS_API_KEY` در سرویس BrsApi.ir + آپدیت در `.env`
- [ ] تغییر رمز عبور دیتابیس در PostgreSQL + آپدیت `DATABASE_URL`
- [ ] تولید `SECRET_KEY` جدید با `python -c "import secrets; print(secrets.token_urlsafe(64))"`
- [x] افزودن `.env` به `.gitignore` (از قبل وجود داشت + `backend/.env` به طور صریح اضافه شد)
- [x] جایگزینی مقادیر واقعی در `.env.example` با placeholder (مثال: `BRS_API_KEY=your_brs_api_key_here`)
- [ ] بررسی تاریخچه git برای اطمینان از اینکه رازهای قدیمی در histor irreversible نیستند (force-push لازم باشد)
- [ ] افزودن ابزار اسکن راز به CI (مثل `git-secrets` یا `trufflehog`)

### ۰.۴) پیاده‌سازی متدهای ناموجود BRS Client (C4)
- [x] پیاده‌سازی یا نگاشت صحیح متدهای زیر در `BrsApiClient`:
  - `get_stock_info` → استفاده از `get_symbol`
  - `get_stock_price` → استفاده از `get_candlestick`
  - `get_stock_history` → استفاده از `get_history`
  - `search_stocks` → فیلتر کردن نتایج `get_all_symbols`
- [x] پیاده‌سازی متدهای ناموجود `MarketService`:
  - `get_market_indices` → `get_index`
  - `get_market_stats` → تجمیع داده‌های indices
  - `get_top_gainers` / `get_top_losers` / `get_most_active` → stub با پیام واضح (نیازمند DB)
- [x] حذف یا آپدیت `_FakeBrsClient` در `tests/conftest.py` تا دقیقاً همان متدها را داشته باشد که کلاینت واقعی
- [x] افزودن تست قرارداد (contract test) که بررسی می‌کند کلاینت واقعی تمام متدهایی را که routes استفاده می‌کنند، ارائه می‌دهد
- [ ] smoke test: اجرای اندپوینت‌های `/stocks/{ticker}`, `/stocks/search`, `/stocks/batch`, `/history/{ticker}` با داده واقعی

---

## فاز ۱ — مشکلات با اولویت بالا (High Priority Fixes)

### ۱.۱) اجرای واقعی RBAC روی اندپوینت‌های سیستم (H1)
- [x] اعمال `Depends(get_current_admin_user)` روی تمام اندپوینت‌های `/system/*`:
  - `/system/scheduler/jobs` (تمام متدها)
  - `/system/metrics`
  - `/system/queue/jobs`
- [x] افزودن `Depends(require_permissions([Permission.ADMIN_ACCESS]))` به اندپوینت‌های حساس
- [x] حذف کد مرده RBAC در صورت عدم نیاز یا مستندسازی دلیل نگهداری
- [x] تست: کاربر عادی به `/system/metrics` → 403

### ۱.۲) رفع نشت تسک‌های asyncio در سرویس‌های سیستم (H2)
- [x] تبدیل `SchedulerService` به singleton در lifespan (`app/main.py`) و تزریق از طریق DependencyContainer
- [x] تبدیل `QueueService` به singleton در lifespan و تزریق از طریق DependencyContainer
- [x] حذف فراخوانی `initialize()` از داخل route handlers
- [x] اطمینان از `_running = False` در `__aexit__` / `shutdown()` برای پاکسازی تسک‌ها
- [x] تست: چند درخواست متوالی به `/system/metrics` → تعداد تسک‌های پس‌زمینه ثابت بماند

### ۱.۳) هماهنگی migration با مدل‌ها و حذف `create_all` (H3)
> وضعیت: **ناقص (PARTIAL)** — migration اولیه (`c57c8b5674de_...`) وجود دارد اما از `Base.metadata` استفاده می‌کند نه autogenerate؛ `db/base.py:65` هنوز `create_all` را صدا می‌زند. جداول `watchlists`/`watchlist_items`/`notifications`/`user_preferences` در مدل‌ها هستند ولی migration کامل نیست.
- [x] اجرای `alembic revision --autogenerate` برای تولید migration کامل از مدل‌های فعلی
- [x] افزودن جداول ناموجود به migration: `watchlists`, `watchlist_items`, `notifications`, `user_preferences`
- [x] اصلاح تناقضات:
  - ستون `active` در `api_logs`: migration `nullable=True` → مدل `nullable=False` (یکسان‌سازی)
  - حذف ایندکس تکراری `idx_log_endpoint` (موجود در migration + مدل `ix_api_logs_endpoint`)
- [x] جایگزینی `Base.metadata.create_all` در `base.py` با اجرای Alembic در startup
- [x] افزودن بررسی CI: `alembic check` یا اسکنر diff بین models و migrations
- [x] تست: اجرای `alembic upgrade head` روی دیتابیس خالی → همه جداول ایجاد شوند

### ۱.۴) اصلاح خطای 500 به جای 401 در `/refresh` (H4)
- [x] Wrap کردن `jwt.decode(token, ...)` در `routes/auth.py:62` با `try/except JWTError`
- [x] بازگرداندن `HTTP_401_UNAUTHORIZED` با پیام مناسب
- [x] تست: ارسال refresh token منقضی شده → 401 (نه 500)

---

## فاز ۲ — مشکلات متوسط (Medium Priority Fixes)

### ۲.۱) رفع N+1 queries در routes بازار (M2)
> وضعیت: **ناقص (PARTIAL)** — `tse_dashboard` و `industry_ranking` از subqueryهای window-function استفاده می‌کنند، اما `get_latest_prices` (`market.py:139-174`) همچنان در یک حلقه جداگانه کوئری می‌زند (N+1 واقعی باقی‌مانده).
- [ ] بازنویسی `get_latest_prices` در `routes/market.py` با یک کوئری `JOIN` یا `LATERAL` برای گرفتن آخرین کندل تمام دارایی‌ها
- [ ] بازنویسی `tse_dashboard` با کوئری واحد که gainers/losers را در یک بار برمی‌گرداند
- [ ] بازنویسی `industry_ranking` با کوئری واحد
- [ ] تست: درخواست `/market/tse-dashboard` با ۵۰ دارایی → تعداد کوئری‌ها از ۵۰ به ۱ کاهش یابد

### ۲.۲) ایمن‌سازی `update_profile` در برابر mass-assignment (M4)
- [ ] جایگزینی حلقه `setattr` با allow-list صریح از فیلدهای قابل به‌روزرسانی
- [ ] افزودن بررسی یکتا بودن email قبل از آپدیت (یا catch کردن `IntegrityError` و بازگرداندن 409)
- [ ] تست: ارسال فیلد `is_admin=True` در بدنه آپدیت → نادیده گرفته شود یا خطای اعتبارسنجی

### ۲.۳) بهبود Rate Limiter (M6)
- [ ] تغییر کلید محدودیت از `client_ip:path` به `client_ip` (جهت جلوگیری از دور زدن با تغییر path)
- [ ] افزودن eviction برای کلیدهای inactive (مثلاً پس از ۱ ساعت بدون درخواست)
- [ ] مستندسازی محدودیت‌های in-memory و план مهاجرت به Redis برای production

### ۲.۴) اطمینان از غیرفعال بودن وضعیت dev در production (M5)
- [x] اطمینان از اینکه `DEV_USER_ID` و `REQUIRE_AUTH=False` هرگز در production فعال نمی‌شوند (`config.py:348-353` fail-fast + `main.py:35-45` RuntimeError هنگام production با `REQUIRE_AUTH=False` یا `DEBUG=True`)

---

## فاز ۳ — مشکلات کم و نگهداری (Low Priority & Maintenance)

### ۳.۱) پاکسازی وابستگی‌ها (L1)
- [ ] حذف وابستگی‌های تکراری از `requirements.txt` (`scikit-learn`, `python-dotenv`)
- [ ] حذف وابستگی‌های استفاده نشده (`sqlmodel`, `tensorflow`, `keras`, `prophet`, `pycaret`, `selenium`, `optuna`, `shap`, `gensim`, `transformers`, `celery`, `rq`)
- [ ] افزودن `pip-tools` یا `uv` برای مدیریت وابستگی با lockfile
- [ ] اجرای `pip-audit` برای اسکن آسیب‌پذیری‌های وابستگی

### ۳.۲) غیرفعال‌سازی مستندات در production (L2)
- [ ] تغییر پیش‌فرض `DEBUG` در `config.py` به `False`
- [ ] شرطی کردن `docs_url` و `redoc_url` در `main.py` بر اساس `ENVIRONMENT`

### ۳.۳) تعریف Pydantic schemas برای بدنه‌های dict (L3)
- [ ] ساخت schemas برای اندپوینت‌هایی که `dict` قبول می‌کنند:
  - `routes/analysis.py`: `/fundamental`, `/scoring`
  - `routes/ml.py`: `/predict`, `/recommendation`, `/optimize`, `/forecast`
  - `routes/specialized.py`: `/screen`, `/compare`, `/correlation`, `/calendar/events`
- [ ] تست: ارسال داده نامعتبر → 422 به جای خطای داخلی

### ۳.۴) منبع‌سازی وزن‌های Scoring از تنظیمات (L5)
- [ ] تغییر `scoring_service.py` برای خواندن `DIMENSION_WEIGHTS` از `get_settings().SCORING_WEIGHTS`
- [ ] حذف constant سخت‌کد شده در `scoring_service.py:41-48`

### ۳.۵) رفع ساختار موتور در زمان import (M3)
- [ ] جابجایی `create_async_engine` از سطح ماژول `db/base.py` به داخل تابع یا lifespan
- [ ] جابجایی فراخوانی `get_settings()` از سطح ماژول به داخل توابع که به آن نیاز دارند

---

## فاز ۴ — قابلیت‌های جدید Tier 3 (مطابق TODO اصلی)

### ۴.۱) CryptoAndStocks integration (RAW/PROCESSED/SNAPSHOT + Online freshness)
> وضعیت: **ناقص (PARTIAL)** — `MLSignal` با `valid_until`/`is_active` (`models.py:303-304`) و اندپوینت `GET /analysis/signals/{symbol}` (`analysis.py:24-70`) پیاده‌سازی شده‌اند، اما جداول `RawMarketData`/`MarketDataSnapshot` و pipeline کریپتو هنوز وجود ندارند.
- [ ] ۰.۱) افزودن دقیقاً ۲ جدول مکمل به مدل‌ها و بدون جدول اضافی:
  - [ ] `RawMarketData`
  - [ ] `MarketDataSnapshot`
- [ ] ۰.۲) ساخت Alembic migration برای این ۲ جدول
- [ ] ۰.۳) ساخت Crypto pipeline (bridge به الگوریتم‌های پایتون OldFils/CryptoAndStocks) برای:
  - [ ] ذخیره RAW
  - [ ] اجرای الگوریتم‌های پایتون و تولید features/processed
  - [ ] ذخیره snapshot/processed
  - [ ] تولید/آپدیت `MLSignal` با `valid_until` و `is_active` (هم‌خوان با `GET /analysis/signals/{symbol}`)
- [ ] ۰.۴) بررسی و تطبیق APIها:
  - [ ] اطمینان از اینکه endpointهای موجود front/back با مدل‌های موجود همخوان هستند
  - [ ] در صورت نیاز، افزودن یک endpoint کوچک وضعیت آنلاین بودن با اتکا به snapshot freshness (بدون تغییرات گسترده)
- [ ] ۰.۵) هندلینگ داده واقعی و آنلاین بودن:
  - [ ] snapshot stale تولید نکند
  - [ ] `valid_until`/`is_active` بودن سیگنال بر اساس freshness محاسبه شود
- [ ] ۰.۶) اجرای migration و smoke test در محیط + تست endpoint:
  - [ ] `/analysis/signals/{symbol}` برای crypto

### ۴.۲) افزودن ranking endpoint برای multi-ticker Top-N
- [ ] بررسی `ScoringService.rank_stocks` و API routes فعلی scoring/ranking
- [ ] افزودن request/response schema models در صورت نیاز
- [ ] پیاده‌سازی `POST /analysis/scoring/rank` که لیست tickerها را با معیارهای 6D دریافت می‌کند
- [ ] استفاده از `ScoringService.rank_stocks` برای محاسبه امتیاز و بازگرداندن Top-N مرتب شده بر اساس `overall_score` (شامل grade)
- [ ] افزودن پارامتر اختیاری `dimension` برای فیلتر بر روی بعد خاص
- [ ] افزودن پارامتر `limit` (پیش‌فرض: ۱۰)

### ۴.۳) اصلاح mapping ورودی macro/ai در scoring route
- [x] بررسی تطابق docstring API با کلیدهای مورد انتظار `ScoringService`
- [x] پیاده‌سازی mapping `growth/momentum` → `macro/ai` در داخل scoring route (`routes/analysis.py:563-566`)
- [ ] آپدیت مستندات endpoint

---

## فاز ۵ — بهبودهای معماری و کیفیت کد

### ۵.۱) پاکسازی کدهای مرده و بدون استفاده (L4)
- [ ] بررسی و تصمیم‌گیری در مورد `DependencyContainer`: حذف یا استفاده واقعی در routes
- [ ] حذف یا expose کردن سرویس‌های NLP بدون استفاده (`chatbot_service.py`, `search_service.py`)
- [ ] حذف یا استفاده از `Portfolio.is_public` و `public_token`
- [ ] حذف جدول‌های مرده `api_logs` و `Alert` (M1) یا پیاده‌سازی استفاده از آن‌ها

### ۵.۲) بهبود پوشش تستی
- [x] افزودن تست قرارداد BRS Client (بررسی تطابق متدهای کلاینت با routes)
- [x] افزودن تست‌های end-to-end برای auth guard فعال (`REQUIRE_AUTH=True`)
- [x] افزودن تست IDOR برای اندپوینت‌های پورتفولیو
- [x] افزودن تست‌های route و middleware (فعلاً فقط services تست می‌شوند)
- [x] افزودن تست migration: `alembic upgrade head` روی دیتابیس خالی

---

## خلاصه اولویت‌ها

| فاز | اولویت | تأثیر |
|------|--------|-------|
| ۰ | 🔴 بحرانی | امنیت، دسترسی، کارکرد اندپوینت‌ها |
| ۱ | 🟠 بالا | اجرای RBAC، نشت منابع، یکپاچگی دیتابیس |
| ۲ | 🟡 متوسط | عملکرد، اعتبارسنجی ورودی |
| ۳ | 🟢 کم | تمیزی کد، وابستگی‌ها |
| ۴ | 🔵 ویژگی | کریپتو، رتبه‌بندی، اصلاح scoring (مطابق TODO اصلی) |
| ۵ | ⚪ معماری | پاکسازی، تست |
