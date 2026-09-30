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


@router.post("/import-excel", dependencies=[Depends(require_admin_privilege)])
async def import_users_excel(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Imports users from a CSV file with line-by-line validation.
    Generates default passwords and dispatches notifications for all valid entries.
    """
    contents = await file.read()
    try:
        decoded = contents.decode("utf-8-sig")
    except UnicodeDecodeError:
        decoded = contents.decode("latin-1")

    reader = csv.reader(io.StringIO(decoded))
    rows = list(reader)
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "ERR-ADMIN-EMPTY_FILE", "message": "Uploaded file is empty."}
        )

    # Expect header in row 0
    header = [h.strip().lower() for h in rows[0]]
    successful = 0
    errors = []

    for idx, row in enumerate(rows[1:], start=2):
        if not any(row):
            continue
        try:
            full_name = row[0].strip() if len(row) > 0 else ""
            role_name = row[1].strip() if len(row) > 1 else "Student"
            phone = row[2].strip() if len(row) > 2 else None
            email = row[3].strip() if len(row) > 3 else None

            payload = AdminUserCreateRequest(
                full_name=full_name,
                role=role_name,
                phone=phone,
                email=email,
                is_active_immediately=True
            )
            AdminUserService.create_user(db=db, payload=payload)
            successful += 1
        except Exception as e:
            errors.append({"row": idx, "error": str(e)})

    return {
        "total_processed": len(rows) - 1,
        "successful_count": successful,
        "errors": errors
    }


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
    db: Session = Depends(get_db)
):
    """
    Updates profile details for an existing user account.
    """
    return AdminUserService.update_user(db=db, user_id=user_id, payload=payload)


@router.patch("/{user_id}/status", dependencies=[Depends(require_admin_privilege)])
def update_user_status(
    user_id: UUID,
    payload: AdminUserStatusUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Updates user account status (e.g. ACTIVE, INACTIVE, SUSPENDED).
    """
    return AdminUserService.update_status(db=db, user_id=user_id, new_status=payload.status, reason=payload.reason)


@router.delete("/{user_id}", dependencies=[Depends(require_admin_privilege)])
def delete_user(
    user_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Soft-deletes a user account by setting status to DELETED.
    Strictly prohibits hard-deleting records to protect historical data integrity.
    """
    return AdminUserService.soft_delete_user(db=db, user_id=user_id)


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
