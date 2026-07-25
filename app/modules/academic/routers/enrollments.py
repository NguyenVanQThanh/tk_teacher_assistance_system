# File Name: enrollments.py
# Description: API router for Enrollment endpoints (F-ACAD-03).
# Created At: 2026-07-23
# Created By: Tam Khang
# Updated At: 2026-07-25
# Updated By: Tam Khang

from uuid import UUID
from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.auth.dependencies import require_perm
from app.modules.academic.schemas import EnrollmentCreate, EnrollmentOut
from app.modules.academic.services.enrollment_service import EnrollmentService

router = APIRouter(prefix="/api/v1/classes", tags=["academic-enrollment"])


@router.post(
    "/{class_id}/students",
    response_model=EnrollmentOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_perm("ACAD_ENROLLMENT_MANAGE"))]
)
def enroll_student(
    class_id: UUID,
    payload: EnrollmentCreate,
    db: Session = Depends(get_db)
):
    """
    Ghi danh học sinh vào lớp. Yêu cầu quyền ACAD_ENROLLMENT_MANAGE.
    """
    return EnrollmentService.enroll_student(
        db=db,
        class_id=class_id,
        student_id=payload.student_id,
        student_code=payload.student_code
    )


@router.get(
    "/{class_id}/students",
    response_model=List[EnrollmentOut],
    dependencies=[Depends(require_perm("ACAD_ENROLLMENT_VIEW"))]
)
def list_students_in_class(
    class_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Liệt kê tất cả học sinh trong một lớp. Yêu cầu quyền ACAD_ENROLLMENT_VIEW.
    """
    return EnrollmentService.list_students_in_class(db=db, class_id=class_id)


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
    Hủy ghi danh học sinh khỏi lớp (xóa mềm). Yêu cầu quyền ACAD_ENROLLMENT_MANAGE.
    """
    EnrollmentService.unenroll_student(db=db, class_id=class_id, student_id=student_id)
