# File Name: users.py
# Description: API routers for Admin User Management (F-ADMIN-01).
# Created At: 2026-09-29
# Created By: Tam Khang
# Updated At: 2026-09-29
# Updated By: Tam Khang

import csv
import io
import math
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile, File, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.resource_limits import IMPORT_SEMAPHORE
from models.models import User, Role
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.services.permission_service import PermissionService
from app.modules.admin.schemas import (
    AdminUserListResponse,
    AdminUserCreateRequest,
    AdminUserCreateResponse,
    AdminUserUpdateRequest,
    AdminUserStatusUpdateRequest,
    AdminUserResetPasswordRequest,
    AdminUserResetPasswordResponse
)
from app.modules.admin.repository import AdminUserRepository
from app.modules.admin.services.user_service import AdminUserService
from app.modules.admin.services.user_import_service import UserImportService, MAX_IMPORT_BYTES

router = APIRouter(prefix="/api/v1/admin/users", tags=["admin-users"])


def require_admin_privilege(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> User:
    """
    Enforces that current user is an Administrator or possesses ADMIN_USER permissions.
    """
    role = db.query(Role).filter(Role.role_id == current_user.role_id).first()
    role_name = role.name.lower() if role else ""
    if role_name == "admin":
        return current_user

    effective_perms = PermissionService.get_effective_permissions(db, current_user.user_id, current_user.role_id)
    if "ADMIN_USER_VIEW" in effective_perms or "ADMIN_USER_MANAGE" in effective_perms:
        return current_user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={
            "code": "ERR-AUTH-FORBIDDEN",
            "message": "Administrative privileges required to access this endpoint."
        }
    )


@router.get("", response_model=AdminUserListResponse, dependencies=[Depends(require_admin_privilege)])
def list_users(
    page: int = Query(1, ge=1, description="Page index"),
    page_size: int = Query(10, ge=1, le=100, description="Page size"),
    search: Optional[str] = Query(None, description="Search keyword for name, phone, or email"),
    role: Optional[str] = Query(None, description="Role filter: all, student, teacher, admin"),
    status_filter: Optional[str] = Query(None, alias="status", description="Status filter: all, ACTIVE, INACTIVE, SUSPENDED, DELETED"),
    grade: Optional[str] = Query(None, description="Grade filter"),
    department: Optional[str] = Query(None, description="Department filter"),
    db: Session = Depends(get_db)
):
    """
    Retrieves paginated user list with multi-criteria filtering and searching.
    Excludes soft-deleted accounts by default unless explicitly specified.
    """
    items, total = AdminUserRepository.list_users(
        db=db,
        page=page,
        page_size=page_size,
        search=search,
        role=role,
        status=status_filter,
        grade=grade,
        department=department
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    return AdminUserListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.post("", response_model=AdminUserCreateResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin_privilege)])
def create_user(
    payload: AdminUserCreateRequest,
    db: Session = Depends(get_db)
):
    """
    Creates a new user account with strict field and age validations.
    Automatically generates a secure default password if omitted, hashes it,
    saves it to the database, and dispatches an SMS / system notification to the recipient.
    """
    return AdminUserService.create_user(db=db, payload=payload)


@router.get("/export-excel", dependencies=[Depends(require_admin_privilege)])
def export_users_csv(
    search: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    grade: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Exports user records to a UTF-8 CSV spreadsheet compatible with Microsoft Excel.
    """
    csv_content = AdminUserService.export_users_csv(
        db=db,
        search=search,
        role=role,
        status_val=status_filter,
        grade=grade,
        department=department
    )

    return Response(
        content=csv_content.encode("utf-8-sig"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=users_export.csv"}
    )


@router.get("/import-template", dependencies=[Depends(require_admin_privilege)])
def download_import_template(fmt: str = Query("xlsx", alias="format", pattern="^(xlsx|csv)$")):
    """Downloads a sample file (header + example rows) the admin fills in and imports."""
    if fmt == "csv":
        return Response(
            content=UserImportService.build_template_csv(),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": "attachment; filename=user_import_template.csv"},
        )
    return Response(
        content=UserImportService.build_template_xlsx(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=user_import_template.xlsx"},
    )


@router.post("/import-excel", dependencies=[Depends(require_admin_privilege)])
def import_users_excel(
    file: UploadFile = File(...),
    dry_run: bool = Query(False),
    db: Session = Depends(get_db)
):
    """
    Imports users from a .csv or .xlsx file (columns matched by header name).
    With dry_run=true rows are validated only. Plain ``def`` on purpose: parsing and per-row
    commits are synchronous; IMPORT_SEMAPHORE bounds concurrent imports.
    """
    contents = file.file.read(MAX_IMPORT_BYTES + 1)
    with IMPORT_SEMAPHORE:
        return UserImportService.import_users(db, file.filename or "", contents, dry_run=dry_run)


@router.get("/generate-code", dependencies=[Depends(require_admin_privilege)])
def generate_unique_code(
    role: str = Query("student", description="Role: student or teacher"),
    db: Session = Depends(get_db)
):
    """
    Generates a guaranteed unique identifier code (e.g. HS2024XXXX or GV2024XXXX).
    Checks database repeatedly until a completely unused code is found.
    """
    code = AdminUserService.generate_unique_code(db=db, role=role)
    return {"code": code}


@router.get("/check-code", dependencies=[Depends(require_admin_privilege)])
def check_code_availability(
    code: str = Query(..., description="Identifier code to verify"),
    db: Session = Depends(get_db)
):
    """
    Checks whether an identifier code already exists in the database.
    """
    exists = AdminUserRepository.check_code_exists(db, code.strip())
    return {"code": code.strip(), "exists": exists, "available": not exists}


@router.get("/{user_id}", dependencies=[Depends(require_admin_privilege)])
def get_user_detail(
    user_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Retrieves full profile details for a specific user.
    """
    items, _ = AdminUserRepository.list_users(db=db, page=1, page_size=10, search=None, status="all")
    for item in items:
        if item["id"] == user_id:
            return item

    user = AdminUserRepository.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ERR-ADMIN-USER_NOT_FOUND", "message": "User not found."}
        )

    role = db.query(Role).filter(Role.role_id == user.role_id).first()
    return {
        "id": user.user_id,
        "user_id": user.user_id,
        "full_name": user.full_name,
        "phone": user.phone,
        "email": user.email,
        "birthday": user.birthday,
        "role": role.name if role else "User",
        "role_key": role.name.lower() if role else "user",
        "status": user.status,
        "created_at": user.created_at,
        "updated_at": user.updated_at
    }


@router.put("/{user_id}", dependencies=[Depends(require_admin_privilege)])
def update_user(
    user_id: UUID,
    payload: AdminUserUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Updates profile details for an existing user account.
    """
    return AdminUserService.update_user(db=db, user_id=user_id, payload=payload, acting_user_id=current_user.user_id)


@router.patch("/{user_id}/status", dependencies=[Depends(require_admin_privilege)])
def update_user_status(
    user_id: UUID,
    payload: AdminUserStatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Updates user account status (e.g. ACTIVE, INACTIVE, SUSPENDED).
    """
    return AdminUserService.update_status(db=db, user_id=user_id, new_status=payload.status, reason=payload.reason, acting_user_id=current_user.user_id)


@router.delete("/{user_id}", dependencies=[Depends(require_admin_privilege)])
def delete_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Soft-deletes a user account by setting status to DELETED.
    Strictly prohibits hard-deleting records to protect historical data integrity.
    """
    return AdminUserService.soft_delete_user(db=db, user_id=user_id, acting_user_id=current_user.user_id)


@router.post("/{user_id}/restore", dependencies=[Depends(require_admin_privilege)])
def restore_user(
    user_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Restores a previously soft-deleted user account back to ACTIVE.
    """
    return AdminUserService.restore_user(db=db, user_id=user_id)


@router.post("/{user_id}/reset-password", response_model=AdminUserResetPasswordResponse, dependencies=[Depends(require_admin_privilege)])
def reset_user_password(
    user_id: UUID,
    payload: AdminUserResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Resets user password, generating a default password and dispatching via SMS / system notification.
    """
    return AdminUserService.reset_password(db=db, user_id=user_id, custom_password=payload.new_password)

