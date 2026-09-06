"""API Routes Package"""

from .routes import (
    analysis,
    auth,
    health,
    history,
    live,
    market,
    ml,
    news,
    notifications,
    portfolios,
    specialized,
    stocks,
    symbols,
    system,
    users,
    watchlists,
)

# Export routers with explicit names
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
live_router = live.router
health_router = health.router

# Export router references
__all__ = [
    "analysis",
    "analysis_router",
    "auth",
    "auth_router",
    "health",
    "health_router",
    "history",
    "history_router",
    "live",
    "live_router",
    "market",
    "market_router",
    "ml",
    "ml_router",
    "news",
    "news_router",
    "notifications",
    "notifications_router",
    "portfolio_router",
    "portfolios",
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
