# File Name: test_notifications.py
# Description: Integration tests for the notification API, including cross-user authorization.
# Created At: 2026-11-15
# Created By: AI Agent
# Updated At: 2026-11-15
# Updated By: AI Agent

import uuid

from fastapi import status

from app.core.rate_limit import reset_login_failures
from app.modules.notification import service
from models.models import Notification, User

ADMIN, TEACHER = "0987654321", "0912345678"


def _login(client, phone):
    reset_login_failures(phone)
    r = client.post("/api/v1/auth/login", json={"phone": phone, "password": "password123"})
    assert r.status_code == status.HTTP_200_OK
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _uid(db, phone):
    return db.query(User).filter(User.phone == phone).one().user_id


def _seed(db, phone, n=3):
    uid = _uid(db, phone)
    for i in range(n):
        service.notify(db, [uid], "T", f"t{i}")
    db.commit()


def test_unauthenticated_rejected(client):
    assert client.get("/api/v1/notifications").status_code == status.HTTP_401_UNAUTHORIZED


def test_list_paginate_and_unread_count(client, db_session):
    _seed(db_session, ADMIN, 3)
    h = _login(client, ADMIN)
    r = client.get("/api/v1/notifications?page=1&page_size=2", headers=h).json()
    assert r["total"] == 3 and len(r["items"]) == 2
    assert client.get("/api/v1/notifications/unread-count", headers=h).json() == {"unread_count": 3}


def test_mark_read_and_read_all(client, db_session):
    _seed(db_session, ADMIN, 3)
    h = _login(client, ADMIN)
    first = client.get("/api/v1/notifications", headers=h).json()["items"][0]["notification_id"]
    assert client.post(f"/api/v1/notifications/{first}/read", headers=h).json()["is_read"] is True
    assert client.get("/api/v1/notifications/unread-count", headers=h).json()["unread_count"] == 2
    assert client.post("/api/v1/notifications/read-all", headers=h).json() == {"updated": 2}
    assert client.get("/api/v1/notifications/unread-count", headers=h).json()["unread_count"] == 0


def test_soft_delete_keeps_row(client, db_session):
    _seed(db_session, ADMIN, 1)
    h = _login(client, ADMIN)
    nid = client.get("/api/v1/notifications", headers=h).json()["items"][0]["notification_id"]
    assert client.delete(f"/api/v1/notifications/{nid}", headers=h).status_code == 204
    assert client.get("/api/v1/notifications", headers=h).json()["total"] == 0
    row = db_session.query(Notification).filter(Notification.notification_id == uuid.UUID(nid)).one()
    assert row.status == "DELETED"
    assert client.delete(f"/api/v1/notifications/{nid}", headers=h).status_code == 404


def test_cannot_touch_other_users_notifications(client, db_session):
    _seed(db_session, ADMIN, 2)
    admin_h = _login(client, ADMIN)
    nid = client.get("/api/v1/notifications", headers=admin_h).json()["items"][0]["notification_id"]
    t = _login(client, TEACHER)
    assert client.get("/api/v1/notifications", headers=t).json()["total"] == 0
    assert client.get("/api/v1/notifications/unread-count", headers=t).json()["unread_count"] == 0
    assert client.post(f"/api/v1/notifications/{nid}/read", headers=t).status_code == 404
    assert client.delete(f"/api/v1/notifications/{nid}", headers=t).status_code == 404
    assert client.post("/api/v1/notifications/read-all", headers=t).json() == {"updated": 0}
    # Admin data is untouched by the teacher's attempts.
    assert client.get("/api/v1/notifications/unread-count", headers=admin_h).json()["unread_count"] == 2


def test_notify_dedupes_and_rolls_back_with_caller(db_session):
    uid = _uid(db_session, ADMIN)
    assert service.notify(db_session, [uid, uid], "T", "x") == 1
    db_session.rollback()
    assert db_session.query(Notification).filter(Notification.user_id == uid).count() == 0
