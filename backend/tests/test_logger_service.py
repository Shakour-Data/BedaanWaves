"""Unit tests for Tier 1 LoggerService."""

import json
import logging

import pytest

from app.services.core.logger_service import LoggerService

pytestmark = pytest.mark.unit


class TestLoggerLevelParsing:
    @pytest.mark.parametrize(
        "level,expected",
        [
            ("DEBUG", logging.DEBUG),
            ("info", logging.INFO),
            ("Warning", logging.WARNING),
            ("ERROR", logging.ERROR),
            ("CRITICAL", logging.CRITICAL),
            ("unknown", logging.INFO),
        ],
    )
    def test_parse_level(self, logger_service, level, expected):
        assert logger_service._parse_level(level) == expected


class TestLoggerCreation:
    def test_get_logger_returns_logger(self, logger_service):
        logger = logger_service.get_logger("mymodule")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "mymodule"

    def test_get_logger_with_module_prefix(self, logger_service):
        logger = logger_service.get_logger("name", module="pkg")
        assert logger.name == "pkg.name"

    def test_get_logger_is_cached(self, logger_service):
        a = logger_service.get_logger("same")
        b = logger_service.get_logger("same")
        assert a is b
        assert len(logger_service._loggers) == 1


class TestLoggerContext:
    def test_set_and_get_context(self, logger_service):
        logger_service.set_context("request_id", "abc123")
        assert logger_service.get_context() == {"request_id": "abc123"}

    def test_get_context_returns_copy(self, logger_service):
        logger_service.set_context("k", "v")
        ctx = logger_service.get_context()
        ctx["k"] = "mutated"
        assert logger_service.get_context()["k"] == "v"

    def test_clear_context(self, logger_service):
        logger_service.set_context("k", "v")
        logger_service.clear_context()
        assert logger_service.get_context() == {}


class TestLoggerStructured:
    def test_log_structured_emits_json(self, logger_service, caplog):
        logger_service.set_level("DEBUG")
        with caplog.at_level(logging.INFO):
            logger_service.log_structured("test.logger", "info", "hello", user="alice")
        # find a record whose message is valid JSON containing our fields
        matched = False
        for record in caplog.records:
            try:
                payload = json.loads(record.getMessage())
            except (ValueError, TypeError):
                continue
            if payload.get("message") == "hello" and payload.get("user") == "alice":
                matched = True
        assert matched

    def test_log_structured_merges_context(self, logger_service, caplog):
        logger_service.set_context("session", "s1")
        with caplog.at_level(logging.INFO):
            logger_service.log_structured("test.logger", "info", "msg")
        assert any("s1" in r.getMessage() for r in caplog.records)

    def test_log_error(self, logger_service, caplog):
        with caplog.at_level(logging.ERROR):
            logger_service.log_error("test.logger", ValueError("bad"), "custom message")
        assert any("custom message" in r.getMessage() for r in caplog.records)

    def test_log_performance(self, logger_service, caplog):
        with caplog.at_level(logging.INFO):
            logger_service.log_performance("test.logger", "op", 12.5, success=True)
        assert any("Performance" in r.getMessage() for r in caplog.records)


class TestLoggerLevelAndStats:
    def test_set_level(self, logger_service):
        logger_service.set_level("ERROR")
        assert logging.getLogger().level == logging.ERROR

    def test_get_stats(self, logger_service):
        logger_service.get_logger("a")
        logger_service.set_context("k", "v")
        stats = logger_service.get_stats()
        assert stats["active_loggers"] == 1
        assert stats["context_fields"] == 1
        assert "log_level" in stats


class TestLoggerFileMode:
    def test_file_handler_creates_directory(self, tmp_path):
        log_dir = tmp_path / "app_logs"
        LoggerService(log_level="INFO", log_dir=str(log_dir), enable_file=True)
        assert log_dir.exists()


class TestLoggerLifecycle:
    async def test_initialize_and_shutdown(self, logger_service):
        await logger_service.initialize()
        logger_service.get_logger("x")
        await logger_service.shutdown()
