"""Filesystem utilities: path building, collection, sanitisation."""
from __future__ import annotations

import re
from pathlib import Path
from typing import List

from app.formats import INPUT_EXTENSIONS
from app.models import NamingMode


# ---------------------------------------------------------------------------
# Path sanitisation
# ---------------------------------------------------------------------------

_UNSAFE_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def sanitize_filename_stem(stem: str) -> str:
    """Remove characters illegal on Windows/macOS from a filename stem."""
    cleaned = _UNSAFE_CHARS.sub("_", stem).strip(". ")
    # Collapse multiple consecutive underscores and strip them from ends
    return re.sub(r"_+", "_", cleaned).strip("_")


# ---------------------------------------------------------------------------
# Output path construction
# ---------------------------------------------------------------------------

def build_output_path(
    input_path: Path,
    output_dir: Path,
    output_format_key: str,
    naming_mode: NamingMode = NamingMode.CONVERTED_SUFFIX,
    custom_prefix: str = "",
    overwrite: bool = False,
) -> Path:
    """
    Build the destination path for a converted file.
    If *overwrite* is False, appends a counter suffix to avoid collisions
    with files that already exist on disk.
    """
    from app.formats import SUPPORTED_FORMATS

    fmt = SUPPORTED_FORMATS[output_format_key]
    ext = fmt.extensions[0]  # Primary extension

    stem = sanitize_filename_stem(input_path.stem)

    if naming_mode == NamingMode.CONVERTED_SUFFIX:
        out_stem = f"{stem}.converted"
    elif naming_mode == NamingMode.KEEP_STEM:
        out_stem = stem
    else:  # CUSTOM_PREFIX
        prefix = sanitize_filename_stem(custom_prefix) or "converted"
        out_stem = f"{prefix}_{stem}"

    candidate = output_dir / f"{out_stem}{ext}"

    if overwrite or not candidate.exists():
        return candidate

    return unique_path(candidate)


def unique_path(path: Path) -> Path:
    """
    Return a path that does not currently exist by appending (1), (2), …
    Checks filesystem existence only (no in-memory reservation).
    """
    if not path.exists():
        return path

    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    counter = 1
    while True:
        candidate = parent / f"{stem} ({counter}){suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


# ---------------------------------------------------------------------------
# Folder scanning
# ---------------------------------------------------------------------------

def collect_image_paths(
    root: Path,
    recursive: bool = False,
) -> List[Path]:
    """
    Collect all supported image files under *root*.
    If *recursive* is False only the immediate directory is scanned.
    """
    glob = "**/*" if recursive else "*"
    results: list[Path] = []
    for p in root.glob(glob):
        if p.is_file() and p.suffix.lower() in INPUT_EXTENSIONS:
            results.append(p)
    return sorted(results)
