"""Batch conversion without a GUI. One failure does not stop the rest."""

from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Event

from app.core.converter import ImageConverter
from app.models import ConversionOptions, ConversionResult, FileStatus, ImageJob
from app.utils.platform import cpu_count

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[ImageJob], None]


class ConversionManager:
    def __init__(self, converter: ImageConverter | None = None, max_workers: int | None = None) -> None:
        self.converter = converter or ImageConverter()
        self.max_workers = max(1, max_workers or min(4, cpu_count()))

    def convert_one(self, source: str | Path, options: ConversionOptions) -> ConversionResult:
        return self.converter.convert(source, options)

    def convert_batch(
        self,
        sources: Sequence[str | Path],
        options: ConversionOptions,
        *,
        cancel_event: Event | None = None,
        job_started: ProgressCallback | None = None,
        progress: ProgressCallback | None = None,
        max_workers: int | None = None,
    ) -> list[ConversionResult]:
        paths = [Path(item) for item in sources]
        if not paths:
            return []

        workers = max(1, max_workers or self.max_workers)
        jobs = [ImageJob(source_path=path) for path in paths]
        results: list[ConversionResult] = []

        def run_job(job: ImageJob) -> ConversionResult:
            if cancel_event is not None and cancel_event.is_set():
                skipped = ConversionResult(
                    success=False,
                    source_path=job.source_path,
                    error="Cancelled",
                    skipped=True,
                )
                job.status = FileStatus.SKIPPED
                job.result = skipped
                if progress:
                    progress(job)
                return skipped

            job.status = FileStatus.CONVERTING
            if job_started:
                job_started(job)

            result = self.converter.convert(job.source_path, options)
            job.result = result
            job.status = FileStatus.COMPLETED if result.success else FileStatus.FAILED
            if progress:
                progress(job)
            return result

        if workers == 1:
            for job in jobs:
                if cancel_event is not None and cancel_event.is_set():
                    skipped = ConversionResult(
                        success=False,
                        source_path=job.source_path,
                        error="Cancelled",
                        skipped=True,
                    )
                    job.status = FileStatus.SKIPPED
                    job.result = skipped
                    if progress:
                        progress(job)
                    results.append(skipped)
                    continue
                results.append(run_job(job))
            return results

        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(run_job, job): job for job in jobs}
            for future in as_completed(futures):
                results.append(future.result())
        return results
