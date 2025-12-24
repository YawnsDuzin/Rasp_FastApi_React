"""
Logging Configuration
=====================

Configures structured logging for the HMI application.
Supports both file and console logging with JSON format option.
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime
from pythonjsonlogger import jsonlogger

from .config import settings


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields."""

    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record["timestamp"] = datetime.utcnow().isoformat()
        log_record["level"] = record.levelname
        log_record["logger"] = record.name
        log_record["module"] = record.module
        log_record["function"] = record.funcName
        log_record["line"] = record.lineno


def setup_logging() -> logging.Logger:
    """
    Set up application logging.

    Returns:
        Root logger instance
    """
    # Create logs directory
    log_dir = settings.LOG_DIR
    log_dir.mkdir(parents=True, exist_ok=True)

    # Get root logger
    logger = logging.getLogger("hmi")
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    logger.handlers = []  # Clear existing handlers

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    console_format = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # File Handler (Rotating)
    file_handler = RotatingFileHandler(
        log_dir / "hmi.log",
        maxBytes=settings.LOG_MAX_SIZE,
        backupCount=settings.LOG_BACKUP_COUNT,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(console_format)
    logger.addHandler(file_handler)

    # JSON File Handler (for structured logging)
    json_handler = RotatingFileHandler(
        log_dir / "hmi_json.log",
        maxBytes=settings.LOG_MAX_SIZE,
        backupCount=settings.LOG_BACKUP_COUNT,
        encoding="utf-8"
    )
    json_handler.setLevel(logging.INFO)
    json_handler.setFormatter(CustomJsonFormatter())
    logger.addHandler(json_handler)

    # Error File Handler
    error_handler = RotatingFileHandler(
        log_dir / "hmi_error.log",
        maxBytes=settings.LOG_MAX_SIZE,
        backupCount=settings.LOG_BACKUP_COUNT,
        encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(console_format)
    logger.addHandler(error_handler)

    logger.info(f"Logging initialized. Level: {settings.LOG_LEVEL}, Dir: {log_dir}")
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(f"hmi.{name}")
