"""Output configuration section: format, dynamic quality/compression, directory, and options."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSlider,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.config import (
    DEFAULT_HEIC_QUALITY,
    DEFAULT_JPEG_QUALITY,
    DEFAULT_OVERWRITE,
    DEFAULT_PNG_COMPRESS_LEVEL,
    DEFAULT_PRESERVE_METADATA,
    DEFAULT_WEBP_QUALITY,
)
from app.formats import output_format_keys
from app.models import ConversionOptions, NamingMode
from app.ui.widgets import MutedLabel, SectionLabel
from app.utils.platform import default_output_dir, open_folder


class OutputSection(QFrame):
    """Card containing destination format, dynamic quality sliders, folder, and save flags."""

    format_changed = Signal(str)
    output_dir_changed = Signal(Path)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("card")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(12)

        # Header
        header = SectionLabel("Output Settings")
        layout.addWidget(header)

        # Format & Dynamic Quality Row
        format_quality_layout = QHBoxLayout()
        format_quality_layout.setSpacing(20)

        # Format picker
        format_col = QVBoxLayout()
        format_col.setSpacing(4)
        format_col.addWidget(MutedLabel("Convert to format:"))
        self.format_combo = QComboBox()
        for key in output_format_keys():
            self.format_combo.addItem(key)
        self.format_combo.currentTextChanged.connect(self._on_format_changed)
        self.format_combo.setMinimumWidth(120)
        format_col.addWidget(self.format_combo)
        format_quality_layout.addLayout(format_col)

        # Dynamic Quality / Compression stack
        self.quality_stack = QStackedWidget()

        # Page 0: JPEG Quality (1-100)
        self.jpeg_widget, self.jpeg_slider, self.jpeg_val_label = self._create_slider_widget(
            "JPEG Quality:", 1, 100, DEFAULT_JPEG_QUALITY
        )
        self.quality_stack.addWidget(self.jpeg_widget)

        # Page 1: PNG Compression (0-9)
        self.png_widget, self.png_slider, self.png_val_label = self._create_slider_widget(
            "PNG Compression (0–9):", 0, 9, DEFAULT_PNG_COMPRESS_LEVEL
        )
        self.quality_stack.addWidget(self.png_widget)

        # Page 2: HEIC / HEIF Quality (1-100)
        self.heic_widget, self.heic_slider, self.heic_val_label = self._create_slider_widget(
            "HEIC Quality:", 1, 100, DEFAULT_HEIC_QUALITY
        )
        self.quality_stack.addWidget(self.heic_widget)

        # Page 3: WEBP Quality (1-100)
        self.webp_widget, self.webp_slider, self.webp_val_label = self._create_slider_widget(
            "WEBP Quality:", 1, 100, DEFAULT_WEBP_QUALITY
        )
        self.quality_stack.addWidget(self.webp_widget)

        # Page 4: Lossless / No settings (BMP, TIFF, AVIF)
        self.lossless_widget = QWidget()
        lossless_layout = QVBoxLayout(self.lossless_widget)
        lossless_layout.setContentsMargins(0, 0, 0, 0)
        lossless_layout.setSpacing(4)
        lossless_layout.addWidget(MutedLabel("Quality:"))
        lossless_label = QLabel("Lossless / standard encoding")
        lossless_label.setStyleSheet("color: #8fa3c7; padding-top: 6px;")
        lossless_layout.addWidget(lossless_label)
        self.quality_stack.addWidget(self.lossless_widget)

        format_quality_layout.addWidget(self.quality_stack, stretch=1)
        layout.addLayout(format_quality_layout)

        # Output Folder Row
        folder_col = QVBoxLayout()
        folder_col.setSpacing(4)
        folder_col.addWidget(MutedLabel("Output Folder:"))

        folder_row = QHBoxLayout()
        folder_row.setSpacing(8)

        self.folder_input = QLineEdit()
        self.folder_input.setText(str(default_output_dir()))
        folder_row.addWidget(self.folder_input, stretch=1)

        self.browse_btn = QPushButton("Choose Folder")
        self.browse_btn.clicked.connect(self._choose_folder)
        folder_row.addWidget(self.browse_btn)

        self.open_folder_btn = QPushButton("Open Folder")
        self.open_folder_btn.clicked.connect(self._open_current_folder)
        folder_row.addWidget(self.open_folder_btn)

        folder_col.addLayout(folder_row)
        layout.addLayout(folder_col)

        # Checkboxes Row
        checks_row = QHBoxLayout()
        checks_row.setSpacing(24)

        self.metadata_checkbox = QCheckBox("Preserve metadata (EXIF, ICC, XMP)")
        self.metadata_checkbox.setChecked(DEFAULT_PRESERVE_METADATA)
        checks_row.addWidget(self.metadata_checkbox)

        self.overwrite_checkbox = QCheckBox("Overwrite existing files")
        self.overwrite_checkbox.setChecked(DEFAULT_OVERWRITE)
        checks_row.addWidget(self.overwrite_checkbox)

        checks_row.addStretch()
        layout.addLayout(checks_row)

        self._update_quality_view(self.format_combo.currentText())

    def _create_slider_widget(
        self, label_text: str, min_val: int, max_val: int, default_val: int
    ) -> tuple[QWidget, QSlider, QLabel]:
        widget = QWidget()
        vbox = QVBoxLayout(widget)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(4)

        header_row = QHBoxLayout()
        header_label = MutedLabel(label_text)
        val_label = QLabel(str(default_val))
        val_label.setStyleSheet("font-weight: 700; color: #f4f6fb;")
        header_row.addWidget(header_label)
        header_row.addStretch()
        header_row.addWidget(val_label)
        vbox.addLayout(header_row)

        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(min_val, max_val)
        slider.setValue(default_val)
        slider.valueChanged.connect(lambda val: val_label.setText(str(val)))
        vbox.addWidget(slider)

        return widget, slider, val_label

    def _on_format_changed(self, format_key: str) -> None:
        self._update_quality_view(format_key)
        self.format_changed.emit(format_key)

    def _update_quality_view(self, format_key: str) -> None:
        key = format_key.upper()
        if key in {"JPG", "JPEG"}:
            self.quality_stack.setCurrentWidget(self.jpeg_widget)
        elif key == "PNG":
            self.quality_stack.setCurrentWidget(self.png_widget)
        elif key in {"HEIC", "HEIF"}:
            self.quality_stack.setCurrentWidget(self.heic_widget)
        elif key == "WEBP":
            self.quality_stack.setCurrentWidget(self.webp_widget)
        else:
            self.quality_stack.setCurrentWidget(self.lossless_widget)

    def _choose_folder(self) -> None:
        current = self.folder_input.text().strip() or str(default_output_dir())
        chosen = QFileDialog.getExistingDirectory(self, "Select Output Folder", current)
        if chosen:
            self.folder_input.setText(chosen)
            self.output_dir_changed.emit(Path(chosen))

    def _open_current_folder(self) -> None:
        folder_path = self.get_output_dir()
        open_folder(folder_path)

    def get_output_dir(self) -> Path:
        raw = self.folder_input.text().strip()
        if raw:
            return Path(raw).expanduser()
        return default_output_dir()

    def set_output_dir(self, path: Path | str) -> None:
        self.folder_input.setText(str(path))

    def get_selected_format(self) -> str:
        return self.format_combo.currentText()

    def set_selected_format(self, format_key: str) -> None:
        idx = self.format_combo.findText(format_key.upper())
        if idx >= 0:
            self.format_combo.setCurrentIndex(idx)

    def get_conversion_options(self) -> ConversionOptions:
        format_key = self.get_selected_format()
        return ConversionOptions(
            output_format=format_key,
            output_dir=self.get_output_dir(),
            quality=self.jpeg_slider.value(),
            png_compress_level=self.png_slider.value(),
            heic_quality=self.heic_slider.value(),
            webp_quality=self.webp_slider.value(),
            preserve_metadata=self.metadata_checkbox.isChecked(),
            overwrite=self.overwrite_checkbox.isChecked(),
            naming_mode=NamingMode.CONVERTED,
        )
