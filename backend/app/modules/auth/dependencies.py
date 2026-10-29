# File Name: dependencies.py
# Description: FastAPI dependencies for user authentication and permission verification.
# Created At: 2026-07-17
# Created By: Tam Khang
# Updated At: 2026-07-17
# Updated By: Tam Khang

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from uuid import UUID

from app.core.security import SECRET_KEY, ALGORITHM
from app.core.database import get_db
from models.models import User, Role
from app.modules.auth.services.permission_service import PermissionService

# Configure OAuth2PasswordBearer, auto_error=False to allow custom error envelopes for missing tokens
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login", auto_error=False)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """
    Dependency to authenticate and return the current active user from the JWT token.
    Raises standardized HTTPExceptions for missing, invalid, or expired tokens, and blocked or inactive accounts.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "ERR-AUTH-MISSING_TOKEN",
                "message": "Authentication token required."
            }
        )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "ERR-AUTH-INVALID_TOKEN",
                    "message": "Invalid authentication token."
                }
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "ERR-AUTH-INVALID_TOKEN",
                "message": "Authentication token is invalid or expired."
            }
        )
    
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "ERR-AUTH-INVALID_TOKEN",
                "message": "Invalid authentication token."
            }
        )
        
    user = db.query(User).filter(User.user_id == user_uuid).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "ERR-AUTH-INVALID_TOKEN",
                "message": "User does not exist in the system."
            }
        )
        
    if user.status == "Blocked":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "ERR-AUTH-ACCOUNT_BLOCKED",
                "message": "Your account has been blocked."
            }
        )
    elif user.status == "Inactive":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "ERR-AUTH-ACCOUNT_INACTIVE",
                "message": "Account has not been activated."
            }
        )
        
    return user

def require_roles(*role_names: str):
    """
    Enforces that the current authenticated user holds one of the given roles (case-insensitive).
    Returns a callable dependency that yields the current user.
    """
    allowed = {name.lower() for name in role_names}

    def dependency(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> User:
        role = db.query(Role).filter(Role.role_id == user.role_id).first()
        if not role or role.name.lower() not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "ERR-AUTH-FORBIDDEN",
                    "message": "You do not have permission to access this resource."
                }
            )
        return user
    return dependency


def require_perm(permission_code: str):
    """
    Enforces that the current authenticated user has the specified permission_code in their effective permissions.
    Returns a callable dependency.
    """
    def dependency(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> None:
        effective_perms = PermissionService.get_effective_permissions(db, user.user_id, user.role_id)
        if permission_code not in effective_perms:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "ERR-AUTH-FORBIDDEN",
                    "message": "You do not have permission to access this resource."
                }
            )
    return dependency
