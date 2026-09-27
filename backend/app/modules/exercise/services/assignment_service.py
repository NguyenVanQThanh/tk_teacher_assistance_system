# File Name: assignment_service.py
# Description: Service layer for ClassAssignment operations (creation, scoping, soft-delete, restore).
# Created At: 2026-07-31
# Created By: Tam Khang
# Updated At: 2026-09-27
# Updated By: Tam Khang

from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.models import User, Class, Exercise, TeacherSubject, ClassAssignment
from app.modules.exercise.schemas import AssignmentCreate
from app.modules.exercise.repository import AssignmentRepository, ExerciseRepository
from app.modules.academic.scoping import get_user_role_name, check_class_access


class AssignmentService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AssignmentRepository(db)
        self.exercise_repo = ExerciseRepository(db)

    def create_assignment(self, class_id: UUID, payload: AssignmentCreate, current_user: User) -> ClassAssignment:
        role_name = get_user_role_name(self.db, current_user)

        # 1. Verify class exists and is ACTIVE
        class_obj = self.db.query(Class).filter(Class.class_id == class_id, Class.status != 'DELETED').first()
        if not class_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "ERR-ACAD-CLASS_NOT_FOUND",
                    "message": "Class not found."
                }
            )

        # 2. Verify exercise exists and is ACTIVE
        exercise = self.exercise_repo.get_by_id(payload.exercise_id)
        if not exercise:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "ERR-EXE-EXERCISE_NOT_FOUND",
                    "message": "Exercise not found."
                }
            )

        # 3. Scoping check for Teacher
        if role_name == "Teacher":
            assigned = self.db.query(TeacherSubject).filter(
                TeacherSubject.teacher_id == current_user.user_id,
                TeacherSubject.class_id == class_id,
                TeacherSubject.subject_id == exercise.subject_id,
                TeacherSubject.status == 'ACTIVE'
            ).first()

            # Also permit if teacher authored the exercise and teaches this class / is homeroom teacher
            if not assigned and exercise.created_by == current_user.user_id:
                has_class_access = self.db.query(TeacherSubject).filter(
                    TeacherSubject.teacher_id == current_user.user_id,
                    TeacherSubject.class_id == class_id,
                    TeacherSubject.status == 'ACTIVE'
                ).first()
                if not has_class_access:
                    has_class_access = self.db.query(Class).filter(
                        Class.class_id == class_id,
                        Class.homeroom_teacher_id == current_user.user_id,
                        Class.status != 'DELETED'
                    ).first()
                if has_class_access:
                    assigned = True

            if not assigned:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "code": "ERR-EXE-CLASS_ACCESS_DENIED",
                        "message": "You do not have permission to assign exercises for this class's subject."
                    }
                )

        # 4. Check duplicate assignment
        existing = self.repo.find_active_by_class_and_exercise(class_id, payload.exercise_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "ERR-EXE-DUPLICATE_ASSIGNMENT",
                    "message": "This exercise has already been assigned to this class."
                }
            )

        # 5. Create class assignment
        assignment = ClassAssignment(
            class_id=class_id,
            exercise_id=payload.exercise_id,
            assigned_by=current_user.user_id,
            due_at=payload.due_at
        )
        return self.repo.create(assignment)

    def list_class_assignments(self, class_id: UUID, current_user: User) -> List[ClassAssignment]:
        # 1. Verify class exists and is ACTIVE
        class_obj = self.db.query(Class).filter(Class.class_id == class_id, Class.status != 'DELETED').first()
        if not class_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "ERR-ACAD-CLASS_NOT_FOUND",
                    "message": "Class not found."
                }
            )

        # 2. Enforce class access scoping
        check_class_access(self.db, current_user, class_id)

        # 3. Retrieve active assignments
        return self.repo.list_by_class_ids([class_id])

    def delete_assignment(self, assignment_id: UUID, current_user: User) -> ClassAssignment:
        assignment = self.repo.get_by_id(assignment_id)
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "ERR-EXE-ASSIGNMENT_NOT_FOUND",
                    "message": "Class assignment record not found."
                }
            )

        if self.repo.has_attempts(assignment_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "ERR-EXE-ASSIGNMENT_HAS_ATTEMPTS",
                    "message": "Assignment has student attempts and cannot be cancelled."
                }
            )

        return self.repo.soft_delete(assignment)

    def restore_assignment(self, assignment_id: UUID, current_user: User) -> ClassAssignment:
        assignment = self.repo.get_by_id(assignment_id, include_deleted=True)
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "ERR-EXE-ASSIGNMENT_NOT_FOUND",
                    "message": "Class assignment record not found."
                }
            )

        return self.repo.restore(assignment)
