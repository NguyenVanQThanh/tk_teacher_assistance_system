# File Name: exercises.py
# Description: API Router for Exercise endpoints (F-EXE-01).
# Created At: 2026-07-31
# Created By: Tam Khang
# Updated At: 2026-11-09
# Updated By: Tam Khang

import json
import hashlib
import logging
import re
from uuid import UUID
from typing import List, Optional, Tuple
from fastapi import APIRouter, Depends, Query, UploadFile, File, Form, HTTPException, Response, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.database import get_db
from models.models import User, Exercise
from app.modules.auth.dependencies import require_perm, get_current_user
from app.modules.exercise.schemas import (
    ExerciseCreate, ExerciseUpdate, ExerciseOut,
    PaginatedExerciseOut, CursorPaginatedExerciseOut,
    QuestionCreate, QuestionOut, AnswerOptionCreate, QuestionTypeEnum,
    AiExerciseGenerateRequest, AiExerciseGenerateOut
)
from app.modules.exercise.services.exercise_service import ExerciseService
from app.modules.exercise.services.question_service import QuestionService
from app.modules.exercise.services.import_parser_service import ImportParserService
from app.modules.exercise.services.answer_solver_service import AnswerSolverService
from app.modules.exercise.services.pdf_export_service import PdfExportService


logger = logging.getLogger("smartlms.exercise.router")
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


from app.modules.auth.services.permission_service import PermissionService


def require_any_perm(*permission_codes: str):
    def dependency(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> None:
        effective_perms = PermissionService.get_effective_permissions(db, user.user_id, user.role_id)
        if not any(code in effective_perms for code in permission_codes):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "ERR-AUTH-FORBIDDEN",
                    "message": "You do not have permission to access this resource."
                }
            )
    return dependency


@router.post(
    "/ai-generate",
    response_model=AiExerciseGenerateOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_any_perm("EXE_ATTEMPT_SUBMIT", "EXE_EXERCISE_VIEW", "EXE_EXERCISE_MANAGE"))]
)
def generate_ai_exercise(
    payload: AiExerciseGenerateRequest,
    service: ExerciseService = Depends(get_exercise_service),
    current_user: User = Depends(get_current_user)
):
    """
    Generate an AI exercise with realistic Part 1, 2, 3 questions, assign it to the student's class,
    and persist Exercise, Question, AnswerOption, and ClassAssignment records into PostgreSQL.
    """
    return service.generate_ai_exercise(current_user, payload)


@router.get(
    "",
    response_model=CursorPaginatedExerciseOut,
    dependencies=[Depends(require_perm("EXE_EXERCISE_VIEW"))]
)
def list_exercises(
    subject_id: Optional[UUID] = Query(None, description="Filter by subject ID"),
    search: Optional[str] = Query(None, description="Search exercises by title"),
    cursor: Optional[str] = Query(None, description="Keyset pagination cursor token"),
    direction: str = Query("next", description="Pagination direction: next or prev"),
    page_size: int = Query(6, ge=1, le=100, description="Page size (default 6)"),
    service: ExerciseService = Depends(get_exercise_service),
    current_user: User = Depends(get_current_user)
):
    """
    List exercises within the user's teaching scope with Keyset / Cursor-based pagination (zero OFFSET).
    Requires EXE_EXERCISE_VIEW permission.
    """
    return service.list_exercises(
        current_user,
        subject_id=subject_id,
        search=search,
        cursor=cursor,
        direction=direction,
        page_size=page_size
    )


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
    exercise = service.get_exercise_detail(current_user, exercise_id)
    # Hide soft-deleted questions (e.g. ones replaced by a re-import) so filters
    # and detail views never show stale duplicates.
    exercise.questions = [q for q in (exercise.questions or []) if q.status != "DELETED"]
    return exercise


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
    current_user: User = Depends(get_current_user),
    response: Response = None,  # injected by FastAPI (declared with default to keep signature stable)
):
    """
    Bulk import questions from docx/pdf files with optional answer key file and test code.
    When some questions fail validation they are skipped; their count is exposed via
    the X-Import-Skipped-Count response header.
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
    # 1MB cap keeps the vision OCR provider stable (page rendering + token budget per chunk)
    if len(q_bytes) > 1 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={
                "code": "ERR-EXE-IMPORT_FILE_TOO_LARGE",
                "message": "Question file size exceeds 1MB limit. Please compress or split the file."
            }
        )

    # Reject a question file already imported into another exercise (SHA-256 of the raw bytes)
    q_hash = hashlib.sha256(q_bytes).hexdigest()
    # ponytail: Python-side scan of ai_metadata; add an indexed column when exercises exceed ~10k rows
    for other_id, other_meta in (
        exercise_service.db.query(Exercise.exercise_id, Exercise.ai_metadata)
        .filter(Exercise.status != "DELETED", Exercise.exercise_id != exercise_id)
        .all()
    ):
        if isinstance(other_meta, dict) and other_meta.get("source_file_hash") == q_hash:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "ERR-EXE-IMPORT_DUPLICATE_FILE",
                    "message": "This file has already been imported into another exercise.",
                },
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
        if len(ans_bytes) > 1 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail={
                    "code": "ERR-EXE-IMPORT_FILE_TOO_LARGE",
                    "message": "Answer file size exceeds 1MB limit."
                }
            )

    # 3. Call ImportParserService
    parse_result = ImportParserService.parse_document(
        file_bytes=q_bytes,
        filename=q_filename,
        answer_file_bytes=ans_bytes,
        answer_filename=ans_filename,
        test_code=test_code
    )

    if parse_result.errors and not parse_result.questions:
        err_details = [
            {"question_number": err.question_number, "message": err.message}
            for err in parse_result.errors
        ]
        first_msgs = " | ".join(err["message"] for err in err_details[:3])
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "ERR-EXE-IMPORT_INVALID_QUESTION",
                "message": f"Import failed due to validation errors. {first_msgs}",
                "errors": err_details
            }
        )

    for err in parse_result.errors:
        logger.warning("Import parser warning: question=%s message=%s", err.question_number, err.message)

    # 3b. Solve unkeyed MC/TF questions with AI (never fails the import)
    try:
        AnswerSolverService.solve_questions(parse_result.questions)
    except Exception:
        logger.warning("Answer solver failed; questions left unanswered", exc_info=True)

    # 4. Group parsed questions by exam label: one file may contain multiple đề,
    #    each đề becomes its own exercise record.
    groups: List[Tuple[Optional[str], List]] = []
    for parsed_q in parse_result.questions:
        label = getattr(parsed_q, "exam_label", None)
        for g_label, g_list in groups:
            if g_label == label:
                g_list.append(parsed_q)
                break
        else:
            groups.append((label, [parsed_q]))

    base_exercise = exercise_service.get_exercise_detail(current_user, exercise_id)
    if base_exercise is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ERR-EXE-EXERCISE_NOT_FOUND", "message": "Exercise not found."},
        )
    base_exercise.ai_metadata = {**(base_exercise.ai_metadata or {}), "source_file_hash": q_hash}
    exercise_service.db.commit()
    multiple_exams = len(groups) > 1
    # Strip a previously appended exam suffix so re-importing does not stack
    # suffixes ("X - ĐỀ SỐ 1 - ĐỀ SỐ 1")
    base_title = re.sub(
        r"\s*-\s*(?:ĐỀ\s*SỐ|MÃ\s*ĐỀ|ĐỀ)\s*[\w]+\s*$",
        "",
        base_exercise.title or "",
        flags=re.IGNORECASE,
    )

    created_questions = []
    import_warnings: List[dict] = []
    for g_idx, (label, group_questions) in enumerate(groups):
        # 4a. Resolve the target exercise record for this exam (đề)
        target_exercise_id = exercise_id
        if multiple_exams:
            suffix = label or f"Đề {g_idx + 1}"
            new_title = f"{base_title} - {suffix}"
            if g_idx == 0:
                exercise_service.update_exercise(current_user, exercise_id, ExerciseUpdate(title=new_title))
            else:
                existing_ex = (
                    exercise_service.db.query(Exercise)
                    .filter(
                        Exercise.created_by == current_user.user_id,
                        Exercise.title == new_title,
                        Exercise.status != "DELETED",
                    )
                    .first()
                )
                if existing_ex is not None:
                    target_exercise_id = existing_ex.exercise_id
                else:
                    new_ex = exercise_service.create_exercise(
                        current_user,
                        ExerciseCreate(
                            title=new_title,
                            subject_id=base_exercise.subject_id,
                            ai_metadata={k: v for k, v in (base_exercise.ai_metadata or {}).items() if k != "source_file_hash"},
                        ),
                    )
                    target_exercise_id = new_ex.exercise_id

        # 4b. Clear old questions of the target exercise before re-importing
        existing_exercise = exercise_service.get_exercise_detail(current_user, target_exercise_id)
        if existing_exercise and existing_exercise.questions:
            for old_q in existing_exercise.questions:
                old_q.status = "DELETED"
            question_service.db.commit()

        # 4c. Sort questions strictly by Part and question_number before inserting into database
        # Layout-resolved groups already are in document order; others fall back to part sort.
        if all(getattr(q, "doc_ordered", False) for q in group_questions):
            sorted_questions = list(group_questions)
        else:
            sorted_questions = sorted(
                group_questions,
                key=lambda q: (
                    1 if q.part == "Part1" else 2 if q.part == "Part2" else 3 if q.part == "Part3" else 4,
                    q.question_number or 0
                )
            )

        for idx, parsed_q in enumerate(sorted_questions, start=1):
            options_create = [
                AnswerOptionCreate(
                    content=opt.content,
                    is_correct=opt.is_correct,
                    display_order=opt.display_order
                )
                for opt in parsed_q.answer_options
            ]
            # OCR/answer-key parsing can mark more than one option as correct for a
            # MultipleChoice question. QuestionCreate requires exactly 1, otherwise it
            # raises ValidationError -> unhandled 500. Normalize here: keep the first
            # correct option (by display order) and flag the question for review.
            if parsed_q.question_type == QuestionTypeEnum.MultipleChoice and options_create:
                correct_idx = [i for i, o in enumerate(options_create) if o.is_correct]
                if len(correct_idx) > 1:
                    keep = min(correct_idx, key=lambda i: (options_create[i].display_order, i))
                    for i in correct_idx:
                        if i != keep:
                            options_create[i].is_correct = False
                    parsed_q.needs_review = True
            # No answer key in the source: keep the question but flag it for teacher review.
            if (parsed_q.question_type == QuestionTypeEnum.MultipleChoice and options_create
                    and not any(o.is_correct for o in options_create)):
                parsed_q.needs_review = True
            try:
                payload = QuestionCreate.model_validate(dict(
                    content=parsed_q.content,
                    content_markdown=parsed_q.content_markdown,
                    content_latex=parsed_q.content_latex,
                    segments=parsed_q.segments,
                    confidence_score=parsed_q.confidence_score,
                    needs_review=parsed_q.needs_review,
                    question_type=parsed_q.question_type,
                    difficulty=parsed_q.difficulty,
                    correct_answer=parsed_q.correct_answer,
                    display_order=idx,
                    image_url=parsed_q.image_url,
                    image_metadata=parsed_q.image_metadata,
                    answer_options=options_create if options_create else None
                ), context={"allow_no_correct": True})
            except ValidationError as exc:
                # Skip only this question instead of failing the whole import; the
                # remaining valid questions are still created.
                warn_msg = exc.errors()[0].get("msg", "invalid question data") if exc.errors() else "invalid question data"
                logger.warning(
                    "Import skipped question number=%s part=%s type=%s options=%d reason=%s",
                    parsed_q.question_number, parsed_q.part, parsed_q.question_type,
                    len(options_create), warn_msg,
                )
                import_warnings.append({
                    "question_number": parsed_q.question_number,
                    "message": warn_msg,
                })
                continue
            created_q = question_service.add_question(current_user, target_exercise_id, payload)
            created_questions.append(created_q)

    if not created_questions and import_warnings:
        err_details = [
            {"question_number": w["question_number"], "message": w["message"]}
            for w in import_warnings
        ]
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "ERR-EXE-IMPORT_INVALID_QUESTION",
                "message": f"Import failed due to validation errors. {import_warnings[0]['message']}",
                "errors": err_details,
            },
        )

    if response is not None and import_warnings:
        response.headers["X-Import-Skipped-Count"] = str(len(import_warnings))
        response.headers["X-Import-Skipped"] = json.dumps(import_warnings, ensure_ascii=False)

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

