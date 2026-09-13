"""Best-effort metadata extraction and re-attachment."""

from __future__ import annotations

from typing import Any

from PIL import Image
from PIL.Image import Exif

EXIF_ORIENTATION = 0x0112
_PASSTHROUGH_INFO_KEYS = ("icc_profile", "xmp", "xml", "iptc", "photoshop", "comment")


def extract_metadata(image: Image.Image) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    try:
        exif = image.getexif()
        if exif and len(exif) > 0:
            payload["exif"] = exif
    except Exception:
        pass

    for key in _PASSTHROUGH_INFO_KEYS:
        value = image.info.get(key)
        if value:
            payload[key] = value
    return payload


def strip_orientation(exif: Exif | None) -> Exif | None:
    if not exif:
        return exif
    if EXIF_ORIENTATION in exif:
        exif[EXIF_ORIENTATION] = 1
    return exif


def build_save_info(
    metadata: dict[str, Any],
    *,
    preserve: bool,
    pillow_format: str,
) -> dict[str, Any]:
    """Return kwargs Pillow understands for save()."""
    if not preserve or not metadata:
        return {}

    kwargs: dict[str, Any] = {}
    icc = metadata.get("icc_profile")
    if icc:
        kwargs["icc_profile"] = icc

    xmp = metadata.get("xmp") or metadata.get("xml")
    if xmp and pillow_format in {"JPEG", "WEBP", "PNG", "TIFF", "HEIF", "AVIF"}:
        kwargs["xmp"] = xmp if isinstance(xmp, (bytes, bytearray)) else str(xmp).encode("utf-8")

    comment = metadata.get("comment")
    if comment and pillow_format in {"JPEG", "PNG"}:
        kwargs["comment"] = comment

    exif = metadata.get("exif")
    if exif and pillow_format in {"JPEG", "WEBP", "TIFF", "HEIF", "AVIF", "PNG"}:
        try:
            cleaned = strip_orientation(exif)
            if cleaned is not None:
                kwargs["exif"] = cleaned.tobytes()
        except Exception:
            pass

    return kwargs
