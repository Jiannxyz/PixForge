"""Shared data models for the conversion engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class NamingMode(str, Enum):
    CONVERTED = "converted"  # original.converted.ext
    ORIGINAL = "original"  # original.ext
    PREFIX = "prefix"  # {prefix}original.ext


class FileStatus(str, Enum):
    WAITING = "WAITING"
    CONVERTING = "CONVERTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class ConversionError(Exception):
    """Raised when a single image cannot be converted."""

    def __init__(self, message: str, code: str = "conversion_failed") -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class ConversionOptions:
    output_format: str
    output_dir: Path
    quality: int = 90
    webp_quality: int = 80
    heic_quality: int = 80
    png_compress_level: int = 6
    background_color: tuple[int, int, int] = (255, 255, 255)
    preserve_metadata: bool = True
    apply_exif_orientation: bool = True
    naming_mode: NamingMode = NamingMode.CONVERTED
    custom_prefix: str = ""
    overwrite: bool = False


@dataclass
class ConversionResult:
    success: bool
    source_path: Path
    output_path: Path | None = None
    error: str | None = None
    warning: str | None = None
    input_format: str | None = None
    output_format: str | None = None
    width: int | None = None
    height: int | None = None
    skipped: bool = False


@dataclass
class ImageJob:
    source_path: Path
    status: FileStatus = FileStatus.WAITING
    result: ConversionResult | None = None
    warnings: list[str] = field(default_factory=list)
