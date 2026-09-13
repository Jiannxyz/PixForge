"""Supported image format registry."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class FormatInfo:
    label: str                  # Display name shown in UI
    extensions: List[str]       # Lower-case extensions including dot
    pillow_format: str          # Pillow format string for save()
    supports_alpha: bool = False
    save_kwargs_base: dict = field(default_factory=dict)


# Central registry — extend here to add new formats
SUPPORTED_FORMATS: dict[str, FormatInfo] = {
    "JPG": FormatInfo(
        label="JPG / JPEG",
        extensions=[".jpg", ".jpeg"],
        pillow_format="JPEG",
        supports_alpha=False,
    ),
    "PNG": FormatInfo(
        label="PNG",
        extensions=[".png"],
        pillow_format="PNG",
        supports_alpha=True,
    ),
    "WEBP": FormatInfo(
        label="WEBP",
        extensions=[".webp"],
        pillow_format="WEBP",
        supports_alpha=True,
    ),
    "BMP": FormatInfo(
        label="BMP",
        extensions=[".bmp"],
        pillow_format="BMP",
        supports_alpha=False,
    ),
    "TIFF": FormatInfo(
        label="TIFF",
        extensions=[".tiff", ".tif"],
        pillow_format="TIFF",
        supports_alpha=True,
    ),
    "GIF": FormatInfo(
        label="GIF",
        extensions=[".gif"],
        pillow_format="GIF",
        supports_alpha=True,
    ),
    "HEIC": FormatInfo(
        label="HEIC",
        extensions=[".heic", ".heif"],
        pillow_format="HEIF",
        supports_alpha=False,
    ),
}

# Build reverse lookup: extension → format key
EXTENSION_TO_FORMAT: dict[str, str] = {}
for _key, _info in SUPPORTED_FORMATS.items():
    for _ext in _info.extensions:
        EXTENSION_TO_FORMAT[_ext.lower()] = _key

# Input extensions accepted by the file dialog / drop zone
INPUT_EXTENSIONS: list[str] = sorted(EXTENSION_TO_FORMAT.keys())

# Output format keys for the dropdown (exclude GIF as output target)
OUTPUT_FORMAT_KEYS: list[str] = [k for k in SUPPORTED_FORMATS if k != "GIF"]


def format_for_extension(ext: str) -> str | None:
    """Return format key (e.g. 'JPG') for a file extension (e.g. '.jpg')."""
    return EXTENSION_TO_FORMAT.get(ext.lower())


def is_supported_input(ext: str) -> bool:
    """Return True if the extension is a recognised input format."""
    return ext.lower() in EXTENSION_TO_FORMAT
