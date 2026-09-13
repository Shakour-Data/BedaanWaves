# BPMN 2.0 — Integrated HR, Finance & Procurement Management System

**Title:** Integrated HR, Finance & Procurement Management System
**Version:** v1.0
**Date:** 2026-09-09
**Format:** PlantUML Activity Notation with BPMN-style labels

---

## 1. Introduction and Modeling Scale

This document models the system's business processes at three abstraction levels. PlantUML Activity Notation is used to represent pools, lanes, activities, gateways, and events. For direct execution in Camunda or Flowable, the model must be converted to BPMN 2.0 XML and extended with Data Objects, Signals, Timers, and Error Events.

| Level | Purpose | Output |
|---|---|---|
| 1 | High-level process view and actor relationships | Process overview with pools and lanes |
| 2 | Executable process for each domain | Six independent process diagrams |
| 3 | Operational tasks and critical exceptions | Payroll approval, purchase-request budget check, and stock allocation |

Shared names across DFD and UML are `Employee`, `PayrollRun`, `PayrollLine`, `Budget`, `BudgetAllocation`, `PurchaseRequest`, `PurchaseOrder`, `Product`, `StockLot`, `GoodsReceipt`, `Payment`, `Report`, and `AuditLog`.

---

## 2. Level 1 — Process Overview

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

### Level-1 Happy Path Table

| Step | Actor / Lane | Activity | Output |
|---|---|---|---|
| 1 | Employee | Submit personal data, leave, or attendance | Input event |
| 2 | HR Manager | Review and approve request | Approved personnel data |
| 3 | PayrollRun | Execute `calculateSalary()` | `PayrollRun` and `PayrollLine` |
| 4 | Finance Manager | Execute `BudgetAllocation.checkBudget()` and approve payment | `Payment` |
| 5 | Bank/Payment Gateway | Execute payment | Transaction confirmation |
| 6 | Procurement Officer | Create PR and issue PO | `PurchaseOrder` |
| 7 | Supplier / Warehouse Officer | Ship goods and record receipt | `GoodsReceipt` and `StockLot` |
| 8 | Executive/Analyst | Execute `ReportEngine.generateReport()` | `Report` |

### Level-1 Exception Flow Table

| Code | Actor / Lane | Exception Event | Process Response |
|---|---|---|---|
| EX-L1-01 | Employee | Incomplete or invalid data | Return for correction and record `AuditLog` |
| EX-L1-02 | HR Manager | Request not approved | Reject request and notify Employee |
| EX-L1-03 | PayrollRun | `calculateSalary()` error | Stop execution, record error, and notify HR |
| EX-L1-04 | Finance Manager | Insufficient `BudgetAllocation` | Defer/reject and request reallocation |
| EX-L1-05 | Bank/Payment Gateway | Transaction error | Intermediate Error and bounded retry |
| EX-L1-06 | Warehouse Officer | Goods discrepancy against PO | Create `DiscrepancyReport` and stop allocation |
| EX-L1-07 | Executive/Analyst | Incomplete report data | Request data completion and record quality event |

---

## 3. Level 2 — Domain Processes

### 3.1 HR — Recruitment, Transfer, and Leave

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

**Happy Path:** Employee submits the request, HR Manager reviews the documents or leave balance, the request is approved, the `Employee` record is updated, and `AuditLog` is recorded.
**Exception Flow:** Documents are incomplete, leave balance is insufficient, or the manager rejects the request; the system returns it for correction or records a final rejection.

### 3.2 Payroll — Calculation, Approval, and Payment

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

**Happy Path:** The list is approved, `calculateSalary()` creates payroll lines, Finance Manager approves the budget, and the bank records the payment.
**Exception Flow:** A calculation error, insufficient budget, or gateway failure stops the process, records `AuditLog`, and invokes a bounded retry where applicable.

### 3.3 Budget — Planning, Allocation, and Validation

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

**Happy Path:** The annual budget is defined, credit is allocated to units, and `BudgetAllocation.checkBudget()` checks and reserves the requested amount.
**Exception Flow:** The remaining credit is lower than the request; Finance Manager sends a reallocation request to Executive/Analyst and pauses dependent operations until a decision is made.

### 3.4 Procurement — Purchase Request to Order

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

**Happy Path:** The PR is created and validated, budget is reserved, the PR is approved, the PO is issued to Supplier, and goods are received with a `GoodsReceipt`.
**Exception Flow:** An invalid line, insufficient budget, supplier rejection, or shipment discrepancy causes correction, rejection, or a `DiscrepancyReport`.

### 3.5 Inventory/Warehouse — Receipt, Stock, and Allocation

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

**Happy Path:** Goods match the PO, `StockLot` is created or updated, `StockLot.allocate()` / `allocateStock()` records the reservation, and the inventory report is published.
**Exception Flow:** Quantity or quality discrepancies, insufficient stock, or warehouse capacity issues create a discrepancy report, stop allocation, or trigger a warehouse-expansion request.

### 3.6 Reporting & Analytics — Management Reporting

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

**Happy Path:** Criteria are defined, domain data is extracted and validated, and `ReportEngine.generateReport()` publishes the report.
**Exception Flow:** Data is incomplete or inconsistent; Report Engine records a data-quality error and requests data completion.

### Level-2 Happy Path Table

| Domain | Happy Path | Entity / Method |
|---|---|---|
| HR | Approve request and update Employee | `Employee`, `approveRequest()` |
| Payroll | Calculate, approve budget, and pay | `PayrollRun`, `calculateSalary()`, `BudgetAllocation.checkBudget()` |
| Budget | Allocate and reserve credit | `BudgetAllocation`, `reserve()` |
| Procurement | PR to PO to Supplier | `PurchaseRequest`, `PurchaseOrder` |
| Inventory | Receipt to StockLot to allocation | `GoodsReceipt`, `StockLot`, `allocateStock()` |
| Reporting | Extract, validate, and report | `Report`, `ReportEngine.generateReport()` |

### Level-2 Exception Flow Table

| Domain | Exception | Response |
|---|---|---|
| HR | Incomplete documents or insufficient leave balance | Correct or reject and notify |
| Payroll | Calculation or payment error | `AuditLog`, stop, and bounded retry |
| Budget | Insufficient remaining credit | Request reallocation |
| Procurement | Invalid PR or rejected PO | Return for correction or cancel |
| Inventory | Receipt discrepancy or stock shortage | `DiscrepancyReport` and stop allocation |
| Reporting | Low-quality data | `DataQualityException` and request completion |

---

## 4. Level 3 — Critical Sub-processes

### 4.1 Payroll Payment Approval

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

#### L3 Payroll Happy Path Table

| Step | Role | Activity | Entity / Method |
|---|---|---|---|
| 1 | HR Manager | Review and digitally sign list | `Employee` |
| 2 | PayrollRun | Calculate salary | `calculateSalary()` |
| 3 | PayrollRun | Generate salary slip | `PayrollLine` |
| 4 | Finance Manager | Check budget | `BudgetAllocation.checkBudget()` |
| 5 | Finance Manager | Create payment | `Payment` |
| 6 | Bank Gateway | Confirm transaction | `Payment.status = Paid` |

#### L3 Payroll Exception Flow Table

| Code | Location | Error | Response |
|---|---|---|---|
| EX-P01 | PayrollRun | `CalculationException` | Stop, record `AuditLog`, and notify HR |
| EX-P02 | Finance Manager | Insufficient budget | Reject/defer and request reallocation |
| EX-P03 | Bank Gateway | `PaymentFailedException` | Retry after 5 minutes, maximum 3 attempts |

### 4.2 Purchase-Request Budget Check

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

#### L3 Budget Check Happy Path Table

| Step | Role | Activity | Entity / Method |
|---|---|---|---|
| 1 | Procurement Officer | Create PR | `PurchaseRequest` |
| 2 | Finance Manager | Check budget | `BudgetAllocation.checkBudget()` |
| 3 | Finance Manager | Reserve credit | `BudgetAllocation.reserve()` |
| 4 | Finance Manager | Approve and issue PO | `PurchaseOrder` |
| 5 | Supplier | Acknowledge order | `PurchaseOrder.acknowledge()` |

#### L3 Budget Check Exception Flow Table

| Code | Location | Error | Response |
|---|---|---|---|
| EX-B01 | Finance Manager | Insufficient budget without reallocation | Reject PR and notify |
| EX-B02 | Executive/Analyst | Reallocation rejected | Stop and record `AuditLog` |
| EX-B03 | Finance Manager | Budget still insufficient after reallocation | Reject PR finally |

### 4.3 Stock Allocation to Requester

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

#### L3 Stock Allocation Happy Path Table

| Step | Role | Activity | Entity / Method |
|---|---|---|---|
| 1 | Warehouse Officer | Receive and inspect goods | `GoodsReceipt` |
| 2 | Warehouse Officer | Select eligible lot | `StockLot` |
| 3 | Warehouse Officer | Reserve quantity | `StockLot.allocate()` / `allocateStock()` |
| 4 | Warehouse Officer | Update inventory | `StockLot.availableQuantity` |
| 5 | Procurement Officer | Receive notice | `PurchaseRequest` if required |

#### L3 Stock Allocation Exception Flow Table

| Code | Location | Error | Response |
|---|---|---|---|
| EX-S01 | Warehouse Officer | Insufficient quantity | `StockShortageException` and purchase notice |
| EX-S02 | Warehouse Officer | Warehouse capacity reached | `OverflowAlert` to Executive/Analyst |
| EX-S03 | Warehouse Officer | Physical receipt discrepancy | `DiscrepancyReport` and stop allocation |

---

## 5. Traceability to DFD and UML

| BPMN ID | Activity | DFD | UML |
|---|---|---|---|
| BPMN-HR-01 | Approve HR request | DFD-L2.1 | `Employee`, `approveRequest()` |
| BPMN-PAY-01 | Calculate salary | DFD-L2.2 / DFD-L3.1 | `PayrollRun.calculateSalary()` |
| BPMN-PAY-02 | Post payment | DFD-L2.2 | `Payment.postPayment()` |
| BPMN-BUD-01 | Check budget | DFD-L2.3 / DFD-L3.2 | `BudgetAllocation.checkBudget()` |
| BPMN-PROC-01 | Create and approve PR | DFD-L2.4 / DFD-L3.2 | `PurchaseRequest.submit()` / `approve()` |
| BPMN-PROC-02 | Issue PurchaseOrder | DFD-L2.4 | `PurchaseOrder.issue()` |
| BPMN-INV-01 | Allocate stock | DFD-L2.5 / DFD-L3.3 | `StockLot.allocate()` / `allocateStock()` |
| BPMN-INV-02 | Record GoodsReceipt | DFD-L2.5 | `GoodsReceipt` |
| BPMN-REP-01 | Generate report | DFD-L2.6 | `ReportEngine.generateReport()` |

## 6. Process Rules

1. No `Payment` is created without an approved `PayrollRun` and a successful `BudgetAllocation.checkBudget()` result.
2. No `PurchaseOrder` is issued without an approved `PurchaseRequest` and a budget reservation.
3. No `StockLot` is created without a valid `GoodsReceipt` that matches a `PurchaseOrder`.
4. Every approval, rejection, reservation, payment, and allocation decision must create an `AuditLog` event.
5. Retryable errors run only within a defined attempt limit and record an error event.

*End of BPMN document*
