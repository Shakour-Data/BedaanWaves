# 🚀 راهنمای شروع سریع BedaanWaves

**زمان تخمین‌ی**: 15 دقیقه  
**سختی**: آسان

---

## ✅ بررسی نیازمندی‌ها

```bash
# Python بررسی
python --version  # باید 3.9+ باشد

# Node.js بررسی
node --version   # باید 18+ باشد

# PostgreSQL بررسی
psql --version   # باید 14+ باشد
```

---

## 1️⃣ تنظیم PostgreSQL (5 دقیقه)

### ویندوز (با pgAdmin):

1. **دانلود و نصب PostgreSQL**:
   - رفتن به https://www.postgresql.org/download/windows/
   - نصب نسخه 14 یا بالاتر

2. **اجرای pgAdmin**:
   - برنامه pgAdmin را باز کنید
   - لاگین با `postgres` / `postgres`

3. **ایجاد دیتابیس**:
   ```
   - سمت راست click روی "Databases"
   - "Create" → "Database"
   - نام: bedaanwaves_db
   - Owner: postgres
   - "Save"
   ```

4. **اجرای Script اولیه**:
   ```
   - انتخاب bedaanwaves_db
   - "Tools" → "Query Tool"
   - Ctrl+O و باز کردن database/init.sql
   - اجرای Query (F5)
   ```

### Linux/Mac:

```bash
# ایجاد دیتابیس
createdb bedaanwaves_db

# اجرای اولیه‌سازی
psql bedaanwaves_db < database/init.sql

# تأیید
psql bedaanwaves_db -c "SELECT COUNT(*) FROM bedaan_data.assets;"
```

---

## 2️⃣ راه‌اندازی Backend (5 دقیقه)

```bash
# 1. بروز به پروژه
cd E:\Shakour\BedaanProjects\BedaanWaves

# 2. ایجاد Virtual Environment
python -m venv venv

# 3. فعال‌سازی (ویندوز)
venv\Scripts\activate

# یا (Linux/Mac)
source venv/bin/activate

# 4. نصب وابستگی‌ها
pip install -r backend/requirements.txt

# 5. اجرای Backend
python -m uvicorn backend.app.main:app --reload --port 3000
```

**نتیجه تأیید**:
- پیام: `Uvicorn running on http://0.0.0.0:3000`
- اجازه‌ی دسترسی به: http://localhost:3000/health
- Swagger Docs: http://localhost:3000/api/v1/docs

---

## 3️⃣ راه‌اندازی Frontend (3 دقیقه)

### در Terminal جدید:

```bash
# 1. بروز به Frontend
cd frontend

# 2. نصب وابستگی‌ها
npm install

# 3. اجرای سرور توسعه
npm run dev
```

**نتیجه تأیید**:
- پیام: `ready - started server on 0.0.0.0:3005`
- رفتن به: http://localhost:3005

---

## 🎉 شروع استفاده

### 1. تست Backend API

```bash
# در Terminal جدید:

# دریافت نمادها
curl http://localhost:3000/api/v1/market/symbols

# دریافت سیگنال‌ها
curl "http://localhost:3000/api/v1/analysis/signals-summary"
```

### 2. بررسی Frontend

- باز کردن http://localhost:3005
- مشاهده‌ی نمادهای بورسی
- کلیک روی نماد برای نمایش جزئیات

---

## 🔑 اطلاعات اتصال

| سرویس | آدرس | توضیح |
|-------|------|-------|
| **Backend API** | http://localhost:3000 | FastAPI Server |
| **Frontend** | http://localhost:3005 | Next.js Client |
| **Database** | localhost:5432 | PostgreSQL |
| **API Docs** | http://localhost:3000/api/v1/docs | Swagger UI |

---

## ⚙️ متغیرهای محیط (اختیاری)

اگر نیاز به تغییر داشتید:

```bash
# backend/.env
DATABASE_URL=postgresql://postgres:password@localhost:5432/bedaanwaves_db
BRS_API_KEY=FreeSV0E1LSgB9RDjuf0QorSLViX8pPG
```

---

## 🐛 حل مشکلات

### مشکل: "psycopg2: could not translate host name"

**حل**:
```bash
# متصل شوید به خودتان
export DATABASE_URL=postgresql://postgres:password@127.0.0.1:5432/bedaanwaves_db
```

### مشکل: "Port 3000 already in use"

**حل**:
```bash
# استفاده از port دیگر
python -m uvicorn backend.app.main:app --port 3001 --reload
```

### مشکل: "npm: command not found"

**حل**:
- Node.js را دوباره نصب کنید
- Restart Terminal را اجرا کنید

---

## 📚 مراحل بعدی

1. **بررسی API Endpoints**:
   ```bash
   curl http://localhost:3000/api/v1/docs
   ```

2. **افزودن داده‌های آزمایشی**:
   ```bash
   python scripts/seed_data.py
   ```

3. **تست Frontend**:
   - نمادهای بورسی را جستجو کنید
   - یک نماد را انتخاب کنید
   - نمودار قیمت را مشاهده کنید

4. **خواندن مستندات**:
   - `backend/app/api/routes/market.py` برای API
   - `frontend/src/components/` برای Components
   - `database/init.sql` برای Schema

---

## 📖 منابع مفید

- **BrsApi.ir**: https://brsapi.ir
- **FastAPI**: https://fastapi.tiangolo.com
- **Next.js**: https://nextjs.org
- **PostgreSQL**: https://www.postgresql.org

---

## ✨ نکات مهم

✅ **انجام شده**:
- ✓ Backend API کامل
- ✓ Database Schema آماده
- ✓ Frontend Base
- ✓ BrsApi Integration

⏳ **مراحل بعدی**:
- [ ] اضافه کردن تست‌ها
- [ ] پیاده‌سازی ویژگی‌های پیشرفته
- [ ] استقرار (Deployment)

---

**اگر مشکلی پیش آمد**:
1. لاگ‌های Terminal را بررسی کنید
2. Database connection را بررسی کنید
3. PORT conflict را بررسی کنید

**موفق باشید! 🎉**
