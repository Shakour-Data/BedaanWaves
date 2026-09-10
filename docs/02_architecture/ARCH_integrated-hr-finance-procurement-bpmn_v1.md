# BPMN 2.0 — سیستم یکپارچه مدیریت منابع انسانی، مالی و تدارکات

**عنوان:** Integrated HR, Finance & Procurement Management System  
**نسخه:** v1.0  
**تاریخ:** 2026-09-09  
**قالب:** PlantUML Activity Notation با برچسب‌گذاری BPMN-style

---

## ۱. مقدمه و مقیاس مدل‌سازی

این سند فرایندهای کسب‌وکار سامانه را در سه سطح مدل‌سازی می‌کند. PlantUML Activity Notation برای نمایش استخرها،_LANE_ها، فعالیت‌ها، گیت‌ها و رویدادها به‌کار رفته است؛ برای اجرای مستقیم در Camunda یا Flowable باید مدل به BPMN 2.0 XML تبدیل و Data Object، Signal، Timer و Error Event آن اضافه شود.

| سطح | هدف | خروجی |
|---|---|---|
| ۱ | نمای کلان و ارتباط بازیگران | Process Overview با Pool/Lane |
| ۲ | فرایندهای قابل اجرا در هر حوزه | شش Process Diagram مستقل |
| ۳ | تسک‌های عملیاتی و استثناهای بحرانی | Payroll Approval، Budget Check PR، Stock Allocation |

نام‌های مشترک با DFD و UML: `Employee`، `PayrollRun`، `PayrollLine`، `Budget`، `BudgetAllocation`، `PurchaseRequest`، `PurchaseOrder`، `Product`، `StockLot`، `GoodsReceipt`، `Payment`، `Report` و `AuditLog`.

---

## ۲. سطح ۱ — نمای کلان فرایندها

```plantuml
@startuml BPMN-L1-Overview
left to right direction
skinparam backgroundColor #FEFEFE
skinparam defaultTextAlignment center

title BPMN Level 1 — Process Overview

|Employee|
start
:Submit personal data / leave / attendance;
:Receive notification and salary slip;
stop

|HR Manager|
:Receive HR request;
if (Request type?) then (Employment)
  :Review recruitment or transfer;
else (Leave)
  :Check leave balance;
endif
if (Approved?) then (Yes)
  :Approve HR request;
  :Publish attendance/eligibility event;
else (No)
  :Reject HR request;
endif
:Write AuditLog;
stop

|PayrollRun|
:Receive approved employee data;
:Invoke calculateSalary();
:Create PayrollRun and PayrollLine;
:Send payroll summary;
stop

|Finance Manager|
:Receive payroll or expense summary;
:Invoke checkBudget();
if (Budget available?) then (Yes)
  :Approve payment;
  :Create Payment;
else (No)
  :Defer or reject payment;
endif
stop

|Budget|
:Receive funding request;
:Read BudgetAllocation;
if (Credit sufficient?) then (Yes)
  :Reserve credit;
else (No)
  :Return insufficient-budget result;
endif
stop

|Procurement Officer|
:Create PurchaseRequest;
:Receive budget decision;
if (Approved?) then (Yes)
  :Issue PurchaseOrder;
else (No)
  :Revise or cancel request;
endif
stop

|Warehouse Officer|
:Receive GoodsReceipt;
:Inspect goods;
:Invoke allocateStock();
:Update StockLot;
stop

|Supplier|
:Receive PurchaseOrder;
:Acknowledge order;
:Ship goods;
stop

|Bank/Payment Gateway|
:Receive Payment request;
if (Transaction success?) then (Yes)
  :Return payment confirmation;
else (No)
  :Return payment failure;
endif
stop

|Executive/Analyst|
:Define report criteria;
:Invoke generateReport();
:Receive Report and dashboard;
stop

' Message-level handoffs are represented by labeled activities.
Employee ..> HR Manager : personal data / leave / attendance
HR Manager ..> PayrollRun : approved employee data
PayrollRun ..> Finance Manager : payroll summary
Finance Manager ..> Bank/Payment Gateway : payment instruction
Procurement Officer ..> Supplier : PurchaseOrder
Supplier ..> Warehouse Officer : GoodsReceipt
Warehouse Officer ..> Executive/Analyst : stock status
Executive/Analyst ..> Finance Manager : budget reallocation decision

@enduml
```

### جدول Happy Path سطح ۱

| مرحله | Actor / Lane | فعالیت | خروجی |
|---|---|---|---|
| ۱ | Employee | ثبت داده پرسنلی، مرخصی یا حضور | رویداد ورودی |
| ۲ | HR Manager | بررسی و تأیید درخواست | داده پرسنلی تأییدشده |
| ۳ | PayrollRun | اجرای `calculateSalary()` | `PayrollRun` و `PayrollLine` |
| ۴ | Finance Manager | اجرای `checkBudget()` و تأیید پرداخت | `Payment` |
| ۵ | Bank/Payment Gateway | اجرای پرداخت | تأییدیه تراکنش |
| ۶ | Procurement Officer | ایجاد PR و صدور PO | `PurchaseOrder` |
| ۷ | Supplier / Warehouse Officer | ارسال کالا و ثبت رسید | `GoodsReceipt` و `StockLot` |
| ۸ | Executive/Analyst | اجرای `generateReport()` | `Report` |

### جدول Exception Flow سطح ۱

| کد | Actor / Lane | رویداد استثنا | پاسخ فرایند |
|---|---|---|---|
| EX-L1-01 | Employee | داده ناقص یا نامعتبر | بازگشت برای اصلاح و ثبت `AuditLog` |
| EX-L1-02 | HR Manager | عدم تأیید درخواست | رد درخواست و اعلان به Employee |
| EX-L1-03 | PayrollRun | خطای `calculateSalary()` | توقف اجرا، ثبت خطا و اعلان به HR |
| EX-L1-04 | Finance Manager | ناکافی بودن `BudgetAllocation` | defer/reject و درخواست تخصیص مجدد |
| EX-L1-05 | Bank/Payment Gateway | خطای تراکنش | Intermediate Error و retry محدود |
| EX-L1-06 | Warehouse Officer | مغایرت کالا با PO | ایجاد `DiscrepancyReport` و توقف تخصیص |
| EX-L1-07 | Executive/Analyst | داده گزارش ناقص | درخواست تکمیل داده و ثبت رویداد کیفیت |

---

## ۳. سطح ۲ — فرایندهای حوزه‌ای

### ۳.۱ HR — Recruitment، Transfer و Leave

```plantuml
@startuml BPMN-L2-HR
left to right direction
skinparam backgroundColor #FEFEFE

title BPMN Level 2 — HR Process

|Employee|
start
:Submit request;
if (Request type?) then (Recruitment/Transfer)
  :Submit profile and documents;
else (Leave)
  :Submit leave form;
endif
:Send request to HR Manager;
stop

|HR Manager|
:Receive request;
if (Recruitment/Transfer?) then (Yes)
  :Review documents;
  if (Complete?) then (Yes)
    :Schedule interview or transfer review;
  else (No)
    :Return for correction;
    stop
  endif
else (Leave)
  :Check leave balance;
endif
if (Approved?) then (Yes)
  :Approve request;
  :Update Employee record;
  :Write AuditLog;
  :Notify Employee;
else (No)
  :Reject request;
  :Write AuditLog;
  :Notify Employee;
  stop
endif
stop

@enduml
```

**Happy Path:** Employee درخواست را ثبت می‌کند → HR Manager مدارک یا مانده مرخصی را بررسی می‌کند → درخواست تأیید، رکورد `Employee` به‌روز و `AuditLog` ثبت می‌شود.  
**Exception Flow:** مدارک ناقص است، مانده مرخصی کافی نیست یا مدیر درخواست را رد می‌کند؛ سیستم درخواست را برای اصلاح برمی‌گرداند یا رد نهایی ثبت می‌کند.

### ۳.۲ Payroll — محاسبه، تأیید و پرداخت

```plantuml
@startuml BPMN-L2-Payroll
left to right direction
skinparam backgroundColor #FEFEFE

title BPMN Level 2 — Payroll Process

|HR Manager|
start
:Approve employee and attendance list;
:Send approved data to PayrollRun;
stop

|PayrollRun|
:Receive approved data;
:Invoke calculateSalary();
loop for each Employee
  :Calculate allowances and deductions;
  :Create PayrollLine;
end
if (Calculation valid?) then (Yes)
  :Generate Salary Slip;
  :Send summary to Finance Manager;
else (No)
  :Raise calculation error;
  :Write AuditLog;
  stop
endif
stop

|Finance Manager|
:Receive payroll summary;
:Invoke checkBudget();
if (Budget available?) then (Yes)
  :Approve payroll payment;
  :Create Payment;
  :Send payment instruction to Bank Gateway;
else (No)
  :Request budget extension;
  :Write AuditLog;
  stop
endif
stop

|Bank/Payment Gateway|
:Receive payment instruction;
if (Transaction success?) then (Yes)
  :Return confirmation;
  :Update Payment status;
else (No)
  :Return failure;
  :Schedule retry;
endif
stop

@enduml
```

**Happy Path:** لیست تأیید می‌شود → `calculateSalary()` خطوط حقوق را می‌سازد → Finance Manager بودجه را تأیید می‌کند → بانک پرداخت را ثبت می‌کند.  
**Exception Flow:** خطای محاسبه، بودجه ناکافی یا failure درگاه باعث توقف، ثبت `AuditLog` و retry محدود می‌شود.

### ۳.۳ Budget — تدوین، تخصیص و اعتبارسنجی

```plantuml
@startuml BPMN-L2-Budget
left to right direction
skinparam backgroundColor #FEFEFE

title BPMN Level 2 — Budget Process

|Executive/Analyst|
start
:Define annual budget plan;
:Submit budget targets;
stop

|Finance Manager|
:Receive budget plan;
:Create Budget;
fork
  :Allocate credit to organization units;
fork again
  :Publish BudgetAllocation;
end fork
:Receive expense or payroll request;
:Invoke checkBudget();
if (Credit sufficient?) then (Yes)
  :Reserve BudgetAllocation;
  :Approve request;
else (No)
  :Request reallocation;
  stop
endif
:Write AuditLog;
stop

@enduml
```

**Happy Path:** بودجه سالانه تعریف می‌شود → اعتبار به واحدها تخصیص می‌یابد → `checkBudget()` مقدار درخواست را بررسی و رزرو می‌کند.  
**Exception Flow:** مانده اعتبار کمتر از درخواست است؛ Finance Manager درخواست reallocates را به Executive/Analyst می‌فرستد و تا تصمیم جدید، عملیات متوقف می‌ماند.

### ۳.۴ Procurement — درخواست خرید تا سفارش

```plantuml
@startuml BPMN-L2-Procurement
left to right direction
skinparam backgroundColor #FEFEFE

title BPMN Level 2 — Procurement Process

|Procurement Officer|
start
:Create PurchaseRequest;
:Attach Product and supplier data;
:Submit to Finance Manager;
stop

|Finance Manager|
:Receive PurchaseRequest;
:Invoke checkBudget();
if (Budget available?) then (Yes)
  :Reserve BudgetAllocation;
  :Approve PurchaseRequest;
  :Issue PurchaseOrder;
  :Send PO to Supplier;
else (No)
  :Reject or request reallocation;
  :Notify Procurement Officer;
  stop
endif
stop

|Supplier|
:Receive PurchaseOrder;
:Acknowledge order;
:Ship goods;
:Send shipment notice;
stop

|Warehouse Officer|
:Receive goods and shipment notice;
:Create GoodsReceipt;
:Send receipt result;
stop

@enduml
```

**Happy Path:** PR ایجاد و اعتبارسنجی می‌شود → بودجه رزرو و PR تأیید می‌شود → PO صادر و به Supplier ارسال می‌شود → کالا دریافت و `GoodsReceipt` ثبت می‌گردد.  
**Exception Flow:** سطر نامعتبر، بودجه ناکافی، رد تامین‌کننده یا مغایرت حمل باعث اصلاح، رد یا ایجاد `DiscrepancyReport` می‌شود.

### ۳.۵ Inventory/Warehouse — رسید، موجودی و تخصیص

```plantuml
@startuml BPMN-L2-Inventory
left to right direction
skinparam backgroundColor #FEFEFE

title BPMN Level 2 — Inventory Process

|Warehouse Officer|
start
:Receive GoodsReceipt;
:Inspect physical goods;
if (Matches PurchaseOrder?) then (Yes)
  :Create or update StockLot;
  :Invoke allocateStock();
  :Update available and reserved quantity;
  :Check reorder level;
  if (Reorder needed?) then (Yes)
    :Create automatic PurchaseRequest;
  else (No)
    :Notify Procurement Officer;
  endif
else (No)
  :Create DiscrepancyReport;
  :Notify Procurement Officer;
  stop
endif
:Write AuditLog;
stop

|Executive/Analyst|
:Receive inventory dashboard;
:Review stock turnover and capacity;
stop

@enduml
```

**Happy Path:** کالا با PO تطبیق دارد → `StockLot` ساخته یا به‌روز می‌شود → `allocateStock()` مقدار رزرو را ثبت می‌کند → گزارش موجودی منتشر می‌شود.  
**Exception Flow:** مغایرت تعداد یا کیفیت، موجودی ناکافی یا ظرفیت انبار باعث گزارش تفاوت، توقف تخصیص یا درخواست توسعه انبار می‌شود.

### ۳.۶ Reporting & Analytics — گزارش مدیریتی

```plantuml
@startuml BPMN-L2-Reporting
left to right direction
skinparam backgroundColor #FEFEFE

title BPMN Level 2 — Reporting Process

|Executive/Analyst|
start
:Define report criteria and period;
:Request integrated report;
stop

|System / Report Engine|
:Extract Employee, Payroll, Budget, Procurement and Inventory data;
fork
  :Validate and transform data;
fork again
  :Calculate metrics;
end fork
:Invoke generateReport();
if (Data quality valid?) then (Yes)
  :Publish Report;
  :Write AuditLog;
else (No)
  :Raise DataQualityException;
  :Request data correction;
  stop
endif
stop

|Executive/Analyst|
:Receive Report;
if (Revision needed?) then (Yes)
  :Request revision;
else (No)
  :Approve and publish dashboard;
endif
stop

@enduml
```

**Happy Path:** معیارها تعریف می‌شوند → داده‌های حوزه‌ای استخراج و اعتبارسنجی می‌شوند → `generateReport()` گزارش را منتشر می‌کند.  
**Exception Flow:** داده ناقص یا ناسازگار است؛ Report Engine خطای کیفیت داده ثبت می‌کند و درخواست تکمیل داده ارسال می‌شود.

### جدول Happy Path سطح ۲

| حوزه | مسیر خوشحال | موجودیت/متد |
|---|---|---|
| HR | تأیید درخواست و به‌روزرسانی Employee | `Employee`، `approveRequest()` |
| Payroll | محاسبه، تأیید بودجه و پرداخت | `PayrollRun`، `calculateSalary()`، `checkBudget()` |
| Budget | تخصیص و رزرو اعتبار | `BudgetAllocation`، `reserve()` |
| Procurement | PR → PO → ارسال به Supplier | `PurchaseRequest`، `PurchaseOrder` |
| Inventory | رسید → StockLot → تخصیص | `GoodsReceipt`، `StockLot`، `allocateStock()` |
| Reporting | استخراج → اعتبارسنجی → Report | `Report`، `generateReport()` |

### جدول Exception Flow سطح ۲

| حوزه | استثنا | واکنش |
|---|---|---|
| HR | مدارک ناقص یا مانده مرخصی ناکافی | اصلاح یا رد و اعلان |
| Payroll | خطای محاسبه یا پرداخت | `AuditLog`، توقف و retry محدود |
| Budget | مانده اعتبار ناکافی | درخواست تخصیص مجدد |
| Procurement | PR نامعتبر یا PO ردشده | بازگشت برای اصلاح یا لغو |
| Inventory | مغایرت رسید یا کسری موجودی | `DiscrepancyReport` و توقف تخصیص |
| Reporting | داده کیفیت‌پایین | `DataQualityException` و درخواست تکمیل |

---

## ۴. سطح ۳ — زیرفرایندهای حیاتی

### ۴.۱ تایید پرداخت حقوق

```plantuml
@startuml BPMN-L3-PayrollApproval
left to right direction
skinparam backgroundColor #FEFEFE

title BPMN Level 3 — Payroll Approval

|HR Manager|
start
:Review payroll list;
:Digitally sign approval;
:Send approved list to PayrollRun;
stop

|PayrollRun|
:Receive approved list;
:Invoke calculateSalary();
if (Calculation valid?) then (Yes)
  :Create PayrollLine;
  :Generate Salary Slip;
  :Send summary to Finance Manager;
else (No)
  :Raise CalculationException;
  :Write AuditLog;
  :Notify HR Manager;
  stop
endif
stop

|Finance Manager|
:Receive payroll summary;
:Invoke checkBudget();
if (Budget available?) then (Yes)
  :Approve payment;
  :Create Payment;
  :Send payment instruction;
else (No)
  :Reject or defer payment;
  :Write AuditLog;
  :Notify HR Manager;
  stop
endif
stop

|Bank/Payment Gateway|
:Receive payment instruction;
if (Transaction success?) then (Yes)
  :Return confirmation;
  :Mark Payment as Paid;
else (No)
  :Return failure;
  :Schedule retry after 5 minutes;
  :Write AuditLog;
  stop
endif
stop

@enduml
```

#### جدول Happy Path — L3 Payroll

| مرحله | نقش | فعالیت | Entity / Method |
|---|---|---|---|
| ۱ | HR Manager | تأیید و امضای لیست | `Employee` |
| ۲ | PayrollRun | محاسبه حقوق | `calculateSalary()` |
| ۳ | PayrollRun | تولید Salary Slip | `PayrollLine` |
| ۴ | Finance Manager | بررسی بودجه | `checkBudget()` |
| ۵ | Finance Manager | ایجاد پرداخت | `Payment` |
| ۶ | Bank Gateway | تأیید تراکنش | `Payment.status = Paid` |

#### جدول Exception Flow — L3 Payroll

| کد | موقعیت | خطا | پاسخ |
|---|---|---|---|
| EX-P01 | PayrollRun | `CalculationException` | توقف، `AuditLog` و اعلان به HR |
| EX-P02 | Finance Manager | بودجه ناکافی | رد/تعویق و درخواست reallocates |
| EX-P03 | Bank Gateway | `PaymentFailedException` | retry پس از ۵ دقیقه، حداکثر ۳ بار |

### ۴.۲ بررسی بودجه درخواست خرید

```plantuml
@startuml BPMN-L3-BudgetCheckPR
left to right direction
skinparam backgroundColor #FEFEFE

title BPMN Level 3 — Budget Check for Purchase Request

|Procurement Officer|
start
:Create PurchaseRequest;
:Submit request and amount;
stop

|Finance Manager|
:Receive PurchaseRequest;
:Invoke checkBudget();
:Read BudgetAllocation;
if (Budget available?) then (Yes)
  :Reserve BudgetAllocation;
  :Approve PurchaseRequest;
  :Issue PurchaseOrder;
  :Send PO to Supplier;
else (No)
  if (Reallocation requested?) then (Yes)
    :Send reallocation request to Executive/Analyst;
  else (No)
    :Reject PurchaseRequest;
    :Notify Procurement Officer;
    stop
  endif
endif
stop

|Executive/Analyst|
:Receive reallocation request;
if (Approved?) then (Yes)
  :Update BudgetAllocation;
  :Notify Finance Manager;
else (No)
  :Reject reallocation;
  :Write AuditLog;
  stop
endif
stop

|Finance Manager|
:Receive reallocation response;
if (Budget now available?) then (Yes)
  :Approve PurchaseRequest;
  :Issue PurchaseOrder;
else (No)
  :Reject PurchaseRequest finally;
  :Write AuditLog;
endif
stop

@enduml
```

#### جدول Happy Path — L3 Budget Check

| مرحله | نقش | فعالیت | Entity / Method |
|---|---|---|---|
| ۱ | Procurement Officer | ایجاد PR | `PurchaseRequest` |
| ۲ | Finance Manager | بررسی بودجه | `checkBudget()` |
| ۳ | Finance Manager | رزرو اعتبار | `BudgetAllocation.reserve()` |
| ۴ | Finance Manager | تأیید و صدور PO | `PurchaseOrder` |
| ۵ | Supplier | تأیید سفارش | `PurchaseOrder.acknowledge()` |

#### جدول Exception Flow — L3 Budget Check

| کد | موقعیت | خطا | پاسخ |
|---|---|---|---|
| EX-B01 | Finance Manager | بودجه ناکافی بدون reallocation | رد PR و اعلان |
| EX-B02 | Executive/Analyst | رد reallocation | توقف و `AuditLog` |
| EX-B03 | Finance Manager | پس از reallocation هنوز بودجه ناکافی | رد نهایی PR |

### ۴.۳ تخصیص موجودی به درخواست‌کننده

```plantuml
@startuml BPMN-L3-StockAllocation
left to right direction
skinparam backgroundColor #FEFEFE

title BPMN Level 3 — Stock Allocation

|Warehouse Officer|
start
:Receive GoodsReceipt;
:Inspect physical goods;
:Scan barcode or serial;
:Record GoodsReceipt;
:Invoke allocateStock();
if (Eligible lot and quantity available?) then (Yes)
  :Select FEFO lot;
  :Reserve quantity;
  :Update StockLot;
  :Confirm issue;
  :Notify Procurement Officer;
else (No)
  if (Warehouse overflow?) then (Yes)
    :Raise OverflowAlert;
    :Notify Executive/Analyst;
  else (No)
    :Raise StockShortageException;
    :Notify Procurement Officer;
  endif
  stop
endif
:Write AuditLog;
stop

|Executive/Analyst|
:Receive OverflowAlert;
if (Expansion approved?) then (Yes)
  :Approve warehouse expansion;
else (No)
  :Approve overflow management or reject;
endif
:Notify Warehouse Officer;
stop

|Procurement Officer|
:Receive allocation notice;
if (Reorder needed?) then (Yes)
  :Create automatic PurchaseRequest;
else (No)
  :Close allocation task;
endif
stop

@enduml
```

#### جدول Happy Path — L3 Stock Allocation

| مرحله | نقش | فعالیت | Entity / Method |
|---|---|---|---|
| ۱ | Warehouse Officer | دریافت و بازرسی کالا | `GoodsReceipt` |
| ۲ | Warehouse Officer | انتخاب لات واجد شرایط | `StockLot` |
| ۳ | Warehouse Officer | رزرو مقدار | `allocateStock()` |
| ۴ | Warehouse Officer | به‌روزرسانی موجودی | `StockLot.availableQuantity` |
| ۵ | Procurement Officer | دریافت اعلان | `PurchaseRequest` در صورت نیاز |

#### جدول Exception Flow — L3 Stock Allocation

| کد | موقعیت | خطا | پاسخ |
|---|---|---|---|
| EX-S01 | Warehouse Officer | مقدار ناکافی | `StockShortageException` و اعلان خرید |
| EX-S02 | Warehouse Officer | ظرفیت انبار تکمیل است | `OverflowAlert` به Executive/Analyst |
| EX-S03 | Warehouse Officer | مغایرت فیزیکی با رسید | `DiscrepancyReport` و توقف تخصیص |

---

## ۵. ردپا به DFD و UML

| شناسه BPMN | فعالیت | DFD | UML |
|---|---|---|---|
| BPMN-HR-01 | Approve HR request | DFD-L2.1 | `Employee`، `approveRequest()` |
| BPMN-PAY-01 | Calculate Salary | DFD-L2.2 / DFD-L3.1 | `PayrollRun.calculateSalary()` |
| BPMN-PAY-02 | Post Payment | DFD-L2.2 | `Payment.postPayment()` |
| BPMN-BUD-01 | Check Budget | DFD-L2.3 / DFD-L3.2 | `BudgetAllocation.checkBudget()` |
| BPMN-PROC-01 | Create and approve PR | DFD-L2.4 / DFD-L3.2 | `PurchaseRequest.submit()` / `approve()` |
| BPMN-PROC-02 | Issue PurchaseOrder | DFD-L2.4 | `PurchaseOrder.issue()` |
| BPMN-INV-01 | Allocate Stock | DFD-L2.5 / DFD-L3.3 | `StockLot.allocate()` / `allocateStock()` |
| BPMN-INV-02 | Record GoodsReceipt | DFD-L2.5 | `GoodsReceipt` |
| BPMN-REP-01 | Generate Report | DFD-L2.6 | `ReportEngine.generateReport()` |

## ۶. قوانین فرایندی

1. هیچ `Payment` بدون `PayrollRun` تأییدشده و نتیجه موفق `checkBudget()` ایجاد نمی‌شود.
2. هیچ `PurchaseOrder` بدون `PurchaseRequest` تأییدشده و رزرو بودجه صادر نمی‌شود.
3. هیچ `StockLot` بدون `GoodsReceipt` معتبر و تطبیق با `PurchaseOrder` ایجاد نمی‌شود.
4. تمام تصمیم‌های تأیید، رد، رزرو، پرداخت و تخصیص باید `AuditLog` ایجاد کنند.
5. خطاهای قابل تکرار فقط با سقف مشخص و ثبت رویداد خطا اجرا می‌شوند.

*پایان سند BPMN*
