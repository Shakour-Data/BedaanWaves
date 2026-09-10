# مستند جامع مدل‌سازی DFD، BPMN و UML 2.5

**سامانه:** Integrated HR, Finance & Procurement Management System  
**نسخه:** v1.0  
**تاریخ:** 2026-09-10  
**وضعیت:** مستند معماری و تحلیل فرایند

## هدف و دامنه

این سند، مدل یکپارچهٔ سامانهٔ مدیریت منابع انسانی، حقوق و دستمزد، بودجه و اعتبارات، تدارکات و انبار، و گزارش‌گیری تحلیلی را در سه لایهٔ انتزاع ارائه می‌کند. DFD مرز سامانه و جریان داده‌ها را نشان می‌دهد، BPMN رفتار کسب‌وکار و همکاری نقش‌ها را مدل می‌کند، و UML 2.5 ساختار، رفتار و تعاملات طراحی را تا سطح پیاده‌سازی پوشش می‌دهد.

### قرارداد نام‌گذاری

- شناسه‌های DFD با `DFD-Lx.y` و مخازن با `D1` تا `D14` نمایش داده می‌شوند.
- شناسه‌های BPMN با `BPMN-Lx-<Domain>` و استثناها با `EX-<Domain><Seq>` نام‌گذاری می‌شوند.
- نام موجودیت‌ها و عملیات‌ها در همهٔ нотاسیون‌ها یکسان است: `Employee`, `PayrollRun`, `PayrollLine`, `Budget`, `BudgetAllocation`, `PurchaseRequest`, `PurchaseOrder`, `Product`, `StockLot`, `GoodsReceipt`, `Payment`, `Report`, `AuditLog`.
- عملیات‌های کلیدی: `calculateSalary()`, `BudgetAllocation.checkBudget()`, `BudgetAllocation.reserve()`, `StockLot.allocate()` / `allocateStock()`, `generateReport()`, `executePayment()`.
- هر تغییر مهم، تأیید، رد، رزرو، پرداخت، تخصیص و انتشار گزارش باید یک رویداد `AuditLog` ایجاد کند.

## فهرست مطالب

1. [DFD](#1-dfd)
2. [BPMN](#2-bpmn)
3. [UML 2.5](#3-uml-25)
4. [ردیابی و قوانین انسجام](#4-ردیابی-و-قوانین-انسجام)

## پوشش مدل‌ها

| خانواده | سطح ۰ / زمینه | سطح ۱ | سطح ۲ | سطح ۳ |
|---|---:|---:|---:|---:|
| DFD | نمودار زمینه | ۶ فرایند اصلی | ۶ تجزیهٔ دامنه‌ای | ۳ فرایند اتمی حیاتی |
| BPMN | — | نمای کلان استخرها و لین‌ها | ۶ فرایند دامنه‌ای | ۳ زیرفرایند اجرایی حیاتی |
| UML 2.5 | — | دامنه و چشم‌انداز | طراحی و زیرسیستم | پیاده‌سازی، امضاها و قیود |

# ۱. DFD

DFD با حفظ اصل balance طراحی شده است: خروجی‌ها و ورودی‌های هر فرایند در سطح تجزیه‌شده باید با فرایند والد همخوانی داشته باشند. موجودیت‌های بیرونی با رنگ آبی، فرایندها با رنگ نارنجی و مخازن داده با رنگ سبز متمایز شده‌اند.

## سطح ۰ — نمودار زمینه

```mermaid
flowchart LR
classDef entity fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#000;
classDef process fill:#FFF3E0,stroke:#EF6C00,stroke-width:3px,color:#000;
classDef store fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,color:#000;

subgraph External [External Entities]
EMP[Employee]:::entity
HRM[HRManager]:::entity
FIN[FinanceManager]:::entity
PROC[ProcurementOfficer]:::entity
WH[WarehouseOfficer]:::entity
SUP[Supplier]:::entity
BANK[BankGateway]:::entity
EXEC[ExecutiveAnalyst]:::entity
AUD[Auditor]:::entity
end

SYS([0. Integrated HR, Finance & Procurement]):::process

EMP <-->|profile, leave, attendance| SYS
HRM <-->|hire, transfer, termination approval| SYS
FIN <-->|budget decision, payment approval| SYS
PROC <-->|purchase request, order status| SYS
WH <-->|goods receipt, stock allocation| SYS
SUP <-->|quotation, PO acknowledgement, shipment| SYS
BANK <-->|payment instruction, transaction result| SYS
EXEC <-->|report criteria, dashboards| SYS
AUD <-->|audit query, audit evidence| SYS
```

- `Employee` داده‌های هویتی، مرخصی و حضور را وارد می‌کند و فیش حقوقی و اعلان دریافت می‌کند.
- `HRManager` تصمیم‌های استخدام، انتقال و خاتمهٔ همکاری را ثبت و تأیید می‌کند.
- `FinanceManager` تصمیم بودجه و پرداخت را صادر می‌کند؛ `BankGateway` نتیجهٔ تراکنش را برمی‌گرداند.
- `ProcurementOfficer` درخواست خرید را ثبت می‌کند و `Supplier` وضعیت سفارش و محموله را اعلام می‌کند.
- `WarehouseOfficer` رسید کالا و تخصیص موجودی را ثبت می‌کند؛ `ExecutiveAnalyst` و `Auditor` خروجی‌های مدیریتی و حسابرسی می‌گیرند.
- در این سطح هیچ مخزن داخلی نمایش داده نمی‌شود و همهٔ جریان‌ها از مرز سامانه عبور می‌کنند.

## سطح ۱ — فرایندهای اصلی

```mermaid
flowchart LR
classDef entity fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#000;
classDef process fill:#FFF3E0,stroke:#EF6C00,stroke-width:3px,color:#000;
classDef store fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,color:#000;

subgraph External [External Entities]
EMP[Employee]:::entity
HRM[HRManager]:::entity
FIN[FinanceManager]:::entity
PROC[ProcurementOfficer]:::entity
WH[WarehouseOfficer]:::entity
SUP[Supplier]:::entity
BANK[BankGateway]:::entity
EXEC[ExecutiveAnalyst]:::entity
AUD[Auditor]:::entity
end

subgraph Processes [Level-1 Processes]
P1([1. HR Management]):::process
P2([2. Payroll]):::process
P3([3. Budget & Credits]):::process
P4([4. Procurement]):::process
P5([5. Inventory/Warehouse]):::process
P6([6. Reporting & Analytics]):::process
end

subgraph Stores [Data Stores]
D1[(D1 Employee)]:::store
D2[(D2 OrganizationUnit)]:::store
D3[(D3 PayrollRun)]:::store
D4[(D4 PayrollLine)]:::store
D5[(D5 Budget)]:::store
D6[(D6 BudgetAllocation)]:::store
D7[(D7 PurchaseRequest)]:::store
D8[(D8 PurchaseOrder)]:::store
D9[(D9 Product)]:::store
D10[(D10 StockLot)]:::store
D11[(D11 GoodsReceipt)]:::store
D12[(D12 Payment)]:::store
D13[(D13 Report)]:::store
D14[(D14 AuditLog)]:::store
end

EMP -->|personal data, leave, attendance| P1
HRM -->|employment decisions| P1
P1 -->|approved employee and org data| D1
P1 -->|unit hierarchy| D2
P1 -->|attendance and eligibility| P2
P1 -->|audit event| D14
P2 -->|payroll run and lines| D3
P2 -->|earnings and deductions| D4
P2 -->|payment instruction| D12
P2 -->|payment instruction| BANK
BANK -->|transaction result| P2
P2 -->|payroll liability| P3
P2 -->|audit event| D14
FIN -->|budget plan and allocation decision| P3
P3 -->|budget header| D5
P3 -->|allocation and remaining credit| D6
P3 -->|funding decision| BANK
P3 -->|approved credit| P4
P3 -->|audit event| D14
PROC -->|purchase request| P4
P4 -->|validated request| D7
P4 -->|approved purchase order| D8
P4 -->|PO and quotation data| SUP
SUP -->|acknowledgement and shipment notice| P4
P4 -->|expected goods| P5
P4 -->|audit event| D14
WH -->|receipt and allocation command| P5
P5 -->|product master update| D9
P5 -->|stock lot and location| D10
P5 -->|goods receipt| D11
P5 -->|consumption and stock status| P3
P5 -->|audit event| D14
EXEC -->|report criteria| P6
D1 -->|employee facts| P6
D5 -->|budget facts| P6
D6 -->|allocation facts| P6
D8 -->|purchase and stock facts| P6
D10 -->|stock facts| P6
D14 -->|audit facts| P6
P6 -->|published report| D13
D13 -->|dashboard and analytical report| EXEC
D13 -->|audit report| AUD
```

- شش فرایند اصلی، پنج دامنهٔ درخواستی را به‌همراه گزارش‌گیری پوشش می‌دهند.
- `HR Management` منبع دادهٔ `Employee` و `OrganizationUnit` برای حقوق و گزارش‌هاست.
- `Payroll` از دادهٔ پرسنلی و اعتبار باقی‌مانده استفاده کرده و `PayrollRun`، `PayrollLine` و `Payment` را تولید می‌کند.
- `Budget & Credits` اعتبار را تخصیص و رزرو می‌کند و هیچ پرداخت یا سفارش خریدی بدون بررسی اعتبار صادر نمی‌شود.
- `Procurement` و `Inventory/Warehouse` چرخهٔ درخواست، سفارش، رسید انبار و `StockLot` را به هم متصل می‌کنند.
- `Reporting & Analytics` فقط از مخازن عملیاتی می‌خواند، `Report` را می‌سازد و خروجی را به `ExecutiveAnalyst` و `Auditor` می‌دهد.

## سطح ۲ — تجزیه فرایندها

### DFD-L2.1 — مدیریت منابع انسانی

```mermaid
flowchart LR
classDef entity fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#000;
classDef process fill:#FFF3E0,stroke:#EF6C00,stroke-width:2px,color:#000;
classDef store fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,color:#000;
EMP[Employee]:::entity
HRM[HRManager]:::entity
P11([1.1 Recruitment]):::process
P12([1.2 Maintain Personnel File]):::process
P13([1.3 Manage Organization Unit]):::process
P14([1.4 Approve Employment Change]):::process
P2([2. Payroll]):::process
D1[(D1 Employee)]:::store
D2[(D2 OrganizationUnit)]:::store
D14[(D14 AuditLog)]:::store
EMP -->|application and profile| P11
HRM -->|review and decision| P13
HRM -->|review and decision| P14
P11 -->|candidate and hire data| P12
P11 -->|employment change data| P14
P12 -->|employee record| D1
P12 -->|employment change data| P14
P13 -->|unit hierarchy| D2
P13 -->|organization change data| P14
P14 -->|approved status| D1
P14 -->|org assignment| D2
P14 -->|approved employee and org data| P2
P11 -->|audit event| D14
P12 -->|audit event| D14
P13 -->|audit event| D14
P14 -->|audit event| D14
```

- استخدام، نگهداری پرونده، مدیریت واحد سازمانی و تأیید تغییرات استخدامی از یکدیگر جدا شده‌اند.
- `Employee` دادهٔ متقاضی و پروفایل را وارد می‌کند و `HRManager` تصمیم استخدام، انتقال یا خاتمه را ثبت می‌کند.
- `D1 Employee` رکورد پایدار پرسنلی و `D2 OrganizationUnit` سلسله‌مراتب سازمانی است.
- هر تغییر وضعیت یا ساختار، رویدادی در `D14 AuditLog` ایجاد می‌کند.
- خروجی تأییدشده به `Payroll` می‌رود تا واجد شرایط بودن و دادهٔ محاسبه حقوق به‌روز بماند.

### DFD-L2.2 — حقوق و دستمزد

```mermaid
flowchart LR
classDef entity fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#000;
classDef process fill:#FFF3E0,stroke:#EF6C00,stroke-width:2px,color:#000;
classDef store fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,color:#000;
EMP[Employee]:::entity
FIN[FinanceManager]:::entity
BANK[BankGateway]:::entity
P21([2.1 Load Attendance]):::process
P22([2.2 Calculate Salary]):::process
P23([2.3 Review Payroll]):::process
P24([2.4 Post Payment]):::process
D1[(D1 Employee)]:::store
D3[(D3 PayrollRun)]:::store
D4[(D4 PayrollLine)]:::store
D6[(D6 BudgetAllocation)]:::store
D12[(D12 Payment)]:::store
D14[(D14 AuditLog)]:::store
EMP -->|attendance and profile| P21
P21 -->|attendance facts| P22
D1 -->|base salary and allowances| P22
D6 -->|remaining credit| P22
P22 -->|calculated payroll| P23
P22 -->|calculated run| D3
P22 -->|earnings, deductions, net| D4
FIN -->|approve or reject| P23
P23 -->|approved run| P24
P24 -->|payment instruction| D12
P24 -->|payment request| BANK
BANK -->|transaction result| P24
P22 -->|calculation audit| D14
P23 -->|approval audit| D14
P24 -->|payment audit| D14
```

- `PayrollRun` شناسهٔ اجرای حقوق و `PayrollLine` جزییات محاسبه هر کارمند را نگهداری می‌کند.
- فرایند محاسبه، حقوق پایه، مزایا، کسورات، حضور و اعتبار باقی‌ماندهٔ `BudgetAllocation` را ترکیب می‌کند.
- `FinanceManager` پس از بررسی مجموع خالص و اعتبار، اجرا را تأیید یا رد می‌کند.
- نتیجهٔ بانک در `Payment` و `AuditLog` ثبت می‌شود و خطای درگاه مسیر Retry محدود را فعال می‌کند.
- این تجزیه مستقیماً با `calculateSalary()` و `postPayment()` در مدل‌های UML و BPMN تناظر دارد.

### DFD-L2.3 — بودجه و اعتبارات

```mermaid
flowchart LR
classDef entity fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#000;
classDef process fill:#FFF3E0,stroke:#EF6C00,stroke-width:2px,color:#000;
classDef store fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,color:#000;
EXEC[ExecutiveAnalyst]:::entity
FIN[FinanceManager]:::entity
BANK[BankGateway]:::entity
P31([3.1 Define Budget Plan]):::process
P32([3.2 Allocate Credit]):::process
P33([3.3 Check and Reserve]):::process
P34([3.4 Release and Reconcile]):::process
D5[(D5 Budget)]:::store
D6[(D6 BudgetAllocation)]:::store
D12[(D12 Payment)]:::store
D14[(D14 AuditLog)]:::store
EXEC -->|annual plan and targets| P31
P31 -->|budget header| D5
D5 -->|budget plan| P32
FIN -->|allocation decision| P32
P32 -->|allocation and remaining| D6
FIN -->|expense or payroll request| P33
D6 -->|available credit| P33
P33 -->|reservation| D6
P33 -->|approved funding| P34
P34 -->|funding instruction| BANK
P34 -->|payment reference| D12
P34 -->|release or reconciliation| D6
P31 -->|audit event| D14
P32 -->|audit event| D14
P33 -->|audit event| D14
P34 -->|audit event| D14
```

- بودجهٔ سالانه در `D5 Budget` و سهم هر واحد یا پروژه در `D6 BudgetAllocation` نگهداری می‌شود.
- `BudgetAllocation.checkBudget()` مقدار درخواستی را با `remaining` مقایسه می‌کند.
- رزرو موقت، مصرف همزمان یک اعتبار توسط درخواست‌های موازی را جلوگیری می‌کند.
- پرداخت موفق، رزرو را آزاد یا تسویه می‌کند و `Payment`D14`D14` را ثبت و تسویه می‌کند.
- کمبود اعتبار، درخواست تخصیص مجدد یا رد عملیات را از طریق زیرفرایند سطح ۳ فعال می‌کند.

### DFD-L2.4 — تدارکات

```mermaid
flowchart LR
classDef entity fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#000;
classDef process fill:#FFF3E0,stroke:#EF6C00,stroke-width:2px,color:#000;
classDef store fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,color:#000;
PROC[ProcurementOfficer]:::entity
FIN[FinanceManager]:::entity
SUP[Supplier]:::entity
P41([4.1 Create PurchaseRequest]):::process
P42([4.2 Validate Request]):::process
P43([4.3 Check Budget]):::process
P44([4.4 Approve and Issue PO]):::process
D6[(D6 BudgetAllocation)]:::store
D7[(D7 PurchaseRequest)]:::store
D8[(D8 PurchaseOrder)]:::store
D9[(D9 Product)]:::store
D14[(D14 AuditLog)]:::store
PROC -->|request lines and amount| P41
P41 -->|draft request| P42
P41 -->|draft request| D7
D7 -->|draft request| P42
P42 -->|validation result| D7
D9 -->|product and price| P42
D6 -->|available credit| P43
P42 -->|valid request| P43
P43 -->|reservation| D6
FIN -->|approval decision| P44
P43 -->|approved credit| P44
P44 -->|approved order| D8
P44 -->| D8
P44 -->|PO and delivery terms| SUP
SUP -->|acknowledgement| P44
P41 -->|audit event| D14
P42 -->|audit event| D14
P43 -->|audit event| D14
P44 -->|audit event| D14
```

- درخواست خرید از نظر کامل بودن سطرها، شناسه کالا و مبلغ مثبت اعتبارسنجی می‌شود.
- `D6 BudgetAllocation` در فرایند `4.3 Check Budget` خوانده و در صورت تأیید، مبلغ رزرو می‌شود.
- فقط درخواست تأیید می‌شود.
- `PurchaseRequest` تنها پس از اعتبارسنجی و رزرو بودجه به `PurchaseOrder` تبدیل می‌شود.
- پاسخ تامین‌کننده و شرایط تحویل به مخزن سفارش و رویدادهای حسابرسی متصل است.
- این مدل با DFD-L3.2 و BPMN-L3 بودجهٔ درخواست خرید هم‌نام و هم‌مسیر است.

### DFD-L2.5 — انبار و موجودی

```mermaid
flowchart LR
classDef entity fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#000;
classDef process fill:#FFF3E0,stroke:#EF6C00,stroke-width:2px,color:#000;
classDef store fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,color:#000;
WH[WarehouseOfficer]:::entity
SUP[Supplier]:::entity
P51([5.1 Receive Goods]):::process
P52([5.2 Inspect and Record]):::process
P53([5.3 Create StockLot]):::process
P54([5.4 Allocate and Issue]):::process
D8[(D8 PurchaseOrder)]:::store
D9[(D9 Product)]:::store
D10[(D10 StockLot)]:::store
D11[(D11 GoodsReceipt)]:::store
D14[(D14 AuditLog)]:::store
SUP -->|shipment and packing list| P51
D8 -->|ordered quantity| P51
P51 -->|physical receipt| P52
P52 -->|inspection result| D11
P52 -->|accepted quantity| P53
D9 -->|product rules and expiry| P53
P53 -->|lot and location| D10
D10 -->|available lots| P54
P53 -->|accepted quantity| P54
P54 -->|reserved quantity| D10
P54 -->|issue confirmation| D11
P54
P54
P51 -->|receipt audit| D14
P52 -->|inspection audit| D14
P53 -->|lot audit| D14
P54 -->|allocation audit| D14
```

- کالای فیزیکی با مقدار سفارش‌شده و بارنامهٔ تامین‌کننده تطبیق داده می‌شود.
- کالای پذیرفته‌شده ابتدا `GoodsReceipt` و سپس `StockLot` با مکان، تاریخ انقضا و مقدار می‌سازد.
- `StockLot.allocate()` / `allocateStock()` مقدار قابل تخصیص را کاهش و وضعیت لات را به‌روز می‌کند.
- مغایرت مقدار یا کیفیت، گزارش مغایرت ایجاد کرده و انتشار نهایی موجودی را متوقف می‌کند.
- دریافت، بررسی کیفیت و ثبت 14
- هر روید.
- `D14
- هیچ تخصی.
```

### D14 — گزارش‌4.3 — بودجه و اعتبارات

```mermaid
flowchart LR
classDef entity fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#000;
classDef process fill:#FFF3E0,stroke:#EF6C00,stroke-width:2px,color:#000;
classDef store fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,color:#000;
EXEC[ExecutiveAnalyst]:::entity
FIN[FinanceManager]:::entity
BANK[BankGateway]:::entity
P31([3.1 Define Budget Plan]):::process
P32([3.2 Allocate Credit]):::process
P33([3.3 Check and Reserve]):::process
P34([3.4 Release and Reconcile]):::process
D5[(D5 Budget)]:::store
D6[(D6 BudgetAllocation)]:::store
D12[(D12 Payment)]:::store
D14[(D14 AuditLog)]:::store
EXEC -->|annual plan and targets| P31
P31 -->|budget header| D5
D5 -->|budget plan| P32
FIN -->|allocation decision| P32
P32 -->|allocation and remaining| D6
FIN -->|expense or payroll request| P33
D6 -->|available credit| P33
P33 -->|reservation| D6
P33 -->|approved funding| P34
P34 -->|funding instruction| BANK
P34 -->|payment reference| D12
P34 -->|release or reconciliation| D6
P31 -->|audit event| D14
P32 -->|audit event| D14
P33 -->|audit event| D14
P34 -->|audit event| D14
```

- بودجهٔ سالانه در `D5 Budget` و سهم هر واحد یا پروژه در `D6 BudgetAllocation` نگهداری می‌شود.
- `BudgetAllocation.checkBudget()` مقدار درخواستی را با `remaining` مقایسه می‌کند.
- رزرو موقت، مصرف همزمان یک اعتبار توسط درخواست‌های موازی را جلوگیری می‌کند.
- پرداخت موفق، رزرو را آزاد یا تسویه می‌کند و `Payment` را ثبت می‌کند.
- کمبود اعتبار، درخواست تخصیص مجدد یا رد عملیات را از طریق زیرفرایند سطح ۳ فعال می‌کند.

### DFD-L2.4 — تدارکات

```mermaid
flowchart LR
classDef entity fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#000;
classDef process fill:#FFF3E0,stroke:#EF6C00,stroke-width:2px,color:#000;
classDef store fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,color:#000;
PROC[ProcurementOfficer]:::entity
FIN[FinanceManager]:::entity
SUP[Supplier]:::entity
P41([4.1 Create PurchaseRequest]):::process
P42([4.2 Validate Request]):::process
P43([4.3 Check Budget]):::process
P44([4.4 Approve and Issue PO]):::process
D6[(D6 BudgetAllocation)]:::store
D7[(D7 PurchaseRequest)]:::store
D8[(D8 PurchaseOrder)]:::store
D9[(D9 Product)]:::store
D14[(D14 AuditLog)]:::store
PROC -->|request lines and amount| P41
P41 -->|draft request| P42
P41 -->|draft request| D7
D7 -->|draft request| P42
P42 -->|validation result| D7
D9 -->|product and price| P42
D6 -->|available credit| P43
P42 -->|valid request| P43
P43 -->|reservation| D6
FIN -->|approval decision| P44
P43 -->|approved credit| P44
P44 -->|approved order| D8
P44 -->|PO and delivery terms| SUP
SUP -->|acknowledgement| P44
P41 -->|audit event| D14
P42 -->|audit event| D14
P43 -->|audit event| D14
P44 -->|audit event| D14
```

- درخواست خرید از نظر کامل بودن سطرها، شناسه کالا و مبلغ مثبت اعتبارسنجی می‌شود.
- `D6 BudgetAllocation` در فرایند `4.3 Check Budget` خوانده و در صورت تأیید، مبلغ رزرو می‌شود.
- `PurchaseRequest` تنها پس از اعتبارسنجی و رزرو بودجه به `PurchaseOrder` تبدیل می‌شود.
- پاسخ تامین‌کننده و شرایط تحویل به مخزن سفارش و رویدادهای حسابرسی متصل است.
- این مدل با DFD-L3.2 و BPMN-L3 بودجهٔ درخواست خرید هم‌نام و هم‌مسیر است.

### DFD-L2.5 — انبار و موجودی

```mermaid
flowchart LR
classDef entity fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#000;
classDef process fill:#FFF3E0,stroke:#EF6C00,stroke-width:2px,color:#000;
classDef store fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,color:#000;
WH[WarehouseOfficer]:::entity
SUP[Supplier]:::entity
P51([5.1 Receive Goods]):::process
P52([5.2 Inspect and Record]):::process
P53([5.3 Create StockLot]):::process
P54([5.4 Allocate and Issue]):::process
D8[(D8 PurchaseOrder)]:::store
D9[(D9 Product)]:::store
D10[(D10 StockLot)]:::store
D11[(D11 GoodsReceipt)]:::store
D14[(D14 AuditLog)]:::store
SUP -->|shipment and packing list| P51
D8 -->|shipment and packing list| P51
D8 -->|shipment and packing list| P51
P53
D14
P54
P54
P4
P54
```

<!-- APPEND -->|D14 AuditLog)]::store
P5
```

### DFD-L2.6 — گزارش‌گیری و تحلیل

```mermaid
flowchart LR
classDef entity fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#000;
classDef process fill:#FFF3E0,stroke:#EF6C00,stroke-width:2px,color:#000;
classDef store fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,color:#000;
EXEC[ExecutiveAnalyst]:::entity
AUD[Auditor]:::entity
P61([6.1 Extract Domain Data]):::process
P62([6.2 Validate and Transform]):::process
P63([6.3 Calculate Metrics]):::process
P64([6.4 Publish Report]):::process
D1[(D1 Employee)]:::store
D3[(D3 PayrollRun)]:::store
D5[(D5 Budget)]:::store
D6[(D6 BudgetAllocation)]:::store
D7[(D7 PurchaseRequest)]:::store
D8[(D8 PurchaseOrder)]:::store
D10[(D10 StockLot)]:::store
D14[(D14 AuditLog)]:::store
D13[(D13 Report)]:::store
EXEC -->|criteria and period| P61
D1 -->|employee facts| P61
D3 -->|payroll facts| P61
D5 -->|budget facts| P61
D6 -->|allocation facts| P61
D7 -->|purchase facts| P61
D8 -->|order facts| P61
D10 -->|stock facts| P61
D14 -->|audit facts| P61
P61 -->|extracted dataset| P62
P62 -->|validated dataset| P63
P63 -->|metrics and trends| P64
P64 -->|published report| D13
D13 -->|dashboard| EXEC
D13 -->|audit evidence| AUD
P62 -->|quality event| D14
P64 -->|publication event| D14
```

- گزارش‌گیری داده‌های دامنه را می‌خواند و رکوردهای عملیاتی را تغییر نمی‌دهد.
- استخراج، اعتبارسنجی، تبدیل و محاسبهٔ شاخص به ترتیب انجام می‌شوند تا گزارش ناسازگار منتشر نشود.
- `Report` دوره، فیلترها، معیارها، نسخه و زمان تولید را نگهداری می‌کند.
- `ExecutiveAnalyst` داشبورد مدیریتی و `Auditor` شواهد حسابرسی را دریافت می‌کند.
- رویدادهای کیفیت داده و انتشار برای بازتولید گزارش در `AuditLog` ثبت می‌شوند.

## سطح ۳ — فرایندهای اتمی حیاتی

### DFD-L3.1 — محاسبه حقوق نهایی

```mermaid
flowchart LR
classDef entity fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#000;
classDef process fill:#FFF3E0,stroke:#EF6C00,stroke-width:2px,color:#000;
classDef store fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,color:#000;
EMP[Employee]:::entity
T1([3.1.1 Load Employee]):::process
T2([3.1.2 Load Attendance]):::process
T3([3.1.3 Calculate Gross]):::process
T4([3.1.4 Calculate Deductions]):::process
T5([3.1.5 Calculate Net Pay]):::process
T6([3.1.6 Validate and Persist]):::process
D1[(D1 Employee)]:::store
D4[(D4 PayrollLine)]:::store
D3[(D3 PayrollRun)]:::store
D6[(D3 PayrollRun)]:::store
D6[(D6 BudgetAllocation)]:::store
D14[(D14 AuditLog)]:::store
EMP -->|employee id and period| T1
EMP -->|attendance data| T2
T1 -->|employee profile| T3
D1 -->|base salary and allowances| T3
T2 -->|attendance facts| T3
T3 -->|gross amount| T4
T4 -->|deduction amount| T5
D6 -->|credit availability| T5
T5 -->|net pay| T6
T6 -->|PayrollLine| D4
T6 -->|PayrollRun summary| D3
T6 -->|calculation audit| D14
```

- ورودی‌های اتمی شامل شناسه کارمند، دوره حقوق، وضعیت اشتغال و دادهٔ حضور هستند.
- حقوق ناخالص برابر است با `baseSalary + allowances + approvedOvertime - unpaidLeave`.
- کسورات شامل مالیات، بیمه و کسورات تأییدشده است و `netPay` نباید منفی شود.
- در صورت کمبود اعتبار یا نقض قانون محاسبه، `PayrollLine` ذخیره نمی‌شود و خطا در `AuditLog` ثبت می‌گردد.
- خروجی نهایی یک `PayrollLine` و `PayrollRun` را در `PayrollLine` را تولید و `PayrollRun` را تولید می‌کند.

### DFD-L3.2 — ثبت و تأیید درخواست خرید

```mermaid
flowchart LR
classDef entity fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#000;
classDef process fill:#FFF3E0,stroke:#EF6C00,stroke-width:2px,color:#000;
classDef store fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,color:#000;
PROC[ProcurementOfficer]:::entity
FIN[FinanceManager]:::entity
T1([3.2.1 Create Draft PR]):::process
T2([3.2.2 Validate Lines]):::process
T3([3.2.3 Check Budget]):::process
T4([3.2.4 Manager Approval]):::process
T5([3.2.5 Issue PurchaseOrder]):::process
D7[(D7 PurchaseRequest)]:::store
D6[(D6 BudgetAllocation)]:::store
D8[(D8 PurchaseOrder)]:::store
D9[(D9 Product)]:::store
D14[(D14 AuditLog)]:::store
PROC -->|requester, lines, amount| T1
T1 -->|draft PR| D7
D7 -->|draft PR| T2
D9 -->|product and unit price| T2
T2 -->|valid request| T3
D6 -->|remaining credit| T3
T3 -->|reservation result| T4
FIN -->|approve or reject| T4
T4 -->|approved PR| T5
T5 -->|PurchaseOrder| D8
T5 -->|audit event| D14
T2 -->|validation audit| D14
T3 -->|budget audit| D14
T4 -->|audit
```

<!-- APPEND -->
```

### DFD-L3.3 — تخصی
```mermaid
flowchart LR
classDef entity fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#000;
classDef process fill:#FFF3E0,stroke:#EF6C00,stroke-width:2px,color:#000;
classDef store fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,color:#000;
WH[WarehouseOfficer]:::entity
T1([3.3.1 Select Eligible Lot]):::process
T2([3.3.2 Verify Expiry and Quality]):::process
T3([3.3.3 Reserve Quantity]):::process
T4([3.3.4 Confirm Issue]):::process
D10[(D10 StockLot)]:::store
D9[(D9 Product)]:::store
D11[(D11 GoodsReceipt)]:::store
D14[(D14 AuditLog)]:::store
WH -->|allocation request| T1
D10 -->|available lots| T1
D9 -->|product rules| T2
D11 -->|receipt evidence| T2
T1 -->|selected lot| T2
T2 -->|eligible lot| T3
T3 -->|reserved quantity| D10
T3 -->|reservation result| T4
T4 -->|issue confirmation| D11
T4 -->|allocation audit| D14
```

- انتخاب لات بر اساس کالا، مقدار قابل تخصیص، تاریخ انقضا، کیفیت و قاعدهٔ FEFO انجام می‌شود.
- قبل از رزرو، مقدار درخواستی نباید از `StockLot.availableQuantity` بیشتر باشد.
- رزرو به‌صورت اتمی مقدار موجود را کم و مقدار رزروشده را زیاد می‌کند تا تخصیص همزمان باعث کسری نشود.
- تأیید خروج، رسید کالا و رویداد حسابرسی را به‌روز می‌کند؛ مغایرت فیزیکی فرایند را متوقف می‌کند.
- خروجی نهایی شامل `StockLot` به‌روز، مقدار تخصیص‌یافته، محل تحویل و رویداد `AuditLog` است.

## قوانین یکپارچگی DFD

1. هر فرایند سطح ۲ باید ورودی‌ها و خروجی‌های فرایند والد سطح �1 را حفظ کند.
2. هر تغییر در `Employee`، `BudgetAllocation`، `PurchaseRequest`، `PurchaseOrder`، `StockLot` یا `Payment` باید رویداد `AuditLog` بسازد.
3. `Reporting & Analytics` حق نوشتن در مخازن عملیاتی را ندارد و فقط `Report` را ایجاد می‌کند.
4. بدون بررسی و رزرو اعتبار، پرداخت یا سفارش خرید صادر نمی‌شود.
5. بدون رسید معتبر و لات واجد شرایط، تخصیص کالا انجام نمی‌شود.

<!-- APPEND -->
