# File Name: attempts.py
# Description: API Router for StudentExerciseAttempt endpoints (F-EXE-03).
# Created At: 2026-08-05
# Created By: Tam Khang
# Updated At: 2026-08-05
# Updated By: Tam Khang

from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from models.models import User
from app.modules.auth.dependencies import require_perm, get_current_user
from app.modules.exercise.schemas import (
    AttemptStartOut, AttemptSubmitRequest, AttemptOut
)
from app.modules.exercise.services.attempt_service import AttemptService

router = APIRouter(tags=["student-attempts"])


def get_attempt_service(db: Session = Depends(get_db)) -> AttemptService:
    """Dependency provider for AttemptService."""
    return AttemptService(db)


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
