# File Name: security.py
# Description: Security utilities including password hashing and JWT token management.
# Created At: 2026-07-16
# Created By: Tam Khang
# Updated At: 2026-07-16
# Updated By: Tam Khang

import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Any, Union
from jose import jwt
from passlib.context import CryptContext

# Configuration
SECRET_KEY = os.environ.get("SECRET_KEY", "super-secret-key-for-local-development-change-in-prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against the hashed password.
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.
    """
    return pwd_context.hash(password)

def create_access_token(subject: Union[str, Any], role: str, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token containing subject (user_id), role, and expiration time.
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "sub": str(subject),
        "role": role,
        "exp": expire
    }
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
