# File Name: attempt_service.py
# Description: Service layer for StudentExerciseAttempt operations (start, submit, grade, view).
# Created At: 2026-08-05
# Created By: Tam Khang
# Updated At: 2026-08-05
# Updated By: Tam Khang

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.models import User, ClassAssignment, StudentClass, StudentExerciseAttempt
from app.modules.exercise.schemas import AttemptSubmitRequest
from app.modules.exercise.repository import AttemptRepository, AssignmentRepository
from app.modules.exercise.services.grading_service import GradingService
from app.modules.academic.scoping import get_user_role_name, check_class_access


class AttemptService:
    """Service layer handling student exercise submission workflow and permissions."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = AttemptRepository(db)
        self.assignment_repo = AssignmentRepository(db)

    def start_attempt(self, assignment_id: UUID, current_user: User) -> StudentExerciseAttempt:
        """Start a new exercise attempt for a student."""
        # 1. Verify assignment exists and is ACTIVE
        assignment = self.assignment_repo.get_by_id(assignment_id)
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "ERR-EXE-ASSIGNMENT_NOT_FOUND",
                    "message": "Class assignment record not found."
                }
            )

        # 2. Verify student is enrolled in the assigned class
        enrolled = self.db.query(StudentClass).filter(
            StudentClass.student_id == current_user.user_id,
            StudentClass.class_id == assignment.class_id,
            StudentClass.status == 'ACTIVE'
        ).first()

        if not enrolled:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "ERR-EXE-STUDENT_NOT_ENROLLED",
                    "message": "You are not enrolled in the class for this assignment."
                }
            )

        # 3. Check if an open attempt already exists
        open_attempt = self.repo.find_open_attempt(current_user.user_id, assignment_id)
        if open_attempt:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "ERR-EXE-ATTEMPT_ALREADY_OPEN",
                    "message": "You already have an open attempt for this assignment."
                }
            )

        # 4. Create new attempt
        attempt = StudentExerciseAttempt(
            student_id=current_user.user_id,
            assignment_id=assignment_id,
            start_time=datetime.now(timezone.utc),
            is_finished=False,
            status='ACTIVE'
        )
        return self.repo.create(attempt)

    def submit_attempt(self, attempt_id: UUID, payload: AttemptSubmitRequest, current_user: User) -> StudentExerciseAttempt:
        """Submit an open exercise attempt and trigger auto-grading."""
        # 1. Retrieve attempt
        attempt = self.repo.get_by_id(attempt_id)
        if not attempt or attempt.student_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "ERR-EXE-ATTEMPT_NOT_FOUND",
                    "message": "Exercise attempt record not found."
                }
            )

        # 2. Check if already submitted
        if attempt.is_finished:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "ERR-EXE-ATTEMPT_ALREADY_SUBMITTED",
                    "message": "This attempt has already been submitted."
                }
            )

        # 3. Get assignment to retrieve exercise_id
        assignment = self.assignment_repo.get_by_id(attempt.assignment_id)
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "ERR-EXE-ASSIGNMENT_NOT_FOUND",
                    "message": "Associated assignment record not found."
                }
            )

        # 4. Run auto-grading
        grading_service = GradingService(self.db)
        score, detailed_results = grading_service.grade_attempt(assignment.exercise_id, payload.answers)

        # 5. Compute time and update attempt
        now = datetime.now(timezone.utc)
        start_time = attempt.start_time
        if start_time and start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=timezone.utc)

        total_seconds = int((now - start_time).total_seconds()) if start_time else 0

        attempt.end_time = now
        attempt.total_time_seconds = total_seconds
        attempt.score = score
        attempt.detailed_results = detailed_results
        attempt.is_finished = True

        return self.repo.update(attempt)

    def get_attempt(self, attempt_id: UUID, current_user: User) -> StudentExerciseAttempt:
        """Retrieve attempt details with RBAC scoping."""
        attempt = self.repo.get_by_id(attempt_id)
        if not attempt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "ERR-EXE-ATTEMPT_NOT_FOUND",
                    "message": "Exercise attempt record not found."
                }
            )

        # Check permission scoping
        if attempt.student_id != current_user.user_id:
            # If user is not the attempt owner, check if user is teacher/admin with class access
            assignment = self.assignment_repo.get_by_id(attempt.assignment_id)
            if not assignment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "code": "ERR-EXE-ASSIGNMENT_NOT_FOUND",
                        "message": "Associated assignment record not found."
                    }
                )
            check_class_access(self.db, current_user, assignment.class_id)

        return attempt
