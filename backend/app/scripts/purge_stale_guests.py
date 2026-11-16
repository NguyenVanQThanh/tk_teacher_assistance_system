# File Name: purge_stale_guests.py
# Description: Soft-delete guest accounts older than N days (status=DELETED); rows are kept, never hard deleted.
# Created At: 2026-11-16
# Created By: AI Agent
# Updated At: 2026-11-16
# Updated By: AI Agent

"""Soft-delete stale guest accounts.

Usage (from backend/): python -m app.scripts.purge_stale_guests [days]   (default 30)

A guest key cannot resume a DELETED account, so the owner simply gets a fresh guest next time.
Per-account caps still count soft-deleted rows, so purging does not reset any quota.
"""

import sys
from datetime import datetime, timedelta, timezone

from app.core.database import SessionLocal
from models.models import User


def purge_stale_guests(db, days: int = 30) -> int:
    """Mark ACTIVE guests created more than `days` days ago as DELETED and return the count."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    rows = db.query(User).filter(
        User.is_guest.is_(True), User.status == "ACTIVE", User.created_at < cutoff).all()
    for user in rows:
        user.status = "DELETED"
    db.commit()
    return len(rows)


if __name__ == "__main__":
    session = SessionLocal()
    try:
        print(f"Soft-deleted stale guest accounts: {purge_stale_guests(session, int(sys.argv[1]) if len(sys.argv) > 1 else 30)}")
    finally:
        session.close()
