"""Settings dialog with QSettings persistence."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from app.config import (
    APP_NAME,
    APP_ORG,
    DEFAULT_HEIC_QUALITY,
    DEFAULT_JPEG_QUALITY,
    DEFAULT_PNG_COMPRESSION,
    DEFAULT_WEBP_QUALITY,
    MAX_WORKERS,
)


class SettingsDialog(QDialog):
    """Configuration dialog backed by QSettings."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"{APP_NAME} Settings")
        self.setMinimumWidth(450)
        self._settings = QSettings(APP_ORG, APP_NAME)
        self._build_ui()
        self._load_settings()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # ── General Settings Group ──
        general_group = QGroupBox("General", self)
        gen_form = QFormLayout(general_group)

        # Theme selection
        self._theme_combo = QComboBox(self)
        self._theme_combo.addItem("Dark", "dark")
        self._theme_combo.addItem("Light", "light")
        gen_form.addRow("Theme:", self._theme_combo)

        # Default output folder
        folder_layout = QHBoxLayout()
        self._default_folder_edit = QLineEdit(self)
        self._default_folder_edit.setPlaceholderText("Leave empty to use source folder")
        folder_btn = QPushButton("Browse...", self)
        folder_btn.clicked.connect(self._browse_default_folder)
        folder_layout.addWidget(self._default_folder_edit)
        folder_layout.addWidget(folder_btn)
        gen_form.addRow("Default Output Folder:", folder_layout)

        self._auto_open_folder = QCheckBox("Automatically open output folder after conversion", self)
        gen_form.addRow("", self._auto_open_folder)

        layout.addWidget(general_group)

        # ── Performance Settings Group ──
        perf_group = QGroupBox("Performance", self)
        perf_form = QFormLayout(perf_group)

        self._worker_spin = QSpinBox(self)
        self._worker_spin.setRange(1, max(1, (os.cpu_count() or 4) * 2))
        self._worker_spin.setValue(MAX_WORKERS)
        perf_form.addRow("Worker Threads:", self._worker_spin)

        layout.addWidget(perf_group)

        # ── Format Defaults Group ──
        fmt_group = QGroupBox("Format Quality Defaults", self)
        fmt_form = QFormLayout(fmt_group)

        self._jpeg_quality_spin = QSpinBox(self)
        self._jpeg_quality_spin.setRange(1, 100)
        self._jpeg_quality_spin.setValue(DEFAULT_JPEG_QUALITY)
        fmt_form.addRow("JPEG Quality (1-100):", self._jpeg_quality_spin)

        self._png_comp_spin = QSpinBox(self)
        self._png_comp_spin.setRange(0, 9)
        self._png_comp_spin.setValue(DEFAULT_PNG_COMPRESSION)
        fmt_form.addRow("PNG Compression (0-9):", self._png_comp_spin)

        self._heic_quality_spin = QSpinBox(self)
        self._heic_quality_spin.setRange(1, 100)
        self._heic_quality_spin.setValue(DEFAULT_HEIC_QUALITY)
        fmt_form.addRow("HEIC Quality (1-100):", self._heic_quality_spin)

        self._webp_quality_spin = QSpinBox(self)
        self._webp_quality_spin.setRange(1, 100)
        self._webp_quality_spin.setValue(DEFAULT_WEBP_QUALITY)
        fmt_form.addRow("WEBP Quality (1-100):", self._webp_quality_spin)

        layout.addWidget(fmt_group)

        # ── Dialog Buttons ──
        btn_box = QHBoxLayout()
        btn_box.addStretch()

        self._save_btn = QPushButton("Save", self)
        self._save_btn.setObjectName("primary")
        self._save_btn.clicked.connect(self._save_and_accept)

        self._cancel_btn = QPushButton("Cancel", self)
        self._cancel_btn.clicked.connect(self.reject)

        btn_box.addWidget(self._cancel_btn)
        btn_box.addWidget(self._save_btn)
        layout.addLayout(btn_box)

    def _browse_default_folder(self) -> None:
        curr = self._default_folder_edit.text()
        chosen = QFileDialog.getExistingDirectory(self, "Select Default Output Folder", curr)
        if chosen:
            self._default_folder_edit.setText(chosen)

    def _load_settings(self) -> None:
        theme = self._settings.value("general/theme", "dark")
        idx = self._theme_combo.findData(theme)
        if idx >= 0:
            self._theme_combo.setCurrentIndex(idx)

        self._default_folder_edit.setText(self._settings.value("general/default_output_dir", ""))
        self._auto_open_folder.setChecked(
            self._settings.value("general/auto_open_output", False, type=bool)
        )

        self._worker_spin.setValue(
            int(self._settings.value("performance/max_workers", MAX_WORKERS))
        )
        self._jpeg_quality_spin.setValue(
            int(self._settings.value("defaults/jpeg_quality", DEFAULT_JPEG_QUALITY))
        )
        self._png_comp_spin.setValue(
            int(self._settings.value("defaults/png_compression", DEFAULT_PNG_COMPRESSION))
        )
        self._heic_quality_spin.setValue(
            int(self._settings.value("defaults/heic_quality", DEFAULT_HEIC_QUALITY))
        )
        self._webp_quality_spin.setValue(
            int(self._settings.value("defaults/webp_quality", DEFAULT_WEBP_QUALITY))
        )

    def _save_and_accept(self) -> None:
        self._settings.setValue("general/theme", self._theme_combo.currentData())
        self._settings.setValue("general/default_output_dir", self._default_folder_edit.text().strip())
        self._settings.setValue("general/auto_open_output", self._auto_open_folder.isChecked())

        self._settings.setValue("performance/max_workers", self._worker_spin.value())
        self._settings.setValue("defaults/jpeg_quality", self._jpeg_quality_spin.value())
        self._settings.setValue("defaults/png_compression", self._png_comp_spin.value())
        self._settings.setValue("defaults/heic_quality", self._heic_quality_spin.value())
        self._settings.setValue("defaults/webp_quality", self._webp_quality_spin.value())

        self.accept()

    def get_theme(self) -> str:
        return self._theme_combo.currentData() or "dark"

    def get_default_output_folder(self) -> Optional[Path]:
        val = self._default_folder_edit.text().strip()
        return Path(val) if val else None

    def get_max_workers(self) -> int:
        return self._worker_spin.value()

    def get_auto_open_output(self) -> bool:
        return self._auto_open_folder.isChecked()
