# File Name: exercise_service.py
# Description: Service layer for Exercise management (scoping, CRUD, soft-delete, restore).
# Created At: 2026-07-31
# Created By: Tam Khang
# Updated At: 2026-07-31
# Updated By: Tam Khang

from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.models import User, Subject, TeacherSubject, Exercise
from app.modules.exercise.schemas import ExerciseCreate, ExerciseUpdate
from app.modules.exercise.repository import ExerciseRepository
from app.modules.academic.scoping import get_user_role_name


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
                    "message": "Môn học không tồn tại."
                }
            )

        # 2. Scope check for Teacher
        if role_name == "Teacher":
            active_subject_ids = self._get_teacher_active_subject_ids(current_user.user_id)
            if payload.subject_id not in active_subject_ids:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "code": "ERR-EXE-INVALID_SUBJECT_SCOPE",
                        "message": "Bạn không có quyền tạo đề bài tập cho môn học này."
                    }
                )

        # 3. Create exercise
        exercise = Exercise(
            title=payload.title,
            subject_id=payload.subject_id,
            created_by=current_user.user_id,
            total_questions=0,
            ai_metadata=payload.ai_metadata,
            status='ACTIVE'
        )
        return self.repo.create(exercise)

    def list_exercises(self, current_user: User, subject_id: Optional[UUID] = None) -> List[Exercise]:
        role_name = get_user_role_name(self.db, current_user)
        
        if role_name == "Admin":
            if subject_id:
                return self.repo.list_exercises(subject_ids=[subject_id], status='ACTIVE')
            return self.repo.list_exercises(status='ACTIVE')
        
        # For Teacher: restrict to created_by OR teacher_subjects
        active_subject_ids = self._get_teacher_active_subject_ids(current_user.user_id)
        if subject_id:
            if subject_id not in active_subject_ids:
                # Can only see if created by self for that subject
                return self.repo.list_exercises(created_by=current_user.user_id, subject_ids=[subject_id], status='ACTIVE')
            return self.repo.list_exercises(subject_ids=[subject_id], status='ACTIVE')
        
        return self.repo.list_exercises(created_by=current_user.user_id, subject_ids=active_subject_ids, status='ACTIVE')

    def get_exercise_detail(self, current_user: User, exercise_id: UUID) -> Exercise:
        role_name = get_user_role_name(self.db, current_user)
        exercise = self.repo.get_by_id(exercise_id, include_deleted=False)
        
        if not exercise:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "ERR-EXE-EXERCISE_NOT_FOUND",
                    "message": "Đề bài tập không tồn tại."
                }
            )

        if role_name == "Teacher":
            active_subject_ids = self._get_teacher_active_subject_ids(current_user.user_id)
            if exercise.created_by != current_user.user_id and exercise.subject_id not in active_subject_ids:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "code": "ERR-EXE-EXERCISE_NOT_FOUND",
                        "message": "Đề bài tập không tồn tại."
                    }
                )

        return exercise

    def update_exercise(self, current_user: User, exercise_id: UUID, payload: ExerciseUpdate) -> Exercise:
        exercise = self.get_exercise_detail(current_user, exercise_id)
        return self.repo.update(exercise, title=payload.title, ai_metadata=payload.ai_metadata)

    def delete_exercise(self, current_user: User, exercise_id: UUID) -> None:
        exercise = self.get_exercise_detail(current_user, exercise_id)
        self.repo.soft_delete(exercise)

    def restore_exercise(self, current_user: User, exercise_id: UUID) -> Exercise:
        role_name = get_user_role_name(self.db, current_user)
        exercise = self.repo.get_by_id(exercise_id, include_deleted=True)
        
        if not exercise:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "ERR-EXE-EXERCISE_NOT_FOUND",
                    "message": "Đề bài tập không tồn tại."
                }
            )

        if role_name == "Teacher":
            active_subject_ids = self._get_teacher_active_subject_ids(current_user.user_id)
            if exercise.created_by != current_user.user_id and exercise.subject_id not in active_subject_ids:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "code": "ERR-EXE-EXERCISE_NOT_FOUND",
                        "message": "Đề bài tập không tồn tại."
                    }
                )

        return self.repo.restore(exercise)
