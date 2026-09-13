"""Output settings panel — format, quality, folder, options."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox, QFileDialog, QFrame, QHBoxLayout, QLabel,
    QPushButton, QSlider, QSpinBox, QStackedWidget, QVBoxLayout, QComboBox,
    QWidget,
)

from app.config import (
    DEFAULT_HEIC_QUALITY, DEFAULT_JPEG_QUALITY,
    DEFAULT_PNG_COMPRESSION, DEFAULT_WEBP_QUALITY,
)
from app.formats import OUTPUT_FORMAT_KEYS, SUPPORTED_FORMATS
from app.models import ConversionOptions, NamingMode
from app.ui.widgets import MutedLabel, SectionLabel


class OutputSection(QFrame):
    """
    Card containing all output options.
    Call get_conversion_options() to read current values.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("card")
        self._output_dir: Optional[Path] = None
        self._build_ui()

    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(12)

        title = SectionLabel("Output Settings", self)
        layout.addWidget(title)

        # ── Format row ──────────────────────────────────────────────
        fmt_row = QHBoxLayout()
        fmt_row.addWidget(QLabel("Convert to:", self))
        self._fmt_combo = QComboBox(self)
        for key in OUTPUT_FORMAT_KEYS:
            self._fmt_combo.addItem(SUPPORTED_FORMATS[key].label, key)
        self._fmt_combo.setMinimumWidth(130)
        self._fmt_combo.currentIndexChanged.connect(self._on_format_changed)
        fmt_row.addWidget(self._fmt_combo)
        fmt_row.addStretch()
        layout.addLayout(fmt_row)

        # ── Quality stacked widget ───────────────────────────────────
        # Each format gets its own quality control page
        self._quality_stack = QStackedWidget(self)

        # JPG page
        jpg_page, self._jpeg_slider, self._jpeg_val = self._make_slider_page(
            "JPEG Quality", 1, 100, DEFAULT_JPEG_QUALITY
        )
        self._quality_stack.addWidget(jpg_page)  # index 0

        # PNG page
        png_page, self._png_spin = self._make_spinbox_page(
            "PNG Compression", 0, 9, DEFAULT_PNG_COMPRESSION
        )
        self._quality_stack.addWidget(png_page)  # index 1

        # WEBP page
        webp_page, self._webp_slider, self._webp_val = self._make_slider_page(
            "WEBP Quality", 1, 100, DEFAULT_WEBP_QUALITY
        )
        self._quality_stack.addWidget(webp_page)  # index 2

        # HEIC page
        heic_page, self._heic_slider, self._heic_val = self._make_slider_page(
            "HEIC Quality", 1, 100, DEFAULT_HEIC_QUALITY
        )
        self._quality_stack.addWidget(heic_page)  # index 3

        # BMP / TIFF — no quality control
        blank = QWidget(self)
        self._quality_stack.addWidget(blank)  # index 4

        layout.addWidget(self._quality_stack)

        # ── Output folder ────────────────────────────────────────────
        layout.addWidget(SectionLabel("Output Folder", self))

        folder_row = QHBoxLayout()
        self._folder_lbl = QLabel("Same as source", self)
        self._folder_lbl.setObjectName("muted")
        self._folder_lbl.setWordWrap(True)
        folder_row.addWidget(self._folder_lbl, stretch=1)

        choose_btn = QPushButton("Choose…", self)
        choose_btn.setFixedWidth(90)
        choose_btn.clicked.connect(self._choose_folder)
        folder_row.addWidget(choose_btn)
        layout.addLayout(folder_row)

        # ── Options ──────────────────────────────────────────────────
        layout.addWidget(SectionLabel("Options", self))
        self._preserve_meta = QCheckBox("Preserve metadata (EXIF/IPTC)", self)
        self._preserve_meta.setChecked(True)
        self._overwrite = QCheckBox("Overwrite existing files", self)
        layout.addWidget(self._preserve_meta)
        layout.addWidget(self._overwrite)

        # Trigger initial page selection
        self._on_format_changed(0)

    # ------------------------------------------------------------------
    # Quality control page builders
    # ------------------------------------------------------------------

    def _make_slider_page(self, label: str, lo: int, hi: int, default: int):
        page = QWidget(self)
        row = QHBoxLayout(page)
        row.setContentsMargins(0, 0, 0, 0)
        lbl = QLabel(f"{label}:", page)
        lbl.setFixedWidth(130)
        slider = QSlider(Qt.Orientation.Horizontal, page)
        slider.setRange(lo, hi)
        slider.setValue(default)
        val_lbl = QLabel(str(default), page)
        val_lbl.setFixedWidth(30)
        slider.valueChanged.connect(lambda v, l=val_lbl: l.setText(str(v)))
        row.addWidget(lbl)
        row.addWidget(slider, stretch=1)
        row.addWidget(val_lbl)
        return page, slider, val_lbl

    def _make_spinbox_page(self, label: str, lo: int, hi: int, default: int):
        page = QWidget(self)
        row = QHBoxLayout(page)
        row.setContentsMargins(0, 0, 0, 0)
        lbl = QLabel(f"{label}:", page)
        lbl.setFixedWidth(130)
        spin = QSpinBox(page)
        spin.setRange(lo, hi)
        spin.setValue(default)
        spin.setFixedWidth(60)
        row.addWidget(lbl)
        row.addWidget(spin)
        row.addStretch()
        return page, spin

    # ------------------------------------------------------------------
    # Signals / slots
    # ------------------------------------------------------------------

    def _on_format_changed(self, _idx: int) -> None:
        key = self._fmt_combo.currentData()
        page_map = {
            "JPG": 0, "PNG": 1, "WEBP": 2, "HEIC": 3,
            "BMP": 4, "TIFF": 4, "GIF": 4,
        }
        self._quality_stack.setCurrentIndex(page_map.get(key, 4))

    def _choose_folder(self) -> None:
        start = str(self._output_dir) if self._output_dir else ""
        chosen = QFileDialog.getExistingDirectory(self, "Select Output Folder", start)
        if chosen:
            self._output_dir = Path(chosen)
            self._folder_lbl.setText(chosen)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_output_dir(self, path: Path) -> None:
        self._output_dir = path
        self._folder_lbl.setText(str(path))

    def get_output_dir(self) -> Optional[Path]:
        return self._output_dir

    def current_format_key(self) -> str:
        return self._fmt_combo.currentData() or "JPG"

    def set_format(self, key: str) -> None:
        idx = self._fmt_combo.findData(key)
        if idx >= 0:
            self._fmt_combo.setCurrentIndex(idx)

    def get_conversion_options(self) -> ConversionOptions:
        key = self.current_format_key()
        return ConversionOptions(
            output_format=key,
            output_dir=self._output_dir,
            jpeg_quality=self._jpeg_slider.value(),
            png_compression=self._png_spin.value(),
            heic_quality=self._heic_slider.value(),
            webp_quality=self._webp_slider.value(),
            preserve_metadata=self._preserve_meta.isChecked(),
            overwrite=self._overwrite.isChecked(),
            naming_mode=NamingMode.CONVERTED_SUFFIX,
        )

    def save_to_settings(self, settings) -> None:
        settings.setValue("output/format", self.current_format_key())
        if self._output_dir:
            settings.setValue("output/folder", str(self._output_dir))
        settings.setValue("output/jpeg_quality", self._jpeg_slider.value())
        settings.setValue("output/png_compression", self._png_spin.value())
        settings.setValue("output/heic_quality", self._heic_slider.value())
        settings.setValue("output/webp_quality", self._webp_slider.value())
        settings.setValue("output/preserve_meta", self._preserve_meta.isChecked())
        settings.setValue("output/overwrite", self._overwrite.isChecked())

    def load_from_settings(self, settings) -> None:
        fmt = settings.value("output/format", "JPG")
        self.set_format(fmt)
        folder = settings.value("output/folder")
        if folder:
            self.set_output_dir(Path(folder))
        self._jpeg_slider.setValue(int(settings.value("output/jpeg_quality", DEFAULT_JPEG_QUALITY)))
        self._png_spin.setValue(int(settings.value("output/png_compression", DEFAULT_PNG_COMPRESSION)))
        self._heic_slider.setValue(int(settings.value("output/heic_quality", DEFAULT_HEIC_QUALITY)))
        self._webp_slider.setValue(int(settings.value("output/webp_quality", DEFAULT_WEBP_QUALITY)))
        self._preserve_meta.setChecked(
            settings.value("output/preserve_meta", True, type=bool)
        )
        self._overwrite.setChecked(
            settings.value("output/overwrite", False, type=bool)
        )
