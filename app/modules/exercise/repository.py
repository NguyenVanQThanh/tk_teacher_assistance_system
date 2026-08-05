# File Name: repository.py
# Description: Data Access Layer (Repository) for Exercise, Question, and AnswerOption models.
# Created At: 2026-07-31
# Created By: Tam Khang
# Updated At: 2026-07-31
# Updated By: Tam Khang

from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session, joinedload
from models.models import Exercise, Question, AnswerOption, ClassAssignment, StudentExerciseAttempt



class ExerciseRepository:
    """Repository handling database operations for Exercise model."""

    def __init__(self, db: Session):
        self.db = db

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
        status: Optional[str] = "ACTIVE"
    ) -> List[Exercise]:
        """List exercises filtered by status, subject IDs, or creator UUID."""
        query = self.db.query(Exercise).options(
            joinedload(Exercise.questions).joinedload(Question.answer_options)
        )
        if status is not None:
            query = query.filter(Exercise.status == status)
        
        if created_by and subject_ids is not None:
            query = query.filter(
                (Exercise.created_by == created_by) | (Exercise.subject_id.in_(subject_ids))
            )
        elif created_by:
            query = query.filter(Exercise.created_by == created_by)
        elif subject_ids is not None:
            query = query.filter(Exercise.subject_id.in_(subject_ids))
            
        return query.order_by(Exercise.created_at.desc()).all()

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
        question_type: Optional[str] = None,
        difficulty: Optional[str] = None,
        correct_answer: Optional[str] = None,
        explanation: Optional[str] = None,
        display_order: Optional[int] = None,
        answer_options: Optional[List[AnswerOption]] = None
    ) -> Question:
        """Update Question fields and replace associated AnswerOptions if provided."""
        if content is not None:
            question.content = content
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
        query = self.db.query(ClassAssignment).filter(ClassAssignment.class_id.in_(class_ids))
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


