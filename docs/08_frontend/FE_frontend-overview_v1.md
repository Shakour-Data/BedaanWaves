# BedaanWaves - Frontend Documentation

## Overview
This document covers the frontend components of BedaanWaves, including the user interface, design system, navigation, and state management architecture.

## Key Frontend Components

### NavigationSystem
Intuitive tabbed navigation with multilingual support (Persian/English).

**Features:**
- Responsive design for all screen sizes
- Dynamic routing
- Search integration
- Quick access tabs

### DarkMode
Smart dark/light theme toggle with system preference detection.

**Features:**
- Automatic theme switching
- Color contrast compliance
- Smooth transition animation

### UI Components
- Interactive dashboards with time-series visualization
- Custom financial charts
- Wizard forms for registration
- Notification carousel

## Design System

```mermaid
graph LR
    A[Typography] --> B[Buttons]
    A --> C[Icons]
    A --> D[Forms]
    B --> E[Appearance States]

## Configuration
- Dark mode preference (default: system setting)
- Font family (custom + system)
- Breakpoint settings (mobile/desktop)

## Integration
- Connected to: AuthService, NotificationService
- API Clients: Stocks, Portfolio, ML Services
- Local Storage: User preferences, session data