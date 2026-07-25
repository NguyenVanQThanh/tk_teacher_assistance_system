# File Name: subjects.py
# Description: API router for Subject CRUD endpoints (F-ACAD-01).
# Created At: 2026-07-21
# Created By: Tam Khang
# Updated At: 2026-07-25
# Updated By: Tam Khang

from uuid import UUID
from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.auth.dependencies import require_perm, get_current_user
from app.modules.academic.schemas import SubjectCreate, SubjectUpdate, SubjectOut
from app.modules.academic.services.subject_service import SubjectService

router = APIRouter(prefix="/api/v1/subjects", tags=["academic-subjects"])


@router.post(
    "",
    response_model=SubjectOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_perm("ACAD_SUBJECT_MANAGE"))]
)
def create_subject(
    payload: SubjectCreate,
    db: Session = Depends(get_db)
):
    """
    Tạo môn học mới. Yêu cầu quyền ACAD_SUBJECT_MANAGE.
    """
    return SubjectService.create_subject(
        db=db,
        subject_name=payload.subject_name,
        description=payload.description
    )


@router.get(
    "",
    response_model=List[SubjectOut],
    dependencies=[Depends(require_perm("ACAD_SUBJECT_VIEW"))]
)
def list_subjects(db: Session = Depends(get_db)):
    """
    Lấy danh sách tất cả môn học. Yêu cầu quyền ACAD_SUBJECT_VIEW.
    """
    return SubjectService.list_subjects(db=db)


@router.get(
    "/{subject_id}",
    response_model=SubjectOut,
    dependencies=[Depends(require_perm("ACAD_SUBJECT_VIEW"))]
)
def get_subject(subject_id: UUID, db: Session = Depends(get_db)):
    """
    Lấy chi tiết một môn học theo ID. Yêu cầu quyền ACAD_SUBJECT_VIEW.
    """
    return SubjectService.get_subject(db=db, subject_id=subject_id)


@router.put(
    "/{subject_id}",
    response_model=SubjectOut,
    dependencies=[Depends(require_perm("ACAD_SUBJECT_MANAGE"))]
)
def update_subject(
    subject_id: UUID,
    payload: SubjectUpdate,
    db: Session = Depends(get_db)
):
    """
    Cập nhật môn học. Yêu cầu quyền ACAD_SUBJECT_MANAGE.
    """
    return SubjectService.update_subject(
        db=db,
        subject_id=subject_id,
        subject_name=payload.subject_name,
        description=payload.description
    )


@router.delete(
    "/{subject_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_perm("ACAD_SUBJECT_MANAGE"))]
)
def delete_subject(subject_id: UUID, db: Session = Depends(get_db)):
    """
    Xóa mềm môn học. Yêu cầu quyền ACAD_SUBJECT_MANAGE.
    """
    SubjectService.delete_subject(db=db, subject_id=subject_id)
