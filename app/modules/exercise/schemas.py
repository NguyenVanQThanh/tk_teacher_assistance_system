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
    content: str = Field(..., min_length=1, description="Nội dung đáp án")
    is_correct: bool = Field(False, description="Đáp án đúng hay sai")
    display_order: int = Field(0, description="Thứ tự hiển thị")

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Nội dung đáp án không được để trống.")
        return v


class AnswerOptionOut(BaseModel):
    option_id: UUID
    question_id: UUID
    content: str
    is_correct: bool
    display_order: int

    model_config = {"from_attributes": True}


class QuestionCreate(BaseModel):
    content: str = Field(..., min_length=1, description="Nội dung câu hỏi")
    question_type: QuestionTypeEnum = Field(QuestionTypeEnum.MultipleChoice, description="Loại câu hỏi")
    difficulty: Optional[DifficultyEnum] = Field(None, description="Độ khó câu hỏi")
    correct_answer: Optional[str] = Field(None, description="Đáp án cho câu hỏi tự luận ngắn")
    explanation: Optional[str] = Field(None, description="Lời giải chi tiết")
    display_order: int = Field(0, description="Thứ tự câu trong đề")
    document_id: Optional[UUID] = Field(None, description="ID tài liệu gốc nếu có")
    answer_options: Optional[List[AnswerOptionCreate]] = Field(default=None, description="Danh sách đáp án lựa chọn")

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Nội dung câu hỏi không được để trống.")
        return v

    @model_validator(mode="after")
    def validate_answer_options_for_multiple_choice(self):
        if self.question_type == QuestionTypeEnum.MultipleChoice:
            options = self.answer_options or []
            if len(options) < 2:
                raise ValueError("Câu hỏi trắc nghiệm (MultipleChoice) phải có ít nhất 2 đáp án lựa chọn.")
            correct_count = sum(1 for opt in options if opt.is_correct)
            if correct_count != 1:
                raise ValueError(f"Câu hỏi trắc nghiệm phải có đúng 1 đáp án đúng (hiện tại có {correct_count} đáp án đúng).")
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
                raise ValueError("Nội dung câu hỏi không được để trống.")
            return v
        return v

    @model_validator(mode="after")
    def validate_answer_options_if_provided(self):
        if self.question_type == QuestionTypeEnum.MultipleChoice and self.answer_options is not None:
            options = self.answer_options
            if len(options) < 2:
                raise ValueError("Câu hỏi trắc nghiệm (MultipleChoice) phải có ít nhất 2 đáp án lựa chọn.")
            correct_count = sum(1 for opt in options if opt.is_correct)
            if correct_count != 1:
                raise ValueError(f"Câu hỏi trắc nghiệm phải có đúng 1 đáp án đúng (hiện tại có {correct_count} đáp án đúng).")
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
    title: str = Field(..., min_length=1, max_length=255, description="Tiêu đề đề bài tập")
    subject_id: UUID = Field(..., description="ID môn học")
    ai_metadata: Optional[Any] = Field(None, description="Metadata cho AI sinh câu hỏi")

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Tiêu đề đề bài tập không được để trống.")
        return v


class ExerciseUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255, description="Tiêu đề mới")
    ai_metadata: Optional[Any] = Field(None, description="Metadata mới")

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Tiêu đề đề bài tập không được để trống.")
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
    exercise_id: UUID = Field(..., description="ID đề bài tập")
    due_at: datetime = Field(..., description="Hạn nộp bài tập")

    @field_validator("due_at")
    @classmethod
    def validate_due_at(cls, v: datetime) -> datetime:
        now = datetime.now(v.tzinfo) if v.tzinfo else datetime.now()
        if v <= now:
            raise ValueError("Hạn nộp bài tập (due_at) phải là một mốc thời gian trong tương lai.")
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

