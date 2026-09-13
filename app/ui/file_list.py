"""File queue widget — list of images with thumbnails, search, sort, status."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional

from PySide6.QtCore import (
    QObject, QRunnable, QSize, Qt, QThreadPool, Signal, Slot,
)
from PySide6.QtGui import (
    QDragEnterEvent, QDropEvent, QMouseEvent, QPixmap,
)
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QScrollArea, QSizePolicy, QVBoxLayout, QWidget,
)

from app.formats import INPUT_EXTENSIONS
from app.models import FileStatus
from app.ui.widgets import (
    MutedLabel, SectionLabel, format_bytes, format_dimensions,
    make_status_label, update_status_label,
)
from app.workers.thumbnail_worker import PreviewRunnable
from app.config import UPLOAD_IMAGE_LOGO_PATH

log = logging.getLogger(__name__)

THUMBNAIL_SIZE = 64


# ---------------------------------------------------------------------------
# Inspect worker signals — defined at module level to avoid redefinition churn
# ---------------------------------------------------------------------------

class _InspectSignals(QObject):
    """Carries the result of a background image-info inspection."""
    ready = Signal(Path, object)  # (path, ImageInfo)


class _InspectRunnable(QRunnable):
    """Reads image headers on a pool thread; emits signals.ready when done."""

    def __init__(self, path: Path) -> None:
        super().__init__()
        self._p = path
        self.signals = _InspectSignals()
        # Do NOT use setAutoDelete(True) — Qt would delete the C++ object
        # before the queued signal is delivered, causing a segfault.
        self.setAutoDelete(False)

    @Slot()
    def run(self) -> None:
        from app.core.inspect import get_image_info
        info = get_image_info(self._p)
        if info:
            self.signals.ready.emit(self._p, info)


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
    """One row in the file queue showing checkbox, thumbnail, info, status, remove."""

    remove_requested = Signal(Path)
    selection_changed = Signal(Path, bool)

    def __init__(self, path: Path, parent=None) -> None:
        super().__init__(parent)
        self.path = path
        self.setObjectName("row")
        self.setFixedHeight(84)
        self._selected: bool = False
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(10)

        # Selection Checkbox
        self._check = QCheckBox(self)
        self._check.setChecked(False)
        self._check.setToolTip("Select file")
        self._check.toggled.connect(self._on_check_toggled)
        layout.addWidget(self._check)

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

    def is_selected(self) -> bool:
        return self._selected

    def set_selected(self, selected: bool) -> None:
        if self._selected != selected:
            self._selected = selected
            self._check.blockSignals(True)
            self._check.setChecked(selected)
            self._check.blockSignals(False)
            self._update_selection_style()
            self.selection_changed.emit(self.path, selected)

    def _on_check_toggled(self, checked: bool) -> None:
        self._selected = checked
        self._update_selection_style()
        self.selection_changed.emit(self.path, checked)

    def _update_selection_style(self) -> None:
        self.setObjectName("rowActive" if self._selected else "row")
        self.style().unpolish(self)
        self.style().polish(self)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            # Clicking anywhere on the row toggles selection
            self.set_selected(not self._selected)
        super().mousePressEvent(event)

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

        # Keep strong Python references to runnables so their embedded
        # signals QObjects are not garbage-collected before queued signals fire.
        # Without this, Qt's C++ side can be alive while Python deletes the
        # object → segfault when the queued signal is delivered.
        self._active_runnables: List = []

        self._build_ui()

    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header bar ──────────────────────────────────────────────
        header = QFrame(self)
        header.setObjectName("card")
        header.setStyleSheet("border-radius: 8px 8px 0 0;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(12, 8, 12, 8)
        h_layout.setSpacing(10)

        self._count_lbl = SectionLabel("0 images", self)

        # Select-all checkbox
        self._select_all_chk = QCheckBox("Select all", self)
        self._select_all_chk.setToolTip("Select / deselect all visible files")
        self._select_all_chk.toggled.connect(self._toggle_select_all)

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
        self._remove_sel_btn.setToolTip("Remove checked files from the queue")
        self._remove_sel_btn.clicked.connect(self._remove_selected)

        self._clear_btn = QPushButton("Clear All", self)
        self._clear_btn.setFixedHeight(28)
        self._clear_btn.clicked.connect(self.clear_all)

        h_layout.addWidget(self._count_lbl)
        h_layout.addSpacing(8)
        h_layout.addWidget(self._select_all_chk)
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

        icon = QLabel(w)
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
            row.selection_changed.connect(lambda _p, _checked: self._update_count())
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
        self._select_all_chk.blockSignals(True)
        self._select_all_chk.setChecked(False)
        self._select_all_chk.blockSignals(False)
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
        """Remove only rows that the user has explicitly selected (checked)."""
        to_remove = [
            p for p, row in self._rows.items() if row.is_selected()
        ]
        if not to_remove:
            return  # nothing selected — do nothing
        for p in to_remove:
            self._remove_row(p)

    def _toggle_select_all(self, checked: bool) -> None:
        """Select or deselect all currently visible rows."""
        for row in self._rows.values():
            if not row.isHidden():
                row.set_selected(checked)
        self._update_count()

    def _update_count(self) -> None:
        n = len(self._rows)
        selected = sum(1 for r in self._rows.values() if r.is_selected())
        base = f"{n} image{'s' if n != 1 else ''}"
        if selected:
            self._count_lbl.setText(f"{base}  ·  {selected} selected")
        else:
            self._count_lbl.setText(base)

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
        # Disable autoDelete so the C++ QRunnable lives until Python GC
        # collects our reference in _active_runnables — prevents segfaults
        # where a queued signal fires into an already-freed C++ object.
        runnable.setAutoDelete(False)
        self._active_runnables.append(runnable)

        def _on_thumb_ready(p: Path, data: bytes, _r=row, _run=runnable) -> None:
            if p == _r.path:
                _r.set_thumbnail(data)
            # Release our reference once signal is delivered
            try:
                self._active_runnables.remove(_run)
            except ValueError:
                pass

        def _on_thumb_failed(p: Path, _run=runnable) -> None:
            try:
                self._active_runnables.remove(_run)
            except ValueError:
                pass

        runnable.signals.ready.connect(_on_thumb_ready)
        runnable.signals.failed.connect(_on_thumb_failed)
        self._thumbnail_pool.start(runnable)

    def _start_inspect(self, path: Path, row: FileQueueRow) -> None:
        runnable = _InspectRunnable(path)  # setAutoDelete(False) already set
        self._active_runnables.append(runnable)

        def _on_inspect_ready(p: Path, info, _r=row, _run=runnable) -> None:
            if p == _r.path:
                _r.set_meta(info.width, info.height, info.file_size, info.detected_format)
            # Release reference once delivered
            try:
                self._active_runnables.remove(_run)
            except ValueError:
                pass

        runnable.signals.ready.connect(_on_inspect_ready)
        self._thumbnail_pool.start(runnable)

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
