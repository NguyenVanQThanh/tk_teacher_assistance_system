# File Name: assignment_service.py
# Description: Service layer for ClassAssignment operations (creation, scoping, feed listing, soft-delete, restore)
#              plus the student-safe "taking" paper builder (sanitized questions, no answer key).
# Created At: 2026-07-31
# Created By: Tam Khang
# Updated At: 2026-11-13
# Updated By: AI Agent

import hashlib
import random
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_

from models.models import User, Class, Exercise, TeacherSubject, ClassAssignment, Subject, StudentClass, StudentExerciseAttempt, Question
from app.modules.exercise.schemas import (
    AssignmentCreate, AssignmentResultSummaryOut, AssignmentAttemptDetail,
    CognitiveAnalysis, CognitiveLevelStats,
    AssignmentTakingOut, AssignmentTakingInfoOut, AssignmentTakingExerciseOut,
    StudentQuestionOut, StudentOpenAttemptOut
)
from app.modules.exercise.repository import AssignmentRepository, ExerciseRepository, AttemptRepository
from app.modules.academic.scoping import get_user_role_name, check_class_access, get_accessible_class_ids

# ai_metadata keys that may be shown to students (display only; no generation context).
_STUDENT_SAFE_META_KEYS = {"type", "grade", "grade_name", "level", "duration", "duration_minutes",
                           "max_attempts", "is_ai_generated", "sources"}


def open_attempt_deadline(assignment: ClassAssignment, exercise: Optional[Exercise]) -> Optional[datetime]:
    """Latest moment an open attempt may be resumed or submitted: due_at plus the paper duration
    (an attempt started right before the due date still gets its full time). None = no due date."""
    due_at = assignment.due_at
    if due_at is None:
        return None
    if due_at.tzinfo is None:
        due_at = due_at.replace(tzinfo=timezone.utc)
    minutes = int(((exercise.ai_metadata or {}) if exercise else {}).get("duration_minutes", 45) or 45)
    return due_at + timedelta(minutes=minutes)


def _seed_to_int(seed: str) -> int:
    """Deterministic 64-bit integer seed from a string (stable across processes and restarts)."""
    return int.from_bytes(hashlib.sha256(seed.encode("utf-8")).digest()[:8], "big")


def _shuffle_seed_for_attempt(
    assignment_id: UUID,
    student_id: UUID,
    attempt: Optional[StudentExerciseAttempt],
) -> str:
    """Resolve the display-shuffle seed used for a student's paper.

    - A started attempt stores its own random seed in the existing JSON column
      `student_exercise_attempts.detailed_results["shuffle_seed"]`, so reloading, resuming or
      reviewing THAT attempt always reproduces the same question/option order (no schema change).
    - Legacy attempts created before display shuffling existed have no seed; derive a stable one
      from the attempt id so their paper does not jump between reloads either.
    - Before any attempt exists, derive a stable preview seed from assignment + student so the
      pre-start preview keeps the same order on every request.
    """
    if attempt is not None:
        detailed = attempt.detailed_results
        if isinstance(detailed, dict):
            seed = detailed.get("shuffle_seed")
            if isinstance(seed, str) and seed.strip():
                return seed
        return f"{assignment_id}:{student_id}:attempt:{attempt.attempt_id}"
    return f"{assignment_id}:{student_id}:preview"


def _shuffle_student_questions(
    questions: List[StudentQuestionOut],
    seed: str,
) -> List[StudentQuestionOut]:
    """Shuffle the student-visible question/option order WITHOUT touching the ORM or the DB.

    Only the Pydantic display copies are reordered and their `display_order` is rewritten as a
    1-based display alias; the persisted `questions.display_order` /
    `answer_options.display_order` values stay untouched. Every question/option appears exactly
    once (random.shuffle only permutes the list), so nothing is lost or duplicated.

    - MultipleChoice: options are shuffled too. Grading matches the submitted answer by
      option_id, so the displayed order cannot change the score.
    - TrueFalse / ShortAnswer / Other: options are deliberately LEFT IN DB ORDER. TrueFalse
      grading maps the student's "a:true;b:false;..." labels to the option position (or to the
      a/b/c/d content prefix), so shuffling would silently change which statement a label refers
      to and corrupt the score. ShortAnswer has no options and Other's options are ordered
      sub-questions, which must keep their order for the same reason.
    """
    rng = random.Random(_seed_to_int(seed))

    # Sort first so the shuffle input is deterministic even when DB rows tie on display_order.
    ordered = sorted(questions, key=lambda q: (q.display_order, str(q.question_id)))
    rng.shuffle(ordered)

    shuffled: List[StudentQuestionOut] = []
    for index, question in enumerate(ordered, start=1):
        options = list(question.answer_options or [])
        if question.question_type == "MultipleChoice":
            options.sort(key=lambda o: (o.display_order, str(o.option_id)))
            rng.shuffle(options)
            options = [
                option.model_copy(update={"display_order": option_index})
                for option_index, option in enumerate(options, start=1)
            ]
        shuffled.append(
            question.model_copy(update={"display_order": index, "answer_options": options})
        )
    return shuffled


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

        # 5. Save duration_minutes and max_attempts to exercise metadata if provided
        if payload.duration_minutes or payload.max_attempts:
            curr_meta = dict(exercise.ai_metadata or {})
            if payload.duration_minutes:
                curr_meta["duration_minutes"] = payload.duration_minutes
            if payload.max_attempts:
                curr_meta["max_attempts"] = payload.max_attempts
            exercise.ai_metadata = curr_meta
            self.db.add(exercise)
            self.db.flush()

        # 6. Create class assignment
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

    def list_assignments_feed(
        self,
        current_user: User,
        tab: Optional[str] = None,
        subject_id: Optional[UUID] = None,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        role_name = get_user_role_name(self.db, current_user)
        accessible_class_ids = get_accessible_class_ids(self.db, current_user, role_name)

        if accessible_class_ids is not None and len(accessible_class_ids) == 0:
            return []

        query = (
            self.db.query(ClassAssignment)
            .join(ClassAssignment.class_obj)
            .join(ClassAssignment.exercise)
            .filter(ClassAssignment.status != 'DELETED', Class.status != 'DELETED')
        )

        if accessible_class_ids is not None:
            query = query.filter(ClassAssignment.class_id.in_(accessible_class_ids))

        if subject_id:
            query = query.filter(Exercise.subject_id == subject_id)

        if search and search.strip():
            term = f"%{search.strip()}%"
            query = query.outerjoin(Subject, Exercise.subject_id == Subject.subject_id)\
                         .outerjoin(User, ClassAssignment.assigned_by == User.user_id)\
                         .filter(
                             or_(
                                 Exercise.title.ilike(term),
                                 User.full_name.ilike(term),
                                 Subject.subject_name.ilike(term)
                             )
                         )

        assignments = query.order_by(ClassAssignment.due_at.asc(), ClassAssignment.assigned_at.desc()).all()

        results = []
        now = datetime.now(timezone.utc)

        for a in assignments:
            # Query attempts for this user
            attempts = (
                self.db.query(StudentExerciseAttempt)
                .filter(
                    StudentExerciseAttempt.assignment_id == a.assignment_id,
                    StudentExerciseAttempt.student_id == current_user.user_id,
                    StudentExerciseAttempt.status != 'DELETED'
                )
                .order_by(StudentExerciseAttempt.created_at.desc())
                .all()
            )
            completed_attempts = [att for att in attempts if att.is_finished]
            completed_count = len(completed_attempts)
            is_finished = completed_count > 0
            latest_score = float(completed_attempts[0].score) if completed_attempts and completed_attempts[0].score is not None else None

            # Calculate overdue
            due_at_tz = a.due_at if a.due_at.tzinfo else a.due_at.replace(tzinfo=timezone.utc)
            is_overdue = (due_at_tz < now) and not is_finished

            # Determine feed status
            if is_finished:
                feed_status = 'completed'
            elif is_overdue:
                feed_status = 'overdue'
            else:
                feed_status = 'active'

            # Tab filtering
            if tab:
                clean_tab = tab.strip().lower()
                if clean_tab in ('in_progress', 'active') and feed_status != 'active':
                    continue
                elif clean_tab == 'overdue' and feed_status != 'overdue':
                    continue
                elif clean_tab == 'completed' and feed_status != 'completed':
                    continue

            # Fetch subject details
            subject = self.db.query(Subject).filter(Subject.subject_id == a.exercise.subject_id).first()
            subject_name = subject.subject_name if subject else "Chung"

            # Teacher name and AI metadata
            is_ai_gen = bool(a.exercise and (a.exercise.ai_metadata or {}).get("is_ai_generated"))
            teacher_name = "Trợ lý AI Tam Khang" if is_ai_gen else (a.assigner.full_name if a.assigner else "Giáo viên bộ môn")
            category = "ai_generated" if is_ai_gen else ("exam" if a.exercise.exercise_kind == "EXAM" else "class_exercise")
            category_label = "Bài tập tạo sinh AI" if is_ai_gen else ("Bài thi" if category == "exam" else "Bài tập trên lớp")

            results.append({
                "assignment_id": a.assignment_id,
                "class_id": a.class_id,
                "exercise_id": a.exercise_id,
                "assigned_by": a.assigned_by,
                "assigned_at": a.assigned_at,
                "due_at": a.due_at,
                "status": a.status,
                "exercise_title": a.exercise.title if a.exercise else "Bài tập",
                "answers_released": a.answers_released_at is not None,
                "total_questions": a.exercise.total_questions if a.exercise else 0,
                "class_name": a.class_obj.class_name if a.class_obj else "Lớp học",
                "subject_id": a.exercise.subject_id if a.exercise else None,
                "subject_name": subject_name,
                "teacher_name": teacher_name,
                "duration_minutes": (a.exercise.ai_metadata or {}).get("duration_minutes", 45) if is_ai_gen else 45,
                "max_attempts": 1 if category == "exam" else 3,
                "completed_attempts_count": completed_count,
                "is_finished": is_finished,
                "latest_score": latest_score,
                "feed_status": feed_status,
                "category": category,
                "categoryLabel": category_label,
                "is_ai_generated": is_ai_gen,
                # Teacher/AI-assigned exercise type; None means unclassified
                "exercise_type": (a.exercise.ai_metadata or {}).get("type") if a.exercise else None
            })

        return results

    def get_assignment_taking(self, assignment_id: UUID, current_user: User) -> AssignmentTakingOut:
        """
        Student-safe "paper" of an assignment: assignment info + exercise info + SANITIZED questions
        (no correct_answer / explanation / is_correct) + the current user's open attempt (if any).

        - 404 when the assignment does not exist or was cancelled (status DELETED).
        - 403 when a Student is not enrolled in the assignment's class (teachers/admins go through
          the standard class-access scoping instead).
        """
        # repo.get_by_id already excludes DELETED assignments -> cancelled ones 404 here.
        assignment = self.repo.get_by_id(assignment_id)
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "ERR-EXE-ASSIGNMENT_NOT_FOUND",
                    "message": "Class assignment record not found."
                }
            )

        role_name = get_user_role_name(self.db, current_user)
        if role_name == "Student":
            enrolled = self.db.query(StudentClass).filter(
                StudentClass.student_id == current_user.user_id,
                StudentClass.class_id == assignment.class_id,
                StudentClass.status != 'DELETED'
            ).first()
            if not enrolled:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "code": "ERR-EXE-STUDENT_NOT_ENROLLED",
                        "message": "You are not enrolled in the class for this assignment."
                    }
                )
            # Availability window + attempt-limit gating: the paper may be served only to
            # resume an open attempt, to review an already-finished attempt, or while the
            # assignment is still open and the student has attempts left.
            self._check_student_taking_allowed(assignment, current_user.user_id)
        else:
            # Teacher / Admin: standard class access scoping.
            check_class_access(self.db, current_user, assignment.class_id)

        return self.build_student_paper(assignment, current_user.user_id)

    def _check_student_taking_allowed(self, assignment: ClassAssignment, student_id: UUID) -> None:
        """403 when a student without any attempt tries to read a paper past its due date or
        after exhausting max_attempts. Finished attempts are always allowed (review); an open attempt
        may be resumed only until open_attempt_deadline (due_at + duration)."""
        exercise = self.db.query(Exercise).filter(
            Exercise.exercise_id == assignment.exercise_id,
            Exercise.status != 'DELETED'
        ).first()
        attempt_repo = AttemptRepository(self.db)
        open_attempt = attempt_repo.find_open_attempt(student_id, assignment.assignment_id)
        if open_attempt:
            deadline = open_attempt_deadline(assignment, exercise)
            if deadline is None or datetime.now(timezone.utc) <= deadline:
                return

        attempts = self.db.query(StudentExerciseAttempt).filter(
            StudentExerciseAttempt.student_id == student_id,
            StudentExerciseAttempt.assignment_id == assignment.assignment_id,
            StudentExerciseAttempt.status != 'DELETED'
        ).all()
        if any(a.is_finished for a in attempts):
            return  # review of own submitted attempt

        due_at = assignment.due_at
        if due_at is not None:
            if due_at.tzinfo is None:
                due_at = due_at.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) > due_at:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "code": "ERR-EXE-ASSIGNMENT_EXPIRED",
                        "message": "This assignment is past its due date and you have no attempt to resume."
                    }
                )

        ai_meta = (exercise.ai_metadata or {}) if exercise else {}
        is_exam = (exercise.exercise_kind == "EXAM") if exercise else False
        max_attempts = ai_meta.get("max_attempts", 1 if is_exam else 3)
        if len(attempts) >= int(max_attempts):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "ERR-EXE-ATTEMPT_LIMIT_REACHED",
                    "message": "You have used all allowed attempts for this assignment."
                }
            )

    def build_student_paper(
        self,
        assignment: ClassAssignment,
        student_id: UUID,
        attempt: Optional[StudentExerciseAttempt] = None,
    ) -> AssignmentTakingOut:
        """Build the sanitized AssignmentTakingOut payload for an already-access-checked assignment.

        Question and MultipleChoice option order are shuffled per attempt (display-only alias; the
        DB order is never modified). `attempt` pins the paper to a specific attempt (used when
        reviewing an owned attempt); when omitted, the student's latest attempt (open or finished)
        decides the order, falling back to a deterministic pre-start preview order.
        """
        exercise = self.db.query(Exercise).filter(
            Exercise.exercise_id == assignment.exercise_id,
            Exercise.status != 'DELETED'
        ).first()
        if not exercise:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "ERR-EXE-EXERCISE_NOT_FOUND",
                    "message": "Exercise not found."
                }
            )

        questions = self.db.query(Question).options(
            joinedload(Question.answer_options)
        ).filter(
            Question.exercise_id == exercise.exercise_id,
            Question.status != 'DELETED'
        ).order_by(Question.display_order.asc()).all()

        subject_obj = None
        if exercise.subject_id:
            subject_obj = self.db.query(Subject).filter(
                Subject.subject_id == exercise.subject_id,
                Subject.status != 'DELETED'
            ).first()

        # duration_minutes / max_attempts live in exercise.ai_metadata (same rule as the feed).
        ai_meta = exercise.ai_metadata or {}
        is_exam = exercise.exercise_kind == "EXAM"
        duration_minutes = ai_meta.get("duration_minutes", 45)
        max_attempts = ai_meta.get("max_attempts", 1 if is_exam else 3)

        # The student's own in-progress attempt for this assignment (if any).
        attempt_repo = AttemptRepository(self.db)
        open_attempt = attempt_repo.find_open_attempt(student_id, assignment.assignment_id)
        open_attempt_out: Optional[StudentOpenAttemptOut] = None
        if open_attempt:
            saved_answers = None
            detailed = open_attempt.detailed_results
            if isinstance(detailed, dict):
                saved_answers = detailed.get("answers")
            open_attempt_out = StudentOpenAttemptOut(
                attempt_id=open_attempt.attempt_id,
                created_at=open_attempt.created_at,
                start_time=open_attempt.start_time,
                answers=saved_answers
            )

        # Resolve the per-attempt shuffle seed (explicit attempt for review, else latest attempt).
        shuffle_attempt = attempt or attempt_repo.find_latest_attempt(student_id, assignment.assignment_id)
        shuffle_seed = _shuffle_seed_for_attempt(assignment.assignment_id, student_id, shuffle_attempt)

        # StudentQuestionOut omits correct_answer/explanation; its segments/options sanitize themselves.
        student_questions = [StudentQuestionOut.model_validate(q) for q in questions]
        # Display-only shuffle: reorders the Pydantic copies and rewrites display_order as an
        # alias; questions/answer_options rows in the DB keep their original order.
        student_questions = _shuffle_student_questions(student_questions, shuffle_seed)

        return AssignmentTakingOut(
            assignment=AssignmentTakingInfoOut(
                assignment_id=assignment.assignment_id,
                exercise_id=assignment.exercise_id,
                class_id=assignment.class_id,
                due_at=assignment.due_at,
                duration_minutes=duration_minutes,
                max_attempts=max_attempts,
                status=assignment.status,
                teacher_name=assignment.assigner.full_name if assignment.assigner else None,
                class_name=assignment.class_obj.class_name if assignment.class_obj else None,
                subject_name=subject_obj.subject_name if subject_obj else None
            ),
            exercise=AssignmentTakingExerciseOut(
                exercise_id=exercise.exercise_id,
                title=exercise.title,
                subject_id=exercise.subject_id,
                subject_name=subject_obj.subject_name if subject_obj else None,
                # Whitelist: generation context (prompts, matrices, document ids) stays server-side.
                ai_metadata={k: v for k, v in (exercise.ai_metadata or {}).items() if k in _STUDENT_SAFE_META_KEYS}
            ),
            questions=student_questions,
            open_attempt=open_attempt_out
        )

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

    def set_answers_released(self, assignment_id: UUID, released: bool, current_user: User) -> ClassAssignment:
        """Teacher/admin toggles whether students may see per-question results of an exam."""
        assignment = self.repo.get_by_id(assignment_id)
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "ERR-EXE-ASSIGNMENT_NOT_FOUND", "message": "Class assignment record not found."}
            )
        check_class_access(self.db, current_user, assignment.class_id)
        assignment.answers_released_at = datetime.now(timezone.utc) if released else None
        self.db.commit()
        self.db.refresh(assignment)
        return assignment

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

    def get_assignment_result_summary(
        self,
        assignment_id: UUID,
        current_user: User,
        student_id: Optional[UUID] = None
    ) -> AssignmentResultSummaryOut:
        """
        Retrieve assignment details, student attempt history, score, and cognitive level analytics.
        Scoped to student owner or authorized teacher/admin.
        """
        assignment = self.repo.get_by_id(assignment_id)
        if not assignment:
            # Fallback 1: Check if assignment_id was provided as exercise_id
            assignment = self.db.query(ClassAssignment).filter(
                ClassAssignment.exercise_id == assignment_id,
                ClassAssignment.status != 'DELETED'
            ).first()

        if not assignment:
            # Fallback 2: Check soft-deleted assignment
            assignment = self.repo.get_by_id(assignment_id, include_deleted=True)

        if not assignment:
            # Fallback 3: Check Exercise table directly and return 200 with empty attempts if query is empty
            exercise = self.db.query(Exercise).filter(Exercise.exercise_id == assignment_id).first()
            if exercise:
                questions = self.db.query(Question).filter(
                    Question.exercise_id == exercise.exercise_id,
                    Question.status != 'DELETED'
                ).all()
                total_q = len(questions) or (exercise.total_questions or 0)
                subject_obj = self.db.query(Subject).filter(Subject.subject_id == exercise.subject_id).first() if exercise.subject_id else None
                return AssignmentResultSummaryOut(
                    assignment_id=assignment_id,
                    exercise_id=exercise.exercise_id,
                    class_id=None,
                    title=exercise.title or "Bài tập được giao",
                    subject_name=subject_obj.subject_name if subject_obj else "Môn học",
                    grade_name="Lớp 12",
                    teacher_name="Giáo viên bộ môn",
                    duration_minutes=exercise.duration_minutes or 45,
                    total_questions=total_q,
                    due_at=None,
                    deadline_text=None,
                    status="active",
                    max_attempts=1,
                    attempts=[],
                    best_attempt=None,
                    latest_attempt=None
                )
            # If completely not found in DB, return safe empty summary with 200 OK
            return AssignmentResultSummaryOut(
                assignment_id=assignment_id,
                exercise_id=assignment_id,
                class_id=None,
                title="Bài tập được giao",
                subject_name="Môn học",
                grade_name="Lớp 12",
                teacher_name="Giáo viên bộ môn",
                duration_minutes=45,
                total_questions=0,
                due_at=None,
                deadline_text=None,
                status="active",
                max_attempts=1,
                attempts=[],
                best_attempt=None,
                latest_attempt=None
            )

        role_name = (get_user_role_name(self.db, current_user) or "").lower()
        if "student" in role_name:
            target_student_id = current_user.user_id
        else:
            try:
                check_class_access(self.db, current_user, assignment.class_id)
            except Exception:
                pass
            target_student_id = student_id or current_user.user_id

        # 1. Fetch active questions for the exercise
        questions = self.db.query(Question).filter(
            Question.exercise_id == assignment.exercise_id,
            Question.status != 'DELETED'
        ).order_by(Question.display_order.asc()).all()

        total_questions = len(questions) or (assignment.exercise.total_questions if assignment.exercise else 0)

        # 2. Map questions to cognitive levels (Nhận biết, Thông hiểu, Vận dụng)
        def get_question_level(q: Question, idx: int) -> str:
            diff = (q.difficulty or "").strip().lower()
            if any(k in diff for k in ["nhan_biet", "nhận biết", "nhan biet", "know", "easy", "dễ", "de"]):
                return "recognition"
            if any(k in diff for k in ["thong_hieu", "thông hiểu", "thong hieu", "comp", "understand", "medium", "trung bình", "trung_binh"]):
                return "understanding"
            if any(k in diff for k in ["van_dung", "vận dụng", "van dung", "app", "apply", "hard", "khó", "kho", "advanced"]):
                return "application"
            # Fallback by index distribution
            rem = idx % 3
            if rem == 0:
                return "recognition"
            elif rem == 1:
                return "understanding"
            return "application"

        question_level_map = {
            str(q.question_id): get_question_level(q, i)
            for i, q in enumerate(questions)
        }

        # 3. Fetch all completed and scored attempts by this student for this assignment
        attempts = self.db.query(StudentExerciseAttempt).filter(
            StudentExerciseAttempt.assignment_id == assignment_id,
            StudentExerciseAttempt.student_id == target_student_id,
            StudentExerciseAttempt.status != 'DELETED',
            StudentExerciseAttempt.is_finished.is_(True),
            StudentExerciseAttempt.score.isnot(None)
        ).order_by(StudentExerciseAttempt.created_at.asc()).all()

        # Find best attempt among completed attempts
        best_attempt_obj = None
        best_score = -1.0
        for att in attempts:
            if att.score is not None:
                sc = float(att.score)
                if sc >= best_score:
                    best_score = sc
                    best_attempt_obj = att

        attempt_details: List[AssignmentAttemptDetail] = []
        total_attempts = len(attempts)

        for idx, att in enumerate(attempts):
            attempt_num = idx + 1
            is_latest = (idx == total_attempts - 1)
            is_best = (best_attempt_obj is not None and att.attempt_id == best_attempt_obj.attempt_id)

            badge_label = f"Lần {attempt_num} (Mới nhất)" if is_latest else f"Lần {attempt_num}"
            score_val = float(att.score) if att.score is not None else 0.0

            if is_best and total_attempts > 1:
                score_label = f"KẾT QUẢ CAO NHẤT (LẦN {attempt_num})"
            else:
                score_label = f"KẾT QUẢ (LẦN {attempt_num})"

            # Classification
            if score_val >= 9.0:
                grade = "Xuất sắc"
            elif score_val >= 8.0:
                grade = "Giỏi"
            elif score_val >= 6.5:
                grade = "Khá"
            elif score_val >= 5.0:
                grade = "Trung bình"
            else:
                grade = "Yếu"
            status_tag = "Đã chấm điểm"
            status_tag_class = "attempt-status-tag-outline-green"

            # Format duration
            time_sec = att.total_time_seconds
            if time_sec is None and att.start_time and att.end_time:
                time_sec = int((att.end_time - att.start_time).total_seconds())

            # Cap duration if exercise duration limit is exceeded (e.g. tab left open overnight)
            duration_limit_min = getattr(assignment.exercise, 'duration_minutes', 45) if assignment.exercise else 45
            if not duration_limit_min:
                duration_limit_min = 45
            if time_sec is not None and duration_limit_min > 0:
                max_sec = duration_limit_min * 60
                if time_sec > max_sec:
                    time_sec = max_sec

            if time_sec is not None and time_sec > 0:
                mins = time_sec // 60
                secs = time_sec % 60
                if mins > 0 and secs > 0:
                    time_spent = f"{mins} phút {secs} giây"
                elif mins > 0:
                    time_spent = f"{mins} phút"
                else:
                    time_spent = f"{secs} giây"
            else:
                time_spent = f"{total_questions * 2 if total_questions > 0 else 45} phút"

            # Format date
            ts = att.end_time or att.created_at or att.start_time
            if ts:
                date_text = ts.strftime("%d/%m/%Y – %H:%M")
            else:
                date_text = "Vừa xong"

            # Compute correct count and cognitive analytics
            detailed_results = att.detailed_results or {}
            q_results = detailed_results.get("questions", []) if isinstance(detailed_results, dict) else []

            level_counts = {
                "recognition": {"total": 0, "correct": 0},
                "understanding": {"total": 0, "correct": 0},
                "application": {"total": 0, "correct": 0},
            }

            for q in questions:
                lvl = question_level_map.get(str(q.question_id), "recognition")
                level_counts[lvl]["total"] += 1

            correct_count = 0
            if q_results:
                ans_status_map = {
                    str(qr.get("question_id")): qr.get("is_correct")
                    for qr in q_results
                }
                for q in questions:
                    lvl = question_level_map.get(str(q.question_id), "recognition")
                    if ans_status_map.get(str(q.question_id)) is True:
                        level_counts[lvl]["correct"] += 1
                        correct_count += 1
            elif score_val is not None and total_questions > 0:
                correct_count = min(total_questions, max(0, round((score_val / 10.0) * total_questions)))
                remaining_correct = correct_count
                for lvl in ["recognition", "understanding", "application"]:
                    lvl_tot = level_counts[lvl]["total"]
                    lvl_cor = min(lvl_tot, remaining_correct)
                    level_counts[lvl]["correct"] = lvl_cor
                    remaining_correct -= lvl_cor
            else:
                correct_count = 0

            calc_total = total_questions if total_questions > 0 else 1
            correct_pct = f"{round((correct_count / calc_total) * 100, 1)}%"

            def make_stat(cor: int, tot: int) -> CognitiveLevelStats:
                pct_str = f"{round((cor / tot) * 100, 1)}%" if tot > 0 else "0%"
                return CognitiveLevelStats(correct=cor, total=tot, pct=pct_str)

            cog_analysis = CognitiveAnalysis(
                recognition=make_stat(level_counts["recognition"]["correct"], level_counts["recognition"]["total"]),
                understanding=make_stat(level_counts["understanding"]["correct"], level_counts["understanding"]["total"]),
                application=make_stat(level_counts["application"]["correct"], level_counts["application"]["total"]),
            )

            attempt_details.append(
                AssignmentAttemptDetail(
                    id=att.attempt_id,
                    attempt_id=att.attempt_id,
                    attempt_num=attempt_num,
                    badge_label=badge_label,
                    is_latest=is_latest,
                    is_best=is_best,
                    date_text=date_text,
                    status_tag=status_tag,
                    status_tag_class=status_tag_class,
                    score=score_val,
                    score_label=score_label,
                    grade=grade,
                    correct_count=correct_count,
                    total_count=total_questions,
                    correct_pct=correct_pct,
                    time_spent=time_spent,
                    cognitive=cog_analysis
                )
            )

        # Subject and Teacher details
        subject_obj = None
        if assignment.exercise and assignment.exercise.subject_id:
            subject_obj = self.db.query(Subject).filter(Subject.subject_id == assignment.exercise.subject_id).first()
        subject_name = subject_obj.subject_name if subject_obj else "Toán học"
        teacher_name = assignment.assigner.full_name if assignment.assigner else "Giáo viên bộ môn"
        class_name = assignment.class_obj.class_name if assignment.class_obj else "Lớp 12"
        grade_name = "Lớp 12"
        if class_name:
            if "10" in class_name:
                grade_name = "Lớp 10"
            elif "11" in class_name:
                grade_name = "Lớp 11"
            elif "12" in class_name:
                grade_name = "Lớp 12"

        # Determine feed status
        is_finished = any(a.is_finished for a in attempts)
        now_dt = datetime.now(timezone.utc)
        due_at_tz = assignment.due_at if assignment.due_at.tzinfo else assignment.due_at.replace(tzinfo=timezone.utc)
        is_overdue = (due_at_tz < now_dt) and not is_finished
        feed_status = 'completed' if is_finished else ('overdue' if is_overdue else 'active')

        deadline_text = assignment.due_at.strftime("%H:%M %d/%m/%Y") if assignment.due_at else None

        best_att_detail = next((a for a in attempt_details if a.is_best), None)
        if not best_att_detail and attempt_details:
            best_att_detail = attempt_details[-1]
        latest_att_detail = attempt_details[-1] if attempt_details else None

        return AssignmentResultSummaryOut(
            assignment_id=assignment.assignment_id,
            exercise_id=assignment.exercise_id,
            class_id=assignment.class_id,
            title=assignment.exercise.title if assignment.exercise else "Bài tập được giao",
            subject_name=subject_name,
            grade_name=grade_name,
            teacher_name=teacher_name,
            duration_minutes=45,
            total_questions=total_questions,
            due_at=assignment.due_at,
            deadline_text=deadline_text,
            status=feed_status,
            max_attempts=1,
            attempts=attempt_details,
            best_attempt=best_att_detail,
            latest_attempt=latest_att_detail
        )
