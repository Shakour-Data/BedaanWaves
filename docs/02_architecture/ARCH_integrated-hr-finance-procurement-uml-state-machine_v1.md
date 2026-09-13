# UML 2.5 State Machine Diagram — PurchaseRequest and PayrollRun

**Domain:** Integrated human resources, finance, and procurement management system  
**Version:** v1.0  
**Date:** 2026-09-09

---

## 1. Purpose and Governance

This document models the state cycles of `PurchaseRequest` and `PayrollRun` at three levels of abstraction. Event, guard, and state names are aligned with the DFD and BPMN models.

---

## 2. Level 1 — Domain Overview

### 2.1 PurchaseRequest State Machine

```plantuml
@startuml ARCH-L1-State-PurchaseRequest
hide empty_description
state "Draft" as Draft
state "Submitted" as Submitted
state "Budget Checking" as BudgetChecking
state "Approved" as Approved
state "Rejected" as Rejected
state "Ordered" as Ordered
state "Received" as Received
state "Closed" as Closed

[*] --> Draft
Draft --> Submitted : submit()
Submitted --> BudgetChecking : BudgetAllocation.checkBudget()
BudgetChecking --> Approved : budgetAvailable
BudgetChecking --> Rejected : budgetUnavailable
Approved --> Ordered : createPurchaseOrder()
Ordered --> Received : recordGoodsReceipt()
Received --> Closed : reconcile()
Rejected --> Draft : revise()
Closed --> [*]
@enduml
```

**Explanation:** A purchase request starts in Draft and, after budget checking, approval, purchase-order creation, goods receipt, and reconciliation, reaches Closed. A rejected request can be revised and returned to Draft. This cycle aligns with DFD-L2.4 and the BPMN activities in the Procurement domain.

### 2.2 PayrollRun State Machine

```plantuml
@startuml ARCH-L1-State-PayrollRun
hide empty_description
state "Scheduled" as Scheduled
state "Calculating" as Calculating
state "Pending Approval" as PendingApproval
state "Approved" as Approved
state "Payment Pending" as PaymentPending
state "Paid" as Paid
state "Failed" as Failed
state "Closed" as Closed

[*] --> Scheduled
Scheduled --> Calculating : startCalculation()
Calculating --> PendingApproval : calculationComplete
Calculating --> Failed : calculationError
PendingApproval --> Approved : approve()
PendingApproval --> Failed : reject()
Approved --> PaymentPending : PaymentGateway.executePayment()
PaymentPending --> Paid : paymentConfirmed
PaymentPending --> Failed : paymentFailed
Paid --> Closed : archive()
Failed --> Scheduled : retry()
Closed --> [*]
@enduml
```

**Explanation:** A payroll run proceeds through scheduling, calculation, approval, payment, and archival. Calculation, approval, payment, and archival errors move the run to Failed; a rejected approval also moves it to Failed, and it can be retried with renewed authorization.

---

## 3. Level 2 — Design and Subsystems

### 3.1 PurchaseRequest with Events and Guards

```plantuml
@startuml ARCH-L2-State-PurchaseRequest
hide empty_description
state "Draft" as Draft
state "Submitted" as Submitted
state "Budget Checking" as BudgetChecking
state "Manager Review" as ManagerReview
state "Approved" as Approved
state "Rejected" as Rejected
state "PO Created" as POCreated
state "Partially Received" as PartiallyReceived
state "Received" as Received
state "Reconciled" as Reconciled
state "Cancelled" as Cancelled

[*] --> Draft
Draft --> Submitted : submit [totalAmount > 0]
Submitted --> BudgetChecking : validate
BudgetChecking --> ManagerReview : available [amount <= allocation.remaining]
BudgetChecking --> Rejected : unavailable [amount > allocation.remaining]
ManagerReview --> Approved : approve
ManagerReview --> Rejected : reject [reason.isDefined]
Rejected --> Draft : revise [version < maxVersions]
Approved --> POCreated : issuePO
POCreated --> PartiallyReceived : receive [receivedQty < orderedQty]
PartiallyReceived --> Received : receive [receivedQty = orderedQty]
PartiallyReceived --> POCreated : backorder
Received --> Reconciled : match [invoice = receipt]
Reconciled --> [*]
Cancelled --> [*]
Approved --> Cancelled : cancel [beforeOrderDispatch]
@enduml
```

**Explanation:** At this level, guards control the request amount, the `BudgetAllocation` balance, the revision version, and invoice-to-receipt matching. A partial receipt enters `PartiallyReceived`, and a stock shortage can create a new order. All important transitions generate an `AuditLog` event.

### 3.2 PayrollRun with Events and Guards

```plantuml
@startuml ARCH-L2-State-PayrollRun
hide empty_description
state "Scheduled" as Scheduled
state "Loading Data" as Loading
state "Calculating" as Calculating
state "Pending Approval" as PendingApproval
state "Approved" as Approved
state "Payment Pending" as PaymentPending
state "Paid" as Paid
state "Failed" as Failed
state "Closed" as Closed

[*] --> Scheduled
Scheduled --> Loading : begin [period.isOpen]
Loading --> Calculating : dataReady [employees.count > 0]
Calculating --> PendingApproval : calculated [netPay >= 0]
Calculating --> Failed : error [ruleViolation]
PendingApproval --> Approved : approve [approver.role = FinanceManager]
PendingApproval --> Failed : reject [reason.isDefined]
Approved --> PaymentPending : post [total <= budget.remaining]
PaymentPending --> Paid : confirmed [gateway.status = Success]
PaymentPending --> Failed : failed [gateway.status = Failed]
Paid --> Closed : archive [audit persisted]
Failed --> Scheduled : retry [retryCount < maxRetries]
@enduml
```

**Explanation:** Personnel and attendance data are loaded from `Employee` and `PayrollLine`. Guards check whether the period is open, net pay is non-negative, the approver's role, and the budget balance. The `calculateSalary()` method is called during the calculation transition, and `PaymentGateway.executePayment()` is called during the payment transition.

---

## 4. Level 3 — Implementation, Composite States, and History

### 4.1 PurchaseRequest with Composite States and History

```plantuml
@startuml ARCH-L3-State-PurchaseRequest
hide empty_description
state "Draft" as Draft
state "Submitted" as Submitted
state "Validation" as Validation {
  state "Budget Check" as BudgetCheck
  state "Manager Review" as ManagerReview
  state "Compliance Check" as Compliance
  BudgetCheck --> ManagerReview : budgetOk
  ManagerReview --> Compliance : approved
  Compliance --> BudgetCheck : correctionRequired [retryCount < maxCorrections]
}
state "Approved" as Approved
state "Ordered" as Ordered
state "Receiving" as Receiving {
  state "Awaiting Supplier" as Awaiting
  state "Partial Receipt" as Partial
  state "Quality Check" as Quality
  Awaiting --> Partial : shipmentReceived
  Partial --> Quality : qtyComplete
  Quality --> Awaiting : discrepancy [retryCount < maxCorrections]
}
state "Reconciled" as Reconciled
state "Rejected" as Rejected
state H1 <<history>>
state H2 <<history>>

[*] --> Draft
Draft --> Submitted : submit()
Submitted --> Validation : validate()
Validation --> Approved : valid
Validation --> Rejected : invalid
Rejected --> H1 : revise()
H1 --> Validation
Approved --> Ordered : createPurchaseOrder()
Ordered --> Receiving : dispatchConfirmed()
Receiving --> Reconciled : receiptMatched()
Reconciled --> [*]
Receiving --> H2 : pause()
H2 --> Receiving
@enduml
```

**Explanation:** `Validation` and `Receiving` are composite states; their internal substates separate budget checking, manager approval, compliance, supplier waiting, partial receipt, and quality control. `H1` retains the last validation substate and `H2` retains the last receiving substate so processing can resume. Compliance errors and goods discrepancies trigger correction paths without losing process context.

### 4.2 PayrollRun with Composite States and History

```plantuml
@startuml ARCH-L3-State-PayrollRun
hide empty_description
state "Scheduled" as Scheduled
state "Processing" as Processing {
  state "Load Employee Data" as Load
  state "Calculate Gross" as Gross
  state "Calculate Net Pay" as Net
  state "Apply Rules" as ApplyRules
  state "Generate Slip" as Generate
  Load --> Gross : dataLoaded
  Gross --> Net : rulesApplied
  Net --> Generate : netPay >= 0
  Generate --> Load : correctionRequired [retryCount < maxCorrections]
}
state "Pending Approval" as PendingApproval
state "Approved" as Approved
state "Payment" as Payment {
  state "Create Payment" as Create
  state "Gateway Call" as Gateway
  state "Confirmation" as Confirmation
  Create --> Gateway : paymentCreated
  Gateway --> Confirmation : requestSent
  Confirmation --> Create : retryableFailure [retryCount < maxRetries]
}
state "Paid" as Paid
state "Failed" as Failed
state "Closed" as Closed
state H <<history>>

[*] --> Scheduled
Scheduled --> Processing : start()
Processing --> PendingApproval : calculationComplete
PendingApproval --> Approved : approve()
PendingApproval --> Failed : reject()
Approved --> Payment : PaymentGateway.executePayment()
Payment --> Paid : confirmed()
Paid --> Closed : archive()
Processing --> H : suspend()
H --> Processing
Failed --> Scheduled : retry()
@enduml
```

**Explanation:** `Processing` covers loading, gross-pay calculation, rule application, and slip generation. `Payment` models payment creation, gateway invocation, and confirmation. `H` enables suspension and resumption from the last substate. Retryable errors may be retried up to `maxRetries`; rule violations go directly to `Failed`.

---

## 5. Guards, Input/Output Operations, and Exceptions

| ID | State/Transition | Guard or Operation | Result and Error |
|---|---|---|---|
| ST-PR-01 | Draft → Submitted | `totalAmount > 0` and `requester.isActive` | Otherwise `ValidationException` |
| ST-PR-02 | Budget Check → Manager Review | `amount <= BudgetAllocation.remaining` | Otherwise `InsufficientBudgetException` |
| ST-PR-03 | Manager Review → Approved | `approver.authorizationLevel >= requiredLevel` | Otherwise `AuthorizationException` |
| ST-PR-04 | Receiving → Reconciled | `receivedQty = orderedQty` and `invoice.amount = receipt.amount` | Creates `DiscrepancyReport` |
| ST-PAY-01 | Processing → Pending Approval | `calculateSalary()` completes without a rule violation and `netPay >= 0` | Creates `CalculationException` |
| ST-PAY-02 | Pending Approval → Approved | `approver.role = FinanceManager` | Creates `ApprovalRejectedException` |
| ST-PAY-03 | Payment → Paid | `gateway.status = Success` | Gateway error goes to `Failed` or is retried |
| ST-PAY-04 | Paid → Closed | `AuditLog` persisted | Archival error prevents run closure |

---

## 6. Traceability to DFD and BPMN

| State Machine ID | DFD Process | BPMN Activity | UML Entity/Method |
|---|---|---|---|
| PurchaseRequest Draft/Submitted | DFD-L2.4 Procurement | Create PurchaseRequest | `PurchaseRequest.submit()` |
| Budget Check | DFD-L3.2 Purchase-Request Approval | Check Budget | `BudgetAllocation.checkBudget()` |
| Ordered/Receiving | DFD-L2.4 and DFD-L2.5 | Issue PO / Record Goods Receipt | `PurchaseOrder`, `GoodsReceipt`, `StockLot.allocate()` / `allocateStock()` |
| PayrollRun Processing | DFD-L2.2 and DFD-L3.1 | Calculate Salary | `PayrollRun.calculateSalary()` |
| PayrollRun Payment | DFD-L2.2 and DFD-L2.3 | Post Payment | `PaymentGateway.executePayment()` |
| Reconciled/Closed | DFD-L2.6 Reporting | Generate Report | `ReportEngine.generateReport()` |

---

## 7. Integrity Rules

1. Every state transition must create a traceable event in `AuditLog`.
2. No `PurchaseOrder` is issued without the `Approved` transition and budget approval.
3. No `Payment` is created without `PayrollRun` being in the `Approved` state.
4. The `Paid` and `Reconciled` states are irreversible; any compensation for a `Closed` error requires a separate administrative operation and audit event.
5. `History` restores only the last valid substate and does not allow budget approval to be bypassed.

---

*End of document*
