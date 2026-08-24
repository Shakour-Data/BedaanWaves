from typing import List
from ..interfaces.i_crypto_price_service import ICryptoPriceService
from ..interfaces.i_cache_service import ICacheService
from ...domain.interfaces.crypto.i_crypto_price_repository import ICryptoPriceRepository
from ...domain.value_objects.crypto.crypto_price import CryptoPrice
from ...domain.value_objects.crypto.crypto_candle import CryptoCandle
from ...domain.shared.result import Result

class CryptoPriceService(ICryptoPriceService):
    """
    Application service for crypto price operations.
    Follows Clean OO: DI, Single Responsibility, Result Pattern.
    """
    
    def __init__(
        self, 
        repository: ICryptoPriceRepository, 
        cache: ICacheService
    ):
        """Constructor injection for repository and cache."""
        self._repository = repository
        self._cache = cache

    async def get_current_price(self, symbol: str, vs_currency: str = "usd") -> Result[CryptoPrice]:
        if not symbol:
            return Result.failure("Symbol cannot be empty", "INVALID_ARGUMENT")
            
        cache_key = self._format_cache_key("price", symbol, vs_currency)
        cached_result = await self._cache.get(cache_key, namespace="crypto")
        
        if cached_result.is_success:
            return Result.success(cached_result.value)
            
        repo_result = await self._repository.get_price(symbol, vs_currency)
        if repo_result.is_success:
            await self._cache.set(cache_key, repo_result.value, namespace="crypto", ttl=60)
            
        return repo_result

    async def get_historical_candles(self, symbol: str, days: int = 7) -> Result[List[CryptoCandle]]:
        if not symbol:
            return Result.failure("Symbol cannot be empty", "INVALID_ARGUMENT")
            
        cache_key = self._format_cache_key("ohlc", symbol, str(days))
        cached_result = await self._cache.get(cache_key, namespace="crypto")
        
        if cached_result.is_success:
            return Result.success(cached_result.value)
            
        repo_result = await self._repository.get_ohlc(symbol, days)
        if repo_result.is_success:
            await self._cache.set(cache_key, repo_result.value, namespace="crypto", ttl=300)
            
        return repo_result

    async def search_symbols(self, query: str) -> Result[List[str]]:
        if not query:
            return Result.failure("Search query cannot be empty", "INVALID_ARGUMENT")
            
        return await self._repository.search_assets(query)

    def _format_cache_key(self, prefix: str, symbol: str, suffix: str) -> str:
        """Private helper for key formatting."""
        return f"{prefix}:{symbol.lower()}:{suffix.lower()}"
