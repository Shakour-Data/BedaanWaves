# UML 2.5 Structural Diagrams — Class, Object, Component, Deployment

**عنوان:** UML 2.5 Structural Diagrams — سیستم یکپارچه HR/Finance/Procurement  
**نسخه:** v1.0  
**تاریخ:** 2026-09-09

---

## ۱. مقدمه و قراردادها

این سند چهار نوع نمودار ساختاری UML 2.5 را در سه سطح انتزاع ارائه می‌کند:

- **سطح ۱:** دامنه و چشم‌انداز سیستم
- **سطح ۲:** طراحی و زیرسیستم‌ها
- **سطح ۳:** جزییات پیاده‌سازی، امضاها، قیود و استقرار

نام‌های اصلی عبارت‌اند از `Employee`، `OrganizationUnit`، `PayrollRun`، `PayrollLine`، `Budget`، `BudgetAllocation`، `PurchaseRequest`، `PurchaseOrder`، `Product`، `StockLot`، `GoodsReceipt`، `Payment`، `Report` و `AuditLog`.

---

## ۲. نمودار کلاس — نوع ۱

### ۲.۱ سطح ۱ — مدل دامنه

```plantuml
@startuml ARCH-L1-Class-Domain
skinparam backgroundColor #FEFEFE
skinparam classAttributeIconSize 0

title L1: Domain Model — HR/Finance/Procurement

class Employee
class OrganizationUnit
class PayrollRun
class PayrollLine
class Budget
class BudgetAllocation
class PurchaseRequest
class PurchaseOrder
class Product
class StockLot
class GoodsReceipt
class Payment
class Report
class AuditLog

Employee "1" -- "0..1" OrganizationUnit : assigned to
Employee "1" -- "0..*" PayrollLine : receives
PayrollRun "1" *-- "1..*" PayrollLine : contains
Budget "1" *-- "0..*" BudgetAllocation : allocates
PurchaseRequest "1" -- "0..1" BudgetAllocation : reserves
PurchaseRequest "1" -- "0..*" PurchaseOrder : converts to
PurchaseOrder "1" -- "1" Product : requests
PurchaseOrder "1" -- "0..*" GoodsReceipt : receives
Product "1" -- "0..*" StockLot : stocked as
GoodsReceipt "1" -- "0..*" StockLot : creates
PayrollRun "1" -- "0..*" Payment : initiates
Report "0..*" --> Employee : summarizes
Report "0..*" --> Budget : summarizes
Report "0..*" --> PurchaseOrder : summarizes
AuditLog "0..*" --> Employee : records
AuditLog "0..*" --> BudgetAllocation : records
AuditLog "0..*" --> PurchaseRequest : records
AuditLog "0..*" --> StockLot : records

@enduml
```

**توضیح:** مدل دامنه موجودیت‌های اصلی و روابط معنایی آن‌ها را بدون جزییات فناوری نشان می‌دهد. هر `PayrollRun` از چند `PayrollLine` تشکیل می‌شود و هر `Budget` می‌تواند چند `BudgetAllocation` داشته باشد. `PurchaseRequest` پس از تأیید به `PurchaseOrder` تبدیل می‌شود و رسید کالا، `StockLot` تولید می‌کند. `Report` و `AuditLog` روابط مشاهده‌ای و ممیزی چند حوزه را نگهداری می‌کنند.

### ۲.۲ سطح ۲ — طراحی زیرسیستم‌ها

```plantuml
@startuml ARCH-L2-Class-Design
skinparam backgroundColor #FEFEFE
skinparam classAttributeIconSize 0

title L2: Design Classes and Subsystems

package "HR" {
  class Employee
  class OrganizationUnit
  class LeaveRequest
}

package "Payroll" {
  class PayrollRun
  class PayrollLine
  class SalaryCalculator
  class Payment
}

package "Budget" {
  class Budget
  class BudgetAllocation
  class BudgetValidator
}

package "Procurement" {
  class PurchaseRequest
  class PurchaseOrder
  class ProcurementService
}

package "Inventory" {
  class Product
  class StockLot
  class GoodsReceipt
  class StockManager
}

package "Reporting" {
  class Report
  class ReportEngine
}

package "Shared" {
  class AuditLog
  class Notification
}

Employee "1" -- "0..1" OrganizationUnit
PayrollRun "1" *-- "1..*" PayrollLine
PayrollRun --> SalaryCalculator : uses
SalaryCalculator --> Employee : reads
SalaryCalculator --> PayrollLine : creates
PayrollRun --> Payment : initiates
Budget "1" *-- "0..*" BudgetAllocation
BudgetValidator --> BudgetAllocation : validates
PurchaseRequest --> BudgetValidator : invokes
PurchaseRequest "1" -- "0..*" PurchaseOrder
ProcurementService --> PurchaseRequest : creates
ProcurementService --> PurchaseOrder : issues
GoodsReceipt "1" -- "0..*" StockLot
StockManager --> StockLot : allocates
ReportEngine --> Report : generates
AuditLog <-- HR : logs
AuditLog <-- Payroll : logs
AuditLog <-- Budget : logs
AuditLog <-- Procurement : logs
AuditLog <-- Inventory : logs
Notification <-- HR : sends
Notification <-- Payroll : sends

@enduml
```

**توضیح:** کلاس‌های طراحی، مرز زیرسیستم‌ها و خدمات تخصصی را مشخص می‌کنند. `SalaryCalculator` فقط محاسبه می‌کند، `BudgetValidator` اعتبار را بررسی می‌کند و `StockManager` تخصیص موجودی را انجام می‌دهد. `ProcurementService` درخواست و سفارش را هماهنگ می‌کند و `ReportEngine` خروجی تحلیلی تولید می‌کند. `AuditLog` و `Notification` خدمات مشترک بین همه حوزه‌ها هستند.

### ۲.۳ سطح ۳ — کلاس‌های پیاده‌سازی

```plantuml
@startuml ARCH-L3-Class-Implementation
skinparam backgroundColor #FEFEFE
skinparam classAttributeIconSize 0
skinparam shadowing false

title L3: Implementation Classes

class Employee {
  -id: UUID
  -employeeNo: String
  -fullName: String
  -status: EmploymentStatus
  -baseSalary: Money
  -organizationUnitId: UUID
  +isActive(): boolean
  +changeOrganizationUnit(unitId: UUID): void
}

class PayrollRun {
  -id: UUID
  -period: DateRange
  -status: PayrollStatus
  -approvedBy: UUID
  +calculateSalary(employee: Employee): PayrollLine
  +approve(approver: FinanceManager): void
  +postPayment(gateway: PaymentGateway): Payment
}

class PayrollLine {
  -id: UUID
  -employeeId: UUID
  -grossAmount: Money
  -deductionAmount: Money
  -netAmount: Money
  +validate(): boolean
  +calculateNet(): Money
}

class BudgetAllocation {
  -id: UUID
  -budgetId: UUID
  -organizationUnitId: UUID
  -allocatedAmount: Money
  -reservedAmount: Money
  -spentAmount: Money
  +remaining(): Money
  +checkBudget(amount: Money): BudgetDecision
  +reserve(amount: Money): void
}

class PurchaseRequest {
  -id: UUID
  -requesterId: UUID
  -status: PurchaseRequestStatus
  -totalAmount: Money
  +submit(): void
  +approve(approver: FinanceManager): void
  +reject(reason: String): void
}

class PurchaseOrder {
  -id: UUID
  -requestId: UUID
  -supplierId: UUID
  -status: PurchaseOrderStatus
  +issue(): void
  +acknowledge(): void
}

class StockLot {
  -id: UUID
  -productId: UUID
  -availableQuantity: decimal
  -reservedQuantity: decimal
  -expiresAt: LocalDate
  +allocate(quantity: decimal): AllocationResult
  +release(quantity: decimal): void
}

class Report {
  -id: UUID
  -type: ReportType
  -period: DateRange
  -payload: JSON
  +generateReport(criteria: ReportCriteria): Report
}

class AuditLog {
  -id: UUID
  -actorId: UUID
  -action: String
  -entityType: String
  -entityId: UUID
  -occurredAt: Instant
  +append(event: AuditEvent): void
}

Employee "1" -- "0..*" PayrollLine
PayrollRun "1" *-- "1..*" PayrollLine
PayrollRun --> BudgetAllocation : checkBudget()
PurchaseRequest --> BudgetAllocation : reserve()
PurchaseRequest "1" -- "0..*" PurchaseOrder
PurchaseOrder "1" -- "0..*" StockLot : fulfilled by
StockLot --> AuditLog : logs
PayrollRun --> AuditLog : logs
Report --> AuditLog : publication event

note right of PayrollLine
  invariant: netAmount >= 0
  invariant: netAmount = grossAmount - deductionAmount
end note

note right of BudgetAllocation
  invariant: reservedAmount + spentAmount <= allocatedAmount
end note

note right of StockLot
  invariant: availableQuantity >= 0
  invariant: reservedQuantity >= 0
end note

@enduml
```

**توضیح:** در سطح پیاده‌سازی، دیدگاه_private_ داده‌ها و عملیات_public_ سرویس‌ها نمایش داده شده‌اند. `calculateSalary()` یک `PayrollLine` برمی‌گرداند، `checkBudget()` یک `BudgetDecision` تولید می‌کند و `allocateStock()` در کلاس `StockLot` به‌صورت `allocate()` مدل شده است. قیدها مقدار خالص غیرمنفی، باقی‌مانده بودجه و موجودی قابل تخصیص را کنترل می‌کنند. خطاهای مقدار نامعتبر، کمبود بودجه و تخصیص بیش از موجودی باید به سرویس فراخوانی‌کننده گزارش شوند.

---

## ۳. نمودار شیء — نوع ۲

### ۳.۱ سطح ۱ — نمونه دامنه

```plantuml
@startuml ARCH-L1-Object
skinparam backgroundColor #FEFEFE

title L1: Object Snapshot — Employee Scenario

object "emp-1001\nEmployee" as emp {
  employeeNo = E-1001
  status = Active
}
object "org-fin\nOrganizationUnit" as org {
  name = Finance
}
object "pr-5001\nPurchaseRequest" as pr {
  status = Draft
  totalAmount = 120000000 IRR
}
object "po-7001\nPurchaseOrder" as po {
  status = Created
}
object "lot-9001\nStockLot" as lot {
  availableQuantity = 20
}

emp --> org : assignedTo
pr --> po : approvedAs
po --> lot : fulfilledBy

@enduml
```

**توضیح:** این نمونه یک کارمند فعال، واحد مالی، یک درخواست خرید پیش‌نویس، سفارش ایجادشده و لات موجودی را در یک سناریوی کلی نشان می‌دهد. مقادیر، نمونه‌ای از ارتباط معنایی بین اشیاء هستند و رفتار محاسبه یا پرداخت را اجرا نمی‌کنند. این نما با مدل دامنه سطح ۱ کلاس هم‌خوان است.

### ۳.۲ سطح ۲ — نمونه میانه فرایند

```plantuml
@startuml ARCH-L2-Object
skinparam backgroundColor #FEFEFE

title L2: Object Snapshot — Payroll Calculation

object "run-2026-09\nPayrollRun" as run {
  period = 1405/06
  status = Calculating
}
object "line-1001\nPayrollLine" as line {
  grossAmount = 180000000 IRR
  deductionAmount = 24000000 IRR
  netAmount = 156000000 IRR
}
object "alloc-fin\nBudgetAllocation" as alloc {
  allocatedAmount = 5000000000 IRR
  reservedAmount = 156000000 IRR
  spentAmount = 0 IRR
}
object "audit-88\nAuditLog" as audit {
  action = SalaryCalculated
}

run *-- line : contains
run --> alloc : checks
run --> audit : records

@enduml
```

**توضیح:** شیء `PayrollRun` در میانه محاسبه قرار دارد و `PayrollLine` مقادیر ناخالص، کسورات و خالص را نگهداری می‌کند. `BudgetAllocation` مقدار رزروشده برای پرداخت را نشان می‌دهد و `AuditLog` رویداد محاسبه را ثبت کرده است. این لحظه با `calculateSalary()` و `checkBudget()` در سطح ۳ کلاس مرتبط است.

### ۳.۳ سطح ۳ — نمونه تراکنش مالی بحرانی

```plantuml
@startuml ARCH-L3-Object
skinparam backgroundColor #FEFEFE

title L3: Object Snapshot — Payment Transaction

object "payment-771\nPayment" as payment {
  amount = 156000000 IRR
  status = Processing
  transactionId = null
}
object "run-2026-09\nPayrollRun" as run {
  status = Approved
}
object "alloc-fin\nBudgetAllocation" as alloc {
  allocatedAmount = 5000000000 IRR
  reservedAmount = 156000000 IRR
  spentAmount = 0 IRR
}
object "gateway-result\nTransactionResult" as result {
  status = Pending
  providerReference = null
}
object "audit-772\nAuditLog" as audit {
  action = PaymentPosted
  occurredAt = 2026-09-09T22:00:00+03:30
}

run --> payment : initiates
payment --> alloc : consumes reservation
payment --> result : awaits
payment --> audit : records

@enduml
```

**توضیح:** این نمونه لحظه‌ای را نشان می‌دهد که `Payment` ایجاد شده اما تأییدیه بانک هنوز دریافت نشده است. `transactionId` و `providerReference` هنوز تهی هستند و وضعیت‌ها `Processing` و `Pending` باقی مانده‌اند. پس از تأیید بانک، وضعیت پرداخت به `Paid` تغییر می‌کند، رزرو بودجه به `spentAmount` منتقل می‌شود و رویداد نهایی در `AuditLog` ثبت می‌گردد.

---

## ۴. نمودار مؤلفه — نوع ۳

### ۴.۱ سطح ۱ — مؤلفه‌های سطح بالا

```plantuml
@startuml ARCH-L1-Component
skinparam backgroundColor #FEFEFE
skinparam componentStyle rectangle

title L1: Component Overview

component "HR Management Component" as HR
component "Payroll Component" as PAY
component "Budget Component" as BUD
component "Procurement Component" as PROC
component "Inventory Component" as INV
component "Reporting Component" as REP
component "Audit and Notification" as SHARED

HR --> PAY : employee and attendance
PAY --> BUD : payroll liability
PROC --> BUD : budget reservation
PROC --> INV : expected goods
INV --> REP : stock facts
PAY --> REP : payroll facts
BUD --> REP : budget facts
HR --> SHARED : audit and notification
PAY --> SHARED : audit and notification
PROC --> SHARED : audit and notification
INV --> SHARED : audit and notification

@enduml
```

**توضیح:** مؤلفه‌های سطح بالا مرزهای منطقی HR، حقوق، بودجه، خرید، انبار و گزارش‌گیری را نشان می‌دهند. مؤلفه مشترک، رویدادهای ممیزی و اعلان‌ها را مدیریت می‌کند. جریان‌های بین مؤلفه‌ها با جریان‌های DFD-L1 و Laneهای BPMN-L1 مطابقت دارند.

### ۴.۲ سطح ۲ — زیرمؤلفه‌ها

```plantuml
@startuml ARCH-L2-Component
skinparam backgroundColor #FEFEFE
skinparam componentStyle rectangle

title L2: Internal Components

component "HR API" as HRAPI
component "Employee Service" as EMP
component "Payroll API" as PAYAPI
component "Salary Calculator" as CALC
component "Payment Service" as PAYMENT
component "Budget API" as BUDAPI
component "Budget Validator" as VALIDATOR
component "Procurement API" as PROC_API
component "Purchase Service" as PURCHASE
component "Inventory API" as INV_API
component "Stock Manager" as STOCK
component "Report Engine" as REPORT

HRAPI --> EMP
PAYAPI --> CALC
PAYAPI --> PAYMENT
BUDAPI --> VALIDATOR
PROC_API --> PURCHASE
PURCHASE --> VALIDATOR
PURCHASE --> STOCK
INV_API --> STOCK
REPORT --> EMP
REPORT --> CALC
REPORT --> VALIDATOR
REPORT --> PURCHASE
REPORT --> STOCK

@enduml
```

**توضیح:** هر مؤلفه سطح بالا به API، سرویس دامنه و موتور تخصصی تجزیه شده است. `Salary Calculator` عملیات محاسبه حقوق، `Budget Validator` بررسی اعتبار، `Purchase Service` چرخه درخواست و سفارش، و `Stock Manager` تخصیص موجودی را انجام می‌دهد. `Report Engine` از سرویس‌های دامنه برای ساخت گزارش استفاده می‌کند.

### ۴.۳ سطح ۳ — رابط‌ها و وابستگی‌ها

```plantuml
@startuml ARCH-L3-Component
skinparam backgroundColor #FEFEFE
skinparam componentStyle rectangle

title L3: Provided and Required Interfaces

interface "IPayrollService" as IPay {
  +calculateSalary(employeeId: UUID, period: DateRange): PayrollLine
  +approveRun(runId: UUID, approverId: UUID): void
}
interface "IBudgetService" as IBud {
  +checkBudget(allocationId: UUID, amount: Money): BudgetDecision
  +reserve(allocationId: UUID, amount: Money): Reservation
}
interface "IProcurementService" as IProc {
  +createPurchaseRequest(command: CreatePRCommand): PurchaseRequest
  +approveRequest(requestId: UUID): void
  +issuePurchaseOrder(requestId: UUID): PurchaseOrder
}
interface "IInventoryService" as IInv {
  +recordGoodsReceipt(command: RecordGRCommand): GoodsReceipt
  +allocateStock(lotId: UUID, quantity: decimal): AllocationResult
}
interface "IReportService" as IRep {
  +generateReport(criteria: ReportCriteria): Report
}
interface "IAuditService" as IAudit {
  +append(event: AuditEvent): void
}

component "Payroll Adapter" as PA
component "Salary Calculator" as CALC
component "Budget Adapter" as BA
component "Budget Validator" as VALID
component "Procurement Adapter" as PCA
component "Purchase Service" as PUR
component "Inventory Adapter" as IA
component "Stock Manager" as STOCK
component "Report Engine" as REP
component "Audit Logger" as AUD

PA ..|> IPay
CALC ..|> IPay
BA ..|> IBud
VALID ..|> IBud
PCA ..|> IProc
PUR ..|> IProc
IA ..|> IInv
STOCK ..|> IInv
REP ..|> IRep
AUD ..|> IAudit

CALC ..> IBud : required
PUR ..> IBud : required
PUR ..> IInv : required
REP ..> IPay : required
REP ..> IBud : required
REP ..> IProc : required
REP ..> IInv : required
PUR ..> IAudit : required
CALC ..> IAudit : required
STOCK ..> IAudit : required

@enduml
```

**توضیح:** رابط‌های ارائه‌شده، قراردادهای قابل فراخوانی هر مؤلفه را مشخص می‌کنند. `IPayrollService.calculateSalary()`، `IBudgetService.checkBudget()`، `IProcurementService.approveRequest()`، `IInventoryService.allocateStock()` و `IReportService.generateReport()` نام‌های مشترک با BPMN و DFD دارند. رابط‌های موردنیاز، وابستگی‌های بین مؤلفه‌ها و نقطه ثبت `AuditLog` را نشان می‌دهند.

---

## ۵. نمودار استقرار — نوع ۴

### ۵.۱ سطح ۱ — گره‌های فیزیکی

```plantuml
@startuml ARCH-L1-Deployment
skinparam backgroundColor #FEFEFE
skinparam deploymentStyle rectangle

title L1: Deployment Overview

node "Client Devices" as CLIENT {
  device "Browser / Mobile" as BROWSER
}

node "Application Cluster" as APP {
  component "HR/Finance/Procurement API" as API
  component "Background Workers" as WORKER
}

node "Database Cluster" as DB {
  database "Primary Database" as PRIMARY
  database "Read Replica" as REPLICA
}

node "Reporting Node" as REPORT_NODE {
  component "Report Engine" as REPORT
}

node "External Services" as EXT {
  cloud "Bank/Payment Gateway" as BANK
  cloud "Notification Provider" as NOTIFY
}

BROWSER --> API : HTTPS
API --> PRIMARY : SQL
API --> REPLICA : read SQL
WORKER --> PRIMARY : SQL
REPORT --> REPLICA : read SQL
API --> BANK : HTTPS/API
API --> NOTIFY : HTTPS/Webhook

@enduml
```

**توضیح:** گره‌های اصلی شامل клієнт، خوشه اپلیکیشن، خوشه پایگاه داده و گره گزارش‌گیری هستند. سرویس‌های بانکی و اعلان به‌عنوان سرویس‌های بیرونی مدل شده‌اند. خواندن گزارش از `Read Replica` انجام می‌شود تا بار گزارش‌گیری روی تراکنش‌های عملیاتی کاهش یابد.

### ۵.۲ سطح ۲ — تخصیص مؤلفه‌ها و پروتکل‌ها

```plantuml
@startuml ARCH-L2-Deployment
skinparam backgroundColor #FEFEFE
skinparam deploymentStyle rectangle

title L2: Component Allocation and Protocols

node "API Nodes :8080" as API_NODES {
  component "HR Component" as HR
  component "Payroll Component" as PAY
  component "Budget Component" as BUD
  component "Procurement Component" as PROC
  component "Inventory Component" as INV
  component "Reporting Component" as REP
}

node "Worker Nodes" as WORKERS {
  component "Payroll Worker" as PAY_WORKER
  component "Procurement Worker" as PROC_WORKER
  component "Report Worker" as REP_WORKER
}

node "PostgreSQL Primary :5432" as PRIMARY
node "PostgreSQL Replica :5432" as REPLICA
cloud "Bank Gateway" as BANK
cloud "Message Broker" as BROKER

API_NODES --> PRIMARY : JDBC/SQL write
API_NODES --> REPLICA : JDBC/SQL read
WORKERS --> PRIMARY : JDBC/SQL
PAY_WORKER --> BANK : HTTPS
API_NODES --> BROKER : AMQP/HTTPS
WORKERS --> BROKER : AMQP
REP_WORKER --> REPLICA : JDBC/SQL read
BROKER --> WORKERS : AMQP

@enduml
```

**توضیح:** مؤلفه‌های API روی گره‌های `:8080` مستقر می‌شوند و نوشته‌ها به PostgreSQL Primary و خواندن‌ها به Replica ارسال می‌شوند. Workerها عملیات طولانی حقوق، خرید و گزارش را پردازش می‌کنند. `Message Broker` پیام‌های ناهمگام و.retry را جدا می‌کند و ارتباط با بانک از HTTPS انجام می‌شود.

### ۵.۳ سطح ۳ — کانفیگ و ظرفیت گره‌ها

```plantuml
@startuml ARCH-L3-Deployment
skinparam backgroundColor #FEFEFE
skinparam deploymentStyle rectangle

title L3: Node Configuration and Capacity

node "API Cluster\nOS: Linux 6.8\nInstances: 3\nPort: 8080" as API {
  artifact "hr-finance-procurement-api.jar" as API_JAR
  component "REST API" as REST
  component "Authentication Filter" as AUTH
}

node "Worker Cluster\nOS: Linux 6.8\nInstances: 2\nQueue: payroll/procurement/report" as WORKER {
  artifact "domain-workers.jar" as WORKER_JAR
  component "Payroll Worker" as PAY_WORKER
  component "Procurement Worker" as PROC_WORKER
  component "Report Worker" as REP_WORKER
}

node "PostgreSQL Primary\nVersion: 16\nPort: 5432\nMax connections: 200" as PRIMARY {
  database "operational_db" as OPERATIONAL
}

node "PostgreSQL Replica\nVersion: 16\nPort: 5432\nRead-only" as REPLICA {
  database "reporting_db" as REPORTING
}

node "Report Node\nOS: Linux 6.8\nInstances: 1\nPort: 8081" as REPORT_NODE {
  component "Report Engine" as REPORT
}

cloud "Bank Gateway\nTLS 1.3\nTimeout: 5s\nRetry: 3" as BANK
cloud "Broker\nProtocol: AMQP 1.0\nPort: 5671" as BROKER

API_JAR --> REST
REST --> AUTH
REST --> OPERATIONAL : JDBC :5432
WORKER_JAR --> PAY_WORKER
WORKER_JAR --> PROC_WORKER
WORKER_JAR --> REP_WORKER
PAY_WORKER --> OPERATIONAL : JDBC :5432
PROC_WORKER --> OPERATIONAL : JDBC :5432
REP_WORKER --> REPORTING : JDBC :5432
REPORT --> REPORTING : JDBC :5432
REST --> BANK : HTTPS :443
REST --> BROKER : AMQPS :5671
WORKER_JAR --> BROKER : AMQPS :5671

@enduml
```

**توضیح:** پیکربندی سطح ۳ نسخه سیستم‌عامل، تعداد نمونه‌ها، پورت‌ها، نسخه PostgreSQL، سقف اتصال و زمان انتظار بانک را مشخص می‌کند. API سه نمونه، Worker دو نمونه و Report یک نمونه دارد. تراکنش‌های عملیاتی به Primary و گزارش‌ها به Replica وصل می‌شوند. زمان انتظار بانک پنج ثانیه و تلاش مجدد حداکثر سه بار تعریف شده است.

---

## ۶. ردپا و قوانین یکپارچگی

| نمودار | سطح ۱ | سطح ۲ | سطح ۳ |
|---|---|---|---|
| Class | مدل دامنه | زیرسیستم و خدمات | امضا، Visibility و invariant |
| Object | سناریوی کلی | میانه محاسبه | تراکنش پرداخت |
| Component | مؤلفه‌های حوزه | زیرمؤلفه‌ها | رابط‌های provided/required |
| Deployment | گره‌های فیزیکی | تخصیص و پروتکل | OS، نسخه، پورت و ظرفیت |

1. نام `calculateSalary()` در Class، Component، Sequence و BPMN یکسان است.
2. `checkBudget()` همیشه `BudgetAllocation` را می‌خواند و در صورت تأیید، رزرو ایجاد می‌کند.
3. `allocateStock()` فقط روی `StockLot` معتبر و دارای موجودی قابل تخصیص اجرا می‌شود.
4. `generateReport()` از داده‌های عملیاتی نوشتن انجام نمی‌دهد و `Report` را تولید می‌کند.
5. تمام تغییرات مهم از طریق `AuditLog` و تمام اعلان‌ها از طریق `Notification` ردیابی می‌شوند.

*پایان سند*
