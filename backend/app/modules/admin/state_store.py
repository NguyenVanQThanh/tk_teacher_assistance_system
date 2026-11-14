# File Name: state_store.py
# Description: Shared PostgreSQL and SQLite compatible state persistence and audit event helpers backed by AuditLog.
# Created At: 2026-11-14
# Created By: Tam Khang
# Updated At: 2026-11-14
# Updated By: Tam Khang

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from models.models import AuditLog

logger = logging.getLogger(__name__)

INTERNAL_STATE_MARKER = "INTERNAL_STATE"


def _parse_json(raw: Optional[str]) -> Dict[str, Any]:
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {}
    except (ValueError, TypeError):
        return {}


def get_latest_state(db: Session, key_title: str) -> Optional[Dict[str, Any]]:
    """
    Fetch the latest active JSON payload persisted under an internal AuditLog key title.
    """
    row = (
        db.query(AuditLog)
        .filter(
            AuditLog.title == key_title,
            AuditLog.ip_address == INTERNAL_STATE_MARKER,
            func.upper(AuditLog.status) != "DELETED",
        )
        .order_by(AuditLog.created_at.desc())
        .first()
    )
    if not row:
        return None
    return _parse_json(row.description)


def upsert_state(
    db: Session,
    key_title: str,
    payload: Dict[str, Any],
    actor_name: str = "System",
) -> AuditLog:
    """
    Create or update an active internal JSON state record identified by key_title.
    """
    existing = (
        db.query(AuditLog)
        .filter(
            AuditLog.title == key_title,
            AuditLog.ip_address == INTERNAL_STATE_MARKER,
            func.upper(AuditLog.status) != "DELETED",
        )
        .order_by(AuditLog.created_at.desc())
        .first()
    )
    serialized = json.dumps(payload, ensure_ascii=False, default=str)
    if existing:
        existing.description = serialized
        existing.actor_name = actor_name
        db.commit()
        db.refresh(existing)
        return existing

    record = AuditLog(
        log_id=uuid.uuid4(),
        title=key_title,
        description=serialized,
        actor_name=actor_name,
        ip_address=INTERNAL_STATE_MARKER,
        severity="info",
        status="ACTIVE",
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def append_state_item(
    db: Session,
    key_title: str,
    payload: Dict[str, Any],
    actor_name: str = "System",
) -> Tuple[AuditLog, Dict[str, Any]]:
    """
    Append a new internal JSON state item (e.g., backup snapshot, report schedule, custom report).
    """
    log_id = uuid.uuid4()
    item_payload = dict(payload)
    item_payload.setdefault("id", str(log_id))
    item_payload.setdefault("createdAt", datetime.now(timezone.utc).isoformat())

    record = AuditLog(
        log_id=log_id,
        title=key_title,
        description=json.dumps(item_payload, ensure_ascii=False, default=str),
        actor_name=actor_name,
        ip_address=INTERNAL_STATE_MARKER,
        severity="info",
        status="ACTIVE",
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record, item_payload


def list_state_items(
    db: Session,
    key_title: str,
    prefix_match: bool = False,
) -> List[Tuple[AuditLog, Dict[str, Any]]]:
    """
    List active internal JSON state items matching key_title (exact or prefix).
    """
    query = db.query(AuditLog).filter(
        AuditLog.ip_address == INTERNAL_STATE_MARKER,
        func.upper(AuditLog.status) != "DELETED",
    )
    if prefix_match:
        # Escape LIKE wildcards so "_" in keys like "__CLASS_META__:" matches literally.
        escaped = key_title.replace("\\", "\\\\").replace("_", "\\_").replace("%", "\\%")
        query = query.filter(AuditLog.title.like(f"{escaped}%", escape="\\"))
    else:
        query = query.filter(AuditLog.title == key_title)

    rows = query.order_by(AuditLog.created_at.desc()).all()
    results: List[Tuple[AuditLog, Dict[str, Any]]] = []
    for row in rows:
        data = _parse_json(row.description)
        data.setdefault("id", str(row.log_id))
        results.append((row, data))
    return results


def get_state_by_log_id(
    db: Session,
    log_id: UUID,
    key_title: Optional[str] = None,
) -> Optional[Tuple[AuditLog, Dict[str, Any]]]:
    """
    Fetch an active internal JSON state record by log_id and optional key_title.
    """
    query = db.query(AuditLog).filter(
        AuditLog.log_id == log_id,
        AuditLog.ip_address == INTERNAL_STATE_MARKER,
        func.upper(AuditLog.status) != "DELETED",
    )
    if key_title:
        query = query.filter(AuditLog.title == key_title)

    row = query.first()
    if not row:
        return None
    data = _parse_json(row.description)
    data.setdefault("id", str(row.log_id))
    return row, data


def soft_delete_state(db: Session, log_id: UUID) -> bool:
    """
    Soft-delete an internal state record by marking status as DELETED.
    """
    row = (
        db.query(AuditLog)
        .filter(
            AuditLog.log_id == log_id,
            AuditLog.ip_address == INTERNAL_STATE_MARKER,
            func.upper(AuditLog.status) != "DELETED",
        )
        .first()
    )
    if not row:
        return False
    row.status = "DELETED"
    db.commit()
    return True


def record_audit_event(
    db: Session,
    title: str,
    description: str,
    actor_name: str,
    severity: str = "info",
    ip_address: Optional[str] = None,
) -> AuditLog:
    """
    Persist a user-visible administrative audit log entry.
    """
    entry = AuditLog(
        log_id=uuid.uuid4(),
        title=title,
        description=description,
        actor_name=actor_name,
        ip_address=ip_address,
        severity=severity,
        status="ACTIVE",
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
