"""API Routes Package"""

from . import (
    analysis,
    auth,
    compare,
    dashboard,
    data_health,
    filter,
    health,
    history,
    live,
    live_sse,
    market,
    market_data,
    ml,
    news,
    notifications,
    observability,
    password_reset,
    portfolios,
    privacy,
    ranking,
    security_audit,
    settings,
    specialized,
    stocks,
    symbols,
    system,
    users,
    watchlists,
)

# Export routers with explicit names for main.py compatibility
analysis_router = analysis.router
auth_router = auth.router
compare_router = compare.router
dashboard_router = dashboard.router
data_health_router = data_health.router
filter_router = filter.router
health_router = health.router
history_router = history.router
live_router = live.router
live_sse_router = live_sse.router
market_data_router = market_data.router
market_router = market.router
ml_router = ml.router
news_router = news.router
notifications_router = notifications.router
observability_router = observability.router
password_reset_router = password_reset.router
portfolio_router = portfolios.router
privacy_router = privacy.router
ranking_router = ranking.router
security_audit_router = security_audit.router
settings_router = settings.router
specialized_router = specialized.router
stocks_router = stocks.router
symbols_router = symbols.router
system_router = system.router
users_router = users.router
watchlists_router = watchlists.router

__all__ = [
    "alerts",
    "alerts_router",
    "analysis",
    "analysis_router",
    "auth",
    "auth_router",
    "compare",
    "compare_router",
    "dashboard",
    "dashboard_router",
    "data_health",
    "data_health_router",
    "filter",
    "filter_router",
    "forecast",
    "forecast_router",
    "health",
    "health_router",
    "history",
    "history_router",
    "live",
    "live_router",
    "live_sse",
    "live_sse_router",
    "market",
    "market_data",
    "market_data_router",
    "market_router",
    "ml",
    "ml_router",
    "news",
    "news_router",
    "notifications",
    "notifications_router",
    "observability",
    "observability_router",
    "password_reset",
    "password_reset_router",
    "portfolio_router",
    "portfolios",
    "privacy_router",
    "privacy",
    "ranking",
    "ranking_router",
    "security_audit",
    "security_audit_router",
    "settings",
    "settings_router",
    "specialized",
    "specialized_router",
    "stocks",
    "stocks_router",
    "symbols",
    "symbols_router",
    "system",
    "system_router",
    "users",
    "users_router",
    "watchlists",
    "watchlists_router",
]
