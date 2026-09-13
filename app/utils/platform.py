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


def open_folder(path: Path | str) -> bool:
    """Open a folder in the operating system's native file explorer."""
    import subprocess

    target = Path(path).resolve()
    if not target.exists():
        target.mkdir(parents=True, exist_ok=True)

    try:
        if sys.platform.startswith("win"):
            os.startfile(str(target))
            return True
        if sys.platform == "darwin":
            subprocess.Popen(["open", str(target)])
            return True
        subprocess.Popen(["xdg-open", str(target)])
        return True
    except Exception:
        return False

