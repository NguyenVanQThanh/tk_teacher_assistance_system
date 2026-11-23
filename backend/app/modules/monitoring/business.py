# File Name: business.py
# Description: Persistent AI generation / OCR outcome tracking. record() writes one row (never raises);
#              counts() aggregates over a window in seconds, where 0 means all time.
# Created At: 2026-11-24
# Created By: AI Agent
# Updated At: 2026-11-24
# Updated By: AI Agent

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from sqlalchemy import case, func

from app.core.database import SessionLocal
from app.modules.monitoring.collector import BUSINESS_KINDS, collector
from models.models import BusinessEvent

logger = logging.getLogger("smartlms.monitoring.business")


def record(kind: str, ok: bool) -> None:
    """Count the event in memory (live view) and persist it (all-time view). Monitoring never breaks callers."""
    collector.record_event(kind, ok)
    if kind not in BUSINESS_KINDS:
        return
    db = SessionLocal()
    try:
        db.add(BusinessEvent(kind=kind, ok=bool(ok)))
        db.commit()
    except Exception:
        db.rollback()
        logger.warning("Failed to persist business event kind=%s", kind, exc_info=True)
    finally:
        db.close()


def counts(window_seconds: int) -> Optional[Dict[str, Dict[str, Any]]]:
    """Per-kind totals from the DB; window_seconds=0 is all time. None when the DB is unavailable."""
    db = SessionLocal()
    try:
        query = db.query(
            BusinessEvent.kind,
            func.count(BusinessEvent.event_id),
            func.coalesce(func.sum(case((BusinessEvent.ok.is_(True), 1), else_=0)), 0),
        )
        if window_seconds > 0:
            cutoff = datetime.now(timezone.utc) - timedelta(seconds=window_seconds)
            query = query.filter(BusinessEvent.created_at >= cutoff)
        rows = {kind: (int(total), int(success)) for kind, total, success in query.group_by(BusinessEvent.kind)}
    except Exception:
        logger.warning("Failed to read business event counts", exc_info=True)
        return None
    finally:
        db.close()
    out: Dict[str, Dict[str, Any]] = {}
    for kind in BUSINESS_KINDS:
        total, success = rows.get(kind, (0, 0))
        out[kind] = {
            "total": total, "success": success, "failed": total - success,
            "success_rate": round(success / total, 4) if total else 0.0,
        }
    return out
