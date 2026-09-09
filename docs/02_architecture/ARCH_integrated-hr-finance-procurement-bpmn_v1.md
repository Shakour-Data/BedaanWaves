# معماری یکپارچه HR، Finance و Procurement — BPMN/PlantUML v1

**عنوان:** Integrated HR, Finance & Procurement Management System  
**نسخه:** v1.0  
**تاریخ:** 2026-09-09  
**وضعیت:** پیش‌نویس برای مستندسازی  
**نگارنده:** Kilo

---

## فهرست مطالب

1. [مقدمه](#1-مقدمه)
2. [سطح ۱ — نمای کلی فرآیندها (Pools)](#2-سطح-1--نمای-کلی-فرآیندها-pools)
3. [سطح ۲ — فرآیندهای حوزه‌ای](#3-سطح-2--فرآیندهای-حوزه‌ای)
4. [سطح ۳ — نمودارهای دقیق](#4-سطح-3--نمودارهای-دقیق)
5. [ردپا (Traceability) به DFD و UML](#5-ردپا-traceability-به-dfd-و-uml)
6. [کنوانسیون‌های نام‌گذاری](#6-کنوانسیون‌های-نام‌گذاری)
7. [ضوابط و محدودیت‌ها](#7-ضوابط-و-محدودیت‌ها)

---

## ۱. مقدمه

این سند معماری فرآیندهای یکپارچه **منابع انسانی (HR)**، **مالی (Payroll/Budget)** و **تدارکات (Procurement/Inventory)** را به صورت **BPMN-style executable process diagrams** با استفاده از **PlantUML Activity Notation** مدل‌سازی می‌کند.

### ۱.۱ مقیاس مدل‌سازی

| سطح | محدوده | خروجی |
|-----|--------|-------|
| **Level 1** | نمای کلی سیستم | ۸ Pool درون یک نمودار |
| **Level 2** | شش حوزه کاری | ۶ نمودار جداگانه |
| **Level 3** | جریان‌های بحرانی | ۳ نمودار با استثناها |

### ۱.۲ منظور از Executable

هر نمودار شامل **Start Event**، **User/Service Tasks**، **Gateways**، **Message Flows**، **Intermediate Events** و **End Events** است و قابل اجرا در موتور BPMN (مانند Camunda یا Flowable) می‌باشد.

---

## ۲. سطح ۱ — نمای کلی فرآیندها (Pools)

در این سطح، هشت استخر (Pool) اصلی سیستم به صورت هم‌زمان ارائه می‌شوند:

1. **Employee** (کارمند)
2. **HR Manager** (مدیر منابع انسانی)
3. **Finance Manager** (مدیر مالی)
4. **Procurement Officer** (کارمند تدارکات)
5. **Warehouse Officer** (کارمند انبار)
6. **Supplier** (تامین‌کننده)
7. **Bank/Payment Gateway** (بانک/درگاه پرداخت)
8. **Executive/Analyst** (مدیرعامل/تحلیلگر)

### ۲.۱ نمودار PlantUML — نمای کلی

```plantuml
@startuml ARCH-L1-Integrated-Overview
left to right direction
skinparam backgroundColor #FEFEFE
skinparam defaultTextAlignment center

title L1: نمای کلی یکپارچه HR، Finance & Procurement

|Employee|
start
:ورود به سیستم\n(Login);
:ثبت درخواست مرخصی/شیفت\n(LeaveRequest);
:ارسال درخواست به HR Manager;
stop

|HR Manager|
:دریافت درخواست مرخصی\n(Receive LeaveRequest);
if (تایید؟) then (بله)
  :تایید درخواست\n(Approve Leave);
  :ثبت در `AuditLog`;
else (خیر)
  :رد درخواست\n(Reject Leave);
  :ثبت در `AuditLog`;
  stop
endif
:اعلان به Employee\n(Notify);
:ارسال داده به PayrollRun;
stop

|PayrollRun|
:دریافت داده‌های حضور\n(Attendance Data);
:فراخوانی `calculateSalary()`\n(Service Task);
if (خطا در محاسبه؟) then (بله)
  :ثبت خطا در `AuditLog`\n(Error Intermediate Event);
  stop
else (خیر)
  :ذخیره فیش حقوقی\n(Salary Slip);
endif
:ارسال خلاصه به Finance Manager;
stop

|Finance Manager|
:دریافت خلاصه حقوق\n(Receive Payroll Summary);
if (بودجه کافی؟) then (بله)
  :تایید پرداخت\n(Approve Payment);
  :ایجاد `Payment`\n(Service Task);
  :ارسال درخواست به Bank/Payment Gateway;
else (خیر)
  :درخواست کسر از بودجه بعدی\n(Defer Payment);
  :ثبت در `AuditLog`;
  stop
endif
stop

|Budget|
:دریافت درخواست پرداخت\n(Receive Payment Request);
:فراخوانی `checkBudget()`\n(Service Task);
if (بودجه کافی؟) then (بله)
  :کسر از `BudgetAllocation`\n(Update Budget);
else (خیر)
  :رد پرداخت\n(Reject Payment);
  :اعلان به Finance Manager\n(Notify);
  stop
endif
:ثبت در `AuditLog`;
stop

|Procurement Officer|
:ایجاد درخواست خرید\n(Create PurchaseRequest);
:دریافت `Product`\n(Product Catalog);
:ارسال درخواست به Finance Manager;
stop

|Warehouse Officer|
:دریافت کالا از Supplier\n(Receive Goods);
:ثبت `GoodsReceipt`\n(Service Task);
:فراخوانی `allocateStock()`\n(Service Task);
:به‌روزرسانی `StockLot`\n(Update StockLot);
:اعلان به Executive/Analyst;
stop

|Supplier|
:دریافت PurchaseOrder\n(Receive PO);
:آماده‌سازی کالا\n(Packaging);
:ارسال کالا به Warehouse;
stop

|Bank/Payment Gateway|
:دریافت درخواست پرداخت\n(Receive Payment Request);
if (تایید تراکنش؟) then (بله)
  :پرداخت موفق\n(Successful Transfer);
  :اعلان به Finance Manager;
else (خیر)
  :پرداخت ناموفق\n(Failed Transfer);
  :اعلان خطا به Finance Manager\n(Error Intermediate Event);
  stop
endif
stop

|Executive/Analyst|
:دریافت داده‌های集成\n(Integrated Data);
:فراخوانی `generateReport()`\n(Service Task);
:ایجاد `Report`\n(Report Generation);
:ارسال به سمت مدیریت\n(Deliver Report);
stop

@enduml
```

### ۲.۲ جدول جریان خوشحال (Happy Path) — سطح ۱

| مرحله | Actor | فعالیت | خروجی |
|-------|-------|---------|-------|
| ۱ | Employee | ورود و ثبت درخواست مرخصی | `LeaveRequest` |
| ۲ | HR Manager | تایید درخواست | `AuditLog` + اعلان |
| ۳ | HR Manager | ارسال داده به PayrollRun | داده‌های حضور |
| ۴ | PayrollRun | محاسبه حقوق (`calculateSalary`) | `SalarySlip` |
| ۵ | Finance Manager | تایید پرداخت | `Payment` |
| ۶ | Bank/Payment Gateway | پرداخت موفق | تأییدیه تراکنش |
| ۷ | Procurement Officer | ایجاد درخواست خرید | `PurchaseRequest` |
| ۸ | Supplier | ارسال کالا | `GoodsReceipt` |
| ۹ | Warehouse Officer | تخصیص موجودی (`allocateStock`) | `StockLot` به‌روز |
| ۱۰ | Executive/Analyst | تولید گزارش (`generateReport`) | `Report` |

### ۲.۳ جدول جریان استثنا (Exception Flow) — سطح ۱

| کد استثنا | مبدأ | رویداد | واکنش سیستم |
|-----------|------|--------|--------------|
| EX-01 | Employee | ورود ناموفق | مسدود شدن بعد از ۳ تلاش، ثبت در `AuditLog` |
| EX-02 | HR Manager | عدم تایید مرخصی | ارسال اعلان به Employee، بستن `LeaveRequest` |
| EX-03 | PayrollRun | خطا در `calculateSalary()` |Intermediate Event خطا، توقف جریان، اطلاع به HR |
| EX-04 | Finance Manager | عدم تایید پرداخت | انتقال به دوره بعدی بودجه، ثبت در `AuditLog` |
| EX-05 | Budget | `checkBudget()` ناموفق | رد پرداخت، اعلان به Finance Manager |
| EX-06 | Bank/Payment Gateway | تراکنش ناموفق | Intermediate Event خطا، بازگشت به Finance Manager برای	retry |
| EX-07 | Warehouse Officer | عدم تطابق `GoodsReceipt` با `PurchaseOrder` | ایجاد گزارش تفاوت، توقف تخصیص |
| EX-08 | Executive/Analyst | ناکافی بودن داده‌ها | Intermediate Event، درخواست تکمیل از منابع دیگر |

---

## ۳. سطح ۲ — فرآیندهای حوزه‌ای

هر حوزه در نمودار جداگانه با泳道های مرتبط رسم می‌شود.

### ۳.۱ حوزه HR — Recruitment & Leave Management

```plantuml
@startuml ARCH-L2-HR
left to right direction
skinparam backgroundColor #FEFEFE

title L2: فرآیند منابع انسانی (HR)

|Employee|
start
:درخواست استخدام/مرخصی\n(Create Request);
if (نوع درخواست؟) then (استخدام)
  :ارسال رزومه\n(Submit Resume);
  :ثبت Candidate;
else (مرخصی)
  :ارسال فرم مرخصی\n(Submit Leave Form);
endif
:ارسال به HR Manager\n(Message Flow);
stop

|HR Manager|
:دریافت درخواست\n(Receive Request);
if (استخدام؟) then (بله)
  :بررسی رزومه\n(Review Resume);
  if (تایید مصاحبه؟) then (بله)
    :دعوت به مصاحبه\n(Schedule Interview);
    :ثبت در `AuditLog`;
  else (خیر)
    :رد رزومه\n(Reject);
    :اعلان به Employee\n(Notify);
    stop
  endif
else (مرخصی)
  :بررسی موجودی مرخصی\n(Check Leave Balance);
  if (موجود؟) then (بله)
    :تایید مرخصی\n(Approve Leave);
    :به‌روزرسانی Leave Balance;
  else (خیر)
    :رد مرخصی\n(Reject);
    :اعلان به Employee;
    stop
  endif
endif
:ارسال نتیجه به Employee\n(Message Flow);
stop

@enduml
```

**جریان خوشحال (Happy Path):** کارمند درخواست می‌کند → HR Manager بررسی و تایید می‌کند → اعلان به کارمند.

**جریان استثنا (Exception Flow):** رزومه رد می‌شود یا موجودی مرخصی ناکافی است → اعلان منفی.

### ۳.۲ حوزه Payroll — حقوق و دستمزد

```plantuml
@startuml ARCH-L2-Payroll
left to right direction
skinparam backgroundColor #FEFEFE

title L2: فرآیند پرداخت حقوق (Payroll)

|HR Manager|
start
:تایید لیست کارکنان\n(Approve Payroll List);
:ارسال داده‌های حضور و غیاب\n(Send Attendance Data);
stop

|PayrollRun|
:دریافت داده‌ها\n(Receive Data);
:فراخوانی `calculateSalary()`\n(Service Task);
:محاسبه کسورات و مزایا\n(Calc Deductions & Benefits);
:تولید Salary Slip\n(Generate Slip);
:ارسال خلاصه به Finance Manager\n(Message Flow);
stop

|Finance Manager|
:دریافت خلاصه حقوق\n(Receive Payroll Summary);
:بررسی `BudgetAllocation`\n(Review Budget);
if (بودجه کافی؟) then (بله)
  :تایید پرداخت\n(Approve Payment);
  :ایجاد `Payment`\n(Service Task);
  :ارسال به Bank/Payment Gateway;
else (خیر)
  :درخواست تمدید بودجه\n(Request Budget Extension);
  stop
endif
stop

|Bank/Payment Gateway|
:دریافت درخواست پرداخت\n(Receive Payment Request);
if (تراکنش موفق؟) then (بله)
  :پرداخت به حساب کارکنان\n(Transfer to Employees);
  :اعلان موفقیت به Finance Manager\n(Notify);
else (خیر)
  :خطای تراکنش\n(Transaction Error);
  :اعلان به Finance Manager\n(Intermediate Event);
  stop
endif
stop

@enduml
```

**جریان خوشحال (Happy Path):** تایید لیست → محاسبه حقوق → تایید مالی → پرداخت موفق.

**جریان استثنا (Exception Flow):** خطا در محاسبه حقوق یا ناموفق بودن تراکنش → توقف و اطلاع.

### ۳.۳ حوزه Budget — بودجه و تخصیص

```plantuml
@startuml ARCH-L2-Budget
left to right direction
skinparam backgroundColor #FEFEFE

title L2: فرآیند مدیریت بودجه (Budget)

|Executive/Analyst|
start
:تعریف بودجه سالانه\n(Define Annual Budget);
:ایجاد `Budget`\n(Service Task);
:تقسیم به `BudgetAllocation`\n(Allocate to Departments);
stop

|Finance Manager|
:دریافت درخواست هزینه\n(Receive Expense Request);
:فراخوانی `checkBudget()`\n(Service Task);
if (بودجه کافی؟) then (بله)
  :کسر از `BudgetAllocation`\n(Update Allocation);
  :تایید هزینه\n(Approve Expense);
else (خیر)
  :رد هزینه\n(Reject Expense);
  :اعلان به Executive/Analyst\n(Notify);
  stop
endif
:ثبت در `AuditLog`;
stop

|Procurement Officer|
:دریافت تأییدیه بودجه\n(Receive Budget Approval);
:پیش‌روی به تدارکات\n(Proceed to Procurement);
stop

@enduml
```

**جریان خوشحال (Happy Path):** تعریف بودجه → تخصیص → بررسی کافی بودن → کسر از بودجه.

**جریان استثنا (Exception Flow):** بودجه ناکافی → رد هزینه → اطلاع به مدیریت.

### ۳.۴ حوزه Procurement — خرید و تدارکات

```plantuml
@startuml ARCH-L2-Procurement
left to right direction
skinparam backgroundColor #FEFEFE

title L2: فرآیند تدارکات (Procurement)

|Procurement Officer|
start
:ایجاد `PurchaseRequest`\n(Service Task);
:ارسال به Finance Manager\n(Message Flow);
stop

|Finance Manager|
:بررسی `checkBudget()`\n(Service Task);
if (بودجه کافی؟) then (بله)
  :تایید درخواست خرید\n(Approve PR);
  :ایجاد `PurchaseOrder`\n(Service Task);
  :ارسال به Supplier\n(Message Flow);
else (خیر)
  :رد درخواست خرید\n(Reject PR);
  :اعلان به Procurement Officer\n(Notify);
  stop
endif
stop

|Supplier|
:دریافت `PurchaseOrder`\n(Receive PO);
:تأیید سفارش\n(Acknowledge Order);
:آماده‌سازی و ارسال کالا\n(Ship Goods);
:ارسال به Warehouse Officer\n(Message Flow);
stop

|Warehouse Officer|
:دریافت کالا\n(Receive Goods);
:ثبت `GoodsReceipt`\n(Service Task);
:فراخوانی `allocateStock()`\n(Service Task);
:به‌روزرسانی `StockLot`\n(Update StockLot);
:اعلان به Procurement Officer\n(Notify);
stop

@enduml
```

**جریان خوشحال (Happy Path):** ایجاد درخواست → تایید بودجه → ارسال سفارش → دریافت کالا → تخصیص موجودی.

**جریان استثنا (Exception Flow):** بودجه ناکافی → رد درخواست → اطلاع به Procurement Officer.

### ۳.۵ حوزه Inventory — مدیریت موجودی

```plantuml
@startuml ARCH-L2-Inventory
left to right direction
skinparam backgroundColor #FEFEFE

title L2: فرآیند مدیریت موجودی (Inventory)

|Warehouse Officer|
start
:دریافت `GoodsReceipt`\n(Receive GR);
:بازرسی فیزیکی کالا\n(Physical Inspection);
if (تطابق با سفارش؟) then (بله)
  :ثبت `StockLot`\n(Create StockLot);
  :فراخوانی `allocateStock()`\n(Service Task);
  :به‌روزرسانی موجودی\n(Update Inventory);
else (خیر)
  :ایجاد گزارش تفاوت\n(Discrepancy Report);
  :اعلان به Procurement Officer\n(Notify);
  stop
endif
:بررسی حداقل موجودی\n(Check Reorder Level);
if (نیاز به خرید؟) then (بله)
  :ایجاد درخواست خرید تلقیمی\n(Auto PR);
else (خیر)
  :پایان جریان\n(End);
endif
stop

|Executive/Analyst|
:دریافت گزارش موجودی\n(Receive Inventory Report);
:بررسی گردش کالا\n(Review Turnover);
stop

@enduml
```

**جریان خوشحال (Happy Path):** دریافت کالا → بازرسی → ثبت موجودی → تخصیص.

**جریان استثنا (Exception Flow):** عدم تطابق → گزارش تفاوت → اطلاع به Procurement Officer.

### ۳.۶ حوزه Reporting — گزارش‌گیری و تحلیل

```plantuml
@startuml ARCH-L2-Reporting
left to right direction
skinparam backgroundColor #FEFEFE

title L2: فرآیند گزارش‌گیری (Reporting)

|Executive/Analyst|
start
:تعریف معیارهای گزارش\n(Define Report Criteria);
:درخواست داده‌های集成\n(Request Integrated Data);
stop

|System|
:تجمیع داده از HR، Payroll، Budget\n(Aggregate Data);
:فراخوانی `generateReport()`\n(Service Task);
:ایجاد `Report`\n(Service Task);
:ارسال به Executive/Analyst\n(Message Flow);
stop

|Executive/Analyst|
:دریافت `Report`\n(Receive Report);
:بررسی و امضا\n(Review & Sign);
if (نیاز به اصلاح؟) then (بله)
  :درخواست اصلاح\n(Request Revision);
  stop
else (خیر)
  :انتشار گزارش\n(Publish Report);
  :ثبت در `AuditLog`;
  stop
endif
stop

@enduml
```

**جریان خوشحال (Happy Path):** تعریف معیار → تجمیع داده → تولید گزارش → انتشار.

**جریان استثنا (Exception Flow):** عدم کافی بودن داده → Intermediate Event → درخواست تکمیل.

---

## ۴. سطح ۳ — نمودارهای دقیق

### ۴.۱ تایید پرداخت حقوق (Payroll Approval)

```plantuml
@startuml ARCH-L3-PayrollApproval
left to right direction
skinparam backgroundColor #FEFEFE

title L3: جریان دقیق تایید پرداخت حقوق

|HR Manager|
start
:تایید لیست کارکنان\n(Approve Payroll List);
:امضا دیجیتال\n(Digital Sign);
:ارسال به PayrollRun\n(Message Flow);
stop

|PayrollRun|
:دریافت لیست تایید شده\n(Receive Approved List);
:فراخوانی `calculateSalary()`\n(Service Task);
:محاسبه نخل حقوقی\n(Calc Payroll);
if (خطای محاسبه؟) then (بله)
  :ثبت خطا در `AuditLog`\n(Error Intermediate Event);
  :اعلان به HR Manager\n(Notify);
  stop
else (خیر)
  :تولید Salary Slip\n(Generate Slip);
endif
:ارسال خلاصه به Finance Manager\n(Message Flow);
stop

|Finance Manager|
:دریافت خلاصه حقوق\n(Receive Summary);
:بررسی `BudgetAllocation`\n(Review Budget);
if (بودجه کافی؟) then (بله)
  :تایید پرداخت\n(Approve Payment);
  :ایجاد `Payment`\n(Service Task);
  :ارسال به Bank/Payment Gateway;
else (خیر)
  :رد پرداخت\n(Reject Payment);
  :اعلان به HR Manager و PayrollRun\n(Notify);
  stop
endif
stop

|Bank/Payment Gateway|
:دریافت درخواست پرداخت\n(Receive Payment Request);
if (تراکنش موفق؟) then (بله)
  :پرداخت به حساب کارکنان\n(Transfer);
  :اعلان موفقیت به Finance Manager\n(Notify);
else (خیر)
  :خطای تراکنش\n(Transaction Error);
  :Intermediate Event خطا;
  :اعلان به Finance Manager\n(Notify);
  :بازگشت به Finance Manager\n(Retry);
  stop
endif
stop

@enduml
```

#### جدول جریان خوشحال — L3 تایید حقوق

| مرحله | نقش | فعالیت | متد/ Entity |
|-------|-----|---------|-------------|
| ۱ | HR Manager | تایید لیست و امضا | — |
| ۲ | PayrollRun | محاسبه حقوق | `calculateSalary()` |
| ۳ | PayrollRun | تولید Salary Slip | `SalarySlip` |
| ۴ | Finance Manager | بررسی بودجه | `checkBudget()` |
| ۵ | Finance Manager | ایجاد Payment | `Payment` |
| ۶ | Bank/Payment Gateway | پرداخت موفق | — |

#### جدول جریان استثنا — L3 تایید حقوق

| کد استثنا | موقعیت | رویداد | واکنش |
|-----------|--------|--------|-------|
| EX-P01 | PayrollRun | خطا در `calculateSalary()` | Intermediate Event، ثبت در `AuditLog`، اعلان به HR |
| EX-P02 | Finance Manager | بودجه ناکافی | توقف جریان، اعلان به HR Manager |
| EX-P03 | Bank/Payment Gateway | تراکنش ناموفق | Intermediate Event، retry بعد از ۵ دقیقه، ثبت در `AuditLog` |

### ۴.۲ بررسی بودجه برای درخواست خرید (Budget-Check for Purchase Request)

```plantuml
@startuml ARCH-L3-BudgetCheck-PR
left to right direction
skinparam backgroundColor #FEFEFE

title L3: بررسی بودجه برای درخواست خرید

|Procurement Officer|
start
:ایجاد `PurchaseRequest`\n(Service Task);
:ارسال به Finance Manager\n(Message Flow);
stop

|Finance Manager|
:دریافت `PurchaseRequest`\n(Receive PR);
:فراخوانی `checkBudget()`\n(Service Task);
:دریافت `BudgetAllocation`\n(Read Allocation);
if (بودجه کافی؟) then (بله)
  :کسر موقت از بودجه\n(Reserve Budget);
  :تایید درخواست خرید\n(Approve PR);
  :ایجاد `PurchaseOrder`\n(Service Task);
  :ارسال به Supplier\n(Message Flow);
else (خیر)
  if (درخواست تخصیص مجدد؟) then (بله)
    :درخواست تخصیص مجدد\n(Request Reallocation);
    :اعلان به Executive/Analyst\n(Notify);
    stop
  else (خیر)
    :رد درخواست خرید\n(Reject PR);
    :اعلان به Procurement Officer\n(Notify);
    stop
  endif
endif
stop

|Supplier|
:دریافت `PurchaseOrder`\n(Receive PO);
:تأیید سفارش\n(Acknowledge);
stop

|Executive/Analyst|
:دریافت درخواست تخصیص مجدد\n(Receive Reallocation Request);
:بررسی اولویت‌ها\n(Review Priorities);
if (موافقت؟) then (بله)
  :تغییر `BudgetAllocation`\n(Update Allocation);
  :اعلان به Finance Manager\n(Notify);
else (خیر)
  :رد درخواست تخصیص\n(Reject Reallocation);
  :اعلان به Finance Manager\n(Notify);
  stop
endif
stop

|Finance Manager|
:دریافت پاسخ Executive/Analyst\n(Receive Response);
if (تخصیص مجدد موفق؟) then (بله)
  :تکرار فراخوانی `checkBudget()`\n(Service Task);
  if (حالا کافی؟) then (بله)
    :تایید نهایی PR\n(Final Approve);
    :ایجاد `PurchaseOrder`\n(Service Task);
    :ارسال به Supplier;
  else (خیر)
    :رد نهایی\n(Final Reject);
    stop
  endif
else (خیر)
  :ثبت در `AuditLog`\n(Log Final Rejection);
  stop
endif
stop

@enduml
```

#### جدول جریان خوشحال — L3 بررسی بودجه

| مرحله | نقش | فعالیت | متد/ Entity |
|-------|-----|---------|-------------|
| ۱ | Procurement Officer | ایجاد PurchaseRequest | `PurchaseRequest` |
| ۲ | Finance Manager | بررسی بودجه | `checkBudget()` |
| ۳ | Finance Manager | کسر از `BudgetAllocation` | `BudgetAllocation` |
| ۴ | Finance Manager | ایجاد PurchaseOrder | `PurchaseOrder` |
| ۵ | Supplier | تأیید سفارش | — |

#### جدول جریان استثنا — L3 بررسی بودجه

| کد استثنا | موقعیت | رویداد | واکنش |
|-----------|--------|--------|-------|
| EX-B01 | Finance Manager | بودجه ناکافی، بدون درخواست reassign | رد PR، اعلان به Procurement Officer |
| EX-B02 | Executive/Analyst | رد درخواست reassign | توقف جریان، ثبت در `AuditLog` |
| EX-B03 | Finance Manager | reassign موفق اما هنوز ناکافی | رد نهایی PR، اعلان به Procurement Officer |

### ۴.۳ تخصیص موجودی (Stock Allocation)

```plantuml
@startuml ARCH-L3-StockAllocation
left to right direction
skinparam backgroundColor #FEFEFE

title L3: جریان دقیق تخصیص موجودی

|Warehouse Officer|
start
:دریافت `GoodsReceipt`\n(Receive GR);
:بازرسی فیزیکی کالا\n(Physical Inspection);
:اسکن بارکد/سériال\n(Scan Barcode/Serial);
:ثبت `GoodsReceipt` در سیستم\n(Record GR);
:فراخوانی `allocateStock()`\n(Service Task);
if (موجودی کافی در هدف؟) then (بله)
  :ایجاد `StockLot`\n(Service Task);
  :به‌روزرسانی `StockLot`\n(Update StockLot);
  :تخصیص به محل/لاین\n(Allocate to Location);
  :اعلان موفقیت به Procurement Officer\n(Notify);
else (خیر)
  :ایجاد `StockLot` با exceeded limit\n(Overflow Lot);
  :اعلان به Executive/Analyst\n(Notify Overflow);
  stop
endif
:ثبت در `AuditLog`;
stop

|Procurement Officer|
:دریافت اعلان تخصیص\n(Receive Allocation Notice);
if (نیاز به خرید مجدد؟) then (بله)
  :ایجاد `PurchaseRequest`\n(Service Task);
  stop
else (خیر)
  :پایان جریان\n(End);
endif
stop

|Executive/Analyst|
:دریافت اعلان Overflow\n(Receive Overflow Alert);
:بررسی ظرفیت انبار\n(Review Warehouse Capacity);
if (نیاز به انبار اضافی؟) then (بله)
  :تایید اجاره/گسترش انبار\n(Approve Warehouse Expansion);
  :اعلان به Warehouse Officer\n(Notify);
else (خیر)
  :تایید مدیریت Overflow\n(Approve Overflow Management);
  :اعلان به Warehouse Officer\n(Notify);
endif
stop

@enduml
```

#### جدول جریان خوشحال — L3 تخصیص موجودی

| مرحله | نقش | فعالیت | متد/ Entity |
|-------|-----|---------|-------------|
| ۱ | Warehouse Officer | دریافت GoodsReceipt | `GoodsReceipt` |
| ۲ | Warehouse Officer | بازرسی فیزیکی و اسکن | — |
| ۳ | Warehouse Officer | فراخوانی `allocateStock()` | `allocateStock()` |
| ۴ | Warehouse Officer | ایجاد و به‌روزرسانی `StockLot` | `StockLot` |
| ۵ | Warehouse Officer | تخصیص به محل | `StockLot.Location` |

#### جدول جریان استثنا — L3 تخصیص موجودی

| کد استثنا | موقعیت | رویداد | واکنش |
|-----------|--------|--------|-------|
| EX-S01 | Warehouse Officer | Overflow در `StockLot` | Intermediate Event، اعلان به Executive/Analyst |
| EX-S02 | Executive/Analyst | عدم تأیید گسترش انبار | توقف جریان، ثبت در `AuditLog` |
| EX-S03 | Warehouse Officer | عدم تطابق فیزیکی با `GoodsReceipt` | گزارش تفاوت، توقف تخصیص |

---

## ۵. ردپا (Traceability) به DFD و UML

### ۵.۱ نگاشت به DFD

| فرآیند BPMN (Activity) | فرآیند DFD | توضیحات |
|------------------------|------------|---------|
| `calculateSalary()` | DFD-04: Compute Payroll | محاسبه حقوق و دستمزد |
| `checkBudget()` | DFD-07: Validate Budget | بررسی کافی بودن بودجه |
| `allocateStock()` | DFD-10: Update Inventory | تخصیص موجودی به `StockLot` |
| `generateReport()` | DFD-12: Produce Reports | تولید گزارش یکپارچه |
| `Approve Leave` | DDF-03: Approve HR Requests | تایید درخواست‌های HR |
| `Create PurchaseOrder` | DFD-08: Issue Purchase Order | صدور سفارش خرید |
| `Record GoodsReceipt` | DFD-09: Record Goods Receipt | ثبت ورود کالا به انبار |
| `Process Payment` | DFD-11: Execute Payment | اجرای پرداخت از طریق بانک |

### ۵.۲ نگاشت به UML

| فعالیت BPMN | کلاس UML | متد UML | نوع |
|-------------|----------|---------|-----|
| محاسبه حقوق | `PayrollRun` | `calculateSalary()` | Service Task |
| بررسی بودجه | `Budget` | `checkBudget()` | Service Task |
| تخصیص موجودی | `Warehouse` | `allocateStock()` | Service Task |
| تولید گزارش | `ReportEngine` | `generateReport()` | Service Task |
| تایید درخواست | `HRManager` | `approveRequest()` | User Task |
| ایجاد سفارش خرید | `ProcurementOfficer` | `createPurchaseOrder()` | User Task |
| پرداخت | `PaymentGateway` | `executePayment()` | Service Task |
| ثبت دریافت کالا | `WarehouseOfficer` | `recordGoodsReceipt()` | User Task |

### ۵.۳ ماتریس ردیابی کامل

| شناسه BPMN | نام فرآیند | DFD | UML Class | UML Method | Entity | خروجی |
|------------|-----------|-----|-----------|------------|--------|-------|
| BPMN-HR-01 | Appove Leave | DFD-03 | HRManager | approveRequest() | LeaveRequest | Approved Leave |
| BPMN-HR-02 | Review Resume | DFD-03 | HRManager | reviewResume() | Candidate | Interview Schedule |
| BPMN-PAY-01 | Calculate Salary | DFD-04 | PayrollRun | calculateSalary() | Employee | SalarySlip |
| BPMN-PAY-02 | Execute Payment | DFD-11 | PaymentGateway | executePayment() | Payment | TransactionResult |
| BPMN-BUD-01 | Check Budget | DFD-07 | Budget | checkBudget() | BudgetAllocation | BudgetStatus |
| BPMN-BUD-02 | Allocate Budget | DFD-06 | Budget | allocateBudget() | Budget | BudgetAllocation |
| BPMN-PROC-01 | Create PR | DFD-05 | ProcurementOfficer | createPurchaseRequest() | PurchaseRequest | PR |
| BPMN-PROC-02 | Create PO | DFD-08 | ProcurementOfficer | createPurchaseOrder() | PurchaseOrder | PO |
| BPMN-INV-01 | Allocate Stock | DFD-10 | Warehouse | allocateStock() | StockLot | Allocated Stock |
| BPMN-INV-02 | Record GR | DFD-09 | WarehouseOfficer | recordGoodsReceipt() | GoodsReceipt | GR Record |
| BPMN-REP-01 | Generate Report | DFD-12 | ReportEngine | generateReport() | Report | Report File |

---

## ۶. کنوانسیون‌های نام‌گذاری

### ۶.۱ Entityها و اشیاء

| نام انگلیسی | نوع | توضیحات فارسی |
|------------|-----|---------------|
| `Employee` | Entity | کارمند |
| `PayrollRun` | Entity | اجرای پرداخت حقوق |
| `Budget` | Entity | بودجه کلی |
| `BudgetAllocation` | Entity | تخصیص بودجه به واحد |
| `PurchaseRequest` | Entity | درخواست خرید |
| `PurchaseOrder` | Entity | سفارش خرید |
| `Product` | Entity | کالا/خدمت |
| `StockLot` | Entity | لات موجودی |
| `GoodsReceipt` | Entity | ثبت ورود کالا |
| `Payment` | Entity | پرداخت |
| `Report` | Entity | گزارش |
| `AuditLog` | Entity | گزارش ممیزی |

### ۶.۲ متدهای UML

| متد | کلاس والد | توضیحات |
|-----|-----------|---------|
| `calculateSalary()` | `PayrollRun` | محاسبه حقوق خالص کارمند |
| `checkBudget()` | `Budget` | بررسی کافی بودن بودجه برای هزینه |
| `allocateStock()` | `Warehouse` / `StockManager` | تخصیص موجودی ورودی به لات‌ها |
| `generateReport()` | `ReportEngine` | تولید گزارش یکپارچه از داده‌های چند حوزه |

---

## ۷. ضوابط و محدودیت‌ها

1. **PlantUML Version:** این نمودارها با PlantUML v1.2024+ سازگار هستند.
2. **BPMN Executability:** برای اجرای واقعی در Camunda/Flowable، نیاز به افزودن **Data Objects**، **Signals**، **Error Events** و **Timer Events** اضافی است.
3. **Persian Rendering:** برخی محیط‌های PlantUML ممکن است از نمایش متن فارسی پشتیبانی نکنند؛ در آن صورت از تصاویر SVG خروجی استفاده شود.
4. **Pool Communication:** پیام‌ها در این سطح به صورت **Message Flow** مدل شده‌اند؛ در پیاده‌سازی واقعی باید از صف‌های.message broker استفاده شود.
5. **DFD Mapping:** نگاشت DFD بر اساس DFD سطح ۱ سیستم یکپارچه است؛ در صورت تغییر DFD، این سند نیاز به به‌روزرسانی دارد.
6. **Traceability:** هر `BPMN-XXX` باید در **Requirement Traceability Matrix (RTM)** به سند نیازمندی ردیابی شود.

---

*پایان سند*
