# File Name: classes.py
# Description: API router for Class CRUD & Restore endpoints (F-ACAD-02).
# Created At: 2026-07-22
# Created By: Tam Khang
# Updated At: 2026-11-14
# Updated By: Tam Khang

from uuid import UUID
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from models.models import User
from app.modules.auth.dependencies import require_perm, get_current_user
from app.modules.academic.schemas import ClassCreate, ClassUpdate, ClassOut, AcademicStatusEnum
from app.modules.academic.services.class_service import ClassService, matches_grade

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
    Create a new class. Requires ACAD_CLASS_MANAGE permission.
    """
    # Class row and its metadata commit together so a failure cannot leave them out of sync.
    try:
        cls = ClassService.create_class(
            db=db,
            class_name=payload.class_name,
            school_year=payload.school_year,
            homeroom_teacher_id=payload.homeroom_teacher_id,
            status_val=payload.status.value,
            commit=False
        )
        ClassService.save_class_metadata(
            db=db,
            class_id=cls.class_id,
            room_name=payload.room_name,
            specialization=payload.specialization,
            update_room="room_name" in payload.model_fields_set,
            update_specialization="specialization" in payload.model_fields_set,
            commit=False,
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(cls)
    return ClassService.enrich_class_out(db, cls)


@router.get(
    "",
    response_model=List[ClassOut],
    dependencies=[Depends(require_perm("ACAD_CLASS_VIEW"))]
)
def list_classes(
    status: Optional[AcademicStatusEnum] = Query(None, description="Filter by status (ACTIVE, INACTIVE, DRAFT, DELETED)"),
    grade: Optional[str] = Query(None, description="Filter by grade level (e.g., 10, 11, 12)"),
    school_year: Optional[str] = Query(None, description="Filter by academic year"),
    search: Optional[str] = Query(None, description="Search by class name, homeroom teacher, or room"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List classes scoped by RBAC role and optional status/grade/year/search filters.
    """
    status_val = status.value if status else None
    classes = ClassService.list_classes(db=db, status_val=status_val, current_user=current_user)
    enriched = ClassService.enrich_classes_out(db, classes)

    if grade and grade.strip() and grade.strip().lower() != "all":
        g = grade.strip().lower()
        for prefix in ("khối", "khoi", "grade", "k"):
            if g.startswith(prefix):
                g = g[len(prefix):].strip()
                break
        enriched = [c for c in enriched if matches_grade(c.class_name, g)]

    if school_year and school_year.strip() and school_year.strip().lower() != "all":
        sy = school_year.strip().lower()
        enriched = [c for c in enriched if (c.school_year or "").lower() == sy]

    if search and search.strip():
        term = search.strip().lower()
        enriched = [
            c for c in enriched
            if term in c.class_name.lower()
            or term in (c.homeroom_teacher_name or "").lower()
            or term in (c.room_name or "").lower()
        ]

    return enriched


@router.get(
    "/available-students",
    dependencies=[Depends(require_perm("ACAD_CLASS_VIEW"))]
)
def get_available_students(
    class_id: Optional[UUID] = Query(None, description="Target class ID to exclude already enrolled students"),
    search: Optional[str] = Query(None, description="Search by student name, email, or phone"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """
    Retrieve non-deleted Student users who are not actively enrolled in the specified class.
    """
    from app.modules.academic.schemas import AvailableStudentsResponse
    from app.modules.academic.services.enrollment_service import EnrollmentService

    items = EnrollmentService.get_available_students(
        db=db, class_id=class_id, search=search, limit=limit
    )
    return AvailableStudentsResponse(items=items)


@router.get(
    "/export-csv",
    dependencies=[Depends(require_perm("ACAD_CLASS_VIEW"))]
)
def export_classes_csv(
    status: Optional[AcademicStatusEnum] = Query(None, description="Filter by class status"),
    grade: Optional[str] = Query(None, description="Filter by grade level"),
    school_year: Optional[str] = Query(None, description="Filter by academic year"),
    search: Optional[str] = Query(None, description="Search filter"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Export filtered classes as a downloadable UTF-8 BOM CSV file.
    """
    import io
    from fastapi.responses import StreamingResponse

    status_val = status.value if status else None
    csv_bytes = ClassService.export_classes_csv(
        db=db,
        status_val=status_val,
        current_user=current_user,
        grade=grade,
        school_year=school_year,
        search=search,
    )
    return StreamingResponse(
        io.BytesIO(csv_bytes),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="classes_export.csv"'},
    )


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
    Retrieve class details by ID with RBAC data scoping.
    """
    cls = ClassService.get_class(db=db, class_id=class_id, current_user=current_user)
    return ClassService.enrich_class_out(db, cls)


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
    Update class information. Requires ACAD_CLASS_MANAGE permission.
    """
    update_homeroom = "homeroom_teacher_id" in payload.model_fields_set
    status_val = payload.status.value if payload.status else None
    try:
        cls = ClassService.update_class(
            db=db,
            class_id=class_id,
            class_name=payload.class_name,
            school_year=payload.school_year,
            homeroom_teacher_id=payload.homeroom_teacher_id,
            update_homeroom_teacher=update_homeroom,
            status_val=status_val,
            commit=False
        )
        ClassService.save_class_metadata(
            db=db,
            class_id=cls.class_id,
            room_name=payload.room_name,
            specialization=payload.specialization,
            update_room="room_name" in payload.model_fields_set,
            update_specialization="specialization" in payload.model_fields_set,
            commit=False,
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(cls)
    return ClassService.enrich_class_out(db, cls)


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
    Restore a soft-deleted class to ACTIVE status (Admin). Requires ACAD_CLASS_MANAGE permission.
    """
    cls = ClassService.restore_class(db=db, class_id=class_id)
    return ClassService.enrich_class_out(db, cls)
