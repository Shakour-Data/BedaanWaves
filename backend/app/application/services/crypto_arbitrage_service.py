import asyncio
from typing import List, Dict, Any
from decimal import Decimal
from ..interfaces.i_crypto_arbitrage_service import ICryptoArbitrageService
from ...domain.interfaces.crypto.i_exchange_price_provider import IExchangePriceProvider
from ...domain.value_objects.crypto.arbitrage_opportunity import ArbitrageOpportunity
from ...domain.shared.result import Result

class CryptoArbitrageService(ICryptoArbitrageService):
    """
    Application service for arbitrage detection.
    Follows Clean OO: Strategy Pattern, DI, Result Pattern.
    """
    
    def __init__(
        self, 
        providers: List[IExchangePriceProvider],
        min_profit_threshold: float = 1.0,
        fee_bps: int = 50
    ):
        self._providers = providers
        self._min_profit_threshold = Decimal(str(min_profit_threshold))
        self._fee_bps = fee_bps

    async def get_opportunities(self) -> Result[List[ArbitrageOpportunity]]:
        price_data_result = await self._aggregate_prices()
        if price_data_result.is_failure:
            return Result.failure(price_data_result.error_message, price_data_result.error_code) # type: ignore
            
        opportunities = self._detect_profitable_trades(price_data_result.value)
        return Result.success(opportunities)

    async def simulate_trade(self, opportunity: ArbitrageOpportunity, amount: Decimal) -> Result[Dict[str, Any]]:
        if amount <= 0:
            return Result.failure("Amount must be positive", "INVALID_ARGUMENT")
            
        fee_cost = Decimal(opportunity.estimated_fee_bps) / Decimal(10000)
        net_profit = (opportunity.profit_percentage - fee_cost * Decimal(100)) * amount / Decimal(100)
        
        return Result.success({
            "opportunity": opportunity,
            "estimated_profit": net_profit.quantize(Decimal('0.00000001')),
            "is_feasible": net_profit > 0
        })

    async def _aggregate_prices(self) -> Result[Dict[str, Dict[str, Any]]]:
        tasks = [p.get_tickers() for p in self._providers]
        results = await asyncio.gather(*tasks)
        
        aggregated = {}
        for idx, res in enumerate(results):
            if res.is_success:
                aggregated[self._providers[idx].exchange_name] = res.value
                
        if not aggregated:
            return Result.failure("Failed to fetch prices from any exchange", "FETCH_ERROR")
            
        return Result.success(aggregated)

    def _detect_profitable_trades(self, price_data: Dict[str, Dict[str, Any]]) -> List[ArbitrageOpportunity]:
        opportunities = []
        exchanges = list(price_data.keys())
        
        for i in range(len(exchanges)):
            for j in range(len(exchanges)):
                if i == j: continue
                
                buy_ex, sell_ex = exchanges[i], exchanges[j]
                opps = self._compare_exchanges(buy_ex, sell_ex, price_data[buy_ex], price_data[sell_ex])
                opportunities.extend(opps)
                
        return sorted(opportunities, key=lambda x: x.profit_percentage, reverse=True)

    def _compare_exchanges(self, buy_ex: str, sell_ex: str, buy_tickers: Dict[str, Any], sell_tickers: Dict[str, Any]) -> List[ArbitrageOpportunity]:
        results = []
        for symbol, buy_ticker in buy_tickers.items():
            if symbol not in sell_tickers: continue
            
            sell_ticker = sell_tickers[symbol]
            spread = (sell_ticker.ask - buy_ticker.bid) / buy_ticker.bid
            profit_pct = spread * Decimal(100)
            
            if profit_pct > self._min_profit_threshold:
                results.append(ArbitrageOpportunity(
                    buy_exchange=buy_ex,
                    sell_exchange=sell_ex,
                    asset=symbol,
                    buy_price=buy_ticker.bid,
                    sell_price=sell_ticker.ask,
                    profit_percentage=profit_pct.quantize(Decimal('0.01')),
                    estimated_fee_bps=self._fee_bps
                ))
        return results
