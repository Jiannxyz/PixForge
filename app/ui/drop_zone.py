"""Drag-and-drop target for files and folders."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import QCheckBox, QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from app.ui.widgets import MutedLabel


class DropZone(QFrame):
    files_dropped = Signal(list)
    add_images_clicked = Signal()
    add_folder_clicked = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("dropZone")
        self.setAcceptDrops(True)
        self.setMinimumHeight(140)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(6)

        title = QLabel("DROP IMAGES HERE")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: 700; color: #f4f6fb; background: transparent;")
        hint = MutedLabel("Drag & drop images or folders here. All conversions run locally on your device.")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet("background: transparent;")
        formats = MutedLabel("Supports: HEIC • JPG • PNG • WEBP • GIF • TIFF • BMP • AVIF")
        formats.setAlignment(Qt.AlignmentFlag.AlignCenter)
        formats.setStyleSheet("font-size: 12px; color: #788296; background: transparent;")

        buttons = QHBoxLayout()
        buttons.setSpacing(12)
        buttons.addStretch()

        self.add_images_button = QPushButton("Add Images")
        self.add_folder_button = QPushButton("Add Folder")
        self.subfolder_checkbox = QCheckBox("Include subfolders")
        self.subfolder_checkbox.setChecked(True)
        self.subfolder_checkbox.setStyleSheet("background: transparent; color: #c5cdd8; font-size: 12px;")

        self.add_images_button.clicked.connect(self.add_images_clicked.emit)
        self.add_folder_button.clicked.connect(self.add_folder_clicked.emit)

        buttons.addWidget(self.add_images_button)
        buttons.addWidget(self.add_folder_button)
        buttons.addSpacing(8)
        buttons.addWidget(self.subfolder_checkbox)
        buttons.addStretch()

        layout.addStretch()
        layout.addWidget(title)
        layout.addWidget(hint)
        layout.addWidget(formats)
        layout.addSpacing(4)
        layout.addLayout(buttons)
        layout.addStretch()

    @property
    def include_subfolders(self) -> bool:
        return self.subfolder_checkbox.isChecked()


    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            self.setProperty("active", True)
            self.style().unpolish(self)
            self.style().polish(self)
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event) -> None:
        self.setProperty("active", False)
        self.style().unpolish(self)
        self.style().polish(self)
        event.accept()

    def dropEvent(self, event: QDropEvent) -> None:
        self.setProperty("active", False)
        self.style().unpolish(self)
        self.style().polish(self)
        paths = [Path(url.toLocalFile()) for url in event.mimeData().urls() if url.toLocalFile()]
        if paths:
            self.files_dropped.emit(paths)
        event.acceptProposedAction()
