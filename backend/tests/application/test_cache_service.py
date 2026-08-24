import pytest
from unittest.mock import AsyncMock
from app.application.services.cache_service import CacheService
from app.application.interfaces.i_cache_backend import ICacheBackend

class TestCacheService:
    """Unit tests for CacheService following AAA pattern."""

    @pytest.fixture
    def mock_backend(self):
        return AsyncMock(spec=ICacheBackend)

    @pytest.fixture
    def cache_service(self, mock_backend):
        return CacheService(backend=mock_backend, default_ttl=100)

    @pytest.mark.asyncio
    async def test_get_ExistingKey_ReturnsSuccessResult(self, cache_service, mock_backend):
        # Arrange
        key = "test_key"
        value = "test_value"
        mock_backend.get.return_value = value

        # Act
        result = await cache_service.get(key)

        # Assert
        assert result.is_success is True
        assert result.value == value
        mock_backend.get.assert_called_once_with(f"default:{key}")

    @pytest.mark.asyncio
    async def test_get_MissingKey_ReturnsFailureResult(self, cache_service, mock_backend):
        # Arrange
        key = "missing_key"
        mock_backend.get.return_value = None

        # Act
        result = await cache_service.get(key)

        # Assert
        assert result.is_failure is True
        assert result.error_code == "CACHE_MISS"

    @pytest.mark.asyncio
    async def test_set_ValidInput_CallsBackendSet(self, cache_service, mock_backend):
        # Arrange
        key = "new_key"
        value = "new_value"

        # Act
        result = await cache_service.set(key, value)

        # Assert
        assert result.is_success is True
        mock_backend.set.assert_called_once_with(f"default:{key}", value, 100)

    @pytest.mark.asyncio
    async def test_delete_ValidKey_CallsBackendDelete(self, cache_service, mock_backend):
        # Arrange
        key = "delete_me"

        # Act
        result = await cache_service.delete(key)

        # Assert
        assert result.is_success is True
        mock_backend.delete.assert_called_once_with(f"default:{key}")
