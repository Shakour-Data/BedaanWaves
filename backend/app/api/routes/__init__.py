"""API Routes Package"""

from . import (
    market,
    analysis,
    stocks,
    portfolios,
    history,
    news,
    auth,
    ml,
    live,
    live_sse,
    users,
    watchlists,
    notifications,
    system,
    crypto,
    specialized,
    health,
    symbols,
    intl,
    settings,
    ranking,
    password_reset,
    market_data,
    data_health,
    dashboard,
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
crypto_router = crypto.router
symbols_router = symbols.router
intl_router = intl.router
live_router = live.router
live_sse_router = live_sse.router
health_router = health.router
settings_router = settings.router
ranking_router = ranking.router
password_reset_router = password_reset.router
market_data_router = market_data.router
data_health_router = data_health.router
dashboard_router = dashboard.router

__all__ = [
    "market", "analysis", "stocks", "portfolios", "history", "news",
    "auth", "ml", "live", "live_sse", "users", "watchlists", "notifications",
    "system", "crypto", "specialized", "health", "symbols", "intl", "settings", "ranking", "password_reset",
    "market_data", "data_health", "dashboard",
    "auth_router", "stocks_router", "market_router", "analysis_router",
    "portfolio_router", "history_router", "news_router", "ml_router",
    "users_router", "watchlists_router", "notifications_router",
    "specialized_router", "system_router", "crypto_router",
    "symbols_router", "intl_router", "live_router", "live_sse_router", "health_router",
    "settings_router", "ranking_router", "password_reset_router",
    "market_data_router", "data_health_router", "dashboard_router",
    # Module references
    "market", "analysis", "stocks", "portfolios", "history", "news",
    "auth", "ml", "live", "live_sse", "users", "watchlists", "notifications",
    "system", "crypto", "specialized", "health", "symbols", "intl",
    "ranking", "password_reset", "market_data", "data_health", "dashboard",
]
