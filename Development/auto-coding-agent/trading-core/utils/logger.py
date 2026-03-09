"""
Logger utility module
"""

import logging
import sys
from pathlib import Path
from loguru import logger as _logger
from typing import Optional

# Remove default logger
_logger.remove()

# Add stderr logger with formatting
_logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO",
    colorize=True,
)

# Add file logger
log_file = Path("logs/trading.log")
log_file.parent.mkdir(parents=True, exist_ok=True)

_logger.add(
    log_file,
    rotation="10 MB",
    retention="7 days",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="DEBUG",
)

# Export logger
logger = _logger


def get_logger(name: Optional[str] = None):
    """
    Get a logger instance

    Args:
        name: Optional logger name

    Returns:
        Logger instance
    """
    if name:
        return logger.bind(name=name)
    return logger
