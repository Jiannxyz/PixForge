"""PixForge application package. Conversion logic lives in app.core."""

from app.formats import register_image_plugins

__version__ = "0.1.0"
APP_NAME = "PixForge"

register_image_plugins()
