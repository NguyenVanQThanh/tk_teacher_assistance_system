# File Name: schemas.py
# Description: Pydantic schemas for Exercise, Question, and AnswerOption CRUD & validation.
# Created At: 2026-07-31
# Created By: Tam Khang
# Updated At: 2026-08-09
# Updated By: Tam Khang

from enum import Enum
from uuid import UUID
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field, field_validator, model_validator


class QuestionTypeEnum(str, Enum):
    MultipleChoice = "MultipleChoice"
    TrueFalse = "TrueFalse"
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


class SegmentSchema(BaseModel):
    type: str = Field("text", description="Segment type: text, math, or image")
    content: Optional[str] = Field(None, description="Text content if type=text")
    latex: Optional[str] = Field(None, description="LaTeX string if type=math")
    display: bool = Field(False, description="Whether math is display/block style ($$) or inline ($)")
    confidence: Optional[float] = Field(None, description="OCR recognition confidence score (0.0 - 1.0)")
    bbox: Optional[List[float]] = Field(None, description="Bounding box coordinates [x0, y0, x1, y1]")


class QuestionCreate(BaseModel):
    content: str = Field(..., min_length=1, description="Question content text")
    content_markdown: Optional[str] = Field(None, description="Formatted plain Markdown text with converted Unicode math symbols")
    content_latex: Optional[str] = Field(None, description="Raw LaTeX math formula content")
    segments: Optional[List[SegmentSchema]] = Field(None, description="Structured content segments (text/math/image)")
    confidence_score: Optional[float] = Field(None, description="Average OCR confidence score")
    needs_review: bool = Field(False, description="Whether question needs teacher review/correction")
    question_type: QuestionTypeEnum = Field(QuestionTypeEnum.MultipleChoice, description="Question type category")
    difficulty: Optional[DifficultyEnum] = Field(None, description="Question difficulty level")
    correct_answer: Optional[str] = Field(None, description="Correct answer for ShortAnswer questions")
    explanation: Optional[str] = Field(None, description="Detailed answer explanation")
    display_order: int = Field(0, description="Display order within exercise")
    document_id: Optional[UUID] = Field(None, description="Associated source document ID")
    image_url: Optional[str] = Field(None, description="URL of question image")
    answer_options: Optional[List[AnswerOptionCreate]] = Field(default=None, description="List of answer choices")

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Question content cannot be empty.")
        return v

    @model_validator(mode="after")
    def validate_answer_options_for_type(self):
        if self.question_type == QuestionTypeEnum.MultipleChoice:
            options = self.answer_options or []
            if len(options) < 2:
                raise ValueError("MultipleChoice questions must have at least 2 answer options.")
            correct_count = sum(1 for opt in options if opt.is_correct)
            if correct_count != 1:
                raise ValueError(f"MultipleChoice questions must have exactly 1 correct answer (found {correct_count}).")
        elif self.question_type == QuestionTypeEnum.TrueFalse:
            options = self.answer_options or []
            if len(options) < 1:
                raise ValueError("TrueFalse questions must have at least 1 option item.")
        return self


class QuestionUpdate(BaseModel):
    content: Optional[str] = Field(None, min_length=1)
    content_markdown: Optional[str] = None
    content_latex: Optional[str] = None
    segments: Optional[List[SegmentSchema]] = None
    confidence_score: Optional[float] = None
    needs_review: Optional[bool] = None
    question_type: Optional[QuestionTypeEnum] = None
    difficulty: Optional[DifficultyEnum] = None
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None
    display_order: Optional[int] = None
    image_url: Optional[str] = None
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
    content_markdown: Optional[str] = None
    content_latex: Optional[str] = None
    segments: Optional[List[Any]] = None
    confidence_score: Optional[float] = None
    needs_review: bool = False
    question_type: str
    difficulty: Optional[str] = None
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None
    display_order: int
    image_url: Optional[str] = None
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


class PaginatedExerciseOut(BaseModel):
    items: List[ExerciseOut]
    total: int
    page: int
    page_size: int
    total_pages: int

    model_config = {"from_attributes": True}


class CursorPaginatedExerciseOut(BaseModel):
    items: List[ExerciseOut]
    page_size: int
    next_cursor: Optional[str] = None
    prev_cursor: Optional[str] = None
    has_more: bool
    total: int

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
    exercise_title: Optional[str] = None
    total_questions: Optional[int] = None

    @model_validator(mode="before")
    @classmethod
    def populate_exercise_fields(cls, data: Any) -> Any:
        if hasattr(data, "exercise") and data.exercise:
            return {
                "assignment_id": data.assignment_id,
                "class_id": data.class_id,
                "exercise_id": data.exercise_id,
                "assigned_by": data.assigned_by,
                "assigned_at": data.assigned_at,
                "due_at": data.due_at,
                "status": data.status,
                "exercise_title": data.exercise.title if hasattr(data.exercise, "title") else None,
                "total_questions": data.exercise.total_questions if hasattr(data.exercise, "total_questions") else None,
            }
        return data

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
    student_name: Optional[str] = None
    student_code: Optional[str] = None
    exercise_id: Optional[UUID] = None
    exercise_title: Optional[str] = None
    class_id: Optional[UUID] = None
    class_name: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    total_time_seconds: Optional[int] = None
    score: Optional[float] = None
    detailed_results: Optional[Any] = None
    is_finished: bool
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @model_validator(mode="before")
    @classmethod
    def populate_attempt_fields(cls, data: Any) -> Any:
        if hasattr(data, "student") and data.student:
            student_name = getattr(data.student, "full_name", None)
            student_code = getattr(data.student, "phone", None)
            exercise_id = None
            exercise_title = None
            class_id = None
            class_name = None
            if hasattr(data, "assignment") and data.assignment:
                class_id = data.assignment.class_id
                exercise_id = data.assignment.exercise_id
                if hasattr(data.assignment, "class_obj") and data.assignment.class_obj:
                    class_name = data.assignment.class_obj.class_name
                if hasattr(data.assignment, "exercise") and data.assignment.exercise:
                    exercise_title = data.assignment.exercise.title
            return {
                "attempt_id": data.attempt_id,
                "student_id": data.student_id,
                "assignment_id": data.assignment_id,
                "student_name": student_name,
                "student_code": student_code,
                "exercise_id": exercise_id,
                "exercise_title": exercise_title,
                "class_id": class_id,
                "class_name": class_name,
                "start_time": data.start_time,
                "end_time": data.end_time,
                "total_time_seconds": data.total_time_seconds,
                "score": data.score,
                "detailed_results": data.detailed_results,
                "is_finished": data.is_finished,
                "status": data.status,
                "created_at": data.created_at,
                "updated_at": data.updated_at,
            }
        return data

    model_config = {"from_attributes": True}


class AttemptListItemOut(BaseModel):
    attempt_id: UUID
    assignment_id: UUID
    student_id: UUID
    student_name: str
    student_code: Optional[str] = None
    class_id: UUID
    class_name: str
    exercise_id: UUID
    exercise_title: str
    subject_id: Optional[UUID] = None
    subject_name: Optional[str] = None
    score: Optional[float] = None
    is_finished: bool
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    total_time_seconds: Optional[int] = None
    status: str

    model_config = {"from_attributes": True}


class AttemptGradeUpdateRequest(BaseModel):
    score: float = Field(..., ge=0.0, le=10.0, description="Updated score from 0.0 to 10.0")
    feedback: Optional[str] = Field(None, max_length=2000, description="Teacher feedback / notes")
    detailed_results: Optional[Any] = Field(None, description="Optional updated detailed question results")



