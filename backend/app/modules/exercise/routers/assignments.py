# File Name: assignments.py
# Description: API Router for ClassAssignment endpoints (F-EXE-02) and student assignments feed.
# Created At: 2026-07-31
# Created By: Tam Khang
# Updated At: 2026-10-03
# Updated By: Tam Khang

from uuid import UUID
from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from models.models import User
from app.modules.auth.dependencies import require_perm, get_current_user
from app.modules.exercise.schemas import AssignmentCreate, AssignmentOut, AssignmentResultSummaryOut
from app.modules.exercise.services.assignment_service import AssignmentService

router = APIRouter(tags=["class-assignments"])


def get_assignment_service(db: Session = Depends(get_db)) -> AssignmentService:
    """Dependency provider for AssignmentService."""
    return AssignmentService(db)


@router.get(
    "/api/v1/assignments",
    response_model=List[AssignmentOut],
    dependencies=[Depends(require_perm("EXE_ASSIGNMENT_VIEW"))]
)
def list_assignments(
    tab: Optional[str] = Query(None, description="Filter by tab: 'active', 'overdue', 'completed'"),
    subject_id: Optional[UUID] = Query(None, description="Filter by subject ID"),
    search: Optional[str] = Query(None, description="Search exercises by title"),
    service: AssignmentService = Depends(get_assignment_service),
    current_user: User = Depends(get_current_user)
):
    """
    List assigned exercises scoped to the user's enrolled/accessible classes.
    Supports tab filtering (active, overdue, completed), subject filtering, and search by title.
    Requires EXE_ASSIGNMENT_VIEW permission.
    """
    return service.list_assignments_feed(
        current_user=current_user,
        tab=tab,
        subject_id=subject_id,
        search=search
    )


@router.post(
    "/api/v1/classes/{class_id}/assignments",
    response_model=AssignmentOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_perm("EXE_ASSIGNMENT_MANAGE"))]
)
def create_class_assignment(
    class_id: UUID,
    payload: AssignmentCreate,
    service: AssignmentService = Depends(get_assignment_service),
    current_user: User = Depends(get_current_user)
):
    """
    Assign an exercise to a class. Requires EXE_ASSIGNMENT_MANAGE permission.
    """
    return service.create_assignment(class_id, payload, current_user)


@router.get(
    "/api/v1/classes/{class_id}/assignments",
    response_model=List[AssignmentOut],
    dependencies=[Depends(require_perm("EXE_ASSIGNMENT_VIEW"))]
)
def list_class_assignments(
    class_id: UUID,
    service: AssignmentService = Depends(get_assignment_service),
    current_user: User = Depends(get_current_user)
):
    """
    List exercise assignments for a class. Requires EXE_ASSIGNMENT_VIEW permission.
    """
    return service.list_class_assignments(class_id, current_user)


@router.delete(
    "/api/v1/assignments/{assignment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_perm("EXE_ASSIGNMENT_MANAGE"))]
)
def delete_class_assignment(
    assignment_id: UUID,
    service: AssignmentService = Depends(get_assignment_service),
    current_user: User = Depends(get_current_user)
):
    """
    Cancel an assignment (Soft Delete). Requires EXE_ASSIGNMENT_MANAGE permission.
    """
    service.delete_assignment(assignment_id, current_user)


@router.post(
    "/api/v1/assignments/{assignment_id}/restore",
    response_model=AssignmentOut,
    dependencies=[Depends(require_perm("EXE_ASSIGNMENT_MANAGE"))]
)
def restore_class_assignment(
    assignment_id: UUID,
    service: AssignmentService = Depends(get_assignment_service),
    current_user: User = Depends(get_current_user)
):
    """
    Restore a cancelled assignment (Soft Delete). Requires EXE_ASSIGNMENT_MANAGE permission.
    """
    return service.restore_assignment(assignment_id, current_user)


@router.get(
    "/api/v1/assignments/{assignment_id}/result",
    response_model=AssignmentResultSummaryOut,
    dependencies=[Depends(require_perm("EXE_ASSIGNMENT_VIEW"))]
)
@router.get(
    "/api/v1/assignments/{assignment_id}/attempts-history",
    response_model=AssignmentResultSummaryOut,
    dependencies=[Depends(require_perm("EXE_ASSIGNMENT_VIEW"))]
)
def get_assignment_result(
    assignment_id: UUID,
    student_id: Optional[UUID] = Query(None, description="Optional student ID filter for teachers"),
    service: AssignmentService = Depends(get_assignment_service),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve assignment details, student attempt history, score, and cognitive level analytics.
    Requires EXE_ASSIGNMENT_VIEW permission.
    """
    return service.get_assignment_result_summary(
        assignment_id=assignment_id,
        current_user=current_user,
        student_id=student_id
    )

