# File Name: sync_service.py
# Description: Lightweight data-version snapshot service. Computes per-table latest change timestamps
#              with func.max (no ORM object loading) so the FE can detect new/changed DB records.
#              Also provides a small in-process cache (2s TTL) for the X-Data-Version middleware.
# Created At: 2026-11-12
# Created By: AI Agent
# Updated At: 2026-11-12
# Updated By: AI Agent

import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from models.models import (
    Exercise, Question, AnswerOption, ClassAssignment,
    StudentExerciseAttempt, Subject, Class,
)

# Fallback version when every tracked table is empty (stable, so SSE does not fire on empty DB).
EPOCH_VERSION = "1970-01-01T00:00:00Z"

# In-process cache TTL for the version snapshot (keeps the middleware / version endpoint light).
CACHE_TTL_SECONDS = 2.0

_cache_lock = threading.Lock()
_cache: Dict[str, Any] = {"expires_at": 0.0, "payload": None}


def _normalize_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """Normalize a DB datetime (may be naive) to an aware UTC datetime."""
    if dt is None:
        return None
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt)
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _iso_utc(dt: Optional[datetime]) -> Optional[str]:
    """Format an aware UTC datetime as ISO8601 with a trailing Z."""
    if dt is None:
        return None
    return dt.isoformat().replace("+00:00", "Z")


class SyncService:
    """Computes the data-version snapshot from aggregate max() queries only (never loads rows)."""

    def __init__(self, db: Session):
        self.db = db

    def _max_ts(self, model, ts_columns: List[str]) -> Optional[datetime]:
        """
        max(coalesce(ts_columns...)) over ALL rows of a table.
        DELETED rows are deliberately INCLUDED: a soft delete bumps updated_at and is a real
        data change the FE must learn about (e.g. a cancelled assignment disappearing).
        """
        cols = [getattr(model, col) for col in ts_columns]
        # coalesce() needs >= 2 args on some dialects (e.g. SQLite) -> skip it for a single column.
        expr = func.coalesce(*cols) if len(cols) > 1 else cols[0]
        query = self.db.query(func.max(expr)).select_from(model)
        return query.scalar()

    def get_table_versions(self) -> Dict[str, Optional[datetime]]:
        """Latest change timestamp per tracked table (raw datetimes, may be naive)."""
        versions: Dict[str, Optional[datetime]] = {}
        versions["exercises"] = self._max_ts(Exercise, ["updated_at", "created_at"])
        versions["questions"] = self._max_ts(Question, ["updated_at", "created_at"])
        # answer_options has NO timestamp columns -> proxy with the parent question's timestamps
        # (options are always written together with a question create/update, which bumps
        # questions.updated_at). This is a documented limitation of the current schema.
        versions["answer_options"] = (
            self.db.query(func.max(func.coalesce(Question.updated_at, Question.created_at)))
            .select_from(AnswerOption)
            .join(Question, AnswerOption.question_id == Question.question_id)
            .scalar()
        )
        # class_assignments: assigned_at covers inserts; updated_at (added 2026-11-12) covers
        # ORM updates incl. soft delete/restore (cancelled assignments must bump the version).
        versions["class_assignments"] = self._max_ts(ClassAssignment, ["updated_at", "assigned_at"])
        versions["student_exercise_attempts"] = self._max_ts(StudentExerciseAttempt, ["updated_at", "created_at"])
        versions["subjects"] = self._max_ts(Subject, ["updated_at", "created_at"])
        versions["classes"] = self._max_ts(Class, ["updated_at", "created_at"])
        # student_class / teacher_subjects have no timestamp columns at all, so they are not
        # part of the version snapshot (enrollment changes surface via class_assignments/attempts).
        return versions

    def get_version_snapshot(self) -> Dict[str, Any]:
        """Return {"version": <ISO8601 UTC max>, "tables": {table: <ISO8601 UTC or null>}}."""
        raw = self.get_table_versions()
        tables: Dict[str, Optional[str]] = {}
        max_dt: Optional[datetime] = None
        for name, dt in raw.items():
            normalized = _normalize_utc(dt)
            tables[name] = _iso_utc(normalized)
            if normalized is not None and (max_dt is None or normalized > max_dt):
                max_dt = normalized
        version = _iso_utc(max_dt) if max_dt is not None else EPOCH_VERSION
        return {"version": version, "tables": tables}


def get_cached_version_snapshot(db: Optional[Session] = None) -> Dict[str, Any]:
    """
    Version snapshot with a process-wide 2s cache (so the middleware can stamp X-Data-Version on
    every GET without hammering the DB). If `db` is provided (e.g. the request session or a test
    override) it is used as-is and NOT closed; otherwise a short-lived SessionLocal is opened.
    """
    now = time.monotonic()
    with _cache_lock:
        cached = _cache["payload"]
        if cached is not None and now < _cache["expires_at"]:
            return cached

    own_session = db is None
    if own_session:
        from app.core.database import SessionLocal
        db = SessionLocal()
    try:
        payload = SyncService(db).get_version_snapshot()
    finally:
        if own_session:
            db.close()

    with _cache_lock:
        _cache["payload"] = payload
        _cache["expires_at"] = time.monotonic() + CACHE_TTL_SECONDS
    return payload
