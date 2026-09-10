# UML 2.5 Structural Diagrams — Package, Composite Structure & Profile (HR/Finance/Procurement)

**Title:** UML 2.5 Structural Diagrams — Package, Composite Structure & Profile
**Scope:** Integrated HR, Finance, and Procurement system
**Version:** v1.0
**Date:** 2026-09-09
**Status:** Draft for documentation
**Author:** Kilo

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Package Diagram (Type 5)](#2-package-diagram-type-5)
3. [Composite Structure Diagram (Type 6)](#3-composite-structure-diagram-type-6)
4. [Profile Diagram (Type 7)](#4-profile-diagram-type-7)
5. [Traceability](#5-traceability)
6. [Naming Conventions](#6-naming-conventions)
7. [Rules and Limitations](#7-rules-and-limitations)

---

## 1. Introduction

This document models three UML 2.5 structural diagram types for the Package, Composite Structure, and Profile layers of the integrated HR/Finance/Procurement system.

### 1.1 Modeling Scale

| Level | Scope | Output |
|-------|-------|--------|
| **Level 1** | Overview of packages / collaborations / profiles | Basic diagrams |
| **Level 2** | Sub-package breakdown / internal parts / primary stereotypes | Medium diagrams |
| **Level 3** | Class details, ports, connectors, and constraints (OCL) | Detailed diagrams |

### 1.2 Fixed Scope

| English Name | Persian Description |
|-------------|-------------------|
| `Employee` | Employee |
| `HRManager` | HR Manager |
| `PayrollRun` | Payroll run |
| `Budget` | Overall budget |
| `BudgetAllocation` | Budget allocation to a department |
| `PurchaseRequest` | Purchase request |
| `PurchaseOrder` | Purchase order |
| `GoodsReceipt` | Goods receipt |
| `StockLot` | Stock lot |
| `Payment` | Payment |
| `Report` | Report |
| `AuditLog` | Audit log |
| `WarehouseOfficer` | Warehouse officer |
| `FinanceManager` | Finance manager |
| `ProcurementOfficer` | Procurement officer |
| `ExecutiveAnalyst` | Executive analyst |
| `Supplier` | Supplier |
| `BankGateway` | Payment gateway |