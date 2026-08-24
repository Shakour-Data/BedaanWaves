from typing import List
from datetime import datetime
from ....domain.interfaces.crypto.i_crypto_price_repository import ICryptoPriceRepository
from ....domain.value_objects.crypto.crypto_price import CryptoPrice
from ....domain.value_objects.crypto.crypto_candle import CryptoCandle
from ....domain.shared.result import Result
from ....application.interfaces.i_http_client import IHttpClient

class CoinGeckoPriceRepository(ICryptoPriceRepository):
    """
    CoinGecko implementation of ICryptoPriceRepository.
    Translates API responses to Domain Value Objects.
    """
    
    def __init__(self, http_client: IHttpClient):
        self._http = http_client
        self._base_url = "https://api.coingecko.com/api/v3"

    async def get_price(self, symbol: str, vs_currency: str = "usd") -> Result[CryptoPrice]:
        url = f"{self._base_url}/simple/price"
        params = {"ids": symbol.lower(), "vs_currencies": vs_currency.lower()}
        
        result = await self._http.get(url, params=params)
        if result.is_failure:
            return Result.failure(result.error_message, result.error_code) # type: ignore
            
        try:
            price_data = result.value[symbol.lower()][vs_currency.lower()]
            return Result.success(CryptoPrice(symbol=symbol, vs_currency=vs_currency, price=float(price_data)))
        except (KeyError, ValueError, TypeError) as e:
            return Result.failure(f"Malformed API response: {str(e)}", "PARSE_ERROR")

    async def get_ohlc(self, symbol: str, days: int = 7) -> Result[List[CryptoCandle]]:
        url = f"{self._base_url}/coins/{symbol.lower()}/ohlc"
        params = {"vs_currency": "usd", "days": str(days)}
        
        result = await self._http.get(url, params=params)
        if result.is_failure:
            return Result.failure(result.error_message, result.error_code) # type: ignore
            
        try:
            candles = [
                CryptoCandle(
                    timestamp=datetime.fromtimestamp(c[0] / 1000),
                    open=float(c[1]), high=float(c[2]), low=float(c[3]), close=float(c[4])
                ) for c in result.value
            ]
            return Result.success(candles)
        except (IndexError, ValueError, TypeError) as e:
            return Result.failure(f"Malformed OHLC data: {str(e)}", "PARSE_ERROR")

    async def search_assets(self, query: str) -> Result[List[str]]:
        url = f"{self._base_url}/search"
        result = await self._http.get(url, params={"query": query})
        
        if result.is_failure:
            return Result.failure(result.error_message, result.error_code) # type: ignore
            
        coins = result.value.get("coins", [])
        return Result.success([c["id"] for c in coins])
