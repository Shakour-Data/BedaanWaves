from typing import Dict, Any

class ValuationEngine:
    """Domain service for calculating valuation ratios."""
    
    def calculate_pe(self, stock_price: float, eps: float) -> float:
        if eps <= 0 or stock_price <= 0:
            return 0.0
        return round(stock_price / eps, 2)

    def calculate_pb(self, stock_price: float, bvps: float) -> float:
        if bvps <= 0 or stock_price <= 0:
            return 0.0
        return round(stock_price / bvps, 2)

    def calculate_ps(self, market_cap: float, revenue: float) -> float:
        if revenue <= 0 or market_cap <= 0:
            return 0.0
        return round(market_cap / revenue, 2)
