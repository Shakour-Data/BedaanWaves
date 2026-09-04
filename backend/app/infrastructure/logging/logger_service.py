import logging
import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from ...application.interfaces.i_logger import ILogger
from app.core.utils import utc_now_iso

class LoggerService(ILogger):
    """
    Concrete implementation of ILogger.
    Handles structured logging and console/file output.
    """
    
    def __init__(self, name: str, level: str = "INFO"):
        self._logger = logging.getLogger(name)
        self._logger.setLevel(self._parse_level(level))
        self._context: Dict[str, Any] = {}

    def debug(self, message: str, **kwargs) -> None:
        self._log("debug", message, **kwargs)

    def info(self, message: str, **kwargs) -> None:
        self._log("info", message, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        self._log("warning", message, **kwargs)

    def error(self, message: str, error: Optional[Exception] = None, **kwargs) -> None:
        if error:
            kwargs["error_type"] = type(error).__name__
            kwargs["error_message"] = str(error)
        self._log("error", message, **kwargs)

    def critical(self, message: str, error: Optional[Exception] = None, **kwargs) -> None:
        if error:
            kwargs["error_type"] = type(error).__name__
            kwargs["error_message"] = str(error)
        self._log("critical", message, **kwargs)

    def _log(self, level: str, message: str, **kwargs) -> None:
        """Internal structured logging logic."""
        log_data = {
            "timestamp": utc_now_iso(),
            "level": level.upper(),
            "message": message,
            "context": self._context,
            "extra": kwargs
        }
        log_method = getattr(self._logger, level)
        log_method(json.dumps(log_data))

    def _parse_level(self, level: str) -> int:
        return getattr(logging, level.upper(), logging.INFO)
