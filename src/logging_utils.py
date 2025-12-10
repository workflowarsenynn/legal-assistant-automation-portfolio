"""Logging configuration helpers for the intake bot."""
from __future__ import annotations

import logging
from logging import Logger
from pathlib import Path
from typing import Optional


DEFAULT_LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> Logger:
    """Configure application logging with console and optional file handlers."""

    logger = logging.getLogger()
    logger.handlers.clear()

    handlers = [logging.StreamHandler()]

    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_path, encoding="utf-8"))

    logging.basicConfig(level=log_level.upper(), format=DEFAULT_LOG_FORMAT, handlers=handlers)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.INFO)
    return logger
