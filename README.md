# PixForge — Offline Image Converter

PixForge is a **fully offline** desktop image converter. All processing happens on your computer. There is no web server, database, cloud API, telemetry, or online conversion service.

This repository currently contains **Phase 1: conversion engine**. The desktop GUI is not implemented yet.

## Features (this phase)

- Local conversion between JPG/JPEG, PNG, WEBP, BMP, TIFF, and HEIC/HEIF
- Format registry (supported types live in one place)
- EXIF orientation correction
- JPEG transparency flattening (default white background)
- Best-effort metadata preservation (EXIF / ICC / XMP when Pillow can write them)
- Safe output names (`original.converted.ext`) with duplicate numbering
- Unit tests for the conversion engine

## Requirements

- Python 3.11+
- See `requirements.txt` (`PySide6`, `Pillow`, `pillow-heif`, `pytest`)

PySide6 is included now so the later GUI phase can use it. The engine does not depend on Qt.

## Setup

```text
python -m pip install -r requirements.txt
```

## Run the engine

```text
python main.py
python main.py photo.heic --format JPG --out ./converted
```

## Tests

```text
python -m pytest
```

## Architecture

Conversion is independent from any UI:

```text
CLI / future GUI
    → ConversionManager
        → ImageConverter
            → Pillow / pillow-heif
```

HEIF support is registered with `pillow_heif.register_heif_opener()`.

## Limitations

- Animated GIF/TIFF: only the first frame is converted, with a warning.
- AVIF is registered when the installed pillow-heif build supports it.
- Metadata is preserved only when the target format and Pillow encoder allow it.
- Perfect EXIF/XMP/IPTC round-trips are not guaranteed across every format pair.
- No GUI, settings window, or Windows executable in this phase.

## License notes

Pillow, PySide6, and pillow-heif are third-party libraries. Use them under their respective licenses.
