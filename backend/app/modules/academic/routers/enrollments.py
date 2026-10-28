# File Name: enrollments.py
# Description: API router for Enrollment & Restore endpoints strictly enforcing ACAD_ENROLLMENT_MANAGE permission (F-ACAD-03).
# Created At: 2026-07-23
# Created By: Tam Khang
# Updated At: 2026-10-29
# Updated By: Tam Khang

from uuid import UUID
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from models.models import User
from app.modules.auth.dependencies import require_perm, get_current_user
from app.modules.academic.schemas import EnrollmentCreate, EnrollmentOut, AcademicStatusEnum
from app.modules.academic.services.enrollment_service import EnrollmentService

router = APIRouter(prefix="/api/v1/classes", tags=["academic-enrollment"])


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
    Ghi danh học sinh vào lớp. Yêu cầu quyền ACAD_ENROLLMENT_MANAGE hoặc là Giáo viên phụ trách/chủ nhiệm lớp.
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

    return EnrollmentService.enroll_student(
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



@router.get(
    "/{class_id}/students",
    response_model=List[EnrollmentOut],
    dependencies=[Depends(require_perm("ACAD_ENROLLMENT_VIEW"))]
)
def list_students_in_class(
    class_id: UUID,
    status: Optional[AcademicStatusEnum] = Query(None, description="Lọc theo trạng thái (ACTIVE, INACTIVE, DRAFT, DELETED)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Liệt kê học sinh trong một lớp theo phân quyền dữ liệu và trạng thái. Yêu cầu quyền ACAD_ENROLLMENT_VIEW.
    """
    status_val = status.value if status else None
    return EnrollmentService.list_students_in_class(
        db=db, class_id=class_id, status_val=status_val, current_user=current_user
    )


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
    Khôi phục bản ghi ghi danh học sinh bị xóa mềm về ACTIVE (dành riêng cho Admin). Yêu cầu quyền ACAD_ENROLLMENT_MANAGE.
    """
    return EnrollmentService.restore_enrollment(db=db, class_id=class_id, student_id=student_id)
