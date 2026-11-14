# File Name: questions.py
# Description: API Router for Question management endpoints (F-EXE-01).
# Created At: 2026-07-31
# Created By: Tam Khang
# Updated At: 2026-08-04
# Updated By: Tam Khang

from uuid import UUID
from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from models.models import User
from app.modules.auth.dependencies import require_perm, get_current_user
from app.modules.exercise.schemas import QuestionImageUploadOut, QuestionUpdate, QuestionOut
from app.modules.exercise.services.question_image_service import QuestionImageService
from app.modules.exercise.services.question_service import QuestionService

router = APIRouter(prefix="/api/v1/questions", tags=["exercise-bank"])


def get_question_service(db: Session = Depends(get_db)) -> QuestionService:
    """Dependency provider for QuestionService."""
    return QuestionService(db)


@router.post(
    "/upload-image",
    response_model=QuestionImageUploadOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_perm("EXE_EXERCISE_MANAGE"))]
)
def upload_question_image(
    file: UploadFile = File(..., description="Image file attached to a question (png, jpg, gif, bmp, webp, svg)"),
    current_user: User = Depends(get_current_user),
):
    """
    Upload an image through the configured storage backend (local disk or Cloudflare R2).
    Returns the public URL plus metadata to persist on the question record.
    Requires EXE_EXERCISE_MANAGE permission.
    """
    return QuestionImageService.save_image(file)


@router.put(
    "/{question_id}",
    response_model=QuestionOut,
    dependencies=[Depends(require_perm("EXE_EXERCISE_MANAGE"))]
)
def update_question(
    question_id: UUID,
    payload: QuestionUpdate,
    service: QuestionService = Depends(get_question_service),
    current_user: User = Depends(get_current_user)
):
    """
    Update question content and answer options. Requires EXE_EXERCISE_MANAGE permission.
    """
    return service.update_question(current_user, question_id, payload)


@router.delete(
    "/{question_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_perm("EXE_EXERCISE_MANAGE"))]
)
def delete_question(
    question_id: UUID,
    service: QuestionService = Depends(get_question_service),
    current_user: User = Depends(get_current_user)
):
    """
    Soft-delete a question (sets status to DELETED). Requires EXE_EXERCISE_MANAGE permission.
    """
    service.delete_question(current_user, question_id)

