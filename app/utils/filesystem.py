"""Safe output path and filename generation. Never overwrite unless asked."""

from __future__ import annotations

import re
from pathlib import Path

from app.formats import preferred_extension
from app.models import ConversionOptions, NamingMode

_UNSAFE_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def sanitize_filename_stem(stem: str) -> str:
    cleaned = _UNSAFE_CHARS.sub("_", stem).strip(" .")
    return cleaned or "image"


def is_inside_directory(path: Path, directory: Path) -> bool:
    try:
        path.resolve().relative_to(directory.resolve())
        return True
    except ValueError:
        return False


def build_output_stem(source: Path, options: ConversionOptions) -> str:
    stem = sanitize_filename_stem(source.stem)
    if options.naming_mode is NamingMode.ORIGINAL:
        return stem
    if options.naming_mode is NamingMode.PREFIX:
        prefix = sanitize_filename_stem(options.custom_prefix)
        return f"{prefix}{stem}" if prefix else stem
    return f"{stem}.converted"


def unique_path(directory: Path, stem: str, extension: str, overwrite: bool) -> Path:
    candidate = directory / f"{stem}{extension}"
    if overwrite or not candidate.exists():
        return candidate
    index = 1
    while True:
        candidate = directory / f"{stem} ({index}){extension}"
        if not candidate.exists():
            return candidate
        index += 1
        if index > 100_000:
            raise OSError("Could not allocate a unique output filename")


def build_output_path(source: Path, options: ConversionOptions) -> Path:
    from app.core.validators import ensure_output_dir, ValidationError

    output_dir = ensure_output_dir(options.output_dir)
    stem = build_output_stem(source, options)
    extension = preferred_extension(options.output_format)
    path = unique_path(output_dir, stem, extension, options.overwrite)
    if not is_inside_directory(path, output_dir):
        raise ValidationError("Output path escapes the destination folder")
    return path
