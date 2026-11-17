"""
File Name: test_job_security.py
Description: Tests for job kind scoping, per-user queue cap and notification failure handling.
Created At: 2026-11-17
Created By: AI Agent
Updated At: 2026-11-17
Updated By: AI Agent
"""
import uuid

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core import background_jobs as bj
from models.models import User


@pytest.fixture(autouse=True)
def _jobs_use_test_connection(db_session, monkeypatch):
    monkeypatch.setattr(bj, "SessionLocal", lambda: Session(bind=db_session.get_bind(), join_transaction_mode="create_savepoint"))


def test_get_job_is_scoped_by_kind_and_payload(db_session):
    bj.register_handler("K_A", lambda s, u, p: 1, "A", "/a")
    bj.register_handler("K_B", lambda s, u, p: 1, "B", "/b")
    u = db_session.query(User).first()
    job = bj.enqueue(db_session, u.user_id, "K_A", {"exercise_id": "e1"})
    jid = str(job.job_id)
    assert bj.get_job(db_session, jid, u.user_id, kind="K_A") is not None
    assert bj.get_job(db_session, jid, u.user_id, kind="K_B") is None
    assert bj.get_job(db_session, jid, u.user_id, payload_match={"exercise_id": "e1"}) is not None
    assert bj.get_job(db_session, jid, u.user_id, payload_match={"exercise_id": "other"}) is None


def test_enqueue_caps_active_jobs_per_user(db_session):
    bj.register_handler("K_CAP", lambda s, u, p: 1, "C", "/c")
    u = db_session.query(User).first()
    for _ in range(bj.MAX_ACTIVE_PER_USER):
        bj.enqueue(db_session, u.user_id, "K_CAP", {})
    with pytest.raises(HTTPException) as exc:
        bj.enqueue(db_session, u.user_id, "K_CAP", {})
    assert exc.value.status_code == 429


def test_notification_failure_does_not_leave_job_running(db_session, monkeypatch):
    from app.modules.notification import service as notification_service
    bj.register_handler("K_NOTIF", lambda s, u, p: {"ok": 1}, "N", "/n")
    u = db_session.query(User).first()
    job = bj.enqueue(db_session, u.user_id, "K_NOTIF", {})
    monkeypatch.setattr(notification_service, "notify", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))
    bj.run_one(bj._claim(db_session))
    db_session.expire_all()
    pub = bj.get_job(db_session, str(job.job_id), u.user_id)
    assert pub["status"] == "done" and pub["result"] == {"ok": 1}
