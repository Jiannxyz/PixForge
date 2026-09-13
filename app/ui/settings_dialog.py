"""Settings dialog persisted via QSettings."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from app.config import (
    DEFAULT_HEIC_QUALITY,
    DEFAULT_JPEG_QUALITY,
    DEFAULT_MAX_WORKERS,
    DEFAULT_PNG_COMPRESS_LEVEL,
    DEFAULT_PRESERVE_METADATA,
)
from app.utils.platform import cpu_count, default_output_dir


class SettingsDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("PixForge Settings")
        self.setMinimumWidth(460)
        self.settings = QSettings("PixForge", "PixForge")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # General Group
        general_group = QGroupBox("General")
        gen_layout = QVBoxLayout(general_group)
        gen_layout.setSpacing(10)

        folder_label = QLabel("Default Output Folder:")
        gen_layout.addWidget(folder_label)

        folder_row = QHBoxLayout()
        self.folder_input = QLineEdit()
        self.browse_btn = QPushButton("Browse…")
        self.browse_btn.clicked.connect(self._browse_folder)
        folder_row.addWidget(self.folder_input, stretch=1)
        folder_row.addWidget(self.browse_btn)
        gen_layout.addLayout(folder_row)

        self.auto_open_checkbox = QCheckBox("Automatically open output folder after conversion")
        gen_layout.addWidget(self.auto_open_checkbox)

        self.preserve_meta_checkbox = QCheckBox("Preserve metadata by default")
        gen_layout.addWidget(self.preserve_meta_checkbox)

        layout.addWidget(general_group)

        # Performance Group
        perf_group = QGroupBox("Performance")
        perf_layout = QHBoxLayout(perf_group)
        perf_layout.addWidget(QLabel("Worker threads:"))
        self.workers_combo = QComboBox()
        self.workers_combo.addItem(f"Auto (recommended: {min(4, cpu_count())})", 0)
        for w in (1, 2, 4, 8, 16):
            self.workers_combo.addItem(str(w), w)
        perf_layout.addWidget(self.workers_combo)
        perf_layout.addStretch()
        layout.addWidget(perf_group)

        # Format Defaults Group
        defaults_group = QGroupBox("Default Quality & Compression")
        def_layout = QVBoxLayout(defaults_group)
        def_layout.setSpacing(10)

        # JPEG
        jpeg_row = QHBoxLayout()
        jpeg_row.addWidget(QLabel("Default JPEG Quality (1–100):"))
        self.jpeg_spin = QSpinBox()
        self.jpeg_spin.setRange(1, 100)
        jpeg_row.addWidget(self.jpeg_spin)
        def_layout.addLayout(jpeg_row)

        # PNG
        png_row = QHBoxLayout()
        png_row.addWidget(QLabel("Default PNG Compression (0–9):"))
        self.png_spin = QSpinBox()
        self.png_spin.setRange(0, 9)
        png_row.addWidget(self.png_spin)
        def_layout.addLayout(png_row)

        # HEIC
        heic_row = QHBoxLayout()
        heic_row.addWidget(QLabel("Default HEIC Quality (1–100):"))
        self.heic_spin = QSpinBox()
        self.heic_spin.setRange(1, 100)
        heic_row.addWidget(self.heic_spin)
        def_layout.addLayout(heic_row)

        layout.addWidget(defaults_group)

        # Dialog Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.cancel_btn = QPushButton("Cancel")
        self.save_btn = QPushButton("Save Settings")
        self.save_btn.setObjectName("primary")
        self.cancel_btn.clicked.connect(self.reject)
        self.save_btn.clicked.connect(self._save_settings)
        btn_row.addWidget(self.cancel_btn)
        btn_row.addWidget(self.save_btn)
        layout.addLayout(btn_row)

        self._load_settings()

    def _browse_folder(self) -> None:
        curr = self.folder_input.text().strip() or str(default_output_dir())
        chosen = QFileDialog.getExistingDirectory(self, "Select Default Output Folder", curr)
        if chosen:
            self.folder_input.setText(chosen)

    def _load_settings(self) -> None:
        default_dir = self.settings.value("default_output_dir", str(default_output_dir()))
        self.folder_input.setText(str(default_dir))

        auto_open = self.settings.value("auto_open_folder", False, type=bool)
        self.auto_open_checkbox.setChecked(auto_open)

        preserve_meta = self.settings.value("preserve_metadata", DEFAULT_PRESERVE_METADATA, type=bool)
        self.preserve_meta_checkbox.setChecked(preserve_meta)

        workers = self.settings.value("max_workers", 0, type=int)
        idx = self.workers_combo.findData(workers)
        if idx >= 0:
            self.workers_combo.setCurrentIndex(idx)

        jpeg_q = self.settings.value("jpeg_quality", DEFAULT_JPEG_QUALITY, type=int)
        self.jpeg_spin.setValue(jpeg_q)

        png_c = self.settings.value("png_compression", DEFAULT_PNG_COMPRESS_LEVEL, type=int)
        self.png_spin.setValue(png_c)

        heic_q = self.settings.value("heic_quality", DEFAULT_HEIC_QUALITY, type=int)
        self.heic_spin.setValue(heic_q)

    def _save_settings(self) -> None:
        self.settings.setValue("default_output_dir", self.folder_input.text().strip())
        self.settings.setValue("auto_open_folder", self.auto_open_checkbox.isChecked())
        self.settings.setValue("preserve_metadata", self.preserve_meta_checkbox.isChecked())
        self.settings.setValue("max_workers", self.workers_combo.currentData())
        self.settings.setValue("jpeg_quality", self.jpeg_spin.value())
        self.settings.setValue("png_compression", self.png_spin.value())
        self.settings.setValue("heic_quality", self.heic_spin.value())
        self.accept()
