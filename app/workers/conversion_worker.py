"""QThread-based batch conversion worker."""
from __future__ import annotations

import threading
from pathlib import Path
from typing import List

from PySide6.QtCore import QThread, Signal

from app.core.conversion_manager import ConversionManager
from app.models import ConversionOptions, ConversionResult


class ConversionBatchWorker(QThread):
    """
    Runs ConversionManager.convert_batch() on a dedicated QThread.

    Signals (all queued-connected to the GUI thread automatically):
        job_started(path)            — emitted when a file begins converting
        job_finished(result)         — emitted after each file completes/fails
        progress_updated(done, total)— overall counter update
        batch_finished(results)      — emitted when the full batch is done
    """

    job_started = Signal(Path)
    job_finished = Signal(object)          # ConversionResult
    progress_updated = Signal(int, int)    # done, total
    batch_finished = Signal(list)          # List[ConversionResult]

    def __init__(
        self,
        paths: List[Path],
        options: ConversionOptions,
        max_workers: int | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._paths = paths
        self._options = options
        self._max_workers = max_workers
        self._cancel_event = threading.Event()
        self._manager = ConversionManager()
        self._lock = threading.Lock()

    def cancel(self) -> None:
        """Signal cancellation; currently-running jobs will finish naturally."""
        self._cancel_event.set()

    def run(self) -> None:
        def _on_started(path: Path) -> None:
            self.job_started.emit(path)

        def _on_progress(result: ConversionResult, done: int, total: int) -> None:
            self.job_finished.emit(result)
            self.progress_updated.emit(done, total)

        results = self._manager.convert_batch(
            paths=self._paths,
            options=self._options,
            cancel_event=self._cancel_event,
            progress=_on_progress,
            job_started=_on_started,
            max_workers=self._max_workers,
        )
        self.batch_finished.emit(results)
