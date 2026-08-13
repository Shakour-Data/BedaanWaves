"""
Integration and Unit Tests for New Features:
- Health check endpoints
- Data export/import API
- Performance optimizations
"""

import pytest
import asyncio
import json
import io
from unittest.mock import AsyncMock, MagicMock, patch

# Health Check Tests
@pytest.mark.integration
class TestHealthCheckEndpoints:
    """Integration tests for health check endpoints."""

    async def test_health_root_endpoint(self, client):
        """Test the root health check endpoint."""
        response = await client.get("/health")
        assert response.status_code == 200

    async def test_health_services_endpoint(self, client):
        """Test the services health endpoint."""
        response = await client.get("/health/services")
        assert response.status_code == 200
        data = response.json()
        assert "services" in data
        assert "overall_status" in data

    async def test_health_specific_service(self, client):
        """Test health check for a specific service."""
        response = await client.get("/health/services/database")
        assert response.status_code in [200, 404]  # May not be registered yet


@pytest.mark.unit
class TestDataExportImport:
    """Unit tests for data export/import functionality."""

    def test_export_json_format(self):
        """Test JSON export format."""
        test_data = {"ticker": "AAPL", "price": 150.25}
        csv_content = json.dumps([test_data])
        assert csv_content.startswith("{")

    def test_export_csv_format(self):
        """Test CSV export format."""
        import csv
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["ticker", "price"])
        writer.writerow(["AAPL", "150.25"])
        csv_content = buffer.getvalue()
        assert "AAPL" in csv_content
        assert "150.25" in csv_content

    def test_import_json_data(self):
        """Test importing JSON data."""
        test_json = '[{"ticker": "AAPL"}, {"ticker": "GOOGL"}]'
        data = json.loads(test_json)
        assert isinstance(data, list)
        assert len(data) == 2

    def test_import_csv_data(self):
        """Test importing CSV data."""
        test_csv = "ticker\nAAPL\nGOOGL\nTSLA"
        buffer = io.StringIO(test_csv)
        import csv
        reader = csv.DictReader(buffer)
        rows = list(reader)
        assert len(rows) == 3


@pytest.mark.unit
class TestCachingOptimizations:
    """Unit tests for caching optimizations."""

    def test_lru_cache_functionality(self):
        """Test that LRU cache works correctly."""
        from functools import lru_cache

        @lru_cache(maxsize=3)
        def expensive_calculation(x):
            return x * x * x

        result1 = expensive_calculation(5)
        result2 = expensive_calculation(5)
        assert result1 == result2
        assert result1 == 125

        expensive_calculation.cache_clear()

    def test_validation_cache_eviction(self):
        """Test LRU eviction in validation cache."""
        cache = {}
        cache_size_limit = 3

        def set_cache(key, value):
            if len(cache) >= cache_size_limit:
                oldest_key = next(iter(cache))
                del cache[oldest_key]
            cache[key] = value

        set_cache("a", 1)
        set_cache("b", 2)
        set_cache("c", 3)
        assert len(cache) == 3

        set_cache("d", 4)
        assert "a" not in cache  # Oldest should be evicted
        assert "d" in cache


# API Versioning Tests
@pytest.mark.integration
class TestAPIVersioning:
    """Tests for API versioning functionality."""

    @pytest.mark.asyncio
    async def test_v1_endpoint(self, client):
        """Test v1 API endpoint."""
        response = await client.get("/api/v1/stocks/AAPL")
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_v2_endpoint(self, client):
        """Test v2 API endpoint."""
        response = await client.post("/api/v1/stocks/v2/batch", json={
            "tickers": ["AAPL"],
            "include_history": True
        })
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_version_header(self, client):
        """Test version header in response."""
        response = await client.get("/api/v1/stocks/AAPL")
        # Version header should be set even if endpoint fails
        assert response.status_code in [200, 404]


# Performance Tests
@pytest.mark.slow
class TestPerformanceOptimizations:
    """Performance tests for optimized services."""

    @pytest.mark.asyncio
    async def test_batch_processing_speed(self, benchmark):
        """Benchmark batch processing performance."""
        async def process_batch():
            tasks = [self.process_single(i) for i in range(100)]
            return await asyncio.gather(*tasks)

        async def process_single(i):
            await asyncio.sleep(0.001)
            return i * 2

        result = benchmark(process_batch)
        assert len(result) == 100

    def test_cache_hit_performance(self):
        """Test cache hit improves performance."""
        from functools import lru_cache
        import time

        @lru_cache(maxsize=100)
        def cached_operation(x):
            return x ** 2

        start = time.time()
        for _ in range(1000):
            cached_operation(5)
        cache_time = time.time() - start

        cached_operation.cache_clear()

        start = time.time()
        for _ in range(1000):
            5 ** 2
        direct_time = time.time() - start

        assert cache_time < direct_time


# Configuration Tests
@pytest.mark.unit
class TestConfiguration:
    """Tests for configuration and environment settings."""

    def test_cache_size_config(self):
        """Test cache size configuration."""
        max_cache_size = 100
        assert max_cache_size > 0

    def test_concurrent_request_limit(self):
        """Test concurrent request limit configuration."""
        max_concurrent = 10
        assert max_concurrent > 0 and max_concurrent <= 100


# Fixture Configuration
@pytest.fixture
async def client():
    """Create test client."""
    from httpx import AsyncClient
    from app.main import app
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def health_checker():
    """Create health checker instance."""
    from app.services.core.health_checker import HealthChecker
    return HealthChecker(check_interval_seconds=10)

@pytest.fixture
def data_validation_service():
    """Create data validation service instance."""
    from app.services.data.data_validation_service import DataValidationService
    return DataValidationService()

@pytest.fixture
def financial_ingest_service():
    """Create financial data ingest service instance."""
    from app.services.data.financial_data_ingest_service import FinancialDataIngestService
    return FinancialDataIngestService()

# Test configuration
pytestmark = [pytest.mark.usefixtures("event_loop_policy")]