"""Tests for GUI widgets, dialogs, theme changes, and interactions."""
from pathlib import Path
from PIL import Image
import pytest

from PySide6.QtCore import Qt
from app.models import ConversionOptions, ConversionResult, FileStatus
from app.ui.about_dialog import AboutDialog
from app.ui.file_list import FileQueueWidget
from app.ui.main_window import ErrorViewerDialog, MainWindow
from app.ui.output_section import OutputSection
from app.ui.settings_dialog import SettingsDialog
from app.ui.theme import get_stylesheet


def test_output_section_options(qapp, tmp_path):
    sec = OutputSection()
    sec.set_output_dir(tmp_path)
    sec.set_format("PNG")
    opts = sec.get_conversion_options()
    assert opts.output_format == "PNG"
    assert opts.output_dir == tmp_path


def test_file_queue_add_remove_clear(qapp, tmp_path):
    p1 = tmp_path / "1.jpg"
    p2 = tmp_path / "2.png"
    p1.touch()
    p2.touch()

    queue = FileQueueWidget()
    res = queue.add_paths([p1, p2])
    assert res.added == 2
    assert res.duplicates == 0
    assert len(queue.all_paths()) == 2

    # Duplicate addition
    res_dup = queue.add_paths([p1])
    assert res_dup.added == 0
    assert res_dup.duplicates == 1

    queue.update_status(p1, FileStatus.COMPLETED)
    queue.clear_all()
    assert len(queue.all_paths()) == 0


def test_settings_dialog(qapp, tmp_path):
    dlg = SettingsDialog()
    assert dlg.get_theme() in ["dark", "light"]
    assert dlg.get_max_workers() >= 1


def test_main_window_instantiation(qapp):
    win = MainWindow()
    assert win.windowTitle().startswith("PixForge")
    assert win.centralWidget() is not None


def test_error_viewer_dialog(qapp, tmp_path):
    res = ConversionResult(success=False, input_path=tmp_path / "fail.png", error="Corrupt header")
    dlg = ErrorViewerDialog([res])
    assert dlg.windowTitle().startswith("PixForge")


def test_about_dialog(qapp):
    dlg = AboutDialog()
    assert "PixForge" in dlg.windowTitle()
    assert bool(dlg.windowFlags() & Qt.WindowType.WindowCloseButtonHint)


def test_theme_stylesheets():
    dark_css = get_stylesheet("dark")
    light_css = get_stylesheet("light")
    assert "letter-spacing" not in dark_css
    assert "letter-spacing" not in light_css
    assert dark_css.count("{") == dark_css.count("}")
    assert light_css.count("{") == light_css.count("}")
