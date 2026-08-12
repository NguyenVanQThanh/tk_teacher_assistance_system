# File Name: exercises.py
# Description: API Router for Exercise endpoints (F-EXE-01).
# Created At: 2026-07-31
# Created By: Tam Khang
# Updated At: 2026-08-04
# Updated By: Tam Khang

from uuid import UUID
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, UploadFile, File, Form, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from models.models import User
from app.modules.auth.dependencies import require_perm, get_current_user
from app.modules.exercise.schemas import (
    ExerciseCreate, ExerciseUpdate, ExerciseOut,
    QuestionCreate, QuestionOut, AnswerOptionCreate
)
from app.modules.exercise.services.exercise_service import ExerciseService
from app.modules.exercise.services.question_service import QuestionService
from app.modules.exercise.services.import_parser_service import ImportParserService
from app.modules.exercise.services.pdf_export_service import PdfExportService


router = APIRouter(prefix="/api/v1/exercises", tags=["exercise-bank"])


def get_exercise_service(db: Session = Depends(get_db)) -> ExerciseService:
    """Dependency provider for ExerciseService."""
    return ExerciseService(db)


def get_question_service(db: Session = Depends(get_db)) -> QuestionService:
    """Dependency provider for QuestionService."""
    return QuestionService(db)


@router.post(
    "",
    response_model=ExerciseOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_perm("EXE_EXERCISE_MANAGE"))]
)
def create_exercise(
    payload: ExerciseCreate,
    service: ExerciseService = Depends(get_exercise_service),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new exercise. Requires EXE_EXERCISE_MANAGE permission.
    """
    return service.create_exercise(current_user, payload)


@router.get(
    "",
    response_model=List[ExerciseOut],
    dependencies=[Depends(require_perm("EXE_EXERCISE_VIEW"))]
)
def list_exercises(
    subject_id: Optional[UUID] = Query(None, description="Filter by subject ID"),
    service: ExerciseService = Depends(get_exercise_service),
    current_user: User = Depends(get_current_user)
):
    """
    List exercises within the user's teaching scope. Requires EXE_EXERCISE_VIEW permission.
    """
    return service.list_exercises(current_user, subject_id=subject_id)


@router.get(
    "/{exercise_id}",
    response_model=ExerciseOut,
    dependencies=[Depends(require_perm("EXE_EXERCISE_VIEW"))]
)
def get_exercise_detail(
    exercise_id: UUID,
    service: ExerciseService = Depends(get_exercise_service),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve details of an exercise including its questions and options. Requires EXE_EXERCISE_VIEW permission.
    """
    return service.get_exercise_detail(current_user, exercise_id)


@router.put(
    "/{exercise_id}",
    response_model=ExerciseOut,
    dependencies=[Depends(require_perm("EXE_EXERCISE_MANAGE"))]
)
def update_exercise(
    exercise_id: UUID,
    payload: ExerciseUpdate,
    service: ExerciseService = Depends(get_exercise_service),
    current_user: User = Depends(get_current_user)
):
    """
    Update exercise title or AI metadata. Requires EXE_EXERCISE_MANAGE permission.
    """
    return service.update_exercise(current_user, exercise_id, payload)


@router.delete(
    "/{exercise_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_perm("EXE_EXERCISE_MANAGE"))]
)
def delete_exercise(
    exercise_id: UUID,
    service: ExerciseService = Depends(get_exercise_service),
    current_user: User = Depends(get_current_user)
):
    """
    Soft-delete an exercise (sets status to DELETED). Requires EXE_EXERCISE_MANAGE permission.
    """
    service.delete_exercise(current_user, exercise_id)


@router.post(
    "/{exercise_id}/restore",
    response_model=ExerciseOut,
    dependencies=[Depends(require_perm("EXE_EXERCISE_MANAGE"))]
)
def restore_exercise(
    exercise_id: UUID,
    service: ExerciseService = Depends(get_exercise_service),
    current_user: User = Depends(get_current_user)
):
    """
    Restore a soft-deleted exercise back to ACTIVE status. Requires EXE_EXERCISE_MANAGE permission.
    """
    return service.restore_exercise(current_user, exercise_id)


@router.post(
    "/{exercise_id}/questions",
    response_model=QuestionOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_perm("EXE_EXERCISE_MANAGE"))]
)
def add_question(
    exercise_id: UUID,
    payload: QuestionCreate,
    service: QuestionService = Depends(get_question_service),
    current_user: User = Depends(get_current_user)
):
    """
    Add a question (with answer options) to an exercise. Requires EXE_EXERCISE_MANAGE permission.
    """
    return service.add_question(current_user, exercise_id, payload)


@router.post(
    "/{exercise_id}/questions/import",
    response_model=List[QuestionOut],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_perm("EXE_QUESTION_IMPORT"))]
)
async def import_questions(
    exercise_id: UUID,
    question_file: UploadFile = File(..., description="Docx or PDF question file"),
    answer_file: Optional[UploadFile] = File(None, description="Optional separate answer key file"),
    test_code: Optional[str] = Form(None, description="Optional target test code (e.g. 0121)"),
    exercise_service: ExerciseService = Depends(get_exercise_service),
    question_service: QuestionService = Depends(get_question_service),
    current_user: User = Depends(get_current_user)
):
    """
    Bulk import questions from docx/pdf files with optional answer key file and test code.
    Requires EXE_QUESTION_IMPORT permission.
    """
    # 1. Verify access to exercise
    exercise_service.get_exercise_detail(current_user, exercise_id)

    # 2. Validate question file
    q_filename = question_file.filename or ""
    if not (q_filename.lower().endswith(".docx") or q_filename.lower().endswith(".pdf")):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail={
                "code": "ERR-EXE-IMPORT_FILE_TYPE_UNSUPPORTED",
                "message": "Only .docx and .pdf files are supported for import."
            }
        )

    q_bytes = await question_file.read()
    if len(q_bytes) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={
                "code": "ERR-EXE-IMPORT_FILE_TOO_LARGE",
                "message": "Question file size exceeds 10MB limit."
            }
        )

    ans_bytes = None
    ans_filename = None
    if answer_file:
        ans_filename = answer_file.filename or ""
        if not (ans_filename.lower().endswith(".docx") or ans_filename.lower().endswith(".pdf")):
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail={
                    "code": "ERR-EXE-IMPORT_FILE_TYPE_UNSUPPORTED",
                    "message": "Answer file must be .docx or .pdf."
                }
            )
        ans_bytes = await answer_file.read()

    # 3. Call ImportParserService
    parse_result = ImportParserService.parse_document(
        file_bytes=q_bytes,
        filename=q_filename,
        answer_file_bytes=ans_bytes,
        answer_filename=ans_filename,
        test_code=test_code
    )

    if parse_result.errors:
        err_details = [
            {"question_number": err.question_number, "message": err.message}
            for err in parse_result.errors
        ]
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "ERR-EXE-IMPORT_INVALID_QUESTION",
                "message": "Import failed due to validation errors.",
                "errors": err_details
            }
        )

    # 4. Clear old questions of this exercise before re-importing
    existing_exercise = exercise_service.get_exercise_detail(current_user, exercise_id)
    if existing_exercise.questions:
        for old_q in existing_exercise.questions:
            old_q.status = "DELETED"
        get_db_session = question_service.db
        get_db_session.flush()

    # 5. Insert newly imported questions in transaction
    created_questions = []
    for parsed_q in parse_result.questions:

        options_create = [
            AnswerOptionCreate(
                content=opt.content,
                is_correct=opt.is_correct,
                display_order=opt.display_order
            )
            for opt in parsed_q.answer_options
        ]
        payload = QuestionCreate(
            content=parsed_q.content,
            question_type=parsed_q.question_type,
            difficulty=parsed_q.difficulty,
            correct_answer=parsed_q.correct_answer,
            display_order=parsed_q.question_number,
            image_url=parsed_q.image_url,
            answer_options=options_create if options_create else None
        )
        created_q = question_service.add_question(current_user, exercise_id, payload)
        created_questions.append(created_q)

    return created_questions


@router.get(
    "/{exercise_id}/export/pdf",
    dependencies=[Depends(require_perm("EXE_EXERCISE_VIEW"))]
)
def export_exercise_pdf(
    exercise_id: UUID,
    exercise_service: ExerciseService = Depends(get_exercise_service),
    current_user: User = Depends(get_current_user)
):
    """
    Export an exercise and its questions to formatted PDF document.
    Requires EXE_EXERCISE_VIEW permission.
    """
    exercise = exercise_service.get_exercise_detail(current_user, exercise_id)
    pdf_bytes = PdfExportService.generate_exercise_pdf(exercise)
    filename = f"exercise_{exercise_id}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

