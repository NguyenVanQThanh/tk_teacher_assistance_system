"""
File Name: background_jobs.py
Description: In-memory background jobs for slow AI endpoints (avoids proxy timeouts such as Cloudflare 524).
Created At: 2026-11-17
Created By: AI Agent
Updated At: 2026-11-17
Updated By: AI Agent
"""
import logging
import threading
import time
from typing import Any, Callable, Optional
from uuid import uuid4

from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder

from app.core.database import SessionLocal
from models.models import User

logger = logging.getLogger("smartlms.background_jobs")

# ponytail: in-memory jobs, valid for a single backend process (uvicorn without --workers);
# move to a DB table or Redis when the backend scales to several processes.
_JOBS: dict = {}
_JOBS_LOCK = threading.Lock()
_TTL_SECONDS = 3600


def _run(job_id: str, user_id, fn: Callable[[Any, User], Any]) -> None:
    """Run fn(session, user) in a worker thread with its own DB session and store the outcome."""
    session = SessionLocal()
    try:
        user = session.get(User, user_id)
        result = fn(session, user)
        data = jsonable_encoder(result)
        outcome = {"status": "done", "result": data}
    except HTTPException as exc:
        outcome = {"status": "error", "http_status": exc.status_code, "detail": exc.detail}
    except Exception:  # noqa: BLE001 - reported as a generic failure, logged here
        logger.exception("Background job %s failed", job_id)
        outcome = {"status": "error", "http_status": 500,
                   "detail": {"code": "ERR-EXE-AI_GENERATION_FAILED", "message": "AI generation failed."}}
    finally:
        session.close()
    with _JOBS_LOCK:
        _JOBS[job_id].update(outcome)


def start_job(user_id, fn: Callable[[Any, User], Any]) -> dict:
    """Start fn in the background and return {job_id, status}."""
    now = time.time()
    job_id = uuid4().hex
    with _JOBS_LOCK:
        for k in [k for k, v in _JOBS.items() if now - v["created"] > _TTL_SECONDS]:
            del _JOBS[k]
        _JOBS[job_id] = {"status": "running", "user_id": str(user_id), "created": now}
    threading.Thread(target=_run, args=(job_id, user_id, fn), daemon=True).start()
    return {"job_id": job_id, "status": "running"}


def get_job(job_id: str, user_id) -> Optional[dict]:
    """Public job state, or None when unknown or owned by someone else."""
    job = _JOBS.get(job_id)
    if job is None or job["user_id"] != str(user_id):
        return None
    return {k: v for k, v in job.items() if k not in ("user_id", "created")}
