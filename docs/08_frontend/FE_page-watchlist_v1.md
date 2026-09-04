# Watchlist Page

## Overview
The Watchlist page enables users to create, manage, and monitor personalized lists of financial instruments for tracking and analysis.

## Key Features
- **Personalized Watchlists**: Create unlimited custom watchlists based on sectors, risk tolerance, or trading strategies
- **Real-Time Updates**: Live price changes, percentage movements, and volatility indicators
- **Alert System**: Price threshold monitoring with customizable notifications
- **Performance Tracking**: P&L tracking across complete watchlists and individual assets
- **Categorization**: Tag assets by industry, region, or trade strategy for grouping
- **Export Functionality**: Export watchlist data to CSV, PDF, or API format
- **Collaboration**: Share watchlists with team members or advisors
- **Historical Analysis**: Review historical performance across all assets in the watchlist

## Watchlist Management
- **Create New**: Start from template or blank slate
- **Edit Existing**: Modify name, description, and categories
- **Add Assets**: Search and add assets by symbol, name, or identifier
- **Remove Assets**: Delete from watchlist with confirmation
- **Reorder Items**: Drag-and-drop to prioritize assets in list

## Technical Details
- **Access Path**: `/watchlist` (protected route)
- **Visualization**: Grid and list views with customizable columns
- **Sortable**: Reorder via drag-and-drop interface
- **Color Coding**: Asset type indicators (stock, fund, etc.)
- **Notable Assets**: Highlight top performers and watchlist leaders
- **Synchronization**: Real-time updates across devices and platforms

## API Integration
- `/api/v1/watchlist` - CRUD operations for watchlists
- `/api/v1/watchlist/{id}/items` - Manage items within a watchlist
- `/api/v1/watchlist/search` - Search and filter watchlists
- `/api/v1/watchlist/watch` - Real-time price monitoring

## User Controls
- **Custom Alerts**: Set price thresholds for individual assets
- **Performance Thresholds**: Define % change alerts for weekly/monthly periods
- **Notification Preferences**: Choose delivery method and frequency
- **Privacy Settings**: Make watchlists public (shared) or private (personal)
- **Themes**: Dark mode and indexing preferences

## Technical Notes
- Backend-tracked via `WatchlistService` with MongoDB-backed storage
- Real-time updates via WebSocket connections
- Cache layer with 1-minute refresh interval
- Rate limiting on creation/modification operations
- Database schema supports unlimited nested categories
- Accessibility features for screen readers and keyboard navigation
- Full CRUD operations with visit history tracking