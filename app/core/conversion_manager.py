"""Batch conversion manager — dispatches jobs to a thread pool."""
from __future__ import annotations

import logging
import threading
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Callable, List, Optional

from app.core.converter import ImageConverter
from app.models import ConversionOptions, ConversionResult

log = logging.getLogger(__name__)

ProgressCallback = Callable[[ConversionResult, int, int], None]
JobStartedCallback = Callable[[Path], None]


class ConversionManager:
    """
    Manages a batch conversion using a ThreadPoolExecutor.
    Thread-safe cancellation via threading.Event.
    """

    def __init__(self) -> None:
        self._converter = ImageConverter()

    def convert_batch(
        self,
        paths: List[Path],
        options: ConversionOptions,
        cancel_event: Optional[threading.Event] = None,
        progress: Optional[ProgressCallback] = None,
        job_started: Optional[JobStartedCallback] = None,
        max_workers: Optional[int] = None,
    ) -> List[ConversionResult]:
        """
        Convert all *paths* in parallel.

        Callbacks fire from worker threads — callers must be thread-safe
        (Qt signals handle this automatically).

        Args:
            paths: Input file list.
            options: Shared conversion options.
            cancel_event: Set to abort remaining jobs.
            progress: Called after each job finishes (result, done, total).
            job_started: Called when a job begins (path).
            max_workers: Thread count (defaults to config.MAX_WORKERS).
        """
        from app.config import MAX_WORKERS

        if max_workers is None:
            max_workers = MAX_WORKERS

        if cancel_event is None:
            cancel_event = threading.Event()

        total = len(paths)
        results: List[ConversionResult] = []
        done_count = 0
        lock = threading.Lock()

        def _run_one(path: Path) -> ConversionResult:
            if cancel_event.is_set():
                result = ConversionResult(
                    success=False, input_path=path,
                    error="Cancelled", skipped=True
                )
                return result
            if job_started:
                job_started(path)
            return self._converter.convert(path, options)

        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            future_to_path: dict[Future, Path] = {
                pool.submit(_run_one, p): p for p in paths
            }

            for future in as_completed(future_to_path):
                result = future.result()
                with lock:
                    done_count += 1
                    results.append(result)
                    current_done = done_count

                if progress:
                    progress(result, current_done, total)

        return results
