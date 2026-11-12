# File Name: attempts.py
# Description: API Router for StudentExerciseAttempt endpoints (F-EXE-03).
# Created At: 2026-08-05
# Created By: Tam Khang
# Updated At: 2026-11-12
# Updated By: AI Agent

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from models.models import User
from app.modules.auth.dependencies import require_perm, get_current_user
from app.modules.exercise.schemas import (
    AttemptStartOut, AttemptSubmitRequest, AttemptOut, AttemptListItemOut,
    AttemptGradeUpdateRequest, GradingDashboardOut, AnswerKeyUpdateRequest, RegradeOut,
    AssignmentResultSummaryOut, AssignmentTakingOut
)
from app.modules.exercise.services.attempt_service import AttemptService
from app.modules.exercise.services.assignment_service import AssignmentService
from app.modules.exercise.services.grading_report_service import build_csv, build_pdf

router = APIRouter(tags=["student-attempts"])


def get_attempt_service(db: Session = Depends(get_db)) -> AttemptService:
    """Dependency provider for AttemptService."""
    return AttemptService(db)


@router.get(
    "/api/v1/attempts/dashboard",
    response_model=GradingDashboardOut,
    dependencies=[Depends(require_perm("EXE_ATTEMPT_VIEW"))]
)
@router.get(
    "/api/v1/grading/dashboard",
    response_model=GradingDashboardOut,
    dependencies=[Depends(require_perm("EXE_ATTEMPT_VIEW"))]
)
def get_grading_dashboard(
    service: AttemptService = Depends(get_attempt_service),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve grading dashboard metrics, score distribution, and breakdown by class.
    Requires EXE_ATTEMPT_VIEW permission.
    """
    return service.get_grading_dashboard(current_user=current_user)


@router.post(
    "/api/v1/assignments/{assignment_id}/attempts",
    response_model=AttemptStartOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_perm("EXE_ATTEMPT_SUBMIT"))]
)
def start_attempt(
    assignment_id: UUID,
    service: AttemptService = Depends(get_attempt_service),
    current_user: User = Depends(get_current_user)
):
    """
    Start an exercise attempt for an assignment. Requires EXE_ATTEMPT_SUBMIT permission.
    """
    return service.start_attempt(assignment_id, current_user)


@router.get(
    "/api/v1/assignments/{assignment_id}/attempts",
    response_model=AssignmentResultSummaryOut,
    dependencies=[Depends(require_perm("EXE_ATTEMPT_VIEW"))]
)
def get_assignment_attempts_history(
    assignment_id: UUID,
    student_id: Optional[UUID] = Query(None, description="Optional student ID filter for teachers"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve assignment details and all student attempts history with cognitive breakdown.
    Requires EXE_ATTEMPT_VIEW permission.
    """
    assignment_service = AssignmentService(db)
    return assignment_service.get_assignment_result_summary(
        assignment_id=assignment_id,
        current_user=current_user,
        student_id=student_id
    )


@router.put(
    "/api/v1/attempts/{attempt_id}/submit",
    response_model=AttemptOut,
    dependencies=[Depends(require_perm("EXE_ATTEMPT_SUBMIT"))]
)
def submit_attempt(
    attempt_id: UUID,
    payload: AttemptSubmitRequest,
    service: AttemptService = Depends(get_attempt_service),
    current_user: User = Depends(get_current_user)
):
    """
    Submit an exercise attempt and trigger auto-grading. Requires EXE_ATTEMPT_SUBMIT permission.
    """
    return service.submit_attempt(attempt_id, payload, current_user)


@router.get(
    "/api/v1/attempts",
    response_model=List[AttemptListItemOut],
    dependencies=[Depends(require_perm("EXE_ATTEMPT_VIEW"))]
)
def list_attempts(
    class_id: Optional[UUID] = Query(None, description="Filter by class ID"),
    assignment_id: Optional[UUID] = Query(None, description="Filter by assignment ID"),
    student_id: Optional[UUID] = Query(None, description="Filter by student ID (teacher/admin only)"),
    is_finished: Optional[bool] = Query(None, description="Filter by completion status"),
    search: Optional[str] = Query(None, description="Search by student name or phone"),
    service: AttemptService = Depends(get_attempt_service),
    current_user: User = Depends(get_current_user)
):
    """
    List exercise attempts/submissions with role-based scoping.
    Requires EXE_ATTEMPT_VIEW permission.
    """
    return service.list_attempts(
        current_user=current_user,
        class_id=class_id,
        assignment_id=assignment_id,
        is_finished=is_finished,
        search=search
    )


@router.get(
    "/api/v1/attempts/export",
    dependencies=[Depends(require_perm("EXE_ATTEMPT_VIEW"))]
)
def export_attempts_report(
    format: str = Query("csv", pattern="^(csv|pdf)$", description="Report format: csv or pdf"),
    class_id: Optional[UUID] = Query(None),
    assignment_id: Optional[UUID] = Query(None),
    student_id: Optional[UUID] = Query(None, description="Optional student ID filter (ignored for Student role: always scoped to the caller)"),
    is_finished: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    service: AttemptService = Depends(get_attempt_service),
    current_user: User = Depends(get_current_user)
):
    """Export grading results (same role scoping and filters as the attempts list) as CSV or PDF.
    Student role is always scoped to the caller's own attempts regardless of student_id."""
    items = service.list_attempts(
        current_user=current_user, class_id=class_id, assignment_id=assignment_id,
        student_id=student_id, is_finished=is_finished, search=search
    )
    if format == "pdf":
        return Response(build_pdf(items), media_type="application/pdf",
                        headers={"Content-Disposition": 'attachment; filename="grading_report.pdf"'})
    return Response(build_csv(items), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": 'attachment; filename="grading_report.csv"'})

@router.get(
    "/api/v1/attempts/{attempt_id}/paper",
    response_model=AssignmentTakingOut,
    dependencies=[Depends(require_perm("EXE_ATTEMPT_SUBMIT"))]
)
def get_attempt_paper(
    attempt_id: UUID,
    service: AttemptService = Depends(get_attempt_service),
    current_user: User = Depends(get_current_user)
):
    """
    Return the sanitized paper (questions without answer key) of an attempt owned by the current
    student. Only the attempt owner may access it. Requires EXE_ATTEMPT_SUBMIT permission.
    """
    return service.get_attempt_paper(attempt_id, current_user)


@router.get(
    "/api/v1/attempts/{attempt_id}",
    response_model=AttemptOut,
    dependencies=[Depends(require_perm("EXE_ATTEMPT_VIEW"))]
)
def get_attempt(
    attempt_id: UUID,
    service: AttemptService = Depends(get_attempt_service),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve attempt result details. Requires EXE_ATTEMPT_VIEW permission.
    """
    return service.get_attempt(attempt_id, current_user)


@router.put(
    "/api/v1/attempts/{attempt_id}/grade",
    response_model=AttemptOut,
    dependencies=[Depends(require_perm("EXE_ASSIGNMENT_MANAGE"))]
)
def update_attempt_grade(
    attempt_id: UUID,
    payload: AttemptGradeUpdateRequest,
    service: AttemptService = Depends(get_attempt_service),
    current_user: User = Depends(get_current_user)
):
    """
    Update teacher score adjustment and feedback notes for an attempt.
    Requires EXE_ASSIGNMENT_MANAGE permission.
    """
    return service.update_attempt_grade(attempt_id, payload, current_user)

@router.put(
    "/api/v1/exercises/{exercise_id}/answer-key",
    response_model=RegradeOut,
    dependencies=[Depends(require_perm("EXE_ASSIGNMENT_MANAGE"))]
)
def update_answer_key(
    exercise_id: UUID,
    payload: AnswerKeyUpdateRequest,
    service: AttemptService = Depends(get_attempt_service),
    current_user: User = Depends(get_current_user)
):
    """
    Save a new answer key and recompute + persist scores of every submission of the exercise.
    Requires EXE_ASSIGNMENT_MANAGE permission.
    """
    return service.update_answer_key_and_regrade(exercise_id, payload.keys, current_user)
