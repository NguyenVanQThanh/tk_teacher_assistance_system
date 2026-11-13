# File Name: resource_limits.py
# Description: Process-wide concurrency guards shared by heavy endpoints/background jobs.
# Created At: 2026-11-13
# Created By: AI Agent

"""Process-local semaphores for memory/CPU-heavy work.

Why semaphores instead of "just run it in the threadpool":
  * PDF export (reportlab + embedded images) can allocate hundreds of MB per
    request. Letting 30 users export at once is the fastest way to OOM a
    2.5 GB backend container.
  * Document ingestion (PDF render + VLM calls + embeddings) is even heavier
    and is a background task; without a guard, uploading 20 documents starts
    20 concurrent ETL pipelines.

Both limits are per process. With N uvicorn workers the effective capacity is
N * the configured value, so keep DB pool sizing and the 5 GB RAM budget in
mind when scaling out (see docs/performance.md).
"""

import logging
import threading

from app.core import config

logger = logging.getLogger("smartlms.resource_limits")

# Keep at least one slot available even if an env var is set to 0/negative.
PDF_EXPORT_CONCURRENCY = max(1, int(config.PDF_EXPORT_CONCURRENCY))
IMPORT_CONCURRENCY = max(1, int(config.IMPORT_CONCURRENCY))
ETL_CONCURRENCY = max(1, int(config.ETL_CONCURRENCY))

# How long a PDF export request waits for a slot before returning 503.
PDF_EXPORT_ACQUIRE_TIMEOUT_SECONDS = 30

PDF_EXPORT_SEMAPHORE = threading.BoundedSemaphore(PDF_EXPORT_CONCURRENCY)
IMPORT_SEMAPHORE = threading.BoundedSemaphore(IMPORT_CONCURRENCY)
ETL_SEMAPHORE = threading.BoundedSemaphore(ETL_CONCURRENCY)

logger.info(
    "Resource limits: PDF_EXPORT_CONCURRENCY=%d IMPORT_CONCURRENCY=%d ETL_CONCURRENCY=%d MAX_INGEST_BYTES=%d",
    PDF_EXPORT_CONCURRENCY,
    IMPORT_CONCURRENCY,
    ETL_CONCURRENCY,
    config.MAX_INGEST_BYTES,
)
