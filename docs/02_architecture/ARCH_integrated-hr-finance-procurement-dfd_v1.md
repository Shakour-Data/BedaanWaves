# مدل جریان داده‌ها (DFD) — سیستم یکپارچه مدیریت منابع انسانی، مالی و خرید

## خلاصه و نقشه‌برداری

| سطح | شناسه | عنوان | ارجاع BPMN/UML |
|---|---|---|---|
| 0 | DFD-L0 | نمودار زمینه (Context) | UC-01 |
| 1 | DFD-L1 | فرآیندهای کلان |泳池泳道 / Component |
| 2 | DFD-L2.1 … L2.6 | تجزیه هر فرآیند کلان | Activity / Sequence / State Machine |
| 3 | DFD-L3.1 … L3.3 | نمودارهای اتمی | Activity Diagram (Atomic) |

---

## سطح 0 — نمودار زمینه (Context Diagram)

```mermaid
flowchart LR
    subgraph External ["اطرافیان بیرونی"]
        EMP[کارمند / Employee]
        MGR[مدیریت / OrganizationUnit]
        VEN[تأمین‌کننده / Vendor]
        BNK[بانک / Bank]
        AUD[حسابرسی / Auditor]
    end
    SYS["سیستم یکپارچه HR، مالی و خرید\n(Integrated HR, Finance & Procurement)"]
    EMP --> SYS
    MGR --> SYS
    VEN --> SYS
    BNK --> SYS
    AUD --> SYS
```

این نمودار کل سیستم را به عنوان یک فرآیند واحد در مرکز قرار می‌دهد.  
هر ذی‌نفع خارجی فقط از طریق رابط‌های مشخص با سیستم تعامل دارد.  
هدف، دامنه کلی جریان داده‌ها و کنترل‌های کلان است.  
برای ردیابی: این نمودار معادل «شرح مورد استفاده» (UC-01) در BPMN و «Use Case Model» در UML است.  
محدودیت: هیچ ذخیره‌سازی یا فرآیند داخلی در این سطح نمایش داده نمی‌شود.  

---

## سطح 1 — نمودار فرآیندهای کلان (Level-1 DFD)

```mermaid
flowchart LR
    subgraph External ["اطرافیان بیرونی"]
        EMP[کارمند / Employee]
        MGR[مدیریت / OrganizationUnit]
        VEN[تأمین‌کننده / Vendor]
        BNK[بانک / Bank]
        AUD[حسابرسی / Auditor]
    end
    subgraph Stores ["ذخایر (Stores)"]
        S1[(Employee)]
        S2[(OrganizationUnit)]
        S3[(Budget)]
        S4[(BudgetAllocation)]
        S5[(Product)]
        S6[(StockLot)]
        S7[(AuditLog)]
        S8[(Report)]
        S9[(Payment)]
    end
    subgraph Processes ["فرآیندهای سطح 1"]
        P1[1. HR Management]
        P2[2. Payroll]
        P3[3. Budget & Credits]
        P4[4. Procurement]
        P5[5. Inventory/Warehouse]
        P6[6. Reporting & Analytics]
    end
    EMP --> P1
    MGR --> P1
    P1 --> S1
    P1 --> S2
    P1 --> P2
    P2 --> S1
    P2 --> P3
    P3 --> S3
    P3 --> S4
    P3 --> P4
    P4 --> VEN
    P4 --> S5
    P4 --> P5
    P5 --> S6
    P5 --> S7
    P5 --> P3
    P6 --> S1
    P6 --> S3
    P6 --> S4
    P6 --> S5
    P6 --> S6
    P6 --> S8
    P6 --> S9
    P6 --> S7
    P6 --> AUD
    P2 --> BNK
    P3 --> BNK
    P3 --> S9
```

شش فرآیند اصلی بر اساس حوزه عملکردی تفکیک شده‌اند.  
داده‌های پایه شامل کارمند، واحد سازمانی، بودجه، تخصیص بودجه، کالا، موجودی و گزارش هستند.  
جریان‌های مالی از طریق «بودجه» و «پرداخت» به پرداخت و خرید متصل هستند.  
همپوشانی‌های منطقی: Payroll ← HR Management، Procurement ← Budget & Credits، Inventory/Warehouse ← Procurement.  
گزارش‌گیری از تمام ذخایر و فرآیندها داده می‌گیرد و گزارش را در Report ذخیره می‌کند.  
ردیابی: معادل «Activity Diagram» و «泳池泳道» در BPMN و «نمودار کامپوننت» در UML است.  
هر فرآیند سطح ۱ در نمودارهای سطح ۲ تفکیک می‌شود.  

---

## سطح 2 — تجزیه فرآیندها (Level-2 DFD)

### DFD-L2.1 — HR Management

```mermaid
flowchart LR
    subgraph External ["اطرافیان"]
        EMP[Employee]
        MGR[OrganizationUnit]
    end
    subgraph Stores ["ذخایر"]
        S1[(Employee)]
        S2[(OrganizationUnit)]
        S3[(AuditLog)]
    end
    subgraph Processes ["فرآیند HR"]
        P1_1[1.1 Recruitment]
        P1_2[1.2 Personnel File]
        P1_3[1.3 Org Structure]
    end
    EMP --> P1_1
    MGR --> P1_3
    P1_1 --> S1
    P1_2 --> S1
    P1_3 --> S2
    P1_1 --> S3
    P1_2 --> S3
    P1_3 --> S3
```

این نمودار فرآیند «مدیریت منابع انسانی» را به سه زیرفرآیند تقسیم می‌کند.  
داده‌های خروجی به Payroll و Reporting & Analytics ارسال می‌شود.  
هر موجودیت (Employee, OrganizationUnit) یک ذخیره مجزا است.  
ردیابی: در BPMN به泳道های «Human Resources» و در UML به «Class Diagram» (Employee, OrganizationUnit) بازمی‌گردد.  
کنترل‌های امنیتی: تنها مدیران مجاز به تغییر ساختار سازمانی هستند.  
تغییرات در Employee و OrganizationUnit همواره در AuditLog ثبت می‌شود.  

### DFD-L2.2 — Payroll

```mermaid
flowchart LR
    subgraph External ["اطرافیان"]
        EMP[Employee]
        BNK[Bank]
    end
    subgraph Stores ["ذخایر"]
        S1[(Employee)]
        S2[(PayrollRun)]
        S3[(PayrollLine)]
        S4[(BudgetAllocation)]
        S5[(AuditLog)]
    end
    subgraph Processes ["فرآیند حقوق و دستمزد"]
        P2_1[2.1 Attendance]
        P2_2[2.2 Salary Calc]
        P2_3[2.3 Payment]
    end
    EMP --> P2_1
    P2_1 --> S3
    S1 --> P2_2
    S3 --> P2_2
    S4 --> P2_2
    P2_2 --> S2
    P2_2 --> S3
    P2_2 --> S5
    P2_3 --> BNK
    P2_3 --> S2
    P2_3 --> S5
```

PayrollRun و PayrollLine برای ردیابی هر اجرای حقوق و خط‌های آن استفاده می‌شود.  
جریان مالی به تجزیه سطح ۳ («محاسبه نهایی حقوق») راهی می‌شود.  
ردیابی: BPMN泳道 «Payroll»؛ UML Sequence Diagram برای محاسبه حقوق.  
همپوشانی: فقط با HR Management (دریافت داده‌های پرسنلی) و Budget & Credits (اعتبار).  
خروجی: PayrollLine شامل دستمزد پایه، اضافات، کسورات و خالص پرداخت است.  
تمام محاسبات در AuditLog برای حسابرسی پیگیری می‌شود.  

### DFD-L2.3 — Budget & Credits

```mermaid
flowchart LR
    subgraph External ["اطرافیان"]
        MGR[OrganizationUnit]
        BNK[Bank]
    end
    subgraph Stores ["ذخایر"]
        S1[(Budget)]
        S2[(BudgetAllocation)]
        S3[(Payment)]
        S4[(AuditLog)]
    end
    subgraph Processes ["فرآیند بودجه و اعتبار"]
        P3_1[3.1 Budget Plan]
        P3_2[3.2 Allocation]
        P3_3[3.3 Payment]
    end
    MGR --> P3_1
    P3_1 --> S1
    P3_2 --> S2
    S2 --> P3_3
    P3_3 --> BNK
    P3_3 --> S3
    P3_3 --> S4
```

BudgetAllocation برای تقسیم اعتبار به واحدهای سازمانی یا پروژه‌ها به کار می‌رود.  
Payment به عنوان ذخیره مشترک با Procurement و Payroll عمل می‌کند.  
ردیابی: BPMN泳道 «Finance»؛ UML Class Diagram برای موجودیت‌های مالی.  
محدودیت: پرداخت‌ها تنها در صورت کافی بودن اعتبار تایید می‌شوند.  
خلاصه بودجه به Reporting & Analytics برای تحلیل ارسال می‌شود.  

### DFD-L2.4 — Procurement

```mermaid
flowchart LR
    subgraph External ["اطرافیان"]
        MGR[OrganizationUnit]
        VEN[Vendor]
    end
    subgraph Stores ["ذخایر"]
        S1[(PurchaseRequest)]
        S2[(PurchaseOrder)]
        S3[(BudgetAllocation)]
        S4[(Product)]
        S5[(GoodsReceipt)]
        S6[(AuditLog)]
    end
    subgraph Processes ["فرآیند خرید"]
        P4_1[4.1 Requisition]
        P4_2[4.2 Approval]
        P4_3[4.3 PO Creation]
    end
    MGR --> P4_1
    P4_1 --> S1
    P4_2 --> S1
    P4_2 --> S2
    P4_2 --> S3
    P4_3 --> VEN
    P4_3 --> S2
    P4_3 --> S5
    P4_3 --> S6
```

PurchaseRequest تا PurchaseOrder و سپس GoodsReceipt جریان دارد.  
ردیابی: BPMN泳道 «Procurement»؛ UML Activity Diagram برای تأیید خرید.  
همپوشانی: با Inventory/Warehouse از طریق Product و GoodsReceipt.  
نقطه اتمی در سطح ۳: «تأیید درخواست خرید».  
کنترل‌ها: هیچ PurchaseOrder بدون تأیید BudgetAllocation صادر نمی‌شود.  

### DFD-L2.5 — Inventory/Warehouse

```mermaid
flowchart LR
    subgraph External ["اطرافیان"]
        VEN[Vendor]
        MGR[OrganizationUnit]
    end
    subgraph Stores ["ذخایر"]
        S1[(Product)]
        S2[(StockLot)]
        S3[(GoodsReceipt)]
        S4[(AuditLog)]
    end
    subgraph Processes ["فرآیند انبار"]
        P5_1[5.1 Receiving]
        P5_2[5.2 Stocking]
        P5_3[5.3 Allocation]
    end
    VEN --> P5_1
    P5_1 --> S3
    P5_2 --> S2
    P5_3 --> S2
    MGR --> P5_3
    P5_1 --> S4
    P5_2 --> S4
    P5_3 --> S4
```

StockLot برای پیگیری سریال یا lot کالاها استفاده می‌شود.  
Allocation به Budget & Credits و Reporting & Analytics باز می‌گردد.  
ردیابی: BPMN泳道 «Warehouse»؛ UML State Machine برای چرخه عمر StockLot.  
نقطه اتمی در سطح ۳: «تخصیص موجودی».  
خروجی: GoodsReceipt برای ورود کالا و AuditLog برای ردیابی ثبت می‌شود.  

### DFD-L2.6 — Reporting & Analytics

```mermaid
flowchart LR
    subgraph External ["اطرافیان"]
        MGR[OrganizationUnit]
        AUD[Auditor]
    end
    subgraph Stores ["ذخایر"]
        S1[(Employee)]
        S2[(Budget)]
        S3[(BudgetAllocation)]
        S4[(PurchaseOrder)]
        S5[(StockLot)]
        S6[(AuditLog)]
        S7[(Report)]
    end
    subgraph Processes ["فرآیند گزارش‌گیری"]
        P6_1[6.1 Data Integration]
        P6_2[6.2 Analytics]
        P6_3[6.3 Export]
    end
    S1 --> P6_1
    S2 --> P6_1
    S3 --> P6_1
    S4 --> P6_1
    S5 --> P6_1
    S6 --> P6_1
    P6_1 --> P6_2
    P6_2 --> P6_3
    P6_3 --> S7
    P6_3 --> MGR
    P6_3 --> AUD
```

تمام ذخایر اصلی به عنوان منبع داده در این فرآیند گردهم می‌آیند.  
گزارش‌ها به صورت Report تولید و به مدیران و حسابرسان ارائه می‌شوند.  
ردیابی: BPMN泳道 «Reporting»؛ UML Component Diagram برای لایه گزارش‌گیری.  
خروجی: Report به OrganizationUnit و Auditor ارسال می‌شود.  
این فرآیند هیچ تغییری در ذخایر اصلی ایجاد نمی‌کند؛ فقط خواندن و تحلیل.  

---

## سطح ۳ — نمودارهای اتمی (Level-3 DFD)

### DFD-L3.1 — محاسبه نهایی حقوق (Final Salary Calculation)

```mermaid
flowchart LR
    subgraph External ["اطرافیان"]
        EMP[Employee]
    end
    subgraph Stores ["ذخایر"]
        S1[(Employee)]
        S2[(PayrollRun)]
        S3[(PayrollLine)]
        S4[(BudgetAllocation)]
        S5[(AuditLog)]
    end
    subgraph Processes ["اتم‌های حقوق"]
        T1[3.1.1 Fetch Base Salary]
        T2[3.1.2 Calc Allowances]
        T3[3.1.3 Deductions]
        T4[3.1.4 Net Pay]
    end
    EMP --> S1
    S1 --> T1
    T1 --> T2
    T2 --> T3
    T3 --> T4
    T4 --> S3
    S4 --> T2
    T4 --> S2
    T4 --> S5
```

این نمودار اتمی مسیر دقیق محاسبه حقوق را از داده‌های پایه تا خروجی نهایی نشان می‌دهد.  
هر مهار (step) یک وظیفه atomic در سطح BPMN و یک تراکنش در Sequence Diagram است.  
ردیابی: BPMN泳道 «Payroll»، فعالیت‌های ۳.۱.۱ تا ۳.۱.۴؛ UML Activity Diagram.  
خروجی: PayrollLine شامل دستمزد پایه، اضافات، کسورات و خالص پرداخت است.  
AuditLog برای پیگیری هر محاسبه الزامی است.  

### DFD-L3.2 — تأیید درخواست خرید (Purchase-Request Approval)

```mermaid
flowchart LR
    subgraph External ["اطرافیان"]
        MGR[OrganizationUnit]
        VEN[Vendor]
    end
    subgraph Stores ["ذخایر"]
        S1[(PurchaseRequest)]
        S2[(BudgetAllocation)]
        S3[(PurchaseOrder)]
        S4[(AuditLog)]
    end
    subgraph Processes ["اتم‌های خرید"]
        T1[3.2.1 Create PR]
        T2[3.2.2 Check Budget]
        T3[3.2.3 Manager Approval]
        T4[3.2.4 Issue PO]
    end
    MGR --> T1
    T1 --> S1
    S1 --> T2
    S2 --> T2
    T2 --> T3
    T3 --> T4
    T4 --> S3
    T4 --> VEN
    T4 --> S4
```

مراحل اتمی از ایجاد درخواست تا صدور PurchaseOrder را پوشش می‌دهد.  
بررسی بودجه و تأیید مدیر نقاط بحرانی تصمیم‌گیری هستند.  
ردیابی: BPMN泳道 «Procurement»، وابستگی‌های Sequence؛ UML Activity Diagram.  
خروجی: PurchaseOrder به Vendor ارسال می‌شود و در AuditLog ثبت می‌گردد.  
هیچ PurchaseRequest بدون تایید BudgetAllocation به Approval نمی‌رسد.  

### DFD-L3.3 — تخصیص موجودی (Stock Allocation)

```mermaid
flowchart LR
    subgraph External ["اطرافیان"]
        MGR[OrganizationUnit]
    end
    subgraph Stores ["ذخایر"]
        S1[(StockLot)]
        S2[(Product)]
        S3[(GoodsReceipt)]
        S4[(AuditLog)]
    end
    subgraph Processes ["اتم‌های انبار"]
        T1[3.3.1 Select Lot]
        T2[3.3.2 Verify Expiry]
        T3[3.3.3 Reserve Qty]
        T4[3.3.4 Confirm Issue]
    end
    S3 --> S1
    S1 --> T1
    T1 --> T2
    T2 --> T3
    T3 --> S1
    MGR --> T3
    T4 --> S4
```

تخصیص موجودی از انتخاب lot تا تایید خروج را دنبال می‌کند.  
اعتبارسنجی انقضا (expiry) قبل از رزرو الزامی است.  
ردیابی: BPMN泳道 «Warehouse»؛ UML State Machine برای StockLot.  
خروجی: کسری یا اضافی موجودی در AuditLog ثبت می‌شود.  
Product و StockLot به عنوان مرجع اصلی برای تخصیص به کار می‌روند.  

---

## ردیابی کلی (Traceability Matrix)

| شناسه DFD | عنوان | BPMN泳道 / Activity | UML artifact |
|---|---|---|---|
| DFD-L0 | Context | UC-01 | Use Case Diagram |
| DFD-L1 | Level-1 |泳池泳道 کلان | Component Diagram |
| DFD-L2.1 | HR Management |泳道 HR | Class Diagram |
| DFD-L2.2 | Payroll |泳道 Payroll | Sequence Diagram |
| DFD-L2.3 | Budget & Credits |泳道 Finance | Class Diagram |
| DFD-L2.4 | Procurement |泳道 Procurement | Activity Diagram |
| DFD-L2.5 | Inventory/Warehouse |泳道 Warehouse | State Machine |
| DFD-L2.6 | Reporting & Analytics |泳道 Reporting | Component Diagram |
| DFD-L3.1 | Final Salary Calc | Activity 3.1.x | Activity Diagram |
| DFD-L3.2 | PR Approval | Activity 3.2.x | Activity Diagram |
| DFD-L3.3 | Stock Allocation | Activity 3.3.x | State Machine |

هر نمودار DFD با یک یا چند Artefact BPMN/UML نگاشت شده است.  
این ماتریس به عنوان مرجع برای هماهنگی بین تیم‌های تحلیل، توسعه و تست استفاده می‌شود.  
در صورت تغییر هر یک از فرآیندها، ردیابی در این ماتریس به‌روزرسانی خواهد شد.  
Artifactهای UML شامل Use Case, Class, Sequence, Activity و State Machine می‌باشند.  
BPMN泳道ها دقیقاً با فرآیندهای سازمانی (HR, Finance, Procurement, Warehouse, Reporting) تطبیق داده شده‌اند.  

---

*تاریخ تهیه: 2026-09-09*  
*نسخه: v1.0*
