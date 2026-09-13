"""Tests for app.formats module."""
from app.formats import (
    EXTENSION_TO_FORMAT,
    INPUT_EXTENSIONS,
    OUTPUT_FORMAT_KEYS,
    SUPPORTED_FORMATS,
    format_for_extension,
    is_supported_input,
)


def test_supported_formats_contains_primary():
    assert "JPG" in SUPPORTED_FORMATS
    assert "PNG" in SUPPORTED_FORMATS
    assert "WEBP" in SUPPORTED_FORMATS
    assert "HEIC" in SUPPORTED_FORMATS
    assert "BMP" in SUPPORTED_FORMATS
    assert "TIFF" in SUPPORTED_FORMATS
    assert "GIF" in SUPPORTED_FORMATS


def test_format_for_extension():
    assert format_for_extension(".jpg") == "JPG"
    assert format_for_extension(".jpeg") == "JPG"
    assert format_for_extension(".png") == "PNG"
    assert format_for_extension(".webp") == "WEBP"
    assert format_for_extension(".heic") == "HEIC"
    assert format_for_extension(".heif") == "HEIC"
    assert format_for_extension(".unknown") is None


def test_is_supported_input():
    assert is_supported_input(".jpg") is True
    assert is_supported_input(".HEIC") is True
    assert is_supported_input(".png") is True
    assert is_supported_input(".exe") is False
    assert is_supported_input(".txt") is False


def test_output_formats_exclude_gif():
    assert "GIF" not in OUTPUT_FORMAT_KEYS
    assert "JPG" in OUTPUT_FORMAT_KEYS
    assert "PNG" in OUTPUT_FORMAT_KEYS
    assert "WEBP" in OUTPUT_FORMAT_KEYS
