import pytest
from app.application.services.config_service import ConfigService

class TestConfigService:
    """Unit tests for ConfigService."""

    def test_get_string_ExistingKey_ReturnsValue(self):
        # Arrange
        env = {"TEST_KEY": "test_value"}
        service = ConfigService(env_vars=env)

        # Act
        value = service.get_string("TEST_KEY")

        # Assert
        assert value == "test_value"

    def test_get_int_ValidInt_ReturnsInt(self):
        # Arrange
        env = {"PORT": "8080"}
        service = ConfigService(env_vars=env)

        # Act
        value = service.get_int("PORT")

        # Assert
        assert value == 8080

    def test_get_bool_TrueValue_ReturnsTrue(self):
        # Arrange
        env = {"DEBUG": "true"}
        service = ConfigService(env_vars=env)

        # Act
        value = service.get_bool("DEBUG")

        # Assert
        assert value is True

    def test_get_section_Database_ReturnsValidDict(self):
        # Arrange
        env = {
            "DB_HOST": "db.local",
            "DB_PORT": "5432"
        }
        service = ConfigService(env_vars=env)

        # Act
        result = service.get_section("database")

        # Assert
        assert result.is_success is True
        assert result.value["host"] == "db.local"
        assert result.value["port"] == 5432
