# News Page

## Overview
The News page aggregates market news from multiple sources, provides sentiment analysis, and allows users to filter and save articles.

## Key Features
- **News Aggregation**: Real-time news from 50+ sources (international markets, crypto)
- **Sentiment Analysis**: AI-powered sentiment scoring (positive/negative/neutral)
- **Filtering**: Filter by sector, asset class, importance, date range
- **Personalized Feed**: User preferences influence article ordering
- **Bookmarking**: Save articles for later reference
- **Search**: Full-text search across headlines and content

## Navigation
- Access via: `/news` (public route, recommended auth)
- Filters panel: Sector, Asset Class, Sentiment, Date Range
- Sort by: Freshness, Sentiment Score, Importance
- Trending: Top stories with highest engagement

## Technical Details
- Auto-refresh every 5 minutes
- Cached articles for 30 minutes
- Fallback to manual refresh on network issues
- Mobile-optimized card layout
- Dark/light theme support

## API Integration
- `/api/v1/news/latest` - Latest headlines
- `/api/v1/news/search` - Full-text search
- `/api/v1/news/sentiment` - Sentiment aggregation
- `/api/v1/news/filter` - Filtered results

## User Controls
- Subscribe/unsubscribe to specific sectors
- Adjust refresh frequency
- Toggle sentiment indicators
- Set news importance threshold