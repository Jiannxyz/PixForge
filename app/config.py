"""Default conversion and application settings."""

from __future__ import annotations

from pathlib import Path

from app.models import NamingMode


APP_NAME = "PixForge"
APP_VERSION = "0.1.0"
LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "pixforge.log"

DEFAULT_JPEG_QUALITY = 90
DEFAULT_WEBP_QUALITY = 80
DEFAULT_HEIC_QUALITY = 80
DEFAULT_PNG_COMPRESS_LEVEL = 6
DEFAULT_BACKGROUND_RGB = (255, 255, 255)
DEFAULT_PRESERVE_METADATA = True
DEFAULT_APPLY_EXIF_ORIENTATION = True
DEFAULT_NAMING_MODE = NamingMode.CONVERTED
DEFAULT_OVERWRITE = False
DEFAULT_MAX_WORKERS = 4
DEFAULT_THUMBNAIL_SIZE = (96, 96)
