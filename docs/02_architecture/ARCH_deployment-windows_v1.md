# BedaanWaves - Native Windows Setup Guide
## Complete Native Windows Setup Guide (Without Docker)

**Version:** 1.0.0  
**Last Updated:** 2026-09-04  
**Target OS:** Windows 10/11 (64-bit)

---

## 📋 Table of Contents

1. [خلاصه پروژه](#خلاصه-پروژه)
2. [پیش‌نیازها](#پیش‌نیازها)
3. [مرحله 1: نصب PostgreSQL](#مرحله-1-نصب-postgresql)
4. [مرحله 2: نصب Redis](#مرحله-2-نصب-redis)
5. [مرحله 3: نصب Python](#مرحله-3-نصب-python)
6. [مرحله 4: نصب Node.js](#مرحله-4-نصب-nodejs)
7. [مرحله 5: پیکربندی پروژه](#مرحله-5-پیکربندی-پروژه)
8. [مرحله 6: اجرای پروژه](#مرحله-6-اجرای-پروژه)
9. [عیب‌یابی](#عیب‌یابی)
10. [منابع](#منابع)

---

## 🚀 Project Summary

**BedaanWaves** یک پلتفرم تحلیل سهام NASDAQ است که شامل:

- **Backend:** FastAPI (Python) - پورت 8000
- **Frontend:** Next.js (React/TypeScript) - پورت 3005
- **Database:** PostgreSQL - پورت 5432
- **Cache:** Redis - پورت 6379

---

## ⚙️ Prerequisites

### Hardware

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 4 cores | 8 cores |
| RAM | 8 GB | 16 GB |
| Disk | 50 GB SSD | 100 GB SSD |

### Software

| Component | Version | Download |
|-----------|---------|----------|
| Windows | 10/11 (64-bit) | [Windows](https://www.microsoft.com/windows) |
| PostgreSQL | 15+ | [Download](https://www.postgresql.org/download/windows/) |
| Redis | 7+ | [Memurai](https://www.memurai.com/download) |
| Python | 3.11+ | [Download](https://www.python.org/downloads/) |
| Node.js | 20+ (LTS) | [Download](https://nodejs.org/) |

---

## 📦 Step 1: Install PostgreSQL

### 1.1 Download and Install

1. به [PostgreSQL Downloads](https://www.postgresql.org/download/windows/) بروید
2. **Windows x86-64** را دانلود کنید
3. فایل `.exe` را اجرا کنید

### 1.2 Installation Settings

در طول نصب، این مقادیر را وارد کنید:

```
Installation Directory: C:\Program Files\PostgreSQL\15
Data Directory: C:\Program Files\PostgreSQL\15\data
Password: YOUR_SECURE_PASSWORD  (را به خاطر بسپارید!)
Port: 5432  (پیش‌فرض)
Locale: English, United States
```

### 1.3 Create Database

پس از نصب، Command Prompt (CMD) را به صورت Administrator باز کنید:

```cmd
# اضافه کردن PostgreSQL به PATH
set PATH=%PATH%;C:\Program Files\PostgreSQL\15\bin

# تست اتصال
psql -U postgres -c "SELECT version();"

# ایجاد دیتابیس
psql -U postgres -c "CREATE DATABASE bedaanwaves_db;"

# بررسی
psql -U postgres -l
```

### 1.4 Firewall Settings

اگر Windows Defender Firewall فعال است:

```powershell
# باز کردن پورت 5432
netsh advfirewall firewall add rule name="PostgreSQL" dir=in action=allow protocol=tcp localport=5432
```

### 1.5 Troubleshooting

| Issue | Solution |
|------|--------|
| "Connection refused" | PostgreSQL service را بررسی کنید: `services.msc` |
| "password authentication failed" | رمز عبور را بررسی کنید در `pg_hba.conf` |
| "database does not exist" | دیتابیس را با `createdb` ایجاد کنید |

---

## 📦 Step 2: Install Redis

### Option 1: Memurai (Recommended)

**Memurai** بهترین گزینه Redis برای ویندوز است.

#### 2.1.1 Download and Install

1. به [Memurai Downloads](https://www.memurai.com/download) بروید
2. نسخه **Developer Edition** را دانلود کنید (رایگان)
3. فایل `.msi` را اجرا کنید

#### 2.1.2 Installation Settings

```
Installation Directory: C:\Program Files\Memurai
Data Directory: C:\ProgramData\Memurai
Port: 6379 (default)
Start Service: Yes
```

#### 2.1.3 Verify Installation

```powershell
# بررسی سرویس
Get-Service Memurai*

# تست اتصال
redis-cli ping
# Expected: PONG
```

### Option 2: Redis for Windows (Microsoft Archive)

اگر Memurai در دسترس نیست:

#### 2.2.1 Download

1. به [Redis Windows Releases](https://github.com/microsoftarchive/redis/releases) بروید
2. آخرین نسخه را دانلود کنید (مثلاً `Redis-x64-3.0.504.msi`)
3. فایل `.msi` را اجرا کنید

#### 2.2.2 Settings

```
Port: 6379
Max Memory: 256MB (for cache)
Add to PATH: Yes
```

### 2.3 Configure Redis

فایل پیکربندی ما در این مسیر است:
```
deployment\redis\redis.conf
```

اگر از Memurai استفاده می‌کنید، این فایل را کپی کنید:
```powershell
Copy-Item "deployment\redis\redis.conf" "C:\ProgramData\Memurai\redis.conf"
```

### 2.4 Final Verification

```powershell
# اتصال به Redis
redis-cli

# داخل Redis CLI:
127.0.0.1:6379> PING
PONG

# ذخیره مقدار
127.0.0.1:6379> SET test "Hello Redis"
OK

# بازیابی مقدار
127.0.0.1:6379> GET test
"Hello Redis"

# خروج
127.0.0.1:6379> EXIT
```

---

## 📦 Step 3: Install Python

### 3.1 Download and Install

1. به [Python Downloads](https://www.python.org/downloads/) بروید
2. **Python 3.11+** را دانلود کنید (Windows installer 64-bit)
3. فایل `.exe` را اجرا کنید

### 3.2 Installation Settings

**⚠️ مهم: این گزینه‌ها را انتخاب کنید:**

```
☑ Add Python to PATH (بسیار مهم!)
☑ Install pip (default)
☑ Install tcl/tk and IDLE (optional)
☐ Create shortcuts (optional)

Customize installation:
  Documentation: Yes
  pip: Yes
  tcl/tk and IDLE: Optional
  Python test suite: Optional
  py launcher: Yes
  for all users: Yes (recommended)

Advanced Options:
  ☑ Install for all users
  ☐ Associate files with Python (optional)
  ☐ Create shortcuts (optional)
  ☑ Add Python to environment variables
  ☐ Precompile standard library (optional)
  ☐ Download debugging symbols (optional)
  ☐ Download debug binaries (optional)
```

### 3.3 Verify Installation

```powershell
# بستن و باز کردن PowerShell (برای بارگذاری PATH)

# بررسی نسخه Python
python --version
# Expected: Python 3.11.x or higher

# بررسی pip
pip --version

# بررسی مسیر Python
where python
```

### 3.4 Troubleshooting

| Issue | Solution |
|------|--------|
| "python is not recognized" | Python به PATH اضافه نشده - نصب را با "Add to PATH" اجرا کنید |
| "pip is not recognized" | pip نصب نشده - Python را دوباره نصب کنید |
| "Permission denied" | PowerShell را به صورت Administrator اجرا کنید |

---

## 📦 Step 4: Install Node.js

### 4.1 Download and Install

1. به [Node.js Downloads](https://nodejs.org/) بروید
2. **LTS (Long Term Support)** را دانلود کنید (Node.js 20.x)
3. فایل `.msi` را اجرا کنید

### 4.2 Installation Settings

```
Destination Folder: C:\Program Files\nodejs

Features:
  ☑ Node.js runtime
  ☑ npm package manager
  ☑ Online documentation shortcuts (optional)
  ☑ Add to PATH

☐ Automatically install necessary tools (optional - requires 3GB)
```

### 4.3 Verify Installation

```powershell
# بستن و باز کردن PowerShell

# بررسی Node.js
node --version
# Expected: v20.x.x

# بررسی npm
npm --version
# Expected: 10.x.x

# بررسی مسیر
where node
where npm
```

### 4.4 npm Settings (Optional)

برای بهبود سرعت دانلود:

```powershell
# استفاده از registry سریع‌تر
npm config set registry https://registry.npmmirror.com

# یا registry اصلی
npm config set registry https://registry.npmjs.org

# بررسی تنظیمات
npm config list
```

---

## 📦 Step 5: Configure Project

### 5.1 Clone or Extract Project

```powershell
# اگر از git استفاده می‌کنید
git clone https://github.com/your-repo/bedaanwaves.git
cd bedaanwaves

# یا اگر فایل ZIP دارید
# Extract to: C:\Projects\bedaanwaves
cd C:\Projects\bedaanwaves
```

### 5.2 Configure Backend

#### 5.2.1 Create `.env` File

```powershell
cd backend

# کپی از فایل نمونه
copy .env.example .env

# یا ایجاد دستی
notepad .env
```

#### 5.2.2 `.env` File Contents

```env
# Application
APP_NAME=BedaanWaves
APP_VERSION=1.0.0
DEBUG=True
ENVIRONMENT=development

# Database (PostgreSQL)
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/bedaanwaves_db
DB_HOST=localhost
DB_PORT=5432
DB_NAME=bedaanwaves_db
DB_USER=postgres
DB_PASSWORD=YOUR_PASSWORD
DATABASE_ECHO=False
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10
DATABASE_POOL_TIMEOUT=30
DATABASE_POOL_RECYCLE=3600

# Redis & Cache
REDIS_URL=redis://localhost:6379/0
CACHE_ENABLED=True
CACHE_BACKEND=redis
CACHE_TTL=3600
CACHE_MAX_SIZE=1000
CACHE_TTL_MINUTES=60
CACHE_SCORE_TTL_HOURS=24
CACHE_API_RESPONSE_TTL_MINUTES=5
SYMBOL_CACHE_TTL=3600

# API Configuration
API_V1_STR=/api/v1
API_HOST=0.0.0.0
API_PORT=8000
API_VERSION=1.0.0
API_TITLE=BedaanWaves API
DOCS_URL=/api/v1/docs
REDOC_URL=/api/v1/redoc
OPENAPI_URL=/api/v1/openapi.json
ENABLE_DOCS=True

# Security & Authentication
SECRET_KEY=your-very-secure-secret-key-minimum-64-characters-long
JWT_SECRET=your-very-secure-jwt-secret-key-minimum-64-characters-long
ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
PASSWORD_MIN_LENGTH=8
ENABLE_HTTPS=False
REQUIRE_AUTH=False

# Rate Limiting
RATE_LIMIT_ENABLED=True
RATE_LIMIT_REQUESTS_PER_MINUTE=100

# CORS Configuration
CORS_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3005", "http://127.0.0.1:3005"]
CORS_ALLOW_CREDENTIALS=True
CORS_ALLOW_METHODS=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
CORS_ALLOW_HEADERS=["*"]

# Logging & Monitoring
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE_ENABLED=True
LOG_FILE_PATH=./logs/bedaanwaves.log
LOG_ROTATION=midnight
LOG_RETENTION_DAYS=30
METRICS_ENABLED=True
```

**⚠️ مهم:** مقادیر زیر را تغییر دهید:
- `YOUR_PASSWORD`: رمز عبور PostgreSQL
- `SECRET_KEY`: کلید تصادفی قوی (حداقل 64 کاراکتر)
- `JWT_SECRET`: کلید JWT تصادفی قوی (حداقل 64 کاراکتر)

### 5.3 Configure Frontend

#### 5.3.1 Check Configuration Files

```powershell
cd ..\frontend

# بررسی فایل .env.local
if (Test-Path .env.local) {
    Get-Content .env.local
} else {
    # ایجاد فایل
    @"
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_APP_ENV=development
"@ | Out-File -FilePath .env.local -Encoding utf8
}
```

---

## 🚀 Step 6: Run Project

### 6.1 Method 1: Use Automatic Script (Recommended)

```powershell
# بازگشت به ریشه پروژه
cd ..\..

# اجرای اسکریپت نصب وابستگی‌ها
.\scripts\install-dependencies.ps1

# پس از نصب موفقیت‌آمیز وابستگی‌ها، اجرای پروژه
.\scripts\setup-windows.ps1
```

### 6.2 Method 2: Manual Execution

اگر می‌خواهید هر سرویس را جداگانه اجرا کنید:

#### 6.2.1 PostgreSQL

```powershell
# بررسی وضعیت سرویس
Get-Service postgresql*

# شروع سرویس
Start-Service postgresql*

# یا از طریق Services Manager
services.msc
```

#### 6.2.2 Redis

```powershell
# اگر Memurai نصب کرده‌اید
Get-Service Memurai*
Start-Service Memurai*

# یا با redis-server مستقیم
redis-server "C:\ProgramData\Memurai\redis.conf"
```

#### 6.2.3 Backend

```powershell
cd backend

# ایجاد محیط مجازی (اگر ایجاد نشده)
python -m venv .venv

# فعال‌سازی
.\.venv\Scripts\Activate.ps1

# نصب وابستگی‌ها
pip install -r requirements.txt

# اجرای API
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 6.2.4 Frontend

```powershell
cd frontend

# نصب وابستگی‌ها (اگر نصب نشده)
npm install

# اجرای سرور توسعه
npm run dev
```

### 6.3 Access Services

پس از راه‌اندازی موفق:

| Service | URL | Description |
|---------|-----|-------------|
| Frontend App | http://localhost:3005 | Main application |
| Backend API | http://localhost:8000 | FastAPI backend |
| API Documentation | http://localhost:8000/api/v1/docs | Swagger UI |
| Alternative Docs | http://localhost:8000/api/v1/redoc | ReDoc |
| PostgreSQL | localhost:5432 | Database |
| Redis | localhost:6379 | Cache |

---

## 🔧 Troubleshooting

### Common Issues

#### 1. "Port already in use"

```powershell
# یافتن پروسه استفاده‌کننده از پورت
netstat -ano | findstr :5432

# Kill process
Stop-Process -Id <PID>
```

#### 2. "Connection refused" to PostgreSQL

```powershell
# بررسی سرویس
Get-Service postgresql*

# شروع مجدد
Restart-Service postgresql*

# بررسی لاگ‌ها
Get-EventLog -LogName Application -Source PostgreSQL -Newest 10
```

#### 3. Redis connection errors

```powershell
# بررسی سرویس Memurai
Get-Service Memurai*

# یافتن redis-server
Get-Process redis-server -ErrorAction SilentlyContinue

# تست اتصال
redis-cli ping
```

#### 4. Python import errors

```powershell
cd backend

# فعال‌سازی venv
.\.venv\Scripts\Activate.ps1

# ارتقای pip
python -m pip install --upgrade pip

# نصب مجدد وابستگی‌ها
pip install -r requirements.txt --force-reinstall
```

#### 5. npm install fails

```powershell
cd frontend

# پاک کردن node_modules
Remove-Item -Recurse -Force node_modules
Remove-Item package-lock.json -ErrorAction SilentlyContinue

# نصب مجدد
npm install
```

---

## 📚 Resources

### Useful Links

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Redis Documentation](https://redis.io/documentation)
- [Memurai Documentation](https://docs.memurai.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)

### Useful Commands

```powershell
# اسکریپت کمکی
.\scripts\setup-windows.ps1 -Action status    # بررسی وضعیت
.\scripts\setup-windows.ps1 -Action stop      # توقف سرویس‌ها
.\scripts\setup-windows.ps1                   # شروع سرویس‌ها

# دستورات PostgreSQL
psql -U postgres -c "\l"                        # لیست دیتابیس‌ها
psql -U postgres -c "\dt"                       # لیست جداول
psql -U postgres bedaanwaves_db                 # اتصال به دیتابیس

# دستورات Redis
redis-cli ping                                  # تست اتصال
redis-cli INFO                                  # اطلاعات سرور
redis-cli KEYS "*"                              # لیست کلیدها
redis-cli FLUSHALL                              # پاک کردن همه (احتیاط!)
```

---

## ✅ Installation Checklist

- [ ] PostgreSQL 15+ نصب شده و سرویس در حال اجرا است
- [ ] دیتابیس `bedaanwaves_db` ایجاد شده است
- [ ] Redis (Memurai یا redis-windows) نصب شده و سرویس در حال اجرا است
- [ ] Python 3.11+ نصب شده و به PATH اضافه شده است
- [ ] Node.js 20+ نصب شده و به PATH اضافه شده است
- [ ] فایل `.env` در backend پیکربندی شده است
- [ ] وابستگی‌های Python نصب شده‌اند
- [ ] وابستگی‌های npm نصب شده‌اند
- [ ] Backend API با موفقیت اجرا می‌شود
- [ ] Frontend با موفقیت اجرا می‌شود

---

**نسخه:** 1.0.0 | **آخرین بروزرسانی:** 2026-09-04
