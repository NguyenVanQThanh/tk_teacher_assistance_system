# File Name: ai_exercise_service.py
# Description: Orchestrates AI exercise generation (teacher and student flows): context retrieval, LLM generation and persistence.
# Created At: 2026-11-13
# Created By: AI Agent
# Updated At: 2026-11-15
# Updated By: AI Agent

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core import config as app_config
from app.core.resource_limits import AI_GENERATE_ACQUIRE_TIMEOUT_SECONDS, AI_GENERATE_SEMAPHORE
from app.modules.academic.scoping import check_class_access, get_user_role_name
from app.modules.exercise.schemas import (
    AiExerciseGenerateOut, AiExerciseGenerateRequest, StudentAiGenerateRequest,
)
from app.modules.exercise.services.ai_generator_service import AiExerciseGeneratorService
from app.modules.exercise.services.rag_context_service import STUDENT_FILE_CHARS, RagContextService
from app.modules.exercise.services.rag_retrieval_service import RagRetrievalService, parse_grade
from models.models import (
    AnswerOption, Class, ClassAssignment, Exercise, Question, StudentClass, Subject, TeacherSubject, User,
)

logger = logging.getLogger("smartlms.exercise.ai_exercise")

MAX_TOTAL_QUESTIONS = 40
DEFAULT_DUE_DAYS = 14


def _err(code: int, error: str, message: str) -> HTTPException:
    return HTTPException(status_code=code, detail={"code": error, "message": message})


class AiExerciseService:
    """Shared generation and persistence used by the teacher and student flows."""

    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------ student helpers
    def _student_classes(self, student_id: uuid.UUID) -> List[Class]:
        """ACTIVE, non-deleted classes of the student."""
        return (
            self.db.query(Class)
            .join(StudentClass, StudentClass.class_id == Class.class_id)
            .filter(StudentClass.student_id == student_id, StudentClass.status == "ACTIVE",
                    Class.status != "DELETED")
            .order_by(Class.class_name)
            .all()
        )

    def _student_subject_context(self, user: User, subject_id: uuid.UUID) -> Tuple[Optional[Class], Subject]:
        """Return (class, subject) where the subject is taught in one of the student's classes; else 403/404.

        Guests have no class: any ACTIVE subject is allowed and the class is None.
        """
        if user.is_guest:
            subject = self.db.query(Subject).filter(
                Subject.subject_id == subject_id, Subject.status == "ACTIVE").first()
            if subject is None:
                raise _err(status.HTTP_404_NOT_FOUND, "ERR-ACAD-SUBJECT_NOT_FOUND", "Subject not found.")
            return None, subject
        classes = self._student_classes(user.user_id)
        if not classes:
            raise _err(status.HTTP_403_FORBIDDEN, "ERR-EXE-AI_NO_CLASS", "You are not enrolled in any class.")
        subject = self.db.query(Subject).filter(
            Subject.subject_id == subject_id, Subject.status != "DELETED").first()
        taught = None
        if subject is not None:
            for cls in classes:
                row = self.db.query(TeacherSubject.teacher_id).filter(
                    TeacherSubject.class_id == cls.class_id, TeacherSubject.subject_id == subject_id,
                    TeacherSubject.status == "ACTIVE").first()
                if row:
                    taught = cls
                    break
        if subject is None or taught is None:
            raise _err(status.HTTP_404_NOT_FOUND, "ERR-ACAD-SUBJECT_NOT_FOUND", "Subject not found.")
        return taught, subject

    def _enforce_guest_ai_limit(self, user: User) -> None:
        """Cap paid LLM generations per guest account; soft-deleted exercises still count."""
        if not user.is_guest:
            return
        used = self.db.query(func.count(Exercise.exercise_id)).filter(Exercise.created_by == user.user_id).scalar() or 0
        if used >= app_config.GUEST_AI_LIMIT:
            raise _err(status.HTTP_403_FORBIDDEN, "ERR-EXE-GUEST_AI_LIMIT",
                       "Guest accounts have reached the AI generation limit.")

    @staticmethod
    def _require_guest_grade(user: User, cls: Optional[Class], grade: Optional[int]) -> None:
        """Guests have no class, so the client must send the grade; fail clearly instead of an empty SGK filter."""
        if user.is_guest and cls is None and not grade:
            raise _err(status.HTTP_422_UNPROCESSABLE_ENTITY, "ERR-EXE-AI_GRADE_REQUIRED",
                       "Grade (10-12) is required for guest accounts.")

    def student_chapters(self, user: User, subject_id: uuid.UUID,
                         grade: Optional[int] = None) -> List[Dict[str, Any]]:
        """Chapters for a subject (grade parsed from the student's class name; guests pass `grade` 10-12)."""
        cls, subject = self._student_subject_context(user, subject_id)
        self._require_guest_grade(user, cls, grade)
        grade = parse_grade(cls.class_name) if cls is not None else grade
        doc_ids = RagRetrievalService.resolve_sgk_filter(self.db, subject.subject_name, grade)
        return RagRetrievalService.list_chapters(self.db, doc_ids)

    # ------------------------------------------------------------------ generation entry points
    def generate(self, user: User, payload: AiExerciseGenerateRequest) -> AiExerciseGenerateOut:
        """Teacher/Admin flow: class-wide assignment for a class the caller can access; nothing is auto-created."""
        self._enforce_guest_ai_limit(user)
        subject = self._resolve_teacher_subject(payload)
        # Guest teachers have no classes: the exercise lands in the bank without an assignment.
        class_obj = None if user.is_guest else self._resolve_teacher_class(user, subject, payload)
        grade_name = payload.grade_name or "Lớp 12"
        context, sources = RagContextService.build_context_with_sources(
            self.db,
            topic_prompt=payload.topic_prompt,
            subject_name=subject.subject_name,
            grade_name=grade_name,
            subject_id=subject.subject_id,
            role_name=get_user_role_name(self.db, user),
            class_id=class_obj.class_id if class_obj is not None else None,
            document_ids=payload.document_ids,
        )
        matrix = payload.matrix.as_dict() if payload.matrix else None
        counts = self._counts(matrix) if matrix else (payload.part1_count, payload.part2_count, payload.part3_count)
        questions = self._generate_guarded(
            subject_name=subject.subject_name, grade_name=grade_name, topic_prompt=payload.topic_prompt,
            counts=counts, context=context, matrix=matrix, student_file="")
        metadata = {
            "is_ai_generated": True, "topic_prompt": payload.topic_prompt, "grade_name": grade_name,
            "duration_minutes": payload.duration_minutes,
            "part1_count": counts[0], "part2_count": counts[1], "part3_count": counts[2],
            "matrix": matrix, "sources": sources,
            "document_ids": [str(d) for d in (payload.document_ids or [])],
        }
        return self._persist(user, subject, class_obj, questions, metadata, payload.duration_minutes,
                             payload.topic_prompt, grade_name, owner_student_id=None)

    def generate_for_student(self, user: User, payload: StudentAiGenerateRequest,
                             file_text: Optional[str] = None,
                             file_name: Optional[str] = None) -> AiExerciseGenerateOut:
        """Student flow: validated chapters/matrix, personal assignment (owner_student_id = the student)."""
        self._enforce_guest_ai_limit(user)
        if not payload.chapters:
            raise _err(status.HTTP_422_UNPROCESSABLE_ENTITY, "ERR-EXE-AI_CHAPTER_REQUIRED",
                       "Select at least one chapter.")
        matrix = payload.matrix.as_dict()
        total = sum(sum(part.values()) for part in matrix.values())
        if total < 1:
            raise _err(status.HTTP_422_UNPROCESSABLE_ENTITY, "ERR-EXE-AI_EMPTY_MATRIX",
                       "The matrix must request at least one question.")
        if total > MAX_TOTAL_QUESTIONS:
            raise _err(status.HTTP_422_UNPROCESSABLE_ENTITY, "ERR-EXE-AI_MATRIX_TOO_LARGE",
                       f"The matrix may request at most {MAX_TOTAL_QUESTIONS} questions.")
        class_obj, subject = self._student_subject_context(user, payload.subject_id)
        self._require_guest_grade(user, class_obj, payload.grade)
        grade = parse_grade(class_obj.class_name) if class_obj is not None else payload.grade
        doc_ids = RagRetrievalService.resolve_sgk_filter(self.db, subject.subject_name, grade)
        allowed = {c["chapter"] for c in RagRetrievalService.list_chapters(self.db, doc_ids)}
        if any(ch not in allowed for ch in payload.chapters):
            raise _err(status.HTTP_422_UNPROCESSABLE_ENTITY, "ERR-EXE-AI_INVALID_CHAPTER",
                       "One or more chapters are not available for this subject.")
        grade_name = f"Lớp {grade}" if grade else (class_obj.class_name if class_obj is not None else "")
        context, sources = RagContextService.build_student_context(
            self.db, student_id=user.user_id, subject_id=subject.subject_id, subject_name=subject.subject_name,
            grade=grade, chapters=payload.chapters, topic_prompt=payload.topic_prompt)
        file_text = (file_text or "")[:STUDENT_FILE_CHARS]
        if file_text:
            sources = sources + [{"source": "student_file", "label": file_name or "Uploaded file", "page": None,
                                  "modality": "text", "image_url": None, "document_id": None}]
        topic = payload.topic_prompt or "; ".join(payload.chapters)
        counts = self._counts(matrix)
        questions = self._generate_guarded(
            subject_name=subject.subject_name, grade_name=grade_name, topic_prompt=topic,
            counts=counts, context=context, matrix=matrix, student_file=file_text)
        metadata = {
            "is_ai_generated": True, "topic_prompt": payload.topic_prompt, "grade_name": grade_name,
            "duration_minutes": payload.duration_minutes, "chapters": payload.chapters, "matrix": matrix,
            "part1_count": counts[0], "part2_count": counts[1], "part3_count": counts[2],
            "sources": sources, "document_ids": [],
        }
        return self._persist(user, subject, class_obj, questions, metadata, payload.duration_minutes,
                             topic, grade_name, owner_student_id=user.user_id)

    # ------------------------------------------------------------------ internals
    @staticmethod
    def _counts(matrix: Dict[str, Dict[str, int]]) -> Tuple[int, int, int]:
        return (sum(matrix["mcq"].values()), sum(matrix["tf"].values()), sum(matrix["short"].values()))

    def _resolve_teacher_subject(self, payload: AiExerciseGenerateRequest) -> Subject:
        query = self.db.query(Subject).filter(Subject.status != "DELETED")
        subject = None
        if payload.subject_id:
            subject = query.filter(Subject.subject_id == payload.subject_id).first()
        elif payload.subject_name.strip():
            subject = query.filter(Subject.subject_name.ilike(payload.subject_name.strip())).first()
            if subject is None:
                subject = query.filter(Subject.subject_name.ilike(f"%{payload.subject_name.strip()}%")).first()
        if subject is None:
            raise _err(status.HTTP_404_NOT_FOUND, "ERR-ACAD-SUBJECT_NOT_FOUND", "Subject not found.")
        return subject

    def _resolve_teacher_class(self, user: User, subject: Subject, payload: AiExerciseGenerateRequest) -> Class:
        if payload.class_id:
            class_obj = self.db.query(Class).filter(
                Class.class_id == payload.class_id, Class.status != "DELETED").first()
            if class_obj is None:
                raise _err(status.HTTP_404_NOT_FOUND, "ERR-ACAD-CLASS_NOT_FOUND", "Class not found.")
            check_class_access(self.db, user, class_obj.class_id)
            return class_obj
        class_obj = (
            self.db.query(Class)
            .join(TeacherSubject, TeacherSubject.class_id == Class.class_id)
            .filter(TeacherSubject.teacher_id == user.user_id, TeacherSubject.subject_id == subject.subject_id,
                    TeacherSubject.status == "ACTIVE", Class.status != "DELETED")
            .first()
        )
        if class_obj is None:
            raise _err(status.HTTP_403_FORBIDDEN, "ERR-ACAD-CLASS_ACCESS_DENIED",
                       "No class available for this subject.")
        return class_obj

    def _generate_guarded(self, *, subject_name: str, grade_name: str, topic_prompt: str,
                          counts: Tuple[int, int, int], context: str, matrix: Optional[dict],
                          student_file: str) -> List[Dict[str, Any]]:
        """Run the generator under the process-wide semaphore; 503 when busy, 502 when generation fails."""
        if not AI_GENERATE_SEMAPHORE.acquire(timeout=AI_GENERATE_ACQUIRE_TIMEOUT_SECONDS):
            raise _err(status.HTTP_503_SERVICE_UNAVAILABLE, "ERR-EXE-AI_BUSY",
                       "AI generation is busy. Please try again shortly.")
        try:
            return AiExerciseGeneratorService.generate_questions(
                subject_name=subject_name, grade_name=grade_name, topic_prompt=topic_prompt,
                part1_count=counts[0], part2_count=counts[1], part3_count=counts[2],
                context=context, matrix=matrix, student_file=student_file)
        except RuntimeError as e:
            raise _err(status.HTTP_502_BAD_GATEWAY, "ERR-EXE-AI_GENERATION_FAILED", str(e))
        finally:
            AI_GENERATE_SEMAPHORE.release()

    def _persist(self, user: User, subject: Subject, class_obj: Optional[Class], questions: List[Dict[str, Any]],
                 metadata: Dict[str, Any], duration_minutes: int, topic: str, grade_name: str,
                 owner_student_id: Optional[uuid.UUID]) -> AiExerciseGenerateOut:
        """Store Exercise, Questions, AnswerOptions (MCQ and True/False) and the assignment in one commit."""
        clean = (topic or "").strip()
        short = clean[:50] + "..." if len(clean) > 50 else clean
        exercise = Exercise(
            title=f"{subject.subject_name} {grade_name} - {short}"[:255],
            subject_id=subject.subject_id, created_by=user.user_id, total_questions=len(questions),
            ai_metadata=metadata, status="ACTIVE",
        )
        self.db.add(exercise)
        self.db.flush()
        for order, q in enumerate(questions):
            question = Question(
                exercise_id=exercise.exercise_id, content=q["content"], content_markdown=q["content"],
                question_type=q["question_type"], difficulty=q.get("difficulty"),
                correct_answer=q.get("correct_answer"), explanation=q.get("explanation"),
                segments=q.get("segments"), display_order=order, is_ai_generated=True, status="ACTIVE",
            )
            self.db.add(question)
            self.db.flush()
            for opt in q.get("answer_options", []):
                self.db.add(AnswerOption(question_id=question.question_id, content=opt["content"],
                                         is_correct=bool(opt["is_correct"]), display_order=opt["display_order"]))
        assignment = None
        if class_obj is not None or owner_student_id is not None:
            now = datetime.now(timezone.utc)
            assignment = ClassAssignment(
                class_id=class_obj.class_id if class_obj is not None else None,
                exercise_id=exercise.exercise_id, assigned_by=user.user_id,
                assigned_at=now, due_at=now + timedelta(days=DEFAULT_DUE_DAYS), status="ACTIVE",
                owner_student_id=owner_student_id,
            )
            self.db.add(assignment)
        self.db.commit()
        if assignment is not None:
            self.db.refresh(assignment)
        self.db.refresh(exercise)
        return AiExerciseGenerateOut(
            exercise_id=exercise.exercise_id,
            assignment_id=assignment.assignment_id if assignment is not None else None,
            title=exercise.title,
            subject_name=subject.subject_name, total_questions=len(questions), duration_minutes=duration_minutes,
            class_id=class_obj.class_id if class_obj is not None else None,
            class_name=class_obj.class_name if class_obj is not None else None,
            due_at=assignment.due_at if assignment is not None else None,
            created_at=exercise.created_at, sources=metadata.get("sources", []),
        )
