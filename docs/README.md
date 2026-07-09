# 🌊 BedaanWaves - یک پلتفرم یکپارچه‌ی تحلیل بازار سرمایه

**نسخه**: 1.0.0  
**زبان‌های اصلی**: Python (Backend) + TypeScript/Next.js (Frontend)  
**دیتابیس**: PostgreSQL 14+  
**وضعیت**: Development (توسعه محلی)

---

## 📋 فهرست مطالب

- [معرفی](#معرفی)
- [ویژگی‌های اصلی](#ویژگی‌های-اصلی)
- [آرکیتکچر سیستم](#آرکیتکچر-سیستم)
- [نصب و راه‌اندازی](#نصب-و-راه‌اندازی)
- [فایل‌های مرجع](#فایل‌های-مرجع)
- [ساختار پروژه](#ساختار-پروژه)
- [استفاده](#استفاده)
- [توسعه](#توسعه)

---

## 🎯 معرفی

**BedaanWaves** یک پلتفرم یکپارچه برای:
- 📊 دریافت و ذخیره‌سازی داده‌های بازار سرمایه ایران
- 🤖 تحلیل ML و تولید سیگنال‌های معاملاتی
- 📈 نمایش داشبورد‌های تحلیلی در زمان واقعی
- 💼 مدیریت پورتفولیو و تحلیل ریسک

این پروژه از صفر توسعه یافته و کاملاً مستقل است.

---

## ✨ ویژگی‌های اصلی

### Backend (FastAPI + Python)
- ✅ اتصال مستقیم به API پلتفرم **BrsApi.ir**
- ✅ ذخیره‌سازی داده‌های OHLCV در PostgreSQL
- ✅ API RESTful برای دسترسی به داده‌ها
- ✅ WebSocket برای به‌روزرسانی لحظه‌ای
- ✅ سیستم ML برای تولید سیگنال‌ها

### Frontend (Next.js + React)
- ✅ داشبورد مدرن و ریسپانسیو
- ✅ نمودارهای تاریخی (Candlestick, Line)
- ✅ لیست نمادها و جستجو
- ✅ پورتفولیو مدیریت
- ✅ سیگنال‌های خریداری و فروش

### Database (PostgreSQL)
- ✅ Schema یکپارچه برای تمام داده‌ها
- ✅ Indexing بهینه برای کوئری‌های سریع
- ✅ Partitioning برای مدیریت داده‌های بزرگ

---

## 🏗️ آرکیتکچر سیستم

```
┌─────────────────────────────────────────────────┐
│         Frontend (Next.js + React)              │
│        http://localhost:3005                    │
└──────────────┬──────────────────────────────────┘
               │ HTTP/WebSocket
┌──────────────▼──────────────────────────────────┐
│         Backend API (FastAPI)                   │
│        http://localhost:3000                    │
│  • Market data endpoints                        │
│  • Analysis/signals endpoints                   │
│  • Portfolio endpoints                          │
└──────────────┬──────────────────────────────────┘
               │ SQL
┌──────────────▼──────────────────────────────────┐
│       Database (PostgreSQL)                     │
│      localhost:5432/bedaanwaves_db              │
│  • Assets & symbols                             │
│  • Price candles (OHLCV)                        │
│  • ML signals                                   │
│  • User portfolios                              │
└──────────────┬──────────────────────────────────┘
               │ HTTP
┌──────────────▼──────────────────────────────────┐
│    External APIs                                │
│  • BrsApi.ir (بورس تهران)                      │
│  • Crypto exchanges (future)                    │
│  • International markets (future)               │
└─────────────────────────────────────────────────┘
```

---

## 📦 نصب و راه‌اندازی

### پیش‌نیازها

- **Python 3.9+** برای Backend
- **Node.js 18+** برای Frontend
- **PostgreSQL 14+** برای Database
- **pip** و **npm** برای Package Management

### مرحله 1: راه‌اندازی PostgreSQL

#### ویندوز:
```bash
# 1. نصب PostgreSQL از: https://www.postgresql.org/download/windows/
# 2. اجرای pgAdmin یا Command Line:

createdb bedaanwaves_db

# ورود به PostgreSQL
psql -U postgres

# در PostgreSQL console:
\c bedaanwaves_db

# اجرای مهاجری‌های پایگاه‌داده (بعداً)
```

#### Linux/Mac:
```bash
# نصب PostgreSQL
brew install postgresql@14  # Mac
sudo apt-get install postgresql postgresql-contrib  # Ubuntu

# شروع سرویس
brew services start postgresql@14  # Mac
sudo systemctl start postgresql  # Linux

# ایجاد پایگاه‌داده
createdb bedaanwaves_db
```

### مرحله 2: راه‌اندازی Backend

```bash
# 1. بروز به دایرکتوری پروژه
cd E:\Shakour\BedaanProjects\BedaanWaves

# 2. ایجاد Virtual Environment
python -m venv venv

# 3. فعال‌سازی Virtual Environment
# ویندوز:
venv\Scripts\activate

# Linux/Mac:
source venv/bin/activate

# 4. نصب وابستگی‌ها
pip install -r backend/requirements.txt

# 5. تنظیم متغیرهای محیط
# فایل backend/.env را با اطلاعات PostgreSQL خود تعدیل کنید

# 6. اجرای Backend
python -m uvicorn backend.app.main:app --reload --port 3000
```

Backend اکنون در `http://localhost:3000` قابل دسترسی است.

### مرحله 3: راه‌اندازی Frontend

```bash
# 1. بروز به دایرکتوری Frontend
cd frontend

# 2. نصب وابستگی‌ها
npm install

# 3. اجرای سرور توسعه
npm run dev

# یا برای محیط تولید:
npm run build
npm run start
```

Frontend اکنون در `http://localhost:3005` قابل دسترسی است.

---

## 📚 فایل‌های مرجع

پروژه بر اساس این فایل‌های توثیق‌شده ساخته شده است:

| فایل | موضوع | مکان |
|------|-------|------|
| **BourseApi.txt** | مستندات API BrsApi.ir | `docs/init_docs/BourseApi.txt` |
| **postgre.txt** | تنظیمات PostgreSQL | `docs/init_docs/postgre.txt` |
| **FrontEnd.txt** | معماری Frontend | `docs/init_docs/FrontEnd.txt` |
| **Source_Within.txt** | کتابخانه علمی شاکاموتو | `docs/init_docs/Source_Within.txt` |

### استفاده از فایل‌های مرجع:

```python
# 1. برای اتصال BrsApi:
from backend.services.brs_service import BrsApiClient

client = BrsApiClient()
symbols = await client.get_all_symbols()

# 2. برای تنظیمات دیتابیس:
# backend/.env را مطابق postgre.txt تنظیم کنید

# 3. برای رابط کاربری:
# Frontend را براساس معماری FrontEnd.txt بسازید
```

---

## 📁 ساختار پروژه

```
BedaanWaves/
├── backend/                          # FastAPI Backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI application
│   │   ├── core/
│   │   │   └── config.py             # Configuration
│   │   ├── db/
│   │   │   └── base.py               # Database setup
│   │   ├── models/
│   │   │   └── models.py             # SQLAlchemy models
│   │   ├── schemas/
│   │   │   └── schemas.py            # Pydantic schemas
│   │   ├── services/
│   │   │   └── brs_service.py        # BrsApi integration
│   │   ├── api/
│   │   │   └── routes/
│   │   │       ├── market.py         # Market endpoints
│   │   │       └── analysis.py       # Analysis endpoints
│   │   └── ml/                       # ML services
│   ├── requirements.txt              # Python dependencies
│   ├── .env                          # Environment variables
│   ├── .env.example                  # Example env
│   └── tests/                        # Test files
│
├── frontend/                         # Next.js Frontend
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx              # Home page
│   │   │   ├── layout.tsx            # Root layout
│   │   │   ├── dashboard/            # Dashboard pages
│   │   │   └── api/                  # API routes
│   │   ├── components/               # React components
│   │   ├── services/                 # API clients
│   │   ├── stores/                   # Zustand stores
│   │   └── hooks/                    # Custom hooks
│   ├── package.json
│   └── tsconfig.json
│
├── database/                         # Database scripts
│   ├── schema.sql                    # Database schema
│   ├── init.sql                      # Initialization
│   └── migrations/                   # Alembic migrations
│
├── docs/                             # Documentation
│   └── init_docs/                    # Reference files
│       ├── BourseApi.txt
│       ├── postgre.txt
│       ├── FrontEnd.txt
│       └── Source_Within.txt
│
├── scripts/                          # Helper scripts
│   ├── setup_db.py                   # Database setup
│   ├── seed_data.py                  # Sample data
│   └── backup_db.sh                  # Database backup
│
├── .gitignore
├── package.json                      # Root package.json
├── README.md                         # This file
└── docker-compose.yml                # Docker (optional)
```

---

## 🚀 استفاده

### 1. دریافت داده‌های بورسی

```bash
# برای دریافت نمادهای بورسی:
curl http://localhost:3000/api/v1/market/symbols

# برای دریافت تاریخچه قیمت:
curl "http://localhost:3000/api/v1/market/price-history?symbol=FSPD"

# برای دریافت سیگنال‌های ML:
curl "http://localhost:3000/api/v1/analysis/signals/FSPD"
```

### 2. استفاده در Python

```python
import asyncio
from backend.services.brs_service import BrsApiClient

async def main():
    client = BrsApiClient()
    
    # دریافت تمام نمادها
    symbols = await client.get_all_symbols()
    print(f"تعداد نمادها: {len(symbols)}")
    
    # دریافت تاریخچه قیمت
    history = await client.get_price_history("FSPD")
    print(f"رکوردهای قیمت: {len(history)}")
    
    await client.close()

asyncio.run(main())
```

### 3. استفاده در Frontend

```tsx
// pages/market.tsx
import { useQuery } from '@tanstack/react-query';
import { BedaanClient } from '@/services/api-client';

const client = new BedaanClient();

export default function MarketPage() {
  const { data: symbols } = useQuery({
    queryKey: ['symbols'],
    queryFn: () => client.getSymbols(),
  });

  return (
    <div>
      <h1>نمادهای بورسی</h1>
      {symbols?.map(symbol => (
        <div key={symbol.id}>{symbol.name}</div>
      ))}
    </div>
  );
}
```

---

## 👨‍💻 توسعه

### ایجاد شاخه‌ی جدید

```bash
# شاخه‌ی جدید برای ویژگی‌ی جدید
git checkout -b feature/new-feature-name

# شاخه‌ی جدید برای رفع باگ
git checkout -b bugfix/bug-name
```

### کد‌نویسی

```bash
# Backend:
# - رعایت PEP 8
# - استفاده از Type Hints
# - نوشتن Docstrings

# Frontend:
# - استفاده از TypeScript
# - رعایت ESLint rules
# - نوشتن unit tests
```

### تست‌ها

```bash
# Backend tests
cd backend
pytest tests/

# Frontend tests
cd frontend
npm run test
```

### Git Workflow

```bash
# 1. انجام تغییرات
git add .

# 2. Commit
git commit -m "feat: توضیح تغییرات"

# 3. Push
git push origin feature/new-feature

# 4. Pull Request
# (در GitHub)
```

---

## 🔧 مشکلات شایع

### PostgreSQL Connection Error
```
خطا: could not connect to server
حل:
1. مطمئن شوید PostgreSQL در حال اجرا است
2. تنظیمات DATABASE_URL را بررسی کنید
3. Password خود را به .env اضافه کنید
```

### API Not Responding
```
خطا: Connection refused localhost:3000
حل:
1. Backend را دوباره اجرا کنید
2. Port 3000 را بررسی کنید
3. Log‌ها را برای خطاها بررسی کنید
```

### Frontend Build Error
```
خطا: npm install fails
حل:
1. node_modules را حذف کنید
2. package-lock.json را حذف کنید
3. npm install را دوباره اجرا کنید
```

---

## 📞 تماس و پشتیبانی

برای سوالات یا مشکلات:
- GitHub Issues: [BedaanWaves Issues](https://github.com/your-repo/issues)
- Email: [your-email@example.com]

---

## 📄 مجوز

این پروژه تحت مجوز MIT منتشر شده است.

---

**توسعه‌دهندگان**: BedaanWaves Team  
**آخرین به‌روزرسانی**: July 2026  
**نسخه فعلی**: 1.0.0
