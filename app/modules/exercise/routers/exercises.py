# File Name: exercises.py
# Description: API Router for Exercise endpoints (F-EXE-01).
# Created At: 2026-07-31
# Created By: Tam Khang
# Updated At: 2026-08-04
# Updated By: Tam Khang

from uuid import UUID
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from models.models import User
from app.modules.auth.dependencies import require_perm, get_current_user
from app.modules.exercise.schemas import (
    ExerciseCreate, ExerciseUpdate, ExerciseOut,
    QuestionCreate, QuestionOut
)
from app.modules.exercise.services.exercise_service import ExerciseService
from app.modules.exercise.services.question_service import QuestionService

router = APIRouter(prefix="/api/v1/exercises", tags=["exercise-bank"])


def get_exercise_service(db: Session = Depends(get_db)) -> ExerciseService:
    """Dependency provider for ExerciseService."""
    return ExerciseService(db)


def get_question_service(db: Session = Depends(get_db)) -> QuestionService:
    """Dependency provider for QuestionService."""
    return QuestionService(db)


@router.post(
    "",
    response_model=ExerciseOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_perm("EXE_EXERCISE_MANAGE"))]
)
def create_exercise(
    payload: ExerciseCreate,
    service: ExerciseService = Depends(get_exercise_service),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new exercise. Requires EXE_EXERCISE_MANAGE permission.
    """
    return service.create_exercise(current_user, payload)


@router.get(
    "",
    response_model=List[ExerciseOut],
    dependencies=[Depends(require_perm("EXE_EXERCISE_VIEW"))]
)
def list_exercises(
    subject_id: Optional[UUID] = Query(None, description="Filter by subject ID"),
    service: ExerciseService = Depends(get_exercise_service),
    current_user: User = Depends(get_current_user)
):
    """
    List exercises within the user's teaching scope. Requires EXE_EXERCISE_VIEW permission.
    """
    return service.list_exercises(current_user, subject_id=subject_id)


@router.get(
    "/{exercise_id}",
    response_model=ExerciseOut,
    dependencies=[Depends(require_perm("EXE_EXERCISE_VIEW"))]
)
def get_exercise_detail(
    exercise_id: UUID,
    service: ExerciseService = Depends(get_exercise_service),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve details of an exercise including its questions and options. Requires EXE_EXERCISE_VIEW permission.
    """
    return service.get_exercise_detail(current_user, exercise_id)


@router.put(
    "/{exercise_id}",
    response_model=ExerciseOut,
    dependencies=[Depends(require_perm("EXE_EXERCISE_MANAGE"))]
)
def update_exercise(
    exercise_id: UUID,
    payload: ExerciseUpdate,
    service: ExerciseService = Depends(get_exercise_service),
    current_user: User = Depends(get_current_user)
):
    """
    Update exercise title or AI metadata. Requires EXE_EXERCISE_MANAGE permission.
    """
    return service.update_exercise(current_user, exercise_id, payload)


@router.delete(
    "/{exercise_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_perm("EXE_EXERCISE_MANAGE"))]
)
def delete_exercise(
    exercise_id: UUID,
    service: ExerciseService = Depends(get_exercise_service),
    current_user: User = Depends(get_current_user)
):
    """
    Soft-delete an exercise (sets status to DELETED). Requires EXE_EXERCISE_MANAGE permission.
    """
    service.delete_exercise(current_user, exercise_id)


@router.post(
    "/{exercise_id}/restore",
    response_model=ExerciseOut,
    dependencies=[Depends(require_perm("EXE_EXERCISE_MANAGE"))]
)
def restore_exercise(
    exercise_id: UUID,
    service: ExerciseService = Depends(get_exercise_service),
    current_user: User = Depends(get_current_user)
):
    """
    Restore a soft-deleted exercise back to ACTIVE status. Requires EXE_EXERCISE_MANAGE permission.
    """
    return service.restore_exercise(current_user, exercise_id)


@router.post(
    "/{exercise_id}/questions",
    response_model=QuestionOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_perm("EXE_EXERCISE_MANAGE"))]
)
def add_question(
    exercise_id: UUID,
    payload: QuestionCreate,
    service: QuestionService = Depends(get_question_service),
    current_user: User = Depends(get_current_user)
):
    """
    Add a question (with answer options) to an exercise. Requires EXE_EXERCISE_MANAGE permission.
    """
    return service.add_question(current_user, exercise_id, payload)

