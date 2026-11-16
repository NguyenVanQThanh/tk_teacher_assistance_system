# File Name: auth.py
# Description: Routers for authentication API endpoints including Login, Me, and Logout with effective permissions.
# Created At: 2026-07-17
# Created By: Tam Khang
# Updated At: 2026-11-15
# Updated By: AI Agent

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Request, status, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core import config as app_config
from app.core.database import get_db
from app.core.security import get_password_hash
from app.core.rate_limit import check_rate_limit, record_login_failure, reset_login_failures
from models.models import User, Role, StudentClass, Class, TeacherSubject, Subject
from app.modules.auth.schemas import (
    GuestRequest, LoginRequest, LoginResponse, UserProfileOut, ChangePasswordRequest, RegisterRequest, UserProfileUpdateRequest
)
from app.modules.admin.state_store import get_current_academic_year
from app.modules.auth.services.auth_service import AuthService
from app.modules.auth.services.password_service import PasswordService
from app.modules.auth.services.permission_service import PermissionService
from app.modules.auth.dependencies import get_current_user, require_perm

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

@router.post("/login", response_model=LoginResponse)
def login(request_data: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate user with phone number and password, then issue a JWT access token.
    """
    # 1. Check rate limit lockout status
    is_blocked, retry_after = check_rate_limit(request_data.phone)
    if is_blocked:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "code": "ERR-AUTH-TOO_MANY_ATTEMPTS",
                "message": f"Too many failed login attempts. Please try again in {retry_after} seconds."
            },
            headers={"Retry-After": str(retry_after)}
        )

    try:
        user = AuthService.authenticate_user(
            db=db,
            identifier=request_data.phone,
            password_plain=request_data.password
        )
    except HTTPException as e:
        # If credentials check failed, record it
        if isinstance(e.detail, dict) and e.detail.get("code") == "ERR-AUTH-INVALID_CREDENTIALS":
            record_login_failure(request_data.phone)
        raise e

    # 2. Login successful, reset rate limit failure counter
    reset_login_failures(request_data.phone)

    return AuthService.issue_access_token(db=db, user=user)

def _hash_guest_key(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()

@router.post("/guest", response_model=LoginResponse)
def guest_login(payload: GuestRequest, request: Request, db: Session = Depends(get_db)):
    """
    Create or resume a guest account (a real users row with is_guest=true) and issue a token.
    A matching ACTIVE guest_key of the same role resumes the account (response guest_key is null);
    otherwise a new guest is created, rate limited per client IP, and guest_key is returned once.
    """
    from app.modules.admin.services.user_service import AdminUserService

    AdminUserService.reject_admin_role(payload.role)
    if not app_config.GUEST_ACCESS_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "ERR-AUTH-GUEST_DISABLED", "message": "Guest access is disabled."},
        )
    role = db.query(Role).filter(Role.name == payload.role).first()
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ERR-AUTH-ROLE_NOT_FOUND", "message": "Role not found."},
        )

    if payload.guest_key:
        existing = db.query(User).filter(
            User.guest_key_hash == _hash_guest_key(payload.guest_key),
            User.is_guest.is_(True), User.role_id == role.role_id, User.status == "ACTIVE",
        ).first()
        if existing is not None:
            return AuthService.issue_access_token(db=db, user=existing)

    ip = app_config.client_ip(request)
    if db.get_bind().dialect.name == "postgresql":
        # Serialize count-then-insert per IP so concurrent requests cannot exceed the hourly cap.
        # The transaction-scoped lock is released by the commit/rollback below.
        db.execute(text("SELECT pg_advisory_xact_lock(hashtext(:k))"), {"k": "guest_create:" + ip})
    since = datetime.now(timezone.utc) - timedelta(hours=1)
    created = db.query(User).filter(
        User.is_guest.is_(True), User.guest_ip == ip, User.created_at >= since).count()
    total_recent = db.query(User).filter(User.is_guest.is_(True), User.created_at >= since).count()
    if created >= app_config.GUEST_CREATE_PER_IP_HOUR or total_recent >= app_config.GUEST_CREATE_GLOBAL_HOUR:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"code": "ERR-AUTH-GUEST_RATE_LIMITED",
                    "message": "Too many guest accounts created from this address. Please try again later."},
            headers={"Retry-After": "3600"},
        )

    guest_key = secrets.token_urlsafe(32)
    guest = User(
        user_id=uuid.uuid4(),
        phone="guest_" + secrets.token_hex(6),
        # Random discarded secret: nobody knows it, so password login is impossible.
        password_hash=get_password_hash(secrets.token_urlsafe(32)),
        full_name="Khách",
        role_id=role.role_id,
        status="ACTIVE",
        is_guest=True,
        guest_key_hash=_hash_guest_key(guest_key),
        guest_ip=ip,
    )
    db.add(guest)
    db.flush()
    db.commit()
    db.refresh(guest)
    response = AuthService.issue_access_token(db=db, user=guest)
    response.guest_key = guest_key
    return response

@router.get("/me", response_model=UserProfileOut, dependencies=[Depends(require_perm("AUTH_ME_VIEW"))])
def get_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Retrieve the current authenticated user profile including student enrollment code, class, and teacher subjects.
    Requires AUTH_ME_VIEW permission.
    """
    role = db.query(Role).filter(Role.role_id == current_user.role_id).first()
    role_name = role.name if role else "User"

    student_code = None
    class_id = None
    class_name = None
    teaching_subjects = None

    if role_name == "Student":
        sc = db.query(StudentClass, Class).join(
            Class, StudentClass.class_id == Class.class_id
        ).filter(
            StudentClass.student_id == current_user.user_id,
            StudentClass.status != "DELETED"
        ).first()
        if sc:
            student_class_record, class_record = sc
            student_code = student_class_record.student_code
            class_id = class_record.class_id
            class_name = class_record.class_name
    elif role_name in ["Teacher", "HomeroomTeacher"]:
        ts_records = db.query(Subject.subject_name).join(
            TeacherSubject, TeacherSubject.subject_id == Subject.subject_id
        ).filter(
            TeacherSubject.teacher_id == current_user.user_id,
            TeacherSubject.status != "DELETED"
        ).distinct().all()
        teaching_subjects = [row[0] for row in ts_records]

    perms = list(PermissionService.get_effective_permissions(db, current_user.user_id, current_user.role_id))
    return UserProfileOut(
        user_id=current_user.user_id,
        full_name=current_user.full_name,
        role=role_name,
        email=current_user.email,
        phone=current_user.phone,
        status=current_user.status,
        student_code=student_code,
        class_id=class_id,
        class_name=class_name,
        teaching_subjects=teaching_subjects,
        permissions=perms,
        is_guest=bool(current_user.is_guest),
        current_academic_year=get_current_academic_year(db),
    )

@router.put("/profile", response_model=UserProfileOut, dependencies=[Depends(require_perm("AUTH_ME_VIEW"))])
def update_profile(
    payload: UserProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update personal profile information for current authenticated user.
    """
    if payload.full_name:
        current_user.full_name = payload.full_name  # already NFC-normalized by the schema
    if payload.email is not None:
        current_user.email = payload.email.strip() if payload.email else None
    if payload.phone:
        current_user.phone = payload.phone.strip()
    
    db.commit()
    db.refresh(current_user)
    return get_me(current_user=current_user, db=db)

@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    """
    Stateless logout endpoint.
    The client is responsible for discarding the token.
    """
    return {"status": "ok"}

@router.post("/change-password", dependencies=[Depends(require_perm("AUTH_PASSWORD_CHANGE"))])
def change_password(
    request_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change password for the current authenticated user.
    Requires AUTH_PASSWORD_CHANGE permission.
    """
    PasswordService.change_password(
        db=db,
        user=current_user,
        old_password=request_data.old_password,
        new_password=request_data.new_password
    )
    return {"status": "ok"}

@router.post("/register")
def register(request_data: RegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new user.
    """
    try:
        user = AuthService.create_user(
            db=db,
            full_name=request_data.full_name,
            phone=request_data.phone,
            password_plain=request_data.password
        )
    except HTTPException as e:
        # If email/phone already exists, record it
        if isinstance(e.detail, dict) and e.detail.get("code") == "ERR-AUTH-DUPLICATE_FIELD":
            record_login_failure(request_data.phone)
        raise e

    return {"status": "ok"}