"""Central image format registry. All format checks go through this module."""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

logger = logging.getLogger(__name__)

_PLUGINS_REGISTERED = False
_ENCODE_CACHE: dict[str, bool] = {}


@dataclass(frozen=True)
class FormatSpec:
    key: str
    pillow_format: str
    extensions: tuple[str, ...]
    supports_alpha: bool
    quality_setting: str | None
    can_decode: bool = True
    can_encode: bool = True


def register_image_plugins() -> None:
    """Register pillow-heif so Pillow can open and save HEIC/HEIF (and AVIF when available)."""
    global _PLUGINS_REGISTERED
    if _PLUGINS_REGISTERED:
        return

    try:
        from pillow_heif import register_heif_opener

        register_heif_opener()
        logger.debug("Registered HEIF opener")
    except Exception:
        logger.warning("pillow-heif HEIF opener is unavailable", exc_info=True)

    try:
        from pillow_heif import register_avif_opener

        register_avif_opener()
        logger.debug("Registered AVIF opener")
    except Exception:
        logger.debug("AVIF opener is unavailable")

    _PLUGINS_REGISTERED = True


def _probe_encode(pillow_format: str) -> bool:
    if pillow_format in _ENCODE_CACHE:
        return _ENCODE_CACHE[pillow_format]
    register_image_plugins()
    try:
        buffer = io.BytesIO()
        Image.new("RGB", (2, 2), (255, 0, 0)).save(buffer, format=pillow_format)
        ok = buffer.tell() > 0
    except Exception:
        ok = False
    _ENCODE_CACHE[pillow_format] = ok
    return ok


def _probe_heif_decode() -> bool:
    register_image_plugins()
    try:
        from pillow_heif import HeifImagePlugin  # noqa: F401

        return True
    except Exception:
        return "HEIF" in Image.registered_extensions().values() or "HEIC" in Image.registered_extensions().values()


FORMAT_SPECS: dict[str, FormatSpec] = {
    "JPG": FormatSpec(
        key="JPG",
        pillow_format="JPEG",
        extensions=(".jpg", ".jpeg", ".jpe", ".jfif"),
        supports_alpha=False,
        quality_setting="jpeg",
    ),
    "JPEG": FormatSpec(
        key="JPEG",
        pillow_format="JPEG",
        extensions=(".jpg", ".jpeg", ".jpe", ".jfif"),
        supports_alpha=False,
        quality_setting="jpeg",
    ),
    "PNG": FormatSpec(
        key="PNG",
        pillow_format="PNG",
        extensions=(".png",),
        supports_alpha=True,
        quality_setting="png",
    ),
    "WEBP": FormatSpec(
        key="WEBP",
        pillow_format="WEBP",
        extensions=(".webp",),
        supports_alpha=True,
        quality_setting="webp",
    ),
    "BMP": FormatSpec(
        key="BMP",
        pillow_format="BMP",
        extensions=(".bmp",),
        supports_alpha=False,
        quality_setting=None,
    ),
    "TIFF": FormatSpec(
        key="TIFF",
        pillow_format="TIFF",
        extensions=(".tif", ".tiff"),
        supports_alpha=True,
        quality_setting=None,
    ),
    "GIF": FormatSpec(
        key="GIF",
        pillow_format="GIF",
        extensions=(".gif",),
        supports_alpha=True,
        quality_setting=None,
    ),
    "HEIC": FormatSpec(
        key="HEIC",
        pillow_format="HEIF",
        extensions=(".heic", ".heif"),
        supports_alpha=True,
        quality_setting="heic",
    ),
    "HEIF": FormatSpec(
        key="HEIF",
        pillow_format="HEIF",
        extensions=(".heic", ".heif"),
        supports_alpha=True,
        quality_setting="heic",
    ),
    "AVIF": FormatSpec(
        key="AVIF",
        pillow_format="AVIF",
        extensions=(".avif",),
        supports_alpha=True,
        quality_setting="heic",
    ),
}

_EXTENSION_INDEX: dict[str, FormatSpec] = {}
for _spec in FORMAT_SPECS.values():
    for _ext in _spec.extensions:
        _EXTENSION_INDEX.setdefault(_ext, _spec)


def normalize_format_key(value: str) -> str:
    key = value.strip().upper().lstrip(".")
    aliases = {"JPEG": "JPG", "JPE": "JPG", "JFIF": "JPG", "TIF": "TIFF"}
    return aliases.get(key, key)


def get_format(value: str) -> FormatSpec | None:
    key = value.strip().upper().lstrip(".")
    if key in FORMAT_SPECS:
        return FORMAT_SPECS[key]
    aliased = normalize_format_key(value)
    return FORMAT_SPECS.get(aliased)


def format_from_extension(path: str | Path) -> FormatSpec | None:
    ext = Path(path).suffix.lower()
    return _EXTENSION_INDEX.get(ext)


def is_supported_extension(path: str | Path) -> bool:
    return format_from_extension(path) is not None


def preferred_extension(format_key: str) -> str:
    spec = get_format(format_key)
    if spec is None:
        raise ValueError(f"Unknown format: {format_key}")
    if spec.key in {"JPG", "JPEG"}:
        return ".jpg"
    if spec.key == "TIFF":
        return ".tiff"
    if spec.key == "HEIF":
        return ".heif"
    return spec.extensions[0]


def can_encode(format_key: str) -> bool:
    spec = get_format(format_key)
    if spec is None:
        return False
    return _probe_encode(spec.pillow_format)


def can_decode_heif() -> bool:
    return _probe_heif_decode()


def registered_input_extensions() -> tuple[str, ...]:
    return tuple(sorted(_EXTENSION_INDEX))


def file_dialog_filter() -> str:
    patterns = " ".join(f"*{ext}" for ext in registered_input_extensions())
    return f"Images ({patterns})"


def output_format_keys() -> tuple[str, ...]:
    keys = []
    seen: set[str] = set()
    for key in ("JPG", "PNG", "WEBP", "BMP", "TIFF", "HEIC", "HEIF", "AVIF"):
        spec = FORMAT_SPECS[key]
        if spec.pillow_format in seen and key in {"JPEG"}:
            continue
        seen.add(spec.pillow_format if key not in {"HEIC", "HEIF"} else key)
        keys.append(key)
    return tuple(keys)
