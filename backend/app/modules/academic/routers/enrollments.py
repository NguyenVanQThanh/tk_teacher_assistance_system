# File Name: enrollments.py
# Description: API router for Enrollment & Restore endpoints strictly enforcing ACAD_ENROLLMENT_MANAGE permission (F-ACAD-03).
# Created At: 2026-07-23
# Created By: Tam Khang
# Updated At: 2026-11-14
# Updated By: Tam Khang

from uuid import UUID
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from models.models import User
from app.modules.auth.dependencies import require_perm, get_current_user
from app.modules.academic.schemas import (
    AcademicStatusEnum,
    EnrollmentCreate,
    EnrollmentOut,
    StudentImportExcelResponse,
)
from app.modules.academic.services.enrollment_service import EnrollmentService

router = APIRouter(prefix="/api/v1/classes", tags=["academic-enrollment"])


def _ensure_enrollment_manage_access(db: Session, class_id: UUID, current_user: User) -> None:
    """
    Verify that current_user holds ACAD_ENROLLMENT_MANAGE permission or is the homeroom teacher of class_id.
    """
    from models.models import Class
    from app.modules.auth.services.permission_service import PermissionService

    cls = db.query(Class).filter(Class.class_id == class_id).first()
    if not cls:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ERR-ACAD-CLASS_NOT_FOUND", "message": "Class not found."}
        )

    perms = PermissionService.get_effective_permissions(db, current_user.user_id, current_user.role_id)
    has_perm = "ACAD_ENROLLMENT_MANAGE" in perms
    is_homeroom = cls.homeroom_teacher_id == current_user.user_id
    if not has_perm and not is_homeroom:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "ERR-AUTH-PERMISSION_DENIED", "message": "You do not have permission to enroll students into this class."}
        )


@router.post(
    "/{class_id}/students",
    response_model=EnrollmentOut,
    status_code=status.HTTP_201_CREATED
)
def enroll_student(
    class_id: UUID,
    payload: EnrollmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Enroll a student into a class. Requires ACAD_ENROLLMENT_MANAGE or homeroom teacher access.
    """
    _ensure_enrollment_manage_access(db, class_id, current_user)

    enrollment = EnrollmentService.enroll_student(
        db=db,
        class_id=class_id,
        student_id=payload.student_id,
        student_code=payload.student_code,
        status_val=payload.status.value,
        student_name=payload.student_name,
        birthday=payload.birthday,
        phone=payload.phone,
        gender=payload.gender
    )
    return EnrollmentService.enrich_enrollment_out(db, enrollment)


@router.post(
    "/{class_id}/students/import-excel",
    response_model=StudentImportExcelResponse
)
async def import_students_excel(
    class_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Bulk import and enroll students into a class from a CSV or XLSX upload.
    """
    from app.modules.admin.user_import import parse_tabular_upload

    _ensure_enrollment_manage_access(db, class_id, current_user)
    _, rows = await parse_tabular_upload(file)
    return EnrollmentService.import_students_from_rows(db=db, class_id=class_id, rows=rows)


@router.get(
    "/{class_id}/students",
    response_model=List[EnrollmentOut],
    dependencies=[Depends(require_perm("ACAD_ENROLLMENT_VIEW"))]
)
def list_students_in_class(
    class_id: UUID,
    status: Optional[AcademicStatusEnum] = Query(None, description="Filter by status (ACTIVE, INACTIVE, DRAFT, DELETED)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List students enrolled in a class with RBAC scoping and optional status filter.
    """
    status_val = status.value if status else None
    enrollments = EnrollmentService.list_students_in_class(
        db=db, class_id=class_id, status_val=status_val, current_user=current_user
    )
    return EnrollmentService.enrich_enrollments_out(db, enrollments)


@router.delete(
    "/{class_id}/students/{student_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_perm("ACAD_ENROLLMENT_MANAGE"))]
)
def unenroll_student(
    class_id: UUID,
    student_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Hủy ghi danh học sinh khỏi lớp (chuyển sang trạng thái DELETED). Yêu cầu quyền ACAD_ENROLLMENT_MANAGE.
    """
    EnrollmentService.unenroll_student(db=db, class_id=class_id, student_id=student_id)


@router.post(
    "/{class_id}/students/{student_id}/restore",
    response_model=EnrollmentOut,
    dependencies=[Depends(require_perm("ACAD_ENROLLMENT_MANAGE"))]
)
def restore_enrollment(
    class_id: UUID,
    student_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Restore a soft-deleted student enrollment record to ACTIVE status.
    """
    enrollment = EnrollmentService.restore_enrollment(db=db, class_id=class_id, student_id=student_id)
    return EnrollmentService.enrich_enrollment_out(db, enrollment)
