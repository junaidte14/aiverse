"""
Structured logging configuration

Provides context-aware logging throughout the application
"""

import logging
import sys
from typing import Any, Dict
from datetime import datetime
import json
from pythonjsonlogger import jsonlogger


# ============================================
# CUSTOM LOG FORMATTER
# ============================================


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """
    Custom JSON log formatter

    Adds standard fields to all log records
    """

    def add_fields(
        self, log_record: Dict, record: logging.LogRecord, message_dict: Dict
    ):
        """Add custom fields to log record"""
        super().add_fields(log_record, record, message_dict)

        # Add timestamp
        log_record["timestamp"] = datetime.utcnow().isoformat()

        # Add log level
        log_record["level"] = record.levelname

        # Add logger name
        log_record["logger"] = record.name

        # Add module/function info
        log_record["module"] = record.module
        log_record["function"] = record.funcName
        log_record["line"] = record.lineno


# ============================================
# LOGGER SETUP
# ============================================


def setup_logger(
    name: str = "fastapi_ai_backend", level: int = logging.INFO
) -> logging.Logger:
    """
    Setup structured logger

    Args:
        name: Logger name
        level: Logging level

    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Remove existing handlers
    logger.handlers = []

    # Console handler with JSON formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    # JSON formatter for structured logs
    formatter = CustomJsonFormatter("%(timestamp)s %(level)s %(name)s %(message)s")
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


# ============================================
# CONTEXT LOGGER
# ============================================


class ContextLogger:
    """
    Logger with request context

    Automatically includes request ID, user info, etc. in all logs
    """

    def __init__(self, logger: logging.Logger, context: Dict[str, Any] = None):
        self.logger = logger
        self.context = context or {}

    def _log_with_context(self, level: int, message: str, **kwargs):
        """Log message with context"""
        # Merge context with kwargs
        log_data = {**self.context, **kwargs}

        # Add message
        log_data["message"] = message

        # Log as JSON
        self.logger.log(level, json.dumps(log_data))

    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self._log_with_context(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs):
        """Log info message"""
        self._log_with_context(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self._log_with_context(logging.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs):
        """Log error message"""
        self._log_with_context(logging.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs):
        """Log critical message"""
        self._log_with_context(logging.CRITICAL, message, **kwargs)

    def with_context(self, **additional_context) -> "ContextLogger":
        """Create new logger with additional context"""
        new_context = {**self.context, **additional_context}
        return ContextLogger(self.logger, new_context)


# ============================================
# GLOBAL LOGGER INSTANCE
# ============================================

# Create global logger
logger = setup_logger()

# Example usage:
# logger.info("Application started")
#
# With context:
# context_logger = ContextLogger(logger, {"request_id": "123", "user_id": "456"})
# context_logger.info("User logged in")
