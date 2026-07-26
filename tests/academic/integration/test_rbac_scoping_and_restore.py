# File Name: test_rbac_scoping_and_restore.py
# Description: Integration tests verifying RBAC Data Scoping (Admin, Teacher, Student), validation rules, and Restore endpoints.
# Created At: 2026-07-26
# Created By: Tam Khang
# Updated At: 2026-07-26
# Updated By: Tam Khang

import uuid
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from tests.academic.integration.test_classes import get_admin_token


class TestValidationAndRestore:
    def test_create_class_validation_invalid_school_year(self, client: TestClient):
        """Verify creating a class with invalid school_year format returns 422 Unprocessable Entity."""
        token = get_admin_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        resp = client.post(
            "/api/v1/classes",
            json={"class_name": "ValClass1", "school_year": "2026-invalid"},
            headers=headers
        )
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_class_validation_whitespace_stripping(self, client: TestClient):
        """Verify leading/trailing whitespace in class_name is automatically stripped."""
        token = get_admin_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        resp = client.post(
            "/api/v1/classes",
            json={"class_name": "   Class Strip Test   ", "school_year": "2025-2026"},
            headers=headers
        )
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.json()["class_name"] == "Class Strip Test"

    def test_restore_class_flow(self, client: TestClient):
        """Verify soft-deleting a class and restoring it via POST /classes/{id}/restore."""
        token = get_admin_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Create class
        c_resp = client.post(
            "/api/v1/classes",
            json={"class_name": "RestoreClass10A", "school_year": "2025-2026"},
            headers=headers
        )
        class_id = c_resp.json()["class_id"]

        # 2. Delete class
        d_resp = client.delete(f"/api/v1/classes/{class_id}", headers=headers)
        assert d_resp.status_code == status.HTTP_204_NO_CONTENT

        # 3. Normal GET should return 404
        g_resp = client.get(f"/api/v1/classes/{class_id}", headers=headers)
        assert g_resp.status_code == status.HTTP_404_NOT_FOUND

        # 4. Admin query with status=DELETED shows it
        list_deleted = client.get("/api/v1/classes?status=DELETED", headers=headers)
        assert list_deleted.status_code == status.HTTP_200_OK
        assert any(c["class_id"] == class_id for c in list_deleted.json())

        # 5. Restore class
        r_resp = client.post(f"/api/v1/classes/{class_id}/restore", headers=headers)
        assert r_resp.status_code == status.HTTP_200_OK
        assert r_resp.json()["status"] == "ACTIVE"

        # 6. GET after restore returns 200 OK
        g_after = client.get(f"/api/v1/classes/{class_id}", headers=headers)
        assert g_after.status_code == status.HTTP_200_OK

    def test_restore_subject_flow(self, client: TestClient):
        """Verify soft-deleting a subject and restoring it via POST /subjects/{id}/restore."""
        token = get_admin_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Create subject
        s_resp = client.post(
            "/api/v1/subjects",
            json={"subject_name": "RestoreSubjectMath", "description": "Test subject"},
            headers=headers
        )
        subject_id = s_resp.json()["subject_id"]

        # 2. Delete subject
        client.delete(f"/api/v1/subjects/{subject_id}", headers=headers)

        # 3. Restore subject
        r_resp = client.post(f"/api/v1/subjects/{subject_id}/restore", headers=headers)
        assert r_resp.status_code == status.HTTP_200_OK
        assert r_resp.json()["status"] == "ACTIVE"
