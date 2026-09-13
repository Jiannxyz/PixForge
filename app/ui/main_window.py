"""Main window for PixForge desktop application."""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.config import APP_NAME
from app.core.conversion_manager import ConversionManager
from app.formats import file_dialog_filter
from app.models import ConversionResult, FileStatus, ImageJob
from app.ui.drop_zone import DropZone
from app.ui.file_list import FileQueueWidget
from app.ui.output_section import OutputSection
from app.ui.settings_dialog import SettingsDialog
from app.ui.theme import APP_STYLESHEET
from app.ui.widgets import PrimaryButton, SubtitleLabel, TitleLabel
from app.utils.filesystem import collect_image_paths
from app.utils.platform import cpu_count, open_folder
from app.workers.conversion_worker import ConversionBatchWorker

logger = logging.getLogger(__name__)


class ErrorViewerDialog(QDialog):
    """Modal dialog displaying failed conversion files and their error messages."""

    def __init__(self, failed_results: list[ConversionResult], parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Conversion Errors")
        self.resize(520, 360)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QLabel(f"{len(failed_results)} file(s) failed conversion:")
        header.setStyleSheet("font-weight: 700; font-size: 14px; color: #f87171;")
        layout.addWidget(header)

        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        lines = []
        for res in failed_results:
            name = res.source_path.name
            err = res.error or "Unknown error"
            lines.append(f"• {name}\n  Reason: {err}\n")
        text_edit.setPlainText("\n".join(lines))
        layout.addWidget(text_edit)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)


class MainWindow(QMainWindow):
    """Main application window for PixForge."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} — Offline Image Converter")
        self.resize(880, 780)
        self.setMinimumSize(720, 600)
        self.setStyleSheet(APP_STYLESHEET)

        self._active_worker: ConversionBatchWorker | None = None
        self._last_results: list[ConversionResult] = []
        self._settings = QSettings("PixForge", "PixForge")

        self._build_ui()
        self._load_persisted_settings()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(12)

        # Header bar
        header_frame = QFrame()
        header_frame.setObjectName("header")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 4)

        title_col = QVBoxLayout()
        title_col.setSpacing(1)
        self.title_label = TitleLabel("PixForge")
        self.subtitle_label = SubtitleLabel("Offline Image Converter")
        title_col.addWidget(self.title_label)
        title_col.addWidget(self.subtitle_label)
        header_layout.addLayout(title_col)

        header_layout.addStretch()

        self.settings_btn = QPushButton("⚙ Settings")
        self.settings_btn.clicked.connect(self._open_settings)
        header_layout.addWidget(self.settings_btn)

        main_layout.addWidget(header_frame)

        # Drop Zone
        self.drop_zone = DropZone()
        self.drop_zone.files_dropped.connect(self._handle_files_dropped)
        self.drop_zone.add_images_clicked.connect(self._handle_add_images)
        self.drop_zone.add_folder_clicked.connect(self._handle_add_folder)
        main_layout.addWidget(self.drop_zone)

        # File Queue Widget
        self.file_queue = FileQueueWidget()
        self.file_queue.queue_changed.connect(self._on_queue_changed)
        self.file_queue.files_dropped.connect(self._handle_files_dropped)
        main_layout.addWidget(self.file_queue, stretch=1)

        # Output Settings Section
        self.output_section = OutputSection()
        main_layout.addWidget(self.output_section)

        # Execution & Progress Card
        exec_card = QFrame()
        exec_card.setObjectName("card")
        exec_layout = QVBoxLayout(exec_card)
        exec_layout.setContentsMargins(16, 14, 16, 14)
        exec_layout.setSpacing(10)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        exec_layout.addWidget(self.progress_bar)

        # Status & Counter info row
        info_row = QHBoxLayout()
        self.status_info_label = QLabel("Ready")
        self.status_info_label.setStyleSheet("color: #9aa3b2; font-size: 12px;")
        info_row.addWidget(self.status_info_label)

        info_row.addStretch()

        self.counter_label = QLabel("0 / 0 completed")
        self.counter_label.setStyleSheet("font-weight: 600; font-size: 12px; color: #c5cdd8;")
        info_row.addWidget(self.counter_label)
        exec_layout.addLayout(info_row)

        # Action Buttons row
        action_row = QHBoxLayout()
        action_row.setSpacing(12)

        self.convert_btn = PrimaryButton("CONVERT ALL")
        self.convert_btn.clicked.connect(self._start_conversion)
        action_row.addWidget(self.convert_btn, stretch=3)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("danger")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self._cancel_conversion)
        action_row.addWidget(self.cancel_btn, stretch=1)

        exec_layout.addLayout(action_row)

        # Post-completion summary banner (initially hidden)
        self.summary_banner = QFrame()
        self.summary_banner.setStyleSheet(
            "background-color: #1a2030; border: 1px solid #2d3852; border-radius: 8px; padding: 6px 12px;"
        )
        banner_layout = QHBoxLayout(self.summary_banner)
        banner_layout.setContentsMargins(8, 4, 8, 4)

        self.summary_text = QLabel("")
        self.summary_text.setStyleSheet("font-weight: 600; font-size: 13px; color: #f4f6fb;")
        banner_layout.addWidget(self.summary_text)

        banner_layout.addStretch()

        self.open_output_btn = QPushButton("Open Output Folder")
        self.open_output_btn.clicked.connect(self._open_output_folder)
        banner_layout.addWidget(self.open_output_btn)

        self.view_errors_btn = QPushButton("View Errors")
        self.view_errors_btn.setObjectName("danger")
        self.view_errors_btn.clicked.connect(self._view_errors)
        self.view_errors_btn.setVisible(False)
        banner_layout.addWidget(self.view_errors_btn)

        self.summary_banner.setVisible(False)
        exec_layout.addWidget(self.summary_banner)

        main_layout.addWidget(exec_card)
        self._on_queue_changed(0)

    def _load_persisted_settings(self) -> None:
        default_dir = self._settings.value("default_output_dir", "")
        if default_dir:
            self.output_section.set_output_dir(Path(default_dir))
        preserve_meta = self._settings.value("preserve_metadata", True, type=bool)
        self.output_section.metadata_checkbox.setChecked(preserve_meta)

    def _open_settings(self) -> None:
        dlg = SettingsDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._load_persisted_settings()

    def _notify_added(self, res) -> None:
        dupes = getattr(res, "duplicates", 0)
        if dupes > 0:
            count = int(res)
            msg = f"Added {count} image{'s' if count != 1 else ''} ({dupes} duplicate{'s' if dupes != 1 else ''} skipped)"
            self.status_info_label.setText(msg)

    def _handle_add_images(self) -> None:
        filter_str = file_dialog_filter()
        paths, _ = QFileDialog.getOpenFileNames(self, "Select Images to Convert", "", filter_str)
        if paths:
            res = self.file_queue.add_paths([Path(p) for p in paths])
            self._notify_added(res)

    def _handle_add_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select Folder of Images")
        if folder:
            recursive = self.drop_zone.include_subfolders
            image_paths = collect_image_paths(Path(folder), recursive=recursive)
            if not image_paths:
                QMessageBox.information(
                    self,
                    "No Images Found",
                    f"No supported image files were found in:\n{folder}",
                )
                return
            res = self.file_queue.add_paths(image_paths)
            self._notify_added(res)

    def _handle_files_dropped(self, raw_paths: list[Path]) -> None:
        recursive = self.drop_zone.include_subfolders
        all_images: list[Path] = []
        for path in raw_paths:
            if path.is_dir():
                all_images.extend(collect_image_paths(path, recursive=recursive))
            elif path.is_file():
                all_images.extend(collect_image_paths(path, recursive=False))

        if all_images:
            res = self.file_queue.add_paths(all_images)
            self._notify_added(res)

    def _on_queue_changed(self, count: int) -> None:
        has_items = count > 0
        is_running = self._active_worker is not None and self._active_worker.isRunning()
        self.convert_btn.setEnabled(has_items and not is_running)
        if not is_running:
            self.counter_label.setText(f"0 / {count} completed")
            self.status_info_label.setText(f"{count} {'file' if count == 1 else 'files'} ready")

    def _start_conversion(self) -> None:
        paths = self.file_queue.get_all_paths()
        if not paths:
            return

        self.summary_banner.setVisible(False)
        self.view_errors_btn.setVisible(False)
        self._last_results.clear()
        self.file_queue.reset_all_statuses()

        options = self.output_section.get_conversion_options()

        # Check worker threads preference
        worker_pref = self._settings.value("max_workers", 0, type=int)
        workers = worker_pref if worker_pref > 0 else min(4, cpu_count())

        self._active_worker = ConversionBatchWorker(
            sources=paths,
            options=options,
            manager=ConversionManager(max_workers=workers),
            max_workers=workers,
            parent=self,
        )

        self._active_worker.job_started.connect(self._on_job_started)
        self._active_worker.job_finished.connect(self._on_job_finished)
        self._active_worker.progress_updated.connect(self._on_progress_updated)
        self._active_worker.batch_finished.connect(self._on_batch_finished)

        # UI state during conversion
        self.convert_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.drop_zone.setEnabled(False)
        self.file_queue.remove_selected_btn.setEnabled(False)
        self.file_queue.clear_all_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.status_info_label.setText("Starting conversion…")
        self.counter_label.setText(f"0 / {len(paths)} completed")

        self._active_worker.start()

    def _cancel_conversion(self) -> None:
        if self._active_worker and self._active_worker.isRunning():
            self.cancel_btn.setEnabled(False)
            self.status_info_label.setText("Cancelling remaining files…")
            self._active_worker.cancel()

    def _on_job_started(self, source_path_str: str) -> None:
        self.file_queue.update_status(Path(source_path_str), FileStatus.CONVERTING)
        name = Path(source_path_str).name
        self.status_info_label.setText(f"Converting: {name}")

    def _on_job_finished(self, job: ImageJob) -> None:
        self.file_queue.update_status(job.source_path, job.status, job.result)

    def _on_progress_updated(self, completed: int, total: int) -> None:
        if total > 0:
            pct = int((completed / total) * 100)
            self.progress_bar.setValue(pct)
        self.counter_label.setText(f"{completed} / {total} completed")

    def _on_batch_finished(self, results: list[ConversionResult]) -> None:
        self._last_results = results
        total = len(results)
        successful = sum(1 for r in results if r.success)
        failed = sum(1 for r in results if not r.success and not r.skipped)
        skipped = sum(1 for r in results if r.skipped)

        # Restore UI buttons
        self.convert_btn.setEnabled(self.file_queue.count > 0)
        self.cancel_btn.setEnabled(False)
        self.drop_zone.setEnabled(True)
        self.file_queue.remove_selected_btn.setEnabled(self.file_queue.count > 0)
        self.file_queue.clear_all_btn.setEnabled(self.file_queue.count > 0)

        # Build summary
        was_cancelled = self._active_worker is not None and self._active_worker.is_cancelled
        if was_cancelled:
            self.status_info_label.setText("Conversion cancelled")
            msg = f"Cancelled: {successful} completed, {skipped} skipped"
            if failed > 0:
                msg += f", {failed} failed"
            self.summary_text.setText(f"⊘ {msg}")
            self.summary_text.setStyleSheet("font-weight: 700; color: #fbbf24;")
        elif failed == 0:
            self.status_info_label.setText("Conversion complete")
            self.progress_bar.setValue(100)
            self.summary_text.setText(f"✓ All {successful} files converted successfully!")
            self.summary_text.setStyleSheet("font-weight: 700; color: #4ade80;")
        else:
            self.status_info_label.setText("Completed with errors")
            self.summary_text.setText(f"Completed: {successful} successful, {failed} failed")
            self.summary_text.setStyleSheet("font-weight: 700; color: #f87171;")
            self.view_errors_btn.setVisible(True)

        self.summary_banner.setVisible(True)
        self._active_worker = None

        # Auto-open output folder if configured
        if successful > 0 and self._settings.value("auto_open_folder", False, type=bool):
            open_folder(self.output_section.get_output_dir())

    def _open_output_folder(self) -> None:
        open_folder(self.output_section.get_output_dir())

    def _view_errors(self) -> None:
        failed = [r for r in self._last_results if not r.success and not r.skipped]
        if failed:
            dlg = ErrorViewerDialog(failed, self)
            dlg.exec()

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._active_worker and self._active_worker.isRunning():
            reply = QMessageBox.question(
                self,
                "Conversion in Progress",
                "Conversions are currently running. Do you want to cancel and exit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._active_worker.cancel()
                self._active_worker.wait(2000)
                event.accept()
            else:
                event.ignore()
                return
        event.accept()
