"""
Logger Service - Tier 1 Core Service

Centralized logging management with structured logging support.
Integrates with structlog and Python's logging module.
"""

import logging
from typing import Any, Dict, Optional
from pathlib import Path
from datetime import datetime
import json
from .base_service import BaseService


class LoggerService(BaseService):
    """
    Centralized logging service for BedaanWaves.
    
    Provides:
    - Structured logging
    - Multiple log handlers (console, file, rotating)
    - Log level management
    - Contextual logging
    """
    
    def __init__(
        self,
        service_name: str = "LoggerService",
        log_level: str = "INFO",
        log_dir: Optional[str] = None,
        enable_file: bool = True,
    ):
        """
        Initialize logger service.
        
        Args:
            service_name: Service identifier
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_dir: Directory for log files
            enable_file: Whether to log to files
        """
        super().__init__(service_name)
        self.log_level = self._parse_level(log_level)
        self.log_dir = Path(log_dir) if log_dir else Path.cwd() / 'logs'
        self.enable_file = enable_file
        self._loggers: Dict[str, logging.Logger] = {}
        self._context: Dict[str, Any] = {}
        self._setup_logging()
    
    async def initialize(self) -> None:
        """Initialize logger service"""
        self.logger.info("LoggerService initialized")
    
    async def shutdown(self) -> None:
        """Shutdown logger service"""
        # Close all handlers
        for logger in self._loggers.values():
            for handler in logger.handlers:
                handler.close()
        self.logger.info("LoggerService shutdown")
    
    def _parse_level(self, level: str) -> int:
        """Parse log level string to logging level"""
        levels = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL,
        }
        return levels.get(level.upper(), logging.INFO)
    
    def _setup_logging(self) -> None:
        """Setup logging configuration"""
        # Create log directory if needed
        if self.enable_file:
            self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(self.log_level)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.log_level)
        console_formatter = self._get_formatter(detailed=False)
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
        
        # File handler (if enabled)
        if self.enable_file:
            log_file = self.log_dir / f"bedaanwaves_{datetime.now().strftime('%Y%m%d')}.log"
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(self.log_level)
            file_formatter = self._get_formatter(detailed=True)
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)
    
    def _get_formatter(self, detailed: bool = False) -> logging.Formatter:
        """Get log formatter"""
        if detailed:
            format_str = (
                '[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d] '
                '%(funcName)s() - %(message)s'
            )
        else:
            format_str = '[%(levelname)s] %(name)s - %(message)s'
        
        return logging.Formatter(format_str, datefmt='%Y-%m-%d %H:%M:%S')
    
    def get_logger(self, name: str, module: Optional[str] = None) -> logging.Logger:
        """
        Get or create logger instance.
        
        Args:
            name: Logger name
            module: Optional module name
            
        Returns:
            Logger instance
        """
        logger_name = f"{module}.{name}" if module else name
        
        if logger_name not in self._loggers:
            logger = logging.getLogger(logger_name)
            logger.setLevel(self.log_level)
            self._loggers[logger_name] = logger
        
        return self._loggers[logger_name]
    
    def set_context(self, key: str, value: Any) -> None:
        """Set contextual information"""
        self._context[key] = value
    
    def get_context(self) -> Dict[str, Any]:
        """Get current context"""
        return self._context.copy()
    
    def clear_context(self) -> None:
        """Clear contextual information"""
        self._context.clear()
    
    def log_structured(
        self,
        logger_name: str,
        level: str,
        message: str,
        **kwargs
    ) -> None:
        """
        Log structured data.
        
        Args:
            logger_name: Logger name
            level: Log level
            message: Log message
            **kwargs: Additional fields
        """
        logger = self.get_logger(logger_name)
        
        # Combine context with kwargs
        data = {**self._context, **kwargs}
        
        # Format as JSON
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'message': message,
            **data
        }
        
        log_method = getattr(logger, level.lower(), logger.info)
        log_method(json.dumps(log_data, default=str))
    
    def log_error(
        self,
        logger_name: str,
        error: Exception,
        message: Optional[str] = None,
        **kwargs
    ) -> None:
        """
        Log error with traceback.
        
        Args:
            logger_name: Logger name
            error: Exception instance
            message: Additional message
            **kwargs: Additional fields
        """
        logger = self.get_logger(logger_name)
        log_message = message or str(error)
        logger.exception(log_message)
        
        self.log_structured(
            logger_name,
            'error',
            log_message,
            error_type=type(error).__name__,
            **kwargs
        )
    
    def log_performance(
        self,
        logger_name: str,
        operation: str,
        duration_ms: float,
        success: bool = True,
        **kwargs
    ) -> None:
        """
        Log performance metrics.
        
        Args:
            logger_name: Logger name
            operation: Operation name
            duration_ms: Duration in milliseconds
            success: Whether operation succeeded
            **kwargs: Additional fields
        """
        self.log_structured(
            logger_name,
            'info' if success else 'warning',
            f"Performance: {operation}",
            operation=operation,
            duration_ms=duration_ms,
            success=success,
            **kwargs
        )
    
    def set_level(self, level: str) -> None:
        """Change logging level"""
        new_level = self._parse_level(level)
        logging.getLogger().setLevel(new_level)
        self.logger.info(f"Log level changed to {level}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get logger statistics"""
        return {
            'active_loggers': len(self._loggers),
            'log_level': logging.getLevelName(self.log_level),
            'log_directory': str(self.log_dir),
            'context_fields': len(self._context),
        }
