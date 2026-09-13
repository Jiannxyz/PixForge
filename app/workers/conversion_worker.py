"""Background conversion jobs. Qt workers will wrap this later."""

from app.core.converter import ImageConverter
from app.models import ConversionOptions, ConversionResult


def run_conversion_job(source, options: ConversionOptions, converter: ImageConverter | None = None) -> ConversionResult:
    engine = converter or ImageConverter()
    return engine.convert(source, options)
