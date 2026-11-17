# File Name: ai_generation.py
# Description: Student AI exercise generation endpoints (chapter list and multipart generation with a guarded optional file).
# Created At: 2026-11-13
# Created By: AI Agent
# Updated At: 2026-11-13
# Updated By: AI Agent

import io
import json
import logging
import threading
import time
from typing import List, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import ValidationError
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.core.database import SessionLocal, get_db
from app.modules.academic.scoping import get_user_role_name
from app.modules.auth.dependencies import get_current_user, require_perm
from app.modules.exercise.schemas import AiChapterOut, AiExerciseGenerateOut, StudentAiGenerateRequest
from app.modules.exercise.services.ai_exercise_service import AiExerciseService
from app.modules.exercise.services.rag_context_service import STUDENT_FILE_CHARS
from models.models import User

logger = logging.getLogger("smartlms.exercise.ai_generation")
router = APIRouter(prefix="/api/v1/ai-exercises", tags=["ai-exercises"])

MAX_FILE_BYTES = 1_048_576  # uploads of 1 MiB or more are rejected
MULTIPART_OVERHEAD_BYTES = 64 * 1024
ALLOWED_EXTENSIONS = (".pdf", ".docx", ".txt")


def _err(code: int, error: str, message: str) -> HTTPException:
    return HTTPException(status_code=code, detail={"code": error, "message": message})


def _too_large() -> HTTPException:
    return _err(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "ERR-EXE-AI_FILE_TOO_LARGE",
                "The uploaded file must be smaller than 1 MiB.")


def _bad_type() -> HTTPException:
    return _err(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "ERR-EXE-AI_FILE_TYPE",
                "Only .pdf, .docx and .txt files are accepted.")


def _require_student(db: Session, user: User) -> None:
    if get_user_role_name(db, user) != "Student":
        raise _err(status.HTTP_403_FORBIDDEN, "ERR-AUTH-FORBIDDEN", "Only students can use this endpoint.")


def validate_upload_type(filename: str, data: bytes) -> str:
    """Return the extension when both extension and magic bytes agree; raise 415 otherwise."""
    name = (filename or "").lower()
    ext = next((e for e in ALLOWED_EXTENSIONS if name.endswith(e)), None)
    if ext is None:
        raise _bad_type()
    if ext == ".pdf" and not data.startswith(b"%PDF"):
        raise _bad_type()
    if ext == ".docx" and not data.startswith(b"PK\x03\x04"):
        raise _bad_type()
    if ext == ".txt":
        try:
            data.decode("utf-8")
        except UnicodeDecodeError:
            raise _bad_type()
    return ext


def extract_text(ext: str, data: bytes) -> str:
    """Extract plain text from a validated upload (no OCR); '' when there is none. CPU-bound: run in a thread."""
    try:
        if ext == ".txt":
            text = data.decode("utf-8")
        elif ext == ".pdf":
            import fitz  # PyMuPDF
            with fitz.open(stream=data, filetype="pdf") as doc:
                text = "\n".join(page.get_text() for page in doc)
        else:
            from docx import Document
            doc = Document(io.BytesIO(data))
            text = "\n".join(p.text for p in doc.paragraphs)
            for table in doc.tables:
                for row in table.rows:
                    text += "\n" + " | ".join(c.text for c in row.cells)
    except Exception as exc:  # noqa: BLE001 - a corrupt file is a client error, not a server error
        logger.warning("Uploaded file could not be parsed: %s", exc)
        raise _bad_type()
    return text.strip()[:STUDENT_FILE_CHARS]


@router.get(
    "/chapters",
    response_model=List[AiChapterOut],
    dependencies=[Depends(require_perm("EXE_ATTEMPT_SUBMIT"))],
)
def list_chapters(
    subject_id: UUID = Query(..., description="Subject taught in one of the student's classes"),
    grade: Optional[int] = Query(None, ge=10, le=12, description="Grade 10-12; used by guest students only"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List textbook chapters for a subject (grade taken from the student's class)."""
    _require_student(db, current_user)
    return AiExerciseService(db).student_chapters(current_user, subject_id, grade)


async def _parse_student_request(request: Request, db: Session, current_user: User):
    """Validate the multipart request and return (payload, file_text, file_name)."""
    _require_student(db, current_user)
    length = request.headers.get("content-length")
    if length is None:
        raise _err(status.HTTP_411_LENGTH_REQUIRED, "ERR-EXE-AI_LENGTH_REQUIRED", "Content-Length is required.")
    try:
        declared = int(length)
    except ValueError:
        raise _err(status.HTTP_400_BAD_REQUEST, "ERR-EXE-AI_BAD_REQUEST", "Invalid Content-Length.")
    if declared >= MAX_FILE_BYTES + MULTIPART_OVERHEAD_BYTES:
        raise _too_large()

    form = await request.form(max_files=1, max_fields=4)
    raw_payload = form.get("payload")
    if not isinstance(raw_payload, str):
        raise _err(status.HTTP_422_UNPROCESSABLE_ENTITY, "ERR-EXE-AI_PAYLOAD_REQUIRED",
                   "The `payload` field is required.")
    try:
        payload = StudentAiGenerateRequest.model_validate(json.loads(raw_payload))
    except ValidationError as exc:
        errors = exc.errors(include_url=False, include_context=False, include_input=False)
        if any(e.get("loc", ())[:1] == ("chapters",) for e in errors):
            raise _err(status.HTTP_422_UNPROCESSABLE_ENTITY, "ERR-EXE-AI_CHAPTER_REQUIRED",
                       "Select between 1 and 10 chapters.")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "ERR-EXE-AI_INVALID_PAYLOAD", "message": "Invalid payload.",
                    "errors": [{"loc": [str(p) for p in e.get("loc", ())], "msg": e.get("msg")} for e in errors]},
        )
    except ValueError:
        raise _err(status.HTTP_422_UNPROCESSABLE_ENTITY, "ERR-EXE-AI_INVALID_PAYLOAD", "Invalid payload JSON.")
    if not payload.chapters:
        raise _err(status.HTTP_422_UNPROCESSABLE_ENTITY, "ERR-EXE-AI_CHAPTER_REQUIRED",
                   "Select between 1 and 10 chapters.")
    if payload.matrix.total() < 1:
        raise _err(status.HTTP_422_UNPROCESSABLE_ENTITY, "ERR-EXE-AI_EMPTY_MATRIX",
                   "The matrix must request at least one question.")

    file_text: Optional[str] = None
    file_name: Optional[str] = None
    upload = form.get("file")
    if upload is not None and not isinstance(upload, str) and getattr(upload, "filename", ""):
        if upload.size is not None and upload.size >= MAX_FILE_BYTES:
            raise _too_large()
        data = await upload.read(MAX_FILE_BYTES)
        if len(data) >= MAX_FILE_BYTES:
            raise _too_large()
        file_name = upload.filename
        ext = validate_upload_type(file_name, data)
        file_text = await run_in_threadpool(extract_text, ext, data)
        if not file_text:
            raise _err(status.HTTP_422_UNPROCESSABLE_ENTITY, "ERR-EXE-AI_FILE_NO_TEXT",
                       "No readable text was found in the uploaded file.")
    return payload, file_text, file_name


@router.post(
    "/student",
    response_model=AiExerciseGenerateOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_perm("EXE_ATTEMPT_SUBMIT"))],
)
async def generate_for_student(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate a personal AI exercise. Multipart fields: `payload` (JSON string) and optional `file`
    (.pdf/.docx/.txt, under 1 MiB). The request size is checked before the body is parsed.
    """
    payload, file_text, file_name = await _parse_student_request(request, db, current_user)
    return await run_in_threadpool(
        AiExerciseService(db).generate_for_student, current_user, payload, file_text, file_name)


# ponytail: in-memory jobs, valid for a single backend process (uvicorn without --workers);
# move to a DB table or Redis when the backend scales to several processes.
_JOBS: dict = {}
_JOB_TTL_SECONDS = 3600
_JOBS_LOCK = threading.Lock()


def _run_job(job_id: str, user_id, payload, file_text, file_name) -> None:
    """Run generation in a worker thread with its own DB session and store the outcome."""
    session = SessionLocal()
    try:
        user = session.get(User, user_id)
        result = AiExerciseService(session).generate_for_student(user, payload, file_text, file_name)
        outcome = {"status": "done", "result": json.loads(result.model_dump_json())}
    except HTTPException as exc:
        outcome = {"status": "error", "http_status": exc.status_code, "detail": exc.detail}
    except Exception:  # noqa: BLE001 - reported to the client as a generic failure, logged here
        logger.exception("AI generation job %s failed", job_id)
        outcome = {"status": "error", "http_status": 500,
                   "detail": {"code": "ERR-EXE-AI_GENERATION_FAILED", "message": "AI generation failed."}}
    finally:
        session.close()
    with _JOBS_LOCK:
        _JOBS[job_id].update(outcome)


@router.post(
    "/student/jobs",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(require_perm("EXE_ATTEMPT_SUBMIT"))],
)
async def start_student_job(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Validate like POST /student, then generate in the background; poll GET /student/jobs/{job_id}."""
    payload, file_text, file_name = await _parse_student_request(request, db, current_user)
    now = time.time()
    job_id = uuid4().hex
    with _JOBS_LOCK:
        for k in [k for k, v in _JOBS.items() if now - v["created"] > _JOB_TTL_SECONDS]:
            del _JOBS[k]
        _JOBS[job_id] = {"status": "running", "user_id": str(current_user.user_id), "created": now}
    threading.Thread(target=_run_job, args=(job_id, current_user.user_id, payload, file_text, file_name),
                     daemon=True).start()
    return {"job_id": job_id, "status": "running"}


@router.get(
    "/student/jobs/{job_id}",
    dependencies=[Depends(require_perm("EXE_ATTEMPT_SUBMIT"))],
)
def get_student_job(job_id: str, current_user: User = Depends(get_current_user)):
    """Job state: running | done (with result) | error (with http_status and detail)."""
    job = _JOBS.get(job_id)
    if job is None or job["user_id"] != str(current_user.user_id):
        raise _err(status.HTTP_404_NOT_FOUND, "ERR-EXE-AI_JOB_NOT_FOUND", "Job not found.")
    return {k: v for k, v in job.items() if k not in ("user_id", "created")}
