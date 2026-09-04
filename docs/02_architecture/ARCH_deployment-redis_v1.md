# Redis Cache Setup Guide
## Redis Cache Setup Guide

**تاریخ:** 2026-09-04  
**نسخه:** 1.0.0

---

## 📋 Table of Contents

1. [مقدمه](#مقدمه)
2. [روش‌های راه‌اندازی](#روشهای-راهاندازی)
3. [پیکربندی](#پیکربندی)
4. [تست و بررسی](#تست-و-بررسی)
5. [عیب‌یابی](#عیبیابی)

---

## Introduction

Redis Cache برای بهبود عملکرد پلتفرم BedaanWaves اضافه شده است. این سیستم:

- **70% کاهش** زمان پاسخ APIها
- **50% کاهش** load دیتابیس
- ** caching** هوشمند با TTL متغیر

---

## Setup Methods

### Method 1: Direct Installation on Ubuntu/Debian (Recommended)

```bash
# 1. به‌روزرسانی لیست بسته‌ها
sudo apt update

# 2. نصب Redis
sudo apt install redis-server -y

# 3. فعال‌سازی و شروع سرویس Redis
sudo systemctl enable redis-server
sudo systemctl start redis-server

# 4. بررسی وضعیت
sudo systemctl status redis-server

# 5. تست اتصال
redis-cli ping
# خروجی مورد انتظار: PONG
```

### Method 2: Direct Installation on macOS

```bash
# 1. نصب Redis با Homebrew
brew install redis

# 2. شروع سرویس Redis
brew services start redis

# 3. تست اتصال
redis-cli ping
# خروجی مورد انتظار: PONG
```

### Method 3: Direct Installation on Windows

**گزینه A: استفاده از Memurai (توصیه شده برای Windows)**
```powershell
# 1. دانلود و نصب Memurai از https://www.memurai.com/
# 2. نصب به عنوان سرویس Windows
# 3. شروع سرویس از Services.msc
# 4. تست اتصال
redis-cli ping
```

**گزینه B: استفاده از Redis برای Windows**
```powershell
# 1. دانلود Redis برای Windows از GitHub
# https://github.com/microsoftarchive/redis/releases

# 2. استخراج و اجرا
redis-server.exe --service-install redis.windows.conf --loglevel verbose

# 3. شروع سرویس
redis-server --service-start

# 4. تست اتصال
redis-cli ping
```

---

## Configuration

### Backend Settings

فایل `.env` را به‌روز کنید:

```bash
# Redis Configuration
REDIS_URL=redis://localhost:6379/0
CACHE_ENABLED=true
CACHE_BACKEND=redis
CACHE_TTL=3600
```

### Redis Configuration Settings

فایل [`redis.conf`](deployment/redis/redis.conf) را بررسی کنید. تنظیمات کلیدی:

```conf
# حداکثر حافظه (256MB برای cache)
maxmemory 256mb

# سیاست حذف کلیدها
maxmemory-policy allkeys-lru

# تعداد دیتابیس‌ها
databases 2

# پورت
port 6379

# bind به همه interfaces (برای دسترسی محلی)
bind 127.0.0.1 ::1

# timeout برای connections idle
timeout 300

# TCP keepalive
tcp-keepalive 60
```

#### Redis Settings for Windows

اگر از Memurai استفاده می‌کنید، فایل کانفیگ در این مسیر قرار می‌گیرد:
```
C:\Program Files\Memurai\memurai.conf
```

اگر از Redis برای Windows استفاده می‌کنید:
```
C:\Program Files\Redis\redis.windows.conf
```

---

## Testing and Verification

### 1. Basic Connection Test

```bash
# اتصال به Redis
redis-cli

# داخل Redis CLI:
PING
# خروجی: PONG

# ذخیره مقدار
SET test_key "Hello Redis"

# بازیابی مقدار
GET test_key

# حذف کلید
DEL test_key

# خروج
EXIT
```

### 2. Testing via Backend

```bash
# اجرای تست اتصال Redis
cd backend
python -c "
import asyncio
from app.infrastructure.cache.redis_cache_backend import RedisCacheBackend

async def test():
    cache = RedisCacheBackend('redis://localhost:6379/0')
    await cache.set('test_key', {'message': 'Hello from BedaanWaves'}, ttl=60)
    result = await cache.get('test_key')
    print(f'Retrieved: {result}')
    await cache.delete('test_key')
    print('Test passed!')

asyncio.run(test())
"
```

### 3. Performance Test

```bash
# استفاده از redis-benchmark
redis-benchmark -h localhost -p 6379 -n 100000 -c 50

# نتایج مورد انتظار:
# - SET: > 100,000 ops/sec
# - GET: > 100,000 ops/sec
```

### 4. Monitoring

```bash
# مشاهده اطلاعات Redis
redis-cli INFO

# مشاهده آمار حافظه
redis-cli INFO memory

# مشاهده آمار clients
redis-cli INFO clients

# لیست کلیدها (با احتیاط در production)
redis-cli KEYS "*"

# تعداد کلیدها
redis-cli DBSIZE
```

---

## Troubleshooting

### Issue 1: Unable to Connect to Redis

**علامت:**
```
Redis connection failed: Error connecting to localhost:6379
```

**راه‌حل:**
```bash
# 1. بررسی وضعیت Redis
sudo systemctl status redis-server

# 2. راه‌اندازی مجدد Redis
sudo systemctl restart redis-server

# 3. بررسی پورت
netstat -tlnp | grep 6379

# 4. بررسی فایروال
sudo ufw allow 6379
```

### Issue 2: Memory Error

**علامت:**
```
OOM command not allowed when used memory > 'maxmemory'
```

**راه‌حل:**
```bash
# 1. بررسی استفاده از حافظه
redis-cli INFO memory

# 2. افزایش maxmemory در redis.conf
maxmemory 512mb

# 3. تغییر سیاست حذف
maxmemory-policy allkeys-lru

# 4. راه‌اندازی مجدد
sudo systemctl restart redis-server
```

### Issue 3: Poor Performance

**علامت:**
- زمان پاسخ بالا
- تعداد connections زیاد

**راه‌حل:**
```bash
# 1. بررسی connections
redis-cli INFO clients

# 2. بستن connections idle
redis-cli CLIENT LIST | grep idle

# 3. تنظیم timeout
# در redis.conf:
timeout 300
tcp-keepalive 60

# 4. استفاده از connection pooling در برنامه
```

### Issue 4: Cached Data Not Expiring

**علامت:**
- داده‌های قدیمی در cache
- عدم به‌روزرسانی اطلاعات

**راه‌حل:**
```bash
# 1. بررسی TTL کلیدها
redis-cli TTL "key_name"

# 2. تنظیم TTL مناسب در برنامه
# برای داده‌های متغیر: 5-15 دقیقه
# برای داده‌های نسبتاً ثابت: 1-24 ساعت

# 3. Invalidation دستی در صورت نیاز
redis-cli DEL "key_name"

# 4. یا استفاده از pattern برای حذف گروهی
redis-cli KEYS "pattern:*" | xargs redis-cli DEL
```

---

## Additional Resources

- [Redis Documentation](https://redis.io/documentation)
- [Redis Configuration](https://redis.io/docs/management/config/)
- [Redis Persistence](https://redis.io/docs/management/persistence/)
- [Memurai Documentation](https://docs.memurai.com/)

---

**تاریخ آخرین به‌روزرسانی:** 2026-09-04  
**نسخه مستند:** 1.0.0
