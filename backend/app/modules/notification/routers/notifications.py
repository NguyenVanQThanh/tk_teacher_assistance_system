# File Name: notifications.py
# Description: Per-user notification API: list, unread count, mark read, soft delete.
# Created At: 2026-11-15
# Created By: AI Agent
# Updated At: 2026-11-15
# Updated By: AI Agent

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.notification import service
from models.models import User

router = APIRouter(prefix="/api/v1/notifications", tags=["Notifications"])

# Any authenticated user may use these endpoints; every query is scoped to the caller's user_id,
# so no extra permission code is needed.


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    notification_id: UUID
    type: str
    title: str
    body: Optional[str] = None
    link: Optional[str] = None
    is_read: bool
    created_at: datetime


class NotificationPage(BaseModel):
    items: List[NotificationOut]
    total: int
    page: int
    page_size: int


def _not_found() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"code": "ERR-NOTIFICATION-NOT_FOUND", "message": "Notification not found."},
    )


@router.get("", response_model=NotificationPage)
def list_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    unread_only: bool = False,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items, total = service.list_for_user(db, user.user_id, page, page_size, unread_only)
    return NotificationPage(items=items, total=total, page=page, page_size=page_size)


@router.get("/unread-count")
def get_unread_count(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return {"unread_count": service.unread_count(db, user.user_id)}


@router.post("/read-all")
def read_all(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return {"updated": service.mark_all_read(db, user.user_id)}


@router.post("/{notification_id}/read", response_model=NotificationOut)
def read_one(notification_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    n = service.mark_read(db, user.user_id, notification_id)
    if not n:
        raise _not_found()
    return n


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_one(notification_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Soft delete (status=DELETED); the row is kept."""
    if not service.soft_delete(db, user.user_id, notification_id):
        raise _not_found()
