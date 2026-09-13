from app.formats import (
    can_encode,
    format_from_extension,
    get_format,
    is_supported_extension,
    preferred_extension,
)


def test_jpg_and_jpeg_share_encoder():
    jpg = get_format("JPG")
    jpeg = get_format("jpeg")
    assert jpg is not None
    assert jpeg is not None
    assert jpg.pillow_format == jpeg.pillow_format == "JPEG"
    assert jpg.supports_alpha is False


def test_extension_lookup():
    assert format_from_extension("photo.HEIC").key in {"HEIC", "HEIF"}
    assert format_from_extension("scan.tif").key == "TIFF"
    assert is_supported_extension("a.png")
    assert not is_supported_extension("notes.txt")


def test_preferred_extensions():
    assert preferred_extension("JPG") == ".jpg"
    assert preferred_extension("HEIC") == ".heic"
    assert preferred_extension("HEIF") == ".heif"


def test_png_and_webp_support_alpha():
    assert get_format("PNG").supports_alpha is True
    assert get_format("WEBP").supports_alpha is True
    assert get_format("BMP").supports_alpha is False


def test_core_encoders_available():
    for key in ("JPG", "PNG", "WEBP", "BMP", "TIFF"):
        assert can_encode(key), f"{key} should be encodable with Pillow"
