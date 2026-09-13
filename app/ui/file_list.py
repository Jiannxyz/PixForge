"""File queue list and row widgets with asynchronous thumbnail loading."""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import QSize, Qt, QThreadPool, Signal
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.core.inspect import ImagePreview
from app.formats import format_from_extension
from app.models import ConversionResult, FileStatus
from app.ui.widgets import MutedLabel, format_bytes, format_dimensions
from app.workers.thumbnail_worker import PreviewRunnable

logger = logging.getLogger(__name__)


class FileQueueRow(QFrame):
    """A single row representing an image in the conversion queue."""

    remove_requested = Signal(object)  # Path

    def __init__(self, path: Path, parent=None) -> None:
        super().__init__(parent)
        self.path = Path(path)
        self.setObjectName("row")
        self.setMinimumHeight(64)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 12, 8)
        layout.setSpacing(12)

        # Thumbnail box
        self.thumb_frame = QFrame()
        self.thumb_frame.setObjectName("thumbnailBox")
        self.thumb_frame.setFixedSize(52, 52)
        thumb_layout = QVBoxLayout(self.thumb_frame)
        thumb_layout.setContentsMargins(0, 0, 0, 0)
        self.thumb_label = QLabel()
        self.thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumb_label.setFixedSize(50, 50)
        self.thumb_label.setStyleSheet("background: transparent; border-radius: 5px;")
        self.thumb_label.setText("IMG")
        thumb_layout.addWidget(self.thumb_label)
        layout.addWidget(self.thumb_frame)

        # File info column
        info_layout = QVBoxLayout()
        info_layout.setSpacing(3)
        info_layout.setContentsMargins(0, 0, 0, 0)

        # Filename
        self.filename_label = QLabel(self.path.name)
        self.filename_label.setStyleSheet("font-weight: 600; font-size: 13px; color: #f4f6fb;")
        self.filename_label.setToolTip(str(self.path))
        info_layout.addWidget(self.filename_label)

        # Subtitle: dimensions • size • format
        spec = format_from_extension(self.path)
        format_name = spec.key if spec else self.path.suffix.lstrip(".").upper()
        try:
            size_str = format_bytes(self.path.stat().st_size)
        except OSError:
            size_str = "—"

        self.sub_info_label = MutedLabel(f"— × —  •  {size_str}  •  {format_name}")
        self.sub_info_label.setStyleSheet("font-size: 11px; color: #8fa3c7;")
        self._size_str = size_str
        self._format_name = format_name
        info_layout.addWidget(self.sub_info_label)

        layout.addLayout(info_layout, stretch=1)

        # Status badge
        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("statusReady")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.status_label)

        # Remove button
        self.remove_btn = QPushButton("✕")
        self.remove_btn.setObjectName("iconButton")
        self.remove_btn.setToolTip("Remove this file")
        self.remove_btn.setFixedSize(26, 26)
        self.remove_btn.clicked.connect(lambda: self.remove_requested.emit(self.path))
        layout.addWidget(self.remove_btn)

    def set_preview(self, preview: ImagePreview) -> None:
        """Update thumbnail and dimensions after background inspection."""
        dim_str = format_dimensions(preview.width, preview.height)
        self.sub_info_label.setText(f"{dim_str}  •  {self._size_str}  •  {self._format_name}")

        if preview.thumbnail_jpeg:
            pixmap = QPixmap()
            if pixmap.loadFromData(preview.thumbnail_jpeg, "JPEG"):
                scaled = pixmap.scaled(
                    QSize(50, 50),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self.thumb_label.setText("")
                self.thumb_label.setPixmap(scaled)

    def set_status(self, status: FileStatus | str, result: ConversionResult | None = None) -> None:
        status_str = status.value if isinstance(status, FileStatus) else str(status)
        self.status_label.setToolTip("")

        if status_str == FileStatus.CONVERTING.value:
            self.status_label.setText("Converting…")
            self.status_label.setObjectName("statusConverting")
        elif status_str == FileStatus.COMPLETED.value:
            self.status_label.setText("✓ Completed")
            self.status_label.setObjectName("statusCompleted")
            if result and result.warning:
                self.status_label.setToolTip(result.warning)
        elif status_str == FileStatus.FAILED.value:
            self.status_label.setText("✗ Failed")
            self.status_label.setObjectName("statusFailed")
            if result and result.error:
                self.status_label.setToolTip(f"Error: {result.error}")
        elif status_str == FileStatus.SKIPPED.value:
            self.status_label.setText("⊘ Skipped")
            self.status_label.setObjectName("statusSkipped")
            if result and result.error:
                self.status_label.setToolTip(result.error)
        else:
            self.status_label.setText("Ready")
            self.status_label.setObjectName("statusReady")

        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)


class FileQueueWidget(QWidget):
    """Queue list widget managing file rows, selection, filtering, and thumbnail requests."""

    queue_changed = Signal(int)  # total count
    all_cleared = Signal()

class AddResult(int):
    """Integer subclass returning added count, with duplicates attribute."""

    added: int
    duplicates: int

    def __new__(cls, added: int, duplicates: int = 0):
        obj = super().__new__(cls, added)
        obj.added = added
        obj.duplicates = duplicates
        return obj


class FileQueueWidget(QWidget):
    """Queue list widget managing file rows, selection, filtering, and thumbnail requests."""

    queue_changed = Signal(int)  # total count
    all_cleared = Signal()
    files_dropped = Signal(list)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self._path_map: dict[Path, tuple[QListWidgetItem, FileQueueRow]] = {}
        self.thumbnail_pool = QThreadPool()
        self.thumbnail_pool.setMaxThreadCount(3)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(8)

        # Header bar
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        title_label = QLabel("Files")
        title_label.setStyleSheet("font-size: 15px; font-weight: 700; color: #f4f6fb;")
        header_layout.addWidget(title_label)

        self.count_badge = QLabel("0 images")
        self.count_badge.setObjectName("countBadge")
        header_layout.addWidget(self.count_badge)

        header_layout.addStretch()

        # Search filter
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filter files…")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setMaximumWidth(180)
        self.search_input.textChanged.connect(self._on_filter_changed)
        header_layout.addWidget(self.search_input)

        # Action buttons
        self.remove_selected_btn = QPushButton("Remove Selected")
        self.clear_all_btn = QPushButton("Clear All")
        self.remove_selected_btn.clicked.connect(self.remove_selected)
        self.clear_all_btn.clicked.connect(self.clear_all)

        header_layout.addWidget(self.remove_selected_btn)
        header_layout.addWidget(self.clear_all_btn)
        main_layout.addLayout(header_layout)

        # List widget
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.list_widget.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list_widget.setSpacing(4)
        main_layout.addWidget(self.list_widget)

        self._update_ui_state()

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event) -> None:
        paths = [Path(url.toLocalFile()) for url in event.mimeData().urls() if url.toLocalFile()]
        if paths:
            self.files_dropped.emit(paths)
        event.acceptProposedAction()

    @property
    def count(self) -> int:
        return len(self._path_map)

    def get_all_paths(self) -> list[Path]:
        return list(self._path_map.keys())

    def add_paths(self, paths: list[Path]) -> AddResult:
        """Add unique paths to the queue. Returns AddResult(added_count, duplicates_skipped)."""
        added_count = 0
        duplicates_count = 0
        for raw_path in paths:
            path = Path(raw_path).resolve()
            if not path.is_file():
                continue
            if path in self._path_map:
                duplicates_count += 1
                continue

            item = QListWidgetItem(self.list_widget)
            item.setSizeHint(QSize(0, 68))
            row = FileQueueRow(path)
            row.remove_requested.connect(self.remove_path)

            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, row)
            self._path_map[path] = (item, row)
            added_count += 1

            # Dispatch background thumbnail generation
            worker = PreviewRunnable(path)
            worker.signals.ready.connect(self._on_thumbnail_ready)
            self.thumbnail_pool.start(worker)

        if added_count > 0:
            self._update_ui_state()
            self.queue_changed.emit(self.count)
        return AddResult(added_count, duplicates_count)

    def remove_path(self, path: Path) -> None:
        target = Path(path).resolve()
        if target in self._path_map:
            item, row = self._path_map.pop(target)
            row_idx = self.list_widget.row(item)
            self.list_widget.takeItem(row_idx)
            self._update_ui_state()
            self.queue_changed.emit(self.count)

    def remove_selected(self) -> None:
        selected_items = self.list_widget.selectedItems()
        for item in selected_items:
            # find path
            for path, (it, row) in list(self._path_map.items()):
                if it is item:
                    self._path_map.pop(path)
                    row_idx = self.list_widget.row(item)
                    self.list_widget.takeItem(row_idx)
                    break
        self._update_ui_state()
        self.queue_changed.emit(self.count)

    def clear_all(self) -> None:
        self._path_map.clear()
        self.list_widget.clear()
        self._update_ui_state()
        self.queue_changed.emit(0)
        self.all_cleared.emit()

    def update_status(self, path: Path | str, status: FileStatus | str, result: ConversionResult | None = None) -> None:
        target = Path(path).resolve()
        if target in self._path_map:
            _, row = self._path_map[target]
            row.set_status(status, result)

    def reset_all_statuses(self) -> None:
        for _, row in self._path_map.values():
            row.set_status(FileStatus.WAITING)

    def _on_thumbnail_ready(self, preview: ImagePreview) -> None:
        target = Path(preview.path).resolve()
        if target in self._path_map:
            _, row = self._path_map[target]
            row.set_preview(preview)

    def _on_filter_changed(self, text: str) -> None:
        query = text.strip().lower()
        for path, (item, _) in self._path_map.items():
            if not query:
                item.setHidden(False)
            else:
                match = query in path.name.lower() or query in path.suffix.lower()
                item.setHidden(not match)

    def _update_ui_state(self) -> None:
        n = len(self._path_map)
        self.count_badge.setText(f"{n} {'image' if n == 1 else 'images'}")
        has_items = n > 0
        self.remove_selected_btn.setEnabled(has_items)
        self.clear_all_btn.setEnabled(has_items)
