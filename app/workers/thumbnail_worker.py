"""Background preview generation so the UI never opens full-resolution images."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, Signal

from app.core.inspect import inspect_and_thumbnail


class PreviewSignals(QObject):
    ready = Signal(object)


class PreviewRunnable(QRunnable):
    def __init__(self, source: Path) -> None:
        super().__init__()
        self.source = Path(source)
        self.signals = PreviewSignals()
        self.setAutoDelete(True)

    def run(self) -> None:
        preview = inspect_and_thumbnail(self.source)
        self.signals.ready.emit(preview)
