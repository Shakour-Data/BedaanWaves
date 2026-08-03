"""Unit tests for CurrencyConversionService."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from app.services.analysis.currency_conversion_service import CurrencyConversionService


class TestCurrencyConversionServiceInitialization:
    def test_default_service_name(self):
        service = CurrencyConversionService()
        assert service.service_name == "CurrencyConversionService"

    async def test_initialize_logs(self, caplog):
        service = CurrencyConversionService()
        with caplog.at_level("INFO"):
            caplog.clear()
            await service.initialize()
        assert "CurrencyConversionService initialized" in caplog.text
        assert service.session is not None

    async def test_shutdown_logs(self, caplog):
        service = CurrencyConversionService()
        await service.initialize()
        with caplog.at_level("INFO"):
            caplog.clear()
            await service.shutdown()
        assert "CurrencyConversionService shutdown" in caplog.text
        assert service.session.closed


class TestCurrencyConversion:
    async def test_same_currency_identity(self):
        service = CurrencyConversionService()
        await service.initialize()
        result = await service.convert(100.0, "USD", "USD")
        await service.shutdown()
        
        assert result["success"] is True
        assert result["from_currency"] == "USD"
        assert result["to_currency"] == "USD"
        assert result["converted_amount"] == 100.0
        assert result["exchange_rate"] == 1.0
        assert result["methodology"] == "identity_conversion"
        assert result["confidence_interval"]["lower"] == 100.0
        assert result["confidence_interval"]["upper"] == 100.0

    async def test_usd_to_eur_conversion(self):
        service = CurrencyConversionService()
        await service.initialize()
        result = await service.convert(1000.0, "USD", "EUR")
        await service.shutdown()
        
        assert result["success"] is True
        assert result["from_currency"] == "USD"
        assert result["to_currency"] == "EUR"
        assert result["exchange_rate"] == 0.85
        assert result["converted_amount"] == 850.0
        assert "confidence_interval" in result
        assert result["confidence_interval"]["confidence"] == 0.95

    async def test_eur_to_usd_conversion(self):
        service = CurrencyConversionService()
        await service.initialize()
        result = await service.convert(1000.0, "EUR", "USD")
        await service.shutdown()
        
        assert result["success"] is True
        assert result["exchange_rate"] == 1.18
        assert result["converted_amount"] == pytest.approx(1180.0, rel=0.01)

    async def test_cross_rate_via_usd(self):
        service = CurrencyConversionService()
        await service.initialize()
        result = await service.convert(1000.0, "EUR", "GBP")
        await service.shutdown()
        
        assert result["success"] is True
        # EUR -> USD (1.18) -> GBP (0.73) = 0.8614
        assert result["exchange_rate"] == pytest.approx(0.8614, rel=0.01)

    async def test_confidence_level_parameter(self):
        service = CurrencyConversionService()
        await service.initialize()
        result = await service.convert(1000.0, "USD", "EUR", confidence_level=0.99)
        await service.shutdown()
        
        assert result["success"] is True
        assert result["confidence_interval"]["confidence"] == 0.99

    async def test_historical_date_parameter(self):
        service = CurrencyConversionService()
        await service.initialize()
        result = await service.convert(1000.0, "USD", "EUR", date="2025-01-01")
        await service.shutdown()
        
        assert result["success"] is True

    async def test_conversion_methodology(self):
        service = CurrencyConversionService()
        await service.initialize()
        method = await service.get_conversion_methodology("USD")
        await service.shutdown()
        
        assert method["currency"] == "USD"
        assert method["primary_methodology"] == "direct"
        assert "currency_basket_weights" in method
        assert "USD" in method["currency_basket_weights"]

    async def test_managed_float_methodology(self):
        service = CurrencyConversionService()
        await service.initialize()
        method = await service.get_conversion_methodology("CNY")
        await service.shutdown()
        
        assert method["primary_methodology"] == "managed_float"

    async def test_audit_trail_tracking(self):
        service = CurrencyConversionService()
        await service.initialize()
        await service.convert(100.0, "USD", "EUR")
        await service.convert(200.0, "EUR", "GBP")
        
        summary = await service.get_audit_summary()
        await service.shutdown()
        
        assert summary["total_conversions"] == 2
        assert summary["successful_conversions"] == 2
        assert summary["failed_conversions"] == 0
        assert summary["success_rate"] == 1.0

    async def test_get_audit_trail(self):
        service = CurrencyConversionService()
        await service.initialize()
        await service.convert(100.0, "USD", "EUR")
        
        trail = await service.get_audit_trail(limit=10)
        await service.shutdown()
        
        assert len(trail) == 1
        assert trail[0]["operation"] == "currency_conversion"
        assert trail[0]["input"]["from_currency"] == "USD"
        assert trail[0]["input"]["to_currency"] == "EUR"
        assert "audit_id" in trail[0]


class TestErrorHandling:
    async def test_invalid_currency_fallback(self):
        service = CurrencyConversionService()
        await service.initialize()
        result = await service.convert(100.0, "INVALID", "USD")
        await service.shutdown()
        
        # Should fallback to default rate of 1.0
        assert result["success"] is True
        assert result["exchange_rate"] == 1.0