from fastapi import HTTPException
from ...application.interfaces.i_crypto_price_service import ICryptoPriceService
from ...domain.shared.result import Result

class CryptoController:
    """
    Presentation layer controller for Crypto operations.
    Follows Clean OO: Dependency Injection, No business logic, Result handling.
    """
    
    def __init__(self, price_service: ICryptoPriceService):
        self._price_service = price_service

    async def get_price(self, symbol: str, vs_currency: str = "usd"):
        result = await self._price_service.get_current_price(symbol, vs_currency)
        return self._handle_result(result)

    async def get_ohlc(self, symbol: str, days: int = 7):
        result = await self._price_service.get_historical_candles(symbol, days)
        return self._handle_result(result)

    def _handle_result(self, result: Result):
        if result.is_success:
            return {"status": "success", "data": result.value}
            
        if result.error_code == "INVALID_ARGUMENT":
            raise HTTPException(status_code=400, detail=result.error_message)
        if result.error_code == "FETCH_ERROR":
            raise HTTPException(status_code=502, detail=result.error_message)
            
        raise HTTPException(status_code=500, detail=result.error_message)
