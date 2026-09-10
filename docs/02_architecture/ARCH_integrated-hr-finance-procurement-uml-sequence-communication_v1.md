# UML 2.5 Interaction Diagrams — Sequence and Communication

**Title:** UML 2.5 Interaction Diagrams — Integrated HR/Finance/Procurement System
**Version:** v1.0
**Date:** 2026-09-09

---

## 1. Introduction

This document presents two types of UML 2.5 interaction diagrams at three levels of abstraction:

- **Sequence:** The temporal order of messages, loops, branches, asynchronous calls, and error handling.
- **Communication:** Object links and message numbers, with a focus on structural collaboration.

Names shared with the DFD, BPMN, and Class Diagram include `Employee`, `PayrollRun`, `BudgetAllocation`, `PurchaseRequest`, `PurchaseOrder`, `StockLot`, `GoodsReceipt`, `Payment`, `Report`, and `AuditLog`.

---

## 2. Sequence Diagrams — Type 11

### 2.1 Level 1 — Generate Financial Report

```plantuml
@startuml ARCH-L1-Sequence-Report
skinparam backgroundColor #FEFEFE
autonumber

title L1: Generate Financial Report

actor "Executive Analyst" as EXEC
participant "Report API" as API
participant "Report Engine" as ENGINE
database "Reporting DB" as DB

EXEC -> API : ReportEngine.generateReport(criteria)
API -> ENGINE : ReportEngine.generateReport(criteria)
ENGINE -> DB : read aggregated facts
DB --> ENGINE : dataset
ENGINE --> API : Report
API --> EXEC : Report

@enduml
```

**Explanation:** The analyst provides the report criteria to the API. The Report Engine reads aggregated data from the Reporting DB and returns a `Report`. This scenario is consistent with DFD-L2.6 and the Reporting component in the Class/Component diagrams. At Level 1, only the overall call order is shown; error and queue details are added at later levels.

### 2.2 Level 2 — Calculate an Employee's Salary

```plantuml
@startuml ARCH-L2-Sequence-Payroll
skinparam backgroundColor #FEFEFE
autonumber

title L2: Calculate Employee Salary

actor "HR Manager" as HRM
participant "PayrollRun" as RUN
participant "Salary Calculator" as CALC
database "Employee" as EMP
database "BudgetAllocation" as BUD
participant "Payment Service" as PAY

HRM -> RUN : approvePayrollList(runId)
RUN -> EMP : loadEmployee(employeeId)
EMP --> RUN : Employee
RUN -> CALC : calculateSalary(employee, period)
loop for each payroll line
  CALC -> EMP : loadAttendance(employeeId, period)
  EMP --> CALC : Attendance
  CALC -> BUD : BudgetAllocation.checkBudget(allocationId, netAmount)
  BUD --> CALC : BudgetDecision
  CALC --> RUN : PayrollLine
end
RUN -> PAY : postPayment(paymentCommand)
PAY --> RUN : PaymentResult
RUN --> HRM : PayrollRun status

alt calculation failed
  RUN -> RUN : recordFailure()
  RUN --> HRM : Failed
else calculation succeeded
  RUN --> HRM : Approved
end

@enduml
```

**Explanation:** The loop runs to produce a `PayrollLine` for each employee, and `calculateSalary()` combines attendance and budget data. The `alt` branch separates calculation failure from the successful path. `postPayment()` is called after approval is executed, and the result is returned to `HRManager`. This scenario is directly related to DFD-L3.1 and BPMN-L3 Payroll Approval.

### 2.3 Level 3 — Concurrency, Asynchronous Messages, and Error Handling

```plantuml
@startuml ARCH-L3-Sequence-Critical
skinparam backgroundColor #FEFEFE
autonumber

title L3: Parallel Payroll, Budget and Audit Processing

actor "Finance Manager" as FIN
participant "Payroll API" as API
participant "PayrollRun" as RUN
participant "Salary Calculator" as CALC
participant "Budget Validator" as BUD
participant "Payment Service" as PAY
participant "Audit Logger" as AUDIT
queue "Retry Queue" as QUEUE

FIN -> API : approveRun(runId)
API -> RUN : approve()
par calculate lines
  RUN -> CALC : calculateSalary(employee, period)
  CALC --> RUN : PayrollLine
else validate budget
  RUN -> BUD : BudgetAllocation.checkBudget(allocationId, amount)
  BUD --> RUN : BudgetDecision
end
RUN -> AUDIT : append(CalculationAudit)
AUDIT --> RUN : Ack
RUN -> PAY : postPayment(paymentCommand)
PAY -> PAY : PaymentGateway.executePayment()
alt payment success
  PAY --> RUN : PaymentConfirmed
  RUN -> AUDIT : append(PaymentAudit)
else timeout or failure
  PAY --> RUN : PaymentFailed
  RUN -> QUEUE : enqueueRetry(paymentCommand)
  RUN --> FIN : RetryScheduled
end
RUN --> API : PayrollRun status
API --> FIN : status

group exception handling
  RUN -> AUDIT : append(ErrorAudit)
  AUDIT --> RUN : Ack
end

@enduml
```

**Explanation:** `par` shows line calculation and budget validation running concurrently; payment occurs after both branches complete. The audit message is synchronous, while the retry message is sent asynchronously to the queue. A gateway error causes `ErrorAudit` to be recorded and a retry to be scheduled. This level is consistent with the Level 3 Interaction Overview and Timing Diagram.

---

## 3. Communication Diagrams — Type 12

### 3.1 Level 1 — Object Communication in the Overall Architecture

```plantuml
@startuml ARCH-L1-Communication
skinparam backgroundColor #FEFEFE

title L1: Object Communication Overview

object "ExecutiveAnalyst" as EXEC
object "ReportAPI" as API
object "ReportEngine" as ENGINE
object "ReportingDB" as DB
object "Report" as REPORT

EXEC --> API : requestReport
API --> ENGINE : ReportEngine.generateReport()
ENGINE --> DB : readFacts
DB --> ENGINE : dataset
ENGINE --> REPORT : create
REPORT --> EXEC : deliver

@enduml
```

**Explanation:** Level 1 communication shows the analyst, API, report engine, database, and report object. Each link represents a semantic collaboration, and message numbering becomes precise at later levels. This view corresponds to the `Generate Analytical Reports` use case and DFD-L2.6.

### 3.2 Level 2 — Intermediate Process Messages

```plantuml
@startuml ARCH-L2-Communication
skinparam backgroundColor #FEFEFE

title L2: Purchase Request Communication

object "ProcurementOfficer" as PROC
object "PurchaseRequest" as PR
object "BudgetAllocation" as BUD
object "FinanceManager" as FIN
object "PurchaseOrder" as PO
object "AuditLog" as AUDIT

PROC --> PR : 1: submit()
PR --> BUD : 2: BudgetAllocation.checkBudget()
BUD --> FIN : 3: decision
FIN --> PR : 4: approve()
PR --> PO : 5: issue()
PR --> AUDIT : 6: log()
PO --> PROC : 7: notify()

@enduml
```

**Explanation:** Message numbers define the collaboration order from request creation through purchase-order issuance. `BudgetAllocation.checkBudget()` is performed before approval, and `AuditLog` is recorded after the final decision. This order matches DFD-L3.2 and the Level 2 Activity diagram.

### 3.3 Level 3 — Detailed Message Numbering

```plantuml
@startuml ARCH-L3-Communication
skinparam backgroundColor #FEFEFE

title L3: Detailed Message Numbering — Payroll

object "HRManager" as HRM
object "PayrollRun" as RUN
object "SalaryCalculator" as CALC
object "EmployeeStore" as EMP
object "BudgetAllocation" as BUD
object "PaymentService" as PAY
object "AuditLog" as AUDIT

HRM --> RUN : 1.1: approveRun(runId)
RUN --> EMP : 1.2: loadEmployee(employeeId)
EMP --> RUN : 1.3: Employee
RUN --> CALC : 2.1: calculateSalary(employee, period)
CALC --> EMP : 2.2: loadAttendance(employeeId, period)
EMP --> CALC : 2.3: Attendance
CALC --> BUD : 2.4: BudgetAllocation.checkBudget(allocationId, amount)
BUD --> CALC : 2.5: BudgetDecision
CALC --> RUN : 2.6: PayrollLine
RUN --> PAY : 3.1: postPayment(paymentCommand)
PAY --> RUN : 3.2: PaymentResult
RUN --> AUDIT : 4.1: append(AuditEvent)
AUDIT --> RUN : 4.2: Ack
RUN --> HRM : 5.1: PayrollRun status

note right of AUDIT
  Exception path: calculation failed
end note
RUN --> AUDIT : 6.1: append(ErrorAudit)
AUDIT --> RUN : 6.2: Ack

note right of RUN
  Exception path: payment failed
end note
RUN --> AUDIT : 6.3: append(PaymentError)
RUN --> RUN : 6.4: enqueueRetry()

@enduml
```

**Explanation:** Decimal message numbers show the order of peer and nested calls. Payroll calculation, budget validation, payment, and auditing are coordinated in a critical scenario. The separately labeled exception paths record `ErrorAudit` or `PaymentError` and schedule a retry with `enqueueRetry()`. This diagram aligns with the Level 3 Sequence and Timing diagrams.

---

## 4. Interaction Rules

| ID | Rule | Consequence of Violation |
|---|---|---|
| INT-01 | `calculateSalary()` must complete before `postPayment()` | Payment is not executed and `PayrollRun` fails |
| INT-02 | `BudgetAllocation.checkBudget()` must complete before reservation and PO issuance | `PurchaseRequest` is not approved |
| INT-03 | `StockLot.allocate()` / `allocateStock()` must be called only after a valid `GoodsReceipt` | Allocation is rejected and `StockShortageException` is recorded |
| INT-04 | All decision and payment messages must produce an `AuditLog` | The operation is incomplete from an audit perspective |
| INT-05 | Retry messages must have a correlation ID and an attempt limit | Duplicate requests or an infinite loop may occur |

## 5. Traceability

| Interaction | DFD | BPMN | UML Class / Method |
|---|---|---|---|
| Generate Report | DFD-L2.6 | BPMN-L2 Reporting | `ReportEngine.generateReport()` |
| Calculate Salary | DFD-L2.2 / L3.1 | BPMN-L3 Payroll Approval | `PayrollRun.calculateSalary()` |
| Check Budget PR | DFD-L2.3 / L3.2 | BPMN-L3 Budget Check PR | `BudgetAllocation.checkBudget()` |
| Allocate Stock | DFD-L2.5 / L3.3 | BPMN-L3 Stock Allocation | `StockLot.allocate()` / `allocateStock()` |

*End of Sequence and Communication document*
