# BedaanWaves - Master Plan
## Comprehensive Project Execution Plan

**تاریخ ایجاد:** 2026-09-04  
**وضعیت:** در حال اجرا  
**نسخه:** 1.0.0

---

## 📋 Table of Contents

1. [ executive summary](#1-executive-summary)
2. [ Roadmap کلی](#2-roadmap-کلی)
3. [ فازها به تفصیل](#3-فازها-به-تفصیل)
4. [ معیارهای موفقیت](#4-معیارهای-موفقیت)
5. [ مدیریت ریسک](#5-مدیریت-ریسک)
6. [ گزارش‌دهی](#6-گزارشدهی)

---

## 1. Executive Summary

### 🎯 Main Objective
ارتقاء و تکمیل پلتفرم تحلیل سهام BedaanWaves با افزودن قابلیت‌های پیشرفته، بهینه‌سازی عملکرد، و رفع مشکلات موجود.

### 📊 Current Status
- **بک‌اند:** 80+ سرویس، معماری DDD، پوشش تست متوسط
- **فرانت‌اند:** Next.js 16, React 19, 100+ کامپوننت
- **دیتابیس:** PostgreSQL با 25+ جدول
- **مشکل اصلی:** ناهماهنگی داده‌ها در Dashboard (رفع شد در فاز ۱)

### 🎯 Expected Results
- بهبود 70% زمان پاسخ API با Redis Cache
- افزودن ۶ API جدید برای مقایسه، پیش‌بینی و هشدار
- پوشش تست E2E کامل با Playwright
- مستندات Swagger کامل

---

## 2. General Roadmap

```
فاز ۰: آماده‌سازی        [██████████] 100% ✅
فاز ۱: رفع Inconsistency [██████████] 100% ✅
فاز ۲: Redis Cache       [░░░░░░░░░░]  0% ⏳
فاز ۳: APIهای جدید       [░░░░░░░░░░]  0% ⏳
فاز ۴: E2E Tests         [░░░░░░░░░░]  0% ⏳
فاز ۵: ویژگی‌های پیشرفته  [░░░░░░░░░░]  0% ⏳
فاز ۶: مستندسازی        [░░░░░░░░░░]  0% ⏳
```

### ⏱️ Estimated Timeline

| Phase | Duration | Start | End |
|-----|-----|-------|-------|
| فاز ۰ | ۱ روز | 2026-09-04 | 2026-09-04 ✅ |
| فاز ۱ | ۱ روز | 2026-09-04 | 2026-09-04 ✅ |
| فاز ۲ | ۲ روز | 2026-09-05 | 2026-09-06 |
| فاز ۳ | ۳ روز | 2026-09-07 | 2026-09-09 |
| فاز ۴ | ۲ روز | 2026-09-10 | 2026-09-11 |
| فاز ۵ | ۳ روز | 2026-09-12 | 2026-09-14 |
| فاز ۶ | ۱ روز | 2026-09-15 | 2026-09-15 |

**تاریخ تکمیل پروژه:** 2026-09-15 (۱۱ روز کاری)

---

## 3. Phases in Detail

### ✅ Phase 0: Preparation (Completed)

**هدف:** بررسی وضعیت فعلی و آماده‌سازی برای شروع

**وظایف:**
- [x] بررسی ساختار پروژه
- [x] شناسایی تکنولوژی‌های استفاده شده
- [x] بررسی فایل‌های پیکربندی
- [x] مستندسازی وضعیت فعلی

**خروجی‌ها:**
- گزارش ساختار پروژه
- لیست تکنولوژی‌ها
- نقشه ماژول‌ها

---

### ✅ Phase 1: Fix Data Inconsistency (Completed)

**هدف:** رفع ناهماهنگی تاریخ در Spider Chart و Trend Chart

**مشکل:** Spider Chart و Trend Chart از دو API جداگانه استفاده می‌کردند که تاریخ‌های متفاوتی برمی‌گرداندند.

**راه‌حل:**
1. ایجاد DateStore مرکزی ([`useDateStore.ts`](file:///e:/BedaanWaves/frontend/src/store/useDateStore.ts))
2. ایجاد کامپوننت DateSelector ([`DateSelector.tsx`](file:///e:/BedaanWaves/frontend/src/components/dashboard/DateSelector.tsx))
3. به‌روزرسانی Dashboard Page برای استفاده از effectiveDate

**وظایف:**
- [x] ایجاد DateStore با Zustand
- [x] پیاده‌سازی انتخاب تاریخ
- [x] به‌روزرسانی API Calls با end_date
- [x] تست همگام‌سازی تاریخ

**خروجی‌ها:**
- فایل [`useDateStore.ts`](file:///e:/BedaanWaves/frontend/src/store/useDateStore.ts)
- فایل [`DateSelector.tsx`](file:///e:/BedaanWaves/frontend/src/components/dashboard/DateSelector.tsx)
- به‌روزرسانی [`page.tsx`](file:///e:/BedaanWaves/frontend/src/app/dashboard/page.tsx)

**معیار موفقیت:**
- ✅ Spider Chart و Trend Chart از یک تاریخ مشترک استفاده می‌کنند
- ✅ کاربر می‌تواند تاریخ مورد نظر را انتخاب کند
- ✅ گزینه استفاده خودکار از آخرین تاریخ موجود

---

### ⏳ Phase 2: Optimization - Add Redis Cache

**هدف:** بهبود 70% زمان پاسخ API با استفاده از Redis Cache

**مشکل فعلی:**
- زمان پاسخ APIها بالا است (گاهی تا ۶۰ ثانیه)
- کوئری‌های تکراری به دیتابیس
- عدم استفاده از Cache Layer

**راه‌حل:**
1. نصب مستقیم Redis بر روی سیستم عامل (بدون Docker)
2. پیاده‌سازی Redis Backend برای Cache Service
3. به‌روزرسانی سرویس‌های اصلی برای استفاده از Cache
4. تنظیم TTL مناسب برای داده‌های مختلف

**وظایف:**
- [ ] پیکربندی Redis به صورت بومی روی سیستم عامل
- [ ] پیاده‌سازی RedisCacheBackend
- [ ] به‌روزرسانی CacheService
- [ ] اضافه کردن Cache به APIهای پرتکرار
- [ ] تنظیم TTL برای انواع داده‌ها
- [ ] تست عملکرد

**خروجی‌ها:**
- فایل `redis_cache_backend.py`
- به‌روزرسانی `cache_service.py`
- فایل‌های پیکربندی Redis بومی
- گزارش بهبود عملکرد

**معیار موفقیت:**
- 70% کاهش زمان پاسخ APIهای پرتکرار
- کاهش 50% load دیتابیس
- hit rate بالای 80% برای Cache

---

### ⏳ Phase 3: New APIs

**هدف:** افزودن ۶ API جدید برای مقایسه، پیش‌بینی و هشدار

**APIهای مورد نیاز:**

| Number | Name | Description |
|-------|-----|---------|
| 21 | Compare | مقایسه چند سهم |
| 22 | Composite Score | امتیاز ترکیبی |
| 23 | Forecast | پیش‌بینی روند |
| 24 | Sentiment | تحلیل احساسات |
| 25 | Portfolio | مدیریت سبد سهام |
| 26 | Alerts | سیستم هشدار |

**وظایف:**
- [ ] طراحی Schema APIها
- [ ] پیاده‌سازی Compare API
- [ ] پیاده‌سازی Forecast API
- [ ] پیاده‌سازی Alerts API
- [ ] مستندسازی Swagger
- [ ] تست APIها

**خروجی‌ها:**
- ۶ فایل Router جدید
- فایل‌های Service مرتبط
- مستندات Swagger
- تست‌های Postman

---

### ⏳ Phase 4: E2E Tests with Playwright

**هدف:** پوشش تست End-to-End کامل برای جلوگیری از باگ‌های مخفی

**وظایف:**
- [ ] پیکربندی Playwright
- [ ] نوشتن تست‌های Dashboard
- [ ] نوشتن تست‌های Stock Detail
- [ ] نوشتن تست‌های Authentication
- [ ] تنظیم CI/CD برای تست‌ها

**خروجی‌ها:**
- فایل `playwright.config.ts`
- پوشه `e2e/tests/`
- گزارش پوشش تست

---

### ⏳ Phase 5: Advanced Features

**ویژگی‌ها:**
1. **مقایسه سهام:** انتخاب ۲-۵ سهم و مقایسه چارت‌ها
2. **Dark Mode:** پشتیبانی از تم تاریک
3. **داشبورد قابل شخصی‌سازی:** Drag & Drop چارت‌ها
4. **پیش‌بینی:** استفاده از ML برای پیش‌بینی روند

**وظایف:**
- [ ] پیاده‌سازی Compare Feature
- [ ] پیاده‌سازی Dark Mode
- [ ] پیاده‌سازی Dashboard Customization
- [ ] بهبود ML Models

---

### ⏳ Phase 6: Documentation

**مستندات مورد نیاز:**
1. **API Documentation:** Swagger/OpenAPI
2. **Architecture Guide:** معماری سیستم
3. **Deployment Guide:** راهنمای استقرار
4. **Developer Guide:** راهنمای توسعه‌دهندگان
5. **User Guide:** راهنمای کاربران

**وظایف:**
- [ ] تکمیل Swagger Docs
- [ ] نوشتن Architecture Guide
- [ ] نوشتن Deployment Guide
- [ ] ایجاد User Guide

---

## 4. Success Criteria

### General Project Criteria

| Criteria | Goal | Measurement Method |
|-------|-----|------------------|
| زمان پاسخ API | < 200ms (p95) | Prometheus/Grafana |
| پوشش تست | > 80% | Coverage Report |
| Uptime | > 99.9% | Monitoring |
| رضایت کاربر | > 4.5/5 | User Survey |

### Phase Criteria

| Phase | Success Criteria | Status |
|-----|--------------|-------|
| فاز ۰ | مستندسازی کامل وضعیت فعلی | ✅ تکمیل |
| فاز ۱ | همگام‌سازی ۱۰۰% تاریخ در چارت‌ها | ✅ تکمیل |
| فاز ۲ | ۷۰% کاهش زمان پاسخ API | ⏳ در انتظار |
| فاز ۳ | ۶ API جدید کاملاً عملیاتی | ⏳ در انتظار |
| فاز ۴ | پوشش E2E برای تمام flowهای اصلی | ⏳ در انتظار |
| فاز ۵ | ۴ ویژگی پیشرفته عملیاتی | ⏳ در انتظار |
| فاز ۶ | ۵ مجموعه مستندات کامل | ⏳ در انتظار |

---

## 5. Risk Management

### Identified Risks

| Risk | Probability | Impact | Solution |
|------|--------|-------|--------|
| ناسازگاری با داده‌های قدیمی | متوسط | بالا | Migration Scripts |
| کاهش عملکرد با Redis | کم | بالا | Monitoring و Tuning |
| باگ‌های E2E Tests | متوسط | متوسط | CI/CD Pipeline |
| عدم پذیرش کاربر از UI جدید | کم | متوسط | A/B Testing |

---

## 6. Reporting

### Reporting Framework

| Report Type | Frequency | Audience |
|-----------|--------|-------|
| Daily Standup | روزانه | تیم توسعه |
| Progress Report | هفتگی | مدیر پروژه |
| Demo | دو هفته‌ای | ذینفعان |
| Final Report | پایان پروژه | همه |

---

## Appendices

### A. Terms and Definitions

- **DateStore:** مدیریت مرکزی تاریخ برای همگام‌سازی چارت‌ها
- **Redis Cache:** سیستم کشینگ در حافظه برای بهبود عملکرد
- **E2E Test:** تست End-to-End برای شبیه‌سازی رفتار کاربر
- **API:** Application Programming Interface

### B. Resources and References

1. [FastAPI Documentation](https://fastapi.tiangolo.com/)
2. [Next.js Documentation](https://nextjs.org/docs)
3. [Redis Documentation](https://redis.io/documentation)
4. [Playwright Documentation](https://playwright.dev/)

### C. Change History

| Date | Version | Changes | Author |
|-------|------|---------|---------|
| 2026-09-04 | 1.0.0 | ایجاد مستند Master Plan | AI Assistant |

---

**پایان مستند Master Plan**

برای ادامه، فاز مورد نظر را انتخاب کنید:
- [ ] فاز ۲: Redis Cache
- [ ] فاز ۳: APIهای جدید
- [ ] فاز ۴: E2E Tests
- [ ] فاز ۵: ویژگی‌های پیشرفته
- [ ] فاز ۶: مستندسازی
