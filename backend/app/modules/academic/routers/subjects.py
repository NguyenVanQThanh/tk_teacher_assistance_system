# File Name: subjects.py
# Description: API router for Subject CRUD & Restore endpoints (F-ACAD-01).
# Created At: 2026-07-21
# Created By: Tam Khang
# Updated At: 2026-07-26
# Updated By: Tam Khang

from uuid import UUID
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from models.models import User
from app.modules.auth.dependencies import require_perm, get_current_user
from app.modules.academic.schemas import SubjectCreate, SubjectUpdate, SubjectOut, AcademicStatusEnum
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
        description=payload.description,
        status_val=payload.status.value
    )


@router.get(
    "",
    response_model=List[SubjectOut],
    dependencies=[Depends(require_perm("ACAD_SUBJECT_VIEW"))]
)
def list_subjects(
    status: Optional[AcademicStatusEnum] = Query(None, description="Lọc theo trạng thái (ACTIVE, INACTIVE, DRAFT, DELETED)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Lấy danh sách các môn học theo phân quyền dữ liệu và trạng thái. Yêu cầu quyền ACAD_SUBJECT_VIEW.
    """
    status_val = status.value if status else None
    return SubjectService.list_subjects(db=db, status_val=status_val, current_user=current_user)


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
    status_val = payload.status.value if payload.status else None
    return SubjectService.update_subject(
        db=db,
        subject_id=subject_id,
        subject_name=payload.subject_name,
        description=payload.description,
        status_val=status_val
    )


@router.delete(
    "/{subject_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_perm("ACAD_SUBJECT_MANAGE"))]
)
def delete_subject(subject_id: UUID, db: Session = Depends(get_db)):
    """
    Xóa mềm môn học (chuyển sang trạng thái DELETED). Yêu cầu quyền ACAD_SUBJECT_MANAGE.
    """
    SubjectService.delete_subject(db=db, subject_id=subject_id)


@router.post(
    "/{subject_id}/restore",
    response_model=SubjectOut,
    dependencies=[Depends(require_perm("ACAD_SUBJECT_MANAGE"))]
)
def restore_subject(subject_id: UUID, db: Session = Depends(get_db)):
    """
    Khôi phục môn học bị xóa mềm về ACTIVE (dành riêng cho Admin). Yêu cầu quyền ACAD_SUBJECT_MANAGE.
    """
    return SubjectService.restore_subject(db=db, subject_id=subject_id)
