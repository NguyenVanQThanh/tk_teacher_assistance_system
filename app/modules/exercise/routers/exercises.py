# File Name: exercises.py
# Description: API Router for Exercise endpoints (F-EXE-01).
# Created At: 2026-07-31
# Created By: Tam Khang
# Updated At: 2026-07-31
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


@router.post(
    "",
    response_model=ExerciseOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_perm("EXE_EXERCISE_MANAGE"))]
)
def create_exercise(
    payload: ExerciseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Tạo đề bài tập mới. Yêu cầu quyền EXE_EXERCISE_MANAGE.
    """
    service = ExerciseService(db)
    return service.create_exercise(current_user, payload)


@router.get(
    "",
    response_model=List[ExerciseOut],
    dependencies=[Depends(require_perm("EXE_EXERCISE_VIEW"))]
)
def list_exercises(
    subject_id: Optional[UUID] = Query(None, description="Lọc theo ID môn học"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Lấy danh sách đề bài tập theo phạm vi môn học giảng dạy. Yêu cầu quyền EXE_EXERCISE_VIEW.
    """
    service = ExerciseService(db)
    return service.list_exercises(current_user, subject_id=subject_id)


@router.get(
    "/{exercise_id}",
    response_model=ExerciseOut,
    dependencies=[Depends(require_perm("EXE_EXERCISE_VIEW"))]
)
def get_exercise_detail(
    exercise_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Xem chi tiết đề bài tập kèm câu hỏi và đáp án lựa chọn. Yêu cầu quyền EXE_EXERCISE_VIEW.
    """
    service = ExerciseService(db)
    return service.get_exercise_detail(current_user, exercise_id)


@router.put(
    "/{exercise_id}",
    response_model=ExerciseOut,
    dependencies=[Depends(require_perm("EXE_EXERCISE_MANAGE"))]
)
def update_exercise(
    exercise_id: UUID,
    payload: ExerciseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Cập nhật thông tin đề bài tập. Yêu cầu quyền EXE_EXERCISE_MANAGE.
    """
    service = ExerciseService(db)
    return service.update_exercise(current_user, exercise_id, payload)


@router.delete(
    "/{exercise_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_perm("EXE_EXERCISE_MANAGE"))]
)
def delete_exercise(
    exercise_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Xóa mềm đề bài tập (chuyển status sang DELETED). Yêu cầu quyền EXE_EXERCISE_MANAGE.
    """
    service = ExerciseService(db)
    service.delete_exercise(current_user, exercise_id)


@router.post(
    "/{exercise_id}/restore",
    response_model=ExerciseOut,
    dependencies=[Depends(require_perm("EXE_EXERCISE_MANAGE"))]
)
def restore_exercise(
    exercise_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Khôi phục đề bài tập đã xóa mềm về trạng thái ACTIVE. Yêu cầu quyền EXE_EXERCISE_MANAGE.
    """
    service = ExerciseService(db)
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Thêm câu hỏi (+ đáp án trắc nghiệm) vào đề bài tập. Yêu cầu quyền EXE_EXERCISE_MANAGE.
    """
    service = QuestionService(db)
    return service.add_question(current_user, exercise_id, payload)
