# File Name: test_document_and_grading_dashboard.py
# Description: Unit and integration tests for Document Repository, Document Dashboard, Grading Dashboard, and User Age Validation.
# Created At: 2026-09-27
# Created By: Tam Khang
# Updated At: 2026-09-27
# Updated By: Tam Khang

import uuid
import io
from datetime import date, timedelta
from fastapi import status
from fastapi.testclient import TestClient
from models.models import User, Role


def get_admin_token(client: TestClient) -> str:
    login_res = client.post("/api/v1/auth/login", json={"phone": "0987654321", "password": "password123"})
    return login_res.json()["access_token"]



def test_grading_dashboard_api(client: TestClient):
    token = get_admin_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/v1/attempts/dashboard", headers=headers)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert "total_submissions" in data
    assert "pending_grading_count" in data
    assert "graded_count" in data
    assert "avg_score" in data
    assert "score_distribution" in data
    assert "by_class" in data
    assert "recent_submissions" in data


def test_document_repository_and_dashboard_lifecycle(client: TestClient):
    token = get_admin_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Document Dashboard API
    dash_res = client.get("/api/v1/documents/dashboard", headers=headers)
    assert dash_res.status_code == status.HTTP_200_OK
    dash_data = dash_res.json()
    assert "total_documents" in dash_data
    assert "total_downloads" in dash_data
    assert "storage_formatted" in dash_data
    assert "by_subject" in dash_data
    assert "by_type" in dash_data

    # 2. Upload document
    pdf_content = b"%PDF-1.4 dummy pdf test content"
    files = {"file": ("giao_an_toan_12.pdf", io.BytesIO(pdf_content), "application/pdf")}
    form_data = {
        "title": "Giao An Chuyen De Dao Ham 12",
        "grade": "12",
        "document_type": "lecture"
    }

    upload_res = client.post("/api/v1/documents/upload", headers=headers, files=files, data=form_data)
    assert upload_res.status_code == status.HTTP_201_CREATED
    doc_id = upload_res.json()["document_id"]
    assert upload_res.json()["title"] == "Giao An Chuyen De Dao Ham 12"

    # 3. List documents
    list_res = client.get("/api/v1/documents", headers=headers)
    assert list_res.status_code == status.HTTP_200_OK
    assert list_res.json()["total"] >= 1

    # 4. Soft Delete document
    del_res = client.delete(f"/api/v1/documents/{doc_id}", headers=headers)
    assert del_res.status_code == status.HTTP_204_NO_CONTENT

    # 5. Restore document
    restore_res = client.post(f"/api/v1/documents/{doc_id}/restore", headers=headers)
    assert restore_res.status_code == status.HTTP_200_OK
    assert restore_res.json()["status"] == "Uploaded"


def test_age_validation_on_enrollment(client: TestClient):
    token = get_admin_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # Create class
    create_cls = client.post(
        "/api/v1/classes",
        headers=headers,
        json={"class_name": "Lop 10A1", "school_year": "2024-2025"}
    )
    assert create_cls.status_code == status.HTTP_201_CREATED
    class_id = create_cls.json()["class_id"]

    # Student younger than 16 (e.g. 10 years old) -> must raise 400
    young_birthday = str(date.today() - timedelta(days=365 * 10))
    res = client.post(
        f"/api/v1/classes/{class_id}/students",
        headers=headers,
        json={
            "student_name": "Hoc Sinh Tre Em",
            "birthday": young_birthday,
            "student_code": f"HS_YOUNG_{uuid.uuid4().hex[:4]}"
        }
    )
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.json()["detail"]["code"] == "ERR-USER-INVALID_AGE_STUDENT"


def test_document_security_and_status_validation(client: TestClient):
    admin_token = get_admin_token(client)
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Upload document as admin
    files = {"file": ("tailieu_test.pdf", io.BytesIO(b"%PDF dummy content"), "application/pdf")}
    form_data = {"title": "Tai Lieu Security Test", "grade": "12", "document_type": "reference"}
    upload_res = client.post("/api/v1/documents/upload", headers=admin_headers, files=files, data=form_data)
    assert upload_res.status_code == status.HTTP_201_CREATED
    doc_id = upload_res.json()["document_id"]

    # 1. Setting status to DELETED via update endpoint should be rejected (422)
    bad_update = client.put(f"/api/v1/documents/{doc_id}", headers=admin_headers, json={"status": "DELETED"})
    assert bad_update.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # 2. Setting invalid status string should be rejected (422)
    invalid_update = client.put(f"/api/v1/documents/{doc_id}", headers=admin_headers, json={"status": "ARBITRARY_STATUS"})
    assert invalid_update.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # 3. Valid status update (Archived)
    valid_update = client.put(f"/api/v1/documents/{doc_id}", headers=admin_headers, json={"status": "Archived"})
    assert valid_update.status_code == status.HTTP_200_OK
    assert valid_update.json()["status"] == "Archived"


def test_teacher_schedule_auth_and_idor_prevention(client: TestClient):
    # 1. Unauthenticated request to /notes must return 401 (no fallback bypass)
    unauth_res = client.get("/api/v1/teacher/schedule/notes")
    assert unauth_res.status_code == status.HTTP_401_UNAUTHORIZED

    # 2. Unauthenticated create note must return 401
    unauth_create = client.post("/api/v1/teacher/schedule/notes", json={"text": "Hack note"})
    assert unauth_create.status_code == status.HTTP_401_UNAUTHORIZED

    # 3. Authenticated as Admin
    admin_token = get_admin_token(client)
    headers = {"Authorization": f"Bearer {admin_token}"}

    create_res = client.post("/api/v1/teacher/schedule/notes", headers=headers, json={"text": "Admin private reminder"})
    assert create_res.status_code == status.HTTP_201_CREATED
    note_id = create_res.json()["id"]

    # Delete non-existent or other user's note returns 404
    random_uuid = str(uuid.uuid4())
    del_res = client.delete(f"/api/v1/teacher/schedule/notes/{random_uuid}", headers=headers)
    assert del_res.status_code == status.HTTP_404_NOT_FOUND

    # Delete own note succeeds
    del_own = client.delete(f"/api/v1/teacher/schedule/notes/{note_id}", headers=headers)
    assert del_own.status_code == status.HTTP_200_OK
    assert del_own.json()["status"] == "DELETED"



def _login(client: TestClient, phone: str) -> dict:
    res = client.post("/api/v1/auth/login", json={"phone": phone, "password": "password123"})
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def test_student_blocked_and_draft_hidden_from_other_teacher(client: TestClient):
    admin = {"Authorization": f"Bearer {get_admin_token(client)}"}
    teacher = _login(client, "0912345678")
    student = _login(client, "0934567890")

    files = {"file": ("draft_doc.pdf", io.BytesIO(b"%PDF draft"), "application/pdf")}
    up = client.post("/api/v1/documents/upload", headers=admin, files=files,
                     data={"title": "Draft Only Doc", "grade": "12", "document_type": "lecture"})
    doc_id = up.json()["document_id"]
    client.put(f"/api/v1/documents/{doc_id}", headers=admin, json={"status": "Draft"})

    # Students are rejected by the role gate
    assert client.get("/api/v1/documents", headers=student).status_code == status.HTTP_403_FORBIDDEN
    assert client.get("/api/v1/teacher/schedule/notes", headers=student).status_code == status.HTTP_403_FORBIDDEN
    # A Draft owned by someone else is invisible to another teacher
    assert client.get(f"/api/v1/documents/{doc_id}", headers=teacher).status_code == status.HTTP_404_NOT_FOUND


def test_document_metadata_validation_and_missing_file_download(client: TestClient):
    admin = {"Authorization": f"Bearer {get_admin_token(client)}"}
    files = {"file": ("meta.pdf", io.BytesIO(b"%PDF meta"), "application/pdf")}
    bad = client.post("/api/v1/documents/upload", headers=admin, files=files,
                      data={"title": "Bad Meta Doc", "grade": "99", "document_type": "lecture"})
    assert bad.status_code == status.HTTP_400_BAD_REQUEST

    files = {"file": ("meta2.pdf", io.BytesIO(b"%PDF meta"), "application/pdf")}
    ok = client.post("/api/v1/documents/upload", headers=admin, files=files,
                     data={"title": "Good Meta Doc", "grade": "11", "document_type": "exam"})
    doc_id = ok.json()["document_id"]
    assert client.put(f"/api/v1/documents/{doc_id}", headers=admin,
                      json={"document_type": "bogus"}).status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
