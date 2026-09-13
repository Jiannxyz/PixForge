"""Offline image conversion engine. Independent of any GUI."""

from __future__ import annotations

import logging
from pathlib import Path
from threading import Lock

from PIL import Image, ImageOps, UnidentifiedImageError

from app.core.metadata import build_save_info, extract_metadata
from app.core.validators import (
    ValidationError,
    validate_extension_supported,
    validate_output_format,
    validate_source_path,
)
from app.formats import FormatSpec, can_encode, format_from_extension, get_format, register_image_plugins
from app.models import ConversionError, ConversionOptions, ConversionResult
from app.utils.filesystem import build_output_path

logger = logging.getLogger(__name__)

_OUTPUT_ALLOC_LOCK = Lock()


def flatten_alpha(image: Image.Image, background: tuple[int, int, int]) -> Image.Image:
    """Composite transparency onto a solid background. JPEG cannot store alpha."""
    if image.mode == "P":
        image = image.convert("RGBA")
    elif image.mode == "LA":
        image = image.convert("RGBA")
    elif image.mode != "RGBA":
        if "A" in image.getbands():
            image = image.convert("RGBA")
        else:
            return image.convert("RGB") if image.mode != "RGB" else image

    if image.mode != "RGBA":
        return image.convert("RGB")

    opaque = Image.new("RGBA", image.size, (*background, 255))
    return Image.alpha_composite(opaque, image).convert("RGB")


def prepare_mode(image: Image.Image, spec: FormatSpec, background: tuple[int, int, int]) -> Image.Image:
    if image.mode == "CMYK" and spec.pillow_format not in {"JPEG", "TIFF"}:
        image = image.convert("RGB")

    if spec.pillow_format == "JPEG":
        if image.mode in {"RGBA", "LA", "P"} or "A" in image.getbands():
            return flatten_alpha(image, background)
        if image.mode not in {"RGB", "L", "CMYK"}:
            return image.convert("RGB")
        return image

    if spec.pillow_format == "BMP":
        if "A" in image.getbands() or image.mode in {"RGBA", "LA", "P"}:
            return flatten_alpha(image, background)
        if image.mode != "RGB":
            return image.convert("RGB")
        return image

    if not spec.supports_alpha and ("A" in image.getbands() or image.mode in {"RGBA", "LA"}):
        return flatten_alpha(image, background)

    if spec.supports_alpha and image.mode == "P":
        return image.convert("RGBA")

    return image


def _save_kwargs(image: Image.Image, spec: FormatSpec, options: ConversionOptions, metadata: dict) -> dict:
    kwargs: dict = {"format": spec.pillow_format}
    kwargs.update(
        build_save_info(
            metadata,
            preserve=options.preserve_metadata,
            pillow_format=spec.pillow_format,
        )
    )

    if spec.pillow_format == "JPEG":
        kwargs.update(quality=max(1, min(options.quality, 100)), optimize=True)
    elif spec.pillow_format == "PNG":
        kwargs.update(compress_level=max(0, min(options.png_compress_level, 9)))
    elif spec.pillow_format == "WEBP":
        kwargs.update(quality=max(1, min(options.webp_quality, 100)), method=4)
    elif spec.pillow_format in {"HEIF", "AVIF"}:
        quality = options.heic_quality if spec.pillow_format == "HEIF" else options.heic_quality
        kwargs.update(quality=max(1, min(quality, 100)))
    return kwargs


class ImageConverter:
    """Convert a single image file to another format using Pillow/pillow-heif."""

    def convert(self, source: str | Path, options: ConversionOptions) -> ConversionResult:
        register_image_plugins()
        source_path = Path(source)
        try:
            validate_output_format(options.output_format)
            validate_source_path(source_path)
            validate_extension_supported(source_path)
            input_spec = format_from_extension(source_path)
            output_spec = get_format(options.output_format)
            if input_spec is None or output_spec is None:
                raise ValidationError("Unsupported format")
            if not can_encode(output_spec.key):
                raise ValidationError("Unsupported format")

            output_path: Path | None = None
            with _OUTPUT_ALLOC_LOCK:
                output_path = build_output_path(source_path, options)
                if not options.overwrite:
                    output_path.touch(exist_ok=True)

            warning = self._convert_file(source_path, output_path, options, output_spec)
            width, height = Image.open(output_path).size
            logger.info("Converted %s -> %s", source_path, output_path)
            return ConversionResult(
                success=True,
                source_path=source_path,
                output_path=output_path,
                warning=warning,
                input_format=input_spec.key,
                output_format=output_spec.key,
                width=width,
                height=height,
            )
        except ValidationError as exc:
            logger.warning("Validation failed for %s: %s", source_path, exc)
            return ConversionResult(
                success=False,
                source_path=source_path,
                error=str(exc),
                output_format=options.output_format,
            )
        except (UnidentifiedImageError, OSError, ConversionError, ValueError) as exc:
            logger.exception("Conversion failed for %s", source_path)
            message = str(exc) or "conversion_failed"
            if isinstance(exc, UnidentifiedImageError) or "cannot identify" in message.lower():
                message = "Invalid image"
            if output_path and output_path.exists():
                try:
                    if output_path.stat().st_size == 0:
                        output_path.unlink(missing_ok=True)
                except OSError:
                    pass
            return ConversionResult(
                success=False,
                source_path=source_path,
                error=message,
                output_format=options.output_format,
            )
        except Exception as exc:
            logger.exception("Unexpected error converting %s", source_path)
            message = str(exc) or "Invalid image"
            if output_path and output_path.exists():
                try:
                    if output_path.stat().st_size == 0:
                        output_path.unlink(missing_ok=True)
                except OSError:
                    pass
            return ConversionResult(
                success=False,
                source_path=source_path,
                error=message,
                output_format=options.output_format,
            )

    def _convert_file(
        self,
        source_path: Path,
        output_path: Path,
        options: ConversionOptions,
        output_spec: FormatSpec,
    ) -> str | None:
        warnings: list[str] = []
        with Image.open(source_path) as image:
            frame_count = getattr(image, "n_frames", 1) or 1
            if frame_count > 1:
                image.seek(0)
                warnings.append("Only the first frame was converted.")
                image = image.copy()
            else:
                image.load()

            metadata = extract_metadata(image)
            if options.apply_exif_orientation:
                image = ImageOps.exif_transpose(image) or image

            image = prepare_mode(image, output_spec, options.background_color)
            save_kwargs = _save_kwargs(image, output_spec, options, metadata)
            try:
                image.save(output_path, **save_kwargs)
            except Exception:
                save_kwargs.pop("exif", None)
                save_kwargs.pop("xmp", None)
                save_kwargs.pop("icc_profile", None)
                save_kwargs.pop("comment", None)
                image.save(output_path, **save_kwargs)
                warnings.append("Metadata could not be preserved for this format.")

        return " ".join(warnings) if warnings else None
