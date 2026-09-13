# PixForge — Fast Offline Batch Image Converter

PixForge is a **production-quality, fully offline** desktop image converter built with Python, PySide6 (Qt6), Pillow, and `pillow-heif`. All processing happens locally on your machine with multithreaded performance. There are no web servers, databases, cloud APIs, telemetry, or third-party networks involved.

Developed by **Jian Alvarez** ([GitHub](https://github.com/Jiannxyz)).

---

## Features

- **Full Batch Processing**: Convert single images, multiple selected images, or whole folders with optional recursive folder scanning.
- **Drag-and-Drop Workflow**: Intuitive drag-and-drop zone with instant thumbnail generation and image inspection in a background thread pool.
- **Supported Formats**: Full read & write conversion support for **JPG/JPEG**, **PNG**, **WEBP**, **HEIC/HEIF**, **BMP**, and **TIFF** (plus GIF decoding).
- **HEIC / HEIF Ready**: Native HEIC/HEIF decoding and encoding powered by `libheif` via `pillow-heif`.
- **Quality & Format Controls**: Format-specific tuning for JPEG/HEIC/WEBP quality (1–100) and PNG compression (0–9), with metadata preservation (EXIF, IPTC, ICC) and collision-safe file naming.
- **Responsive Modern UI**: Modern dark & light themes, search and sort filters, row checkboxes with "Select All" and "Remove Selected", detailed error viewer, and persistent user preferences via `QSettings`.
- **Single-File Distribution**: Standalone portable Windows executable (`PixForge.exe`) that requires no Python installation.

---

## Running from Source

### Requirements
- Python 3.11+
- Virtual environment (recommended)

### Installation
```bash
# Clone the repository
git clone https://github.com/Jiannxyz/PixForge.git
cd PixForge

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Launch GUI
```bash
python main.py
```

### Headless / CLI Conversion Mode
PixForge also provides a command-line interface for scripts and automation:
```bash
# Convert a single image
python main.py -i input.heic -o ./output -f JPG

# Convert an entire folder recursively
python main.py -i ./Photos -o ./Converted -f WEBP -q 85 -r --overwrite
```

---

## Automated Tests

Run the full pytest suite (covering conversion engine, batch processing, naming, formats, and GUI components):
```bash
pytest -v
```

---

## Building the Windows Executable (`PixForge.exe`)

PixForge uses **PyInstaller** with a customized build specification (`PixForge.spec`) to bundle the complete Python runtime, PySide6 libraries, Pillow plugins, `pillow-heif`, bundled native `libheif` dynamic link libraries (DLLs), and UI assets into a single standalone `.exe`.

### 1. Install Build Dependencies
```bash
pip install pyinstaller
```

### 2. Build Executable
Run PyInstaller using the provided spec file:
```bash
pyinstaller --clean -y PixForge.spec
```

The output executable will be created at:
```text
dist/PixForge.exe
```

### Build Configuration Highlights (`PixForge.spec`)
- **HEIC Dynamic Libraries**: Explicitly gathers `libheif*.dll` and `_pillow_heif*.pyd` from `site-packages` into the executable root.
- **Assets & Icons**: Bundles `app/resources/icons/*` (including transparent and background logos, upload icons, and custom control assets).
- **Application Icon**: Embeds `app/resources/icons/PixForge.ico` as the native Windows application icon.
- **No Python Required**: Users can double-click and run `PixForge.exe` on any 64-bit Windows machine without installing Python or any extra runtimes.

---

## Verifying Executable Conversions

You can test both GUI and CLI functionality directly with the packaged binary:

```bash
# Verify JPG -> HEIC conversion
dist\PixForge.exe -i sample.jpg -o ./output -f HEIC --overwrite

# Verify HEIC -> JPG conversion
dist\PixForge.exe -i sample.heic -o ./output -f JPG --overwrite
```

---

## License & Credits

- **Developer**: Jian Alvarez ([https://github.com/Jiannxyz](https://github.com/Jiannxyz))
- Built with PySide6 (LGPLv3), Pillow (HPND), and pillow-heif (LGPLv3 / Apache 2.0).
