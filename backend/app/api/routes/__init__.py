"""API Routes Package"""

from . import (
    analysis,
    auth,
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
    password_reset,
    portfolios,
    ranking,
    settings,
    specialized,
    stocks,
    symbols,
    system,
    tse,
    users,
    watchlists,
)

# Export routers with explicit names for main.py compatibility
auth_router = auth.router
stocks_router = stocks.router
market_router = market.router
analysis_router = analysis.router
portfolio_router = portfolios.router
history_router = history.router
news_router = news.router
ml_router = ml.router
users_router = users.router
watchlists_router = watchlists.router
notifications_router = notifications.router
specialized_router = specialized.router
system_router = system.router
symbols_router = symbols.router
tse_router = tse.router
live_router = live.router
live_sse_router = live_sse.router
health_router = health.router
settings_router = settings.router
ranking_router = ranking.router
password_reset_router = password_reset.router
market_data_router = market_data.router
data_health_router = data_health.router
dashboard_router = dashboard.router
filter_router = filter.router

__all__ = [
    "analysis",
    "analysis_router",
    "auth",
    "auth_router",
    "dashboard",
    "dashboard_router",
    "data_health",
    "data_health_router",
    "filter",
    "filter_router",
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
    "password_reset",
    "password_reset_router",
    "portfolio_router",
    "portfolios",
    "ranking",
    "ranking_router",
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
    "tse",
    "tse_router",
    "users",
    "users_router",
    "watchlists",
    "watchlists_router",
]
