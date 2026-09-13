"""PixForge entry point. GUI is intentionally not implemented in this phase."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from app.core.converter import ImageConverter
from app.formats import register_image_plugins
from app.logging_config import configure_logging
from app.models import ConversionOptions


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="PixForge offline image converter (engine-only; no GUI in this phase)."
    )
    parser.add_argument("source", nargs="?", help="Source image path")
    parser.add_argument("--format", dest="output_format", default="JPG", help="Output format key, e.g. JPG or PNG")
    parser.add_argument("--out", dest="output_dir", default=".", help="Output directory")
    parser.add_argument("--quality", type=int, default=90)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    configure_logging()
    register_image_plugins()
    args = parse_args(argv)
    if not args.source:
        print("PixForge conversion engine is ready. GUI is not implemented yet.")
        print("Example: python main.py photo.heic --format JPG --out ./converted")
        return 0

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
