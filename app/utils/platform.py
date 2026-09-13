"""Small platform helpers for later GUI use."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def cpu_count(default: int = 4) -> int:
    return os.cpu_count() or default


def default_output_dir() -> Path:
    pictures = Path.home() / "Pictures"
    if pictures.is_dir():
        return pictures / "PixForge"
    return Path.home() / "PixForge"


def is_windows() -> bool:
    return sys.platform.startswith("win")
