# File Name: test_password.py
# Description: Integration tests for change password functionality and edge cases.
# Created At: 2026-07-17
# Created By: Tam Khang
# Updated At: 2026-07-17
# Updated By: Tam Khang

from fastapi import status
from fastapi.testclient import TestClient

def get_auth_headers(client: TestClient, phone: str, password: str) -> dict:
    """
    Helper to log in and get Authorization header.
    """
    response = client.post("/api/v1/auth/login", json={"phone": phone, "password": password})
    assert response.status_code == status.HTTP_200_OK
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_change_password_success(client: TestClient):
    """
    Test changing password successfully when old password is correct.
    """
    phone = "0912345678"  # Teacher user
    headers = get_auth_headers(client, phone, "password123")
    
    payload = {
        "old_password": "password123",
        "new_password": "newpassword456"
    }
    response = client.post("/api/v1/auth/change-password", json=payload, headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "ok"}
    
    # Verify that we can log in with the new password
    login_response = client.post("/api/v1/auth/login", json={"phone": phone, "password": "newpassword456"})
    assert login_response.status_code == status.HTTP_200_OK
    
    # Verify that the old password no longer works
    login_old_response = client.post("/api/v1/auth/login", json={"phone": phone, "password": "password123"})
    assert login_old_response.status_code == status.HTTP_401_UNAUTHORIZED

def test_change_password_wrong_old_password(client: TestClient):
    """
    Test changing password with incorrect old password.
    """
    phone = "0912345678"
    headers = get_auth_headers(client, phone, "password123")
    
    payload = {
        "old_password": "wrong_password",
        "new_password": "newpassword456"
    }
    response = client.post("/api/v1/auth/change-password", json=payload, headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"]["code"] == "ERR-AUTH-INVALID_CREDENTIALS"

def test_change_password_reuse(client: TestClient):
    """
    EC-07: Test changing password to the same as the old password.
    """
    phone = "0912345678"
    headers = get_auth_headers(client, phone, "password123")
    
    payload = {
        "old_password": "password123",
        "new_password": "password123"
    }
    response = client.post("/api/v1/auth/change-password", json=payload, headers=headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"]["code"] == "ERR-AUTH-PASSWORD_REUSE"
