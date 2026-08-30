"""
Crypto Ingestion Service - tier 2 data ingestion for cryptocurrency markets.
"""

import asyncio
import functools
import time
from datetime import timezone, datetime
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



class CryptoRateLimiter:
    """Simple rate limiter for crypto API calls."""

    def __init__(self, max_requests: int = 100, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.request_times: List[float] = []

    async def acquire(self) -> None:
        """Acquire permission to make a request, respecting rate limits."""
        now = datetime.now(timezone.utc).timestamp()
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
        now = datetime.now(timezone.utc).timestamp()
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
                "timestamp": datetime.now(timezone.utc).replace(tzinfo=utc),
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
                "timestamp": datetime.now(timezone.utc).replace(tzinfo=utc),
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
            ingested_at=datetime.now(timezone.utc).replace(tzinfo=utc),
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
                "ingested_at": datetime.now(timezone.utc).replace(tzinfo=utc),
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
                        age_seconds = (datetime.now(timezone.utc).replace(tzinfo=timezone.utc) - 
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
                "timestamp": datetime.now(timezone.utc).replace(tzinfo=utc),
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