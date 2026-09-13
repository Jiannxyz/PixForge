"""Cross-platform helper: open a folder in the native file manager."""
from __future__ import annotations

import logging
import os
import subprocess
import sys
from pathlib import Path

log = logging.getLogger(__name__)


def open_folder(path: Path) -> None:
    """Open *path* in the platform's native file explorer."""
    try:
        if sys.platform == "win32":
            os.startfile(str(path))
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])
    except Exception as exc:  # noqa: BLE001
        log.warning("Could not open folder %s: %s", path, exc)
