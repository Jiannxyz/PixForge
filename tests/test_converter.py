"""Tests for app.core.converter module."""
from pathlib import Path
from PIL import Image, ImageOps
import pytest

from app.core.converter import ImageConverter
from app.models import ConversionOptions


@pytest.fixture
def converter():
    return ImageConverter()


@pytest.fixture
def sample_rgb_image(tmp_path):
    p = tmp_path / "rgb.png"
    img = Image.new("RGB", (100, 100), color=(255, 0, 0))
    img.save(p)
    return p


@pytest.fixture
def sample_rgba_image(tmp_path):
    p = tmp_path / "rgba.png"
    img = Image.new("RGBA", (100, 100), color=(0, 255, 0, 128))
    img.save(p)
    return p


def test_convert_rgb_png_to_jpg(converter, sample_rgb_image, tmp_path):
    out_dir = tmp_path / "out"
    opts = ConversionOptions(output_format="JPG", output_dir=out_dir)
    res = converter.convert(sample_rgb_image, opts)
    assert res.success is True
    assert res.output_path.exists()
    assert res.output_path.suffix.lower() in [".jpg", ".jpeg"]
    with Image.open(res.output_path) as out_img:
        assert out_img.format == "JPEG"


def test_convert_rgba_to_jpg_flattens_alpha(converter, sample_rgba_image, tmp_path):
    out_dir = tmp_path / "out"
    opts = ConversionOptions(output_format="JPG", output_dir=out_dir)
    res = converter.convert(sample_rgba_image, opts)
    assert res.success is True
    assert res.output_path.exists()
    with Image.open(res.output_path) as out_img:
        assert out_img.mode == "RGB"


def test_convert_to_png_and_webp(converter, sample_rgb_image, tmp_path):
    out_dir = tmp_path / "out"
    opts_png = ConversionOptions(output_format="PNG", output_dir=out_dir)
    res_png = converter.convert(sample_rgb_image, opts_png)
    assert res_png.success is True
    assert res_png.output_path.suffix == ".png"

    opts_webp = ConversionOptions(output_format="WEBP", output_dir=out_dir)
    res_webp = converter.convert(sample_rgb_image, opts_webp)
    assert res_webp.success is True
    assert res_webp.output_path.suffix == ".webp"


def test_convert_to_heic(converter, sample_rgb_image, tmp_path):
    out_dir = tmp_path / "out"
    opts = ConversionOptions(output_format="HEIC", output_dir=out_dir)
    res = converter.convert(sample_rgb_image, opts)
    assert res.success is True
    assert res.output_path.suffix in [".heic", ".heif"]


def test_convert_heic_to_jpg_and_png(converter, tmp_path):
    src_png = tmp_path / "src.png"
    img = Image.new("RGB", (60, 60), color=(10, 20, 30))
    img.save(src_png)

    # First convert to HEIC
    heic_out = tmp_path / "out_heic"
    opts_heic = ConversionOptions(output_format="HEIC", output_dir=heic_out)
    res_heic = converter.convert(src_png, opts_heic)
    assert res_heic.success is True

    # Now convert HEIC -> JPG
    jpg_out = tmp_path / "out_jpg"
    opts_jpg = ConversionOptions(output_format="JPG", output_dir=jpg_out)
    res_jpg = converter.convert(res_heic.output_path, opts_jpg)
    assert res_jpg.success is True
    assert res_jpg.output_path.suffix.lower() in [".jpg", ".jpeg"]

    # Now convert HEIC -> PNG
    png_out = tmp_path / "out_png"
    opts_png = ConversionOptions(output_format="PNG", output_dir=png_out)
    res_png = converter.convert(res_heic.output_path, opts_png)
    assert res_png.success is True
    assert res_png.output_path.suffix == ".png"


def test_convert_bmp_and_tiff(converter, tmp_path):
    p = tmp_path / "test.png"
    img = Image.new("RGB", (50, 50), color=(100, 100, 100))
    img.save(p)

    out_dir = tmp_path / "out_others"
    # To BMP
    opts_bmp = ConversionOptions(output_format="BMP", output_dir=out_dir)
    res_bmp = converter.convert(p, opts_bmp)
    assert res_bmp.success is True
    assert res_bmp.output_path.suffix == ".bmp"

    # To TIFF
    opts_tiff = ConversionOptions(output_format="TIFF", output_dir=out_dir)
    res_tiff = converter.convert(p, opts_tiff)
    assert res_tiff.success is True
    assert res_tiff.output_path.suffix in [".tiff", ".tif"]


def test_convert_gif_first_frame(converter, tmp_path):
    gif_path = tmp_path / "test.gif"
    img = Image.new("RGB", (50, 50), color=(200, 50, 50))
    img.save(gif_path, format="GIF")

    out_dir = tmp_path / "out_gif"
    opts = ConversionOptions(output_format="JPG", output_dir=out_dir)
    res = converter.convert(gif_path, opts)
    assert res.success is True


def test_convert_invalid_image_fails_safely(converter, tmp_path):
    corrupt = tmp_path / "corrupt.jpg"
    corrupt.write_bytes(b"NOT_AN_IMAGE_CONTENT")
    out_dir = tmp_path / "out"
    opts = ConversionOptions(output_format="PNG", output_dir=out_dir)
    res = converter.convert(corrupt, opts)
    assert res.success is False
    assert res.error is not None
