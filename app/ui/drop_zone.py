"""Drop zone widget — accepts drag-and-drop of images and folders."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import List

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QPixmap
from PySide6.QtWidgets import (
    QCheckBox, QFileDialog, QFrame, QHBoxLayout, QLabel,
    QPushButton, QSizePolicy, QVBoxLayout,
)

from app.config import UPLOAD_IMAGE_LOGO_PATH
from app.formats import INPUT_EXTENSIONS

log = logging.getLogger(__name__)


class DropZone(QFrame):
    """
    Drag-and-drop area at the top of the window.
    Emits *files_dropped* with a flat list of resolved paths.
    """

    files_dropped = Signal(list)  # List[Path]
    add_images_clicked = Signal()
    add_folder_clicked = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("dropZone")
        self.setAcceptDrops(True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setMinimumHeight(130)

        self._build_ui()

    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 18, 24, 18)
        layout.setSpacing(8)

        # Icon + primary text
        icon = QLabel(self)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if UPLOAD_IMAGE_LOGO_PATH.exists():
            pix = QPixmap(str(UPLOAD_IMAGE_LOGO_PATH)).scaled(
                48, 48,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            icon.setPixmap(pix)
        else:
            icon.setText("🖼")
            icon.setStyleSheet("font-size: 28px;")

        hint = QLabel("Drop images or folders here", self)
        hint.setObjectName("dropHint")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)

        sub = QLabel(
            "HEIC  •  JPG  •  PNG  •  WEBP  •  GIF  •  TIFF  •  BMP", self
        )
        sub.setObjectName("dropSub")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Buttons row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        btn_row.addStretch()

        self._add_images_btn = QPushButton("📂  Add Images", self)
        self._add_images_btn.setFixedHeight(34)
        self._add_images_btn.clicked.connect(self.add_images_clicked)

        self._add_folder_btn = QPushButton("📁  Add Folder", self)
        self._add_folder_btn.setFixedHeight(34)
        self._add_folder_btn.clicked.connect(self.add_folder_clicked)

        btn_row.addWidget(self._add_images_btn)
        btn_row.addWidget(self._add_folder_btn)
        btn_row.addStretch()

        # Subfolder checkbox
        self.include_subfolders = QCheckBox("Include subfolders", self)
        self.include_subfolders.setChecked(True)
        sf_row = QHBoxLayout()
        sf_row.addStretch()
        sf_row.addWidget(self.include_subfolders)
        sf_row.addStretch()

        layout.addWidget(icon)
        layout.addWidget(hint)
        layout.addWidget(sub)
        layout.addSpacing(6)
        layout.addLayout(btn_row)
        layout.addLayout(sf_row)

    # ------------------------------------------------------------------
    # Drag-and-drop handlers
    # ------------------------------------------------------------------

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setObjectName("dropZoneActive")
            self.style().unpolish(self)
            self.style().polish(self)

    def dragLeaveEvent(self, event) -> None:
        self._reset_style()

    def dropEvent(self, event: QDropEvent) -> None:
        self._reset_style()
        paths: List[Path] = []
        recursive = self.include_subfolders.isChecked()

        for url in event.mimeData().urls():
            local = Path(url.toLocalFile())
            if local.is_dir():
                from app.utils.filesystem import collect_image_paths
                paths.extend(collect_image_paths(local, recursive=recursive))
            elif local.is_file() and local.suffix.lower() in INPUT_EXTENSIONS:
                paths.append(local)

        if paths:
            log.info("Dropped %d paths from drop zone", len(paths))
            self.files_dropped.emit(paths)
        event.acceptProposedAction()

    def _reset_style(self) -> None:
        self.setObjectName("dropZone")
        self.style().unpolish(self)
        self.style().polish(self)
