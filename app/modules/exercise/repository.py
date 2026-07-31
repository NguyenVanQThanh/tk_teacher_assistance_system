# File Name: repository.py
# Description: Data Access Layer (Repository) for Exercise, Question, and AnswerOption models.
# Created At: 2026-07-31
# Created By: Tam Khang
# Updated At: 2026-07-31
# Updated By: Tam Khang

from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session, joinedload
from models.models import Exercise, Question, AnswerOption, ClassAssignment


class ExerciseRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(self, exercise: Exercise) -> Exercise:
        self.db.add(exercise)
        self.db.commit()
        self.db.refresh(exercise)
        return exercise

    def get_by_id(self, exercise_id: UUID, include_deleted: bool = False) -> Optional[Exercise]:
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
        if title is not None:
            exercise.title = title
        if ai_metadata is not None:
            exercise.ai_metadata = ai_metadata
        self.db.commit()
        self.db.refresh(exercise)
        return exercise

    def soft_delete(self, exercise: Exercise) -> Exercise:
        exercise.status = 'DELETED'
        self.db.commit()
        self.db.refresh(exercise)
        return exercise

    def restore(self, exercise: Exercise) -> Exercise:
        exercise.status = 'ACTIVE'
        self.db.commit()
        self.db.refresh(exercise)
        return exercise

    def update_total_questions(self, exercise_id: UUID) -> None:
        count = self.db.query(Question).filter(
            Question.exercise_id == exercise_id,
            Question.status != 'DELETED'
        ).count()
        exercise = self.get_by_id(exercise_id, include_deleted=True)
        if exercise:
            exercise.total_questions = count
            self.db.commit()


class QuestionRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, question_id: UUID, include_deleted: bool = False) -> Optional[Question]:
        query = self.db.query(Question).options(
            joinedload(Question.answer_options)
        ).filter(Question.question_id == question_id)
        
        if not include_deleted:
            query = query.filter(Question.status != 'DELETED')
        return query.first()

    def create(self, question: Question, answer_options: Optional[List[AnswerOption]] = None) -> Question:
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
        question.status = 'DELETED'
        self.db.commit()
        self.db.refresh(question)
        return question


class AssignmentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, assignment: ClassAssignment) -> ClassAssignment:
        self.db.add(assignment)
        self.db.commit()
        self.db.refresh(assignment)
        return assignment

    def get_by_id(self, assignment_id: UUID, include_deleted: bool = False) -> Optional[ClassAssignment]:
        query = self.db.query(ClassAssignment).filter(ClassAssignment.assignment_id == assignment_id)
        if not include_deleted:
            query = query.filter(ClassAssignment.status != 'DELETED')
        return query.first()

    def find_active_by_class_and_exercise(self, class_id: UUID, exercise_id: UUID) -> Optional[ClassAssignment]:
        return self.db.query(ClassAssignment).filter(
            ClassAssignment.class_id == class_id,
            ClassAssignment.exercise_id == exercise_id,
            ClassAssignment.status != 'DELETED'
        ).first()

    def list_by_class_ids(self, class_ids: List[UUID], include_deleted: bool = False) -> List[ClassAssignment]:
        if not class_ids:
            return []
        query = self.db.query(ClassAssignment).filter(ClassAssignment.class_id.in_(class_ids))
        if not include_deleted:
            query = query.filter(ClassAssignment.status != 'DELETED')
        return query.order_by(ClassAssignment.assigned_at.desc()).all()

    def soft_delete(self, assignment: ClassAssignment) -> ClassAssignment:
        assignment.status = 'DELETED'
        self.db.commit()
        self.db.refresh(assignment)
        return assignment

    def restore(self, assignment: ClassAssignment) -> ClassAssignment:
        assignment.status = 'ACTIVE'
        self.db.commit()
        self.db.refresh(assignment)
        return assignment

    def has_attempts(self, assignment_id: UUID) -> bool:
        return False

