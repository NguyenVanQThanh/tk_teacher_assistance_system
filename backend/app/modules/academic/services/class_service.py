# File Name: class_service.py
# Description: Service layer for Class business logic — duplicate check, homeroom teacher validation, RBAC Data Scoping, CRUD, and restore operations.
# Created At: 2026-07-22
# Created By: Tam Khang
# Updated At: 2026-11-14
# Updated By: Tam Khang

import logging
import re
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.models import User, Role
from app.modules.academic.models import Class
from app.modules.academic.repository import ClassRepository
from app.modules.academic.scoping import (
    get_user_role_name,
    get_accessible_class_ids,
    check_class_access,
)

logger = logging.getLogger("class_service")


def matches_grade(class_name: str, grade: str) -> bool:
    """Match a class name's leading digit run exactly (grade '1' must not match '10A1')."""
    name = class_name.strip().lower()
    if grade.isdigit():
        m = re.match(r"\d+", name)
        return bool(m) and m.group() == grade
    return name.startswith(grade)


class ClassService:
    @staticmethod
    def _validate_homeroom_teacher(db: Session, teacher_id: UUID) -> None:
        """
        Validate that homeroom_teacher_id references an Active user with Teacher role.
        Raises 400 ERR-ACAD-INVALID_HOMEROOM_TEACHER if invalid.
        """
        teacher = (
            db.query(User)
            .join(Role, User.role_id == Role.role_id)
            .filter(
                User.user_id == teacher_id,
                Role.name == "Teacher",
                User.status.in_(["Active", "ACTIVE"])
            )
            .first()
        )
        if not teacher:
            logger.warning(
                "Homeroom teacher validation failed for user_id: %s", teacher_id
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "ERR-ACAD-INVALID_HOMEROOM_TEACHER",
                    "message": "Invalid homeroom teacher (must have Teacher role and Active status)."
                }
            )

    @staticmethod
    def create_class(
        db: Session,
        class_name: str,
        school_year: Optional[str] = None,
        homeroom_teacher_id: Optional[UUID] = None,
        status_val: str = "ACTIVE"
    ) -> Class:
        """
        Create a new class.
        Raises 400 if homeroom_teacher_id is provided but invalid.
        Raises 409 if class_name already exists.
        """
        if homeroom_teacher_id is not None:
            ClassService._validate_homeroom_teacher(db, homeroom_teacher_id)

        existing = ClassRepository.get_by_name(db, class_name)
        if existing:
            logger.warning(
                "Domain Event: EVT-ACAD-CLASS_CREATED failed — duplicate name: %s", class_name
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "ERR-ACAD-CLASS_DUPLICATE_NAME",
                    "message": "Class name already exists in the system."
                }
            )

        kwargs = {}
        if status_val and status_val != "ACTIVE":
            kwargs["status"] = status_val

        cls = ClassRepository.create(
            db=db,
            class_name=class_name,
            academic_year=school_year,
            homeroom_teacher_id=homeroom_teacher_id,
            **kwargs
        )
        logger.info(
            "Domain Event: EVT-ACAD-CLASS_CREATED - class_id: %s, name: %s",
            cls.class_id, cls.class_name
        )
        return cls

    @staticmethod
    def list_classes(
        db: Session,
        status_val: Optional[str] = None,
        current_user: Optional[User] = None
    ) -> List[Class]:
        """
        Return classes filtered by status and RBAC Data Scoping based on current_user role.
        """
        if current_user:
            role_name = get_user_role_name(db, current_user)
            accessible_ids = get_accessible_class_ids(db, current_user, role_name)
            if accessible_ids is not None:
                if not accessible_ids:
                    return []
                return ClassRepository.filter_classes(db, class_ids=accessible_ids, status=status_val)

        if status_val:
            return ClassRepository.list_all(db, status=status_val)
        return ClassRepository.list_all(db)

    @staticmethod
    def get_class(
        db: Session,
        class_id: UUID,
        current_user: Optional[User] = None,
        allow_deleted: bool = False
    ) -> Class:
        """
        Return a class by ID. Enforces Data Scoping if current_user is provided.
        Raises 404 if not found.
        Raises 403 if user does not have access to this class.
        """
        if allow_deleted:
            results = ClassRepository.filter_classes(db, class_id=class_id, exclude_status=None)
            cls = results[0] if results else None
        else:
            cls = ClassRepository.get_by_id(db, class_id)

        if not cls:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "ERR-ACAD-CLASS_NOT_FOUND",
                    "message": "Class not found."
                }
            )

        if current_user:
            role_name = get_user_role_name(db, current_user)
            check_class_access(db, current_user, class_id, role_name=role_name)

        return cls

    @staticmethod
    def update_class(
        db: Session,
        class_id: UUID,
        class_name: Optional[str] = None,
        school_year: Optional[str] = None,
        homeroom_teacher_id: Optional[UUID] = None,
        update_homeroom_teacher: bool = False,
        status_val: Optional[str] = None
    ) -> Class:
        """
        Update a class.
        Raises 404 if not found.
        Raises 400 if homeroom_teacher_id is updated to an invalid teacher.
        Raises 409 if new class_name conflicts with another class.
        """
        cls = ClassService.get_class(db, class_id)

        if update_homeroom_teacher and homeroom_teacher_id is not None:
            ClassService._validate_homeroom_teacher(db, homeroom_teacher_id)

        if class_name is not None:
            conflict = ClassRepository.get_by_name(db, class_name)
            if conflict and conflict.class_id != cls.class_id:
                logger.warning(
                    "Domain Event: EVT-ACAD-CLASS_UPDATED failed — duplicate name: %s", class_name
                )
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "code": "ERR-ACAD-CLASS_DUPLICATE_NAME",
                        "message": "Class name already exists in the system."
                    }
                )

        cls = ClassRepository.update(
            db=db,
            class_obj=cls,
            class_name=class_name,
            academic_year=school_year,
            homeroom_teacher_id=homeroom_teacher_id,
            update_homeroom_teacher=update_homeroom_teacher,
            status=status_val
        )
        logger.info(
            "Domain Event: EVT-ACAD-CLASS_UPDATED - class_id: %s", cls.class_id
        )
        return cls

    @staticmethod
    def delete_class(db: Session, class_id: UUID) -> None:
        """
        Delete a class by ID.
        Raises 404 if not found.
        """
        cls = ClassService.get_class(db, class_id)
        ClassRepository.delete(db, cls)
        logger.info(
            "Domain Event: EVT-ACAD-CLASS_DELETED - class_id: %s", class_id
        )

    @staticmethod
    def restore_class(db: Session, class_id: UUID) -> Class:
        """
        Restore a soft-deleted class for Admin.
        Raises 404 if class record does not exist.
        """
        results = ClassRepository.filter_classes(db, class_id=class_id, exclude_status=None)
        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "ERR-ACAD-CLASS_NOT_FOUND",
                    "message": "Class not found."
                }
            )
        cls = results[0]
        ClassRepository.restore(db, cls)
        logger.info("Domain Event: EVT-ACAD-CLASS_RESTORED - class_id: %s", class_id)
        return cls

    @staticmethod
    def _class_meta_key(class_id: UUID) -> str:
        return f"__CLASS_META__:{class_id}"

    @staticmethod
    def save_class_metadata(
        db: Session,
        class_id: UUID,
        room_name: Optional[str] = None,
        specialization: Optional[str] = None,
        update_room: bool = False,
        update_specialization: bool = False,
    ) -> None:
        """
        Persist extended class metadata (room_name, specialization) in the shared state store.
        """
        if not update_room and not update_specialization:
            return
        from app.modules.admin.state_store import get_latest_state, upsert_state

        key = ClassService._class_meta_key(class_id)
        current = get_latest_state(db, key) or {}
        if update_room:
            current["room_name"] = room_name.strip() if room_name else None
        if update_specialization:
            current["specialization"] = specialization.strip() if specialization else None
        upsert_state(db, key, current, actor_name="System")

    @staticmethod
    def enrich_classes_out(db: Session, classes: List[Class]):
        """
        Convert Class ORM objects into enriched ClassOut schemas with teacher info,
        active student counts, room_name, and specialization without triggering N+1 queries.
        """
        from sqlalchemy import func
        from models.models import StudentClass, User
        from app.modules.academic.schemas import ClassOut
        from app.modules.admin.state_store import list_state_items

        if not classes:
            return []

        class_ids = [c.class_id for c in classes]
        teacher_ids = list({c.homeroom_teacher_id for c in classes if c.homeroom_teacher_id})

        # 1. Batch count active students per class
        count_rows = (
            db.query(StudentClass.class_id, func.count(StudentClass.student_id))
            .filter(
                StudentClass.class_id.in_(class_ids),
                func.upper(StudentClass.status) != "DELETED",
            )
            .group_by(StudentClass.class_id)
            .all()
        )
        counts_map = {cid: int(cnt) for cid, cnt in count_rows}

        # 2. Batch load homeroom teachers
        teachers_map = {}
        if teacher_ids:
            teacher_rows = db.query(User).filter(User.user_id.in_(teacher_ids)).all()
            teachers_map = {t.user_id: t for t in teacher_rows}

        # 3. Batch load optional class metadata (room_name, specialization)
        meta_rows = list_state_items(db, "__CLASS_META__:", prefix_match=True)
        meta_map = {}
        for row, payload in meta_rows:
            cid_str = row.title.split("__CLASS_META__:", 1)[-1]
            meta_map[cid_str] = payload

        enriched: List[ClassOut] = []
        for cls in classes:
            teacher = teachers_map.get(cls.homeroom_teacher_id) if cls.homeroom_teacher_id else None
            teacher_name = teacher.full_name if teacher else None
            teacher_code = (
                f"GV-{str(teacher.user_id).replace('-', '')[:6].upper()}"
                if teacher
                else None
            )
            meta = meta_map.get(str(cls.class_id), {})
            enriched.append(
                ClassOut(
                    class_id=cls.class_id,
                    class_name=cls.class_name,
                    school_year=cls.academic_year,
                    homeroom_teacher_id=cls.homeroom_teacher_id,
                    homeroom_teacher_name=teacher_name,
                    homeroom_teacher_code=teacher_code,
                    student_count=counts_map.get(cls.class_id, 0),
                    room_name=meta.get("room_name"),
                    specialization=meta.get("specialization"),
                    status=cls.status,
                    created_at=cls.created_at,
                    updated_at=cls.updated_at,
                )
            )
        return enriched

    @staticmethod
    def enrich_class_out(db: Session, cls: Class):
        """
        Enrich a single Class ORM object into ClassOut.
        """
        return ClassService.enrich_classes_out(db, [cls])[0]

    @staticmethod
    def export_classes_csv(
        db: Session,
        status_val: Optional[str] = None,
        current_user: Optional[User] = None,
        grade: Optional[str] = None,
        school_year: Optional[str] = None,
        search: Optional[str] = None,
    ) -> bytes:
        """
        Export filtered classes as UTF-8 BOM CSV bytes.
        """
        import csv
        import io

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

        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow([
            "Class ID",
            "Class Name",
            "Academic Year",
            "Homeroom Teacher",
            "Teacher Code",
            "Student Count",
            "Room",
            "Specialization",
            "Status",
        ])
        for item in enriched:
            writer.writerow([
                str(item.class_id),
                item.class_name,
                item.school_year or "",
                item.homeroom_teacher_name or "",
                item.homeroom_teacher_code or "",
                item.student_count,
                item.room_name or "",
                item.specialization or "",
                item.status.value if hasattr(item.status, "value") else str(item.status),
            ])

        return b"\xef\xbb\xbf" + buf.getvalue().encode("utf-8")
