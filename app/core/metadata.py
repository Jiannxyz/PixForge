"""EXIF / XMP / IPTC metadata helpers."""
from __future__ import annotations

import logging
from typing import Any

from PIL import Image

log = logging.getLogger(__name__)


def copy_metadata(src: Image.Image, dst: Image.Image) -> Image.Image:
    """
    Copy EXIF data from *src* to *dst* where possible.
    Returns *dst* (possibly with exif attached).
    Failures are silently swallowed — metadata is best-effort.
    """
    try:
        exif = src.info.get("exif")
        if exif:
            dst.info["exif"] = exif
    except Exception as exc:  # noqa: BLE001
        log.debug("Could not copy EXIF: %s", exc)
    return dst


def get_exif_bytes(image: Image.Image) -> bytes | None:
    """Return raw EXIF bytes from *image*, or None if unavailable."""
    try:
        return image.info.get("exif")
    except Exception:  # noqa: BLE001
        return None
