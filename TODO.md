# TODO - پروژه BedaanWaves (Updated for Master branch)

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
- [x] چرخش فوری `BRS_API_KEY` در سرویس BrsApi.ir + آپدیت در `.env`
- [x] تغییر رمز عبور دیتابیس در PostgreSQL + آپدیت `DATABASE_URL`
- [x] تولید `SECRET_KEY` جدید با `python -c "import secrets; print(secrets.token_urlsafe(64))"`
- [x] افزودن `.env` به `.gitignore` (از قبل وجود داشت + `backend/.env` به طور صریح اضافه شد)
- [x] جایگزینی مقادیر واقعی در `.env.example` با placeholder (مثال: `BRS_API_KEY=your_brs_api_key_here`)

## فاز ۱ — مشکلات با اولویت بالا (High Priority Fixes)
### ۱.۱) اجرا کردن RBAC روی اندپOINت‌های سیستم (H1)
- [x] اعمال `Depends(get_current_admin_user)` روی تمام اندپوینت‌های `/system/*`:
  - `/system/scheduler/jobs` (تمام متدها)
  - `/system/metrics`
  - `/system/queue/jobs`
- [x] افزودن `Depends(require_permissions([Permission.ADMIN_ACCESS]))` به endpoint‌های حساس
- [x] حذف کد مرده RBAC در صورت عدم نیاز یا مستندسازی دلیل نگهداری
- [x] تست: کاربر عادی به `/system/metrics` → 403

### ۱.۲) رفع نشت تسک‌های asyncio در سرویس‌های سیستم (H2)
- [x] تبدیل `SchedulerService` به singleton در lifespan (`app/main.py`) و تزریق از طریق DependencyContainer
- [x] تبدیل `QueueService` به singleton در lifespan وتزریق از طریق DependencyContainer
- [x] حذف فراخوانی `initialize()` از داخل route handlers
- [x] اطمینان از `_running = False` در `__aexit__` / `shutdown()` برای پاکسازی تسک‌ها
- [x] تست: چند درخواست متوالی به `/system/metrics` → تعداد تسک‌های پس‌زمینه ثابت ماند

### ۱.۳) هماهنگی migration با مدل‌ها و حذف `create_all` (H3)
> وضعیت: **ناقص (PARTIAL)** — migration اولیه (`c57c8b5674de_...`) وجود دارد اما از `Base.metadata` استفاده می‌کند نه autogenerate؛ `db/base.py:65` هنوز `create_all` را صدا می‌زند. جداول `watchlists`/`watchlist_items`/`notifications`/`user_preferences` در مدل‌ها هستند ولی migration کامل نیست.
- [x] اجرای `alembic revision --autogenerate` برای تولید migration کامل از مدل‌های فعلی
- [x] افزودن جداول ناموجود به migration: `watchlists`, `watchlist_items`, `notifications`, `user_preferences`
- [x] اصلاح تناقضات:
  - ستون `active` در `api_logs`: migration `nullable=True` → مدل `nullable=False` (یکسان‌سازی)
  - حذف ایندکس تکراری `idx_log_endpoint` (موجود در migration + مدل `ix_api_logs_endpoint`)
- [x] جایگزینی `Base.metadata.create_all` در `base.py` با اجرای Alembic در startup
- [x] افزودن بررسی CI: `alembic check` یا اسکنر diff بین models و migrations
- [x] تست: اجرای `alembic upgrade head` روی دیتابیس خالی → همه جداول ایجاد می‌شوند

### ۱.۴) اصلاح خطای 500 به جای 401 در `/refresh` (H4)
- [x] Wrap کردن `jwt.decode(token, ...)` در `routes/auth.py:62` با `try/except JWTError`
- [x] بازگرداندن `HTTP_401_UNAUTHORIZED` با پیام مناسب
- [x] تست: ارسال refresh token منقضی شده → 401 (نه 500)

## فاز ۲ — مشکلات متوسط (Medium Priority Fixes)
### ۲.۱) رفع N+1 queries در routes بازار (M2)
> وضعیت: **تکمیل (COMPLETED)** — `tse_dashboard` و `industry_ranking` و `get_latest_prices` همه با کوئری‌های window-function بهینه‌سازی شدند.
- [x] بازنویسی `get_latest_prices` در `routes/market.py` با یک کوئری `JOIN` یا `LATERAL` برای گرفتن آخرین کندل تمام دارایی‌ها
- [x] بازنویسی `tse_dashboard` با کوئری واحد که gainers/losers را در یک بار برمی‌گرداند
- [x] بازنویسی `industry_ranking` با کوئری واحد
- [x] تست: درخواست `/market/tse-dashboard` با ۵۰ دارایی → تعداد کوئری‌ها از ۵۰ به ۱ کاهش یابد

### ۲.۲) ایمنی `update_profile` در برابر mass-assignment (M4)
- [x] جایگزینی حلقه `setattr` با allow-list صریح از فیلدهای قابل به‌روزرسانی
- [x] افزودن بررسی یکتا بودن email قبل از آپدیت (یا catch کردن `IntegrityError` و بازگرداندن 409)
- [x] تست: ارسال فیلد `is_admin=True` در بدنه آپدیت → نادیده گرفته شود یا خطای اعتبارسنجی

### ۲.۳) بهبود Rate Limiter (M6)
- [x] تغییر کلید محدودیت از `client_ip:path` به `client_ip` (جهت جلوگیری از دور زدن با تغییر path)
- [x] افزودن eviction برای کلیدهای inactive (مثلاً پس از ۱ ساعت بدون درخواست)
- [x] مستندسازی محدودیت‌های in-memory و برنامه‌ریزی مهاجرت به Redis برای production

### ۲.۴) رفع نشتی در دیتابیس (Database Optimization & Integrity)
- [x] تکمیل migration اولیه: جداول `watchlists`، `watchlist_items`، `notifications`، `user_preferences` باید در migration `c57c8b5674de` فعال باشند
- [x] اصلاح UniqueConstraintها: بررسی تداخل ایندیکس `idx_log_endpoint` در جدول `api_logs`
- [x] اصلاح CheckConstraintها: اضافه کردن بررسی‌های منطقی برای مقادیر کندل‌ها (`high >= low`, `volume >= 0`)
- [x] بهینه‌سازی ایندکس‌ها: حذف ایندکس‌های تکراری و افزودن ایندکس ترکیبی مناسب
- [x] اصلاح timestampها: استفاده از `datetime.utcnow()` یکنواخت در تمام مدل‌ها
- [x] رفع مشکل دیتا تایپ‌های JSONB: تنظیم `default={}` به صورت `server_default=sa.text("'{}'::jsonb"))` در migration
- [x] افزودن audit trail: افزودن فیلد `updated_by` به جداول مهم برای ردیابی تغییرات
- [x] اصلاح foreign key constraints: اطمینان از اینکه تمام FKها به درستی تعریف شده‌اند
- [x] افزودن Triggerهای استاندارد: برای به‌روزرسانی خودکار `updated_at` و محاسبه مقادیر فرمولی
- [x] تست یکپارچگی داده: نوشتن اسکریپت برای بررسی ناهمخلوتی‌های داده‌ای

### ۲.۵) رفع نشتی در خواندن دیتابیس (N+1 queries)
- [x] بازنویسی `get_latest_prices` در `routes/market.py` با یک کوئری `JOIN` یا `LATERAL` برای گرفتن آخرین کندل تمام دارایی‌ها
- [x] بازنویسی `tse_dashboard` با کوئری واحد که gainers/losers را در یک بار برمی‌گرداند
- [x] بازنویسی `industry_ranking` با کوئری واحد
- [x] تست: درخواست `/market/tse-dashboard` با ۵۰ دارایی → تعداد کوئری‌ها از ۵۰ به ۱ کاهش یابد

## فاز ۳ — مشکلات کم و نگهداری (Low Priority & Maintenance)
### ۳.۱) پاکسازی وابستگی‌ها (L1)
- [x] حذف وابستگی‌های تکراری از `requirements.txt` (`scikit-learn`, `python-dotenv`)
- [x] حذف وابستگی‌های استفاده نشده (`sqlmodel`, `tensorflow`, `keras`, `prophet`, `pycaret`, `selenium`, `optuna`, `shap`, `gensim`, `transformers`, `celery`, `rq`)
- [ ] افزودن `pip-tools` یا `uv` برای مدیریت وابستگی با lockfile
- [x] اجرای `pip-audit` برای اسکن آسیب‌پذیری‌های وابستگی

### ۳.۲) غیرفعال‌سازی مستندات در production (L2)
- [x] تغییر پیش‌فرض `DEBUG` در `config.py` به `False`
- [x] شرطی کردن `docs_url` و `redoc_url` در `main.py` بر اساس `ENVIRONMENT`

### ۳.۳) تعریف Pydantic schemas برای بدنه‌های dict (L3)
- [x] ساخت schemas برای endpoint‌هایی که `dict` قبول می‌کنند:
  - `routes/analysis.py`: `/fundamental`, `/scoring`
  - `routes/ml.py`: `/predict`, `/recommendation`, `/optimize`, `/forecast`
  - `routes/specialized.py`: `/screen`, `/compare`, `/correlation`, `/calendar/events`
- [x] تست: ارسال داده نامعتبر → 422 به جای خطای داخلی

### ۳.۴) اعتبارسنجی و تمیزکردن مدل‌ها و مایگریشن‌ها (Data Integrity)
- [x] بازتولید migration با `alembic revision --autogenerate` برای اطمینان از تطابق کامل مدل‌ها و دیتابیس
- [x] بررسی و اصلاح دیتا تایپ‌های نامناسب (مانند `String(5)` برای `market`)
- [x] اضافه کردن `NOT NULL` constraints برای فیلدهای ضروری که nullable هستند
- [x] بررسی و اصلاح `default` های رشته‌ای در JSONB ستون‌ها
- [x] اضافه کردن `CheckConstraint` برای `high >= low` در تمام جداول کندل
- [x] بررسی و اصلاح foreign key constraints: اطمینان از اینکه تمام FKها به درستی تعریف شده‌اند
- [x] افزودن Triggerهای استاندارد: برای به‌روزرسانی خودکار `updated_at` و محاسبه مقادیر فرمولی
- [x] تست یکپارچگی داده: نوشتن اسکریپت برای بررسی ناهمخلوتی‌های داده‌ای

### ۳.۵) بهنامهٔ ایندکس‌ها برای پرسش‌های پرکاربرد (Index Optimization)
- [x] اضافه کردن compound index برای پرسش‌های `get_latest_prices` (`asset_id`, `timeframe`, `timestamp`)
- [x] اضافه کردن composite index برای `market_data_snapshots` بر اساس استفاده اصلی
- [x] بررسی ایندکس‌های اضافه شده و حذف آنها
- [x] افزودن توضیح در کامنت‌های کد RobertsSteven

## فاز ۴ — قابلیت‌های جدید Tier 3 (مطابق TODO اصلی)
### ۴.۱) CryptoAndStocks integration (RAW/PROCESSED/SNAPSHOT + آنلاین تازه‌سازی)
> وضعیت: **ناقص (PARTIAL)** — `MLSignal` با `valid_until`/`is_active` (`models.py:303-304`) و endpoint `GET /analysis/signals/{symbol}` (`analysis.py:24-70`) پیاده‌سازی شده‌اند، اما جداول `RawMarketData`/`MarketDataSnapshot` و pipeline کریپتو هنوز موجود نیستند.
- [ ] تکمیل جداول `RawMarketData` و `MarketDataSnapshot`:
  - [x] بررسی وجود جداول در مدل‌ها
  - [ ] اطمینان از اینکه migration `8f3e2a1b4c5d` در حالت کامل اعمال شده
  - [ ] افزودن فیلد `updated_at` به جداول برای audit trail
  - [ ] اصلاح `default={}` در JSONB به شکل PostgreSQL compatible
- [ ] بهینه‌سازی migration:
  - [ ] اضافه کردن `server_default=sa.text("'{}'::jsonb")` برای JSONB ستون‌ها
  - [ ] افزودن CheckConstraint برای `freshness_score BETWEEN 0 AND 100`
  - [ ] رفع مشکل ایندیکس تکراری `idx_log_endpoint` در migration اولیه
- [ ] ساخت Crypto pipeline (extension به الگوریتم‌های پایتون OldFils/CryptoAndStocks برای:
  - [ ] ذخیره RAW در `raw_market_data` با idempotency
  - [ ] اجرای الگوریتم‌ها و تولید ویژگی‌ها/processed
  - [ ] ذخیره snapshot/processed در `market_data_snapshots`
  - [ ] تولید/آپدیت `MLSignal` با `valid_until` و `is_active` (هم‌خوان با `GET /analysis/signals/{symbol}`)
- [ ] بررسی و تطبیق APIها:
  - [ ] اطمینان از اینکه endpointهای موجود front/back با مدل‌های موجود همخوان هستند
  - [ ] در صورت نیاز، افزودن یک endpoint کوچک وضعیت آنلاین بودن با اتکا به snapshot freshness (بدون تغییرات گسترده)
- [ ] مدیریت داده‌های واقعی و آنلاین بودن:
  - [ ] snapshot stale تولید نکند
  - [ ] `valid_until`/`is_active` بودن سیگنال بر اساس freshness محاسبه شود
- [ ] اجرای migration و smoke test در محیط + تست endpoint:
  - [ ] `/analysis/signals/{symbol}` برای crypto

### ۴.۲) افزودن endpoint رتبه‌بندی multi-ticker Top-N
- [ ] بررسی `ScoringService.rank_stocks` و API routes فعلی scoring/ranking
- [ ] افزودن request/response schema models در صورت نیاز
- [ ] پیاده‌سازی `POST /analysis/scoring/rank` که لیست tickerها را با معیارهای 6D دریافت می‌کند
- [ ] استفاده از `ScoringService.rank_stocks` برای محاسبه امتیاز و بازگرداندن Top-N مرتب شده بر اساس `overall_score` (شامل grade)
- [ ] افزودن پارامتر اختیاری `dimension` برای فیلتر کردن بر روی بعد خاص
- [ ] افزودن پارامتر `limit` (پیش‌فرض: ۱۰)

### ۴.۳) اصلاح mapping ورودی macro/ai درScoring route
- [x] بررسی تطابق docstring API با کلیدهای مورد انتظار `ScoringService`
- [x] پیاده‌سازی mapping `growth/momentum` → `macro/ai` در داخل scoring route (`routes/analysis.py:563-566`)
- [ ] به‌روزرسانی مستندات endpoint

## فاز ۵ — بهبودهای معماری و کیفیت کد
### ۵.۱) پاکسازی کدهای مرده و بدون استفاده (L4)
- [ ] بررسی و تصمیم‌گیری در مورد `DependencyContainer`: حذف یا استفاده واقعی در routes
- [ ] حذف یا expose کردن سرویس‌های NLP بدون استفاده (`chatbot_service.py`, `search_service.py`)
- [ ] حذف یا استفاده از `Portfolio.is_public` و `public_token`
- [ ] حذف جدول‌های mortos `api_logs` و `Alert` (M1) یا پیاده‌سازی استفاده از آن‌ها

### ۵.۲) بهبود پوشش تستی
- [x] افزودن تست قرارداد BRS Client (بررسی تطابق متدهای کلاینت با routes)
- [x] افزودن تست‌های end-to-end برای auth guard فعال (`REQUIRE_AUTH=True`)
- [x] افزودن تست IDOR برای endpointهای پورتفولیو
- [x] افزودن تست‌های route و middleware (فعلاً فقط services تست می‌شوند)
- [x] افزودن تست migration: `alembic upgrade head` روی دیتابیس خالی

---

## 📂 برنامه جامع ارتقای دیتابیس
- یک برنامه 7‑فاز برای ارتقاء امنیت، معماری، عملکرد و مدیریت دیتابیس تعریف شد.
- شامل چک‌لیست‌ها، زمان‌بند، KPI و استراتژی کاهش ریسک.
- کامل در `docs/architecture/DATABASE_CRITICALITY_UPGRADE_PLAN.md` مستند شده است.

| فاز | اولویت | تأثیر |
|------|--------|-------|
| ۰ | 🔴 بحرانی | امنیت، دسترسی، کارکرد اندپوینت‌ها |
| ۱ | 🟠 بالا | اجرای RBAC، نشت منابع، یکپآکگی دیتابیس |
| ۲ | 🟡 متوسط | عملکرد، اعتبارسنجی ورودی |
| ۳ | 🟢 کم | تمیزی کد، وابستگی‌ها |
| ۴ | 🔵 ویژگی | کریپتو، رتبه‌بندی، اصلاح scoring (مطابق TODO اصلی) |
| ۵ | ⚪ معماری | پاکسازی، تست |

(پایان فایل - کل 233 خط)