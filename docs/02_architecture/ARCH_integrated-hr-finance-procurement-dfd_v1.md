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

Six high-level processes cover the five requested domains plus analytical reporting.
`HR Management` supplies `Employee` and `OrganizationUnit` data to payroll and reporting.
`Payroll` uses personnel and budget data to produce `PayrollRun`, `PayrollLine`, and `Payment`.
`Budget & Credits` defines and allocates credit and checks the `BudgetAllocation` balance before purchasing or payment.
`Procurement` and `Inventory/Warehouse` connect purchase requests, orders, goods receipts, `Product`, and `StockLot`.
`Reporting & Analytics` reads domain data, creates `Report`, and delivers outputs to `ExecutiveAnalyst` and `Auditor`.

---

## Level 2 — Process Decomposition

### DFD-L2.1 — Human Resources Management

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

This diagram separates recruitment, personnel-file maintenance, organization-unit management, and employment-change approval.
The `Employee` input includes applications and profile data, while `HRManager` records hiring, transfer, or termination decisions.
`D1 Employee` is the persistent personnel record and `D2 OrganizationUnit` is the organizational hierarchy.
Every status and structure change creates an event in `D14 AuditLog`.
Approved outputs are sent to payroll so eligibility and calculation data remain current.

### DFD-L2.2 — Payroll

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

`PayrollRun` holds the payroll execution identifier, and `PayrollLine` holds each employee's calculation details.
The calculation process uses `Employee`, attendance, allowances, deductions, and the remaining `BudgetAllocation`.
`FinanceManager` approves the net total and available credit before the payment request is sent to the gateway.
The bank result is written to `Payment` and `AuditLog`; a gateway error activates the bounded retry path.
This decomposition maps directly to `calculateSalary()` and `postPayment()` in the Level-3 UML and BPMN models.

### DFD-L2.3 — Budget & Credits

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

The annual budget is stored in `D5 Budget`, while each unit or project share is stored in `D6 BudgetAllocation`.
Before reserving credit, `BudgetAllocation.checkBudget()` compares the requested amount with `remaining`.
A temporary reservation prevents concurrent requests from consuming the same credit.
A successful payment releases or reconciles the reservation and records `Payment`.
Insufficient credit triggers a reallocation request or rejection through the Level-3 BPMN process.

### DFD-L2.4 — Procurement

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

Before approval, `PurchaseRequest` validates line completeness, price, and product identifiers.
`BudgetAllocation` is read by `4.3 Check Budget`; when approved, the requested amount is reserved.
Only an approved request is converted into a `PurchaseOrder` and sent to `Supplier`.
The supplier response and delivery terms are connected to the order store and audit events.
This diagram aligns with DFD-L3.2 and BPMN-L3 Budget Check for Purchase Request.

### DFD-L2.5 — Inventory & Warehouse

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
P51 -->|receipt audit| D14
P52 -->|inspection audit| D14
P53 -->|lot audit| D14
P54 -->|allocation audit| D14
```

The physical receipt is reconciled with the ordered quantity and the supplier packing list.
Accepted goods become a `GoodsReceipt` and then a `StockLot` with location, expiry date, and quantity.
`StockLot.allocate()` / `allocateStock()` reduces available quantity and updates the lot state.
A quantity or quality discrepancy creates a discrepancy report and prevents final inventory posting.
Receipt, inspection, lot creation, and allocation events are auditable in `AuditLog`.

### DFD-L2.6 — Reporting & Analytics

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

Reporting reads the primary stores and does not modify operational domain records.
Extraction, validation, transformation, and metric calculation run in sequence so inconsistent reports are not published.
`Report` contains the period, filters, criteria, version, and generation time.
`ExecutiveAnalyst` receives the management dashboard, and `Auditor` receives audit evidence.
Data-quality and publication events are stored in `AuditLog` for traceability and report reproduction.

---

## Level 3 — Critical Atomic Processes

### DFD-L3.1 — Final Salary Calculation

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

Atomic inputs include employee ID, payroll period, employment status, and attendance data.
Gross pay is calculated as `baseSalary + allowances + approved overtime - unpaidLeave`.
Deductions include tax, insurance, and other approved deductions, and net pay must not be negative.
If credit is insufficient or a calculation rule is violated, no `PayrollLine` is persisted and the error is recorded in `AuditLog`.
The final output is a `PayrollLine` containing gross, deductions, net pay, and the rule version, aggregated into `PayrollRun`.

### DFD-L3.2 — Purchase-Request Registration and Approval

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
T4 -->|approval audit| D14
```

A request must have an active requester, at least one line, a positive amount, and a valid product.
`BudgetAllocation.checkBudget()` compares the total request with the allocation balance and creates a temporary reservation on success.
Manager approval is possible only after line validation and budget reservation; rejection releases the reservation.
Issuing a `PurchaseOrder` is atomic and persists the order number, supplier, amount, and delivery deadline.
All decisions and budget changes are recorded in `AuditLog` for auditability.

### DFD-L3.3 — Stock Allocation to Requester

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

Lot selection uses product, available quantity, expiry date, quality, and the FEFO rule.
Before reservation, the requested quantity must not exceed `StockLot.availableQuantity`.
Reservation atomically decreases `availableQuantity` and increases `reservedQuantity`, preventing concurrent allocation from creating a shortage.
Issue confirmation updates the goods receipt and audit event; a physical discrepancy stops allocation.
The final output contains the updated `StockLot`, allocated quantity, delivery location, and `AuditLog`.

---

## Traceability Matrix

| DFD ID | Process | BPMN | UML |
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

## Integrity Rules

1. Every Level-2 process must preserve the inputs and outputs of its Level-1 parent process.
2. Every change to `Employee`, `BudgetAllocation`, `PurchaseRequest`, `PurchaseOrder`, `StockLot`, or `Payment` must create an `AuditLog` event.
3. `Reporting & Analytics` may not write to operational stores and may create only `Report`.
4. No payment or purchase order is issued without credit checking and reservation.
5. No stock allocation occurs without a valid receipt and an eligible lot.

*End of DFD document*
