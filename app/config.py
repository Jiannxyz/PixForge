"""Application-wide configuration constants."""
from __future__ import annotations

import os
import sys
from pathlib import Path

APP_NAME = "PixForge"
APP_VERSION = "1.0.0"
APP_ORG = "PixForge"

if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    BASE_DIR = Path(sys._MEIPASS) / "app"
else:
    BASE_DIR = Path(__file__).resolve().parent

RESOURCES_DIR = BASE_DIR / "resources"
ICONS_DIR = RESOURCES_DIR / "icons"
LOGO_TRANSPARENT_PATH = ICONS_DIR / "PixForgeLogoTransparent.png"
LOGO_BACKGROUND_PATH = ICONS_DIR / "PixForgeLogoWithBackground.png"
UPLOAD_IMAGE_LOGO_PATH = ICONS_DIR / "UploadimageLogo.png"

# Worker thread count for batch conversion
MAX_WORKERS: int = min(4, os.cpu_count() or 2)

# Thumbnail size for preview list (px)
THUMBNAIL_SIZE = 72

# Default quality settings
DEFAULT_JPEG_QUALITY = 90
DEFAULT_PNG_COMPRESSION = 6
DEFAULT_HEIC_QUALITY = 80
DEFAULT_WEBP_QUALITY = 90

# Alpha compositing background (white)
ALPHA_BG_COLOR = (255, 255, 255)
