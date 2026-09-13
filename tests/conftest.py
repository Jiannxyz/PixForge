from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from app.models import ConversionOptions


@pytest.fixture
def tmp_output(tmp_path: Path) -> Path:
    output = tmp_path / "out"
    output.mkdir()
    return output


@pytest.fixture
def options_factory(tmp_output: Path):
    def factory(fmt: str = "PNG", **overrides) -> ConversionOptions:
        values = {
            "output_format": fmt,
            "output_dir": tmp_output,
        }
        values.update(overrides)
        return ConversionOptions(**values)

    return factory


def save_rgb(path: Path, size: tuple[int, int] = (32, 24), color=(220, 40, 40)) -> Path:
    Image.new("RGB", size, color).save(path)
    return path


def save_rgba(path: Path, size: tuple[int, int] = (32, 24)) -> Path:
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    for x in range(16):
        for y in range(size[1]):
            image.putpixel((x, y), (0, 255, 0, 255))
    image.save(path)
    return path
