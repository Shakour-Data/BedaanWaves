# BedaanWaves API Documentation
## مستندات کامل API

**نسخه:** 1.0.0  
**تاریخ:** 2026-09-04  
**وضعیت:** فعال ✅

---

## 📋 فهرست مطالب

1. [مقدمه](#مقدمه)
2. [احراز هویت](#احراز-هویت)
3. [APIهای اصلی](#apiهای-اصلی)
4. [مدل‌های داده](#مدلهای-داده)
5. [کدهای خطا](#کدهای-خطا)
6. [محدودیت‌های نرخ](#محدودیتهای-نرخ)

---

## مقدمه

API BedaanWaves یک رابط RESTful است که امکان دسترسی به داده‌های تحلیل سهام، پیش‌بینی‌ها، و مدیریت هشدارها را فراهم می‌کند.

### اطلاعات پایه

| مشخصه | مقدار |
|-------|-------|
| **Base URL** | `https://api.bedaanwaves.com/api/v1` |
| **Protocol** | HTTPS |
| **Content-Type** | `application/json` |
| **Authentication** | Bearer Token (JWT) |

---

## احراز هویت

### دریافت توکن

**Endpoint:** `POST /auth/login`

**درخواست:**
```json
{
  "email": "user@example.com",
  "password": "your_password"
}
```

**پاسخ:**
```json
{
  "status": "success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "Bearer",
    "expires_in": 3600
  }
}
```

### استفاده از توکن

```http
GET /api/v1/dashboard/general HTTP/1.1
Host: api.bedaanwaves.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

---

## APIهای اصلی

### 1. Dashboard APIs

#### دریافت داشبورد اصلی

**Endpoint:** `GET /dashboard/general`

**پاسخ:**
```json
{
  "status": "success",
  "summary": {
    "total_symbols": 8500,
    "total_signals": 15000,
    "total_news": 2500
  },
  "dimensions": {
    "fundamental": {
      "avg_score": 65.4,
      "min_score": 12.5,
      "max_score": 98.7
    }
  },
  "latest_date": "2026-09-04"
}
```

### 2. Compare APIs

#### مقایسه چند سهم

**Endpoint:** `POST /compare/stocks`

**درخواست:**
```json
{
  "symbols": ["AAPL", "GOOGL", "MSFT"],
  "include_dimensions": true,
  "include_metrics": true,
  "include_technical": true
}
```

**پاسخ:**
```json
{
  "status": "success",
  "count": 3,
  "comparisons": [
    {
      "symbol": "AAPL",
      "name": "Apple Inc.",
      "current_price": 175.50,
      "overall_score": 78.5,
      "grade": "A-",
      "dimensions": {
        "fundamental": 82.3,
        "technical": 75.6,
        "sentiment": 80.1
      }
    }
  ]
}
```

### 3. Alerts APIs

#### ایجاد هشدار جدید

**Endpoint:** `POST /alerts`

**درخواست:**
```json
{
  "name": "AAPL Price Alert",
  "symbols": ["AAPL"],
  "condition": {
    "type": "price_above",
    "price_threshold": {
      "value": 200.00
    }
  },
  "delivery": {
    "channels": ["in_app", "email"]
  }
}
```

### 4. Forecast APIs

#### پیش‌بینی قیمت

**Endpoint:** `POST /forecast/price`

**درخواست:**
```json
{
  "symbol": "AAPL",
  "model": "ensemble",
  "horizon": "7d",
  "confidence_level": 0.95
}
```

**پاسخ:**
```json
{
  "status": "success",
  "symbol": "AAPL",
  "last_price": 175.50,
  "forecast": [
    {
      "date": "2026-09-05",
      "predicted_price": 177.20,
      "lower_bound": 172.50,
      "upper_bound": 181.90,
      "confidence": 0.95
    }
  ],
  "model_accuracy": 0.87
}
```

---

## مدل‌های داده

### Stock

| فیلد | نوع | توضیحات |
|------|-----|---------|
| `symbol` | string | نماد سهم |
| `name` | string | نام شرکت |
| `sector` | string | صنعت |
| `price` | number | قیمت فعلی |
| `change` | number | تغییر قیمت |
| `changePct` | number | درصد تغییر |
| `marketCap` | number | ارزش بازار |
| `overallScore` | number | امتیاز کلی (0-100) |
| `grade` | string | نمره (A+, A, B, etc.) |
| `dimensions` | object | امتیازات 6 بعد |

### Alert

| فیلد | نوع | توضیحات |
|------|-----|---------|
| `id` | string | شناسه یکتا |
| `name` | string | نام هشدار |
| `symbols` | array | لیست نمادها |
| `condition` | object | شرط trigger |
| `status` | string | وضعیت (active, paused, etc.) |
| `createdAt` | string | تاریخ ایجاد |

---

## کدهای خطا

| کد | پیام | توضیحات |
|----|------|---------|
| 400 | Bad Request | درخواست نادرست |
| 401 | Unauthorized | عدم احراز هویت |
| 403 | Forbidden | دسترسی غیرمجاز |
| 404 | Not Found | یافت نشد |
| 429 | Too Many Requests | محدودیت نرخ |
| 500 | Internal Server Error | خطای سرور |
| 503 | Service Unavailable | سرویس در دسترس نیست |

---

## محدودیت‌های نرخ

| سطح | درخواست/دقیقه | درخواست/ساعت | درخواست/روز |
|-----|----------------|---------------|--------------|
| Free | 10 | 100 | 1,000 |
| Basic | 60 | 3,000 | 10,000 |
| Pro | 300 | 15,000 | 50,000 |
| Enterprise | Unlimited | Unlimited | Unlimited |

---

## پشتیبانی

- **ایمیل:** api-support@bedaanwaves.com
- **مستندات:** https://docs.bedaanwaves.com
- **GitHub:** https://github.com/bedaanwaves/api
- **Discord:** https://discord.gg/bedaanwaves

---

**آخرین به‌روزرسانی:** 2026-09-04  
**نسخه:** 1.0.0
