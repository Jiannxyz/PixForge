"""Async thumbnail generation via QRunnable."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, Signal, Slot


class _ThumbnailSignals(QObject):
    ready = Signal(Path, bytes)   # (path, jpeg_bytes)
    failed = Signal(Path)


class PreviewRunnable(QRunnable):
    """
    Generates a JPEG thumbnail for *path* on a thread-pool thread.
    Emits signals.ready with the raw JPEG bytes on success.
    """

    def __init__(self, path: Path, size: int = 72) -> None:
        super().__init__()
        self.path = path
        self.size = size
        self.signals = _ThumbnailSignals()
        self.setAutoDelete(True)

    @Slot()
    def run(self) -> None:
        from app.core.inspect import make_thumbnail

        data = make_thumbnail(self.path, self.size)
        if data:
            self.signals.ready.emit(self.path, data)
        else:
            self.signals.failed.emit(self.path)
