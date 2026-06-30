"""Logging configuration for the ETL pipeline."""

import logging
from pathlib import Path

from etl.config import LOGS_DIR, LOG_LEVEL


def setup_logging(name: str = "movies_etl") -> logging.Logger:
    """
    Configure and return a logger with file and console handlers.

    Args:
        name: Logger name.

    Returns:
        Configured logger instance.
    """
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOGS_DIR / "etl.log"

    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(LOG_LEVEL)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(LOG_LEVEL)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(LOG_LEVEL)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
