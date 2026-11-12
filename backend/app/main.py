# File Name: main.py
# Description: Main entry point of the FastAPI application.
# Created At: 2026-07-17
# Created By: Tam Khang
# Updated At: 2026-11-13
# Updated By: AI Agent

import sys
from pathlib import Path

# Ensure backend root is always in python sys.path
backend_root = str(Path(__file__).resolve().parent.parent)
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

import logging
import os
import re
from typing import Optional

from dotenv import load_dotenv
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

_TOKEN_QUERY_RE = re.compile(r"([?&]token=)[^&\s\"]*")

class _MaskTokenQueryFilter(logging.Filter):
    """Redact ?token=<JWT> (SSE EventSource auth) from uvicorn access-log lines."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.args, tuple):
            record.args = tuple(
                _TOKEN_QUERY_RE.sub(r"\1***", a) if isinstance(a, str) else a for a in record.args
            )
        return True

# ponytail: masks only the in-process uvicorn access log; reverse proxies must mask/disable
# query logging themselves. Upgrade path: short-lived single-purpose stream ticket endpoint.
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
from fastapi.staticfiles import StaticFiles

from app.core.config import QUESTION_IMAGE_DIR, QUESTION_IMAGE_URL_PREFIX, SGK_IMAGE_DIR, SGK_IMAGE_URL_PREFIX
from app.core.database import get_db
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
from app.modules.document.routers.documents import router as documents_router
from app.modules.admin.routers.users import router as admin_users_router
from app.modules.admin.routers.dashboard import router as admin_dashboard_router
from app.modules.exercise.routers.student_dashboard import router as student_dashboard_router
from app.modules.exercise.routers.teacher_schedule import router as teacher_schedule_router
from app.modules.exercise.routers.teacher_dashboard import router as teacher_dashboard_router

app = FastAPI(title="SmartLMS API", version="1.0.0")

# Enable CORS for Frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Import-Skipped-Count", "X-Import-Skipped", "X-Data-Version"],
)


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
        and path.startswith("/api")
        and not path.startswith("/api/v1/sync/stream")
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
app.include_router(questions_router)
app.include_router(assignments_router)
app.include_router(attempts_router)
app.include_router(sync_router)
app.include_router(documents_router)
app.include_router(admin_users_router)
app.include_router(admin_dashboard_router)
app.include_router(student_dashboard_router)
app.include_router(teacher_schedule_router)
app.include_router(teacher_dashboard_router)

# Serve question images from BE storage (path configurable via .env, see app/core/config.py)
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