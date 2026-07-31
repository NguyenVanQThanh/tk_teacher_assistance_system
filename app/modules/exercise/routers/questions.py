# File Name: questions.py
# Description: API Router for Question management endpoints (F-EXE-01).
# Created At: 2026-07-31
# Created By: Tam Khang
# Updated At: 2026-07-31
# Updated By: Tam Khang

from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from models.models import User
from app.modules.auth.dependencies import require_perm, get_current_user
from app.modules.exercise.schemas import QuestionUpdate, QuestionOut
from app.modules.exercise.services.question_service import QuestionService

router = APIRouter(prefix="/api/v1/questions", tags=["exercise-bank"])


@router.put(
    "/{question_id}",
    response_model=QuestionOut,
    dependencies=[Depends(require_perm("EXE_EXERCISE_MANAGE"))]
)
def update_question(
    question_id: UUID,
    payload: QuestionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Cập nhật câu hỏi (+ đáp án trắc nghiệm). Yêu cầu quyền EXE_EXERCISE_MANAGE.
    """
    service = QuestionService(db)
    return service.update_question(current_user, question_id, payload)


@router.delete(
    "/{question_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_perm("EXE_EXERCISE_MANAGE"))]
)
def delete_question(
    question_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Xóa mềm câu hỏi (chuyển status sang DELETED). Yêu cầu quyền EXE_EXERCISE_MANAGE.
    """
    service = QuestionService(db)
    service.delete_question(current_user, question_id)
