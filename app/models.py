"""Domain models shared across the application."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Optional


class FileStatus(str, Enum):
    WAITING = "Waiting"
    CONVERTING = "Converting"
    COMPLETED = "Completed"
    FAILED = "Failed"
    SKIPPED = "Skipped"


class NamingMode(str, Enum):
    CONVERTED_SUFFIX = "original.converted.ext"   # photo.jpg → photo.converted.png
    KEEP_STEM = "original.ext"                     # photo.jpg → photo.png
    CUSTOM_PREFIX = "prefix_original.ext"          # prefix_photo.png


@dataclass
class ConversionOptions:
    output_format: str = "JPG"          # Key in SUPPORTED_FORMATS
    output_dir: Optional[Path] = None
    jpeg_quality: int = 90
    png_compression: int = 6
    heic_quality: int = 80
    webp_quality: int = 90
    preserve_metadata: bool = True
    overwrite: bool = False
    naming_mode: NamingMode = NamingMode.CONVERTED_SUFFIX
    custom_prefix: str = ""
    recursive: bool = False


@dataclass
class ConversionResult:
    success: bool
    input_path: Path
    output_path: Optional[Path] = None
    error: Optional[str] = None
    skipped: bool = False


@dataclass
class ImageJob:
    path: Path
    status: FileStatus = FileStatus.WAITING
    error_message: Optional[str] = None
    output_path: Optional[Path] = None
    # Info populated after inspection
    width: int = 0
    height: int = 0
    file_size: int = 0
    detected_format: str = ""
