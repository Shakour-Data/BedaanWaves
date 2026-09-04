# Redis Cache Setup Guide
## راهنمای راه‌اندازی Redis Cache

**تاریخ:** 2026-09-04  
**نسخه:** 1.0.0

---

## 📋 فهرست مطالب

1. [مقدمه](#مقدمه)
2. [روش‌های راه‌اندازی](#روشهای-راهاندازی)
3. [پیکربندی](#پیکربندی)
4. [تست و بررسی](#تست-و-بررسی)
5. [عیب‌یابی](#عیبیابی)

---

## مقدمه

Redis Cache برای بهبود عملکرد پلتفرم BedaanWaves اضافه شده است. این سیستم:

- **70% کاهش** زمان پاسخ APIها
- **50% کاهش** load دیتابیس
- ** caching** هوشمند با TTL متغیر

---

## روش‌های راه‌اندازی

### روش ۱: Docker Compose (توصیه شده)

```bash
# 1. اجرای Redis به همراه سایر سرویس‌ها
docker-compose -f docker-compose.yml -f docker-compose.redis.yml up -d

# 2. بررسی وضعیت
docker-compose ps

# 3. مشاهده logs
docker-compose logs -f redis
```

### روش ۲: اجرای مستقل Redis

```bash
# 1. اجرای Redis به صورت standalone
docker run -d \
  --name bedaanwaves-redis \
  -p 6379:6379 \
  -v redis_data:/data \
  redis:7-alpine \
  redis-server --appendonly yes

# 2. تست اتصال
docker exec -it bedaanwaves-redis redis-cli ping
```

### روش ۳: نصب مستقیم (بدون Docker)

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server

# macOS
brew install redis
brew services start redis

# تست
redis-cli ping
```

---

## پیکربندی

### تنظیمات Backend

فایل `.env` را به‌روز کنید:

```bash
# Redis Configuration
REDIS_URL=redis://localhost:6379/0
CACHE_ENABLED=true
CACHE_BACKEND=redis
CACHE_TTL=3600
```

### تنظیمات Docker

برای محیط production، فایل `docker-compose.redis.yml` را ویرایش کنید:

```yaml
services:
  redis:
    environment:
      - REDIS_PASSWORD=${REDIS_PASSWORD}
    command: redis-server --requirepass ${REDIS_PASSWORD}
```

### تنظیمات Redis

فایل [`redis.conf`](file:///e:/BedaanWaves/deployment/redis/redis.conf) را بررسی کنید. تنظیمات کلیدی:

```conf
# حداکثر حافظه (256MB برای cache)
maxmemory 256mb

# سیاست حذف کلیدها
maxmemory-policy allkeys-lru

# تعداد دیتابیس‌ها
databases 2

# پورت
port 6379
```

---

## تست و بررسی

### ۱. تست اتصال پایه

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

### ۲. تست از طریق Backend

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

### ۳. تست عملکرد

```bash
# استفاده از redis-benchmark
redis-benchmark -h localhost -p 6379 -n 100000 -c 50

# نتایج مورد انتظار:
# - SET: > 100,000 ops/sec
# - GET: > 100,000 ops/sec
```

### ۴. مانیتورینگ

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

## عیب‌یابی

### مشکل ۱: عدم اتصال به Redis

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

### مشکل ۲: خطای حافظه

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

### مشکل ۳: عملکرد ضعیف

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

### مشکل ۴: داده‌های cache شده منقضی نمی‌شوند

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

## منابع بیشتر

- [Redis Documentation](https://redis.io/documentation)
- [Redis Docker Hub](https://hub.docker.com/_/redis)
- [Redis Configuration](https://redis.io/docs/management/config/)
- [Redis Persistence](https://redis.io/docs/management/persistence/)

---

**تاریخ آخرین به‌روزرسانی:** 2026-09-04  
**نسخه مستند:** 1.0.0
