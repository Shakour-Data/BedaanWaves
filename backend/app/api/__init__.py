"""API Routes Package"""

from .routes import (
    market,
    analysis,
    stocks,
    portfolios,
    history,
    news,
    auth,
    ml,
    live,
    users,
    watchlists,
    notifications,
    system,
    crypto,
    specialized,
    health,
)

# Export routers with explicit names
health_router = health.router

# Export router references
__all__ = [
    "market", "analysis", "stocks", "portfolios", "history", "news",
    "auth", "ml", "live", "users", "watchlists", "notifications",
    "system", "crypto", "specialized", "health",
    "auth_router", "stocks_router", "market_router", "analysis_router",
    "portfolio_router", "history_router", "news_router", "ml_router",
    "users_router", "watchlists_router", "notifications_router",
    "specialized_router", "system_router", "crypto_router",
    "health_router"
]