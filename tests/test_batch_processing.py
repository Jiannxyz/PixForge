"""Comprehensive tests for batch processing, thread-safety, and queue edge cases."""
import threading
from pathlib import Path
from PIL import Image
import pytest

from app.core.conversion_manager import ConversionManager
from app.models import ConversionOptions


def create_dummy_images(folder: Path, count: int, prefix: str = "img", mode: str = "RGB", fmt: str = "PNG") -> list[Path]:
    folder.mkdir(parents=True, exist_ok=True)
    paths = []
    for i in range(count):
        p = folder / f"{prefix}_{i:03d}.{fmt.lower()}"
        img = Image.new(mode, (50, 50), color=(i % 255, 100, 150))
        img.save(p, format=fmt)
        paths.append(p)
    return paths


def test_batch_10_images(tmp_path):
    src_dir = tmp_path / "src_10"
    out_dir = tmp_path / "out_10"
    paths = create_dummy_images(src_dir, 10, prefix="batch10")

    manager = ConversionManager()
    opts = ConversionOptions(output_format="JPG", output_dir=out_dir)

    done_counter = 0
    def _prog(res, done, total):
        nonlocal done_counter
        done_counter = done

    results = manager.convert_batch(paths, opts, progress=_prog)
    assert len(results) == 10
    assert all(r.success for r in results)
    assert done_counter == 10
    assert len(list(out_dir.glob("*.jpg"))) == 10


def test_batch_50_images(tmp_path):
    src_dir = tmp_path / "src_50"
    out_dir = tmp_path / "out_50"
    paths = create_dummy_images(src_dir, 50, prefix="batch50")

    manager = ConversionManager()
    opts = ConversionOptions(output_format="WEBP", output_dir=out_dir)
    results = manager.convert_batch(paths, opts)
    assert len(results) == 50
    assert all(r.success for r in results)
    assert len(list(out_dir.glob("*.webp"))) == 50


def test_mixed_formats_batch(tmp_path):
    src_dir = tmp_path / "src_mixed"
    out_dir = tmp_path / "out_mixed"
    src_dir.mkdir(parents=True, exist_ok=True)

    paths = []
    for i, (fmt, mode) in enumerate([("PNG", "RGBA"), ("JPEG", "RGB"), ("BMP", "RGB"), ("TIFF", "RGB")]):
        p = src_dir / f"mixed_{i}.{fmt.lower()}"
        img = Image.new(mode, (40, 40), color=(50, 50, 50))
        img.save(p, format=fmt)
        paths.append(p)

    manager = ConversionManager()
    opts = ConversionOptions(output_format="PNG", output_dir=out_dir)
    results = manager.convert_batch(paths, opts)
    assert len(results) == 4
    assert all(r.success for r in results)


def test_fault_tolerance_with_corrupt_files(tmp_path):
    src_dir = tmp_path / "src_fault"
    out_dir = tmp_path / "out_fault"
    src_dir.mkdir(parents=True, exist_ok=True)

    # 3 valid images
    valid_paths = create_dummy_images(src_dir, 3, prefix="valid")

    # 2 corrupt files
    corrupt1 = src_dir / "broken1.jpg"
    corrupt1.write_bytes(b"")  # 0 byte
    corrupt2 = src_dir / "broken2.png"
    corrupt2.write_text("Hello not an image!")

    all_paths = [valid_paths[0], corrupt1, valid_paths[1], corrupt2, valid_paths[2]]

    manager = ConversionManager()
    opts = ConversionOptions(output_format="WEBP", output_dir=out_dir)
    results = manager.convert_batch(all_paths, opts)

    assert len(results) == 5
    succeeded = [r for r in results if r.success]
    failed = [r for r in results if not r.success]

    assert len(succeeded) == 3
    assert len(failed) == 2


def test_duplicate_filenames_in_batch(tmp_path):
    dir_a = tmp_path / "dir_a"
    dir_b = tmp_path / "dir_b"
    out_dir = tmp_path / "out_dup"

    img_a = create_dummy_images(dir_a, 1, prefix="same_name")[0]
    img_b = create_dummy_images(dir_b, 1, prefix="same_name")[0]

    manager = ConversionManager()
    opts = ConversionOptions(output_format="JPG", output_dir=out_dir, overwrite=False)

    results = manager.convert_batch([img_a, img_b], opts)
    assert len(results) == 2
    assert all(r.success for r in results)

    out_files = list(out_dir.glob("*.jpg"))
    assert len(out_files) == 2
    names = [f.name for f in out_files]
    assert any("(1)" in name for name in names)


def test_batch_cancellation(tmp_path):
    src_dir = tmp_path / "src_cancel"
    out_dir = tmp_path / "out_cancel"
    paths = create_dummy_images(src_dir, 20, prefix="cancel")

    cancel_event = threading.Event()
    manager = ConversionManager()
    opts = ConversionOptions(output_format="PNG", output_dir=out_dir)

    def _on_started(p):
        cancel_event.set()

    results = manager.convert_batch(paths, opts, cancel_event=cancel_event, job_started=_on_started, max_workers=1)
    assert any(r.skipped for r in results)
