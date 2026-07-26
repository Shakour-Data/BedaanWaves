# مستندات API پروژه Bedaan6D

## فهرست مطالب
1. [معرفی API](#معرفی-api)
2. [پایه‌های عمومی](#پایه‌های-عمومی)
3. [Endpointهای مدیریت سلسله‌مراتب](#endpointهای-مدیریت-سلسله‌مراتب)
4. [Endpointهای مدیریت نمادها](#endpointهای-مدیریت-نمادها)
5. [Endpointهای سیستم امتیازدهی](#endpointهای-سیستم-امتیازدهی)
6. [Endpointهای رتبه‌بندی](#endpointهای-رتبه‌بندی)
7. [کدهای خطا](#کدهای-خطا)
8. [مثال‌های استفاده](#مثال‌های-استفاده)

## معرفی API

API پروژه Bedaan6D یک RESTful API است که امکان تعامل با سیستم تحلیل ۶ بعدی بازار بورس تهران را فراهم می‌کند. این API از JSON برای تبادل داده استفاده می‌کند و از احراز هویت مبتنی بر توکن پشتیبانی می‌کند.

### پایه URL
```
https://api.bedaan6d.ir/api/6d
```

### هدرهای عمومی
```http
Content-Type: application/json
Accept: application/json
Authorization: Bearer <token>  # برای endpoints حساس
```

### فرمت پاسخ
تمامی پاسخ‌های API دارای فرمت زیر هستند:
```json
{
  "success": true,
  "data": {...},
  "message": "عملیات با موفقیت انجام شد"
}
```

یا در صورت خطا:
```json
{
  "success": false,
  "error": "پیام خطا",
  "code": "کد_خطا"
}
```

## پایه‌های عمومی

### احراز هویت
در حال حاضر API از احراز هویت ساده استفاده می‌کند. برای endpoints حساس، توکن باید در هدر Authorization ارسال شود.

### نرخ محدودیت
- **عمومی**: ۱۰۰ درخواست در دقیقه
- **احراز شده**: ۱۰۰۰ درخواست در دقیقه

### مدیریت خطا
- خطاهای اعتبارسنجی: ۴۰۰
- خطاهای احراز هویت: ۴۰۱
- خطاهای مجوز: ۴۰۳
- منابع یافت نشده: ۴۰۴
- خطاهای سرور: ۵۰۰

## Endpointهای مدیریت سلسله‌مراتب

### دریافت ساختار سلسله‌مراتبی

**درخواست**:
```http
GET /hierarchy
```

**پاسخ موفق** (200):
```json
{
  "success": true,
  "data": {
    "mainDimensions": [
      {
        "id": "dim-1",
        "code": "TD-01",
        "name": "تحلیل تکنیکال",
        "description": "تحلیل بر اساس نمودارها و شاخص‌های تکنیکال",
        "weight": 1.0,
        "order": 1,
        "subDimensions": [
          {
            "id": "sub-1",
            "code": "TD-01-01",
            "name": "شاخص‌های روند",
            "description": "شاخص‌های شناسایی روند بازار",
            "weight": 1.0,
            "order": 1,
            "aspects": [
              {
                "id": "asp-1",
                "code": "TD-01-01-01",
                "name": "میانگین متحرک",
                "description": "میانگین قیمت در بازه زمانی مشخص",
                "weight": 1.0,
                "order": 1,
                "subCategories": [
                  {
                    "id": "cat-1",
                    "code": "TD-01-01-01-01",
                    "name": "MA-20",
                    "description": "میانگین متحرک ۲۰ روزه",
                    "weight": 1.0,
                    "order": 1
                  }
                ]
              }
            ]
          }
        ]
      }
    ]
  },
  "message": "ساختار سلسله‌مراتبی با موفقیت دریافت شد"
}
```

### ایجاد بعد اصلی جدید

**درخواست**:
```http
POST /hierarchy
```

**بدنه درخواست**:
```json
{
  "code": "TD-02",
  "name": "تحلیل بنیادی",
  "description": "تحلیل بر اساس صورت‌های مالی و عملکرد شرکت",
  "weight": 1.0,
  "order": 2
}
```

**اعتبارسنجی**:
- `code`: الزامی، منحصربه‌فرد، فرمت: XX-XX
- `name`: الزامی، حداقل ۳ کاراکتر
- `weight`: اختیاری، پیش‌فرض ۱.۰، بین ۰ و ۱۰
- `order`: الزامی، عدد صحیح مثبت، منحصربه‌فرد

**پاسخ موفق** (201):
```json
{
  "success": true,
  "data": {
    "id": "dim-2",
    "code": "TD-02",
    "name": "تحلیل بنیادی",
    "description": "تحلیل بر اساس صورت‌های مالی و عملکرد شرکت",
    "weight": 1.0,
    "order": 2,
    "createdAt": "2024-01-01T10:30:00.000Z",
    "updatedAt": "2024-01-01T10:30:00.000Z"
  },
  "message": "بعد اصلی با موفقیت ایجاد شد"
}
```

### دریافت بعد اصلی

**درخواست**:
```http
GET /hierarchy/{id}
```

**پارامترهای مسیر**:
- `id`: شناسه بعد اصلی

**پاسخ موفق** (200):
```json
{
  "success": true,
  "data": {
    "id": "dim-1",
    "code": "TD-01",
    "name": "تحلیل تکنیکال",
    "description": "تحلیل بر اساس نمودارها و شاخص‌های تکنیکال",
    "weight": 1.0,
    "order": 1,
    "subDimensions": [...],
    "createdAt": "2024-01-01T10:30:00.000Z",
    "updatedAt": "2024-01-01T10:30:00.000Z"
  },
  "message": "بعد اصلی با موفقیت دریافت شد"
}
```

### به‌روزرسانی بعد اصلی

**درخواست**:
```http
PUT /hierarchy/{id}
```

**پارامترهای مسیر**:
- `id`: شناسه بعد اصلی

**بدنه درخواست**:
```json
{
  "name": "تحلیل تکنیکال پیشرفته",
  "description": "تحلیل پیشرفته بر اساس نمودارها و شاخص‌های تکنیکال",
  "weight": 1.2
}
```

**پاسخ موفق** (200):
```json
{
  "success": true,
  "data": {
    "id": "dim-1",
    "code": "TD-01",
    "name": "تحلیل تکنیکال پیشرفته",
    "description": "تحلیل پیشرفته بر اساس نمودارها و شاخص‌های تکنیکال",
    "weight": 1.2,
    "order": 1,
    "createdAt": "2024-01-01T10:30:00.000Z",
    "updatedAt": "2024-01-01T11:45:00.000Z"
  },
  "message": "بعد اصلی با موفقیت به‌روزرسانی شد"
}
```

### حذف بعد اصلی

**درخواست**:
```http
DELETE /hierarchy/{id}
```

**پارامترهای مسیر**:
- `id`: شناسه بعد اصلی

**پاسخ موفق** (200):
```json
{
  "success": true,
  "data": {
    "id": "dim-1",
    "code": "TD-01",
    "name": "تحلیل تکنیکال",
    "description": "تحلیل بر اساس نمودارها و شاخص‌های تکنیکال",
    "weight": 1.0,
    "order": 1
  },
  "message": "بعد اصلی با موفقیت حذف شد"
}
```

## Endpointهای مدیریت نمادها

### دریافت لیست نمادها

**درخواست**:
```http
GET /symbols
```

**پارامترهای query**:
- `market` (اختیاری): فیلتر بر اساس بازار (بورس، فرابورس، ...)
- `sector` (اختیاری): فیلتر بر اساس صنعت
- `search` (اختیاری): جستجو در نماد و نام
- `page` (اختیاری): شماره صفحه، پیش‌فرض: ۱
- `limit` (اختیاری): تعداد در هر صفحه، پیش‌فرض: ۲۰، حداکثر: ۱۰۰

**پاسخ موفق** (200):
```json
{
  "success": true,
  "data": {
    "symbols": [
      {
        "id": "sym-1",
        "isin": "IRO1FOLD0001",
        "symbol": "فولاد",
        "name": "فولاد مبارکه اصفهان",
        "market": "بورس",
        "sector": "فلزات اساسی",
        "subSector": "فولاد",
        "marketData": [
          {
            "id": "md-1",
            "date": "2024-01-01T00:00:00.000Z",
            "price": 15000,
            "rsi": 55.5,
            "macd": 2.5,
            "peg": 1.2,
            "roe": 18.5
          }
        ],
        "createdAt": "2024-01-01T10:30:00.000Z",
        "updatedAt": "2024-01-01T10:30:00.000Z"
      }
    ],
    "pagination": {
      "total": 100,
      "page": 1,
      "limit": 20,
      "pages": 5
    }
  },
  "message": "نمادها با موفقیت دریافت شدند"
}
```

### دریافت نماد

**درخواست**:
```http
GET /symbols/{id}
```

**پارامترهای مسیر**:
- `id`: شناسه نماد

**پاسخ موفق** (200):
```json
{
  "success": true,
  "data": {
    "id": "sym-1",
    "isin": "IRO1FOLD0001",
    "symbol": "فولاد",
    "name": "فولاد مبارکه اصفهان",
    "market": "بورس",
    "sector": "فلزات اساسی",
    "subSector": "فولاد",
    "marketData": [...],
    "createdAt": "2024-01-01T10:30:00.000Z",
    "updatedAt": "2024-01-01T10:30:00.000Z"
  },
  "message": "نماد با موفقیت دریافت شد"
}
```

### ایجاد نماد جدید

**درخواست**:
```http
POST /symbols
```

**بدنه درخواست**:
```json
{
  "isin": "IRO1FOLD0001",
  "symbol": "فولاد",
  "name": "فولاد مبارکه اصفهان",
  "market": "بورس",
  "sector": "فلزات اساسی",
  "subSector": "فولاد"
}
```

**اعتبارسنجی**:
- `isin`: الزامی، منحصربه‌فرد، فرمت: IROXXXXXXXXXX
- `symbol`: الزامی، منحصربه‌فرد، حداقل ۲ کاراکتر
- `name`: الزامی، حداقل ۳ کاراکتر
- `market`: الزامی، یکی از: بورس، فرابورس، پایه، ...
- `sector`: الزامی، حداقل ۲ کاراکتر

**پاسخ موفق** (201):
```json
{
  "success": true,
  "data": {
    "id": "sym-1",
    "isin": "IRO1FOLD0001",
    "symbol": "فولاد",
    "name": "فولاد مبارکه اصفهان",
    "market": "بورس",
    "sector": "فلزات اساسی",
    "subSector": "فولاد",
    "createdAt": "2024-01-01T10:30:00.000Z",
    "updatedAt": "2024-01-01T10:30:00.000Z"
  },
  "message": "نماد با موفقیت ایجاد شد"
}
```

### به‌روزرسانی نماد

**درخواست**:
```http
PUT /symbols/{id}
```

**پارامترهای مسیر**:
- `id`: شناسه نماد

**بدنه درخواست**:
```json
{
  "name": "فولاد مبارکه اصفهان (به‌روز شده)",
  "sector": "فلزات اساسی و معادن"
}
```

**پاسخ موفق** (200):
```json
{
  "success": true,
  "data": {
    "id": "sym-1",
    "isin": "IRO1FOLD0001",
    "symbol": "فولاد",
    "name": "فولاد مبارکه اصفهان (به‌روز شده)",
    "market": "بورس",
    "sector": "فلزات اساسی و معادن",
    "subSector": "فولاد",
    "createdAt": "2024-01-01T10:30:00.000Z",
    "updatedAt": "2024-01-01T11:45:00.000Z"
  },
  "message": "نماد با موفقیت به‌روزرسانی شد"
}
```

### حذف نماد

**درخواست**:
```http
DELETE /symbols/{id}
```

**پارامترهای مسیر**:
- `id`: شناسه نماد

**پاسخ موفق** (200):
```json
{
  "success": true,
  "data": {
    "id": "sym-1",
    "isin": "IRO1FOLD0001",
    "symbol": "فولاد",
    "name": "فولاد مبارکه اصفهان",
    "market": "بورس",
    "sector": "فلزات اساسی"
  },
  "message": "نماد با موفقیت حذف شد"
}
```

### افزودن داده‌های بازار

**درخواست**:
```http
POST /symbols/{id}/market-data
```

**پارامترهای مسیر**:
- `id`: شناسه نماد

**بدنه درخواست**:
```json
{
  "date": "2024-01-01",
  "price": 15000,
  "rsi": 55.5,
  "macd": 2.5,
  "peg": 1.2,
  "roe": 18.5,
  "debtToEquity": 0.8
}
```

**پاسخ موفق** (201):
```json
{
  "success": true,
  "data": {
    "id": "md-1",
    "date": "2024-01-01T00:00:00.000Z",
    "price": 15000,
    "rsi": 55.5,
    "macd": 2.5,
    "peg": 1.2,
    "roe": 18.5,
    "debtToEquity": 0.8,
    "symbolId": "sym-1"
  },
  "message": "داده‌های بازار با موفقیت افزوده شدند"
}
```

## Endpointهای سیستم امتیازدهی

### محاسبه امتیاز برای نماد

**درخواست**:
```http
POST /scoring
```

**بدنه درخواست**:
```json
{
  "symbolId": "sym-1",
  "date": "2024-01-01"
}
```

**اعتبارسنجی**:
- `symbolId`: الزامی، شناسه نماد معتبر
- `date`: الزامی، فرمت YYYY-MM-DD

**پاسخ موفق** (200):
```json
{
  "success": true,
  "data": {
    "symbolId": "sym-1",
    "calculationDate": "2024-01-01T00:00:00.000Z",
    "dimensionScores": [
      {
        "dimensionId": "dim-1",
        "dimensionCode": "TD-01",
        "dimensionName": "تحلیل تکنیکال",
        "score": 85.5,
        "weightedScore": 85.5
      },
      {
        "dimensionId": "dim-2",
        "dimensionCode": "TD-02",
        "dimensionName": "تحلیل بنیادی",
        "score": 78.2,
        "weightedScore": 78.2
      }
    ],
    "totalScore": 81.85,
    "totalWeightedScore": 81.85
  },
  "message": "امتیازها با موفقیت محاسبه شدند"
}
```

### دریافت امتیازهای نماد

**درخواست**:
```http
GET /scoring
```

**پارامترهای query**:
- `symbolId` (الزامی): شناسه نماد
- `startDate` (اختیاری): تاریخ شروع، فرمت YYYY-MM-DD
- `endDate` (اختیاری): تاریخ پایان، فرمت YYYY-MM-DD
- `dimensionId` (اختیاری): فیلتر بر اساس بعد

**پاسخ موفق** (200):
```json
{
  "success": true,
  "data": [
    {
      "id": "score-1",
      "value": 85.5,
      "weightedValue": 85.5,
      "calculationDate": "2024-01-01T00:00:00.000Z",
      "mainDimension": {
        "id": "dim-1",
        "code": "TD-01",
        "name": "تحلیل تکنیکال",
        "weight": 1.0
      },
      "subDimension": null,
      "aspect": null,
      "subCategory": null
    },
    {
      "id": "score-2",
      "value": 78.2,
      "weightedValue": 78.2,
      "calculationDate": "2024-01-01T00:00:00.000Z",
      "mainDimension": {
        "id": "dim-2",
        "code": "TD-02",
        "name": "تحلیل بنیادی",
        "weight": 1.0
      },
      "subDimension": null,
      "aspect": null,
      "subCategory": null
    }
  ],
  "message": "امتیازها با موفقیت دریافت شدند"
}
```

## Endpointهای رتبه‌بندی

### دریافت رتبه‌بندی نمادها

**درخواست**:
```http
GET /scoring/rankings
```

**پارامترهای query**:
- `dimensionId` (اختیاری): فیلتر بر اساس بعد
- `market` (اختیاری): فیلتر بر اساس بازار
- `sector` (اختیاری): فیلتر بر اساس صنعت
- `minScore` (اختیاری): حداقل امتیاز، بین ۰ و ۱۰۰
- `maxScore` (اختیاری): حداکثر امتیاز، بین ۰ و ۱۰۰
- `page` (اختیاری): شماره صفحه، پیش‌فرض: ۱
- `limit` (اختیاری): تعداد در هر صفحه، پیش‌فرض: ۲۰، حداکثر: ۱۰۰

**پاسخ موفق** (200):
```json
{
  "success": true,
  "data": {
    "rankings": [
      {
        "symbolId": "sym-1",
        "symbolCode": "فولاد",
        "symbolName": "فولاد مبارکه اصفهان",
        "score": 85.5,
        "weightedScore": 85.5,
        "rank": 1,
        "calculationDate": "2024-01-01T00:00:00.000Z"
      },
      {
        "symbolId": "sym-2",
        "symbolCode": "خساپا",
        "symbolName": "خودروسازی ایران خودرو",
        "score": 78.2,
        "weightedScore": 78.2,
        "rank": 2,
        "calculationDate": "2024-01-01T00:00:00.000Z"
      }
    ],
    "averageScore": 81.85,
    "pagination": {
      "total": 50,
      "page": 1,
      "limit": 20,
      "pages": 3
    }
  },
  "message": "رتبه‌بندی با موفقیت دریافت شد"
}
```

## کدهای خطا

### خطاهای عمومی

| کد خطا | پیام | توضیح |
|--------|------|-------|
| `VALIDATION_ERROR` | خطای اعتبارسنجی | داده‌های ورودی نامعتبر هستند |
| `AUTHENTICATION_ERROR` | خطای احراز هویت | توکن معتبر ارائه نشده است |
| `AUTHORIZATION_ERROR` | خطای مجوز | کاربر مجوز دسترسی ندارد |
| `NOT_FOUND` | منبع یافت نشد | شناسه ارائه شده معتبر نیست |
| `DATABASE_ERROR` | خطای دیتابیس | خطا در دسترسی به دیتابیس |
| `EXTERNAL_API_ERROR` | خطای API خارجی | خطا در ارتباط با API خارجی |
| `INTERNAL_SERVER_ERROR` | خطای داخلی سرور | خطای غیرمنتظره در سرور |

### خطاهای خاص

| کد خطی | پیام | توضیح |
|--------|------|-------|
| `DUPLICATE_CODE` | کد تکراری است | کد ارائه شده قبلاً استفاده شده |
| `DUPLICATE_ORDER` | ترتیب تکراری است | ترتیب ارائه شده قبلاً استفاده شده |
| `DUPLICATE_ISIN` | کد ISIN تکراری است | کد ISIN ارائه شده قبلاً استفاده شده |
| `DUPLICATE_SYMBOL` | نماد تکراری است | نماد ارائه شده قبلاً استفاده شده |
| `INVALID_MARKET` | بازار نامعتبر است | بازار ارائه شده معتبر نیست |
| `MISSING_MARKET_DATA` | داده‌های بازار یافت نشد | داده‌های بازار برای نماد وجود ندارد |
| `MISSING_HIERARCHY` | ساختار سلسله‌مراتبی یافت نشد | ساختار سلسله‌مراتبی تعریف نشده است |

## مثال‌های استفاده

### مثال ۱: دریافت لیست نمادها

**درخواست**:
```bash
curl -X GET "https://api.bedaan6d.ir/api/6d/symbols?market=بورس&sector=فلزات اساسی&page=1&limit=10" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_token_here"
```

**پاسخ**:
```json
{
  "success": true,
  "data": {
    "symbols": [...],
    "pagination": {
      "total": 25,
      "page": 1,
      "limit": 10,
      "pages": 3
    }
  },
  "message": "نمادها با موفقیت دریافت شدند"
}
```

### مثال ۲: ایجاد نماد جدید

**درخواست**:
```bash
curl -X POST "https://api.bedaan6d.ir/api/6d/symbols" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_token_here" \
  -d '{
    "isin": "IRO1FOLD0001",
    "symbol": "فولاد",
    "name": "فولاد مبارکه اصفهان",
    "market": "بورس",
    "sector": "فلزات اساسی",
    "subSector": "فولاد"
  }'
```

**پاسخ**:
```json
{
  "success": true,
  "data": {
    "id": "sym-1",
    "isin": "IRO1FOLD0001",
    "symbol": "فولاد",
    "name": "فولاد مبارکه اصفهان",
    "market": "بورس",
    "sector": "فلزات اساسی",
    "subSector": "فولاد",
    "createdAt": "2024-01-01T10:30:00.000Z",
    "updatedAt": "2024-01-01T10:30:00.000Z"
  },
  "message": "نماد با موفقیت ایجاد شد"
}
```

### مثال ۳: محاسبه امتیاز

**درخواست**:
```bash
curl -X POST "https://api.bedaan6d.ir/api/6d/scoring" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_token_here" \
  -d '{
    "symbolId": "sym-1",
    "date": "2024-01-01"
  }'
```

**پاسخ**:
```json
{
  "success": true,
  "data": {
    "symbolId": "sym-1",
    "calculationDate": "2024-01-01T00:00:00.000Z",
    "dimensionScores": [...],
    "totalScore": 81.85,
    "totalWeightedScore": 81.85
  },
  "message": "امتیازها با موفقیت محاسبه شدند"
}
```

### مثال ۴: دریافت رتبه‌بندی

**درخواست**:
```bash
curl -X GET "https://api.bedaan6d.ir/api/6d/scoring/rankings?dimensionId=dim-1&minScore=70&maxScore=90&page=1&limit=5" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_token_here"
```

**پاسخ**:
```json
{
  "success": true,
  "data": {
    "rankings": [...],
    "averageScore": 81.85,
    "pagination": {
      "total": 20,
      "page": 1,
      "limit": 5,
      "pages": 4
    }
  },
  "message": "رتبه‌بندی با موفقیت دریافت شد"
}
```

### مثال ۵: مدیریت خطا

**درخواست نامعتبر**:
```bash
curl -X POST "https://api.bedaan6d.ir/api/6d/symbols" \
  -H "Content-Type: application/json" \
  -d '{
    "isin": "invalid",
    "symbol": "",
    "name": ""
  }'
```

**پاسخ خطا**:
```json
{
  "success": false,
  "error": "خطای اعتبارسنجی: کد ISIN الزامی است، نماد الزامی است، نام الزامی است",
  "code": "VALIDATION_ERROR"
}
```

---

**تاریخ آخرین به‌روزرسانی**: ۵ ژوئیه ۲۰۲۶  
**نگارنده**: تیم توسعه Bedaan6D  
**نسخه**: ۱.۰.۰