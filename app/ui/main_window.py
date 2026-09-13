"""Main application window for PixForge."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import QSettings, Qt, Slot
from PySide6.QtGui import QCloseEvent, QIcon, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.config import APP_NAME, APP_ORG, APP_VERSION, LOGO_TRANSPARENT_PATH
from app.formats import INPUT_EXTENSIONS
from app.models import ConversionOptions, ConversionResult, FileStatus
from app.ui.about_dialog import AboutDialog
from app.ui.drop_zone import DropZone
from app.ui.file_list import FileQueueWidget
from app.ui.output_section import OutputSection
from app.ui.settings_dialog import SettingsDialog
from app.ui.theme import get_stylesheet
from app.ui.widgets import MutedLabel, PrimaryButton, SectionLabel, SubtitleLabel, TitleLabel
from app.utils.filesystem import collect_image_paths
from app.utils.platform import open_folder
from app.workers.conversion_worker import ConversionBatchWorker

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Error Viewer Dialog
# ---------------------------------------------------------------------------

class ErrorViewerDialog(QDialog):
    """Dialog showing detailed conversion errors for failed files."""

    def __init__(self, errors: list[ConversionResult], parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"{APP_NAME} — Conversion Errors")
        if LOGO_TRANSPARENT_PATH.exists():
            self.setWindowIcon(QIcon(str(LOGO_TRANSPARENT_PATH)))
        self.setMinimumSize(600, 360)
        self._errors = errors
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        desc = QLabel(f"The following {len(self._errors)} file(s) failed during conversion:")
        desc.setStyleSheet("font-weight: bold;")
        layout.addWidget(desc)

        table = QTableWidget(len(self._errors), 2, self)
        table.setHorizontalHeaderLabels(["Filename", "Error Reason"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        for i, res in enumerate(self._errors):
            f_item = QTableWidgetItem(res.input_path.name)
            e_item = QTableWidgetItem(res.error or "Unknown error")
            table.setItem(i, 0, f_item)
            table.setItem(i, 1, e_item)

        layout.addWidget(table)

        btn_box = QHBoxLayout()
        btn_box.addStretch()
        close_btn = QPushButton("Close", self)
        close_btn.clicked.connect(self.accept)
        btn_box.addWidget(close_btn)
        layout.addLayout(btn_box)


# ---------------------------------------------------------------------------
# Main Window
# ---------------------------------------------------------------------------

class MainWindow(QMainWindow):
    """PixForge main desktop application window."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} — Offline Image Converter")
        if LOGO_TRANSPARENT_PATH.exists():
            self.setWindowIcon(QIcon(str(LOGO_TRANSPARENT_PATH)))
        self.setMinimumSize(960, 720)
        self.resize(1080, 800)

        self._settings = QSettings(APP_ORG, APP_NAME)
        self._current_theme = "dark"
        self._batch_worker: Optional[ConversionBatchWorker] = None
        self._last_results: list[ConversionResult] = []

        self._build_ui()
        self._load_persisted_settings()

    # ------------------------------------------------------------------
    # UI Building
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        central = QWidget(self)
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(16, 14, 16, 14)
        root_layout.setSpacing(12)

        # ── Top App Bar ──────────────────────────────────────────────
        app_bar = QFrame(self)
        app_bar.setObjectName("header")
        app_bar_layout = QHBoxLayout(app_bar)
        app_bar_layout.setContentsMargins(8, 6, 8, 6)
        app_bar_layout.setSpacing(10)

        if LOGO_TRANSPARENT_PATH.exists():
            logo_lbl = QLabel(self)
            pix = QPixmap(str(LOGO_TRANSPARENT_PATH)).scaled(
                36, 36,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            logo_lbl.setPixmap(pix)
            logo_lbl.setFixedSize(36, 36)
            app_bar_layout.addWidget(logo_lbl)

        title_box = QVBoxLayout()
        title_box.setSpacing(0)
        app_title = TitleLabel(APP_NAME, self)
        app_subtitle = SubtitleLabel("Offline Image Converter", self)
        title_box.addWidget(app_title)
        title_box.addWidget(app_subtitle)
        app_bar_layout.addLayout(title_box)

        app_bar_layout.addStretch()

        self._about_btn = QPushButton("ℹ  About", self)
        self._about_btn.setFixedHeight(32)
        self._about_btn.clicked.connect(self._open_about)
        app_bar_layout.addWidget(self._about_btn)

        self._settings_btn = QPushButton("⚙  Settings", self)
        self._settings_btn.setFixedHeight(32)
        self._settings_btn.clicked.connect(self._open_settings)
        app_bar_layout.addWidget(self._settings_btn)

        root_layout.addWidget(app_bar)

        # ── Drop Zone ────────────────────────────────────────────────
        self._drop_zone = DropZone(self)
        self._drop_zone.files_dropped.connect(self._handle_files_dropped)
        self._drop_zone.add_images_clicked.connect(self._handle_add_images)
        self._drop_zone.add_folder_clicked.connect(self._handle_add_folder)
        root_layout.addWidget(self._drop_zone)

        # ── Main Content: Split File List & Output Section ──────────
        content_layout = QHBoxLayout()
        content_layout.setSpacing(12)

        # Left/Middle: File Queue
        self._queue_widget = FileQueueWidget(self)
        self._queue_widget.files_dropped.connect(self._handle_files_dropped)
        self._queue_widget.queue_changed.connect(self._on_queue_changed)
        content_layout.addWidget(self._queue_widget, stretch=3)

        # Right: Output Options
        self._output_section = OutputSection(self)
        self._output_section.setFixedWidth(340)
        content_layout.addWidget(self._output_section, stretch=0)

        root_layout.addLayout(content_layout, stretch=1)

        # ── Bottom Execution & Status Card ──────────────────────────
        self._exec_card = QFrame(self)
        self._exec_card.setObjectName("card")
        exec_layout = QVBoxLayout(self._exec_card)
        exec_layout.setContentsMargins(16, 12, 16, 12)
        exec_layout.setSpacing(10)

        # Normal Action View (Progress & Buttons)
        self._action_view = QWidget(self)
        action_layout = QHBoxLayout(self._action_view)
        action_layout.setContentsMargins(0, 0, 0, 0)
        action_layout.setSpacing(14)

        # Progress info
        progress_box = QVBoxLayout()
        progress_box.setSpacing(4)
        prog_header = QHBoxLayout()
        self._prog_title = SectionLabel("Overall Progress", self)
        self._prog_counter = MutedLabel("0 / 0 completed", self)
        prog_header.addWidget(self._prog_title)
        prog_header.addStretch()
        prog_header.addWidget(self._prog_counter)

        self._progress_bar = QProgressBar(self)
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)

        progress_box.addLayout(prog_header)
        progress_box.addWidget(self._progress_bar)
        action_layout.addLayout(progress_box, stretch=1)

        # Convert / Cancel button
        self._convert_btn = PrimaryButton("CONVERT ALL", self)
        self._convert_btn.setMinimumHeight(42)
        self._convert_btn.setMinimumWidth(140)
        self._convert_btn.clicked.connect(self._start_conversion)

        self._cancel_btn = QPushButton("Cancel", self)
        self._cancel_btn.setObjectName("danger")
        self._cancel_btn.setMinimumHeight(42)
        self._cancel_btn.setMinimumWidth(100)
        self._cancel_btn.setVisible(False)
        self._cancel_btn.clicked.connect(self._cancel_conversion)

        action_layout.addWidget(self._convert_btn)
        action_layout.addWidget(self._cancel_btn)
        exec_layout.addWidget(self._action_view)

        # Summary Banner (Hidden until batch completes)
        self._summary_banner = QFrame(self)
        self._summary_banner.setObjectName("card")
        self._summary_banner.setStyleSheet("background-color: #12281e; border: 1px solid #2e7d32; border-radius: 8px;")
        summary_layout = QHBoxLayout(self._summary_banner)
        summary_layout.setContentsMargins(14, 10, 14, 10)
        summary_layout.setSpacing(12)

        self._summary_icon = QLabel("✓", self)
        self._summary_icon.setStyleSheet("color: #4caf50; font-size: 20px; font-weight: bold;")
        summary_layout.addWidget(self._summary_icon)

        self._summary_text = QLabel("Conversion Complete!", self)
        self._summary_text.setStyleSheet("font-size: 13px; font-weight: 600;")
        summary_layout.addWidget(self._summary_text, stretch=1)

        self._view_errors_btn = QPushButton("View Errors", self)
        self._view_errors_btn.setFixedHeight(30)
        self._view_errors_btn.setVisible(False)
        self._view_errors_btn.clicked.connect(self._view_errors)
        summary_layout.addWidget(self._view_errors_btn)

        self._open_folder_btn = QPushButton("📂 Open Output Folder", self)
        self._open_folder_btn.setFixedHeight(30)
        self._open_folder_btn.clicked.connect(self._open_output_folder)
        summary_layout.addWidget(self._open_folder_btn)

        self._convert_more_btn = QPushButton("Convert More Images", self)
        self._convert_more_btn.setObjectName("primary")
        self._convert_more_btn.setFixedHeight(30)
        self._convert_more_btn.clicked.connect(self._reset_for_more_images)
        summary_layout.addWidget(self._convert_more_btn)

        self._summary_banner.setVisible(False)
        exec_layout.addWidget(self._summary_banner)

        root_layout.addWidget(self._exec_card)

        # Status Bar
        self.setStatusBar(QStatusBar(self))
        self.statusBar().showMessage("Ready")

        self._update_convert_button_state()

    # ------------------------------------------------------------------
    # Settings & Theme Management
    # ------------------------------------------------------------------

    def _load_persisted_settings(self) -> None:
        self._current_theme = self._settings.value("general/theme", "dark")
        self.setStyleSheet(get_stylesheet(self._current_theme))

        # Output Section
        self._output_section.load_from_settings(self._settings)

        # Check default output folder from settings
        default_folder = self._settings.value("general/default_output_dir", "")
        if default_folder and Path(default_folder).exists():
            self._output_section.set_output_dir(Path(default_folder))

    def _open_about(self) -> None:
        AboutDialog(self).exec()

    def _open_settings(self) -> None:
        dlg = SettingsDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            new_theme = dlg.get_theme()
            if new_theme != self._current_theme:
                self._current_theme = new_theme
                self.setStyleSheet(get_stylesheet(self._current_theme))

            def_folder = dlg.get_default_output_folder()
            if def_folder and def_folder.exists() and not self._output_section.get_output_dir():
                self._output_section.set_output_dir(def_folder)

    # ------------------------------------------------------------------
    # User Actions: Adding Files
    # ------------------------------------------------------------------

    def _handle_add_images(self) -> None:
        filter_str = f"Image Files ({' '.join(f'*{ext}' for ext in INPUT_EXTENSIONS)});;All Files (*.*)"
        files, _ = QFileDialog.getOpenFileNames(self, "Select Images", "", filter_str)
        if files:
            paths = [Path(f) for f in files]
            self._notify_added(self._queue_widget.add_paths(paths))

    def _handle_add_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select Folder Containing Images")
        if folder:
            rec = self._drop_zone.include_subfolders.isChecked()
            paths = collect_image_paths(Path(folder), recursive=rec)
            self._notify_added(self._queue_widget.add_paths(paths))

    def _handle_files_dropped(self, paths: List[Path]) -> None:
        self._notify_added(self._queue_widget.add_paths(paths))

    def _notify_added(self, res) -> None:
        msg = f"Added {res.added} file{'s' if res.added != 1 else ''}"
        if res.duplicates > 0:
            msg += f" ({res.duplicates} duplicate{'s' if res.duplicates != 1 else ''} skipped)"
        self.statusBar().showMessage(msg, 4000)
        log.info(msg)

    def _on_queue_changed(self, count: int) -> None:
        self._update_convert_button_state()
        if not count:
            self._summary_banner.setVisible(False)
            self._prog_counter.setText("0 / 0 completed")
            self._progress_bar.setValue(0)

    def _update_convert_button_state(self) -> None:
        has_items = len(self._queue_widget.all_paths()) > 0
        is_running = self._batch_worker is not None and self._batch_worker.isRunning()
        self._convert_btn.setEnabled(has_items and not is_running)

    # ------------------------------------------------------------------
    # Batch Conversion
    # ------------------------------------------------------------------

    def _start_conversion(self) -> None:
        paths = self._queue_widget.all_paths()
        if not paths:
            return

        options = self._output_section.get_conversion_options()
        # Save last chosen format and options
        self._output_section.save_to_settings(self._settings)

        # Reset row statuses & UI progress
        self._queue_widget.reset_statuses()
        total = len(paths)
        self._progress_bar.setRange(0, total)
        self._progress_bar.setValue(0)
        self._prog_counter.setText(f"0 / {total} completed")

        self._summary_banner.setVisible(False)
        self._action_view.setVisible(True)
        self._convert_btn.setVisible(False)
        self._cancel_btn.setVisible(True)
        self._cancel_btn.setEnabled(True)

        self._last_results.clear()

        # Worker thread count from settings
        max_workers = int(self._settings.value("performance/max_workers", 0)) or None

        self._batch_worker = ConversionBatchWorker(
            paths=paths,
            options=options,
            max_workers=max_workers,
            parent=self,
        )
        self._batch_worker.job_started.connect(self._on_job_started)
        self._batch_worker.job_finished.connect(self._on_job_finished)
        self._batch_worker.progress_updated.connect(self._on_progress_updated)
        self._batch_worker.batch_finished.connect(self._on_batch_finished)

        log.info("Starting batch conversion of %d files to %s", total, options.output_format)
        self.statusBar().showMessage(f"Converting {total} images...")
        self._batch_worker.start()

    def _cancel_conversion(self) -> None:
        if self._batch_worker and self._batch_worker.isRunning():
            self._cancel_btn.setEnabled(False)
            self._cancel_btn.setText("Cancelling...")
            self.statusBar().showMessage("Cancelling conversion batch...")
            log.info("User requested batch cancellation")
            self._batch_worker.cancel()

    @Slot(Path)
    def _on_job_started(self, path: Path) -> None:
        self._queue_widget.update_status(path, FileStatus.CONVERTING)

    @Slot(object)
    def _on_job_finished(self, result: ConversionResult) -> None:
        self._last_results.append(result)
        if result.skipped:
            st = FileStatus.SKIPPED
        elif result.success:
            st = FileStatus.COMPLETED
        else:
            st = FileStatus.FAILED
        self._queue_widget.update_status(result.input_path, st)

    @Slot(int, int)
    def _on_progress_updated(self, done: int, total: int) -> None:
        self._progress_bar.setValue(done)
        self._prog_counter.setText(f"{done} / {total} completed")

    @Slot(list)
    def _on_batch_finished(self, results: list[ConversionResult]) -> None:
        self._cancel_btn.setVisible(False)
        self._cancel_btn.setText("Cancel")
        self._convert_btn.setVisible(True)
        self._convert_btn.setEnabled(True)

        total = len(results)
        succeeded = sum(1 for r in results if r.success)
        failed = sum(1 for r in results if not r.success and not r.skipped)
        skipped = sum(1 for r in results if r.skipped)

        log.info(
            "Batch finished: %d total, %d succeeded, %d failed, %d skipped",
            total, succeeded, failed, skipped
        )

        # Update Summary Banner
        banner_msg = f"Done: {succeeded} succeeded"
        if failed > 0:
            banner_msg += f", {failed} failed"
        if skipped > 0:
            banner_msg += f", {skipped} skipped"

        self._summary_text.setText(banner_msg)

        if failed > 0:
            self._summary_icon.setText("⚠️")
            self._summary_icon.setStyleSheet("color: #ff9800; font-size: 20px; font-weight: bold;")
            self._summary_banner.setStyleSheet("background-color: #2b1d12; border: 1px solid #b26a00; border-radius: 8px;")
            self._view_errors_btn.setVisible(True)
        else:
            self._summary_icon.setText("✓")
            self._summary_icon.setStyleSheet("color: #4caf50; font-size: 20px; font-weight: bold;")
            self._summary_banner.setStyleSheet("background-color: #12281e; border: 1px solid #2e7d32; border-radius: 8px;")
            self._view_errors_btn.setVisible(False)

        self._summary_banner.setVisible(True)
        self.statusBar().showMessage("Batch conversion complete.", 5000)

        # Auto-open folder if configured in settings
        auto_open = self._settings.value("general/auto_open_output", False, type=bool)
        if auto_open:
            self._open_output_folder()

    def _view_errors(self) -> None:
        errors = [r for r in self._last_results if not r.success and not r.skipped]
        if errors:
            dlg = ErrorViewerDialog(errors, self)
            dlg.exec()

    def _open_output_folder(self) -> None:
        out_dir = self._output_section.get_output_dir()
        if not out_dir:
            # If no explicit output dir, use directory of first converted file
            if self._last_results and self._last_results[0].output_path:
                out_dir = self._last_results[0].output_path.parent
            elif self._queue_widget.all_paths():
                out_dir = self._queue_widget.all_paths()[0].parent
            else:
                out_dir = Path.home() / "Pictures"

        if out_dir and out_dir.exists():
            open_folder(out_dir)
        else:
            QMessageBox.information(self, "Output Folder", f"Directory does not exist:\n{out_dir}")

    def _reset_for_more_images(self) -> None:
        self._queue_widget.clear_all()
        self._summary_banner.setVisible(False)
        self._prog_counter.setText("0 / 0 completed")
        self._progress_bar.setValue(0)
        self._update_convert_button_state()

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._batch_worker and self._batch_worker.isRunning():
            reply = QMessageBox.question(
                self,
                "Conversion in Progress",
                "Images are currently being converted. Do you want to cancel and exit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._batch_worker.cancel()
                self._batch_worker.wait(2000)
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
