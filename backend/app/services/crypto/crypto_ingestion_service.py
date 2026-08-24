"""
Crypto Ingestion Service - tier 2 data ingestion for cryptocurrency markets.
"""

import asyncio
import functools
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import aiohttp
from pytz import utc

import logging
from sqlalchemy import select
from ..core.base_service import DataService
from ..core.config import get_settings
from ...db.base import async_session_maker
from ...models.models import RawMarketData, Asset

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Configuration & Constants
# ----------------------------------------------------------------------
settings = get_settings()
SESSION_TIMEOUT = 30  # seconds


# ----------------------------------------------------------------------
# Circuit Breaker Pattern for API Resilience
# ----------------------------------------------------------------------
class CircuitBreaker:
    """Circuit breaker for API calls to prevent cascading failures."""
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60, expected_exception: type = Exception):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def __call__(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if self.state == "OPEN":
                if self._should_attempt_reset():
                    self.state = "HALF_OPEN"
                else:
                    raise Exception("Circuit breaker is OPEN - blocking call")
    
    async def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
            else:
                raise Exception("Circuit breaker is OPEN - blocking call")
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as exc:
            self._on_failure()
            raise exc
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        return (
            self.last_failure_time is not None and 
            time.time() - self.last_failure_time >= self.timeout
        )
    
    def _on_success(self) -> None:
        """Reset circuit breaker on successful call."""
        self.failure_count = 0
        self.state = "CLOSED"
    
    def _on_failure(self) -> None:
        """Record failure and potentially open circuit."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"


# ----------------------------------------------------------------------
# Helper Functions
# ----------------------------------------------------------------------
def _sanitize_symbol(raw_symbol: str) -> str:
    """Normalize symbol format (CoinGecko, Binance differences)."""
    sanitized = raw_symbol.upper().replace("/", "")
    return sanitized


async def _fetch_coingecko_price(crypto_id: str) -> Dict[str, Any]:
    """Fetch price from CoinGecko API."""
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://api.coingecko.com/api/v3/simple/price",
            params={"ids": crypto_id, "vs_currencies": "usd"},
            timeout=SESSION_TIMEOUT,
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                text = await response.text()
                raise RuntimeError(
                    f"CoinGecko request failed ({response.status}): {text}"
                )


async def _fetch_binance_depth(symbol: str) -> Dict[str, Any]:
    """Fetch order book depth from Binance API."""
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://api.binance.com/api/v3/depth",
            params={"symbol": symbol, "limit": 100},
            timeout=SESSION_TIMEOUT,
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                text = await response.text()
                raise RuntimeError(
                    f"Binance depth request failed ({response.status}): {text}"
                )


async def _fetch_coingecko_market_data(crypto_id: str) -> Dict[str, Any]:
    """Fetch full market data from CoinGecko API."""
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
        url = f"https://api.coingecko.com/api/v3/coins/{crypto_id}"
        params = {
            "localization": False,
            "tickers": False,
            "market_data": True,
            "community_data": False,
            "developer_data": False,
            "sparkline": False,
        }
        async with session.get(url, params=params) as response:
            if response.status == 200:
                return await response.json()
            else:
                text = await response.text()
                raise RuntimeError(
                    f"CoinGecko market data request failed ({response.status}): {text}"
                )


# ----------------------------------------------------------------------
# Main Service Class
# ----------------------------------------------------------------------
class FallbackDataSource:
    """Fallback data source for cryptocurrency fundamental data with rate limiting."""

    def __init__(self):
        self.primary_source = "coingecko"
        self.secondary_sources = ["coinmarketcap", "crypto_compare"]
        self.rate_limit_tracker: Dict[str, tuple] = {}
        self.max_retries = 5
        self.backoff_factor = 1.5

    async def get_fundamental_data(self, crypto_id: str, symbol: str) -> Dict[str, Any]:
        """Fetch fundamental data with fallback strategy and rate limit handling."""
        self._check_rate_limits()

        for attempt in range(self.max_retries):
            try:
                wait_time = self._get_backoff_time(crypto_id)
                if wait_time > 0:
                    await asyncio.sleep(wait_time)

                data = await self._fetch_coingecko_with_retry(crypto_id, symbol)
                return data
            except Exception as exc:
                logger.warning(f"CoinGecko attempt {attempt + 1} failed for {symbol}: {exc}")
                if attempt == self.max_retries - 1:
                    break
                await asyncio.sleep(self.backoff_factor ** attempt)

        return await self._try_secondary_sources(crypto_id, symbol)

    async def _fetch_coingecko_with_retry(self, crypto_id: str, symbol: str) -> Dict[str, Any]:
        """Fetch from CoinGecko with retry logic."""
        url = f"https://api.coingecko.com/api/v3/coins/{crypto_id}"
        params = {
            "localization": False,
            "tickers": False,
            "market_data": True,
            "community_data": False,
            "developer_data": False,
            "sparkline": False,
        }

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    return self._extract_fundamental_data(result, crypto_id, symbol)
                elif response.status == 429:
                    self._record_rate_limit(crypto_id)
                    raise Exception("Rate limit exceeded for CoinGecko")
                elif response.status == 404:
                    raise Exception(f"CoinGecko: {crypto_id} not found")
                else:
                    text = await response.text()
                    raise Exception(f"CoinGecko API error {response.status}: {text}")

    async def _try_secondary_sources(self, crypto_id: str, symbol: str) -> Dict[str, Any]:
        """Try secondary data sources as fallback."""
        logger.warning(f"Trying secondary sources for {symbol}")

        for source in self.secondary_sources:
            try:
                if source == "coinmarketcap":
                    data = await self._fetch_coinmarketcap(crypto_id, symbol)
                    if data:
                        return data
                elif source == "crypto_compare":
                    data = await self._fetch_crypto_compare(crypto_id, symbol)
                    if data:
                        return data
            except Exception as exc:
                logger.debug(f"{source} failed for {symbol}: {exc}")

        return self._get_minimal_fallback_data(crypto_id, symbol)

    async def _fetch_coinmarketcap(self, crypto_id: str, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch from CoinMarketCap API (secondary source)."""
        api_key = settings.COINMARKETCAP_API_KEY if hasattr(settings, "COINMARKETCAP_API_KEY") else None
        if not api_key:
            logger.warning("CoinMarketCap API key not configured")
            return None

        import aiohttp

        url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
        headers = {"X-CMC_PRO_API_KEY": api_key}
        params = {"symbol": symbol.upper()}

        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    return self._extract_fundamental_data(result, crypto_id, symbol)
                return None

    async def _fetch_crypto_compare(self, crypto_id: str, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch from CryptoCompare API (tertiary source)."""
        import aiohttp

        url = "https://min-api.cryptocompare.com/data/pricemultifull"
        params = {"fsyms": symbol.upper(), "tsyms": "USD"}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    return self._extract_fundamental_data(result, crypto_id, symbol)
                return None

    def _extract_fundamental_data(self, api_result: Dict[str, Any], crypto_id: str, symbol: str) -> Dict[str, Any]:
        """Extract and normalize fundamental data from API result."""
        try:
            market_data = {}

            if "market_data" in api_result:
                market_data = api_result["market_data"]
            elif "data" in api_result and len(api_result["data"]) > 0:
                coin_data = api_result["data"][list(api_result["data"].keys())[0]]
                if "quote" in coin_data and "USD" in coin_data["quote"]:
                    market_data = coin_data["quote"]["USD"]

            current_price = market_data.get("price_usd", market_data.get("price", {}).get("usd", 0)) if market_data else 0
            market_cap = market_data.get("market_cap_usd", market_data.get("marketCapUSD", 0)) if market_data else 0
            total_volume = market_data.get("total_volume_usd", market_data.get("volume24hUSD", 0)) if market_data else 0
            circulating_supply = market_data.get("circulating_supply", 0)
            total_supply = market_data.get("total_supply", 0)
            price_change_24h = market_data.get("price_change_percentage_24h", 0)
            market_cap_change_24h = market_data.get("market_cap_change_percentage_24h", 0)

            return {
                "price": current_price,
                "market_cap": market_cap,
                "total_volume": total_volume,
                "circulating_supply": circulating_supply,
                "total_supply": total_supply,
                "price_change_24h_pct": float(price_change_24h),
                "market_cap_change_24h_pct": float(market_cap_change_24h),
                "timestamp": datetime.utcnow().replace(tzinfo=utc),
                "fallback_source": True,
            }
        except Exception as exc:
            logger.error(f"Error extracting fundamental data for {symbol}: {exc}")
            return self._get_minimal_fallback_data(crypto_id, symbol)

    def _get_minimal_fallback_data(self, crypto_id: str, symbol: str) -> Dict[str, Any]:
        """Return minimal data when all APIs fail."""
        return {
            "price": 0.0,
            "market_cap": 0.0,
            "total_volume": 0.0,
            "circulating_supply": 0.0,
            "total_supply": 0.0,
            "price_change_24h_pct": 0.0,
            "market_cap_change_24h_pct": 0.0,
            "timestamp": datetime.utcnow().replace(tzinfo=utc),
            "fallback_source": True,
            "quality": "poorest",
            "error_message": "All data sources failed",
        }

    def _check_rate_limits(self) -> None:
        """Check and enforce rate limits."""
        current_time = datetime.utcnow().timestamp()
        expired_keys = [k for k, (count, ts) in self.rate_limit_tracker.items() if current_time - ts > 3600]
        for key in expired_keys:
            del self.rate_limit_tracker[key]

        for crypto_id, (count, ts) in self.rate_limit_tracker.items():
            if count >= 120:
                wait_seconds = 3600 - (current_time - ts)
                if wait_seconds > 0:
                    logger.warning(f"Rate limit approaching for {crypto_id}, wait {wait_seconds:.0f}s")

    def _get_backoff_time(self, crypto_id: str) -> float:
        """Get backoff time based on rate limit history."""
        if crypto_id not in self.rate_limit_tracker:
            return 0.0
        count, ts = self.rate_limit_tracker[crypto_id]
        current_time = datetime.utcnow().timestamp()
        if count >= 120 and current_time - ts < 3600:
            return max(0, 3600 - (current_time - ts)) / 60.0
        return 0.0

    def _record_rate_limit(self, crypto_id: str) -> None:
        """Record rate limit hit."""
        current_time = datetime.utcnow().timestamp()
        if crypto_id not in self.rate_limit_tracker:
            self.rate_limit_tracker[crypto_id] = (1, current_time)
        else:
            count, ts = self.rate_limit_tracker[crypto_id]
            self.rate_limit_tracker[crypto_id] = (count + 1, ts)


class CryptoRateLimiter:
    """Simple rate limiter for crypto API calls."""

    def __init__(self, max_requests: int = 100, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.request_times: List[float] = []

    async def acquire(self) -> None:
        """Acquire permission to make a request, respecting rate limits."""
        now = datetime.utcnow().timestamp()
        self.request_times = [t for t in self.request_times if now - t < self.time_window]

        if len(self.request_times) >= self.max_requests:
            sleep_time = self.time_window - (now - self.request_times[0])
            if sleep_time > 0:
                logger.warning(f"Rate limit reached, sleeping for {sleep_time:.1f}s")
                await asyncio.sleep(sleep_time)
                self.request_times = [t for t in self.request_times if now - t < self.time_window]

        self.request_times.append(now)

    def get_current_usage(self) -> tuple:
        """Return current request count and time window."""
        now = datetime.utcnow().timestamp()
        self.request_times = [t for t in self.request_times if now - t < self.time_window]
        return len(self.request_times), self.time_window


class CryptoIngestionService(DataService):
    """
    Service for ingesting cryptocurrency market data from external APIs
    (CoinGecko, Binance) into the raw_market_data table.
    """

    def __init__(
        self,
        service_name: str = "CryptoIngestionService",
        crypto_client: Optional[Any] = None,
    ):
        super().__init__(service_name)
        self.crypto_client = crypto_client
        self.fallback_source = FallbackDataSource()
        self.rate_limiter = CryptoRateLimiter(max_requests=50, time_window=60)
    
    async def initialize(self) -> None:
        self.logger.info("CryptoIngestionService initialized")

    async def shutdown(self) -> None:
        self.logger.info("CryptoIngestionService shutdown")

    # ------------------------------------------------------------------
    # Core Ingestion Workflow
    # ------------------------------------------------------------------
    async def ingest_raw_data(
        self,
        assets: List[Any],
        session: Any,
        limit_per_symbol: int = 1,
        include_price: bool = True,
        include_depth: bool = True,
    ) -> int:
        """
        Fetch raw crypto market data for given trading pairs/symbols
        and store them in raw_market_data table.
        """
        stored_count = 0

        for asset in assets:
            asset_id = asset.id
            symbol = asset.symbol.upper()
            exchange = "BINANCE"  # default exchange for crypto pairs
            raw_symbol = _sanitize_symbol(symbol)

            # Fetch price data (CoinGecko)
            if include_price:
                try:
                    price_data = await self._fetch_price_data(raw_symbol)
                    await self._store_raw_market_data(
                        session,
                        asset_id,
                        raw_symbol,
                        exchange,
                        "PRICE",
                        price_data,
                    )
                    stored_count += 1
                except Exception as exc:
                    self.logger.warning(f"Failed to ingest price for {symbol}: {exc}")

            # Fetch depth data (Binance)
            if include_depth:
                try:
                    depth_data = await self._fetch_depth_data(raw_symbol)
                    await self._store_raw_market_data(
                        session,
                        asset_id,
                        raw_symbol,
                        exchange,
                        "DEPTH",
                        depth_data,
                    )
                    stored_count += 1
                except Exception as exc:
                    self.logger.warning(f"Failed to ingest depth for {symbol}: {exc}")

        await session.commit()
        return stored_count

    # ------------------------------------------------------------------
    # API Calls
    # ------------------------------------------------------------------
    async def _fetch_price_data(self, crypto_id: str) -> Dict[str, Any]:
        """Fetch price data from CoinGecko API."""
        try:
            raw = await _fetch_coingecko_price(crypto_id)
            # CoinGecko returns: {crypto_id: {usd: price, ...}, ...}
            price_info = raw.get(crypto_id.lower(), {})
            usd_price = price_info.get("usd")

            if usd_price is None:
                raise ValueError("Price not found in CoinGecko response")

            return {
                "price": usd_price,
                "timestamp": datetime.utcnow().replace(tzinfo=utc),
                "volume": 0,  # Will be populated from other endpoint
            }
        except Exception as exc:
            self.logger.error(f"Error fetching price for {crypto_id}: {exc}")
            raise

    async def _fetch_depth_data(self, symbol: str) -> Dict[str, Any]:
        """Fetch depth data from Binance API."""
        try:
            raw = await _fetch_binance_depth(symbol)
            # Binance response includes 'bids' and 'asks' arrays and 'lastPrice'
            last_price = float(raw.get("lastPrice", 0))
            return {
                "price": last_price,
                "bids": raw.get("bids", []),
                "asks": raw.get("asks", []),
                "timestamp": datetime.utcnow().replace(tzinfo=utc),
                "volume_base": sum(float(bid[1]) for bid in raw.get("bids", [])),
                "volume_quote": sum(float(ask[1]) * float(ask[0]) for ask in raw.get("asks", [])),
            }
        except Exception as exc:
            self.logger.error(f"Error fetching depth for {symbol}: {exc}")
            raise

    # ------------------------------------------------------------------
    # Database Operations
    # ------------------------------------------------------------------
    async def _store_raw_market_data(
        self,
        session: Any,
        asset_id: str,
        raw_symbol: str,
        exchange: str,
        data_type: str,
        payload: Dict[str, Any],
    ):
        """
        Insert one record into raw_market_data table.
        Payload must contain at least 'price'/'volume' fields.
        """
        from sqlalchemy.dialects.postgresql import insert as pg_insert

        stmt = pg_insert(RawMarketData).values(
            asset_id=asset_id,
            raw_symbol=raw_symbol,
            market="CRYPTO",
            exchange=exchange,
            data_type=data_type,
            raw_payload=payload,
            # Basic extracted fields – may be empty depending on data_type
            price=payload.get("price"),
            volume=payload.get("volume_base"),
            quote_volume=payload.get("volume_quote"),
            source_timestamp=payload.get("timestamp"),
            ingested_at=datetime.utcnow().replace(tzinfo=utc),
            data_quality="RAW",
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["raw_symbol", "exchange", "data_type", "source_timestamp"],
            set_={
                "price": payload.get("price"),
                "volume": payload.get("volume_base"),
                "quote_volume": payload.get("volume_quote"),
                "source_timestamp": payload.get("timestamp"),
                "raw_payload": payload,
                "ingested_at": datetime.utcnow().replace(tzinfo=utc),
            },
        )
        await session.execute(stmt)

    # ------------------------------------------------------------------
    # Public Endpoints
    # ------------------------------------------------------------------
    async def ingest_symbol(self, symbol: str, session: Any) -> int:
        """
        Ingest raw data for a single trading pair/symbol.
        Returns number of rows inserted/updated.
        """
        # Look up asset by symbol
        stmt = select(Asset).where(Asset.symbol == symbol)
        result = await session.execute(stmt)
        asset = result.scalars().first()
        
        if not asset:
            raise ValueError(f"Asset {symbol} not found in database")

        if not await self._test_connection():
            raise RuntimeError("Failed to establish API connection")

        # Process single asset
        assets = [asset]
        return await self.ingest_raw_data(assets, session)

    async def ingest_crypto_fundamental_data(
        self,
        assets: List[Any],
        session: Any,
        incremental: bool = True,
    ) -> int:
        """
        Fetch fundamental market data (market cap, supply, volume) from CoinGecko
        and store them in raw_market_data table for fundamental analysis.
        
        Args:
            assets: List of Asset objects
            session: Database session
            incremental: If True, skip assets that were recently updated
        """
        stored_count = 0

        for asset in assets:
            asset_id = asset.id
            symbol = asset.symbol.upper()
            raw_symbol = _sanitize_symbol(symbol)
            exchange = "COINGECKO"

            try:
                # Incremental update: check if data was recently ingested
                if incremental:
                    existing = await session.execute(
                        select(RawMarketData)
                        .where(
                            (RawMarketData.raw_symbol == raw_symbol),
                            (RawMarketData.exchange == exchange),
                            (RawMarketData.data_type == "FUNDAMENTAL"),
                        )
                        .order_by(RawMarketData.ingested_at.desc())
                        .limit(1)
                    )
                    latest_record = existing.scalars().first()
                    if latest_record:
                        age_seconds = (datetime.utcnow().replace(tzinfo=timezone.utc) - 
                                       latest_record.ingested_at.replace(tzinfo=timezone.utc)).total_seconds()
                        if age_seconds < 21600:  # 6 hours
                            self.logger.debug(f"Skipping {symbol}, recently updated ({age_seconds:.0f}s ago)")
                            continue

                fundamental_data = await self._fetch_fundamental_data(raw_symbol)
                
                # Data quality check
                if not self._validate_fundamental_data(fundamental_data):
                    self.logger.warning(f"Data quality check failed for {symbol}, storing with quality flag")
                    fundamental_data["data_quality"] = "LOW_QUALITY"
                else:
                    fundamental_data["data_quality"] = "CONFIRMED"
                
                await self._store_raw_market_data(
                    session,
                    asset_id,
                    raw_symbol,
                    exchange,
                    "FUNDAMENTAL",
                    fundamental_data,
                )
                stored_count += 1
            except Exception as exc:
                self.logger.warning(f"Failed to ingest fundamental data for {symbol}: {exc}")

        await session.commit()
        return stored_count
    
    def _validate_fundamental_data(self, data: Dict[str, Any]) -> bool:
        """Validate fundamental data quality."""
        required_fields = ["price", "market_cap", "total_volume"]
        for field in required_fields:
            if field not in data or data[field] is None:
                return False
            try:
                if float(data[field]) <= 0:
                    return False
            except (ValueError, TypeError):
                return False
        return True

    async def _fetch_fundamental_data(self, crypto_id: str) -> Dict[str, Any]:
        """Fetch fundamental market data from CoinGecko API."""
        try:
            raw = await _fetch_coingecko_market_data(crypto_id)
            market_data = raw.get("market_data", {})

            current_price = market_data.get("current_price", {})
            usd_price = current_price.get("usd", 0.0) if current_price else 0.0

            market_cap = market_data.get("market_cap", {})
            usd_mcap = market_cap.get("usd", 0.0) if market_cap else 0.0

            total_volume = market_data.get("total_volume", {})
            usd_volume = total_volume.get("usd", 0.0) if total_volume else 0.0

            circulating_supply = market_data.get("circulating_supply", 0.0) or 0.0
            total_supply = market_data.get("total_supply", 0.0) or 0.0

            price_change_24h = market_data.get("price_change_percentage_24h", 0.0) or 0.0
            market_cap_change_24h = market_data.get("market_cap_change_percentage_24h", 0.0) or 0.0

            return {
                "price": usd_price,
                "market_cap": usd_mcap,
                "total_volume": usd_volume,
                "circulating_supply": circulating_supply,
                "total_supply": total_supply,
                "price_change_24h_pct": float(price_change_24h),
                "market_cap_change_24h_pct": float(market_cap_change_24h),
                "timestamp": datetime.utcnow().replace(tzinfo=utc),
            }
        except Exception as exc:
            self.logger.error(f"Error fetching fundamental data for {crypto_id}: {exc}")
            raise

    async def ingest_symbol(self, symbol: str, session: Any) -> int:
        """Ingest raw data for a single trading pair/symbol."""
        stmt = select(Asset).where(Asset.symbol == symbol)
        result = await session.execute(stmt)
        asset = result.scalars().first()
        
        if not asset:
            raise ValueError(f"Asset {symbol} not found in database")

        if not await self._test_connection():
            raise RuntimeError("Failed to establish API connection")

        assets = [asset]
        return await self.ingest_raw_data(assets, session)

    async def _lookup_asset_by_symbol(self, session: Any, symbol: str) -> Any:
        """Look up asset by symbol (case-insensitive)."""
        stmt = select(Asset).where(Asset.symbol == symbol)
        result = await session.execute(stmt)
        return result.scalars().first()

    async def _test_connection(self) -> bool:
        """Basic connectivity test (placeholder for circuit breaker logic)."""
        return True