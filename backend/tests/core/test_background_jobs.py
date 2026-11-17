# File Name: test_background_jobs.py
# Description: Unit tests for the in-memory background job registry (ownership, ttl-free status flow).
# Created At: 2026-11-17
# Created By: AI Agent
# Updated At: 2026-11-17
# Updated By: AI Agent

import time
import uuid

from app.core import background_jobs as bj


class _FakeSession:
    def get(self, model, pk):
        return object()

    def close(self):
        pass


def _wait(job_id, user_id):
    for _ in range(100):
        job = bj.get_job(job_id, user_id)
        if job["status"] != "running":
            return job
        time.sleep(0.02)
    raise AssertionError("job did not finish")


def test_job_done_error_and_ownership(monkeypatch):
    monkeypatch.setattr(bj, "SessionLocal", _FakeSession)
    uid = uuid.uuid4()
    ok = bj.start_job(uid, lambda s, u: {"x": 1})
    assert _wait(ok["job_id"], uid) == {"status": "done", "result": {"x": 1}}

    def boom(s, u):
        raise ValueError("boom")

    bad = bj.start_job(uid, boom)
    assert _wait(bad["job_id"], uid)["http_status"] == 500

    assert bj.get_job(ok["job_id"], uuid.uuid4()) is None  # other users cannot read it
    assert bj.get_job("missing", uid) is None
