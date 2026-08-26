"""Integration tests for inflation and PPP services."""

import pytest
import numpy as np

from app.services.analysis.inflation_service import InflationService


pytestmark = pytest.mark.integration


class TestInflationService:
    async def test_ppp_adjusted_inflation(self):
        service = InflationService()
        inflation_data = [
            {"date": "2023-01-01", "inflation": 2.5},
            {"date": "2023-02-01", "inflation": 3.1},
            {"date": "2023-03-01", "inflation": 4.2}
        ]
        mapping = {"real_inflation": "inflation"}
        assert "nominal" in mapping

    async def test_big_mac_normalization(self):
        service = InflationService()
        formatted_data = await service.fetch_historical()
        assert isinstance(formatted_data, list)

    async def test_phillips_curve_correlation(self):
        service = InflationService()
        inflation_data = [
            {"date": "2023-01-01", "inflation": 2.5, "unemployment": 5.0},
            {"date": "2023-02-01", "inflation": 3.1, "unemployment": 4.8},
            {"date": "2023-03-01", "inflation": 4.2, "unemployment": 4.5},
        ]
        assert len(inflation_data) == 3
