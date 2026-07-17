# File Name: test_rbac.py
# Description: Integration tests for RBAC, get_current_user dependencies, token validation, and overrides.
# Created At: 2026-07-17
# Created By: Tam Khang
# Updated At: 2026-07-17
# Updated By: Tam Khang

import uuid
from datetime import timedelta
from fastapi import status, Depends
from fastapi.testclient import TestClient
from jose import jwt

from app.main import app
from app.core.security import create_access_token, SECRET_KEY, ALGORITHM
from app.modules.auth.dependencies import require_perm

# Helper authentication function
def get_auth_headers_for_phone(client: TestClient, phone: str) -> dict:
    response = client.post("/api/v1/auth/login", json={"phone": phone, "password": "password123"})
    assert response.status_code == status.HTTP_200_OK
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

# Register a temporary endpoint to test custom permission enforcement
@app.get("/api/test-perm-manage", dependencies=[Depends(require_perm("AUTH_PERM_MANAGE"))])
def api_test_perm_manage():
    return {"status": "ok"}

def test_rbac_success_with_permission(client: TestClient):
    """
    Test that a user with proper role permissions can access a protected endpoint.
    """
    # Teacher user has AUTH_ME_VIEW permission
    headers = get_auth_headers_for_phone(client, "0912345678")
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["full_name"] == "Teacher User"

def test_rbac_fail_missing_permission(client: TestClient):
    """
    EC-05: Test that a user without permission is denied access (403 ERR-AUTH-FORBIDDEN).
    """
    # Student user (0934567890) does not have AUTH_PERM_MANAGE permission
    headers = get_auth_headers_for_phone(client, "0934567890")
    response = client.get("/api/test-perm-manage", headers=headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"]["code"] == "ERR-AUTH-FORBIDDEN"

def test_rbac_override_deny(client: TestClient):
    """
    EC-05b: Test override DENY (User role has permission, but user specifically denied -> 403 Forbidden).
    """
    # student_deny_user (0934567892) has Student role (which has AUTH_ME_VIEW) but is explicitly denied AUTH_ME_VIEW
    headers = get_auth_headers_for_phone(client, "0934567892")
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"]["code"] == "ERR-AUTH-FORBIDDEN"

def test_rbac_override_allow(client: TestClient):
    """
    EC-05c: Test override ALLOW (User role lacks permission, but user specifically allowed -> 200 OK).
    """
    # student_allow_user (0934567891) has Student role (lacks AUTH_PERM_MANAGE) but is explicitly allowed AUTH_PERM_MANAGE
    headers = get_auth_headers_for_phone(client, "0934567891")
    response = client.get("/api/test-perm-manage", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "ok"}

def test_rbac_missing_token(client: TestClient):
    """
    EC-08: Test call to protected endpoint without Authorization header (401 ERR-AUTH-MISSING_TOKEN).
    """
    response = client.get("/api/v1/auth/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"]["code"] == "ERR-AUTH-MISSING_TOKEN"

def test_rbac_expired_token(client: TestClient):
    """
    EC-03: Test call to protected endpoint with expired token (401 ERR-AUTH-INVALID_TOKEN).
    """
    # Generate a token that expired 5 minutes ago
    expired_token = create_access_token(
        subject=uuid.uuid4(),
        role="Student",
        expires_delta=timedelta(minutes=-5)
    )
    headers = {"Authorization": f"Bearer {expired_token}"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"]["code"] == "ERR-AUTH-INVALID_TOKEN"

def test_rbac_invalid_signature_token(client: TestClient):
    """
    EC-04: Test call to protected endpoint with tampered signature (401 ERR-AUTH-INVALID_TOKEN).
    """
    # Generate a valid token first
    valid_token = create_access_token(subject=uuid.uuid4(), role="Student")
    # Tamper with the token string (e.g. modify the signature part at the end)
    parts = valid_token.split(".")
    tampered_token = f"{parts[0]}.{parts[1]}.signatureisnowfakeandinvalid"
    
    headers = {"Authorization": f"Bearer {tampered_token}"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"]["code"] == "ERR-AUTH-INVALID_TOKEN"
