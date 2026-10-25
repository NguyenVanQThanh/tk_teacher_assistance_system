# File Name: test_security.py
# Description: Unit tests for password hashing and JWT token utility logic.
# Created At: 2026-07-17
# Created By: Tam Khang
# Updated At: 2026-07-17
# Updated By: Tam Khang

import uuid
from datetime import timedelta
from jose import jwt

from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    SECRET_KEY,
    ALGORITHM
)

def test_password_hashing():
    """
    Test password hash generation and verification.
    """
    plain_password = "secure_password_123"
    hashed = get_password_hash(plain_password)
    
    # 1. Hashed password should not be plain text
    assert hashed != plain_password
    assert len(hashed) > 0
    
    # 2. Hashing same password should be verifiable
    assert verify_password(plain_password, hashed) is True
    
    # 3. Wrong password should fail verification
    assert verify_password("wrong_password", hashed) is False

def test_jwt_token_creation_and_decoding():
    """
    Test access token generation and verify standard payload attributes.
    """
    user_id = uuid.uuid4()
    role = "Teacher"
    expires_delta = timedelta(minutes=5)
    
    # 1. Create token
    token = create_access_token(subject=user_id, role=role, expires_delta=expires_delta)
    assert isinstance(token, str)
    assert len(token) > 0
    
    # 2. Decode and check claims
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert payload.get("sub") == str(user_id)
    assert payload.get("role") == role
    assert payload.get("exp") is not None
