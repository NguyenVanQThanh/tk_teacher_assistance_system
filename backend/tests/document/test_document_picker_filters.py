# File Name: test_document_picker_filters.py
# Description: Tests for the document picker list filters (mine, ready_only) and the SGK image mount.
# Created At: 2026-11-11
# Created By: AI Agent
# Updated At: 2026-11-11
# Updated By: AI Agent

import io
import uuid

from fastapi.testclient import TestClient

from models.models import Document


def _login(client):
    r = client.post("/api/v1/auth/login", json={"phone": "0987654321", "password": "password123"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_ready_only_and_ingest_status(client: TestClient, db_session, monkeypatch):
    monkeypatch.setattr("app.modules.document.routers.documents.DocumentIngestService.ingest", lambda *a, **k: None)
    h = _login(client)
    files = {"file": ("a.pdf", io.BytesIO(b"%PDF-1.4 picker test"), "application/pdf")}
    up = client.post("/api/v1/documents/upload", headers=h, files=files,
                     data={"title": "Picker Doc", "grade": "12", "document_type": "lecture"})
    assert up.status_code == 201
    doc_id = up.json()["document_id"]
    assert up.json()["ingest_status"] == "PENDING"

    ready = client.get("/api/v1/documents?ready_only=true&mine=true", headers=h).json()
    assert doc_id not in [d["document_id"] for d in ready["items"]]

    db_session.query(Document).filter(Document.document_id == uuid.UUID(doc_id)).update({"ingest_status": "DONE"})
    db_session.commit()
    ready = client.get("/api/v1/documents?ready_only=true&mine=true", headers=h).json()
    item = next(d for d in ready["items"] if d["document_id"] == doc_id)
    assert item["ingest_status"] == "DONE"


def test_sgk_images_mount_is_read_only(client: TestClient):
    assert client.get("/sgk-images/nope.png").status_code == 404
    assert client.post("/sgk-images/nope.png").status_code in (404, 405)
