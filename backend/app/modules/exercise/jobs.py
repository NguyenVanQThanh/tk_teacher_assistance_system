"""
File Name: jobs.py
Description: Job handlers for slow exercise work (student AI, teacher AI, question import) run by the job queue.
Created At: 2026-11-17
Created By: AI Agent
Updated At: 2026-11-17
Updated By: AI Agent
"""
import base64
import io
import json
from types import SimpleNamespace
from uuid import UUID

from fastapi import HTTPException, Response

from app.core.background_jobs import register_handler
from app.core.resource_limits import IMPORT_SEMAPHORE
from app.modules.exercise.schemas import AiExerciseGenerateRequest, StudentAiGenerateRequest
from app.modules.exercise.services.ai_exercise_service import AiExerciseService
from app.modules.exercise.services.exercise_service import ExerciseService
from app.modules.exercise.services.question_service import QuestionService

KIND_STUDENT_AI = "STUDENT_AI_EXERCISE"
KIND_TEACHER_AI = "TEACHER_AI_EXERCISE"
KIND_IMPORT = "QUESTION_IMPORT"


def _student_ai(session, user, payload: dict):
    return AiExerciseService(session).generate_for_student(
        user, StudentAiGenerateRequest.model_validate(payload["request"]),
        payload.get("file_text"), payload.get("file_name"))


def _teacher_ai(session, user, payload: dict):
    return ExerciseService(session).generate_ai_exercise(user, AiExerciseGenerateRequest.model_validate(payload))


def _upload(d):
    """Rebuild an UploadFile-like object from a base64 payload entry."""
    if not d:
        return None
    return SimpleNamespace(filename=d["filename"], file=io.BytesIO(base64.b64decode(d["data"])))


def encode_upload(f) -> dict:
    """Serialize an UploadFile for the job payload (files are capped at 1 MB by the router)."""
    if f is None:
        return None
    return {"filename": f.filename, "data": base64.b64encode(f.file.read()).decode("ascii")}


def _import(session, user, payload: dict):
    from app.modules.exercise.routers.exercises import _import_questions_impl
    from app.modules.auth.services.permission_service import PermissionService
    if "EXE_QUESTION_IMPORT" not in PermissionService.get_effective_permissions(session, user.user_id, user.role_id):
        raise HTTPException(status_code=403, detail={
            "code": "ERR-AUTH-FORBIDDEN", "message": "You do not have permission to access this resource."})
    resp = Response()
    with IMPORT_SEMAPHORE:
        questions = _import_questions_impl(
            exercise_id=UUID(payload["exercise_id"]), question_file=_upload(payload["question_file"]),
            answer_file=_upload(payload.get("answer_file")), test_code=payload.get("test_code"),
            exercise_service=ExerciseService(session), question_service=QuestionService(session),
            current_user=user, response=resp)
    skipped = json.loads(resp.headers.get("X-Import-Skipped", "[]"))
    return {"questions": questions, "skipped_count": len(skipped), "skipped": skipped}


register_handler(KIND_STUDENT_AI, _student_ai, "Tạo bài tập AI", "/student/exercises", 90)
register_handler(KIND_TEACHER_AI, _teacher_ai, "Tạo đề AI", "/teacher/exercises", 90)
register_handler(KIND_IMPORT, _import, "Nhập câu hỏi từ tệp", "/teacher/exercises", 120)
