# DFD — Integrated HR, Finance & Procurement Management System

**Title:** Integrated HR, Finance & Procurement Management System  
**Version:** v1.0  
**Date:** 2026-09-09

## Traceability Map

| Level | ID | Content | Primary Output |
|---|---|---|---|
| 0 | DFD-L0 | System context and boundary | External actors and boundary flows |
| 1 | DFD-L1 | Six high-level processes | Domain-level data architecture |
| 2 | DFD-L2.1 through L2.6 | Decomposition of each high-level process | Operational sub-processes |
| 3 | DFD-L3.1 through L3.3 | Critical atomic processes | Detailed data transformation rules |

## Naming Convention

- External entities use the names `Employee`, `HRManager`, `FinanceManager`, `ProcurementOfficer`, `WarehouseOfficer`, `Supplier`, `BankGateway`, `ExecutiveAnalyst`, and `Auditor`.
- Data stores are numbered `D1` through `D14`, with each store's logical name included in its label.
- Processes use level and domain numbers, such as `2.2` or `3.1.4`.
- Flows carry data names, and input/output arrows preserve DFD balance.
- `AuditLog` records all material changes, and `Report` contains analytical outputs.

---

## Level 0 — Context Diagram

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

This diagram defines the system boundary and treats the software as one process.  
`Employee` provides identity, leave, and attendance data and receives salary slips and notifications.  
`HRManager`, `FinanceManager`, `ProcurementOfficer`, and `WarehouseOfficer` are internal organizational roles that submit decisions and operations for their domains.  
`Supplier` and `BankGateway` are external supply and payment systems, while `ExecutiveAnalyst` and `Auditor` receive management and audit outputs.  
No internal data stores appear at this level; every flow crosses the system boundary.  
This diagram aligns with the Level-1 UML Use Case Diagram.

---

## Level 1 — High-Level Processes

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
    P6 -->|integrated facts| D1
    P6 -->|budget facts| D5
    P6 -->|allocation facts| D6
    P6 -->|purchase and stock facts| D8
    P6 -->|stock facts| D10
    P6 -->|audit facts| D14
    P6 -->|published report| D13
    D13 -->|dashboard and analytical report| EXEC
    D13 -->|audit report| AUD
```

شش فرایند کلان، پنج حوزه درخواستی به‌علاوه گزارش‌گیری تحلیلی را پوشش می‌دهند.  
`HR Management` منبع داده `Employee` و `OrganizationUnit` را برای حقوق و گزارش‌ها فراهم می‌کند.  
`Payroll` از داده‌های پرسنلی و بودجه استفاده می‌کند و `PayrollRun`، `PayrollLine` و `Payment` را تولید می‌کند.  
`Budget & Credits` اعتبار را تعریف و تخصیص می‌دهد و قبل از خرید یا پرداخت، مانده `BudgetAllocation` را کنترل می‌کند.  
`Procurement` و `Inventory/Warehouse` زنجیره درخواست خرید، سفارش، رسید کالا، `Product` و `StockLot` را به‌هم وصل می‌کنند.  
`Reporting & Analytics` فقط داده‌های حوزه‌ای را می‌خواند، `Report` را تولید می‌کند و خروجی را به `ExecutiveAnalyst` و `Auditor` می‌دهد.

---

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
    D1[(D1 Employee)]:::store
    D2[(D2 OrganizationUnit)]:::store
    D14[(D14 AuditLog)]:::store

    EMP -->|application and profile| P11
    HRM -->|review and decision| P14
    P11 -->|candidate and hire data| P12
    P12 -->|employee record| D1
    P13 -->|unit hierarchy| D2
    P14 -->|approved status| D1
    P14 -->|org assignment| D2
    P11 -->|audit event| D14
    P12 -->|audit event| D14
    P13 -->|audit event| D14
    P14 -->|audit event| D14
```

این نمودار استخدام، پرونده پرسنلی، ساختار سازمانی و تأیید تغییرات استخدامی را جدا می‌کند.  
ورودی `Employee` شامل درخواست و اطلاعات هویتی است و `HRManager` تصمیم استخدام، انتقال یا خاتمه همکاری را ثبت می‌کند.  
`D1 Employee` رکورد پایدار پرسنلی و `D2 OrganizationUnit` سلسله‌مراتب واحد سازمانی است.  
تمام تغییرات وضعیت و ساختار، یک رویداد در `D14 AuditLog` ایجاد می‌کنند.  
خروجی‌های تأییدشده به فرایند حقوق ارسال می‌شوند تا eligiblity و داده‌های محاسبه به‌روز باشد.

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

`PayrollRun` شناسه اجرای حقوق و `PayrollLine` جزئیات هر کارمند را نگهداری می‌کند.  
فرایند محاسبه از `Employee`، حضور، مزایا، کسورات و مانده `BudgetAllocation` استفاده می‌کند.  
`FinanceManager` پیش از ارسال به درگاه، جمع خالص و اعتبار را تأیید می‌کند.  
نتیجه بانک به `Payment` و `AuditLog` نوشته می‌شود و خطای درگاه مسیر retry را فعال می‌کند.  
این تجزیه مستقیماً با `calculateSalary()` و `postPayment()` در UML و BPMN سطح ۳ مرتبط است؛ امضای این متدها در Class Diagram سطح ۳ تعریف شده‌اند.

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

بودجه سالانه در `D5 Budget` و سهم هر واحد یا پروژه در `D6 BudgetAllocation` نگهداری می‌شود.  
`checkBudget()` قبل از رزرو، مقدار درخواست را با `remaining` مقایسه می‌کند.  
رزرو موقت از کاهش همزمان اعتبار توسط درخواست‌های موازی جلوگیری می‌کند.  
پرداخت موفق باعث آزادسازی یا تطبیق اعتبار و ثبت `Payment` می‌شود.  
کمبود اعتبار، درخواست تخصیص مجدد یا رد درخواست را از طریق BPMN سطح ۳ فعال می‌کند.

### DFD-L2.4 — تدارکات و خرید

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
    P41 -->|draft request| D7
    P42 -->|validation result| D7
    D9 -->|product and price| P42
    P43 -->|budget decision| D6
    P42 -->|valid request| P43
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

`PurchaseRequest` قبل از تأیید، اعتبارسنجی کامل بودن سطرها، قیمت و شناسه کالا را انجام می‌دهد.  
`BudgetAllocation` در `4.3 Check Budget` خوانده و در صورت تأیید، مقدار درخواست رزرو می‌شود.  
فقط درخواست تأییدشده به `PurchaseOrder` تبدیل می‌شود و برای `Supplier` ارسال می‌گردد.  
پاسخ تامین‌کننده و شرایط تحویل به مخزن سفارش و رویدادهای ممیزی وصل است.  
این نمودار با DFD-L3.2 و BPMN-L3 Budget Check for Purchase Request هم‌ردیف است.

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
    P54 -->|reserved quantity| D10
    P54 -->|issue confirmation| D11
    P51 -->|receipt audit| D14
    P52 -->|inspection audit| D14
    P53 -->|lot audit| D14
    P54 -->|allocation audit| D14
```

رسید فیزیکی با مقدار سفارش و فهرست حمل تامین‌کننده تطبیق داده می‌شود.  
کالای پذیرفته‌شده به `GoodsReceipt` و سپس به `StockLot` با محل، تاریخ انقضا و مقدار تبدیل می‌شود.  
`allocateStock()` مقدار رزروشده را از موجودی قابل تخصیص کسر و وضعیت لات را به‌روز می‌کند.  
مغایرت تعداد یا کیفیت، گزارش تفاوت ایجاد می‌کند و از ثبت موجودی قطعی جلوگیری می‌کند.  
رخدادهای دریافت، بازرسی، ساخت لات و تخصیص در `AuditLog` قابل ممیزی هستند.

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
    P61 -->|employee facts| D1
    P61 -->|payroll facts| D3
    P61 -->|budget facts| D5
    P61 -->|allocation facts| D6
    P61 -->|purchase facts| D7
    P61 -->|order facts| D8
    P61 -->|stock facts| D10
    P61 -->|audit facts| D14
    P61 -->|extracted dataset| P62
    P62 -->|validated dataset| P63
    P63 -->|metrics and trends| P64
    P64 -->|published report| D13
    D13 -->|dashboard| EXEC
    D13 -->|audit evidence| AUD
    P62 -->|quality event| D14
    P64 -->|publication event| D14
```

گزارش‌گیری از مخازن اصلی خواندن انجام می‌دهد و هیچ رکورد عملیاتی حوزه‌ای را تغییر نمی‌دهد.  
استخراج، اعتبارسنجی، تبدیل و محاسبه شاخص‌ها به‌ترتیب انجام می‌شوند تا گزارش‌های ناسازگار منتشر نشوند.  
`Report` شامل دوره، فیلترها، معیارها، نسخه و زمان تولید است.  
`ExecutiveAnalyst` داشبورد مدیریتی و `Auditor` شواهد ممیزی دریافت می‌کند.  
رخداد کیفیت داده و انتشار گزارش برای ردیابی و بازتولید گزارش در `AuditLog` ثبت می‌شود.

---

## سطح ۳ — فرایندهای اتمی بحرانی

### DFD-L3.1 — محاسبه نهایی حقوق

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
    D6[(D6 BudgetAllocation)]:::store
    D14[(D14 AuditLog)]:::store

    EMP -->|employee id and period| T1
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

ورودی اتمی شامل شناسه کارمند، دوره حقوق، وضعیت استخدام و داده‌های حضور است.  
قانون تبدیل ناخالص برابر است با `baseSalary + allowances + approved overtime - unpaidLeave`.  
کسورات شامل مالیات، بیمه و سایر کسرهای تأییدشده است و خالص نباید منفی شود.  
در صورت ناکافی بودن اعتبار یا نقض قانون محاسبه، `PayrollLine` پایدار نمی‌شود و خطا در `AuditLog` ثبت می‌گردد.  
خروجی نهایی یک `PayrollLine` با مقادیر ناخالص، کسورات، خالص و نسخه قوانین است که به `PayrollRun` جمع می‌شود.

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
    T4 -->|approval audit| D14
```

درخواست باید دارای درخواست‌دهنده فعال، حداقل یک سطر، مقدار مثبت و کالای معتبر باشد.  
`checkBudget()` مقدار کل درخواست را با مانده تخصیص مقایسه و در صورت موفقیت، رزرو موقت ایجاد می‌کند.  
تأیید مدیر فقط پس از اعتبارسنجی و رزرو بودجه امکان‌پذیر است و رد درخواست، رزرو را آزاد می‌کند.  
صدور `PurchaseOrder` یک عمل اتمی است و شماره سفارش، تامین‌کننده، مبلغ و مهلت تحویل را پایدار می‌کند.  
همه تصمیم‌ها و تغییرات بودجه در `AuditLog` ثبت می‌شوند تا درخواست قابل ممیزی باشد.

### DFD-L3.3 — تخصیص کالا به درخواست‌کننده

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

انتخاب لات بر اساس محصول، مقدار قابل تخصیص، تاریخ انقضا، کیفیت و قانون FEFO انجام می‌شود.  
قبل از رزرو، مقدار درخواست باید از `StockLot.availableQuantity` بیشتر نباشد.  
رزرو به‌صورت اتمی مقدار `availableQuantity` را کاهش و مقدار `reservedQuantity` را افزایش می‌دهد تا تخصیص موازی باعث کسری نشود.  
تأیید خروج، رسید کالا و رویداد ممیزی را به‌روز می‌کند و در صورت مغایرت فیزیکی، تخصیص متوقف می‌شود.  
خروجی نهایی شامل `StockLot` به‌روز، مقدار تخصیص‌یافته، محل تحویل و `AuditLog` است.

---

## ماتریس ردیابی

| شناسه DFD | فرایند | BPMN | UML |
|---|---|---|---|
| DFD-L0 | Context | BPMN-L1 Overview | Use Case Diagram |
| DFD-L1 | Level-1 processes | BPMN-L1 Pools | Component Diagram |
| DFD-L2.1 | HR Management | BPMN-L2 HR | Class Diagram |
| DFD-L2.2 | Payroll | BPMN-L2 Payroll / L3 Payroll Approval | Sequence Diagram |
| DFD-L2.3 | Budget & Credits | BPMN-L2 Budget / L3 Budget Check | Class Diagram |
| DFD-L2.4 | Procurement | BPMN-L2 Procurement / L3 PR Approval | Activity Diagram |
| DFD-L2.5 | Inventory/Warehouse | BPMN-L2 Inventory / L3 Stock Allocation | State Machine Diagram |
| DFD-L2.6 | Reporting & Analytics | BPMN-L2 Reporting | Component Diagram |
| DFD-L3.1 | Final Salary Calculation | `calculateSalary()` | PayrollRun / PayrollLine |
| DFD-L3.2 | Purchase-Request Approval | `checkBudget()` / approve PR | PurchaseRequest / BudgetAllocation |
| DFD-L3.3 | Stock Allocation | `allocateStock()` | StockLot / GoodsReceipt |

## قوانین یکپارچگی

1. هر فرایند سطح ۲ باید ورودی و خروجی‌های متناظر با فرایند والد سطح ۱ را حفظ کند.
2. هر تغییر در `Employee`، `BudgetAllocation`، `PurchaseRequest`، `PurchaseOrder`، `StockLot` یا `Payment` باید `AuditLog` تولید کند.
3. `Reporting & Analytics` حق نوشتن در مخازن عملیاتی ندارد و فقط `Report` را ایجاد می‌کند.
4. هیچ پرداخت یا سفارش خرید بدون بررسی و رزرو اعتبار صادر نمی‌شود.
5. هیچ تخصیص موجودی بدون رسید معتبر و لات واجد شرایط انجام نمی‌شود.

*پایان سند DFD*
