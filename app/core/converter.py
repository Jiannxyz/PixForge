"""Image converter — handles a single file conversion end-to-end."""
from __future__ import annotations

import logging
from pathlib import Path
from threading import Lock

from PIL import Image, ImageOps, UnidentifiedImageError

from app.config import ALPHA_BG_COLOR
from app.core.metadata import get_exif_bytes
from app.formats import SUPPORTED_FORMATS
from app.models import ConversionOptions, ConversionResult
from app.utils.filesystem import build_output_path

log = logging.getLogger(__name__)

# Thread-safe output path reservation lock.
# Held only during path allocation + touch(); never during I/O.
_OUTPUT_ALLOC_LOCK = Lock()


class ImageConverter:
    """Converts a single image file according to *options*."""

    def convert(
        self,
        input_path: Path,
        options: ConversionOptions,
    ) -> ConversionResult:
        """
        Convert *input_path* and write to options.output_dir.
        Always returns a ConversionResult — never raises.
        """
        try:
            return self._run(input_path, options)
        except UnidentifiedImageError as exc:
            log.warning("Cannot identify %s: %s", input_path.name, exc)
            return ConversionResult(success=False, input_path=input_path, error=str(exc))
        except OSError as exc:
            log.warning("OS error converting %s: %s", input_path.name, exc)
            return ConversionResult(success=False, input_path=input_path, error=str(exc))
        except Exception as exc:  # noqa: BLE001
            log.exception("Unexpected error converting %s", input_path.name)
            return ConversionResult(success=False, input_path=input_path, error=str(exc))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _run(self, input_path: Path, options: ConversionOptions) -> ConversionResult:
        output_dir = options.output_dir or input_path.parent
        output_dir.mkdir(parents=True, exist_ok=True)

        # Allocate output path under lock; touch immediately to reserve it
        with _OUTPUT_ALLOC_LOCK:
            out_path = build_output_path(
                input_path=input_path,
                output_dir=output_dir,
                output_format_key=options.output_format,
                naming_mode=options.naming_mode,
                custom_prefix=options.custom_prefix,
                overwrite=options.overwrite,
            )
            # Reserve the path so other threads don't collide
            out_path.touch()

        try:
            self._convert_file(input_path, out_path, options)
        except Exception:
            # Clean up zero-byte reservation on failure
            if out_path.exists() and out_path.stat().st_size == 0:
                out_path.unlink(missing_ok=True)
            raise

        log.info("Converted %s → %s", input_path.name, out_path.name)
        return ConversionResult(success=True, input_path=input_path, output_path=out_path)

    def _convert_file(
        self, src: Path, dst: Path, options: ConversionOptions
    ) -> None:
        fmt_info = SUPPORTED_FORMATS[options.output_format]

        with Image.open(src) as img:
            # Correct EXIF orientation (critical for phone photos)
            img = ImageOps.exif_transpose(img)

            # Collect EXIF bytes before mode conversion discards them
            exif_bytes = get_exif_bytes(img) if options.preserve_metadata else None

            # Handle animated GIF — export first frame with warning
            if getattr(img, "is_animated", False) and src.suffix.lower() == ".gif":
                log.warning(
                    "%s is animated — exporting first frame only.", src.name
                )
                img.seek(0)

            img = self._prepare_mode(img, fmt_info, options)

            save_kwargs = self._build_save_kwargs(options, fmt_info, exif_bytes)
            img.save(dst, fmt_info.pillow_format, **save_kwargs)

    @staticmethod
    def _prepare_mode(img: Image.Image, fmt_info, options: ConversionOptions) -> Image.Image:
        """Convert image mode to one compatible with the output format."""
        if img.mode == "P":
            img = img.convert("RGBA")

        if not fmt_info.supports_alpha and img.mode in ("RGBA", "LA"):
            # Flatten transparency onto a white background
            bg = Image.new("RGB", img.size, ALPHA_BG_COLOR)
            if img.mode == "LA":
                img = img.convert("RGBA")
            bg.paste(img, mask=img.split()[3])
            return bg

        if fmt_info.pillow_format == "JPEG" and img.mode != "RGB":
            return img.convert("RGB")

        if fmt_info.pillow_format == "BMP" and img.mode not in ("RGB", "RGBA", "L"):
            return img.convert("RGB")

        return img

    @staticmethod
    def _build_save_kwargs(
        options: ConversionOptions, fmt_info, exif_bytes: bytes | None
    ) -> dict:
        kwargs: dict = {}

        pf = fmt_info.pillow_format
        if pf == "JPEG":
            kwargs["quality"] = options.jpeg_quality
            kwargs["optimize"] = True
            if exif_bytes:
                kwargs["exif"] = exif_bytes
        elif pf == "PNG":
            kwargs["compress_level"] = options.png_compression
        elif pf == "WEBP":
            kwargs["quality"] = options.webp_quality
            if exif_bytes:
                kwargs["exif"] = exif_bytes
        elif pf == "HEIF":
            kwargs["quality"] = options.heic_quality
        elif pf == "TIFF":
            if exif_bytes:
                kwargs["exif"] = exif_bytes

        return kwargs
