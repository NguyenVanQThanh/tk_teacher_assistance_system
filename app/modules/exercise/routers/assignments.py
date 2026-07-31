# File Name: assignments.py
# Description: API Router for ClassAssignment endpoints (F-EXE-02).
# Created At: 2026-07-31
# Created By: Tam Khang
# Updated At: 2026-07-31
# Updated By: Tam Khang

from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from models.models import User
from app.modules.auth.dependencies import require_perm, get_current_user
from app.modules.exercise.schemas import AssignmentCreate, AssignmentOut
from app.modules.exercise.services.assignment_service import AssignmentService

router = APIRouter(tags=["class-assignments"])


@router.post(
    "/api/v1/classes/{class_id}/assignments",
    response_model=AssignmentOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_perm("EXE_ASSIGNMENT_MANAGE"))]
)
def create_class_assignment(
    class_id: UUID,
    payload: AssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Giao đề bài tập cho lớp học. Yêu cầu quyền EXE_ASSIGNMENT_MANAGE.
    """
    service = AssignmentService(db)
    return service.create_assignment(class_id, payload, current_user)


@router.get(
    "/api/v1/classes/{class_id}/assignments",
    response_model=List[AssignmentOut],
    dependencies=[Depends(require_perm("EXE_ASSIGNMENT_VIEW"))]
)
def list_class_assignments(
    class_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Xem danh sách bài tập được giao của lớp. Yêu cầu quyền EXE_ASSIGNMENT_VIEW.
    """
    service = AssignmentService(db)
    return service.list_class_assignments(class_id, current_user)


@router.delete(
    "/api/v1/assignments/{assignment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_perm("EXE_ASSIGNMENT_MANAGE"))]
)
def delete_class_assignment(
    assignment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Hủy giao bài tập (Soft Delete). Yêu cầu quyền EXE_ASSIGNMENT_MANAGE.
    """
    service = AssignmentService(db)
    service.delete_assignment(assignment_id, current_user)


@router.post(
    "/api/v1/assignments/{assignment_id}/restore",
    response_model=AssignmentOut,
    dependencies=[Depends(require_perm("EXE_ASSIGNMENT_MANAGE"))]
)
def restore_class_assignment(
    assignment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Khôi phục lượt giao bài tập đã bị hủy (Soft Delete). Yêu cầu quyền EXE_ASSIGNMENT_MANAGE.
    """
    service = AssignmentService(db)
    return service.restore_assignment(assignment_id, current_user)
