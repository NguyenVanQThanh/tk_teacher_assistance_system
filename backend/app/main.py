# File Name: main.py
# Description: Main entry point of the FastAPI application.
# Created At: 2026-07-17
# Created By: Tam Khang
# Updated At: 2026-11-14
# Updated By: Tam Khang

import sys
from pathlib import Path

# Ensure backend root is always in python sys.path
backend_root = str(Path(__file__).resolve().parent.parent)
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

import asyncio
import logging
import os
import re
import time
from contextlib import asynccontextmanager, suppress
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from sqlalchemy import delete, insert
from starlette.concurrency import run_in_threadpool

# Load environment variables from .env file
load_dotenv()

# Configure root logging once so application loggers (INFO) are visible in console
if not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

logger = logging.getLogger("smartlms.startup")

_TOKEN_QUERY_RE = re.compile(r"([?&](?:token|ticket)=)[^&\s\"]*")

class _MaskTokenQueryFilter(logging.Filter):
    """Redact ?token=/?ticket= (defense in depth; SSE now uses a 30s ticket) from uvicorn access-log lines."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.args, tuple):
            record.args = tuple(
                _TOKEN_QUERY_RE.sub(r"\1***", a) if isinstance(a, str) else a for a in record.args
            )
        return True

# ponytail: masks only the in-process uvicorn access log; reverse proxies may still log the
# 30s single-use-purpose ticket, which is harmless once expired.
logging.getLogger("uvicorn.access").addFilter(_MaskTokenQueryFilter())


def _mask_key(value: str) -> str:
    """Mask an API key for logs: show only length, never the secret itself."""
    if not value:
        return "MISSING"
    return f"set({len(value)} chars)"


# Log scan OCR provider config at startup (masked) so Docker/env issues are visible in logs
logger.warning(
    "Scan OCR config: SCAN_AI_PROVIDER=%s | MISTRAL_API_KEY=%s | GEMINI_API_KEY=%s | ENABLE_MARKER_PDF=%s",
    os.environ.get("SCAN_AI_PROVIDER", "mistral"),
    _mask_key(os.environ.get("MISTRAL_API_KEY") or os.environ.get("MISTRAL_KEY")),
    _mask_key(os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_KEY")),
    os.environ.get("ENABLE_MARKER_PDF", "1"),
)

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import QUESTION_IMAGE_DIR, QUESTION_IMAGE_URL_PREFIX, SGK_IMAGE_DIR, SGK_IMAGE_URL_PREFIX
from app.core.database import SessionLocal, get_db
from models.models import ApiRequestMetric
from app.modules.exercise.services.sync_service import get_cached_version_snapshot

from app.modules.auth.routers.auth import router as auth_router
from app.modules.academic.routers.subjects import router as subjects_router
from app.modules.academic.routers.classes import router as classes_router
from app.modules.academic.routers.enrollments import router as enrollments_router
from app.modules.academic.routers.teacher_assignments import router as teacher_assignments_router
from app.modules.exercise.routers.exercises import router as exercises_router
from app.modules.exercise.routers.questions import router as questions_router
from app.modules.exercise.routers.assignments import router as assignments_router
from app.modules.exercise.routers.attempts import router as attempts_router
from app.modules.exercise.routers.sync import router as sync_router
from app.modules.exercise.routers.ai_generation import router as ai_generation_router
from app.modules.document.routers.documents import router as documents_router
from app.modules.admin.routers.users import router as admin_users_router
from app.modules.admin.routers.dashboard import router as admin_dashboard_router
from app.modules.admin.routers.roles import router as admin_roles_router
from app.modules.exercise.routers.student_dashboard import router as student_dashboard_router
from app.modules.exercise.routers.teacher_schedule import router as teacher_schedule_router
from app.modules.exercise.routers.teacher_dashboard import router as teacher_dashboard_router
from app.modules.monitoring.collector import collector
from app.modules.monitoring.middleware import monitoring_middleware, static_cache_middleware
from app.modules.monitoring.router import router as monitoring_router


# ---------------------------------------------------------------------------
# Realtime API monitoring persistence
# ---------------------------------------------------------------------------
# The in-memory collector is always active; DB persistence is opt-out so tests and dev
# environments without a reachable database can still serve the realtime dashboard.
def _env_float(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, str(default)))
    except (TypeError, ValueError):
        return float(default)


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, str(default)))
    except (TypeError, ValueError):
        return int(default)


MONITORING_FLUSH_INTERVAL_SECONDS = max(1.0, _env_float("MONITORING_FLUSH_INTERVAL_SECONDS", 5.0))
MONITORING_RETENTION_DAYS = max(1, _env_int("MONITORING_RETENTION_DAYS", 7))
MONITORING_PURGE_INTERVAL_SECONDS = max(60.0, _env_float("MONITORING_PURGE_INTERVAL_SECONDS", 3600.0))


def _metric_row(metric: Dict[str, Any]) -> Dict[str, Any]:
    """Map one collector metric dict onto api_request_metrics columns."""
    timestamp = metric.get("timestamp")
    if isinstance(timestamp, (int, float)):
        created_at = datetime.fromtimestamp(float(timestamp), tz=timezone.utc)
    else:
        created_at = datetime.now(timezone.utc)
    return {
        "request_id": str(metric.get("request_id") or "unknown")[:64],
        "method": str(metric.get("method") or "GET")[:10],
        "route": str(metric.get("route") or "")[:255],
        "path": str(metric.get("path") or "")[:512],
        "status_code": int(metric.get("status_code") or 0),
        "duration_ms": float(metric.get("duration_ms") or 0.0),
        "request_bytes": max(0, int(metric.get("request_bytes") or 0)),
        "response_bytes": max(0, int(metric.get("response_bytes") or 0)),
        "user_ref": str(metric.get("user_ref") or "anonymous")[:64],
        "ip_ref": str(metric.get("ip_ref") or "anonymous")[:64],
        "is_error": bool(metric.get("is_error")),
        "created_at": created_at,
    }


def _persist_metrics(batch: List[Dict[str, Any]]) -> None:
    """Bulk-insert a flushed batch. On any DB error the batch is requeued (bounded) and the
    application keeps running; monitoring must never take the API down."""
    rows: List[Dict[str, Any]] = []
    for metric in batch:
        try:
            rows.append(_metric_row(metric))
        except Exception:
            logger.debug("Skipping malformed API metric row", exc_info=True)
    if not rows:
        return

    db = SessionLocal()
    try:
        db.execute(insert(ApiRequestMetric), rows)
        db.commit()
    except Exception:
        db.rollback()
        collector.requeue(batch)
        logger.warning("Failed to persist %d API request metrics; requeued", len(batch), exc_info=True)
    finally:
        db.close()


def purge_old_metrics(days: int = MONITORING_RETENTION_DAYS) -> int:
    """Delete metrics older than the retention window. Returns the number of deleted rows."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=max(1, int(days)))
    db = SessionLocal()
    try:
        result = db.execute(delete(ApiRequestMetric).where(ApiRequestMetric.created_at < cutoff))
        db.commit()
        return int(result.rowcount or 0)
    except Exception:
        db.rollback()
        logger.debug("API request metric retention purge failed", exc_info=True)
        return 0
    finally:
        db.close()


async def flush_metrics_loop() -> None:
    """Flush buffered metrics every few seconds and purge old rows hourly."""
    last_purge = 0.0
    while True:
        try:
            batch = collector.flush_batch()
            if batch:
                await asyncio.to_thread(_persist_metrics, batch)

            now = time.monotonic()
            if now - last_purge >= MONITORING_PURGE_INTERVAL_SECONDS:
                last_purge = now
                await asyncio.to_thread(purge_old_metrics, MONITORING_RETENTION_DAYS)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.warning("Monitoring flush loop iteration failed", exc_info=True)
        await asyncio.sleep(MONITORING_FLUSH_INTERVAL_SECONDS)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start/stop the background metrics flush task with the application."""
    flush_task: Optional[asyncio.Task] = None
    if collector.persist_enabled():
        flush_task = asyncio.create_task(flush_metrics_loop(), name="monitoring-flush")
        logger.info(
            "API monitoring persistence enabled (flush every %ss, retention %s days)",
            MONITORING_FLUSH_INTERVAL_SECONDS,
            MONITORING_RETENTION_DAYS,
        )
    else:
        logger.info("API monitoring persistence disabled (MONITORING_PERSIST_ENABLED=0)")

    try:
        yield
    finally:
        if flush_task is not None:
            flush_task.cancel()
            with suppress(asyncio.CancelledError):
                await flush_task
            # Best-effort final flush so a graceful shutdown does not lose the last batch.
            try:
                remaining = collector.flush_batch()
                if remaining:
                    await asyncio.to_thread(_persist_metrics, remaining)
            except Exception:
                logger.debug("Final API metric flush failed", exc_info=True)


app = FastAPI(title="SmartLMS API", version="1.0.0", lifespan=lifespan)

# Enable CORS for Frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Import-Skipped-Count", "X-Import-Skipped", "X-Data-Version", "X-Request-ID"],
)

# Middleware order matters: the last registered HTTP middleware is the outermost one.
# add_data_version_header is registered below (outermost) -> monitoring -> static cache ->
# gzip -> CORS -> app. GZip skips text/event-stream (Starlette default exclusions), so SSE
# is unaffected.
app.add_middleware(GZipMiddleware, minimum_size=1024)
app.middleware("http")(static_cache_middleware)
app.middleware("http")(monitoring_middleware)


def _version_snapshot_sync() -> Optional[dict]:
    """
    Synchronous helper for the X-Data-Version middleware. Runs in a worker thread (never on the
    event loop). In tests get_db is overridden -> reuse that session, closing the override
    generator properly so the session is released; otherwise open a short-lived SessionLocal.
    """
    override = app.dependency_overrides.get(get_db)
    if override is not None:
        gen = override()
        db = next(gen)
        try:
            return get_cached_version_snapshot(db=db)
        finally:
            gen.close()  # drives the override's finally block -> session closed
    return get_cached_version_snapshot(db=None)


@app.middleware("http")
async def add_data_version_header(request: Request, call_next):
    """
    Stamp `X-Data-Version: <ISO8601 UTC>` on API GET responses so the FE can read the current
    data version from any response. The version is computed at most once per 2s (process cache)
    and the DB work runs in a threadpool so the event loop is never blocked. SSE and static
    mounts are skipped. Never breaks the request: any DB error simply skips the header.
    """
    response = await call_next(request)
    path = request.url.path
    if (
        request.method.upper() == "GET"
        and 200 <= response.status_code < 300  # no version leak on 401/403/errors
        # Defense in depth: never stamp a response that was not requested with credentials
        # (every /api GET requires auth today; a future public endpoint must not leak it).
        and request.headers.get("authorization")
        and path.startswith("/api")
        and not path.startswith("/api/v1/sync/stream")
        and not path.startswith("/api/v1/admin/monitoring/stream")
    ):
        try:
            snapshot = await run_in_threadpool(_version_snapshot_sync)
            if snapshot:
                response.headers["X-Data-Version"] = snapshot["version"]
        except Exception:
            logger.debug("X-Data-Version header skipped", exc_info=True)
    return response

# Register routers
app.include_router(auth_router)
app.include_router(subjects_router)
app.include_router(classes_router)
app.include_router(enrollments_router)
app.include_router(teacher_assignments_router)
app.include_router(exercises_router)
app.include_router(ai_generation_router)
app.include_router(questions_router)
app.include_router(assignments_router)
app.include_router(attempts_router)
app.include_router(sync_router)
app.include_router(documents_router)
app.include_router(admin_users_router)
app.include_router(admin_dashboard_router)
app.include_router(admin_roles_router)
app.include_router(student_dashboard_router)
app.include_router(teacher_schedule_router)
app.include_router(teacher_dashboard_router)
app.include_router(monitoring_router)

# Serve question images from BE storage (path configurable via .env, see app/core/config.py).
# Both mounts stay unconditional: the SGK figures are local static data loaded from
# sgk_data/images.tar (never uploaded through the storage backend), and keeping the
# question-image mount preserves URLs stored by earlier local-mode rows.
QUESTION_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
app.mount(
    QUESTION_IMAGE_URL_PREFIX,
    StaticFiles(directory=QUESTION_IMAGE_DIR),
    name="question-images",
)

# Serve SGK textbook figures read-only (StaticFiles only handles GET/HEAD)
SGK_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
app.mount(SGK_IMAGE_URL_PREFIX, StaticFiles(directory=SGK_IMAGE_DIR), name="sgk-images")

@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0.1"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)