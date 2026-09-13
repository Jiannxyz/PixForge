"""Lightweight image inspection for the file queue. Does not convert files."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageOps

from app.config import DEFAULT_THUMBNAIL_SIZE
from app.formats import format_from_extension, register_image_plugins


@dataclass(frozen=True)
class ImagePreview:
    path: Path
    width: int | None
    height: int | None
    format_key: str | None
    thumbnail_jpeg: bytes | None
    error: str | None = None


def inspect_and_thumbnail(
    source: str | Path,
    size: tuple[int, int] = DEFAULT_THUMBNAIL_SIZE,
) -> ImagePreview:
    register_image_plugins()
    path = Path(source)
    spec = format_from_extension(path)
    format_key = spec.key if spec else None
    try:
        with Image.open(path) as image:
            image = ImageOps.exif_transpose(image) or image
            width, height = image.size
            preview = image.convert("RGB") if image.mode not in {"RGB", "L"} else image.copy()
            preview.thumbnail(size, Image.Resampling.LANCZOS)
            buffer = BytesIO()
            preview.save(buffer, format="JPEG", quality=70, optimize=True)
            return ImagePreview(path, width, height, format_key, buffer.getvalue())
    except Exception as exc:
        return ImagePreview(path, None, None, format_key, None, error=str(exc))
