"""Input validators — extension and path safety checks."""
from __future__ import annotations

from pathlib import Path

from app.formats import is_supported_input


def is_valid_image_path(path: Path) -> bool:
    """Return True if path is a file with a supported extension."""
    return path.is_file() and is_supported_input(path.suffix)


def is_safe_output_path(path: Path, base_dir: Path) -> bool:
    """
    Return True if *path* is safely nested inside *base_dir*.
    Prevents path-traversal attacks when building output paths from filenames.
    """
    try:
        path.resolve().relative_to(base_dir.resolve())
        return True
    except ValueError:
        return False
