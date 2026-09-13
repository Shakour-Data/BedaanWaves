import pytest

from app.infrastructure.database.multi_db_manager import DatabaseRole, MultiDatabaseManager


class TestMultiDatabaseManager:
    @pytest.fixture
    def manager(self):
        return MultiDatabaseManager()

    async def test_get_session_factory_before_init_raises(self, manager):
        with pytest.raises(RuntimeError, match="not initialized"):
            manager.get_session_factory(DatabaseRole.CORE)

    async def test_get_stats_before_init(self, manager):
        stats = manager.get_stats()
        assert stats["initialized"] is False
        assert stats["roles"] == []
