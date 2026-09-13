"""Logging configuration for PixForge."""
from __future__ import annotations

import logging
import logging.handlers
import sys
from pathlib import Path


def setup_logging(log_dir: Path | None = None) -> None:
    """Configure rotating file handler + console handler."""
    if log_dir is None:
        if getattr(sys, "frozen", False):
            base = Path(sys.executable).resolve().parent
        else:
            base = Path.cwd()
        log_dir = base / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / "pixforge.log"

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    # Rotating file handler (5 MB × 3 backups)
    fh = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    fh.setLevel(logging.DEBUG)
    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    fh.setFormatter(fmt)

    # Console handler (WARNING+ only)
    ch = logging.StreamHandler()
    ch.setLevel(logging.WARNING)
    ch.setFormatter(fmt)

    if not root.handlers:
        root.addHandler(fh)
        root.addHandler(ch)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
