from pathlib import Path
from threading import Event

import pytest
from PIL import Image, ImageDraw

from app.core.conversion_manager import ConversionManager
from app.core.converter import ImageConverter, flatten_alpha
from app.formats import can_encode
from app.models import ConversionOptions
from tests.conftest import save_rgb, save_rgba

heif_available = pytest.mark.skipif(
    not can_encode("HEIC"),
    reason="HEIC encoder is not available in this Pillow/pillow-heif build",
)


@pytest.fixture
def converter() -> ImageConverter:
    return ImageConverter()


def _open_size(path: Path) -> tuple[int, int]:
    with Image.open(path) as image:
        return image.size


def test_jpg_to_png(converter: ImageConverter, tmp_path: Path, tmp_output: Path):
    source = save_rgb(tmp_path / "in.jpg")
    result = converter.convert(source, ConversionOptions(output_format="PNG", output_dir=tmp_output))
    assert result.success, result.error
    assert result.output_path.suffix == ".png"
    assert _open_size(result.output_path) == (32, 24)


def test_png_to_jpg(converter: ImageConverter, tmp_path: Path, tmp_output: Path):
    source = save_rgb(tmp_path / "in.png")
    result = converter.convert(source, ConversionOptions(output_format="JPG", output_dir=tmp_output))
    assert result.success, result.error
    assert result.output_path.suffix == ".jpg"


@heif_available
def test_heic_to_jpg(converter: ImageConverter, tmp_path: Path, tmp_output: Path):
    png = save_rgb(tmp_path / "src.png", color=(10, 20, 200))
    heic = converter.convert(png, ConversionOptions(output_format="HEIC", output_dir=tmp_path, heic_quality=70))
    assert heic.success, heic.error
    result = converter.convert(heic.output_path, ConversionOptions(output_format="JPG", output_dir=tmp_output))
    assert result.success, result.error
    assert result.output_path.suffix == ".jpg"


@heif_available
def test_heic_to_png(converter: ImageConverter, tmp_path: Path, tmp_output: Path):
    png = save_rgb(tmp_path / "src.png")
    heic = converter.convert(png, ConversionOptions(output_format="HEIC", output_dir=tmp_path))
    assert heic.success, heic.error
    result = converter.convert(heic.output_path, ConversionOptions(output_format="PNG", output_dir=tmp_output))
    assert result.success, result.error


@heif_available
def test_jpg_to_heic(converter: ImageConverter, tmp_path: Path, tmp_output: Path):
    source = save_rgb(tmp_path / "in.jpg")
    result = converter.convert(source, ConversionOptions(output_format="HEIC", output_dir=tmp_output))
    assert result.success, result.error
    assert result.output_path.suffix == ".heic"


@heif_available
def test_png_to_heic(converter: ImageConverter, tmp_path: Path, tmp_output: Path):
    source = save_rgb(tmp_path / "in.png")
    result = converter.convert(source, ConversionOptions(output_format="HEIC", output_dir=tmp_output))
    assert result.success, result.error


def test_webp_to_jpg(converter: ImageConverter, tmp_path: Path, tmp_output: Path):
    source = save_rgb(tmp_path / "in.webp")
    result = converter.convert(source, ConversionOptions(output_format="JPG", output_dir=tmp_output))
    assert result.success, result.error


def test_tiff_to_png(converter: ImageConverter, tmp_path: Path, tmp_output: Path):
    source = save_rgb(tmp_path / "in.tiff")
    result = converter.convert(source, ConversionOptions(output_format="PNG", output_dir=tmp_output))
    assert result.success, result.error


def test_bmp_roundtrip(converter: ImageConverter, tmp_path: Path, tmp_output: Path):
    source = save_rgb(tmp_path / "in.bmp")
    result = converter.convert(source, ConversionOptions(output_format="PNG", output_dir=tmp_output))
    assert result.success, result.error


def test_jpeg_transparency_uses_white_background(converter: ImageConverter, tmp_path: Path, tmp_output: Path):
    source = save_rgba(tmp_path / "alpha.png")
    result = converter.convert(
        source,
        ConversionOptions(output_format="JPG", output_dir=tmp_output, background_color=(255, 255, 255)),
    )
    assert result.success, result.error
    with Image.open(result.output_path) as image:
        rgb = image.convert("RGB")
        assert rgb.getpixel((31, 12)) == (255, 255, 255)
        assert rgb.getpixel((2, 12))[1] > 200


def test_flatten_alpha_custom_color():
    image = Image.new("RGBA", (4, 4), (0, 0, 0, 0))
    flat = flatten_alpha(image, (12, 34, 56))
    assert flat.mode == "RGB"
    assert flat.getpixel((0, 0)) == (12, 34, 56)


def test_png_keeps_transparency(converter: ImageConverter, tmp_path: Path, tmp_output: Path):
    source = save_rgba(tmp_path / "alpha.png")
    result = converter.convert(source, ConversionOptions(output_format="PNG", output_dir=tmp_output))
    assert result.success, result.error
    with Image.open(result.output_path) as image:
        converted = image.convert("RGBA")
        assert converted.getpixel((31, 12))[3] == 0


def test_exif_orientation_is_applied(converter: ImageConverter, tmp_path: Path, tmp_output: Path):
    source = tmp_path / "oriented.jpg"
    image = Image.new("RGB", (40, 20), (255, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 9, 19), fill=(0, 0, 255))
    exif = Image.Exif()
    exif[0x0112] = 6
    image.save(source, format="JPEG", exif=exif)
    result = converter.convert(source, ConversionOptions(output_format="PNG", output_dir=tmp_output))
    assert result.success, result.error
    assert _open_size(result.output_path) == (20, 40)


def test_invalid_image(converter: ImageConverter, tmp_path: Path, tmp_output: Path):
    source = tmp_path / "broken.jpg"
    source.write_bytes(b"this is not an image")
    result = converter.convert(source, ConversionOptions(output_format="PNG", output_dir=tmp_output))
    assert result.success is False
    assert result.error == "Invalid image"


def test_unsupported_extension(converter: ImageConverter, tmp_path: Path, tmp_output: Path):
    source = tmp_path / "notes.txt"
    source.write_text("hello")
    result = converter.convert(source, ConversionOptions(output_format="PNG", output_dir=tmp_output))
    assert result.success is False
    assert result.error == "Unsupported format"


def test_empty_queue(tmp_output: Path):
    manager = ConversionManager(max_workers=1)
    results = manager.convert_batch([], ConversionOptions(output_format="JPG", output_dir=tmp_output))
    assert results == []


def test_cancel_batch(tmp_path: Path, tmp_output: Path):
    sources = [save_rgb(tmp_path / f"{i}.png") for i in range(5)]
    cancel = Event()
    cancel.set()
    results = ConversionManager(max_workers=1).convert_batch(
        sources,
        ConversionOptions(output_format="JPG", output_dir=tmp_output),
        cancel_event=cancel,
    )
    assert all(item.skipped for item in results)


def test_batch_of_one_hundred(tmp_path: Path, tmp_output: Path):
    sources = [save_rgb(tmp_path / f"img_{i:03d}.png", size=(8, 8)) for i in range(120)]
    results = ConversionManager(max_workers=4).convert_batch(
        sources,
        ConversionOptions(output_format="JPG", output_dir=tmp_output, quality=70),
    )
    assert len(results) == 120
    assert all(item.success for item in results)


def test_metadata_preserved_when_possible(converter: ImageConverter, tmp_path: Path, tmp_output: Path):
    source = tmp_path / "meta.jpg"
    image = Image.new("RGB", (16, 16), (90, 90, 90))
    exif = Image.Exif()
    exif[0x010F] = "PixForgeTestCam"
    image.save(source, format="JPEG", exif=exif)
    result = converter.convert(
        source,
        ConversionOptions(output_format="JPG", output_dir=tmp_output, preserve_metadata=True),
    )
    assert result.success, result.error
    with Image.open(result.output_path) as converted:
        values = [str(v) for v in converted.getexif().values()]
        assert any("PixForgeTestCam" in value for value in values)
