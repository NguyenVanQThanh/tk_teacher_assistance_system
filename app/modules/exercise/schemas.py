# File Name: schemas.py
# Description: Pydantic schemas for Exercise, Question, and AnswerOption CRUD & validation.
# Created At: 2026-07-31
# Created By: Tam Khang
# Updated At: 2026-07-31
# Updated By: Tam Khang

from enum import Enum
from uuid import UUID
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field, field_validator, model_validator


class QuestionTypeEnum(str, Enum):
    MultipleChoice = "MultipleChoice"
    ShortAnswer = "ShortAnswer"


class DifficultyEnum(str, Enum):
    NhanBiet = "NhanBiet"
    ThongHieu = "ThongHieu"
    VanDung = "VanDung"


class ExerciseStatusEnum(str, Enum):
    ACTIVE = "ACTIVE"
    DELETED = "DELETED"


class AnswerOptionCreate(BaseModel):
    content: str = Field(..., min_length=1, description="Option content text")
    is_correct: bool = Field(False, description="Whether option is correct")
    display_order: int = Field(0, description="Display order sequence")

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Option content cannot be empty.")
        return v


class AnswerOptionOut(BaseModel):
    option_id: UUID
    question_id: UUID
    content: str
    is_correct: bool
    display_order: int

    model_config = {"from_attributes": True}


class QuestionCreate(BaseModel):
    content: str = Field(..., min_length=1, description="Question content text")
    question_type: QuestionTypeEnum = Field(QuestionTypeEnum.MultipleChoice, description="Question type category")
    difficulty: Optional[DifficultyEnum] = Field(None, description="Question difficulty level")
    correct_answer: Optional[str] = Field(None, description="Correct answer for ShortAnswer questions")
    explanation: Optional[str] = Field(None, description="Detailed answer explanation")
    display_order: int = Field(0, description="Display order within exercise")
    document_id: Optional[UUID] = Field(None, description="Associated source document ID")
    answer_options: Optional[List[AnswerOptionCreate]] = Field(default=None, description="List of answer choices")

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Question content cannot be empty.")
        return v

    @model_validator(mode="after")
    def validate_answer_options_for_multiple_choice(self):
        if self.question_type == QuestionTypeEnum.MultipleChoice:
            options = self.answer_options or []
            if len(options) < 2:
                raise ValueError("MultipleChoice questions must have at least 2 answer options.")
            correct_count = sum(1 for opt in options if opt.is_correct)
            if correct_count != 1:
                raise ValueError(f"MultipleChoice questions must have exactly 1 correct answer (found {correct_count}).")
        return self


class QuestionUpdate(BaseModel):
    content: Optional[str] = Field(None, min_length=1)
    question_type: Optional[QuestionTypeEnum] = None
    difficulty: Optional[DifficultyEnum] = None
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None
    display_order: Optional[int] = None
    answer_options: Optional[List[AnswerOptionCreate]] = None

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Question content cannot be empty.")
            return v
        return v

    @model_validator(mode="after")
    def validate_answer_options_if_provided(self):
        if self.question_type == QuestionTypeEnum.MultipleChoice and self.answer_options is not None:
            options = self.answer_options
            if len(options) < 2:
                raise ValueError("MultipleChoice questions must have at least 2 answer options.")
            correct_count = sum(1 for opt in options if opt.is_correct)
            if correct_count != 1:
                raise ValueError(f"MultipleChoice questions must have exactly 1 correct answer (found {correct_count}).")
        return self


class QuestionOut(BaseModel):
    question_id: UUID
    exercise_id: UUID
    document_id: Optional[UUID] = None
    content: str
    question_type: str
    difficulty: Optional[str] = None
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None
    display_order: int
    is_ai_generated: bool
    status: str
    created_at: datetime
    updated_at: datetime
    answer_options: List[AnswerOptionOut] = []

    model_config = {"from_attributes": True}


class ExerciseCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Exercise title")
    subject_id: UUID = Field(..., description="Subject UUID")
    ai_metadata: Optional[Any] = Field(None, description="Metadata for AI generation")

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Exercise title cannot be empty.")
        return v


class ExerciseUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255, description="New exercise title")
    ai_metadata: Optional[Any] = Field(None, description="New AI metadata")

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Exercise title cannot be empty.")
            return v
        return v


class ExerciseOut(BaseModel):
    exercise_id: UUID
    title: str
    subject_id: UUID
    created_by: UUID
    total_questions: int
    ai_metadata: Optional[Any] = None
    status: str
    created_at: datetime
    updated_at: datetime
    questions: List[QuestionOut] = []

    model_config = {"from_attributes": True}


class AssignmentCreate(BaseModel):
    exercise_id: UUID = Field(..., description="Exercise UUID")
    due_at: datetime = Field(..., description="Assignment due date")

    @field_validator("due_at")
    @classmethod
    def validate_due_at(cls, v: datetime) -> datetime:
        now = datetime.now(v.tzinfo) if v.tzinfo else datetime.now()
        if v <= now:
            raise ValueError("Assignment due date (due_at) must be in the future.")
        return v


class AssignmentOut(BaseModel):
    assignment_id: UUID
    class_id: UUID
    exercise_id: UUID
    assigned_by: UUID
    assigned_at: Optional[datetime] = None
    due_at: datetime
    status: str

    model_config = {"from_attributes": True}


class AttemptStartOut(BaseModel):
    attempt_id: UUID
    assignment_id: UUID
    student_id: UUID
    start_time: Optional[datetime] = None
    is_finished: bool

    model_config = {"from_attributes": True}


class AnswerInput(BaseModel):
    question_id: UUID
    answer_option_id: Optional[UUID] = None
    answer_text: Optional[str] = None

    @model_validator(mode="after")
    def validate_answer_content(self):
        if self.answer_option_id is None and (self.answer_text is None or not self.answer_text.strip()):
            raise ValueError("Answer must provide either answer_option_id or non-empty answer_text.")
        return self


class AttemptSubmitRequest(BaseModel):
    answers: List[AnswerInput] = Field(default_factory=list, description="List of question answers")


class AttemptOut(BaseModel):
    attempt_id: UUID
    student_id: UUID
    assignment_id: UUID
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    total_time_seconds: Optional[int] = None
    score: Optional[float] = None
    detailed_results: Optional[Any] = None
    is_finished: bool
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


