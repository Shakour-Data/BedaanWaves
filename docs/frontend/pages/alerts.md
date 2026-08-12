# Alerts Page

## Overview
The Alerts page enables users to set up price alerts, technical signal alerts, and portfolio notifications with multi-channel delivery.

## Key Features
- **Price Alerts**: Trigger when stock/crypto reaches specified price
- **Technical Signal Alerts**: Trigger when indicators cross thresholds (RSI, MACD, etc.)
- **Portfolio Alerts**: Portfolio value changes, rebalancing needed
- **News Sentiment Alerts**: Significant market news with sentiment shift
- **Multi-Channel Delivery**: Email, push notification, SMS (when configured)
- **Alert History**: Complete log of triggered alerts with timestamps

## Alert Types
1. **Price Above/Below**: Custom price level triggers
2. **Technical Indicators**: RSI overbought/oversold, MACD crossover, Bollinger Band touches
3. **Volume Alerts**: Unusual volume spikes
4. **News Sentiment**: Significant sentiment shifts in market news
5. **Portfolio Metrics**: Value changes, target achievement

## Management
- Create/Edit/Delete alerts
- Enable/Disable alerts
- View alert triggers and history
- Bulk operations on similar alerts
- Priority ordering for notification delivery

## Navigation
- Access via: `/alerts` (protected route)
- Dashboard view: Active, Triggered, and Dismissed alerts
- Quick create: One-click alert from stock detail page
- Edit triggers: Adjust thresholds without deleting

## Technical Details
- Backend-triggered via scheduled jobs
- Rate limiting on alert creation (10 per user per hour)
- Persistence in database with timestamps
- Notification throttling to prevent spam
- Cross-user isolation for privacy

## API Integration
- `/api/v1/alerts` - CRUD operations for alerts
- `/api/v1/alerts/triggered` - Recently triggered alerts
- `/api/v1/alerts/{id}` - Individual alert management

## User Controls
- Adjust notification frequency
- Set quiet hours for non-essential alerts
- Choose preferred delivery channels
- Global enable/disable for all alerts