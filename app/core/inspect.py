"""Image inspection helpers — dimensions, format, file size."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from app.formats import format_for_extension


@dataclass
class ImageInfo:
    width: int
    height: int
    detected_format: str   # Upper-case key e.g. 'JPG', 'HEIC'
    file_size: int         # Bytes on disk
    mode: str              # PIL mode e.g. 'RGB', 'RGBA'


def get_image_info(path: Path) -> ImageInfo | None:
    """
    Open *path* just enough to read header metadata.
    Returns None if the file cannot be identified.
    Does NOT load pixel data into memory.
    """
    try:
        with Image.open(path) as img:
            width, height = img.size
            mode = img.mode
        detected = format_for_extension(path.suffix) or path.suffix.lstrip(".").upper()
        file_size = path.stat().st_size
        return ImageInfo(
            width=width,
            height=height,
            detected_format=detected,
            file_size=file_size,
            mode=mode,
        )
    except (UnidentifiedImageError, OSError, Exception):  # noqa: BLE001
        return None


def make_thumbnail(path: Path, size: int = 72) -> bytes | None:
    """
    Return JPEG thumbnail bytes for *path*, or None on failure.
    Uses PIL thumbnail() which downsamples without loading the full image.
    """
    try:
        with Image.open(path) as img:
            img.thumbnail((size, size), Image.LANCZOS)
            if img.mode in ("RGBA", "P", "LA"):
                bg = Image.new("RGB", img.size, (40, 40, 40))
                if img.mode == "P":
                    img = img.convert("RGBA")
                bg.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
                img = bg
            elif img.mode != "RGB":
                img = img.convert("RGB")
            import io
            buf = io.BytesIO()
            img.save(buf, "JPEG", quality=75)
            return buf.getvalue()
    except Exception:  # noqa: BLE001
        return None
