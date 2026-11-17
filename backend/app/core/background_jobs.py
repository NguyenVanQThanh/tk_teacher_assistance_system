"""
File Name: background_jobs.py
Description: Postgres-backed job queue (table background_jobs) with in-process workers, progress, ETA and notifications.
Created At: 2026-11-17
Created By: AI Agent
Updated At: 2026-11-17
Updated By: AI Agent
"""
import logging
import statistics
import threading
import time
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import text
from fastapi.encoders import jsonable_encoder

from app.core import config
from app.core.database import SessionLocal
from models.models import BackgroundJob, User

logger = logging.getLogger("smartlms.background_jobs")

# kind -> (handler(session, user, payload) -> result, notification label, frontend link, default seconds)
_HANDLERS: Dict[str, Tuple[Callable[[Any, User, dict], Any], str, str, int]] = {}
_local = threading.local()
_stop = threading.Event()
_threads: List[threading.Thread] = []
POLL_SECONDS = 2.0
STALE_SECONDS = 600  # a RUNNING job untouched this long is presumed orphaned (heartbeat refreshes updated_at)
HEARTBEAT_SECONDS = 30
MAX_ACTIVE_PER_USER = 3  # queued + running jobs one user may hold
MAX_ATTEMPTS = 2  # a job interrupted by a restart is re-queued once, then failed


def register_handler(kind: str, fn: Callable[[Any, User, dict], Any], label: str, link: str,
                     default_seconds: int = 60) -> None:
    """Register the function that processes jobs of this kind."""
    _HANDLERS[kind] = (fn, label, link, default_seconds)


def current_job_id() -> Optional[UUID]:
    """Id of the job running in this thread (None outside a job); capture it before spawning threads."""
    return getattr(_local, "job_id", None)


def hold_ownership(session) -> None:
    """Lock this thread's job row until the caller commits and verify this run still owns it.

    Call right before a non-idempotent write: recovery cannot re-queue the job while the lock is held, and a
    run that was already re-queued or re-claimed gets a 409 instead of writing a duplicate. No-op outside a job."""
    job_id = current_job_id()
    if job_id is None:
        return
    job = session.query(BackgroundJob).filter(BackgroundJob.job_id == job_id).with_for_update().first()
    if job is None or job.status != "RUNNING" or job.attempts != getattr(_local, "attempt", job.attempts):
        session.rollback()
        raise HTTPException(status_code=409, detail={
            "code": "ERR-EXE-AI_GENERATION_FAILED", "message": "Job was superseded by a newer run."})


def report_for(job_id: Optional[UUID], stage: str, progress: int) -> None:
    """Publish progress of a job from any thread; a no-op without a job id. Never raises."""
    if job_id is None:
        return
    try:
        session = SessionLocal()
        try:
            session.query(BackgroundJob).filter(BackgroundJob.job_id == job_id).update(
                {"stage": stage, "progress": max(0, min(99, int(progress)))})
            session.commit()
        finally:
            session.close()
    except Exception:  # noqa: BLE001 - progress is best effort
        logger.debug("Could not report job progress", exc_info=True)


def report(stage: str, progress: int) -> None:
    """Publish progress of the job running in this thread."""
    report_for(current_job_id(), stage, progress)


def enqueue(session, user_id: UUID, kind: str, payload: dict) -> BackgroundJob:
    """Insert a QUEUED job and commit. A handler must be registered for the kind.

    Raises HTTPException 429 when the user already has MAX_ACTIVE_PER_USER queued or running jobs, so one
    account cannot flood the shared FIFO queue."""
    if kind not in _HANDLERS:
        raise ValueError(f"Unknown job kind: {kind}")
    if session.get_bind().dialect.name == "postgresql":
        # Serialize concurrent enqueues of one user so the cap check and the insert are atomic.
        session.execute(text("SELECT pg_advisory_xact_lock(hashtext(:k))"), {"k": f"job-enqueue:{user_id}"})
    active = session.query(BackgroundJob).filter(
        BackgroundJob.user_id == user_id, BackgroundJob.status.in_(("QUEUED", "RUNNING"))).count()
    if active >= MAX_ACTIVE_PER_USER:
        raise HTTPException(status_code=429, detail={
            "code": "ERR-EXE-AI_TOO_MANY_JOBS",
            "message": "Too many jobs in progress. Wait for one to finish."})
    job = BackgroundJob(user_id=user_id, kind=kind, payload=payload, status="QUEUED", progress=0)
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def _estimate_seconds(session, kind: str) -> int:
    """Median duration of the last 10 finished jobs of this kind, else the handler default."""
    rows = (session.query(BackgroundJob.started_at, BackgroundJob.finished_at)
            .filter(BackgroundJob.kind == kind, BackgroundJob.status == "DONE",
                    BackgroundJob.started_at.isnot(None), BackgroundJob.finished_at.isnot(None))
            .order_by(BackgroundJob.finished_at.desc()).limit(10).all())
    durations = [(_aware(f) - _aware(s)).total_seconds() for s, f in rows if _aware(f) >= _aware(s)]
    if durations:
        return max(5, int(statistics.median(durations)))
    return _HANDLERS[kind][3] if kind in _HANDLERS else 60


def _aware(dt: Optional[datetime]) -> Optional[datetime]:
    return dt if dt is None or dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def to_public(session, job: BackgroundJob, estimates: Optional[Dict[str, int]] = None) -> dict:
    """Client view of a job: queued|running|done|error with progress, stage and ETA seconds."""
    status = {"QUEUED": "queued", "RUNNING": "running", "DONE": "done", "FAILED": "error"}[job.status]
    if estimates is None:
        estimates = {}
    if job.kind not in estimates:
        estimates[job.kind] = _estimate_seconds(session, job.kind)
    est = estimates[job.kind]
    out: Dict[str, Any] = {
        "job_id": str(job.job_id), "kind": job.kind, "status": status,
        "progress": 100 if job.status == "DONE" else job.progress, "stage": job.stage,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "estimated_seconds": est,
    }
    if job.status == "RUNNING":
        started = _aware(job.started_at) or datetime.now(timezone.utc)
        out["eta_seconds"] = max(0, est - int((datetime.now(timezone.utc) - started).total_seconds()))
    elif job.status == "QUEUED":
        ahead = session.query(BackgroundJob).filter(
            BackgroundJob.status.in_(("QUEUED", "RUNNING")), BackgroundJob.created_at < job.created_at).count()
        out["queue_position"] = ahead + 1
        out["eta_seconds"] = est * (ahead // max(1, config.JOB_WORKERS) + 1)
    if job.status == "DONE":
        out["result"] = job.result
    elif job.status == "FAILED":
        out["http_status"] = (job.error or {}).get("http_status", 500)
        out["detail"] = (job.error or {}).get("detail")
    return out


def get_job(session, job_id: str, user_id: UUID, kind: Optional[str] = None,
            payload_match: Optional[Dict[str, Any]] = None) -> Optional[dict]:
    """Public job state, or None when unknown, owned by someone else, of another kind or payload."""
    try:
        jid = UUID(str(job_id))
    except ValueError:
        return None
    job = session.query(BackgroundJob).filter(
        BackgroundJob.job_id == jid, BackgroundJob.user_id == user_id).first()
    if job is None or (kind is not None and job.kind != kind):
        return None
    if payload_match and any((job.payload or {}).get(k) != v for k, v in payload_match.items()):
        return None
    return to_public(session, job)


def list_jobs(session, user_id: UUID, active_only: bool = False, limit: int = 20) -> List[dict]:
    """Newest jobs of one user."""
    q = session.query(BackgroundJob).filter(BackgroundJob.user_id == user_id)
    if active_only:
        q = q.filter(BackgroundJob.status.in_(("QUEUED", "RUNNING")))
    estimates: Dict[str, int] = {}  # one estimate query per kind, not per job
    return [to_public(session, j, estimates) for j in q.order_by(BackgroundJob.created_at.desc()).limit(limit).all()]


def _claim(session) -> Optional[UUID]:
    """Atomically take the oldest QUEUED job (FOR UPDATE SKIP LOCKED on Postgres)."""
    job = (session.query(BackgroundJob).filter(BackgroundJob.status == "QUEUED")
           .order_by(BackgroundJob.created_at).with_for_update(skip_locked=True).first())
    if job is None:
        session.rollback()
        return None
    job.status, job.progress, job.stage = "RUNNING", 0, "STARTING"
    job.started_at, job.attempts = datetime.now(timezone.utc), (job.attempts or 0) + 1
    session.commit()
    return job.job_id


def _finish(job_id: UUID, ok: bool, result: Any = None, error: Optional[dict] = None,
            attempt: Optional[int] = None) -> None:
    """Store the outcome and notify the owner in one transaction."""
    from app.modules.notification import service as notification_service
    session = SessionLocal()
    try:
        job = session.get(BackgroundJob, job_id)
        if job.status != "RUNNING" or (attempt is not None and job.attempts != attempt):
            logger.warning("Job %s was re-queued or re-claimed; discarding the stale outcome", job_id)
            return
        job.status = "DONE" if ok else "FAILED"
        job.progress = 100 if ok else job.progress
        job.finished_at = datetime.now(timezone.utc)
        job.result, job.error = (result if ok else None), (None if ok else error)
        # Drop uploaded file content: it is only needed to run the job.
        job.payload = _scrub(job.payload)
        _, label, link, _ = _HANDLERS.get(job.kind, (None, "Tác vụ", "/", 60))
        session.commit()  # the outcome is durable before the best-effort notification
        try:
            notification_service.notify(
                session, [job.user_id], "JOB_DONE" if ok else "JOB_FAILED",
                f"{label} đã hoàn tất" if ok else f"{label} thất bại",
                "Nhấn để xem kết quả." if ok else "Vui lòng thử lại.", link)
            session.commit()
        except Exception:  # noqa: BLE001 - a failed notification must never undo the job outcome
            session.rollback()
            logger.exception("Could not notify the owner of job %s", job_id)
    except Exception:  # noqa: BLE001
        session.rollback()
        logger.exception("Could not store the outcome of job %s", job_id)
    finally:
        session.close()


def run_one(job_id: UUID) -> None:
    """Run one claimed job with its own session; always ends in DONE or FAILED."""
    session = SessionLocal()
    _local.job_id = job_id
    attempt = None
    hb_stop = threading.Event()
    threading.Thread(target=_heartbeat, args=(job_id, hb_stop), daemon=True).start()
    try:
        job = session.get(BackgroundJob, job_id)
        attempt = _local.attempt = job.attempts
        fn = _HANDLERS[job.kind][0]
        user = session.get(User, job.user_id)
        outcome = (True, jsonable_encoder(fn(session, user, job.payload)), None)
    except HTTPException as exc:
        session.rollback()
        outcome = (False, None, {"http_status": exc.status_code, "detail": exc.detail})
    except Exception:  # noqa: BLE001 - reported to the client as a generic failure
        session.rollback()
        logger.exception("Job %s failed", job_id)
        outcome = (False, None, {"http_status": 500, "detail": {
            "code": "ERR-EXE-AI_GENERATION_FAILED", "message": "Job failed."}})
    finally:
        hb_stop.set()
        _local.job_id = None
        session.close()
    _finish(job_id, *outcome, attempt=attempt)


_FILE_KEYS = ("file_text", "question_file", "answer_file")


def _scrub(payload: Optional[dict]) -> dict:
    """Payload without uploaded file content (only needed while the job can still run)."""
    return {k: v for k, v in (payload or {}).items() if k not in _FILE_KEYS}


def _heartbeat(job_id: UUID, stop: threading.Event) -> None:
    """Touch updated_at while a job runs so other processes do not mistake it for an orphan."""
    while not stop.wait(HEARTBEAT_SECONDS):
        try:
            session = SessionLocal()
            try:
                session.query(BackgroundJob).filter(BackgroundJob.job_id == job_id).update(
                    {"updated_at": datetime.now(timezone.utc)})
                session.commit()
            finally:
                session.close()
        except Exception:  # noqa: BLE001
            logger.debug("Heartbeat failed", exc_info=True)


def recover_interrupted() -> int:
    """After a restart: stale RUNNING jobs were cut off; re-queue them once, then mark them FAILED.

    Only jobs not touched for STALE_SECONDS are recovered, so a second backend process never steals a live job."""
    from datetime import timedelta
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=STALE_SECONDS)
    session = SessionLocal()
    try:
        n = 0
        for job in session.query(BackgroundJob).filter(
                BackgroundJob.status == "RUNNING", BackgroundJob.updated_at < cutoff).all():
            if (job.attempts or 0) < MAX_ATTEMPTS:
                job.status, job.progress, job.stage = "QUEUED", 0, None
            else:
                job.status, job.finished_at = "FAILED", datetime.now(timezone.utc)
                job.payload = _scrub(job.payload)
                job.error = {"http_status": 500, "detail": {
                    "code": "ERR-EXE-AI_GENERATION_FAILED", "message": "Job interrupted by a restart."}}
            n += 1
        session.commit()
        return n
    finally:
        session.close()


RECOVER_EVERY_SECONDS = 60


def _worker_loop() -> None:
    last_recover = 0.0
    while not _stop.is_set():
        job_id = None
        try:
            session = SessionLocal()
            try:
                job_id = _claim(session)
            finally:
                session.close()
        except Exception:  # noqa: BLE001
            logger.exception("Job claim failed")
        if job_id is None:
            # Periodic sweep: jobs orphaned by a crashed process must not count against the user cap forever.
            if time.monotonic() - last_recover > RECOVER_EVERY_SECONDS:
                last_recover = time.monotonic()
                try:
                    recover_interrupted()
                except Exception:  # noqa: BLE001
                    logger.exception("Periodic job recovery failed")
            _stop.wait(POLL_SECONDS)
            continue
        run_one(job_id)


def start_workers() -> int:
    """Start JOB_WORKERS daemon threads (0 disables). Returns the number started."""
    if config.JOB_WORKERS < 1 or _threads:
        return 0
    _stop.clear()
    try:
        recover_interrupted()
    except Exception:  # noqa: BLE001
        logger.exception("Could not recover interrupted jobs")
    for i in range(config.JOB_WORKERS):
        t = threading.Thread(target=_worker_loop, name=f"job-worker-{i}", daemon=True)
        t.start()
        _threads.append(t)
    logger.info("Started %d job worker(s)", len(_threads))
    return len(_threads)


def stop_workers() -> None:
    """Ask workers to stop after their current job."""
    _stop.set()
    for t in _threads:
        t.join(timeout=2)
    _threads.clear()
