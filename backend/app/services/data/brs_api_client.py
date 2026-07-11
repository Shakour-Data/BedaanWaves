"""
BRS API Client - Tier 2 Data Service

Integration with Tehran Stock Exchange (بورس اوراق بهادار تهران) via BrsApi.ir.

All endpoints, parameters and field names follow the canonical reference:
    docs/BourseApi.txt  (brsapi.ir free web-service documentation)

Reference rules implemented here:
  * Base URL:  https://Api.BrsApi.ir
  * Auth:      API key passed as the `key` query parameter (NOT a Bearer header)
  * Headers:   a browser User-Agent is REQUIRED (Python/Go default UAs are blocked)
  * Format:    every endpoint returns JSON
  * Symbols:   Persian ticker names (e.g. "فملی", "خودرو")
  * Rate limit (free key): 300 requests / 5 minutes
"""

import asyncio
import time
from collections import deque
from typing import Any, Dict, List, Optional

import aiohttp

from ..core import ExternalAPIService
from app.core.config import get_settings

# Browser User-Agent is mandatory: brsapi.ir blocks the default Python/Go UA.
_BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


class RateLimiter:
    """Token-bucket style rate limiter for BrsApi.ir."""

    def __init__(
        self,
        max_daily_requests: int = 50000,
        max_window_requests: int = 300,
        window_seconds: int = 300,
    ):
        self.max_daily_requests = max_daily_requests
        self.max_window_requests = max_window_requests
        self.window_seconds = window_seconds

        self.daily_count = 0
        self.daily_reset = self._next_midnight()
        self.window_timestamps: deque[float] = deque()

    def _next_midnight(self) -> float:
        now = time.localtime()
        midnight = time.mktime(
            (now.tm_year, now.tm_mon, now.tm_mday, 0, 0, 0, 0, 0, -1)
        ) + 86400
        return midnight

    def _rotate_day(self) -> None:
        now = time.time()
        if now >= self.daily_reset:
            self.daily_count = 0
            self.daily_reset = self._next_midnight()

    def _clean_window(self) -> None:
        cutoff = time.time() - self.window_seconds
        while self.window_timestamps and self.window_timestamps[0] <= cutoff:
            self.window_timestamps.popleft()

    def acquire(self) -> None:
        self._rotate_day()
        self._clean_window()

        if self.daily_count >= self.max_daily_requests:
            wait = max(0.0, self.daily_reset - time.time())
            raise RuntimeError(
                f"BrsApi daily limit reached: {self.max_daily_requests} requests/day. "
                f"Wait {wait/60:.1f} minutes until midnight."
            )

        if len(self.window_timestamps) >= self.max_window_requests:
            oldest = self.window_timestamps[0]
            wait = self.window_seconds - (time.time() - oldest)
            raise RuntimeError(
                f"BrsApi short-term limit reached: {self.max_window_requests} requests "
                f"per {self.window_seconds}s. Wait {wait:.1f} seconds."
            )

        now = time.time()
        self.window_timestamps.append(now)
        self.daily_count += 1

    def status(self) -> Dict[str, Any]:
        self._rotate_day()
        self._clean_window()
        return {
            "daily_used": self.daily_count,
            "daily_limit": self.max_daily_requests,
            "window_used": len(self.window_timestamps),
            "window_limit": self.max_window_requests,
            "window_seconds": self.window_seconds,
            "seconds_until_midnight": max(0.0, self.daily_reset - time.time()),
        }


class BrsApiClient(ExternalAPIService):
    """
    Tehran Stock Exchange (BRS) API client backed by brsapi.ir.

    Provides real-time and historical market data exactly as documented in
    docs/BourseApi.txt:
      - AllSymbols / Symbol (real-time)
      - Candlestick (real-time 2-minute + adjusted/unadjusted daily history)
      - History (daily price & trade)
      - Transaction, Shareholder, Index, Codal, Option, Nav
      - IME (physical / fund / certificate)
    """

    def __init__(
        self,
        service_name: str = "BrsApiClient",
        base_url: str = "https://Api.BrsApi.ir",
        api_key: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        rate_limiter: Optional[RateLimiter] = None,
    ):
        super().__init__(
            service_name=service_name,
            base_url=base_url.rstrip("/"),
            timeout=timeout,
            max_retries=max_retries,
        )
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None
        settings = get_settings()
        self.rate_limiter = rate_limiter or RateLimiter(
            max_daily_requests=settings.BRS_RATE_LIMIT_MAX_DAILY,
            max_window_requests=settings.BRS_RATE_LIMIT_MAX_WINDOW,
            window_seconds=settings.BRS_RATE_LIMIT_WINDOW_SECONDS,
        )

    async def initialize(self) -> None:
        """Initialize the HTTP session."""
        self.session = aiohttp.ClientSession()
        self.logger.info("BrsApiClient initialized (base_url=%s)", self.base_url)

    async def shutdown(self) -> None:
        """Close the HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()
        self.logger.info("BrsApiClient shutdown")

    # ------------------------------------------------------------------ #
    # Low-level request helper
    # ------------------------------------------------------------------ #
    async def _request(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Perform an authenticated GET against brsapi.ir.

        The API key is injected automatically as the `key` query parameter.
        A browser User-Agent is always sent because brsapi.ir rejects the
        default Python/Go user agents.
        """
        if not self.session:
            raise RuntimeError("BrsApiClient not initialized")

        self.rate_limiter.acquire()

        if params is None:
            params = {}
        if self.api_key:
            params["key"] = self.api_key

        url = f"{self.base_url}{path}"
        headers = {
            "User-Agent": _BROWSER_USER_AGENT,
            "Accept": "application/json",
        }

        for attempt in range(self.max_retries):
            try:
                async with self.session.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as response:
                    if response.status == 429:  # rate limited
                        await self._handle_rate_limit(attempt)
                        continue

                    try:
                        data = await response.json()
                    except Exception:
                        text = await response.text()
                        raise RuntimeError(
                            f"BrsApi returned non-JSON ({response.status}): {text[:200]}"
                        )

                    if response.status == 200:
                        return data
                    raise RuntimeError(f"BrsApi error {response.status}: {data}")
            except aiohttp.ClientError as e:
                if attempt < self.max_retries - 1:
                    self.logger.warning("Retry %s/%s: %s", attempt + 1, self.max_retries, e)
                    await asyncio.sleep(min(2 ** attempt, 30))
                else:
                    self.logger.error("BrsApi request failed: %s", e)
                    raise

        raise RuntimeError("BrsApi max retries exceeded")

    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Return current rate-limit usage."""
        return self.rate_limiter.status()

    # ------------------------------------------------------------------ #
    # Real-time market data
    # ------------------------------------------------------------------ #
    async def get_all_symbols(self, market_type: int = 1) -> List[Dict[str, Any]]:
        """
        AllSymbols endpoint - real-time snapshot of every symbol.

        type: 1=Stocks+ETF+Rights (default), 2=Commodity Exchange,
              3=Futures, 4=Debt Securities, 5=Housing Facilities
        """
        data = await self._request(
            "/Tsetmc/AllSymbols.php", {"type": market_type}
        )
        return data.get("symbols", data) if isinstance(data, dict) else data

    async def get_symbol(self, l18: str) -> Dict[str, Any]:
        """
        Symbol endpoint - comprehensive real-time data for one ticker.

        Includes all AllSymbols fields plus assemblies, industry group and
        full market depth.
        """
        return await self._request("/Tsetmc/Symbol.php", {"l18": l18})

    # ------------------------------------------------------------------ #
    # Candles & history
    # ------------------------------------------------------------------ #
    async def get_candlestick(
        self, l18: str, candle_type: int = 1
    ) -> Dict[str, Any]:
        """
        Candlestick endpoint.

        candle_type: 1=real-time 2-minute candles (current day),
                     2=unadjusted daily history,
                     3=adjusted daily history (cash dividend + capital increase)
        """
        return await self._request(
            "/Tsetmc/Candlestick.php", {"type": candle_type, "l18": l18}
        )

    async def get_history(self, l18: str, history_type: int = 0) -> List[Dict[str, Any]]:
        """
        History endpoint - daily price & trade data.

        history_type: 0=default daily history
        """
        data = await self._request(
            "/Tsetmc/History.php", {"type": history_type, "l18": l18}
        )
        return data.get("history", data) if isinstance(data, dict) else data

    # ------------------------------------------------------------------ #
    # Trades & shareholders
    # ------------------------------------------------------------------ #
    async def get_transaction(
        self, l18: str, date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Transaction endpoint - intraday trade ticks.

        date (optional, Jalali YYYY-MM-DD) defaults to the last trading day.
        """
        params: Dict[str, Any] = {"l18": l18}
        if date:
            params["date"] = date
        data = await self._request("/Tsetmc/Transaction.php", params)
        return data.get("transactions", data) if isinstance(data, dict) else data

    async def get_shareholder(
        self, l18: str, date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Shareholder endpoint - major shareholders of a symbol.

        date (optional, Jalali YYYY-MM-DD) defaults to the latest snapshot.
        """
        params: Dict[str, Any] = {"l18": l18}
        if date:
            params["date"] = date
        data = await self._request("/Tsetmc/Shareholder.php", params)
        return data.get("shareholders", data) if isinstance(data, dict) else data

    # ------------------------------------------------------------------ #
    # Indices & options
    # ------------------------------------------------------------------ #
    async def get_index(self, index_type: int = 1) -> Dict[str, Any]:
        """
        Index endpoint - market indices.

        index_type: 1=TSE Total+Equal-Weight, 2=Fara Bours, 3=Selected indices
        """
        return await self._request("/Tsetmc/Index.php", {"type": index_type})

    async def get_option(self) -> List[Dict[str, Any]]:
        """Option endpoint - real-time option market (call/put)."""
        data = await self._request("/Tsetmc/Option.php")
        return data.get("options", data) if isinstance(data, dict) else data

    async def get_nav(self, l18: str) -> Dict[str, Any]:
        """Nav endpoint - ETF fund NAV (subscription / redemption)."""
        return await self._request("/Tsetmc/Nav.php", {"l18": l18})

    # ------------------------------------------------------------------ #
    # Codal (disclosures)
    # ------------------------------------------------------------------ #
    async def get_codal(
        self,
        l18: Optional[str] = None,
        category: Optional[int] = None,
        date_start: Optional[str] = None,
        date_end: Optional[str] = None,
        page: int = 1,
    ) -> Dict[str, Any]:
        """
        Codal Announcement endpoint - company disclosures.

        category: 1=Annual financial, 2=Info disclosure, 3=Monthly performance,
                  6=Assemblies, 7=Capital increase
        """
        params: Dict[str, Any] = {"page": page}
        if l18:
            params["l18"] = l18
        if category is not None:
            params["category"] = category
        if date_start:
            params["date_start"] = date_start
        if date_end:
            params["date_end"] = date_end
        return await self._request("/Codal/Announcement.php", params)

    # ------------------------------------------------------------------ #
    # IME (commodity exchange)
    # ------------------------------------------------------------------ #
    async def get_ime_physical(self) -> List[Dict[str, Any]]:
        """IME Physical endpoint - physical commodity trade statistics."""
        data = await self._request("/IME/Physical.php")
        return data.get("physical", data) if isinstance(data, dict) else data

    async def get_ime_fund(self) -> List[Dict[str, Any]]:
        """IME Fund endpoint - commodity-backed fund data."""
        data = await self._request("/IME/Fund.php")
        return data.get("funds", data) if isinstance(data, dict) else data

    async def get_ime_certificate(self) -> List[Dict[str, Any]]:
        """IME Certificate endpoint - commodity deposit certificates."""
        data = await self._request("/IME/Certificate.php")
        return data.get("certificates", data) if isinstance(data, dict) else data

    # ------------------------------------------------------------------ #
    # Compatibility wrappers used by StockService / HistoryService /
    # MarketService. These map the service-level method names onto the
    # canonical BrsApi endpoints above so the rest of the codebase can
    # call a stable interface regardless of endpoint naming.
    # ------------------------------------------------------------------ #
    async def get_stock_info(self, l18: str) -> Dict[str, Any]:
        """Compatibility wrapper: stock info → Symbol endpoint."""
        return await self.get_symbol(l18)

    async def get_stock_price(self, l18: str) -> Dict[str, Any]:
        """Compatibility wrapper: current price → real-time 2-minute candle."""
        data = await self.get_candlestick(l18, candle_type=1)
        candles = (
            data.get("candles", data) if isinstance(data, dict) else data
        )
        if isinstance(candles, list) and candles:
            latest = candles[-1]
            return {
                "open": latest.get("open"),
                "high": latest.get("high"),
                "low": latest.get("low"),
                "close": latest.get("close"),
                "last": latest.get("close"),
            }
        return data

    async def get_stock_history(
        self,
        l18: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        interval: str = "daily",
    ) -> List[Dict[str, Any]]:
        """Compatibility wrapper: history → History endpoint."""
        return await self.get_history(l18, history_type=0)

    async def search_stocks(self, query: str) -> List[Dict[str, Any]]:
        """Compatibility wrapper: search → filter AllSymbols by l18/name."""
        symbols = await self.get_all_symbols(market_type=1)
        if not isinstance(symbols, list):
            return []
        q = query.strip().lower()
        return [
            s for s in symbols
            if q in str(s.get("l18", "")).lower()
            or q in str(s.get("name", "")).lower()
            or q in str(s.get("symbol", "")).lower()
        ]

    async def get_market_indices(self) -> List[Dict[str, Any]]:
        """Compatibility wrapper: market indices → Index endpoint (type=1)."""
        data = await self.get_index(index_type=1)
        if isinstance(data, dict):
            return data.get("indices", [data])
        return data if isinstance(data, list) else [data]

    async def get_market_stats(self) -> Dict[str, Any]:
        """Compatibility wrapper: market stats → aggregate Index data."""
        indices = await self.get_index(index_type=1)
        if isinstance(indices, dict):
            return indices
        return {"indices": indices}

    async def get_top_gainers(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Compatibility stub: gainers require DB latest_prices view."""
        raise RuntimeError(
            "get_top_gainers requires database access. "
            "Use the /market/tse-dashboard endpoint instead."
        )

    async def get_top_losers(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Compatibility stub: losers require DB latest_prices view."""
        raise RuntimeError(
            "get_top_losers requires database access. "
            "Use the /market/tse-dashboard endpoint instead."
        )

    async def get_most_active(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Compatibility stub: most active requires DB latest_prices view."""
        raise RuntimeError(
            "get_most_active requires database access. "
            "Use the /market/tse-dashboard endpoint instead."
        )
