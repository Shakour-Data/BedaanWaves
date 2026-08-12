# Portfolio Page

## Overview
The Portfolio page enables users to manage their investment portfolios, track performance, and execute rebalancing operations.

## Key Features
- **Portfolio Overview**: Total value, daily P&L, asset allocation breakdown
- **Holdings Management**: Add/remove positions, adjust quantities
- **Performance Analytics**: Time-weighted returns, benchmark comparison
- **Risk Metrics**: Portfolio VaR, correlation matrix, concentration risk
- **Rebalancing**: Automated and manual rebalancing with tax optimization
- **Transaction History**: Complete audit trail of all trades

## Navigation
- Access via: `/portfolio` (protected route)
- Tabs: Overview, Holdings, Performance, Risk, Transactions
- Quick actions: Deposit, Withdraw, Rebalance

## Technical Details
- Real-time valuation updates via WebSocket
- Tax-lot accounting for accurate P&L
- Support for multi-currency portfolios
- Integration with crypto and traditional assets
- Export to CSV/PDF for reporting

## API Integration
- `/api/v1/portfolio` - CRUD operations
- `/api/v1/portfolio/value` - Real-time valuation
- `/api/v1/portfolio/risk` - Risk metrics
- `/api/v1/portfolio/rebalance` - Rebalancing suggestions