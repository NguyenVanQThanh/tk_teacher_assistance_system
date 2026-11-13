# File Name: exercise_service.py
# Description: Service layer for Exercise management (scoping, CRUD, soft-delete, restore).
# Created At: 2026-07-31
# Created By: Tam Khang
# Updated At: 2026-11-13
# Updated By: AI Agent

from typing import List, Optional, Dict, Any
from uuid import UUID
import uuid
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.models import User, Subject, TeacherSubject, Exercise, Question, AnswerOption, ClassAssignment, StudentClass, Class
from app.modules.exercise.schemas import ExerciseCreate, ExerciseUpdate, AiExerciseGenerateRequest, AiExerciseGenerateOut
from app.modules.exercise.repository import ExerciseRepository
from app.modules.academic.scoping import get_user_role_name
from app.modules.auth import access_policy
from app.modules.exercise.services.ai_exercise_service import AiExerciseService
from app.modules.exercise.services.rag_context_service import RagContextService


class ExerciseService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ExerciseRepository(db)

    def _get_teacher_active_subject_ids(self, teacher_id: UUID) -> List[UUID]:
        assigned = self.db.query(TeacherSubject.subject_id).filter(
            TeacherSubject.teacher_id == teacher_id,
            TeacherSubject.status == 'ACTIVE'
        ).distinct().all()
        return [row[0] for row in assigned]

    def create_exercise(self, current_user: User, payload: ExerciseCreate) -> Exercise:
        role_name = get_user_role_name(self.db, current_user)
        
        # 1. Verify subject exists
        subject = self.db.query(Subject).filter(Subject.subject_id == payload.subject_id).first()
        if not subject or subject.status == 'DELETED':
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "ERR-EXE-SUBJECT_NOT_FOUND",
                    "message": "Subject not found."
                }
            )

        # 2. Scope check for Teacher
        if access_policy.is_teacher(role_name):
            active_subject_ids = self._get_teacher_active_subject_ids(current_user.user_id)
            if payload.subject_id not in active_subject_ids:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "code": "ERR-EXE-INVALID_SUBJECT_SCOPE",
                        "message": "You do not have permission to create exercises for this subject."
                    }
                )

        # 3. Create exercise
        exercise = Exercise(
            title=payload.title,
            subject_id=payload.subject_id,
            created_by=current_user.user_id,
            total_questions=0,
            ai_metadata=payload.ai_metadata,
            exercise_kind=payload.exercise_kind,
            status='ACTIVE'
        )
        return self.repo.create(exercise)

    def list_exercises(
        self,
        current_user: User,
        subject_id: Optional[UUID] = None,
        search: Optional[str] = None,
        cursor: Optional[str] = None,
        direction: str = "next",
        page_size: int = 6
    ) -> Dict[str, Any]:
        """List exercises visible to the user (own, plus head-of-subject shared; Admin sees all)."""
        return self.repo.list_exercises(
            subject_ids=[subject_id] if subject_id else None,
            status='ACTIVE',
            search=search,
            cursor=cursor,
            direction=direction,
            page_size=page_size,
            visibility_clause=access_policy.exercise_visibility_clause(self.db, current_user),
        )

    def _not_found(self) -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ERR-EXE-EXERCISE_NOT_FOUND", "message": "Exercise not found."}
        )

    def _load_visible(self, current_user: User, exercise_id: UUID, include_deleted: bool = False) -> Exercise:
        """Load an exercise or raise 404 when missing or invisible to the user."""
        exercise = self.repo.get_by_id(exercise_id, include_deleted=include_deleted)
        if not exercise:
            raise self._not_found()
        clause = access_policy.exercise_visibility_clause(self.db, current_user)
        if clause is not None:
            visible = self.db.query(Exercise.exercise_id).filter(
                Exercise.exercise_id == exercise_id, clause
            ).first()
            if not visible:
                raise self._not_found()
        return exercise

    def get_exercise_detail(self, current_user: User, exercise_id: UUID) -> Exercise:
        """Read access: 404 unless visible to the user."""
        return self._load_visible(current_user, exercise_id)

    def get_exercise_for_write(self, current_user: User, exercise_id: UUID, include_deleted: bool = False) -> Exercise:
        """Write access: visibility (404) then owner-only (403)."""
        exercise = self._load_visible(current_user, exercise_id, include_deleted=include_deleted)
        access_policy.ensure_can_write(self.db, current_user, exercise.created_by)
        return exercise

    def update_exercise(self, current_user: User, exercise_id: UUID, payload: ExerciseUpdate) -> Exercise:
        exercise = self.get_exercise_for_write(current_user, exercise_id)
        return self.repo.update(exercise, title=payload.title, ai_metadata=payload.ai_metadata,
                                exercise_kind=payload.exercise_kind)

    def set_answers_released(self, current_user: User, exercise_id: UUID, released: bool) -> Exercise:
        """Release/hide answers for every active assignment of an EXAM exercise (all classes)."""
        exercise = self.get_exercise_for_write(current_user, exercise_id)
        if exercise.exercise_kind != 'EXAM':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "ERR-EXE-NOT_AN_EXAM", "message": "Only exam exercises have releasable answers."}
            )
        stamp = datetime.now(timezone.utc) if released else None
        for a in exercise.assignments:
            if a.status != 'DELETED':
                a.answers_released_at = stamp
        self.db.commit()
        self.db.refresh(exercise)
        return exercise

    def delete_exercise(self, current_user: User, exercise_id: UUID) -> None:
        exercise = self.get_exercise_for_write(current_user, exercise_id)
        self.repo.soft_delete(exercise)

    def restore_exercise(self, current_user: User, exercise_id: UUID) -> Exercise:
        exercise = self.get_exercise_for_write(current_user, exercise_id, include_deleted=True)
        return self.repo.restore(exercise)

    def generate_ai_exercise(self, current_user: User, payload: AiExerciseGenerateRequest) -> AiExerciseGenerateOut:
        """Teacher generation; delegates to AiExerciseService (no Subject/Class is auto-created)."""
        return AiExerciseService(self.db).generate(current_user, payload)
