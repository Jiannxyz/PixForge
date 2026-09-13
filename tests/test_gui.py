"""Automated GUI and worker tests for PixForge."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

# Set headless/offscreen for PySide6 tests
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from app.core.inspect import ImagePreview
from app.models import ConversionOptions, FileStatus
from app.ui.drop_zone import DropZone
from app.ui.file_list import FileQueueRow, FileQueueWidget
from app.ui.main_window import MainWindow
from app.ui.output_section import OutputSection
from app.ui.settings_dialog import SettingsDialog
from app.utils.platform import open_folder
from app.workers.conversion_worker import ConversionBatchWorker
from tests.conftest import save_rgb


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_drop_zone_widget(qapp):
    drop_zone = DropZone()
    assert drop_zone.include_subfolders is True
    drop_zone.subfolder_checkbox.setChecked(False)
    assert drop_zone.include_subfolders is False


def test_file_queue_add_remove_clear(qapp, tmp_path: Path):
    queue = FileQueueWidget()
    assert queue.count == 0

    img1 = save_rgb(tmp_path / "photo1.png")
    img2 = save_rgb(tmp_path / "photo2.jpg")

    # Add paths
    added = queue.add_paths([img1, img2])
    assert added == 2
    assert queue.count == 2
    assert img1 in queue.get_all_paths()
    assert img2 in queue.get_all_paths()

    # Prevent duplicates
    added_dup = queue.add_paths([img1])
    assert added_dup == 0
    assert queue.count == 2

    # Status update
    queue.update_status(img1, FileStatus.CONVERTING)
    _, row = queue._path_map[img1]
    assert "Converting" in row.status_label.text()

    # Preview update
    preview = ImagePreview(
        path=img1,
        width=100,
        height=200,
        format_key="PNG",
        thumbnail_jpeg=None,
    )
    queue._on_thumbnail_ready(preview)
    assert "100 × 200" in row.sub_info_label.text()

    # Filter search
    queue.search_input.setText("photo1")
    item1, _ = queue._path_map[img1]
    item2, _ = queue._path_map[img2]
    assert not item1.isHidden()
    assert item2.isHidden()
    queue.search_input.clear()
    assert not item2.isHidden()

    # Remove single item
    queue.remove_path(img1)
    assert queue.count == 1
    assert img1 not in queue.get_all_paths()

    # Clear all
    queue.clear_all()
    assert queue.count == 0
    assert len(queue.get_all_paths()) == 0


def test_output_section_options(qapp, tmp_path: Path):
    section = OutputSection()
    section.set_output_dir(tmp_path)

    # Check default format
    section.set_selected_format("JPG")
    assert section.get_selected_format() == "JPG"
    section.jpeg_slider.setValue(85)

    opts = section.get_conversion_options()
    assert opts.output_format == "JPG"
    assert opts.output_dir == tmp_path
    assert opts.quality == 85
    assert opts.preserve_metadata is True
    assert opts.overwrite is False

    # Switch format to PNG
    section.set_selected_format("PNG")
    assert section.get_selected_format() == "PNG"
    section.png_slider.setValue(4)
    opts_png = section.get_conversion_options()
    assert opts_png.output_format == "PNG"
    assert opts_png.png_compress_level == 4

    # Switch format to HEIC
    section.set_selected_format("HEIC")
    section.heic_slider.setValue(75)
    opts_heic = section.get_conversion_options()
    assert opts_heic.output_format == "HEIC"
    assert opts_heic.heic_quality == 75


def test_settings_dialog_roundtrip(qapp, tmp_path: Path):
    dialog = SettingsDialog()
    dialog.folder_input.setText(str(tmp_path))
    dialog.jpeg_spin.setValue(95)
    dialog.png_spin.setValue(8)
    dialog.auto_open_checkbox.setChecked(True)
    dialog._save_settings()

    # Create new dialog to verify loaded settings
    dialog2 = SettingsDialog()
    assert dialog2.folder_input.text() == str(tmp_path)
    assert dialog2.jpeg_spin.value() == 95
    assert dialog2.png_spin.value() == 8
    assert dialog2.auto_open_checkbox.isChecked() is True


def test_conversion_batch_worker(qapp, tmp_path: Path, tmp_output: Path):
    img1 = save_rgb(tmp_path / "one.png", size=(10, 10))
    img2 = save_rgb(tmp_path / "two.png", size=(10, 10))

    options = ConversionOptions(output_format="JPG", output_dir=tmp_output)
    worker = ConversionBatchWorker([img1, img2], options, max_workers=2)

    started_paths = []
    finished_jobs = []
    progress_records = []
    batch_results = []

    worker.job_started.connect(lambda p: started_paths.append(p))
    worker.job_finished.connect(lambda j: finished_jobs.append(j))
    worker.progress_updated.connect(lambda c, t: progress_records.append((c, t)))
    worker.batch_finished.connect(lambda res: batch_results.extend(res))

    worker.start()
    worker.wait(5000)
    qapp.processEvents()

    assert len(batch_results) == 2
    assert all(r.success for r in batch_results)
    assert len(progress_records) == 2
    assert progress_records[-1] == (2, 2)


def test_main_window_lifecycle(qapp, tmp_path: Path, tmp_output: Path):
    window = MainWindow()
    window.show()
    assert window.title_label.text() == "PixForge"
    assert window.convert_btn.isEnabled() is False

    # Add images
    img1 = save_rgb(tmp_path / "a.png", size=(12, 12))
    img2 = save_rgb(tmp_path / "b.png", size=(12, 12))
    window.file_queue.add_paths([img1, img2])

    assert window.file_queue.count == 2
    assert window.convert_btn.isEnabled() is True

    window.output_section.set_output_dir(tmp_output)
    window.output_section.set_selected_format("JPG")

    # Run conversion
    window._start_conversion()
    assert window._active_worker is not None
    window._active_worker.wait(5000)
    qapp.processEvents()

    assert window.convert_btn.isEnabled() is True
    assert window.summary_banner.isVisible() is True
    assert (tmp_output / "a.converted.jpg").exists()
    assert (tmp_output / "b.converted.jpg").exists()

    window.close()


def test_main_window_cancellation(qapp, tmp_path: Path, tmp_output: Path):
    window = MainWindow()
    window.show()

    sources = [save_rgb(tmp_path / f"cancel_{i}.png", size=(8, 8)) for i in range(10)]
    window.file_queue.add_paths(sources)
    window.output_section.set_output_dir(tmp_output)

    window._start_conversion()
    assert window._active_worker is not None

    window._cancel_conversion()
    window._active_worker.wait(5000)
    qapp.processEvents()

    assert window.cancel_btn.isEnabled() is False
    assert window.convert_btn.isEnabled() is True
    assert "Cancelled" in window.summary_text.text()
    window.close()


def test_main_window_error_handling(qapp, tmp_path: Path, tmp_output: Path):
    window = MainWindow()
    window.show()

    good_img = save_rgb(tmp_path / "valid.png", size=(10, 10))
    bad_img = tmp_path / "corrupted.jpg"
    bad_img.write_bytes(b"not a valid image format at all")

    window.file_queue.add_paths([good_img, bad_img])
    window.output_section.set_output_dir(tmp_output)

    window._start_conversion()
    window._active_worker.wait(5000)
    qapp.processEvents()

    assert window.view_errors_btn.isVisible() is True
    assert "Completed: 1 successful, 1 failed" in window.summary_text.text()
    window.close()


def test_open_folder_utility(tmp_path: Path):
    folder = tmp_path / "test_open"
    # Should create folder and call os.startfile / subprocess without raising
    with patch("os.startfile", return_value=None, create=True):
        with patch("subprocess.Popen", return_value=None):
            assert open_folder(folder) is True
            assert folder.exists()
