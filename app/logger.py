"""
Centralized logging configuration with structured logging support.
"""
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Any
from logging.handlers import RotatingFileHandler

from app.config import get_settings

settings = get_settings()


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data, default=str)


class StandardFormatter(logging.Formatter):
    """Standard text formatter for console output."""
    
    def __init__(self):
        super().__init__(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )


def setup_logger(name: str = "app") -> logging.Logger:
    """
    Set up and configure logger with both file and console handlers.
    
    Args:
        name: Logger name
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    
    if settings.LOG_FORMAT == "json":
        console_handler.setFormatter(JSONFormatter())
    else:
        console_handler.setFormatter(StandardFormatter())
    
    logger.addHandler(console_handler)
    
    # File handler with rotation
    log_file = Path(settings.LOG_FILE)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Parse rotation size (e.g., "500 MB")
    max_bytes = 500 * 1024 * 1024  # Default 500 MB
    if "MB" in settings.LOG_ROTATION:
        max_bytes = int(settings.LOG_ROTATION.split()[0]) * 1024 * 1024
    
    file_handler = RotatingFileHandler(
        filename=log_file,
        maxBytes=max_bytes,
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    
    if settings.LOG_FORMAT == "json":
        file_handler.setFormatter(JSONFormatter())
    else:
        file_handler.setFormatter(StandardFormatter())
    
    logger.addHandler(file_handler)
    
    return logger


def log_with_context(logger: logging.Logger, level: str, message: str, **kwargs: Any) -> None:
    """
    Log message with additional context fields.
    
    Args:
        logger: Logger instance
        level: Log level (info, warning, error, etc.)
        message: Log message
        **kwargs: Additional context fields
    """
    log_method = getattr(logger, level.lower())
    
    # Create a log record with extra fields
    extra = {"extra_fields": kwargs} if kwargs else {}
    log_method(message, extra=extra)


# Create default logger instance
logger = setup_logger()
