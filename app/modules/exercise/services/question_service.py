# File Name: question_service.py
# Description: Service layer for Question and AnswerOption operations within exercises.
# Created At: 2026-07-31
# Created By: Tam Khang
# Updated At: 2026-07-31
# Updated By: Tam Khang

from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.models import User, Question, AnswerOption
from app.modules.exercise.schemas import QuestionCreate, QuestionUpdate
from app.modules.exercise.repository import QuestionRepository, ExerciseRepository
from app.modules.exercise.services.exercise_service import ExerciseService


class QuestionService:
    def __init__(self, db: Session):
        self.db = db
        self.question_repo = QuestionRepository(db)
        self.exercise_repo = ExerciseRepository(db)
        self.exercise_service = ExerciseService(db)

    def add_question(self, current_user: User, exercise_id: UUID, payload: QuestionCreate) -> Question:
        # 1. Verify access to exercise
        exercise = self.exercise_service.get_exercise_detail(current_user, exercise_id)

        # 2. Build Question model
        question = Question(
            exercise_id=exercise.exercise_id,
            document_id=payload.document_id,
            content=payload.content,
            question_type=payload.question_type.value if hasattr(payload.question_type, "value") else payload.question_type,
            difficulty=payload.difficulty.value if payload.difficulty and hasattr(payload.difficulty, "value") else payload.difficulty,
            correct_answer=payload.correct_answer,
            explanation=payload.explanation,
            display_order=payload.display_order,
            image_url=payload.image_url,
            is_ai_generated=False,
            status='ACTIVE'
        )

        # 3. Build AnswerOptions if present
        options = []
        if payload.answer_options:
            for idx, opt_in in enumerate(payload.answer_options):
                options.append(AnswerOption(
                    content=opt_in.content,
                    is_correct=opt_in.is_correct,
                    display_order=opt_in.display_order if opt_in.display_order != 0 else idx
                ))

        created_question = self.question_repo.create(question, answer_options=options)
        self.exercise_repo.update_total_questions(exercise_id)
        return created_question

    def update_question(self, current_user: User, question_id: UUID, payload: QuestionUpdate) -> Question:
        question = self.question_repo.get_by_id(question_id, include_deleted=False)
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "ERR-EXE-QUESTION_NOT_FOUND",
                    "message": "Question not found."
                }
            )

        # Verify exercise permission
        self.exercise_service.get_exercise_detail(current_user, question.exercise_id)

        options = None
        if payload.answer_options is not None:
            options = [
                AnswerOption(
                    content=opt_in.content,
                    is_correct=opt_in.is_correct,
                    display_order=opt_in.display_order if opt_in.display_order != 0 else idx
                )
                for idx, opt_in in enumerate(payload.answer_options)
            ]

        updated_question = self.question_repo.update(
            question=question,
            content=payload.content,
            question_type=payload.question_type.value if payload.question_type and hasattr(payload.question_type, "value") else payload.question_type,
            difficulty=payload.difficulty.value if payload.difficulty and hasattr(payload.difficulty, "value") else payload.difficulty,
            correct_answer=payload.correct_answer,
            explanation=payload.explanation,
            display_order=payload.display_order,
            image_url=payload.image_url,
            answer_options=options
        )
        return updated_question

    def delete_question(self, current_user: User, question_id: UUID) -> None:
        question = self.question_repo.get_by_id(question_id, include_deleted=False)
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "ERR-EXE-QUESTION_NOT_FOUND",
                    "message": "Question not found."
                }
            )

        # Verify exercise permission
        self.exercise_service.get_exercise_detail(current_user, question.exercise_id)

        self.question_repo.soft_delete(question)
        self.exercise_repo.update_total_questions(question.exercise_id)
