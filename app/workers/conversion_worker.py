"""Background conversion workers for PySide6. Keeps the GUI thread non-blocking."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from pathlib import Path
from threading import Event, Lock

from PySide6.QtCore import QObject, QRunnable, QThread, Signal

from app.core.conversion_manager import ConversionManager
from app.models import ConversionOptions, ConversionResult, FileStatus, ImageJob

logger = logging.getLogger(__name__)


class ConversionSignals(QObject):
    started = Signal(str)
    finished = Signal(object)


class ConversionRunnable(QRunnable):
    """Single-item runnable for QThreadPool execution."""

    def __init__(
        self,
        source: Path,
        options: ConversionOptions,
        cancel_event: Event,
        manager: ConversionManager,
    ) -> None:
        super().__init__()
        self.source = Path(source)
        self.options = options
        self.cancel_event = cancel_event
        self.manager = manager
        self.signals = ConversionSignals()
        self.setAutoDelete(True)

    def run(self) -> None:
        if self.cancel_event.is_set():
            skipped = ConversionResult(
                success=False,
                source_path=self.source,
                error="Cancelled",
                skipped=True,
            )
            job = ImageJob(source_path=self.source, status=FileStatus.SKIPPED, result=skipped)
            self.signals.finished.emit(job)
            return

        self.signals.started.emit(str(self.source))
        result = self.manager.convert_one(self.source, self.options)
        if result.skipped:
            status = FileStatus.SKIPPED
        elif result.success:
            status = FileStatus.COMPLETED
        else:
            status = FileStatus.FAILED

        job = ImageJob(source_path=self.source, status=status, result=result)
        self.signals.finished.emit(job)


class ConversionBatchWorker(QThread):
    """Background worker thread executing a batch of images without freezing the GUI."""

    job_started = Signal(str)  # source path string
    job_finished = Signal(object)  # ImageJob
    progress_updated = Signal(int, int)  # completed, total
    batch_finished = Signal(list)  # list[ConversionResult]

    def __init__(
        self,
        sources: Sequence[str | Path],
        options: ConversionOptions,
        manager: ConversionManager | None = None,
        max_workers: int | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self.sources = [Path(s) for s in sources]
        self.options = options
        self.manager = manager or ConversionManager()
        self.max_workers = max_workers
        self.cancel_event = Event()
        self._completed_count = 0
        self._total_count = len(self.sources)
        self._lock = Lock()

    @property
    def is_cancelled(self) -> bool:
        return self.cancel_event.is_set()

    def cancel(self) -> None:
        """Signal background jobs to safely halt starting new conversions."""
        self.cancel_event.set()

    def run(self) -> None:
        if not self.sources:
            self.batch_finished.emit([])
            return

        def on_job_started(job: ImageJob) -> None:
            self.job_started.emit(str(job.source_path))

        def on_job_progress(job: ImageJob) -> None:
            with self._lock:
                self._completed_count += 1
                count = self._completed_count
            self.job_finished.emit(job)
            self.progress_updated.emit(count, self._total_count)

        try:
            results = self.manager.convert_batch(
                self.sources,
                self.options,
                cancel_event=self.cancel_event,
                job_started=on_job_started,
                progress=on_job_progress,
                max_workers=self.max_workers,
            )
        except Exception as exc:
            logger.exception("Unexpected error in ConversionBatchWorker")
            results = [
                ConversionResult(
                    success=False,
                    source_path=path,
                    error=str(exc) or "Unexpected error",
                )
                for path in self.sources
            ]

        self.batch_finished.emit(results)
