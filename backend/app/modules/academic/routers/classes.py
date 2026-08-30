# File Name: classes.py
# Description: API router for Class CRUD & Restore endpoints (F-ACAD-02).
# Created At: 2026-07-22
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
from app.modules.academic.schemas import ClassCreate, ClassUpdate, ClassOut, AcademicStatusEnum
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
        homeroom_teacher_id=payload.homeroom_teacher_id,
        status_val=payload.status.value
    )


@router.get(
    "",
    response_model=List[ClassOut],
    dependencies=[Depends(require_perm("ACAD_CLASS_VIEW"))]
)
def list_classes(
    status: Optional[AcademicStatusEnum] = Query(None, description="Lọc theo trạng thái (ACTIVE, INACTIVE, DRAFT, DELETED)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Lấy danh sách các lớp học theo phân quyền dữ liệu (Admin, Teacher, Student) và trạng thái. Yêu cầu quyền ACAD_CLASS_VIEW.
    """
    status_val = status.value if status else None
    return ClassService.list_classes(db=db, status_val=status_val, current_user=current_user)


@router.get(
    "/{class_id}",
    response_model=ClassOut,
    dependencies=[Depends(require_perm("ACAD_CLASS_VIEW"))]
)
def get_class(
    class_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Lấy chi tiết một lớp học theo ID với phân quyền dữ liệu. Yêu cầu quyền ACAD_CLASS_VIEW.
    """
    return ClassService.get_class(db=db, class_id=class_id, current_user=current_user)


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
    status_val = payload.status.value if payload.status else None
    return ClassService.update_class(
        db=db,
        class_id=class_id,
        class_name=payload.class_name,
        school_year=payload.school_year,
        homeroom_teacher_id=payload.homeroom_teacher_id,
        update_homeroom_teacher=update_homeroom,
        status_val=status_val
    )


@router.delete(
    "/{class_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_perm("ACAD_CLASS_MANAGE"))]
)
def delete_class(class_id: UUID, db: Session = Depends(get_db)):
    """
    Xóa mềm lớp học (chuyển sang trạng thái DELETED). Yêu cầu quyền ACAD_CLASS_MANAGE.
    """
    ClassService.delete_class(db=db, class_id=class_id)


@router.post(
    "/{class_id}/restore",
    response_model=ClassOut,
    dependencies=[Depends(require_perm("ACAD_CLASS_MANAGE"))]
)
def restore_class(class_id: UUID, db: Session = Depends(get_db)):
    """
    Khôi phục lớp học bị xóa mềm về ACTIVE (dành riêng cho Admin). Yêu cầu quyền ACAD_CLASS_MANAGE.
    """
    return ClassService.restore_class(db=db, class_id=class_id)
