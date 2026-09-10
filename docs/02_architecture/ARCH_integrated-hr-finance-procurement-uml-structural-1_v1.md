# UML 2.5 Structural Diagrams — Class, Object, Component, Deployment

**Title:** UML 2.5 Structural Diagrams — Integrated HR/Finance/Procurement System
**Version:** v1.0
**Date:** 2026-09-09

---

## 1. Introduction and Conventions

This document presents four types of UML 2.5 structural diagrams at three levels of abstraction:

- **Level 1:** Domain and System Context
- **Level 2:** Design and Subsystems
- **Level 3:** Implementation Details, Signatures, Constraints, and Deployment

Key entities are `Employee`, `OrganizationUnit`, `PayrollRun`, `PayrollLine`, `Budget`, `BudgetAllocation`, `PurchaseRequest`, `PurchaseOrder`, `Product`, `StockLot`, `GoodsReceipt`, `Payment`, `Report`, and `AuditLog`.

---

## 2. Class Diagram — Type 1

### 2.1 Level 1 — Domain Model

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

**Description:** The domain model shows core entities and their semantic relationships without technical details. Each `PayrollRun` consists of multiple `PayrollLine` items, and each `Budget` can have multiple `BudgetAllocation` items. A `PurchaseRequest` converts to a `PurchaseOrder` upon approval, and a goods receipt creates `StockLot` items. `Report` and `AuditLog` maintain cross-domain observation and audit relationships.

### 2.2 Level 2 — Subsystem Design

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

**Description:** Design classes define subsystem boundaries and specialized services. `SalaryCalculator` performs calculations only, `BudgetValidator` checks validity, and `StockManager` handles stock allocation. `ProcurementService` coordinates requests and orders, and `ReportEngine` produces analytical output. `AuditLog` and `Notification` are shared services across all domains.

### 2.3 Level 3 — Implementation Classes

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
}

class ReportEngine {
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
endnote

note right of BudgetAllocation
  invariant: reservedAmount + spentAmount <= allocatedAmount
endnote

note right of StockLot
  invariant: availableQuantity >= 0
  invariant: reservedQuantity >= 0
endnote

@enduml
```

**Description:** At the implementation level, private data and public service operations are shown. `calculateSalary()` returns a `PayrollLine`, `checkBudget()` produces a `BudgetDecision`, and `allocate()` on `StockLot` models the entity operation with `allocateStock()` as the service alias. Constraints enforce non-negative net amount, remaining budget, and allocatable stock. Errors for invalid amounts, budget shortfalls, and over-allocation must be reported to the calling service.

---

## 3. Object Diagram — Type 2

### 3.1 Level 1 — Domain Snapshot

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

**Description:** This snapshot shows an active employee, the Finance unit, a draft purchase request, a created order, and a stock lot in a single scenario. Values represent sample semantic links between objects and do not execute calculation or payment behavior. This view is consistent with the Level 1 class domain model.

### 3.2 Level 2 — Mid-Process Snapshot

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

**Description:** The `PayrollRun` object is mid-calculation and the `PayrollLine` holds gross, deduction, and net amounts. `BudgetAllocation` shows the reserved amount for payment, and `AuditLog` has recorded the calculation event. This moment relates to `calculateSalary()` and `checkBudget()` in the Level 3 class diagram.

### 3.3 Level 3 — Critical Financial Transaction Snapshot

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

**Description:** This snapshot shows a moment where `Payment` has been created but bank confirmation has not yet been received. `transactionId` and `providerReference` are still null, and statuses remain `Processing` and `Pending`. After bank confirmation, the payment status changes to `Paid`, the budget reservation moves to `spentAmount`, and the final event is recorded in `AuditLog`.

---

## 4. Component Diagram — Type 3

### 4.1 Level 1 — Top-Level Components

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

**Description:** Top-level components show logical boundaries for HR, Payroll, Budget, Procurement, Inventory, and Reporting. The shared component manages audit events and notifications. Inter-component flows align with DFD-L1 flows and BPMN-L1 lanes.

### 4.2 Level 2 — Subcomponents

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

**Description:** Each top-level component decomposes into API, domain service, and specialized engine. `Salary Calculator` performs payroll calculation, `Budget Validator` checks validity, `Purchase Service` handles the request and order lifecycle, and `Stock Manager` handles stock allocation. `Report Engine` uses domain services to build reports.

### 4.3 Level 3 — Provided and Required Interfaces

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

**Description:** Provided interfaces specify each component's callable contracts. `IPayrollService.calculateSalary()`, `IBudgetService.checkBudget()`, `IProcurementService.approveRequest()`, `IInventoryService.allocateStock()`, and `IReportService.generateReport()` share names with BPMN and DFD. Required interfaces show inter-component dependencies and the `AuditLog` registration point.

---

## 5. Deployment Diagram — Type 4

### 5.1 Level 1 — Physical Nodes

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

**Description:** Primary nodes include clients, the application cluster, the database cluster, and the reporting node. Banking and notification services are modeled as external services. Report reads use the `Read Replica` to reduce load on operational transactions.

### 5.2 Level 2 — Component Allocation and Protocols

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

**Description:** API components deploy on `:8080` nodes with writes to PostgreSQL Primary and reads from Replica. Workers process long-running payroll, procurement, and reporting operations. The `Message Broker` decouples async messages and retries, and bank communication uses HTTPS.

### 5.3 Level 3 — Node Configuration and Capacity

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

**Description:** Level 3 configuration specifies OS version, instance counts, ports, PostgreSQL version, connection limits, and bank timeout. API has three instances, Worker has two, and Report has one. Operational transactions connect to Primary and reports to Replica. Bank timeout is five seconds with a maximum of three retries.

---

## 6. Traceability and Integrity Rules

| Diagram | Level 1 | Level 2 | Level 3 |
|---|---|---|---|
| Class | Domain Model | Subsystems and Services | Signatures, Visibility, and Invariants |
| Object | Overview Scenario | Mid-Calculation | Payment Transaction |
| Component | Domain Components | Subcomponents | Provided/Required Interfaces |
| Deployment | Physical Nodes | Allocation and Protocols | OS, Version, Port, and Capacity |

1. The name `calculateSalary()` is consistent across Class, Component, Sequence, and BPMN diagrams.
2. `checkBudget()` always reads `BudgetAllocation` and creates a reservation upon approval.
3. `allocateStock()` executes only on a valid `StockLot` with allocatable quantity.
4. `generateReport()` does not write to operational data and produces a `Report`.
5. All significant changes are tracked via `AuditLog` and all notifications via `Notification`.

*End of Document*