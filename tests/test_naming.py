from pathlib import Path

from app.models import ConversionOptions, NamingMode
from app.utils.filesystem import build_output_path, sanitize_filename_stem


def test_default_converted_suffix(tmp_path: Path):
    options = ConversionOptions(output_format="JPG", output_dir=tmp_path)
    path = build_output_path(tmp_path / "IMG_1234.HEIC", options)
    assert path.name == "IMG_1234.converted.jpg"


def test_original_naming(tmp_path: Path):
    options = ConversionOptions(
        output_format="PNG",
        output_dir=tmp_path,
        naming_mode=NamingMode.ORIGINAL,
    )
    path = build_output_path(tmp_path / "photo.jpeg", options)
    assert path.name == "photo.png"


def test_prefix_naming(tmp_path: Path):
    options = ConversionOptions(
        output_format="WEBP",
        output_dir=tmp_path,
        naming_mode=NamingMode.PREFIX,
        custom_prefix="pix_",
    )
    path = build_output_path(tmp_path / "cat.png", options)
    assert path.name == "pix_cat.webp"


def test_duplicate_names_get_counter(tmp_path: Path):
    options = ConversionOptions(output_format="JPG", output_dir=tmp_path, overwrite=False)
    first = build_output_path(tmp_path / "photo.png", options)
    first.write_bytes(b"x")
    second = build_output_path(tmp_path / "photo.png", options)
    third = build_output_path(tmp_path / "photo.png", options)
    second.write_bytes(b"x")
    third = build_output_path(tmp_path / "photo.png", options)
    assert first.name == "photo.converted.jpg"
    assert second.name == "photo.converted (1).jpg"
    assert third.name == "photo.converted (2).jpg"


def test_overwrite_reuses_name(tmp_path: Path):
    options = ConversionOptions(output_format="JPG", output_dir=tmp_path, overwrite=True)
    first = build_output_path(tmp_path / "photo.png", options)
    first.write_bytes(b"x")
    second = build_output_path(tmp_path / "photo.png", options)
    assert first == second


def test_sanitize_dangerous_stem():
    assert "/" not in sanitize_filename_stem("a/b\\c:d")
    assert sanitize_filename_stem("...") == "image"
