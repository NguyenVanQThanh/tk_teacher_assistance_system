# File Name: test_auth_flow.py
# Description: E2E test cases for complete user authentication flow.
# Created At: 2026-07-17
# Created By: Tam Khang
# Updated At: 2026-07-17
# Updated By: Tam Khang

from fastapi import status
from fastapi.testclient import TestClient

def test_complete_auth_flow(client: TestClient):
    """
    E2E: Test login -> get user info -> logout.
    """
    # 1. Login to retrieve the token
    payload = {
        "phone": "0912345678",
        "password": "password123"
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == status.HTTP_200_OK
    
    login_data = response.json()
    token = login_data["access_token"]
    assert len(token) > 0
    
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Access the protected /me endpoint with the token
    me_response = client.get("/api/v1/auth/me", headers=headers)
    assert me_response.status_code == status.HTTP_200_OK
    
    me_data = me_response.json()
    assert me_data["full_name"] == "Teacher User"
    assert me_data["role"] == "Teacher"
    assert me_data["phone"] == "0912345678"
    assert me_data["email"] == "teacher@test.com"

    # 3. Call the logout endpoint
    logout_response = client.post("/api/v1/auth/logout", headers=headers)
    assert logout_response.status_code == status.HTTP_200_OK
    assert logout_response.json() == {"status": "ok"}
