# File Name: teacher_assignments.py
# Description: API router for Teacher Assignment & Restore endpoints (F-ACAD-04).
# Created At: 2026-07-23
# Created By: Tam Khang
# Updated At: 2026-07-26
# Updated By: Tam Khang

from uuid import UUID
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from models.models import User
from app.modules.auth.dependencies import require_perm, get_current_user
from app.modules.academic.schemas import TeacherAssignmentCreate, TeacherAssignmentOut, AcademicStatusEnum
from app.modules.academic.services.teacher_assignment_service import TeacherAssignmentService

router = APIRouter(prefix="/api/v1/classes", tags=["academic-teacher-assignment"])


@router.post(
    "/{class_id}/teacher-subjects",
    response_model=TeacherAssignmentOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_perm("ACAD_TEACHER_ASSIGN_MANAGE"))]
)
def assign_teacher(
    class_id: UUID,
    payload: TeacherAssignmentCreate,
    db: Session = Depends(get_db)
):
    """
    Phân công giáo viên dạy môn học tại một lớp. Yêu cầu quyền ACAD_TEACHER_ASSIGN_MANAGE.
    """
    return TeacherAssignmentService.assign_teacher(
        db=db,
        class_id=class_id,
        teacher_id=payload.teacher_id,
        subject_id=payload.subject_id,
        status_val=payload.status.value
    )


@router.get(
    "/{class_id}/teacher-subjects",
    response_model=List[TeacherAssignmentOut],
    dependencies=[Depends(require_perm("ACAD_TEACHER_ASSIGN_VIEW"))]
)
def list_assignments_in_class(
    class_id: UUID,
    status: Optional[AcademicStatusEnum] = Query(None, description="Lọc theo trạng thái (ACTIVE, INACTIVE, DRAFT, DELETED)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Liệt kê các phân công giáo viên theo lớp và trạng thái với phân quyền dữ liệu. Yêu cầu quyền ACAD_TEACHER_ASSIGN_VIEW.
    """
    status_val = status.value if status else None
    return TeacherAssignmentService.list_assignments_in_class(
        db=db, class_id=class_id, status_val=status_val, current_user=current_user
    )


@router.delete(
    "/{class_id}/teacher-subjects/{teacher_id}/{subject_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_perm("ACAD_TEACHER_ASSIGN_MANAGE"))]
)
def unassign_teacher(
    class_id: UUID,
    teacher_id: UUID,
    subject_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Hủy phân công giáo viên (chuyển sang trạng thái DELETED). Yêu cầu quyền ACAD_TEACHER_ASSIGN_MANAGE.
    """
    TeacherAssignmentService.unassign_teacher(
        db=db,
        class_id=class_id,
        teacher_id=teacher_id,
        subject_id=subject_id
    )


@router.post(
    "/{class_id}/teacher-subjects/{teacher_id}/{subject_id}/restore",
    response_model=TeacherAssignmentOut,
    dependencies=[Depends(require_perm("ACAD_TEACHER_ASSIGN_MANAGE"))]
)
def restore_assignment(
    class_id: UUID,
    teacher_id: UUID,
    subject_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Khôi phục phân công giáo viên bị xóa mềm về ACTIVE (dành riêng cho Admin). Yêu cầu quyền ACAD_TEACHER_ASSIGN_MANAGE.
    """
    return TeacherAssignmentService.restore_assignment(
        db=db,
        class_id=class_id,
        teacher_id=teacher_id,
        subject_id=subject_id
    )
