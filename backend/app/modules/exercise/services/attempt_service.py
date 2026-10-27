# File Name: attempt_service.py
# Description: Service layer for StudentExerciseAttempt operations (start, submit, grade, view).
# Created At: 2026-08-05
# Created By: Tam Khang
# Updated At: 2026-10-04
# Updated By: Tam Khang

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.models import User, ClassAssignment, StudentClass, StudentExerciseAttempt
from app.modules.exercise.schemas import AttemptSubmitRequest, AttemptListItemOut, AttemptGradeUpdateRequest
from app.modules.exercise.repository import AttemptRepository, AssignmentRepository
from app.modules.exercise.services.grading_service import GradingService
from app.modules.academic.scoping import get_user_role_name, check_class_access, get_accessible_class_ids


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
                    "message": "An in-progress attempt already exists for this assignment.",
                    "attempt_id": str(open_attempt.attempt_id)
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

    def list_attempts(
        self,
        current_user: User,
        class_id: Optional[UUID] = None,
        assignment_id: Optional[UUID] = None,
        is_finished: Optional[bool] = None,
        search: Optional[str] = None
    ) -> List[AttemptListItemOut]:
        """List attempts with RBAC data scoping for Teacher / Student / Admin."""
        role_name = get_user_role_name(self.db, current_user)

        if role_name == "Student":
            attempts = self.repo.list_attempts(
                student_id=current_user.user_id,
                assignment_id=assignment_id,
                is_finished=is_finished,
                search=search
            )
        elif role_name == "Teacher":
            accessible_class_ids = get_accessible_class_ids(self.db, current_user, role_name) or []
            if class_id:
                if class_id not in accessible_class_ids:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail={
                            "code": "ERR-ACAD-CLASS_ACCESS_DENIED",
                            "message": "You do not have permission to access attempts for this class."
                        }
                    )
                target_class_ids = [class_id]
            else:
                target_class_ids = accessible_class_ids

            attempts = self.repo.list_attempts(
                class_ids=target_class_ids,
                assignment_id=assignment_id,
                is_finished=is_finished,
                search=search
            )
        else:
            # Admin: unrestricted
            target_class_ids = [class_id] if class_id else None
            attempts = self.repo.list_attempts(
                class_ids=target_class_ids,
                assignment_id=assignment_id,
                is_finished=is_finished,
                search=search
            )

        items: List[AttemptListItemOut] = []
        for att in attempts:
            student_name = att.student.full_name if att.student else "Học sinh"
            student_code = att.student.phone if att.student else None
            class_id_val = att.assignment.class_id if att.assignment else att.attempt_id
            class_name = att.assignment.class_obj.class_name if (att.assignment and att.assignment.class_obj) else "Lớp"
            exercise_id = att.assignment.exercise_id if att.assignment else att.attempt_id
            exercise_title = att.assignment.exercise.title if (att.assignment and att.assignment.exercise) else "Bài tập"
            subject_id = att.assignment.exercise.subject_id if (att.assignment and att.assignment.exercise) else None

            items.append(
                AttemptListItemOut(
                    attempt_id=att.attempt_id,
                    assignment_id=att.assignment_id,
                    student_id=att.student_id,
                    student_name=student_name,
                    student_code=student_code,
                    class_id=class_id_val,
                    class_name=class_name,
                    exercise_id=exercise_id,
                    exercise_title=exercise_title,
                    subject_id=subject_id,
                    score=float(att.score) if att.score is not None else None,
                    is_finished=att.is_finished,
                    start_time=att.start_time,
                    end_time=att.end_time,
                    total_time_seconds=att.total_time_seconds,
                    status=att.status
                )
            )

        return items

    def update_attempt_grade(
        self,
        attempt_id: UUID,
        payload: AttemptGradeUpdateRequest,
        current_user: User
    ) -> StudentExerciseAttempt:
        """Teacher updates score and feedback on a submitted attempt."""
        attempt = self.repo.get_by_id(attempt_id)
        if not attempt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "ERR-EXE-ATTEMPT_NOT_FOUND",
                    "message": "Exercise attempt record not found."
                }
            )

        assignment = self.assignment_repo.get_by_id(attempt.assignment_id)
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "ERR-EXE-ASSIGNMENT_NOT_FOUND",
                    "message": "Associated assignment record not found."
                }
            )

        # Enforce class access scoping for Teacher
        check_class_access(self.db, current_user, assignment.class_id)

        return self.repo.update_grade(
            attempt=attempt,
            score=payload.score,
            feedback=payload.feedback,
            detailed_results=payload.detailed_results,
            status=payload.status
        )

    def get_grading_dashboard(self, current_user: User) -> "GradingDashboardOut":
        """Compute aggregate metrics and breakdown statistics for grading dashboard."""
        from app.modules.exercise.schemas import (
            GradingDashboardOut, GradingScoreDistribution, GradingClassSummary
        )

        attempts = self.list_attempts(current_user=current_user)

        total_submissions = len(attempts)
        known_statuses = ("pending_grading", "pending_review", "approved")

        def resolve_status(a) -> str:
            # Same rule as the Grading page: trust lifecycle status, otherwise infer from score
            st = getattr(a, 'status', None)
            if st in known_statuses:
                return st
            return 'approved' if a.score is not None else 'pending_grading'

        resolved = [resolve_status(a) for a in attempts]
        pending_grading_count = resolved.count('pending_grading')
        pending_review_count = resolved.count('pending_review')
        graded_count = resolved.count('approved')

        need_feedback = pending_grading_count

        scores = [a.score for a in attempts if a.score is not None]
        avg_score = round(sum(scores) / len(scores), 2) if scores else 0.0

        under_5 = sum(1 for s in scores if s < 5.0)
        from_5_to_6_5 = sum(1 for s in scores if 5.0 <= s < 6.5)
        from_6_5_to_8 = sum(1 for s in scores if 6.5 <= s < 8.0)
        from_8_to_10 = sum(1 for s in scores if s >= 8.0)

        distribution = GradingScoreDistribution(
            under_5=under_5,
            from_5_to_6_5=from_5_to_6_5,
            from_6_5_to_8=from_6_5_to_8,
            from_8_to_10=from_8_to_10
        )

        # Class breakdown
        class_map = {}
        for a in attempts:
            cid = a.class_id
            if cid not in class_map:
                class_map[cid] = {
                    "class_id": cid,
                    "class_name": a.class_name,
                    "total": 0,
                    "graded": 0,
                    "pending": 0,
                    "scores": []
                }
            class_map[cid]["total"] += 1
            if a.score is not None:
                class_map[cid]["graded"] += 1
                class_map[cid]["scores"].append(a.score)
            else:
                class_map[cid]["pending"] += 1

        by_class = []
        for cdata in class_map.values():
            c_scores = cdata["scores"]
            c_avg = round(sum(c_scores) / len(c_scores), 2) if c_scores else 0.0
            by_class.append(
                GradingClassSummary(
                    class_id=cdata["class_id"],
                    class_name=cdata["class_name"],
                    total_submissions=cdata["total"],
                    graded_count=cdata["graded"],
                    pending_count=cdata["pending"],
                    avg_score=c_avg
                )
            )

        return GradingDashboardOut(
            total_submissions=total_submissions,
            pending_grading_count=pending_grading_count,
            pending_review_count=pending_review_count,
            graded_count=graded_count,
            need_feedback_count=need_feedback,
            avg_score=avg_score,
            score_distribution=distribution,
            by_class=by_class,
            recent_submissions=attempts[:10]
        )

