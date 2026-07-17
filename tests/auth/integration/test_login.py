# File Name: test_login.py
# Description: Integration tests for login endpoint, user authentication flow, and rate limiting.
# Created At: 2026-07-17
# Created By: Tam Khang
# Updated At: 2026-07-17
# Updated By: Tam Khang

import time
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.core.rate_limit import _failed_attempts

def test_login_success(client: TestClient):
    """
    Test successful login with correct phone and password.
    """
    payload = {
        "phone": "0987654321",
        "password": "password123"
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 600
    assert "user" in data
    
    user_info = data["user"]
    assert user_info["full_name"] == "Admin User"
    assert user_info["role"] == "Admin"
    assert user_info["email_masked"] == "a***@test.com"
    assert user_info["phone_masked"] == "0******321"

def test_login_wrong_password(client: TestClient):
    """
    Test login attempt with incorrect password.
    """
    payload = {
        "phone": "0987654321",
        "password": "wrong_password"
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    data = response.json()
    assert data["detail"]["code"] == "ERR-AUTH-INVALID_CREDENTIALS"
    assert "Tên đăng nhập hoặc mật khẩu không chính xác." in data["detail"]["message"]

def test_login_non_existent_phone(client: TestClient):
    """
    EC-01: Test login attempt with phone that does not exist.
    """
    payload = {
        "phone": "0999999999",
        "password": "password123"
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    data = response.json()
    # Should use identical error code and message to prevent user enumeration
    assert data["detail"]["code"] == "ERR-AUTH-INVALID_CREDENTIALS"
    assert "Tên đăng nhập hoặc mật khẩu không chính xác." in data["detail"]["message"]

def test_login_blocked_user(client: TestClient):
    """
    EC-02: Test login attempt with blocked user status.
    """
    payload = {
        "phone": "0987654322",
        "password": "password123"
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    
    data = response.json()
    assert data["detail"]["code"] == "ERR-AUTH-ACCOUNT_BLOCKED"
    assert "Tài khoản của bạn đã bị khóa." in data["detail"]["message"]

def test_login_inactive_user(client: TestClient):
    """
    Test login attempt with inactive user status.
    """
    payload = {
        "phone": "0987654323",
        "password": "password123"
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    
    data = response.json()
    assert data["detail"]["code"] == "ERR-AUTH-ACCOUNT_INACTIVE"
    assert "Tài khoản chưa được kích hoạt." in data["detail"]["message"]

def test_login_rate_limiting(client: TestClient):
    """
    EC-06: Test rate limiting on consecutive failed login attempts.
    """
    phone = "0912345678"  # Teacher phone
    payload = {
        "phone": phone,
        "password": "wrong_password"
    }
    
    # Reset internal attempts store before test
    _failed_attempts.pop(phone, None)
    
    # 1. Try 5 times with wrong password
    for i in range(5):
        response = client.post("/api/v1/auth/login", json=payload)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
    # 2. The 6th attempt should block the request with 429 Too Many Requests
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert "Retry-After" in response.headers
    
    data = response.json()
    assert data["detail"]["code"] == "ERR-AUTH-TOO_MANY_ATTEMPTS"
    assert "Quá số lần thử đăng nhập cho phép" in data["detail"]["message"]
    
    # Cleanup rate limit dict
    _failed_attempts.pop(phone, None)
