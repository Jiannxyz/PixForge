"""Input validation. Treat every file as untrusted."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, UnidentifiedImageError

from app.formats import format_from_extension, get_format, register_image_plugins


class ValidationError(ValueError):
    """The file or format cannot be processed."""


def validate_source_path(path: str | Path) -> Path:
    source = Path(path)
    if not source.exists():
        raise ValidationError(f"File not found: {source}")
    if not source.is_file():
        raise ValidationError(f"Not a file: {source}")
    return source.resolve()


def validate_output_dir(path: str | Path) -> Path:
    output_dir = Path(path).expanduser()
    if output_dir.exists() and not output_dir.is_dir():
        raise ValidationError(f"Output path is not a directory: {output_dir}")
    return output_dir


def ensure_output_dir(path: str | Path) -> Path:
    output_dir = validate_output_dir(path)
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir.resolve()


def validate_extension_supported(path: str | Path) -> None:
    if format_from_extension(path) is None:
        raise ValidationError("Unsupported format")


def validate_output_format(format_key: str) -> None:
    if get_format(format_key) is None:
        raise ValidationError("Unsupported format")


def validate_image_readable(path: str | Path) -> None:
    register_image_plugins()
    source = validate_source_path(path)
    try:
        with Image.open(source) as image:
            image.verify()
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise ValidationError("Invalid image") from exc
