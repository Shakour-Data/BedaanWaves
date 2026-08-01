import pytest
import numpy as np
from unittest.mock import MagicMock
from backend.app.services.analysis.structural_break_service import StructuralBreakDetectionService


class TestStructuralBreakDetectionService:
    """Test cases for StructuralBreakDetectionService."""

    @pytest.fixture
    def service(self):
        """Create a service instance for testing."""
        service = StructuralBreakDetectionService()
        service.logger = MagicMock()
        return service

    @pytest.mark.asyncio
    async def test_initialize(self, service):
        """Test service initialization."""
        await service.initialize()
        service.logger.info.assert_called_with("StructuralBreakDetectionService initialized")

    @pytest.mark.asyncio
    async def test_shutdown(self, service):
        """Test service shutdown."""
        await service.shutdown()
        service.logger.info.assert_called_with("StructuralBreakDetectionService shutdown")

    @pytest.mark.asyncio
    async def test_analyze_insufficient_data(self, service):
        """Test analysis with insufficient data."""
        result = await service.analyze({"series": []})
        assert result == {"error": "Insufficient data for structural break detection"}

        result = await service.analyze({"series": [1, 2, 3]})
        assert result == {"error": "Insufficient data for structural break detection"}

    @pytest.mark.asyncio
    async def test_bai_perron_test(self, service):
        """Test Bai-Perron multiple break test."""
        series = [1, 2, 3, 4, 5] * 5 + [10, 12, 15, 18, 20] * 5
        result = await service._bai_perron_test(series)

        assert "break_points" in result
        assert "count" in result
        assert "confidence" in result
        assert "method" in result
        assert result["method"] == "sequential_search"
        assert result["confidence"] >= 0.0

    @pytest.mark.asyncio
    async def test_chow_test(self, service):
        """Test Chow test for structural change."""
        series = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        result = await service._chow_test(series)

        assert "chow_statistic" in result
        assert "p_value" in result
        assert "breakable" in result
        assert "break_point" in result
        assert result["break_point"] == 5

    @pytest.mark.asyncio
    async def test_markov_structure_change(self, service):
        """Test Markov structure change detection."""
        series = list(np.repeat([1, 2, 3, 4, 5], 20))
        result = await service._markov_structure_change(series)

        assert "transition_matrix" in result
        assert "states" in result
        assert "non_stationary" in result
        assert "confidence" in result
        assert result["states"] == ["low", "medium_low", "medium_high", "high"]
        assert isinstance(result["transition_matrix"], list)
        assert all(isinstance(row, list) for row in result["transition_matrix"])

    @pytest.mark.asyncio
    async def test_analyze_with_data(self, service):
        """Test full analysis with sample data."""
        series = [1.0, 2.0, 3.0, 4.0, 5.0] * 10
        result = await service.analyze({"series": series})

        assert "bai_perron" in result
        assert "chow_test" in result
        assert "markov_change" in result

        assert "break_points" in result["bai_perron"]
        assert "chow_statistic" in result["chow_test"]
        assert "transition_matrix" in result["markov_change"]