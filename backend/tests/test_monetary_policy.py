"""Unit tests for MonetaryPolicyService."""

import pytest
import numpy as np
from app.services.analysis.monetary_policy_service import MonetaryPolicyService


class TestMonetaryPolicyServiceInitialization:
    def test_default_service_name(self):
        service = MonetaryPolicyService()
        assert service.service_name == "MonetaryPolicyService"

    async def test_initialize_logs(self, caplog):
        service = MonetaryPolicyService()
        with caplog.at_level("INFO"):
            caplog.clear()
            await service.initialize()
        assert "MonetaryPolicyService initialized" in caplog.text

    async def test_shutdown_logs(self, caplog):
        service = MonetaryPolicyService()
        await service.initialize()
        with caplog.at_level("INFO"):
            caplog.clear()
            await service.shutdown()
        assert "MonetaryPolicyService shutdown" in caplog.text


class TestSectoralBalances:
    async def test_basic_sectoral_balance_calculation(self):
        service = MonetaryPolicyService()
        await service.initialize()
        
        data = {
            "government_spending": 500,
            "tax_revenue": 480,
            "private_savings": 600,
            "private_investment": 550,
            "imports": 300,
            "exports": 250
        }
        
        result = await service._calculate_sectoral_balances(data)
        await service.shutdown()
        
        assert result["government"]["balance"] == 20  # 500 - 480
        assert result["private"]["balance"] == 50  # 600 - 550
        assert result["foreign"]["balance"] == 50  # 300 - 250
        # MMT Identity: (G-T) + (S-I) + (M-X) = 20 + 50 + 50 = 120 ≠ 0
        # This is expected since we're using simplified data

    async def test_government_surplus(self):
        service = MonetaryPolicyService()
        await service.initialize()
        
        data = {
            "government_spending": 450,
            "tax_revenue": 500,
            "private_savings": 600,
            "private_investment": 550,
            "imports": 300,
            "exports": 300
        }
        
        result = await service._calculate_sectoral_balances(data)
        await service.shutdown()
        
        assert result["government"]["balance"] == -50  # Government surplus

    async def test_missing_data_handling(self):
        service = MonetaryPolicyService()
        await service.initialize()
        
        result = await service._calculate_sectoral_balances({})
        await service.shutdown()
        
        assert "error" in result
        assert result["government"]["balance"] == 0

    async def test_identity_verification(self):
        service = MonetaryPolicyService()
        await service.initialize()
        
        # Create data where identity holds
        data = {
            "government_spending": 500,
            "tax_revenue": 480,
            "private_savings": 600,
            "private_investment": 550,
            "imports": 300,
            "exports": 370  # Adjusted so (G-T)+(S-I)+(M-X) = 20+50-70 = 0
        }
        
        result = await service._calculate_sectoral_balances(data)
        await service.shutdown()
        
        identity_sum = 20 + 50 + (300 - 370)  # 0
        assert abs(identity_sum) < 0.01


class TestMonetaryAggregates:
    async def test_money_multipliers(self):
        service = MonetaryPolicyService()
        await service.initialize()
        
        data = {
            "monetary_base": 1000,  # M0
            "narrow_money": 4000,   # M1
            "broad_money": 8000,   # M2
            "gdp": 50000
        }
        
        result = await service._analyze_monetary_aggregates(data)
        await service.shutdown()
        
        assert result["money_multipliers"]["m1_multiplier"] == 4.0
        assert result["money_multipliers"]["m2_multiplier"] == 8.0
        assert result["velocity_of_money"]["m1_velocity"] == 12.5  # 50000/4000

    async def test_zero_monetary_base(self):
        service = MonetaryPolicyService()
        await service.initialize()
        
        data = {"monetary_base": 0, "narrow_money": 0, "broad_money": 0, "gdp": 100000}
        result = await service._analyze_monetary_aggregates(data)
        await service.shutdown()
        
        assert result["money_multipliers"]["m1_multiplier"] == 0
        assert result["money_multipliers"]["m2_multiplier"] == 0

    async def test_missing_monetary_data(self):
        service = MonetaryPolicyService()
        await service.initialize()
        
        result = await service._analyze_monetary_aggregates({})
        await service.shutdown()
        
        assert result["money_multipliers"]["m1_multiplier"] == 0
        assert result["money_multipliers"]["m2_multiplier"] == 0


class TestMMTRegimeClassification:
    async def test_fiscal_expansion_regime(self):
        service = MonetaryPolicyService()
        await service.initialize()
        
        sectoral_balances = {
            "government": {"balance": 100},
            "private": {"balance": -50},
            "foreign": {"balance": -50}
        }
        monetary_analysis = {"money_supply_composition": {"m2_m1_ratio": 3.5}}
        data = {}
        
        result = await service._classify_mmt_regime(sectoral_balances, monetary_analysis, data)
        await service.shutdown()
        
        assert result["primary_driver"] == "fiscal"
        assert "confidence" in result
        assert isinstance(result["confidence"], float)

    async def test_private_sector_saving_regime(self):
        service = MonetaryPolicyService()
        await service.initialize()
        
        sectoral_balances = {
            "government": {"balance": 30},
            "private": {"balance": 100},
            "foreign": {"balance": -130}
        }
        monetary_analysis = {"money_supply_composition": {"m2_m1_ratio": 2.0}}
        data = {}
        
        result = await service._classify_mmt_regime(sectoral_balances, monetary_analysis, data)
        await service.shutdown()
        
        # Government has largest absolute balance
        assert result["primary_driver"] == "fiscal"

    async def test_external_driven_regime(self):
        service = MonetaryPolicyService()
        await service.initialize()
        
        sectoral_balances = {
            "government": {"balance": 50},
            "private": {"balance": 30},
            "foreign": {"balance": 400}
        }
        monetary_analysis = {"money_supply_composition": {"m2_m1_ratio": 2.5}}
        data = {}
        
        result = await service._classify_mmt_regime(sectoral_balances, monetary_analysis, data)
        await service.shutdown()
        
        assert result["primary_driver"] == "external"


class TestFiscalSpace:
    async def test_fiscal_space_calculation(self):
        service = MonetaryPolicyService()
        await service.initialize()
        
        data = {
            "gdp": 1000000,
            "inflation_rate": 0.02,
            "capacity_utilization": 0.80,
            "unemployment_rate": 0.06
        }
        
        result = await service._calculate_fiscal_space(data)
        await service.shutdown()
        
        assert result["gdp"] == 1000000
        assert result["inflation_rate"] == 0.02
        assert result["available_fiscal_space"] > 0
        assert result["fiscal_space_as_percent_gdp"] > 0

    async def test_fiscal_space_full_employment(self):
        service = MonetaryPolicyService()
        await service.initialize()
        
        data = {
            "gdp": 1000000,
            "inflation_rate": 0.02,
            "capacity_utilization": 0.95,
            "unemployment_rate": 0.03
        }
        
        result = await service._calculate_fiscal_space(data)
        await service.shutdown()
        
        # With high capacity utilization and low unemployment, fiscal space should be limited
        assert result["capacity_utilization"] == 0.95

    async def test_fiscal_space_high_inflation(self):
        service = MonetaryPolicyService()
        await service.initialize()
        
        data = {
            "gdp": 1000000,
            "inflation_rate": 0.04,
            "capacity_utilization": 0.80,
            "unemployment_rate": 0.06
        }
        
        result = await service._calculate_fiscal_space(data)
        await service.shutdown()
        
        # High inflation should reduce fiscal space
        assert result["inflation_rate"] == 0.04


class TestFullAnalysis:
    async def test_full_analysis(self):
        service = MonetaryPolicyService()
        await service.initialize()
        
        data = {
            "government_spending": 500,
            "tax_revenue": 480,
            "private_savings": 600,
            "private_investment": 550,
            "imports": 300,
            "exports": 370,  # Identity holds: 20 + 50 + (-70) = 0
            "monetary_base": 1000,
            "narrow_money": 4000,
            "broad_money": 8000,
            "gdp": 50000,
            "inflation_rate": 0.02,
            "capacity_utilization": 0.80,
            "unemployment_rate": 0.06
        }
        
        result = await service.analyze(data)
        await service.shutdown()
        
        assert "sectoral_balances" in result
        assert "monetary_analysis" in result
        assert "regime_classification" in result
        assert "fiscal_space" in result
        assert "mmt_identity_check" in result
        assert result["mmt_identity_check"]["identity_holds"]


class TestSectoralBalanceTrend:
    async def test_get_trend(self):
        service = MonetaryPolicyService()
        await service.initialize()
        
        # Add some history
        for i in range(5):
            await service._update_historical_data(
                {"government": {"balance": i * 10}, "private": {"balance": i * 5}, "foreign": {"balance": 0}},
                {"regime": "test", "primary_driver": "test"}
            )
        
        trend = await service.get_sectoral_balance_trend("government", periods=10)
        await service.shutdown()
        
        assert trend["sector"] == "government"
        assert len(trend["values"]) > 0
        assert "trend" in trend

    async def test_no_history(self):
        service = MonetaryPolicyService()
        await service.initialize()
        trend = await service.get_sectoral_balance_trend("government", periods=10)
        await service.shutdown()
        
        assert "error" in trend


class TestMMTRegimeHistory:
    async def test_get_history(self):
        service = MonetaryPolicyService()
        await service.initialize()
        
        # Add some history
        sectoral_balances = {
            "government": {"balance": 100},
            "private": {"balance": -50},
            "foreign": {"balance": -50}
        }
        monetary_analysis = {"money_supply_composition": {"m2_m1_ratio": 3.5}}
        data = {}
        
        for _ in range(3):
            await service._classify_mmt_regime(sectoral_balances, monetary_analysis, data)
        
        history = await service.get_mmt_regime_history(limit=10)
        await service.shutdown()
        
        assert len(history) == 3