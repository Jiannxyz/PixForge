"""PixForge entry point."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from app.core.converter import ImageConverter
from app.formats import register_image_plugins
from app.logging_config import configure_logging
from app.models import ConversionOptions
from app.ui.main_window import MainWindow


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="PixForge — Offline Image Converter.")
    parser.add_argument(
        "source",
        nargs="?",
        help="Source image path (if omitted, launches the desktop GUI)",
    )
    parser.add_argument(
        "--format",
        dest="output_format",
        default="JPG",
        help="Output format key, e.g. JPG or PNG",
    )
    parser.add_argument("--out", dest="output_dir", default=".", help="Output directory")
    parser.add_argument("--quality", type=int, default=90)
    return parser.parse_args(argv)


def run_gui() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("PixForge")
    app.setOrganizationName("PixForge")
    window = MainWindow()
    window.show()
    return app.exec()


def main(argv: list[str] | None = None) -> int:
    configure_logging()
    register_image_plugins()
    args = parse_args(argv)
    if not args.source:
        return run_gui()

    options = ConversionOptions(
        output_format=args.output_format,
        output_dir=Path(args.output_dir),
        quality=args.quality,
    )
    result = ImageConverter().convert(args.source, options)
    if result.success:
        print(f"Converted: {result.output_path}")
        return 0
    print(f"Failed: {result.error}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
