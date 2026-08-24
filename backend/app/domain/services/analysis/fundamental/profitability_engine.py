from typing import Dict, Any

class ProfitabilityEngine:
    """Domain service for calculating profitability ratios."""
    
    def calculate_gross_margin(self, gross_profit: float, revenue: float) -> float:
        if revenue <= 0:
            return 0.0
        return round((gross_profit / revenue) * 100, 2)

    def calculate_net_margin(self, net_income: float, revenue: float) -> float:
        if revenue <= 0:
            return 0.0
        return round((net_income / revenue) * 100, 2)

    def calculate_roe(self, net_income: float, equity: float) -> float:
        if equity <= 0:
            return 0.0
        return round((net_income / equity) * 100, 2)
