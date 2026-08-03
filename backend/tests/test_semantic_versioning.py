"""Unit tests for SemanticVersioningService."""

import pytest
from app.services.analysis.semantic_versioning_service import SemanticVersioningService


class TestSemanticVersioningInitialization:
    async def test_default_service_name(self):
        service = SemanticVersioningService()
        assert service.get_service_name() == "SemanticVersioningService"

    async def test_initialize_logs(self, caplog):
        service = SemanticVersioningService()
        with caplog.at_level("INFO"):
            caplog.clear()
            await service.initialize()
        assert "SemanticVersioningService initialized" in caplog.text

    async def test_shutdown_logs(self, caplog):
        service = SemanticVersioningService()
        await service.initialize()
        with caplog.at_level("INFO"):
            caplog.clear()
            await service.shutdown()
        assert "SemanticVersioningService shutdown" in caplog.text


class TestSemanticVersioningMethods:
    async def test_check_version_compatibility(self):
        service = SemanticVersioningService()
        await service.check_version_compatibility("1.0.0", "1.0.0")  # Same version
        await service.check_version_compatibility("1.0.1", "1.0.0")  # Higher patch
        await service.check_version_compatibility("0.9.9", "1.0.0")  # Lower minor
        await service.check_version_compatibility("2.0.0", "1.0.0")  # Higher major
}