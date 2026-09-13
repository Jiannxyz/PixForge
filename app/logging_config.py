"""Application logging. Never log image contents."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from app.config import APP_NAME, LOG_DIR, LOG_FILE


def configure_logging(level: int = logging.INFO) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("app")
    if logger.handlers:
        return
    logger.setLevel(level)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")

    file_handler = RotatingFileHandler(LOG_FILE, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    file_handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    logger.info("%s logging started", APP_NAME)
