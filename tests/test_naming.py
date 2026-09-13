"""Tests for app.utils.filesystem module."""
from pathlib import Path

from app.models import NamingMode
from app.utils.filesystem import (
    build_output_path,
    collect_image_paths,
    sanitize_filename_stem,
    unique_path,
)


def test_sanitize_filename_stem():
    assert sanitize_filename_stem("normal_name") == "normal_name"
    assert sanitize_filename_stem("image:with*bad?chars") == "image_with_bad_chars"
    assert sanitize_filename_stem('test<name>|"/\\') == "test_name"


def test_build_output_path_converted_suffix(tmp_path):
    src = tmp_path / "photo.jpg"
    out_dir = tmp_path / "out"
    res = build_output_path(src, out_dir, "PNG", NamingMode.CONVERTED_SUFFIX)
    assert res == out_dir / "photo.converted.png"


def test_build_output_path_keep_stem(tmp_path):
    src = tmp_path / "photo.jpg"
    out_dir = tmp_path / "out"
    res = build_output_path(src, out_dir, "WEBP", NamingMode.KEEP_STEM)
    assert res == out_dir / "photo.webp"


def test_build_output_path_custom_prefix(tmp_path):
    src = tmp_path / "photo.jpg"
    out_dir = tmp_path / "out"
    res = build_output_path(src, out_dir, "JPG", NamingMode.CUSTOM_PREFIX, custom_prefix="thumb")
    assert res == out_dir / "thumb_photo.jpg"


def test_unique_path_counter(tmp_path):
    base = tmp_path / "file.txt"
    assert unique_path(base) == base

    base.touch()
    first_collision = unique_path(base)
    assert first_collision == tmp_path / "file (1).txt"

    first_collision.touch()
    second_collision = unique_path(base)
    assert second_collision == tmp_path / "file (2).txt"


def test_collect_image_paths_recursive(tmp_path):
    sub = tmp_path / "subdir"
    sub.mkdir()
    (tmp_path / "1.jpg").touch()
    (tmp_path / "2.png").touch()
    (tmp_path / "ignore.txt").touch()
    (sub / "3.heic").touch()

    # Non-recursive
    flat = collect_image_paths(tmp_path, recursive=False)
    assert len(flat) == 2
    assert tmp_path / "1.jpg" in flat
    assert tmp_path / "2.png" in flat

    # Recursive
    all_files = collect_image_paths(tmp_path, recursive=True)
    assert len(all_files) == 3
    assert sub / "3.heic" in all_files
