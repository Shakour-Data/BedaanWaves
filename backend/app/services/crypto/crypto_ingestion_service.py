"""
Crypto Ingestion Service - tier 2 data ingestion for cryptocurrency markets.
"""

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import aiohttp
from pytz import utc

from ..core.base_service import DataService
from ..core.config import get_settings
from ..core.logging_service import getLogger
from ..db.base import async_session_maker
from ..models.models import RawMarketData, Asset

logger = getLogger(__name__)

# ----------------------------------------------------------------------
# Configuration & Constants
# ----------------------------------------------------------------------
settings = get_settings()
SESSION_TIMEOUT = 30  # seconds


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


# ----------------------------------------------------------------------
# Main Service Class
# ----------------------------------------------------------------------
class CryptoIngestionService(DataService):
    """
    Service for ingesting cryptocurrency market data from external APIs
    (CoinGecko, Binance) into the raw_market_data table.
    """

    def __init__(
        self,
        service_name: str = "CryptoIngestionService",
        crypto_client: Optional[Any] = None,  # Will be set externally
    ):
        super().__init__(service_name)
        self.crypto_client = crypto_client

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

    async def _lookup_asset_by_symbol(self, session: Any, symbol: str) -> Any:
        """
        Look up asset by symbol (case-insensitive).
        Returns first matching Asset row.
        """
        stmt = select(Asset).where(Asset.symbol == symbol)
        result = await session.execute(stmt)
        return result.scalars().first()

    async def _test_connection(self) -> bool:
        """Basic connectivity test (placeholder for circuit breaker logic)."""
        return True