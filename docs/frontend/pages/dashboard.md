# Dashboard Page

## Overview
The Dashboard is the main landing page for authenticated users, providing a comprehensive overview of the BedaanWaves platform's capabilities and real-time market data.

## Key Features
- **Market Overview**: Displays current market indices, top gainers/losers, and most active stocks
- **Quick Access**: One-click access to analysis tools, portfolio management, and watchlist
- **Recent Activity**: Shows recent news, price changes, and ML predictions
- **Customization**: Users can customize which widgets are displayed and their arrangement

## Navigation
- Access via: `/dashboard` (protected route)
- Authentication required: Yes (JWT Bearer token)
- Role-based access: Standard users see basic dashboard, admins see full analytics

## Widgets
1. **Market Summary**: Real-time price data for NASDAQ and crypto markets
2. **Portfolio Performance**: Quick view of user's portfolio value and daily changes
3. **Latest News**: Aggregated market news with sentiment indicators
4. **ML Predictions**: Top 5 stocks with AI predictions for the day
5. **Watchlist**: User-defined stock watchlist with price alerts

## Technical Details
- Built with Next.js 16+ App Router
- Data fetched via API routes: `/api/v1/market`, `/api/v1/portfolio`, `/api/v1/news`
- Real-time updates using WebSocket connections
- Cached responses for improved performance