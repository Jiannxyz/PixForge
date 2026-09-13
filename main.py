"""Application entry point for PixForge."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pillow_heif import register_heif_opener

# Always register pillow-heif opener at startup for HEIC/HEIF decoding & encoding
register_heif_opener()

from app.config import APP_NAME
from app.logging_config import get_logger, setup_logging

log = get_logger("main")


def run_gui() -> int:
    """Launch the PySide6 desktop GUI."""
    from PySide6.QtWidgets import QApplication
    from app.ui.main_window import MainWindow

    setup_logging()
    log.info("Starting %s GUI...", APP_NAME)

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)

    window = MainWindow()
    window.show()

    return app.exec()


def run_cli(args: argparse.Namespace) -> int:
    """Fallback CLI conversion mode for scripting or headless conversion."""
    from app.core.conversion_manager import ConversionManager
    from app.models import ConversionOptions
    from app.utils.filesystem import collect_image_paths

    setup_logging()
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input path '{input_path}' does not exist.")
        return 1

    if input_path.is_dir():
        paths = collect_image_paths(input_path, recursive=args.recursive)
    else:
        paths = [input_path]

    if not paths:
        print("No supported image files found.")
        return 0

    out_dir = Path(args.output) if args.output else None
    options = ConversionOptions(
        output_format=args.format.upper(),
        output_dir=out_dir,
        jpeg_quality=args.quality,
        png_compression=args.compression,
        overwrite=args.overwrite,
    )

    print(f"Converting {len(paths)} file(s) to {options.output_format}...")
    manager = ConversionManager()

    def _progress(res, done, total):
        status = "OK" if res.success else f"FAIL ({res.error})"
        print(f"[{done}/{total}] {res.input_path.name} -> {status}")

    results = manager.convert_batch(paths, options, progress=_progress)
    succeeded = sum(1 for r in results if r.success)
    failed = len(results) - succeeded
    print(f"\nBatch complete: {succeeded} succeeded, {failed} failed.")
    return 0 if failed == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="PixForge: Fast Offline Batch Image Converter",
    )
    parser.add_argument("-i", "--input", help="Path to an image file or folder")
    parser.add_argument("-o", "--output", help="Output directory")
    parser.add_argument("-f", "--format", default="JPG", help="Target format (JPG, PNG, WEBP, HEIC, etc.)")
    parser.add_argument("-q", "--quality", type=int, default=90, help="JPEG/HEIC/WEBP quality (1-100)")
    parser.add_argument("-c", "--compression", type=int, default=6, help="PNG compression level (0-9)")
    parser.add_argument("-r", "--recursive", action="store_true", help="Recursively scan folders")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing output files")

    # If any conversion arguments are provided, use CLI mode; otherwise run desktop GUI
    if len(sys.argv) > 1 and ("-i" in sys.argv or "--input" in sys.argv):
        args = parser.parse_args()
        return run_cli(args)
    else:
        return run_gui()


if __name__ == "__main__":
    sys.exit(main())
