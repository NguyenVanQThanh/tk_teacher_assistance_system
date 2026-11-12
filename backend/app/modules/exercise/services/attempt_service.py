# File Name: attempt_service.py
# Description: Service layer for StudentExerciseAttempt operations (start, submit, grade, view)
#              plus the student-safe sanitized "paper" of an owned attempt.
# Created At: 2026-08-05
# Created By: Tam Khang
# Updated At: 2026-11-12
# Updated By: AI Agent

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.models import User, Subject, Exercise, ClassAssignment, StudentClass, StudentExerciseAttempt
from app.modules.exercise.schemas import (
    AttemptSubmitRequest, AttemptListItemOut, AttemptGradeUpdateRequest, AssignmentTakingOut
)
from app.modules.exercise.repository import AttemptRepository, AssignmentRepository
from app.modules.exercise.services.assignment_service import AssignmentService
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

        # 3b. Availability window: a new attempt may not start after the due date.
        due_at = assignment.due_at
        if due_at is not None:
            if due_at.tzinfo is None:
                due_at = due_at.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) > due_at:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "code": "ERR-EXE-ASSIGNMENT_EXPIRED",
                        "message": "This assignment is past its due date."
                    }
                )

        # 3c. Attempt limit: max_attempts comes from the exercise metadata (exams default to 1).
        exercise = self.db.query(Exercise).filter(
            Exercise.exercise_id == assignment.exercise_id,
            Exercise.status != 'DELETED'
        ).first()
        ai_meta = (exercise.ai_metadata or {}) if exercise else {}
        is_exam = "đề thi" in (exercise.title or "").lower() if exercise else False
        max_attempts = int(ai_meta.get("max_attempts", 1 if is_exam else 3))
        attempt_count = self.db.query(StudentExerciseAttempt).filter(
            StudentExerciseAttempt.student_id == current_user.user_id,
            StudentExerciseAttempt.assignment_id == assignment_id,
            StudentExerciseAttempt.status != 'DELETED'
        ).count()
        if attempt_count >= max_attempts:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "ERR-EXE-ATTEMPT_LIMIT_REACHED",
                    "message": "You have used all allowed attempts for this assignment."
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

    def get_attempt_paper(self, attempt_id: UUID, current_user: User) -> AssignmentTakingOut:
        """
        Return the sanitized paper (questions without answer key) of an attempt owned by the
        current student. Only the attempt owner may access it (403 otherwise).
        """
        attempt = self.repo.get_by_id(attempt_id)
        if not attempt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "ERR-EXE-ATTEMPT_NOT_FOUND",
                    "message": "Exercise attempt record not found."
                }
            )

        if attempt.student_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "ERR-EXE-ATTEMPT_NOT_OWNER",
                    "message": "You can only view the paper of your own attempt."
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

        # Reuses the student-safe builder (sanitized questions, open attempt attached).
        return AssignmentService(self.db).build_student_paper(assignment, current_user.user_id)

    def list_attempts(
        self,
        current_user: User,
        class_id: Optional[UUID] = None,
        assignment_id: Optional[UUID] = None,
        is_finished: Optional[bool] = None,
        search: Optional[str] = None,
        student_id: Optional[UUID] = None
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
                student_id=student_id,
                is_finished=is_finished,
                search=search
            )
        else:
            # Admin: unrestricted
            target_class_ids = [class_id] if class_id else None
            attempts = self.repo.list_attempts(
                class_ids=target_class_ids,
                assignment_id=assignment_id,
                student_id=student_id,
                is_finished=is_finished,
                search=search
            )

        subject_names = {sid: name for sid, name in self.db.query(Subject.subject_id, Subject.subject_name).all()}
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
                    assignment_title=exercise_title,
                    subject_id=subject_id,
                    subject_name=subject_names.get(subject_id),
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

        detailed_results = payload.detailed_results
        if payload.manual_marks:
            # Persist teacher verdicts on short answers so later regrades keep them.
            base = dict(detailed_results if isinstance(detailed_results, dict) else (attempt.detailed_results or {}))
            marks = {str(k).lower(): bool(v) for k, v in payload.manual_marks.items()}
            questions = []
            for r in base.get("questions", []):
                r = dict(r)
                verdict = marks.get(str(r.get("question_id", "")).lower())
                if verdict is not None:
                    r.update(is_correct=verdict, manual_override=True, pending_manual_grade=False)
                questions.append(r)
            base["questions"] = questions
            if payload.feedback is not None:
                base["teacher_feedback"] = payload.feedback
            detailed_results = base

        # Mark a teacher-set TOTAL score so a later answer-key regrade does not silently
        # overwrite it (regrade_exercise preserves detailed_results['teacher_total_score']).
        if payload.score is not None:
            if not isinstance(detailed_results, dict):
                detailed_results = dict(attempt.detailed_results or {})
            detailed_results["teacher_total_score"] = float(payload.score)

        return self.repo.update_grade(
            attempt=attempt,
            score=payload.score,
            feedback=payload.feedback,
            detailed_results=detailed_results,
            status=payload.status
        )

    def update_answer_key_and_regrade(self, exercise_id: UUID, keys: dict, current_user: User) -> dict:
        """Apply a new MultipleChoice answer key and persist recomputed scores for ALL submissions of the exercise."""
        from app.modules.exercise.services.exercise_service import ExerciseService
        # Scoping check (raises 404 when the teacher cannot access the exercise)
        ExerciseService(self.db).get_exercise_detail(current_user, exercise_id)
        grader = GradingService(self.db)
        updated = grader.apply_answer_key(exercise_id, list(keys.items()))
        regraded = grader.regrade_exercise(exercise_id)
        return {"updated_questions": updated, "regraded_attempts": regraded}

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

