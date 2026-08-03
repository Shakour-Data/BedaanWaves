from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timezone
import aiohttp
import numpy as np
import pandas as pd
from collections import deque

from ..core import AnalysisService
from ..core.dependency_container import get_global_container
from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class MonetaryPolicyService(AnalysisService):
    """Modern Monetary Theory (MMT) based monetary metrics and sectoral balance analysis."""

    # MMT Sectoral Balance Equation: (G - T) + (S - I) + (M - X) = 0
    # Where: G=T Government spending, T=Taxes, S=Private savings, I=Private investment, 
    # M=Imports, X=Exports
    
    SECTORAL_BALANCE_SECTORS = {
        "government": "G - T (Government balance)",
        "private": "S - I (Private domestic balance)", 
        "foreign": "M - X (Foreign balance / Current account)"
    }

    def __init__(self, service_name: str = "MonetaryPolicyService"):
        super().__init__(service_name)
        self.session: Optional[aiohttp.ClientSession] = None
        self.monetary_data_cache: Dict[str, Any] = {}
        self.sectoral_balance_history: Dict[str, deque] = {
            "government": deque(maxlen=100),
            "private": deque(maxlen=100),
            "foreign": deque(maxlen=100)
        }
        self.mmt_regime_history: List[Dict[str, Any]] = []

    async def initialize(self) -> None:
        """Initialize HTTP session for central bank and economic data APIs."""
        self.session = aiohttp.ClientSession()
        self.logger.info("MonetaryPolicyService initialized with MMT framework")

    async def shutdown(self) -> None:
        """Close HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()
        self.logger.info("MonetaryPolicyService shutdown")

    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform comprehensive MMT-based monetary analysis.
        
        Args:
            data: Economic data dictionary containing:
                - government_spending: Government expenditure
                - tax_revenue: Tax collections
                - private_savings: Private sector savings
                - private_investment: Private sector investment
                - exports: Value of exports
                - imports: Value of imports
                - monetary_base: Central bank monetary base (M0)
                - narrow_money: Narrow money supply (M1)
                - broad_money: Broad money supply (M2)
                
        Returns:
            MFT analysis results including sectoral balances and regime classification
        """
        try:
            # Calculate sectoral balances (MMT core identity)
            sectoral_balances = await self._calculate_sectoral_balances(data)
            
            # Analyze monetary aggregates
            monetary_analysis = await self._analyze_monetary_aggregates(data)
            
            # Determine MMT regime
            regime_analysis = await self._classify_mmt_regime(sectoral_balances, monetary_analysis, data)
            
            # Calculate fiscal space
            fiscal_space = await self._calculate_fiscal_space(data)
            
            # Store historical data
            self._update_historical_data(sectoral_balances, regime_analysis)
            
            return {
                "sectoral_balances": sectoral_balances,
                "monetary_analysis": monetary_analysis,
                "regime_classification": regime_analysis,
                "fiscal_space": fiscal_space,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "mmt_identity_check": self._verify_mmt_identity(sectoral_balances)
            }
            
        except Exception as e:
            self.logger.error(f"MMT analysis failed: {str(e)}")
            return {"error": str(e), "timestamp": datetime.now(timezone.utc).isoformat()}

    async def _calculate_sectoral_balances(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate the three sectoral balances from MMT framework."""
        try:
            # Government balance: G - T
            government_spending = float(data.get("government_spending", 0))
            tax_revenue = float(data.get("tax_revenue", 0))
            government_balance = government_spending - tax_revenue
            
            # Private domestic balance: S - I
            private_savings = float(data.get("private_savings", 0))
            private_investment = float(data.get("private_investment", 0))
            private_balance = private_savings - private_investment
            
            # Foreign balance: M - X (Current account)
            imports = float(data.get("imports", 0))
            exports = float(data.get("exports", 0))
            foreign_balance = imports - exports  # Positive = trade deficit
            
            # Verify MMT identity: (G-T) + (S-I) + (M-X) = 0
            identity_sum = government_balance + private_balance + foreign_balance
            
            return {
                "government": {
                    "balance": government_balance,
                    "components": {
                        "government_spending": government_spending,
                        "tax_revenue": tax_revenue
                    },
                    "interpretation": "positive = deficit, negative = surplus"
                },
                "private": {
                    "balance": private_balance,
                    "components": {
                        "private_savings": private_savings,
                        "private_investment": private_investment
                    },
                    "interpretation": "positive = net saving, negative = net borrowing"
                },
                "foreign": {
                    "balance": foreign_balance,
                    "components": {
                        "imports": imports,
                        "exports": exports
                    },
                    "interpretation": "positive = trade deficit, negative = trade surplus"
                },
                "identity_sum": identity_sum,
                "identity_hold": abs(identity_sum) < 0.01  # Should be zero in theory
            }
        except (ValueError, TypeError) as e:
            self.logger.warning(f"Error calculating sectoral balances: {e}")
            return {"error": str(e)}

    async def _analyze_monetary_aggregates(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze monetary aggregates for MMT insights."""
        try:
            monetary_base = float(data.get("monetary_base", 0))  # M0
            narrow_money = float(data.get("narrow_money", 0))   # M1
            broad_money = float(data.get("broad_money", 0))     # M2
            
            # Calculate money multipliers
            m1_multiplier = narrow_money / monetary_base if monetary_base > 0 else 0
            m2_multiplier = broad_money / monetary_base if monetary_base > 0 else 0
            
            # Calculate velocity of money (simplified)
            # In practice, would need GDP data: Velocity = GDP / Money Supply
            gdp_estimate = float(data.get("gdp", 1000))  # Placeholder
            m1_velocity = gdp_estimate / narrow_money if narrow_money > 0 else 0
            m2_velocity = gdp_estimate / broad_money if broad_money > 0 else 0
            
            return {
                "monetary_base": monetary_base,
                "narrow_money": narrow_money,
                "broad_money": broad_money,
                "money_multipliers": {
                    "m1_multiplier": m1_multiplier,
                    "m2_multiplier": m2_multiplier
                },
                "velocity_of_money": {
                    "m1_velocity": m1_velocity,
                    "m2_velocity": m2_velocity
                },
                "money_supply_composition": {
                    "m0_percentage": (monetary_base / broad_money * 100) if broad_money > 0 else 0,
                    "m1_m0_ratio": (narrow_money / monetary_base) if monetary_base > 0 else 0,
                    "m2_m1_ratio": (broad_money / narrow_money) if narrow_money > 0 else 0
                }
            }
        except (ValueError, TypeError, ZeroDivisionError) as e:
            self.logger.warning(f"Error analyzing monetary aggregates: {e}")
            return {"error": str(e)}

    async def _classify_mmt_regime(
        self, 
        sectoral_balances: Dict[str, Any], 
        monetary_analysis: Dict[str, Any],
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Classify the current MMT regime based on sectoral balances and monetary conditions."""
        try:
            gov_balance = sectoral_balances.get("government", {}).get("balance", 0)
            private_balance = sectoral_balances.get("private", {}).get("balance", 0)
            foreign_balance = sectoral_balances.get("foreign", {}).get("balance", 0)
            
            # MMT Regime Classification Framework
            regimes = []
            
            # Fiscal stance
            if gov_balance > 0:
                fiscal_stance = "expansionary"  # Government deficit
                fiscal_strength = min(abs(gov_balance) / 100, 1.0)  # Normalize
            else:
                fiscal_stance = "contractionary"  # Government surplus
                fiscal_strength = min(abs(gov_balance) / 100, 1.0)
            
            # Private sector health
            if private_balance > 0:
                private_health = "net_saving"  # Private sector saving
            else:
                private_health = "net_borrowing"  # Private sector borrowing
            
            # External position
            if foreign_balance > 0:
                external_position = "trade_deficit"  # Importing more than exporting
            else:
                external_position = "trade_surplus"  # Exporting more than importing
            
            # Monetary conditions
            m2_m1_ratio = monetary_analysis.get("money_supply_composition", {}).get("m2_m1_ratio", 1)
            if m2_m1_ratio > 3.0:
                monetary_condition = "high_credit_expansion"
            elif m2_m1_ratio < 1.5:
                monetary_condition = "low_credit_expansion"
            else:
                monetary_condition = "moderate_credit_expansion"
            
            # Determine primary MMT regime
            if abs(gov_balance) > abs(private_balance) and abs(gov_balance) > abs(foreign_balance):
                primary_driver = "fiscal"
                if gov_balance > 0:
                    regime = "fiscal_expansion"
                    description = "Government deficit driving economic activity"
                else:
                    regime = "fiscal_contraction"
                    description = "Government surplus restricting economic activity"
            elif abs(private_balance) > abs(foreign_balance):
                primary_driver = "private"
                if private_balance > 0:
                    regime = "private_sector_saving"
                    description = "Private sector net saving, government must deficit to accommodate"
                else:
                    regime = "private_sector_borrowing"
                    description = "Private sector net borrowing, potentially unsustainable"
            else:
                primary_driver = "external"
                if foreign_balance > 0:
                    regime = "trade_deficit_driven"
                    description = "Trade deficit requiring offsetting domestic surpluses"
                else:
                    regime = "trade_surplus_driven"
                    description = "Trade surplus providing space for domestic deficits"
            
            # Calculate confidence based on data quality and consistency
            confidence_factors = [
                0.9,  # Base confidence in framework
                0.8 if sectoral_balances.get("identity_hold", False) else 0.6,  # MMT identity holds
                0.85  # Data completeness assumption
            ]
            confidence = np.mean(confidence_factors)
            
            regime_record = {
                "regime": regime,
                "primary_driver": primary_driver,
                "description": description,
                "fiscal_stance": fiscal_stance,
                "private_health": private_health,
                "external_position": external_position,
                "monetary_condition": monetary_condition,
                "confidence": float(confidence),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            self.mmt_regime_history.append(regime_record)
            # Keep only last 100 regime classifications
            if len(self.mmt_regime_history) > 100:
                self.mmt_regime_history = self.mmt_regime_history[-100:]
            
            return regime_record
            
        except Exception as e:
            self.logger.error(f"Error classifying MMT regime: {e}")
            return {"error": str(e)}

    async def _calculate_fiscal_space(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate available fiscal space using MMT principles."""
        try:
            # In MMT, fiscal space for currency-issuing governments is not financially constrained
            # but inflation-constrained and resource-constrained
            
            gdp = float(data.get("gdp", 1000))
            inflation_rate = float(data.get("inflation_rate", 0.02))  # 2% default
            capacity_utilization = float(data.get("capacity_utilization", 0.75))  # 75% default
            unemployment_rate = float(data.get("unemployment_rate", 0.05))  # 5% default
            
            # Inflation constraint: how much additional spending before inflation accelerates
            inflation_gap = max(0, 0.025 - inflation_rate)  # Target 2.5% inflation
            inflation_constrained_spending = gdp * inflation_gap * 2  # Simplified multiplier
            
            # Resource constraint: output gap
            output_gap = 1 - (capacity_utilization / 0.85)  # Assuming 85% is potential
            resource_constrained_spending = gdp * max(0, output_gap)
            
            # Employment constraint: how much spending to reach full employment
            employment_gap = max(0, 0.04 - unemployment_rate)  # Target 4% unemployment
            employment_constrained_spending = gdp * employment_gap * 1.5  # Okun's law approx
            
            # The most binding constraint determines fiscal space
            fiscal_space = min(
                inflation_constrained_spending,
                resource_constrained_spending,
                employed_constrained_spending := employment_constrained_spending
            )
            
            return {
                "gdp": gdp,
                "inflation_rate": inflation_rate,
                "inflation_constraint": max(0, inflation_constrained_spending),
                "capacity_utilization": capacity_utilization,
                "resource_constraint": max(0, resource_constrained_spending),
                "unemployment_rate": unemployment_rate,
                "employment_constraint": max(0, employment_constrained_spending),
                "available_fiscal_space": max(0, fiscal_space),
                "fiscal_space_as_percent_gdp": (max(0, fiscal_space) / gdp * 100) if gdp > 0 else 0,
                "constraint_binding": min(
                    ("inflation", inflation_constrained_spending),
                    ("resource", resource_constrained_spending),
                    ("employment", employment_constrained_spending),
                    key=lambda x: x[1]
                )[0] if max(0, fiscal_space) > 0 else "none"
            }
        except (ValueError, TypeError) as e:
            self.logger.warning(f"Error calculating fiscal space: {e}")
            return {"error": str(e)}

    def _verify_mmt_identity(self, sectoral_balances: Dict[str, Any]) -> Dict[str, Any]:
        """Verify the MMT sectoral balance identity holds."""
        try:
            gov_balance = sectoral_balances.get("government", {}).get("balance", 0)
            private_balance = sectoral_balances.get("private", {}).get("balance", 0)
            foreign_balance = sectoral_balances.get("foreign", {}).get("balance", 0)
            
            identity_sum = gov_balance + private_balance + foreign_balance
            
            return {
                "government_balance": gov_balance,
                "private_balance": private_balance,
                "foreign_balance": foreign_balance,
                "sum": identity_sum,
                "identity_holds": abs(identity_sum) < 0.01,
                "discrepancy": identity_sum
            }
        except Exception as e:
            return {"error": str(e)}

    def _update_historical_data(
        self, 
        sectoral_balances: Dict[str, Any], 
        regime_analysis: Dict[str, Any]
    ) -> None:
        """Update historical data stores."""
        try:
            # Store sectoral balances
            for sector in ["government", "private", "foreign"]:
                balance = sectoral_balances.get(sector, {}).get("balance", 0)
                self.sectoral_balance_history[sector].append(balance)
            
            # Regime history already updated in _classify_mmt_regime
        except Exception as e:
            self.logger.debug(f"Error updating historical data: {e}")

    async def get_sectoral_balance_trend(self, sector: str, periods: int = 10) -> Dict[str, Any]:
        """Get historical trend for a sectoral balance."""
        if sector not in self.sectoral_balance_history:
            return {"error": f"Invalid sector: {sector}"}
        
        history = list(self.sectoral_balance_history[sector])
        if len(history) == 0:
            return {"error": "No historical data available"}
        
        recent = history[-min(periods, len(history)):]
        
        return {
            "sector": sector,
            "periods": len(recent),
            "values": recent,
            "mean": np.mean(recent) if recent else 0,
            "std": np.std(recent) if len(recent) > 1 else 0,
            "trend": "improving" if len(recent) >= 2 and recent[-1] > recent[-2] else "deteriorating" if len(recent) >= 2 and recent[-1] < recent[-2] else "stable"
        }

    async def get_mmt_regime_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent MMT regime classifications."""
        return list(reversed(self.mmt_regime_history[-min(limit, len(self.mmt_regime_history)):]))


get_global_container().register("MonetaryPolicyService", MonetaryPolicyService, singleton=True)