# FrontEnd Display Documentation

## Overview
Detailed documentation of all frontend pages, components, and user interfaces in the BedaanWaves platform.

## Page Documentation
Each frontend page has dedicated documentation covering:

1. [Dashboard Page](pages/dashboard.md)
   - Real-time market overview
   - Portfolio performance summary
   - Latest news and ML predictions
   - Customizable widget layout

2. [Registration Page](pages/register.md)
   - Account creation flow
   - Email verification process
   - Password security requirements
   - Terms & conditions acceptance

3. [Login Page](pages/login.md)
   - JWT-based authentication
   - Session management
   - Multi-factor authentication support
   - Password reset functionality

4. [Stock Page](pages/stock.md)
   - Real-time stock quotes
   - Interactive charting with technical indicators
   - Fundamental data display
   - Trading controls and watchlist integration

5. [Portfolio Page](pages/portfolio.md)
   - Asset allocation visualization
   - Performance tracking
   - Transaction history
   - Rebalancing recommendations

6. [News Page](pages/news.md)
   - Market news aggregation
   - Sentiment analysis integration
   - Filtering by sector and importance
   - Search and bookmarking

7. [Analysis Page](pages/analysis.md)
   - Technical analysis tools
   - Fundamental ratio analysis
   - Risk metrics dashboard
   - Exportable reports

8. [Alerts Page](pages/alerts.md)
   - Price alert configuration
   - Notification preferences
   - Alert history
   - Bulk management

9. [Scoring Page](pages/scoring.md)
   - 6D scoring visualization
   - 305-node hierarchy display
   - Filtering and sorting
   - Detailed score breakdown

10. [Settings Page](pages/settings.md)
    - User profile management
    - Notification preferences
    - Theme customization
    - Market data selections

11. [Methodology Page](pages/methodology.md)
    - Scoring methodology explanation
    - Technical indicator descriptions
    - Risk model documentation
    - ML model transparency

12. [Watchlist Page](pages/watchlist.md)
    - Custom watchlist management
    - Real-time updates
    - Price alerts
    - Performance metrics

## Frontend Technologies
- Framework: Next.js 16+ (App Router)
- Styling: Tailwind CSS with custom design system
- State Management: React Context + custom hooks
- API Integration: SWR for data fetching
- Charting: TradingView Lightweight Charts
- Authentication: JWT tokens + HttpOnly cookies
- Testing: Jest + React Testing Library
- Type Checking: TypeScript strict mode

## Component Architecture
- Shared components: UI library (buttons, forms, modals)
- Layout components: Header, sidebar, grid system
- Feature components: Charts, tables, cards
- Utility components: Loaders, error boundaries
