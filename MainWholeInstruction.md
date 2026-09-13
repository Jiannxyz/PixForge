# PixForge

# Build Specification: Offline Batch Image Converter

Build a polished, native desktop application called **ImageForge**.

The application is an **offline image converter** capable of converting large batches of images between common image formats, especially HEIC/HEIF, JPG/JPEG, PNG, WEBP, GIF, BMP, TIFF, and AVIF where supported.

The application must NOT upload images to the internet or depend on an online server for conversion.

---

## 1. Main Goal

Create a desktop application where the user can:

1. Select one image.
2. Select many images at once.
3. Drag and drop a large number of images into the application.
4. Select an entire folder of images.
5. Choose an output format.
6. Convert all selected images in batch.
7. Choose an output folder.
8. See conversion progress.
9. See which files succeeded or failed.
10. Open the output folder when conversion is complete.

The application should feel similar to a modern professional utility such as a simple version of HandBrake/ImageMagick GUI, but focused specifically on image conversion.

---

# 2. IMPORTANT ARCHITECTURE REQUIREMENT

This is an OFFLINE-FIRST application.

Do NOT create:

- a web server
- Flask backend
- FastAPI backend
- database
- cloud storage
- API calls
- online image conversion services
- image uploads to external servers

All image processing must happen locally on the user's computer.

The application must continue working when the computer has no internet connection.

---

# 3. Recommended Technology Stack

Use:

- Python 3.11+
- PySide6 for the desktop GUI
- Pillow for general image processing
- pillow-heif for HEIC/HEIF support
- pathlib for filesystem operations
- concurrent.futures or QThreadPool for background processing
- zipfile only if needed for optional ZIP export

Use a clean modular architecture.

Recommended packages:

```text
PySide6
Pillow
pillow-heif

```

Register the HEIF plugin at application startup:

```python
from pillow_heif import register_heif_opener

register_heif_opener()

```

Do not hard-code unsupported formats. Create a central format registry so supported formats can easily be extended.

---

# 4. Supported Formats

The first version should support:

### Input

- JPG
- JPEG
- PNG
- WEBP
- BMP
- TIFF
- TIF
- GIF
- HEIC
- HEIF
- AVIF where the installed Pillow/pillow-heif stack supports it

### Output

- JPG / JPEG
- PNG
- WEBP
- BMP
- TIFF
- HEIC
- HEIF
- AVIF where supported

Before processing a file, detect whether the format is actually supported.

If a format cannot be decoded or encoded, show:

```text
Unsupported format

```

instead of crashing.

---

# 5. GUI DESIGN

Create a modern clean interface.

Main window layout:

```text
┌────────────────────────────────────────────────────────────┐
│ ImageForge                              ⚙ Settings          │
├────────────────────────────────────────────────────────────┤
│                                                            │
│             DROP IMAGES HERE                              │
│                                                            │
│       Drag & drop images or folders here                  │
│                                                            │
│                 [ Add Images ]                             │
│                 [ Add Folder ]                             │
│                                                            │
├────────────────────────────────────────────────────────────┤
│ Files                                            24 images │
│                                                            │
│  ✓ photo1.heic       4032×3024    HEIC       Ready        │
│  ✓ photo2.jpg        1920×1080    JPG        Ready        │
│  ✓ photo3.png        1200×800     PNG        Ready        │
│                                                            │
├────────────────────────────────────────────────────────────┤
│ Output Format                                              │
│                                                            │
│  Convert to: [ JPG ▼ ]                                     │
│                                                            │
│  Quality:  [████████████████░░] 90                         │
│                                                            │
│  Output Folder:                                            │
│  C:\Users\User\Pictures\Converted                          │
│  [ Choose Folder ]                                         │
│                                                            │
├────────────────────────────────────────────────────────────┤
│                                                            │
│             [ CONVERT ALL ]                                │
│                                                            │
│ Overall Progress                                           │
│ [████████████████████░░░░░░] 78%                           │
│                                                            │
│ 19 / 24 completed                                          │
│                                                            │
└────────────────────────────────────────────────────────────┘

```

Use a professional dark/light theme.

Do not make the interface overly complicated.

---

# 6. Drag and Drop

The main window must accept:

- individual image files
- multiple image files
- folders

When a folder is dropped:

1. Ask whether to include images recursively.
2. Scan the folder.
3. Add all supported image files.
4. Avoid duplicate files.

Example:

```text
Dropped folder:
Vacation/

Vacation/
├── IMG001.HEIC
├── IMG002.HEIC
├── IMG003.JPG
└── Screenshots/
    ├── IMG004.PNG
    └── IMG005.JPG

```

If recursive mode is enabled, include everything.

---

# 7. Batch Processing

The application must support large batches.

Example:

```text
1 image
10 images
100 images
500 images
1000+ images

```

Do not process everything directly on the GUI thread.

Use background workers.

The UI must remain responsive while conversion is running.

Each file should have a status:

```text
WAITING
CONVERTING
COMPLETED
FAILED
SKIPPED

```

---

# 8. Conversion Pipeline

Create a dedicated conversion service.

Example architecture:

```text
GUI
 ↓
Conversion Manager
 ↓
Worker Queue
 ↓
Image Converter
 ↓
Pillow / pillow-heif
 ↓
Output File

```

Do not put conversion logic directly inside button click handlers.

---

# 9. Image Conversion Rules

Handle image modes correctly.

For JPEG:

- JPEG does not support transparency.
- If the source has an alpha channel, provide a configurable background color.
- Default background should be white.

For PNG:

- Preserve transparency when possible.

For WEBP:

- Support RGB and RGBA.

For HEIC:

- Use pillow-heif.
- Preserve image orientation.
- Preserve metadata when practical.
- Allow quality configuration.

For GIF:

- If the GIF is animated, do not silently destroy animation.
- Either:
  1. export the first frame and clearly warn the user, or
  2. implement animated conversion separately.

Prefer implementing a clear warning first rather than pretending animated conversion is fully supported.

---

# 10. EXIF Orientation

This is extremely important.

Some phone images, especially HEIC images, contain orientation metadata.

Before saving the converted image, correctly handle EXIF orientation.

Use:

```python
from PIL import ImageOps

image = ImageOps.exif_transpose(image)

```

Do not produce rotated or sideways photos after conversion.

---

# 11. Metadata

Attempt to preserve metadata when technically possible.

Important metadata:

- EXIF
- XMP
- IPTC

Do not promise perfect metadata preservation across every format.

When metadata cannot be preserved, conversion should still succeed.

Provide an optional setting:

```text
☑ Preserve metadata

```

Default:

```text
ON

```

---

# 12. JPEG Quality

When output format is JPG/JPEG, display:

```text
Quality: 1–100

```

Default:

```text
90

```

Allow the user to change it.

Use reasonable Pillow JPEG settings:

```python
image.save(
    output_path,
    "JPEG",
    quality=quality,
    optimize=True
)

```

Convert incompatible modes such as RGBA to RGB before saving JPEG.

---

# 13. PNG Settings

For PNG:

Provide an optional compression setting.

Example:

```text
PNG Compression
[ 6 ]

```

Range:

```text
0–9

```

Default:

```text
6

```

Do not reduce image dimensions.

---

# 14. HEIC Settings

When converting TO HEIC:

Provide:

```text
HEIC Quality
[ 80 ]

```

Allow approximately:

```text
1–100

```

Use pillow-heif's HEIC encoder.

Do not manually shell out to an internet service.

---

# 15. Output Naming

Default:

```text
original_name.converted.extension

```

Example:

```text
IMG_1234.HEIC

```

becomes:

```text
IMG_1234.converted.jpg

```

Also provide an option:

```text
Naming:
○ original.converted.ext
○ original.ext
○ custom prefix

```

---

# 16. Duplicate Filename Handling

Never overwrite files accidentally.

If:

```text
photo.converted.jpg

```

already exists:

automatically create:

```text
photo.converted (1).jpg
photo.converted (2).jpg

```

Unless the user explicitly enables:

```text
☑ Overwrite existing files

```

---

# 17. Conversion Preview

When files are added, display:

- filename
- thumbnail
- dimensions
- file size
- detected format
- status

Example:

```text
┌──────┐
│ IMG  │  IMG_001.HEIC
│      │  4032 × 3024
└──────┘  2.4 MB
          HEIC
          Ready

```

Generate thumbnails efficiently.

Do not load full-resolution images into the preview list.

---

# 18. File Management Controls

Provide:

```text
[ Add Images ]
[ Add Folder ]
[ Remove Selected ]
[ Clear All ]

```

Also:

```text
☑ Include subfolders

```

and:

```text
☑ Automatically remove duplicates

```

---

# 19. Sorting and Filtering

Allow sorting by:

- filename
- format
- size
- dimensions
- status

Provide a search box:

```text
Search files...

```

This is especially useful when hundreds of images are loaded.

---

# 20. Progress System

Show:

### Per-file progress

```text
IMG_002.HEIC
Converting...

```

### Overall progress

```text
37 / 100
[██████████████░░░░░░]

```

Calculate:

```text
completed / total

```

At completion:

```text
Conversion complete

100 files processed
96 successful
3 failed
1 skipped

```

---

# 21. Error Handling

Never crash the whole batch because one image is broken.

Example:

```text
✗ damaged_image.heic
Error: Unable to decode image

```

Continue processing the remaining images.

Provide:

```text
[ View Errors ]

```

The error panel should contain:

```text
Filename
Error
Reason

```

Example:

```text
damaged.heic
Unable to identify image file

unsupported.xyz
Unsupported format

```

---

# 22. Cancel Button

While conversion is running:

```text
[ Cancel ]

```

must be visible.

When clicked:

- stop starting new conversions
- allow the current operation to safely finish if necessary
- mark remaining files as cancelled
- return the application to an idle state

Never abruptly terminate the whole Python process.

---

# 23. Open Output Folder

After conversion:

```text
[ Open Output Folder ]

```

Use the platform's native file manager.

Windows example:

```python
os.startfile(output_folder)

```

Add macOS/Linux handling too.

---

# 24. Settings

Create a Settings dialog.

Possible settings:

```text
General
────────────────────────

Default output folder
☑ Preserve metadata
☑ Automatically open output folder
☑ Remember last format

Performance
────────────────────────

Worker threads: [ Auto ▼ ]

JPEG
────────────────────────

Default quality: [90]

PNG
────────────────────────

Default compression: [6]

HEIC
────────────────────────

Default quality: [80]

```

Store settings locally using QSettings.

Do not create a database.

---

# 25. Offline Requirement

The application must not make network requests.

Do not use:

- cloud APIs
- online converters
- telemetry
- remote image processing
- external upload services

The application should work completely offline after installation.

---

# 26. Performance

Optimize for batch conversion.

Requirements:

- GUI remains responsive.
- Conversion happens in background workers.
- Do not load all full-resolution images into RAM simultaneously.
- Release image resources after each conversion.
- Use thumbnails rather than full-size preview images.
- Avoid unnecessary image copies.
- Process files independently so one failure does not terminate the queue.

For example:

```text
100 images
↓
Worker Queue
↓
Worker 1 → Image
Worker 2 → Image
Worker 3 → Image
Worker 4 → Image

```

Make the number of workers configurable.

Default to:

```text
min(4, CPU_count)

```

or another safe automatic value.

---

# 27. Project Structure

Use this structure:

```text
imageforge/
│
├── main.py
│
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── formats.py
│   ├── models.py
│   │
│   ├── core/
│   │   ├── converter.py
│   │   ├── conversion_manager.py
│   │   ├── metadata.py
│   │   ├── thumbnails.py
│   │   └── validators.py
│   │
│   ├── workers/
│   │   └── conversion_worker.py
│   │
│   ├── ui/
│   │   ├── main_window.py
│   │   ├── settings_dialog.py
│   │   ├── drop_zone.py
│   │   ├── file_list.py
│   │   └── widgets.py
│   │
│   └── utils/
│       ├── filesystem.py
│       └── platform.py
│
├── assets/
│   └── icons/
│
├── tests/
│   ├── test_converter.py
│   ├── test_formats.py
│   └── test_naming.py
│
├── requirements.txt
├── README.md
└── .gitignore

```

Keep responsibilities separated.

---

# 28. Important Design Principle

Do NOT generate a giant single-file Python program.

I want maintainable code.

The GUI should not know the implementation details of HEIC conversion.

For example:

```text
UI
 ↓
ConversionManager
 ↓
Converter
 ↓
Format Handler

```

This makes it possible to add formats later without rewriting the interface.

---

# 29. Format Registry

Create something similar to:

```python
SUPPORTED_FORMATS = {
    "JPG": {
        "extensions": [".jpg", ".jpeg"],
        "supports_alpha": False,
    },

    "PNG": {
        "extensions": [".png"],
        "supports_alpha": True,
    },

    "WEBP": {
        "extensions": [".webp"],
        "supports_alpha": True,
    },

    "HEIC": {
        "extensions": [".heic", ".heif"],
        "supports_alpha": True,
    },
}

```

Do not scatter format checks throughout the application.

---

# 30. Security / Safety

Treat every input file as untrusted.

Validate file paths.

Do not execute files.

Do not run arbitrary shell commands based on filenames.

Use safe output paths.

Avoid path traversal issues.

---

# 31. User Experience

The application should be understandable without documentation.

Ideal workflow:

```text
1. Open ImageForge
2. Drag 50 HEIC files
3. Choose JPG
4. Choose output folder
5. Click Convert All
6. Wait for progress to finish
7. Open output folder

```

A new user should understand this immediately.

---

# 32. Empty State

When no files have been added:

```text
Convert Images Offline

Drag & drop your images here

Supports:
HEIC • JPG • PNG • WEBP • GIF • TIFF • BMP • AVIF

Everything is processed locally.
Your images never leave your computer.

[ Add Images ]
[ Add Folder ]

```

---

# 33. Completion Screen

After conversion:

```text
✓ Conversion Complete

Successfully converted: 47
Failed: 2
Skipped: 1

Output:
C:\Users\User\Pictures\Converted

[ Open Output Folder ]
[ Convert More Images ]

```

---

# 34. Testing

Create automated tests for:

1. JPG → PNG
2. PNG → JPG
3. HEIC → JPG
4. HEIC → PNG
5. JPG → HEIC
6. PNG → HEIC
7. WEBP → JPG
8. TIFF → PNG
9. transparency handling
10. EXIF orientation
11. duplicate filenames
12. invalid images
13. unsupported extensions
14. empty queue
15. cancelling a batch
16. 100+ image batch

Do not rely only on manual testing.

---

# 35. Logging

Add application logging.

Example:

```text
logs/
    imageforge.log

```

Log:

- application startup
- files added
- conversion success
- conversion failures
- exceptions
- cancellation
- settings errors

Do not log image contents.

---

# 36. Packaging

The final application should be distributable as a Windows executable.

Prefer:

```text
PyInstaller

```

Create a build configuration.

The final user should be able to run:

```text
ImageForge.exe

```

without installing Python manually.

Make sure the HEIC libraries and required binaries are included in the packaged application.

Do not assume that `python imageforge` is sufficient for the final user.

---

# 37. README

Create a complete README containing:

- project description
- features
- supported formats
- installation
- development setup
- running the application
- building the executable
- architecture
- troubleshooting
- limitations
- licensing/dependency notes

Clearly document that image processing happens locally.

---

# 38. Development Rules

Before writing code:

1. Inspect the repository.
2. Create the project architecture.
3. Create requirements.txt.
4. Implement the image conversion engine.
5. Test conversion independently.
6. Implement the GUI.
7. Connect the GUI to the conversion engine.
8. Add batch processing.
9. Add error handling.
10. Add settings.
11. Add packaging.
12. Run tests.

Do NOT skip straight to a huge GUI implementation.

---

# 39. Vibe-Coding Behavior

When implementing:

- Explain what you are changing before major architectural changes.
- Make small, logically separated changes.
- Do not rewrite working code unnecessarily.
- Do not replace libraries without a reason.
- Do not remove features just to make errors disappear.
- When an error occurs, identify the root cause first.
- Keep functions small and testable.
- Keep UI and business logic separate.

After every major feature, run the relevant tests.

---

# 40. First Implementation Task

Start with ONLY the foundation.

Implement:

```text
project structure
requirements.txt
format registry
image conversion engine
HEIC support
JPG support
PNG support
WEBP support
basic tests

```

Do NOT implement the complete GUI yet.

At the end, demonstrate that these conversions work:

```text
HEIC → JPG
HEIC → PNG
JPG → PNG
PNG → JPG
PNG → HEIC
JPG → HEIC

```

After the conversion engine is confirmed working, proceed to the desktop GUI.