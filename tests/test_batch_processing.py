"""Comprehensive test suite for Phase 3 — Batch Processing."""

from __future__ import annotations

import os
from pathlib import Path
from threading import Event

import pytest
from PIL import Image

from app.core.conversion_manager import ConversionManager
from app.core.converter import ImageConverter
from app.formats import can_encode
from app.models import ConversionOptions, FileStatus, ImageJob
from app.ui.main_window import MainWindow
from app.utils.filesystem import collect_image_paths
from tests.conftest import save_rgb, save_rgba

os.environ["QT_QPA_PLATFORM"] = "offscreen"


def test_batch_ten_images(tmp_path: Path, tmp_output: Path):
    """Test batch conversion of 10 images."""
    sources = [save_rgb(tmp_path / f"img_{i:02d}.png", size=(16, 16)) for i in range(10)]
    manager = ConversionManager(max_workers=3)
    options = ConversionOptions(output_format="JPG", output_dir=tmp_output)

    results = manager.convert_batch(sources, options)
    assert len(results) == 10
    assert all(r.success for r in results)
    assert sum(1 for r in results if r.success) == 10
    assert sum(1 for r in results if r.skipped) == 0

    # Verify all 10 output files exist on disk
    for r in results:
        assert r.output_path is not None
        assert r.output_path.exists()
        assert r.output_path.suffix == ".jpg"


def test_batch_fifty_images(tmp_path: Path, tmp_output: Path):
    """Test high-volume batch conversion of 50 images with 4 concurrent workers."""
    sources = [save_rgb(tmp_path / f"batch50_{i:03d}.jpg", size=(12, 12)) for i in range(50)]
    manager = ConversionManager(max_workers=4)
    options = ConversionOptions(output_format="PNG", output_dir=tmp_output)

    completed_jobs = []

    def on_progress(job: ImageJob):
        completed_jobs.append(job)

    results = manager.convert_batch(sources, options, progress=on_progress)

    assert len(results) == 50
    assert len(completed_jobs) == 50
    assert all(r.success for r in results)

    # Check that each file in the output directory is a valid PNG
    output_files = list(tmp_output.glob("*.png"))
    assert len(output_files) == 50
    for out_file in output_files:
        with Image.open(out_file) as img:
            assert img.format == "PNG"
            assert img.size == (12, 12)


def test_batch_mixed_formats(tmp_path: Path, tmp_output: Path):
    """Test batch conversion of mixed input formats (JPG, PNG, WEBP, BMP, TIFF)."""
    img_jpg = save_rgb(tmp_path / "sample.jpg", size=(20, 20), color=(255, 0, 0))
    img_png = save_rgb(tmp_path / "sample.png", size=(20, 20), color=(0, 255, 0))
    img_webp = save_rgb(tmp_path / "sample.webp", size=(20, 20), color=(0, 0, 255))
    img_bmp = save_rgb(tmp_path / "sample.bmp", size=(20, 20), color=(255, 255, 0))
    img_tiff = save_rgb(tmp_path / "sample.tiff", size=(20, 20), color=(255, 0, 255))

    sources = [img_jpg, img_png, img_webp, img_bmp, img_tiff]

    # If HEIC is supported, add a HEIC file to the mixed batch
    if can_encode("HEIC"):
        converter = ImageConverter()
        heic_res = converter.convert(img_png, ConversionOptions(output_format="HEIC", output_dir=tmp_path))
        if heic_res.success and heic_res.output_path:
            sources.append(heic_res.output_path)

    manager = ConversionManager(max_workers=4)
    options = ConversionOptions(output_format="JPG", output_dir=tmp_output)

    results = manager.convert_batch(sources, options)
    assert len(results) == len(sources)
    assert all(r.success for r in results), [r.error for r in results if not r.success]

    for res in results:
        assert res.output_path is not None
        assert res.output_path.exists()
        with Image.open(res.output_path) as out:
            assert out.format == "JPEG"


def test_broken_image_does_not_stop_batch(tmp_path: Path, tmp_output: Path):
    """Verify that damaged or invalid images fail gracefully without terminating remaining conversions."""
    # 3 valid images
    valid1 = save_rgb(tmp_path / "good1.png", size=(10, 10))
    valid2 = save_rgb(tmp_path / "good2.png", size=(10, 10))
    valid3 = save_rgb(tmp_path / "good3.png", size=(10, 10))

    # 3 broken / invalid files
    broken_header = tmp_path / "corrupt_header.jpg"
    broken_header.write_bytes(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01notrealimagecontents!!")

    zero_byte = tmp_path / "empty.png"
    zero_byte.write_bytes(b"")

    non_image = tmp_path / "text_as_image.png"
    non_image.write_text("Hello this is plain text masquerading as PNG")

    sources = [valid1, broken_header, valid2, zero_byte, non_image, valid3]

    manager = ConversionManager(max_workers=2)
    options = ConversionOptions(output_format="JPG", output_dir=tmp_output)

    results = manager.convert_batch(sources, options)
    assert len(results) == 6

    # Count successes and failures
    successful = [r for r in results if r.success]
    failed = [r for r in results if not r.success and not r.skipped]

    assert len(successful) == 3
    assert len(failed) == 3

    # Ensure valid images were all converted properly
    successful_paths = {r.source_path.name for r in successful}
    assert successful_paths == {"good1.png", "good2.png", "good3.png"}

    for r in successful:
        assert r.output_path is not None
        assert r.output_path.exists()

    # Ensure failed files have non-empty error messages
    for r in failed:
        assert r.error is not None
        assert len(r.error) > 0


def test_duplicate_filenames_in_batch(tmp_path: Path, tmp_output: Path):
    """Test that two files with the same filename from different directories don't collide or overwrite."""
    dir_a = tmp_path / "sub_a"
    dir_b = tmp_path / "sub_b"
    dir_c = tmp_path / "sub_c"
    dir_a.mkdir()
    dir_b.mkdir()
    dir_c.mkdir()

    # Three files with the exact same name 'photo.png' in different directories
    file_a = save_rgb(dir_a / "photo.png", color=(100, 0, 0))
    file_b = save_rgb(dir_b / "photo.png", color=(0, 100, 0))
    file_c = save_rgb(dir_c / "photo.png", color=(0, 0, 100))

    manager = ConversionManager(max_workers=3)
    options = ConversionOptions(output_format="JPG", output_dir=tmp_output, overwrite=False)

    results = manager.convert_batch([file_a, file_b, file_c], options)
    assert len(results) == 3
    assert all(r.success for r in results)

    output_names = {r.output_path.name for r in results if r.output_path}
    assert len(output_names) == 3
    assert "photo.converted.jpg" in output_names
    assert "photo.converted (1).jpg" in output_names
    assert "photo.converted (2).jpg" in output_names


def test_transparency_in_batch(tmp_path: Path, tmp_output: Path):
    """Test converting transparent images to JPG (flattened to white) and PNG (transparency kept)."""
    alpha_img = save_rgba(tmp_path / "transparent.png")

    manager = ConversionManager(max_workers=2)

    # 1. Convert to JPG -> alpha flattened to white
    jpg_options = ConversionOptions(
        output_format="JPG",
        output_dir=tmp_output / "jpg_out",
        background_color=(255, 255, 255),
    )
    jpg_res = manager.convert_batch([alpha_img], jpg_options)
    assert len(jpg_res) == 1 and jpg_res[0].success
    with Image.open(jpg_res[0].output_path) as out:
        assert out.mode == "RGB"
        # Transparent pixel at (31, 12) should now be white background
        assert out.getpixel((31, 12)) == (255, 255, 255)
        # Opaque green pixel at (2, 12) remains green
        assert out.getpixel((2, 12))[1] > 200

    # 2. Convert to PNG -> transparency preserved
    png_options = ConversionOptions(output_format="PNG", output_dir=tmp_output / "png_out")
    png_res = manager.convert_batch([alpha_img], png_options)
    assert len(png_res) == 1 and png_res[0].success
    with Image.open(png_res[0].output_path) as out:
        assert out.mode == "RGBA"
        # Alpha channel intact at (31, 12)
        assert out.getpixel((31, 12))[3] == 0
        # Alpha channel intact at (2, 12)
        assert out.getpixel((2, 12))[3] == 255


@pytest.mark.skipif(not can_encode("HEIC"), reason="HEIC encoder not available")
def test_heic_batch_conversion(tmp_path: Path, tmp_output: Path):
    """Test batch conversion of HEIC files."""
    converter = ImageConverter()
    heic_sources = []
    for i in range(4):
        src = save_rgb(tmp_path / f"src_{i}.png", size=(24, 24))
        h_res = converter.convert(src, ConversionOptions(output_format="HEIC", output_dir=tmp_path))
        assert h_res.success and h_res.output_path
        heic_sources.append(h_res.output_path)

    manager = ConversionManager(max_workers=2)
    options = ConversionOptions(output_format="PNG", output_dir=tmp_output)

    results = manager.convert_batch(heic_sources, options)
    assert len(results) == 4
    assert all(r.success for r in results)
    for r in results:
        assert r.output_path.suffix == ".png"
        with Image.open(r.output_path) as out:
            assert out.size == (24, 24)


def test_batch_cancellation(tmp_path: Path, tmp_output: Path):
    """Test cancelling an active batch mid-flight."""
    sources = [save_rgb(tmp_path / f"canc_{i:02d}.png", size=(8, 8)) for i in range(15)]
    cancel_event = Event()

    processed_count = 0

    def on_progress(job: ImageJob):
        nonlocal processed_count
        processed_count += 1
        # Trigger cancel after 3 jobs complete
        if processed_count >= 3:
            cancel_event.set()

    manager = ConversionManager(max_workers=1)
    options = ConversionOptions(output_format="JPG", output_dir=tmp_output)

    results = manager.convert_batch(
        sources,
        options,
        cancel_event=cancel_event,
        progress=on_progress,
    )

    assert len(results) == 15
    successful = [r for r in results if r.success]
    skipped = [r for r in results if r.skipped]

    assert len(successful) >= 3
    assert len(skipped) > 0
    assert len(successful) + len(skipped) == 15


def test_recursive_vs_flat_folder_collection(tmp_path: Path):
    """Test folder scanning with and without recursion."""
    root = tmp_path / "photo_library"
    root.mkdir()
    sub1 = root / "2024"
    sub2 = root / "2025" / "Vacation"
    sub1.mkdir(parents=True)
    sub2.mkdir(parents=True)

    root_file = save_rgb(root / "root.jpg")
    sub1_file = save_rgb(sub1 / "sub1.png")
    sub2_file = save_rgb(sub2 / "sub2.webp")

    # Non-recursive: only root images
    flat_paths = collect_image_paths(root, recursive=False)
    assert len(flat_paths) == 1
    assert root_file in flat_paths
    assert sub1_file not in flat_paths

    # Recursive: all images in all subdirectories
    recursive_paths = collect_image_paths(root, recursive=True)
    assert len(recursive_paths) == 3
    assert root_file in recursive_paths
    assert sub1_file in recursive_paths
    assert sub2_file in recursive_paths


def test_gui_batch_with_duplicates_and_errors(qapp, tmp_path: Path, tmp_output: Path):
    """Verify GUI queue duplicate detection and failure reporting during batch."""
    window = MainWindow()
    window.show()

    img1 = save_rgb(tmp_path / "img1.png")
    img2 = save_rgb(tmp_path / "img2.png")
    bad = tmp_path / "corrupt.png"
    bad.write_text("corrupted content")

    # Add items, including a duplicate
    res1 = window.file_queue.add_paths([img1, img2])
    assert res1.added == 2
    assert res1.duplicates == 0

    res2 = window.file_queue.add_paths([img1, bad])
    assert res2.added == 1  # bad was added
    assert res2.duplicates == 1  # img1 duplicate was skipped
    window._notify_added(res2)
    assert "1 duplicate skipped" in window.status_info_label.text()

    assert window.file_queue.count == 3

    # Run batch conversion in GUI
    window.output_section.set_output_dir(tmp_output)
    window._start_conversion()
    assert window._active_worker is not None
    window._active_worker.wait(5000)
    qapp.processEvents()

    # 2 succeeded, 1 failed
    assert window.summary_banner.isVisible() is True
    assert window.view_errors_btn.isVisible() is True
    assert "2 successful, 1 failed" in window.summary_text.text()
    assert (tmp_output / "img1.converted.jpg").exists()
    assert (tmp_output / "img2.converted.jpg").exists()

    window.close()
