"""Logging configuration for LLM Tester."""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import TextIO


def setup_logging(
    level: str = "INFO",
    log_file: str | Path | None = None,
    enable_file_logging: bool = False,
) -> logging.Logger:
    """Configure logging for the application.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (optional)
        enable_file_logging: Whether to enable file logging

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger("llm_tester")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Remove existing handlers
    logger.handlers.clear()

    # Console handler with formatting
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # File handler if enabled
    if enable_file_logging and log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str | None = None) -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Logger name (defaults to 'llm_tester')

    Returns:
        Logger instance
    """
    return logging.getLogger(name or "llm_tester")


__all__ = ["setup_logging", "get_logger"]
