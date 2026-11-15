# File Name: service.py
# Description: Notification creation and per-user queries. Every query is scoped by user_id.
# Created At: 2026-11-15
# Created By: AI Agent
# Updated At: 2026-11-15
# Updated By: AI Agent

import logging
from datetime import datetime, timezone
from typing import Iterable, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from models.models import Notification

logger = logging.getLogger("notification")


def notify(
    db: Session,
    user_ids: Iterable[UUID],
    type: str,
    title: str,
    body: Optional[str] = None,
    link: Optional[str] = None,
) -> int:
    """Stage notifications for the given users in the caller's transaction (flush, no commit).

    The caller owns the commit, so a rolled-back business action leaves no notification.
    Duplicate recipients are collapsed. Returns the number of rows staged.
    """
    unique = list(dict.fromkeys(user_ids))
    for uid in unique:
        db.add(Notification(user_id=uid, type=type, title=title, body=body, link=link))
    if unique:
        db.flush()
    return len(unique)


def _own(db: Session, user_id: UUID):
    return db.query(Notification).filter(
        Notification.user_id == user_id, Notification.status == "ACTIVE"
    )


def list_for_user(
    db: Session, user_id: UUID, page: int, page_size: int, unread_only: bool = False
) -> Tuple[List[Notification], int]:
    """Return one page of the user's active notifications (newest first) and the total count."""
    q = _own(db, user_id)
    if unread_only:
        q = q.filter(Notification.is_read.is_(False))
    total = q.count()
    items = (
        q.order_by(Notification.created_at.desc(), Notification.notification_id)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return items, total


def unread_count(db: Session, user_id: UUID) -> int:
    """Count the user's unread active notifications."""
    return _own(db, user_id).filter(Notification.is_read.is_(False)).count()


def _get_own(db: Session, user_id: UUID, notification_id: UUID) -> Optional[Notification]:
    return _own(db, user_id).filter(Notification.notification_id == notification_id).first()


def mark_read(db: Session, user_id: UUID, notification_id: UUID) -> Optional[Notification]:
    """Mark one own notification read. Returns None when it is not found or not owned."""
    n = _get_own(db, user_id, notification_id)
    if n and not n.is_read:
        n.is_read = True
        n.read_at = datetime.now(timezone.utc)
        db.commit()
    return n


def mark_all_read(db: Session, user_id: UUID) -> int:
    """Mark all of the user's unread notifications read. Returns the number updated."""
    count = _own(db, user_id).filter(Notification.is_read.is_(False)).update(
        {"is_read": True, "read_at": datetime.now(timezone.utc)}, synchronize_session=False
    )
    db.commit()
    return count


def soft_delete(db: Session, user_id: UUID, notification_id: UUID) -> bool:
    """Soft delete one own notification. Returns False when it is not found or not owned."""
    n = _get_own(db, user_id, notification_id)
    if not n:
        return False
    n.status = "DELETED"
    db.commit()
    return True
