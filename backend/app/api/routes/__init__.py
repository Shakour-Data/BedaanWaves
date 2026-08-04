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
    users,
    watchlists,
    notifications,
    system,
    crypto,
    specialized,
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
intl_router = market.router
live_router = live.router

__all__ = [
    "market", "analysis", "stocks", "portfolios", "history", "news",
    "auth", "ml", "live", "users", "watchlists", "notifications",
    "system", "crypto", "specialized",
    "auth_router", "stocks_router", "market_router", "analysis_router",
    "portfolio_router", "history_router", "news_router", "ml_router",
    "users_router", "watchlists_router", "notifications_router",
    "specialized_router", "system_router", "crypto_router",
    "intl_router", "live_router",
    # Module references
    "market", "analysis", "stocks", "portfolios", "history", "news",
    "auth", "ml", "live", "users", "watchlists", "notifications",
    "system", "crypto", "specialized",
]