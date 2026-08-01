import pytest
from unittest.mock import MagicMock
from app.services.analysis.crypto_industry_service import CryptoIndustryMapperService


class TestCryptoIndustryMapperService:
    """Test cases for CryptoIndustryMapperService."""

    @pytest.fixture
    def service(self):
        """Create a service instance for testing."""
        service = CryptoIndustryMapperService()
        service.logger = MagicMock()
        return service

    @pytest.mark.asyncio
    async def test_initialize(self, service):
        """Test service initialization."""
        await service.initialize()
        service.logger.info.assert_called_with("CryptoIndustryMapperService initialized")

    @pytest.mark.asyncio
    async def test_shutdown(self, service):
        """Test service shutdown."""
        await service.shutdown()
        service.logger.info.assert_called_with("CryptoIndustryMapperService shutdown")

    @pytest.mark.asyncio
    async def test_classify_asset_btc(self, service):
        """Test classification of Bitcoin."""
        result = await service.classify_asset("btc")

        assert result["layer"] == "settlement"
        assert result["function"] == "digital_gold"
        assert result["usage"] == "store_of_value"
        assert result["risk_profile"] == "high"
        assert result["theme"] == "monetary"

    @pytest.mark.asyncio
    async def test_classify_asset_eth(self, service):
        """Test classification of Ethereum."""
        result = await service.classify_asset("eth")

        assert result["layer"] == "smart_contract_platform"
        assert result["function"] == "smart_contract"
        assert result["usage"] == "programmable_money"
        assert result["theme"] == "technology"

    @pytest.mark.asyncio
    async def test_classify_asset_stablecoin(self, service):
        """Test classification of stablecoins."""
        for symbol in ["usdc", "usdt"]:
            result = await service.classify_asset(symbol)
            assert result["risk_profile"] == "low"
            assert result["function"] == "stablecoin"
            assert result["theme"] == "stablecoin"

    @pytest.mark.asyncio
    async def test_classify_asset_privacy(self, service):
        """Test classification of privacy coins."""
        result = await service.classify_asset("xmr")
        assert result["risk_profile"] == "high"
        assert result["theme"] == "privacy"

    @pytest.mark.asyncio
    async def test_classify_asset_unknown(self, service):
        """Test classification of unknown asset."""
        result = await service.classify_asset("unknown")

        assert result["layer"] == "other"
        assert result["function"] == "other"
        assert result["usage"] == "trading"
        assert result["theme"] == "other"

    @pytest.mark.asyncio
    async def test_classify_asset_case_insensitive(self, service):
        """Test classification is case-insensitive."""
        result_lower = await service.classify_asset("btc")
        result_upper = await service.classify_asset("BTC")
        assert result_lower == result_upper

    @pytest.mark.asyncio
    async def test_analyze_multiple_assets(self, service):
        """Test analysis of multiple assets."""
        assets = ["btc", "eth", "usdc", "xmr"]
        result = await service.analyze({"assets": assets})

        assert "classifications" in result
        assert len(result["classifications"]) == 4
        assert "btc" in result["classifications"]
        assert "eth" in result["classifications"]
        assert "usdc" in result["classifications"]
        assert "xmr" in result["classifications"]

    @pytest.mark.asyncio
    async def test_get_cross_asset_industries(self, service):
        """Test cross-asset industry buckets."""
        result = await service.get_cross_asset_industries()

        assert "digital_assets" in result
        assert "blockchain_infrastructure" in result
        assert "decentralized_finance" in result
        assert "digital_payments" in result
        assert "privacy_computing" in result
        assert "scaling_solutions" in result
        assert "technology_sector_stocks" in result
        assert "financial_services_stocks" in result
        assert "commodity_mining_stocks" in result

    def test_tiers(self, service):
        """Test that the 5-tier hierarchy is defined."""
        assert service.TIERS == ["layer", "function", "usage", "risk_profile", "theme"]
        assert len(service.TIERS) == 5

    def test_layer_map(self, service):
        """Test layer mapping contains expected entries."""
        assert "btc" in service.LAYER_MAP
        assert "eth" in service.LAYER_MAP
        assert service.LAYER_MAP["btc"] == "settlement"

    def test_function_map(self, service):
        """Test function mapping contains expected entries."""
        assert "btc" in service.FUNCTION_MAP
        assert "eth" in service.FUNCTION_MAP
        assert service.FUNCTION_MAP["btc"] == "digital_gold"

    def test_usage_map(self, service):
        """Test usage mapping contains expected entries."""
        assert "btc" in service.USAGE_MAP
        assert "eth" in service.USAGE_MAP

    def test_theme_map(self, service):
        """Test theme mapping contains expected entries."""
        assert "btc" in service.THEME_MAP
        assert "eth" in service.THEME_MAP
        assert service.THEME_MAP["btc"] == "monetary"