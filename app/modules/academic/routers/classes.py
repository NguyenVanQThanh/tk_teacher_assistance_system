# File Name: classes.py
# Description: API router for Class CRUD endpoints (F-ACAD-02).
# Created At: 2026-07-22
# Created By: Tam Khang
# Updated At: 2026-07-22
# Updated By: Tam Khang

from uuid import UUID
from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.auth.dependencies import require_perm
from app.modules.academic.schemas import ClassCreate, ClassUpdate, ClassOut
from app.modules.academic.services.class_service import ClassService

router = APIRouter(prefix="/api/v1/classes", tags=["academic-classes"])


@router.post(
    "",
    response_model=ClassOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_perm("ACAD_CLASS_MANAGE"))]
)
def create_class(
    payload: ClassCreate,
    db: Session = Depends(get_db)
):
    """
    Tạo lớp học mới. Yêu cầu quyền ACAD_CLASS_MANAGE.
    """
    return ClassService.create_class(
        db=db,
        class_name=payload.class_name,
        school_year=payload.school_year,
        homeroom_teacher_id=payload.homeroom_teacher_id
    )


@router.get(
    "",
    response_model=List[ClassOut],
    dependencies=[Depends(require_perm("ACAD_CLASS_VIEW"))]
)
def list_classes(db: Session = Depends(get_db)):
    """
    Lấy danh sách tất cả lớp học. Yêu cầu quyền ACAD_CLASS_VIEW.
    """
    return ClassService.list_classes(db=db)


@router.get(
    "/{class_id}",
    response_model=ClassOut,
    dependencies=[Depends(require_perm("ACAD_CLASS_VIEW"))]
)
def get_class(class_id: UUID, db: Session = Depends(get_db)):
    """
    Lấy chi tiết một lớp học theo ID. Yêu cầu quyền ACAD_CLASS_VIEW.
    """
    return ClassService.get_class(db=db, class_id=class_id)


@router.put(
    "/{class_id}",
    response_model=ClassOut,
    dependencies=[Depends(require_perm("ACAD_CLASS_MANAGE"))]
)
def update_class(
    class_id: UUID,
    payload: ClassUpdate,
    db: Session = Depends(get_db)
):
    """
    Cập nhật lớp học. Yêu cầu quyền ACAD_CLASS_MANAGE.
    """
    update_homeroom = "homeroom_teacher_id" in payload.model_fields_set
    return ClassService.update_class(
        db=db,
        class_id=class_id,
        class_name=payload.class_name,
        school_year=payload.school_year,
        homeroom_teacher_id=payload.homeroom_teacher_id,
        update_homeroom_teacher=update_homeroom
    )


@router.delete(
    "/{class_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_perm("ACAD_CLASS_MANAGE"))]
)
def delete_class(class_id: UUID, db: Session = Depends(get_db)):
    """
    Xóa lớp học. Yêu cầu quyền ACAD_CLASS_MANAGE.
    """
    ClassService.delete_class(db=db, class_id=class_id)
