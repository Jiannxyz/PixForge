"""File queue widget — list of images with thumbnails, search, sort, status."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional

from PySide6.QtCore import (
    QSize, Qt, QThreadPool, Signal,
)
from PySide6.QtGui import (
    QDragEnterEvent, QDropEvent, QPixmap,
)
from PySide6.QtWidgets import (
    QComboBox, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QScrollArea, QSizePolicy, QVBoxLayout, QWidget,
)

from app.formats import INPUT_EXTENSIONS
from app.models import FileStatus
from app.ui.widgets import (
    MutedLabel, SectionLabel, format_bytes, format_dimensions,
    make_status_label, update_status_label,
)
from app.workers.thumbnail_worker import PreviewRunnable

log = logging.getLogger(__name__)

THUMBNAIL_SIZE = 64


# ---------------------------------------------------------------------------
# AddResult
# ---------------------------------------------------------------------------

class AddResult(int):
    """
    int subclass returned by FileQueueWidget.add_paths().
    Backward-compatible with `if added_count > 0`.
    """
    added: int
    duplicates: int

    def __new__(cls, added: int, duplicates: int = 0) -> "AddResult":
        obj = super().__new__(cls, added)
        obj.added = added
        obj.duplicates = duplicates
        return obj


# ---------------------------------------------------------------------------
# Single row
# ---------------------------------------------------------------------------

class FileQueueRow(QFrame):
    """One row in the file queue showing thumbnail, info, status, remove."""

    remove_requested = Signal(Path)

    def __init__(self, path: Path, parent=None) -> None:
        super().__init__(parent)
        self.path = path
        self.setObjectName("row")
        self.setFixedHeight(84)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(10)

        # Thumbnail
        self._thumb = QLabel(self)
        self._thumb.setObjectName("thumbnailBox")
        self._thumb.setFixedSize(THUMBNAIL_SIZE, THUMBNAIL_SIZE)
        self._thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._thumb.setText("⏳")
        layout.addWidget(self._thumb)

        # File info column
        info = QVBoxLayout()
        info.setSpacing(2)
        self._name_lbl = QLabel(self.path.name, self)
        self._name_lbl.setStyleSheet("font-weight: 600; font-size: 13px;")
        self._name_lbl.setToolTip(str(self.path))

        self._meta_lbl = MutedLabel("", self)
        self._meta_lbl.setStyleSheet("font-size: 11px;")

        self._status_lbl = make_status_label(FileStatus.WAITING, self)

        info.addWidget(self._name_lbl)
        info.addWidget(self._meta_lbl)
        info.addWidget(self._status_lbl)
        layout.addLayout(info, stretch=1)

        # Remove button
        remove_btn = QPushButton("✕", self)
        remove_btn.setObjectName("iconButton")
        remove_btn.setFixedSize(24, 24)
        remove_btn.setToolTip("Remove")
        remove_btn.clicked.connect(lambda: self.remove_requested.emit(self.path))
        layout.addWidget(remove_btn)

    # ------------------------------------------------------------------

    def set_thumbnail(self, jpeg_bytes: bytes) -> None:
        px = QPixmap()
        px.loadFromData(jpeg_bytes)
        px = px.scaled(
            THUMBNAIL_SIZE, THUMBNAIL_SIZE,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._thumb.setPixmap(px)
        self._thumb.setText("")

    def set_meta(self, w: int, h: int, file_size: int, fmt: str) -> None:
        parts = []
        if w and h:
            parts.append(format_dimensions(w, h))
        if file_size:
            parts.append(format_bytes(file_size))
        if fmt:
            parts.append(fmt)
        self._meta_lbl.setText("  ·  ".join(parts))

    def set_status(self, status: FileStatus) -> None:
        update_status_label(self._status_lbl, status)

    def matches_filter(self, query: str) -> bool:
        return query.lower() in self.path.name.lower()


# ---------------------------------------------------------------------------
# Sort key helpers
# ---------------------------------------------------------------------------

def _sort_key(row: FileQueueRow, mode: str):
    if mode == "Name":
        return row.path.name.lower()
    if mode == "Format":
        return row.path.suffix.lower()
    if mode == "Size":
        return row.path.stat().st_size if row.path.exists() else 0
    if mode == "Status":
        return row._status_lbl.text()
    return row.path.name.lower()


# ---------------------------------------------------------------------------
# File queue widget
# ---------------------------------------------------------------------------

class FileQueueWidget(QWidget):
    """
    Full file queue: header (count + search + sort), scroll area of rows,
    and an empty-state placeholder.
    Emits *files_dropped* and *queue_changed*.
    """

    files_dropped = Signal(list)   # List[Path]
    queue_changed = Signal(int)    # current count

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)

        self._rows: Dict[Path, FileQueueRow] = {}
        self._seen: set[Path] = set()
        self._thumbnail_pool = QThreadPool()
        self._thumbnail_pool.setMaxThreadCount(3)

        self._build_ui()

    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header bar ──────────────────────────────────────────────
        header = QFrame(self)
        header.setObjectName("card")
        header.setStyleSheet("border-radius: 8px 8px 0 0; border-bottom: none;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(12, 8, 12, 8)
        h_layout.setSpacing(10)

        self._count_lbl = SectionLabel("0 images", self)

        self._search = QLineEdit(self)
        self._search.setPlaceholderText("🔍  Search files…")
        self._search.setMaximumWidth(220)
        self._search.textChanged.connect(self._apply_filter)

        sort_lbl = MutedLabel("Sort:", self)
        self._sort_combo = QComboBox(self)
        self._sort_combo.addItems(["Name", "Format", "Size", "Status"])
        self._sort_combo.setFixedWidth(100)
        self._sort_combo.currentTextChanged.connect(self._apply_sort)

        self._remove_sel_btn = QPushButton("Remove Selected", self)
        self._remove_sel_btn.setFixedHeight(28)
        self._remove_sel_btn.clicked.connect(self._remove_selected)

        self._clear_btn = QPushButton("Clear All", self)
        self._clear_btn.setFixedHeight(28)
        self._clear_btn.clicked.connect(self.clear_all)

        h_layout.addWidget(self._count_lbl)
        h_layout.addStretch()
        h_layout.addWidget(self._search)
        h_layout.addWidget(sort_lbl)
        h_layout.addWidget(self._sort_combo)
        h_layout.addWidget(self._remove_sel_btn)
        h_layout.addWidget(self._clear_btn)

        root.addWidget(header)

        # ── Scroll area ──────────────────────────────────────────────
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        container.setObjectName("card")
        container.setStyleSheet("border-radius: 0 0 8px 8px;")
        self._list_layout = QVBoxLayout(container)
        self._list_layout.setContentsMargins(8, 8, 8, 8)
        self._list_layout.setSpacing(4)
        self._list_layout.addStretch()

        scroll.setWidget(container)
        root.addWidget(scroll, stretch=1)

        # ── Empty state ──────────────────────────────────────────────
        self._empty_widget = self._make_empty_state()
        self._list_layout.insertWidget(0, self._empty_widget)
        self._empty_widget.setVisible(True)

    def _make_empty_state(self) -> QWidget:
        w = QWidget(self)
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, 40, 0, 40)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon = QLabel("🖼", w)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet("font-size: 40px;")

        title = QLabel("Drop images here to get started", w)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 15px; font-weight: 600;")

        sub = MutedLabel("HEIC  •  JPG  •  PNG  •  WEBP  •  GIF  •  TIFF  •  BMP", w)
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)

        note = MutedLabel("Everything is processed locally.\nYour images never leave your computer.", w)
        note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        note.setStyleSheet("color: #5a6478; font-size: 11px;")

        layout.addWidget(icon)
        layout.addWidget(title)
        layout.addWidget(sub)
        layout.addSpacing(4)
        layout.addWidget(note)
        return w

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_paths(self, paths: List[Path]) -> AddResult:
        """
        Add *paths* to the queue, skipping duplicates.
        Returns AddResult with .added and .duplicates counts.
        """
        added = 0
        dupes = 0
        for p in paths:
            resolved = p.resolve()
            if resolved in self._seen:
                dupes += 1
                continue
            self._seen.add(resolved)
            row = FileQueueRow(resolved)
            row.remove_requested.connect(self._remove_row)
            self._rows[resolved] = row

            # Insert before the trailing stretch
            self._list_layout.insertWidget(
                self._list_layout.count() - 1, row
            )

            self._start_thumbnail(resolved, row)
            self._start_inspect(resolved, row)
            added += 1

        if added:
            self._empty_widget.setVisible(False)
            self._update_count()
            self._apply_sort(self._sort_combo.currentText())
            self.queue_changed.emit(len(self._rows))

        return AddResult(added, dupes)

    def remove_paths(self, paths: List[Path]) -> None:
        for p in paths:
            resolved = p.resolve()
            self._remove_row(resolved)

    def clear_all(self) -> None:
        for row in list(self._rows.values()):
            self._list_layout.removeWidget(row)
            row.deleteLater()
        self._rows.clear()
        self._seen.clear()
        self._empty_widget.setVisible(True)
        self._update_count()
        self.queue_changed.emit(0)

    def all_paths(self) -> List[Path]:
        return list(self._rows.keys())

    def update_status(self, path: Path, status: FileStatus) -> None:
        resolved = path.resolve()
        if resolved in self._rows:
            self._rows[resolved].set_status(status)

    def reset_statuses(self) -> None:
        for row in self._rows.values():
            row.set_status(FileStatus.WAITING)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _remove_row(self, path: Path) -> None:
        resolved = path.resolve()
        if resolved in self._rows:
            row = self._rows.pop(resolved)
            self._seen.discard(resolved)
            self._list_layout.removeWidget(row)
            row.deleteLater()
            if not self._rows:
                self._empty_widget.setVisible(True)
            self._update_count()
            self.queue_changed.emit(len(self._rows))

    def _remove_selected(self) -> None:
        # Remove all currently visible (not hidden by filter)
        to_remove = [
            p for p, row in self._rows.items() if not row.isHidden()
        ]
        for p in to_remove:
            self._remove_row(p)

    def _update_count(self) -> None:
        n = len(self._rows)
        self._count_lbl.setText(f"{n} image{'s' if n != 1 else ''}")

    def _apply_filter(self, query: str) -> None:
        for row in self._rows.values():
            row.setVisible(row.matches_filter(query))

    def _apply_sort(self, mode: str) -> None:
        rows = list(self._rows.values())
        try:
            rows.sort(key=lambda r: _sort_key(r, mode))
        except Exception:
            pass
        # Re-insert in sorted order (before the stretch)
        for row in rows:
            self._list_layout.removeWidget(row)
        for row in rows:
            self._list_layout.insertWidget(
                self._list_layout.count() - 1, row
            )

    def _start_thumbnail(self, path: Path, row: FileQueueRow) -> None:
        runnable = PreviewRunnable(path, THUMBNAIL_SIZE)
        runnable.signals.ready.connect(
            lambda p, data, r=row: r.set_thumbnail(data) if p == r.path else None
        )
        self._thumbnail_pool.start(runnable)

    def _start_inspect(self, path: Path, row: FileQueueRow) -> None:
        from app.core.inspect import get_image_info
        # Run on the thumbnail pool (cheap — only reads header)
        from PySide6.QtCore import QRunnable, Slot

        class _InspectRunnable(QRunnable):
            def __init__(self, p, r):
                super().__init__()
                self._p = p
                self._r = r
                self.setAutoDelete(True)

            @Slot()
            def run(self):
                info = get_image_info(self._p)
                if info:
                    # Qt widget updates must happen on GUI thread
                    from PySide6.QtCore import QMetaObject, Qt
                    def _apply():
                        self._r.set_meta(
                            info.width, info.height,
                            info.file_size, info.detected_format
                        )
                    QMetaObject.invokeMethod(
                        self._r, _apply,  # type: ignore[arg-type]
                        Qt.ConnectionType.QueuedConnection,
                    )

        self._thumbnail_pool.start(_InspectRunnable(path, row))

    # ------------------------------------------------------------------
    # Drag-and-drop (the queue itself also accepts drops)
    # ------------------------------------------------------------------

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        paths: List[Path] = []
        for url in event.mimeData().urls():
            local = Path(url.toLocalFile())
            if local.is_dir():
                from app.utils.filesystem import collect_image_paths
                paths.extend(collect_image_paths(local, recursive=True))
            elif local.is_file() and local.suffix.lower() in INPUT_EXTENSIONS:
                paths.append(local)
        if paths:
            self.files_dropped.emit(paths)
        event.acceptProposedAction()
