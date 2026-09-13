"""Lightweight thumbnails for later UI use. Never keep full-resolution images."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from PIL import Image, ImageOps

from app.config import DEFAULT_THUMBNAIL_SIZE
from app.formats import register_image_plugins


def generate_thumbnail(
    source: str | Path,
    size: tuple[int, int] = DEFAULT_THUMBNAIL_SIZE,
) -> bytes:
    register_image_plugins()
    with Image.open(source) as image:
        image = ImageOps.exif_transpose(image) or image
        image = image.convert("RGB") if image.mode not in {"RGB", "L"} else image
        image.thumbnail(size, Image.Resampling.LANCZOS)
        buffer = BytesIO()
        image.save(buffer, format="JPEG", quality=70, optimize=True)
        return buffer.getvalue()
