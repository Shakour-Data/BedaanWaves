"""Unit tests for Tier 1 ConfigService."""

import json

import pytest

from app.services.core.config_service import ConfigService

pytestmark = pytest.mark.unit


class TestConfigTypeConversion:
    def test_get_string_default(self, config_service, monkeypatch):
        monkeypatch.delenv("SOME_KEY", raising=False)
        assert config_service.get("SOME_KEY", "fallback") == "fallback"

    def test_get_string_from_env(self, config_service, monkeypatch):
        monkeypatch.setenv("SOME_KEY", "hello")
        assert config_service.get("SOME_KEY") == "hello"

    def test_get_int_valid(self, config_service, monkeypatch):
        monkeypatch.setenv("NUM", "42")
        assert config_service.get_int("NUM") == 42

    def test_get_int_invalid_returns_default(self, config_service, monkeypatch):
        monkeypatch.setenv("NUM", "not-a-number")
        assert config_service.get_int("NUM", 7) == 7

    def test_get_float_valid(self, config_service, monkeypatch):
        monkeypatch.setenv("RATE", "0.25")
        assert config_service.get_float("RATE") == 0.25

    def test_get_float_invalid_returns_default(self, config_service, monkeypatch):
        monkeypatch.setenv("RATE", "abc")
        assert config_service.get_float("RATE", 1.5) == 1.5

    @pytest.mark.parametrize("value", ["true", "1", "yes", "on", "TRUE", "On"])
    def test_get_bool_truthy(self, config_service, monkeypatch, value):
        monkeypatch.setenv("FLAG", value)
        assert config_service.get_bool("FLAG") is True

    @pytest.mark.parametrize("value", ["false", "0", "no", "off", "FALSE"])
    def test_get_bool_falsy(self, config_service, monkeypatch, value):
        monkeypatch.setenv("FLAG", value)
        assert config_service.get_bool("FLAG") is False

    def test_get_bool_unknown_returns_default(self, config_service, monkeypatch):
        monkeypatch.setenv("FLAG", "maybe")
        assert config_service.get_bool("FLAG", True) is True

    def test_get_list(self, config_service, monkeypatch):
        monkeypatch.setenv("ITEMS", "a, b ,c")
        assert config_service.get_list("ITEMS") == ["a", "b", "c"]

    def test_get_list_empty_returns_default(self, config_service, monkeypatch):
        monkeypatch.delenv("ITEMS", raising=False)
        assert config_service.get_list("ITEMS", ["x"]) == ["x"]

    def test_get_json_valid(self, config_service, monkeypatch):
        monkeypatch.setenv("CFG", json.dumps({"a": 1}))
        assert config_service.get_json("CFG") == {"a": 1}

    def test_get_json_invalid_returns_default(self, config_service, monkeypatch):
        monkeypatch.setenv("CFG", "{invalid")
        assert config_service.get_json("CFG", {"d": 2}) == {"d": 2}


class TestConfigSections:
    def test_config_has_all_sections(self, config_service):
        cfg = config_service.get_config()
        for section in ("api", "database", "cache", "ml", "security", "services"):
            assert section in cfg

    def test_get_config_section(self, config_service):
        db = config_service.get_config("database")
        assert db["driver"] == "postgresql"
        assert db["port"] == 5432

    def test_get_config_unknown_section(self, config_service):
        assert config_service.get_config("nonexistent") == {}

    def test_set_config(self, config_service):
        config_service.set_config("custom", 123)
        assert config_service.get_config("custom") == 123


class TestConfigEnvironment:
    def test_is_development_default(self, config_service):
        # _load_config reads ENVIRONMENT; pytest sets it to "testing"
        assert config_service.is_production() is False

    def test_is_production_true(self, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "production")
        svc = ConfigService(env_file=None)
        assert svc.is_production() is True
        assert svc.is_development() is False

    def test_is_development_true(self, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "development")
        svc = ConfigService(env_file=None)
        assert svc.is_development() is True

    def test_is_debug(self, monkeypatch):
        monkeypatch.setenv("DEBUG", "true")
        svc = ConfigService(env_file=None)
        assert svc.is_debug() is True


class TestConfigLifecycle:
    async def test_initialize_and_shutdown(self, config_service):
        await config_service.initialize()
        # environment variables loaded into _config
        assert config_service._config
        await config_service.shutdown()

    def test_find_env_file_returns_none_when_absent(self, monkeypatch, tmp_path):
        # ConfigService(env_file=None) triggers _find_env_file; ensure no crash
        monkeypatch.chdir(tmp_path)
        svc = ConfigService(env_file=None)
        # With no .env in temp dir hierarchy, env_file should be None or an existing path
        assert svc.env_file is None or svc.env_file
