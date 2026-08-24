from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from ..interfaces.i_logger import ILogger
from ...domain.interfaces.crypto.i_crypto_price_repository import ICryptoPriceRepository
from ...domain.interfaces.crypto.i_crypto_market_data_repository import ICryptoMarketDataRepository
from ...domain.shared.result import Result

class CryptoIngestionService:
    """
    Application service for ingesting crypto market data.
    Follows Clean OO: DI, Small Methods, Single Responsibility.
    """
    
    def __init__(
        self,
        price_repo: ICryptoPriceRepository,
        market_data_repo: ICryptoMarketDataRepository,
        logger: ILogger
    ):
        self._price_repo = price_repo
        self._market_data_repo = market_data_repo
        self._logger = logger

    async def ingest_market_prices(self, assets: List[Dict[str, Any]]) -> Result[int]:
        """Ingest current prices for a list of assets."""
        count = 0
        for asset in assets:
            result = await self._ingest_single_price(asset["id"], asset["symbol"])
            if result.is_success:
                count += 1
        return Result.success(count)

    async def ingest_fundamentals(self, assets: List[Dict[str, Any]]) -> Result[int]:
        """Ingest fundamental data for a list of assets."""
        count = 0
        for asset in assets:
            result = await self._ingest_single_fundamental(asset["id"], asset["symbol"])
            if result.is_success:
                count += 1
        return Result.success(count)

    async def _ingest_single_price(self, asset_id: str, symbol: str) -> Result[bool]:
        price_result = await self._price_repo.get_price(symbol)
        if price_result.is_failure:
            return Result.failure(price_result.error_message, price_result.error_code) # type: ignore
            
        payload = {
            "price": price_result.value.price,
            "timestamp": price_result.value.timestamp.isoformat(),
            "vs_currency": price_result.value.vs_currency
        }
        
        return await self._market_data_repo.save_raw_data(
            asset_id=asset_id,
            symbol=symbol,
            data_type="PRICE",
            payload=payload,
            exchange="COINGECKO"
        )

    async def _ingest_single_fundamental(self, asset_id: str, symbol: str) -> Result[bool]:
        # Implementation for fundamentals...
        return Result.success(True)
