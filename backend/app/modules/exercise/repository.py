# File Name: repository.py
# Description: Data Access Layer (Repository) for Exercise, Question, and AnswerOption models.
# Created At: 2026-07-31
# Created By: Tam Khang
# Updated At: 2026-07-31
# Updated By: Tam Khang

from typing import List, Optional, Any, Tuple, Dict
from uuid import UUID
from datetime import datetime
import base64
from fastapi import HTTPException, status
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session, joinedload
from models.models import User, Exercise, Question, AnswerOption, ClassAssignment, StudentExerciseAttempt



class ExerciseRepository:
    """Repository handling database operations for Exercise model."""

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def encode_cursor(created_at: datetime, exercise_id: UUID) -> str:
        """Encodes created_at and exercise_id into URL-safe base64 cursor token."""
        token = f"{created_at.isoformat()}|{str(exercise_id)}"
        return base64.urlsafe_b64encode(token.encode("utf-8")).decode("utf-8")

    @staticmethod
    def decode_cursor(cursor_str: str) -> Tuple[datetime, UUID]:
        """Decodes URL-safe base64 cursor token into created_at and exercise_id."""
        try:
            raw = base64.urlsafe_b64decode(cursor_str.encode("utf-8")).decode("utf-8")
            dt_str, id_str = raw.split("|", 1)
            return datetime.fromisoformat(dt_str), UUID(id_str)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "ERR-EXE-INVALID_CURSOR", "message": "Invalid pagination cursor."}
            )

    def create(self, exercise: Exercise) -> Exercise:
        """Create a new Exercise record in the database."""
        self.db.add(exercise)
        self.db.commit()
        self.db.refresh(exercise)
        return exercise

    def get_by_id(self, exercise_id: UUID, include_deleted: bool = False) -> Optional[Exercise]:
        """Retrieve an Exercise by ID with joined questions and answer options."""
        query = self.db.query(Exercise).options(
            joinedload(Exercise.questions).joinedload(Question.answer_options)
        ).filter(Exercise.exercise_id == exercise_id)
        
        if not include_deleted:
            query = query.filter(Exercise.status != 'DELETED')
        return query.first()

    def list_exercises(
        self,
        subject_ids: Optional[List[UUID]] = None,
        created_by: Optional[UUID] = None,
        status: Optional[str] = "ACTIVE",
        search: Optional[str] = None,
        cursor: Optional[str] = None,
        direction: str = "next",
        page_size: int = 6,
    ) -> Dict[str, Any]:
        """
        List exercises using Keyset / Cursor-based Pagination (zero OFFSET) for O(1) query performance.
        Keyset tuple: (created_at DESC, exercise_id DESC)
        """
        base_query = self.db.query(Exercise)
        if status is not None:
            base_query = base_query.filter(Exercise.status == status)
        
        if created_by and subject_ids is not None:
            base_query = base_query.filter(
                (Exercise.created_by == created_by) | (Exercise.subject_id.in_(subject_ids))
            )
        elif created_by:
            base_query = base_query.filter(Exercise.created_by == created_by)
        elif subject_ids is not None:
            base_query = base_query.filter(Exercise.subject_id.in_(subject_ids))

        if search:
            search_clean = search.strip()
            if search_clean:
                base_query = base_query.filter(Exercise.title.ilike(f"%{search_clean}%"))

        total = base_query.count()

        item_query = base_query.options(
            joinedload(Exercise.questions).joinedload(Question.answer_options)
        )

        # Apply Keyset cursor condition (ZERO OFFSET)
        if cursor:
            cursor_dt, cursor_id = self.decode_cursor(cursor)
            if direction == "prev":
                # Moving backwards (newer items)
                item_query = item_query.filter(
                    or_(
                        Exercise.created_at > cursor_dt,
                        and_(Exercise.created_at == cursor_dt, Exercise.exercise_id > cursor_id)
                    )
                ).order_by(Exercise.created_at.asc(), Exercise.exercise_id.asc())
            else:
                # Moving forwards (older items)
                item_query = item_query.filter(
                    or_(
                        Exercise.created_at < cursor_dt,
                        and_(Exercise.created_at == cursor_dt, Exercise.exercise_id < cursor_id)
                    )
                ).order_by(Exercise.created_at.desc(), Exercise.exercise_id.desc())
        else:
            item_query = item_query.order_by(Exercise.created_at.desc(), Exercise.exercise_id.desc())

        # Fetch page_size + 1 items to check has_more without an extra count query
        fetched_items = item_query.limit(page_size + 1).all()

        if direction == "prev":
            fetched_items.reverse()

        has_more = len(fetched_items) > page_size
        items = fetched_items[:page_size]

        next_cursor = None
        prev_cursor = None

        if items:
            if has_more and direction == "next":
                last_item = items[-1]
                next_cursor = self.encode_cursor(last_item.created_at, last_item.exercise_id)
            elif cursor and direction == "prev":
                last_item = items[-1]
                next_cursor = self.encode_cursor(last_item.created_at, last_item.exercise_id)

            first_item = items[0]
            if cursor or direction == "prev":
                prev_cursor = self.encode_cursor(first_item.created_at, first_item.exercise_id)

        return {
            "items": items,
            "page_size": page_size,
            "next_cursor": next_cursor,
            "prev_cursor": prev_cursor,
            "has_more": has_more,
            "total": total
        }

    def update(self, exercise: Exercise, title: Optional[str] = None, ai_metadata: Optional[dict] = None) -> Exercise:
        """Update title or AI metadata of an Exercise."""
        if title is not None:
            exercise.title = title
        if ai_metadata is not None:
            exercise.ai_metadata = ai_metadata
        self.db.commit()
        self.db.refresh(exercise)
        return exercise

    def soft_delete(self, exercise: Exercise) -> Exercise:
        """Soft-delete an Exercise by setting its status to DELETED."""
        exercise.status = 'DELETED'
        self.db.commit()
        self.db.refresh(exercise)
        return exercise

    def restore(self, exercise: Exercise) -> Exercise:
        """Restore a soft-deleted Exercise back to ACTIVE status."""
        exercise.status = 'ACTIVE'
        self.db.commit()
        self.db.refresh(exercise)
        return exercise

    def update_total_questions(self, exercise_id: UUID) -> None:
        """Recalculate and update active total_questions count for an Exercise."""
        count = self.db.query(Question).filter(
            Question.exercise_id == exercise_id,
            Question.status != 'DELETED'
        ).count()
        exercise = self.get_by_id(exercise_id, include_deleted=True)
        if exercise:
            exercise.total_questions = count
            self.db.commit()


class QuestionRepository:
    """Repository handling database operations for Question and AnswerOption models."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, question_id: UUID, include_deleted: bool = False) -> Optional[Question]:
        """Retrieve a Question by ID with joined answer options."""
        query = self.db.query(Question).options(
            joinedload(Question.answer_options)
        ).filter(Question.question_id == question_id)
        
        if not include_deleted:
            query = query.filter(Question.status != 'DELETED')
        return query.first()

    def create(self, question: Question, answer_options: Optional[List[AnswerOption]] = None) -> Question:
        """Create a new Question record along with associated AnswerOptions."""
        self.db.add(question)
        self.db.flush()
        if answer_options:
            for opt in answer_options:
                opt.question_id = question.question_id
                self.db.add(opt)
        self.db.commit()
        self.db.refresh(question)
        return question

    def update(
        self,
        question: Question,
        content: Optional[str] = None,
        content_markdown: Optional[str] = None,
        content_latex: Optional[str] = None,
        segments: Optional[Any] = None,
        confidence_score: Optional[float] = None,
        needs_review: Optional[bool] = None,
        question_type: Optional[str] = None,
        difficulty: Optional[str] = None,
        correct_answer: Optional[str] = None,
        explanation: Optional[str] = None,
        display_order: Optional[int] = None,
        image_url: Optional[str] = None,
        answer_options: Optional[List[AnswerOption]] = None
    ) -> Question:
        """Update Question fields and replace associated AnswerOptions if provided."""
        if content is not None:
            question.content = content
        if content_markdown is not None:
            question.content_markdown = content_markdown
        if content_latex is not None:
            question.content_latex = content_latex
        if segments is not None:
            question.segments = segments
        if confidence_score is not None:
            question.confidence_score = confidence_score
        if needs_review is not None:
            question.needs_review = needs_review
        if question_type is not None:
            question.question_type = question_type
        if difficulty is not None:
            question.difficulty = difficulty
        if correct_answer is not None:
            question.correct_answer = correct_answer
        if explanation is not None:
            question.explanation = explanation
        if display_order is not None:
            question.display_order = display_order
        if image_url is not None:
            question.image_url = image_url
        
        if answer_options is not None:
            self.db.query(AnswerOption).filter(AnswerOption.question_id == question.question_id).delete()
            self.db.flush()
            for opt in answer_options:
                opt.question_id = question.question_id
                self.db.add(opt)

        self.db.commit()
        self.db.refresh(question)
        return question

    def soft_delete(self, question: Question) -> Question:
        """Soft-delete a Question by setting its status to DELETED."""
        question.status = 'DELETED'
        self.db.commit()
        self.db.refresh(question)
        return question


class AssignmentRepository:
    """Repository handling database operations for ClassAssignment model."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, assignment: ClassAssignment) -> ClassAssignment:
        """Create a new ClassAssignment record in the database."""
        self.db.add(assignment)
        self.db.commit()
        self.db.refresh(assignment)
        return assignment

    def get_by_id(self, assignment_id: UUID, include_deleted: bool = False) -> Optional[ClassAssignment]:
        """Retrieve a ClassAssignment by ID."""
        query = self.db.query(ClassAssignment).filter(ClassAssignment.assignment_id == assignment_id)
        if not include_deleted:
            query = query.filter(ClassAssignment.status != 'DELETED')
        return query.first()

    def find_active_by_class_and_exercise(self, class_id: UUID, exercise_id: UUID) -> Optional[ClassAssignment]:
        """Find active assignment for a given class and exercise."""
        return self.db.query(ClassAssignment).filter(
            ClassAssignment.class_id == class_id,
            ClassAssignment.exercise_id == exercise_id,
            ClassAssignment.status != 'DELETED'
        ).first()

    def list_by_class_ids(self, class_ids: List[UUID], include_deleted: bool = False) -> List[ClassAssignment]:
        """List assignments for given class IDs ordered by assigned_at descending."""
        if not class_ids:
            return []
        query = self.db.query(ClassAssignment).options(
            joinedload(ClassAssignment.exercise)
        ).filter(ClassAssignment.class_id.in_(class_ids))
        if not include_deleted:
            query = query.filter(ClassAssignment.status != 'DELETED')
        return query.order_by(ClassAssignment.assigned_at.desc()).all()

    def soft_delete(self, assignment: ClassAssignment) -> ClassAssignment:
        """Soft-delete a ClassAssignment by setting its status to DELETED."""
        assignment.status = 'DELETED'
        self.db.commit()
        self.db.refresh(assignment)
        return assignment

    def restore(self, assignment: ClassAssignment) -> ClassAssignment:
        """Restore a soft-deleted ClassAssignment back to ACTIVE status."""
        assignment.status = 'ACTIVE'
        self.db.commit()
        self.db.refresh(assignment)
        return assignment

    def has_attempts(self, assignment_id: UUID) -> bool:
        """Check if any active student attempts exist for this assignment."""
        count = self.db.query(StudentExerciseAttempt).filter(
            StudentExerciseAttempt.assignment_id == assignment_id,
            StudentExerciseAttempt.status != 'DELETED'
        ).count()
        return count > 0


class AttemptRepository:
    """Repository handling database operations for StudentExerciseAttempt model."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, attempt: StudentExerciseAttempt) -> StudentExerciseAttempt:
        """Create a new StudentExerciseAttempt record."""
        self.db.add(attempt)
        self.db.commit()
        self.db.refresh(attempt)
        return attempt

    def get_by_id(self, attempt_id: UUID, include_deleted: bool = False) -> Optional[StudentExerciseAttempt]:
        """Retrieve a StudentExerciseAttempt by ID."""
        query = self.db.query(StudentExerciseAttempt).filter(StudentExerciseAttempt.attempt_id == attempt_id)
        if not include_deleted:
            query = query.filter(StudentExerciseAttempt.status != 'DELETED')
        return query.first()

    def find_open_attempt(self, student_id: UUID, assignment_id: UUID) -> Optional[StudentExerciseAttempt]:
        """Find an unsubmitted (is_finished=False) active attempt for a student and assignment."""
        return self.db.query(StudentExerciseAttempt).filter(
            StudentExerciseAttempt.student_id == student_id,
            StudentExerciseAttempt.assignment_id == assignment_id,
            StudentExerciseAttempt.is_finished == False,
            StudentExerciseAttempt.status != 'DELETED'
        ).first()

    def update(self, attempt: StudentExerciseAttempt) -> StudentExerciseAttempt:
        """Commit changes to an existing StudentExerciseAttempt."""
        self.db.commit()
        self.db.refresh(attempt)
        return attempt

    def list_attempts(
        self,
        class_ids: Optional[List[UUID]] = None,
        assignment_id: Optional[UUID] = None,
        student_id: Optional[UUID] = None,
        is_finished: Optional[bool] = None,
        search: Optional[str] = None,
        include_deleted: bool = False
    ) -> List[StudentExerciseAttempt]:
        """List attempts with joins on student, assignment, class, and exercise."""
        query = self.db.query(StudentExerciseAttempt).join(
            StudentExerciseAttempt.assignment
        ).join(
            StudentExerciseAttempt.student
        ).options(
            joinedload(StudentExerciseAttempt.student),
            joinedload(StudentExerciseAttempt.assignment).joinedload(ClassAssignment.class_obj),
            joinedload(StudentExerciseAttempt.assignment).joinedload(ClassAssignment.exercise)
        )

        if not include_deleted:
            query = query.filter(
                StudentExerciseAttempt.status != 'DELETED',
                ClassAssignment.status != 'DELETED'
            )

        if class_ids is not None:
            if not class_ids:
                return []
            query = query.filter(ClassAssignment.class_id.in_(class_ids))

        if assignment_id:
            query = query.filter(StudentExerciseAttempt.assignment_id == assignment_id)

        if student_id:
            query = query.filter(StudentExerciseAttempt.student_id == student_id)

        if is_finished is not None:
            query = query.filter(StudentExerciseAttempt.is_finished == is_finished)

        if search and search.strip():
            term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    User.full_name.ilike(term),
                    User.phone.ilike(term)
                )
            )

        return query.order_by(StudentExerciseAttempt.created_at.desc()).all()

    def update_grade(
        self,
        attempt: StudentExerciseAttempt,
        score: float,
        feedback: Optional[str] = None,
        detailed_results: Optional[Any] = None,
        status: Optional[str] = None
    ) -> StudentExerciseAttempt:
        """Update score, feedback, status and detailed_results on an attempt."""
        attempt.score = score
        if status:
            attempt.status = status
        else:
            attempt.status = 'approved'

        if detailed_results is not None:
            attempt.detailed_results = detailed_results
        elif feedback is not None:
            curr_results = dict(attempt.detailed_results or {})
            curr_results["teacher_feedback"] = feedback
            attempt.detailed_results = curr_results

        self.db.commit()
        self.db.refresh(attempt)
        return attempt


