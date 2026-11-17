"""
File Name: test_background_jobs.py
Description: Tests for the Postgres-backed job queue (enqueue, run, ETA, ownership, recovery, notification).
Created At: 2026-11-17
Created By: AI Agent
Updated At: 2026-11-17
Updated By: AI Agent
"""
from datetime import datetime, timedelta, timezone
import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core import background_jobs as bj
from models.models import BackgroundJob, Notification, User


@pytest.fixture(autouse=True)
def _jobs_use_test_connection(db_session, monkeypatch):
    """Workers open their own sessions; point them at the test transaction."""
    monkeypatch.setattr(bj, "SessionLocal", lambda: Session(bind=db_session.get_bind(), join_transaction_mode="create_savepoint"))


def _user(db):
    return db.query(User).first()


def test_run_ok_notifies_and_sets_eta(db_session, monkeypatch):
    bj.register_handler("T_OK", lambda s, u, p: {"x": p["n"] * 2}, "Test", "/t", 42)
    u = _user(db_session)
    job = bj.enqueue(db_session, u.user_id, "T_OK", {"n": 2})
    pub = bj.to_public(db_session, job)
    assert pub["status"] == "queued" and pub["queue_position"] >= 1 and pub["estimated_seconds"] == 42
    jid = bj._claim(db_session)
    bj.run_one(jid)
    db_session.expire_all()
    pub = bj.get_job(db_session, str(jid), u.user_id)
    assert pub["status"] == "done" and pub["result"] == {"x": 4} and pub["progress"] == 100
    assert db_session.query(Notification).filter_by(type="JOB_DONE").count() == 1


def test_failure_and_ownership(db_session):
    def boom(s, u, p):
        raise HTTPException(422, {"code": "ERR-X", "message": "m"})
    bj.register_handler("T_BAD", boom, "Test", "/t")
    u = _user(db_session)
    job = bj.enqueue(db_session, u.user_id, "T_BAD", {})
    bj.run_one(bj._claim(db_session))
    db_session.expire_all()
    pub = bj.get_job(db_session, str(job.job_id), u.user_id)
    assert pub["status"] == "error" and pub["http_status"] == 422
    assert bj.get_job(db_session, str(job.job_id), __import__("uuid").uuid4()) is None
    assert bj.get_job(db_session, "not-a-uuid", u.user_id) is None


def test_recover_interrupted(db_session):
    bj.register_handler("T_REC", lambda s, u, p: 1, "Test", "/t")
    u = _user(db_session)
    job = bj.enqueue(db_session, u.user_id, "T_REC", {})
    job.status, job.attempts = "RUNNING", 1
    db_session.commit()
    assert bj.recover_interrupted() == 0  # fresh heartbeat: a live job of another process is left alone
    job.updated_at = datetime.now(timezone.utc) - timedelta(seconds=bj.STALE_SECONDS + 5)
    db_session.commit()
    assert bj.recover_interrupted() == 1
    db_session.expire_all()
    assert db_session.get(BackgroundJob, job.job_id).status == "QUEUED"
    job.status, job.attempts = "RUNNING", bj.MAX_ATTEMPTS
    job.updated_at = datetime.now(timezone.utc) - timedelta(seconds=bj.STALE_SECONDS + 5)
    db_session.commit()
    bj.recover_interrupted()
    db_session.expire_all()
    assert db_session.get(BackgroundJob, job.job_id).status == "FAILED"


def test_finish_ignores_job_requeued_by_recovery(db_session):
    bj.register_handler("T_STALE", lambda s, u, p: 1, "Test", "/t")
    u = _user(db_session)
    job = bj.enqueue(db_session, u.user_id, "T_STALE", {})
    job.status, job.attempts = "QUEUED", 1  # recovered while the old worker still runs
    db_session.commit()
    bj._finish(job.job_id, True, {"x": 1}, attempt=1)
    db_session.expire_all()
    assert db_session.get(BackgroundJob, job.job_id).status == "QUEUED"


def test_hold_ownership_rejects_superseded_run(db_session):
    bj.register_handler("T_OWN", lambda s, u, p: 1, "Test", "/t")
    u = _user(db_session)
    job = bj.enqueue(db_session, u.user_id, "T_OWN", {})
    job.status, job.attempts = "RUNNING", 2
    db_session.commit()
    bj._local.job_id, bj._local.attempt = job.job_id, 2
    try:
        bj.hold_ownership(db_session)  # owner: passes
        bj._local.attempt = 1  # an older run
        with pytest.raises(HTTPException) as e:
            bj.hold_ownership(db_session)
        assert e.value.status_code == 409
    finally:
        bj._local.job_id = bj._local.attempt = None
