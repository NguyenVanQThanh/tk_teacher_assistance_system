# File Name: enrollment_service.py
# Description: Service layer for Enrollment business logic — validation of class, student role/status, duplicate checks, RBAC Data Scoping, CRUD, and restore operations.
# Created At: 2026-07-23
# Created By: Tam Khang
# Updated At: 2026-11-14
# Updated By: Tam Khang

import logging
import secrets
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.models import User, Role
from app.modules.academic.models import StudentClass
from app.modules.academic.repository import ClassRepository, EnrollmentRepository
from app.modules.academic.scoping import check_class_access

logger = logging.getLogger("enrollment_service")


class EnrollmentService:
    @staticmethod
    def enroll_student(
        db: Session,
        class_id: UUID,
        student_id: Optional[UUID] = None,
        student_code: Optional[str] = None,
        status_val: str = "ACTIVE",
        student_name: Optional[str] = None,
        birthday: Optional[object] = None,
        phone: Optional[str] = None,
        gender: Optional[str] = None
    ) -> StudentClass:
        """
        Enroll a student into a class, creating the student user first if not yet existing.
        Enforces age constraint: Student must be at least 16 years old.
        """
        # 1. Validate class_id exists
        cls = ClassRepository.get_by_id(db, class_id)
        if not cls:
            logger.warning("Enrollment failed — class_id not found: %s", class_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "ERR-ACAD-CLASS_NOT_FOUND",
                    "message": "Class not found."
                }
            )

        # 2. If student_id is not provided, auto-create student user
        from datetime import date
        if not student_id:
            if not student_name or not student_name.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "code": "ERR-ACAD-MISSING_STUDENT_INFO",
                        "message": "Either student_id or student_name must be provided."
                    }
                )

            # Age validation (Student >= 16)
            if birthday:
                today = date.today()
                b_date = birthday if isinstance(birthday, date) else date.fromisoformat(str(birthday))
                age = today.year - b_date.year - ((today.month, today.day) < (b_date.month, b_date.day))
                if age < 16:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={
                            "code": "ERR-USER-INVALID_AGE_STUDENT",
                            "message": f"Student must be at least 16 years old. (Calculated age: {age})"
                        }
                    )

            import uuid as py_uuid
            from app.core.security import get_password_hash
            student_role = db.query(Role).filter(Role.name == "Student").first()
            if not student_role:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={"code": "ERR-ACAD-ROLE_NOT_FOUND", "message": "Student role not found in system."}
                )

            new_user_id = py_uuid.uuid4()
            b_date_val = birthday if isinstance(birthday, date) else (date.fromisoformat(str(birthday)) if birthday else None)
            new_user = User(
                user_id=new_user_id,
                full_name=student_name.strip(),
                phone=phone or None,
                birthday=b_date_val,
                role_id=student_role.role_id,
                # Random unknown password; admin must issue a reset to enable login.
                password_hash=get_password_hash(secrets.token_urlsafe(16)),
                status="ACTIVE"
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            student_id = new_user_id

        # 3. Validate student_id exists
        user = db.query(User).filter(User.user_id == student_id).first()
        if not user:
            logger.warning("Enrollment failed — student_id not found: %s", student_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "ERR-ACAD-STUDENT_NOT_FOUND",
                    "message": "Student does not exist in the system."
                }
            )

        # 4. Validate user role Student + status Active
        valid_student = (
            db.query(User)
            .join(Role, User.role_id == Role.role_id)
            .filter(
                User.user_id == student_id,
                Role.name == "Student",
                User.status.in_(["Active", "ACTIVE"])
            )
            .first()
        )
        if not valid_student:
            logger.warning(
                "Enrollment failed — user %s is not active Student", student_id
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "ERR-ACAD-INVALID_STUDENT_ROLE",
                    "message": "Invalid student (must have Student role and Active status)."
                }
            )


        # 4. Validate not already enrolled in this class
        existing = EnrollmentRepository.get_enrollment(db, class_id=class_id, student_id=student_id)
        if existing:
            logger.warning(
                "Enrollment failed — student %s already enrolled in class %s", student_id, class_id
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "ERR-ACAD-ALREADY_ENROLLED",
                    "message": "Student is already enrolled in this class."
                }
            )

        # 5. Validate student_code uniqueness if provided
        if student_code:
            code_conflict = EnrollmentRepository.get_by_student_code(db, student_code)
            if code_conflict:
                logger.warning(
                    "Enrollment failed — duplicate student_code: %s", student_code
                )
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "code": "ERR-ACAD-DUPLICATE_STUDENT_CODE",
                        "message": "Student code already exists in the system."
                    }
                )

        # 6. Insert enrollment record
        kwargs = {}
        if status_val and status_val != "ACTIVE":
            kwargs["status"] = status_val

        enrollment = EnrollmentRepository.create(
            db=db,
            class_id=class_id,
            student_id=student_id,
            student_code=student_code,
            **kwargs
        )
        if gender and str(gender).strip():
            EnrollmentService.save_student_metadata(db, student_id=student_id, gender=str(gender).strip())
        logger.info(
            "Domain Event: EVT-ACAD-STUDENT_ENROLLED - class_id: %s, student_id: %s",
            class_id, student_id
        )
        return enrollment

    @staticmethod
    def list_students_in_class(
        db: Session,
        class_id: UUID,
        status_val: Optional[str] = None,
        current_user: Optional[User] = None
    ) -> List[StudentClass]:
        """
        List enrolled students in a class with RBAC Data Scoping.
        Raises 404 ERR-ACAD-CLASS_NOT_FOUND if class does not exist.
        """
        cls = ClassRepository.get_by_id(db, class_id)
        if not cls:
            logger.warning("List enrollments failed — class_id not found: %s", class_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "ERR-ACAD-CLASS_NOT_FOUND",
                    "message": "Class not found."
                }
            )

        if current_user:
            check_class_access(db, current_user, class_id)

        if status_val:
            return EnrollmentRepository.list_by_class_id(db, class_id, status=status_val)
        return EnrollmentRepository.list_by_class_id(db, class_id)

    @staticmethod
    def unenroll_student(db: Session, class_id: UUID, student_id: UUID) -> None:
        """
        Unenroll a student from a class.
        Raises 404 ERR-ACAD-CLASS_NOT_FOUND if class does not exist.
        Raises 404 ERR-ACAD-ENROLLMENT_NOT_FOUND if student is not enrolled in class.
        """
        cls = ClassRepository.get_by_id(db, class_id)
        if not cls:
            logger.warning("Unenroll failed — class_id not found: %s", class_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "ERR-ACAD-CLASS_NOT_FOUND",
                    "message": "Class not found."
                }
            )

        enrollment = EnrollmentRepository.get_enrollment(db, class_id=class_id, student_id=student_id)
        if not enrollment:
            logger.warning(
                "Unenroll failed — student %s not enrolled in class %s", student_id, class_id
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "ERR-ACAD-ENROLLMENT_NOT_FOUND",
                    "message": "Enrollment record not found in class."
                }
            )

        EnrollmentRepository.delete(db, enrollment)
        logger.info(
            "Domain Event: EVT-ACAD-STUDENT_UNENROLLED - class_id: %s, student_id: %s",
            class_id, student_id
        )

    @staticmethod
    def restore_enrollment(db: Session, class_id: UUID, student_id: UUID) -> StudentClass:
        """
        Restore a soft-deleted student enrollment record for Admin.
        Raises 404 if enrollment record does not exist.
        """
        results = EnrollmentRepository.filter_enrollments(
            db, class_id=class_id, student_id=student_id, exclude_status=None
        )
        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "ERR-ACAD-ENROLLMENT_NOT_FOUND",
                    "message": "Enrollment record not found in class."
                }
            )
        enrollment = results[0]
        EnrollmentRepository.restore(db, enrollment)
        logger.info("Domain Event: EVT-ACAD-STUDENT_ENROLLMENT_RESTORED - class_id: %s, student_id: %s", class_id, student_id)
        return enrollment

    @staticmethod
    def _student_meta_key(student_id: UUID) -> str:
        return f"__STUDENT_META__:{student_id}"

    @staticmethod
    def save_student_metadata(db: Session, student_id: UUID, gender: Optional[str] = None) -> None:
        """
        Persist extended student metadata (gender) in the shared state store.
        """
        if gender is None:
            return
        from app.modules.admin.state_store import get_latest_state, upsert_state

        key = EnrollmentService._student_meta_key(student_id)
        current = get_latest_state(db, key) or {}
        current["gender"] = gender.strip() if gender else None
        upsert_state(db, key, current, actor_name="System")

    @staticmethod
    def _load_student_meta_map(db: Session) -> dict:
        from app.modules.admin.state_store import list_state_items

        meta_map = {}
        for row, payload in list_state_items(db, "__STUDENT_META__:", prefix_match=True):
            sid_str = row.title.split("__STUDENT_META__:", 1)[-1]
            meta_map[sid_str] = payload
        return meta_map

    @staticmethod
    def enrich_enrollments_out(db: Session, enrollments: List[StudentClass]):
        """
        Convert StudentClass ORM records into enriched EnrollmentOut schemas
        with email, phone, gender, dob, and birthday.
        """
        from app.modules.academic.schemas import EnrollmentOut

        if not enrollments:
            return []

        student_ids = list({e.student_id for e in enrollments})
        users = db.query(User).filter(User.user_id.in_(student_ids)).all()
        user_map = {u.user_id: u for u in users}
        meta_map = EnrollmentService._load_student_meta_map(db)

        results: List[EnrollmentOut] = []
        for enrollment in enrollments:
            user = user_map.get(enrollment.student_id)
            meta = meta_map.get(str(enrollment.student_id), {})
            bday = user.birthday if user else None
            dob_str = bday.isoformat() if bday else None
            results.append(
                EnrollmentOut(
                    student_id=enrollment.student_id,
                    class_id=enrollment.class_id,
                    student_code=enrollment.student_code,
                    student_name=user.full_name if user else enrollment.student_name,
                    email=user.email if user else None,
                    phone=user.phone if user else None,
                    gender=meta.get("gender"),
                    dob=dob_str,
                    birthday=bday,
                    status=enrollment.status,
                )
            )
        return results

    @staticmethod
    def enrich_enrollment_out(db: Session, enrollment: StudentClass):
        """
        Enrich a single StudentClass enrollment into EnrollmentOut.
        """
        return EnrollmentService.enrich_enrollments_out(db, [enrollment])[0]

    @staticmethod
    def get_available_students(
        db: Session,
        class_id: Optional[UUID] = None,
        search: Optional[str] = None,
        limit: int = 100,
    ):
        """
        List non-deleted Student users not currently enrolled in the given class_id.
        """
        from sqlalchemy import func, or_
        from app.modules.academic.schemas import AvailableStudentItem

        query = (
            db.query(User)
            .join(Role, User.role_id == Role.role_id)
            .filter(
                func.lower(Role.name) == "student",
                func.upper(User.status) != "DELETED",
            )
        )

        if class_id is not None:
            enrolled_ids = (
                db.query(StudentClass.student_id)
                .filter(
                    StudentClass.class_id == class_id,
                    func.upper(StudentClass.status) != "DELETED",
                )
                .distinct()
            )
            query = query.filter(~User.user_id.in_(enrolled_ids))

        if search and search.strip():
            term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    User.full_name.ilike(term),
                    User.email.ilike(term),
                    User.phone.ilike(term),
                )
            )

        users = query.order_by(User.full_name.asc()).limit(limit).all()
        if not users:
            return []

        user_ids = [u.user_id for u in users]
        existing_codes = (
            db.query(StudentClass.student_id, StudentClass.student_code)
            .filter(
                StudentClass.student_id.in_(user_ids),
                StudentClass.student_code.isnot(None),
                func.upper(StudentClass.status) != "DELETED",
            )
            .all()
        )
        code_map = {sid: code for sid, code in existing_codes if code}
        meta_map = EnrollmentService._load_student_meta_map(db)

        items: List[AvailableStudentItem] = []
        for user in users:
            meta = meta_map.get(str(user.user_id), {})
            bday = user.birthday
            items.append(
                AvailableStudentItem(
                    user_id=user.user_id,
                    student_id=user.user_id,
                    full_name=user.full_name,
                    student_name=user.full_name,
                    student_code=code_map.get(user.user_id),
                    email=user.email,
                    phone=user.phone,
                    gender=meta.get("gender"),
                    dob=bday.isoformat() if bday else None,
                    birthday=bday,
                    status=user.status,
                )
            )
        return items

    @staticmethod
    def import_students_from_rows(
        db: Session,
        class_id: UUID,
        rows: list,
    ):
        """
        Import and enroll students from parsed CSV/XLSX rows into a target class.
        Finds existing students by email, phone, or student_code; creates new Student accounts if absent.
        """
        import re
        import uuid as py_uuid
        from datetime import date
        from sqlalchemy import func
        from app.core.security import get_password_hash
        from app.modules.academic.schemas import StudentImportErrorItem, StudentImportExcelResponse
        from app.modules.admin.services.user_import_service import (
            _cell_text,
            _normalize_phone,
            _parse_birthday,
        )

        cls = ClassRepository.get_by_id(db, class_id)
        if not cls:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "ERR-ACAD-CLASS_NOT_FOUND", "message": "Class not found."},
            )

        student_role = db.query(Role).filter(func.lower(Role.name) == "student").first()
        if not student_role:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"code": "ERR-ACAD-ROLE_NOT_FOUND", "message": "Student role not found in system."},
            )

        def _pick(record: dict, *aliases: str) -> str:
            for alias in aliases:
                if alias in record and record[alias] is not None:
                    text = _cell_text(record[alias])
                    if text:
                        return text
            return ""

        enrolled_orm: List[StudentClass] = []
        errors: List[StudentImportErrorItem] = []

        for idx, row in enumerate(rows, start=2):
            row_num = int(row.get("__row_num__", idx))
            try:
                full_name = _pick(
                    row,
                    "full_name",
                    "fullname",
                    "student_name",
                    "name",
                    "họ và tên",
                    "ho va ten",
                    "họ tên",
                    "ho ten",
                    "tên học sinh",
                    "ten hoc sinh",
                )
                student_code = _pick(
                    row,
                    "student_code",
                    "code",
                    "mã học sinh",
                    "ma hoc sinh",
                    "mã hs",
                    "ma hs",
                ) or None
                email = _pick(row, "email", "e-mail", "mail").lower() or None
                raw_phone = _pick(row, "phone", "số điện thoại", "so dien thoai", "sđt", "sdt", "điện thoại", "dien thoai")
                phone = _normalize_phone(raw_phone) if raw_phone else None
                gender = _pick(row, "gender", "giới tính", "gioi tinh", "sex") or None

                raw_bday = None
                for b_alias in ("birthday", "dob", "ngày sinh", "ngay sinh", "birth_date"):
                    if b_alias in row and row[b_alias] not in (None, ""):
                        raw_bday = row[b_alias]
                        break
                parsed_bday = _parse_birthday(raw_bday) if raw_bday is not None else None
                if raw_bday is not None and parsed_bday is None:
                    errors.append(
                        StudentImportErrorItem(row=row_num, message="Invalid date of birth format.")
                    )
                    continue

                if phone and not re.match(r"^0\d{9,10}$", phone):
                    errors.append(
                        StudentImportErrorItem(row=row_num, message=f"Invalid phone number '{raw_phone}'.")
                    )
                    continue

                # Locate existing non-deleted user by email, phone, or student_code
                matched_user = None
                if email:
                    matched_user = (
                        db.query(User)
                        .filter(func.lower(User.email) == email, func.upper(User.status) != "DELETED")
                        .first()
                    )
                if not matched_user and phone:
                    matched_user = (
                        db.query(User)
                        .filter(User.phone == phone, func.upper(User.status) != "DELETED")
                        .first()
                    )
                if not matched_user and student_code:
                    existing_code_row = (
                        db.query(StudentClass)
                        .filter(
                            StudentClass.student_code == student_code,
                            func.upper(StudentClass.status) != "DELETED",
                        )
                        .first()
                    )
                    if existing_code_row:
                        matched_user = (
                            db.query(User)
                            .filter(
                                User.user_id == existing_code_row.student_id,
                                func.upper(User.status) != "DELETED",
                            )
                            .first()
                        )

                if matched_user:
                    role_obj = db.query(Role).filter(Role.role_id == matched_user.role_id).first()
                    if not role_obj or role_obj.name.lower() != "student":
                        errors.append(
                            StudentImportErrorItem(row=row_num, message="Matched user does not have Student role.")
                        )
                        continue
                    if matched_user.status.upper() != "ACTIVE":
                        errors.append(
                            StudentImportErrorItem(row=row_num, message="Matched student account is not ACTIVE.")
                        )
                        continue

                    existing_enrollment = (
                        db.query(StudentClass)
                        .filter(
                            StudentClass.class_id == class_id,
                            StudentClass.student_id == matched_user.user_id,
                        )
                        .first()
                    )
                    if existing_enrollment:
                        if existing_enrollment.status.upper() != "DELETED":
                            errors.append(
                                StudentImportErrorItem(
                                    row=row_num,
                                    message="Student is already enrolled in this class.",
                                )
                            )
                            continue
                        existing_enrollment.status = "ACTIVE"
                        if student_code and not existing_enrollment.student_code:
                            code_conflict = EnrollmentRepository.get_by_student_code(db, student_code)
                            if code_conflict and code_conflict.student_id != matched_user.user_id:
                                errors.append(
                                    StudentImportErrorItem(
                                        row=row_num,
                                        message=f"Student code '{student_code}' is already in use.",
                                    )
                                )
                                continue
                            existing_enrollment.student_code = student_code
                        db.commit()
                        db.refresh(existing_enrollment)
                        if gender:
                            EnrollmentService.save_student_metadata(db, matched_user.user_id, gender=gender)
                        enrolled_orm.append(existing_enrollment)
                        continue

                    if student_code:
                        code_conflict = EnrollmentRepository.get_by_student_code(db, student_code)
                        if code_conflict and code_conflict.student_id != matched_user.user_id:
                            errors.append(
                                StudentImportErrorItem(
                                    row=row_num,
                                    message=f"Student code '{student_code}' is already in use.",
                                )
                            )
                            continue

                    enrollment = EnrollmentRepository.create(
                        db=db,
                        class_id=class_id,
                        student_id=matched_user.user_id,
                        student_code=student_code,
                    )
                    if gender:
                        EnrollmentService.save_student_metadata(db, matched_user.user_id, gender=gender)
                    enrolled_orm.append(enrollment)
                else:
                    if not full_name:
                        errors.append(
                            StudentImportErrorItem(
                                row=row_num,
                                message="Missing student full name for new student record.",
                            )
                        )
                        continue

                    if parsed_bday:
                        today = date.today()
                        age = (
                            today.year
                            - parsed_bday.year
                            - ((today.month, today.day) < (parsed_bday.month, parsed_bday.day))
                        )
                        if age < 16:
                            errors.append(
                                StudentImportErrorItem(
                                    row=row_num,
                                    message=f"Student must be at least 16 years old (calculated: {age}).",
                                )
                            )
                            continue

                    if student_code:
                        code_conflict = EnrollmentRepository.get_by_student_code(db, student_code)
                        if code_conflict:
                            errors.append(
                                StudentImportErrorItem(
                                    row=row_num,
                                    message=f"Student code '{student_code}' is already in use.",
                                )
                            )
                            continue

                    new_user = User(
                        user_id=py_uuid.uuid4(),
                        full_name=full_name,
                        email=email,
                        phone=phone,
                        birthday=parsed_bday,
                        role_id=student_role.role_id,
                        # Random unknown password; admin must issue a reset to enable login.
                        password_hash=get_password_hash(secrets.token_urlsafe(16)),
                        status="ACTIVE",
                    )
                    # Flush only: EnrollmentRepository.create commits user and enrollment atomically.
                    db.add(new_user)
                    db.flush()

                    enrollment = EnrollmentRepository.create(
                        db=db,
                        class_id=class_id,
                        student_id=new_user.user_id,
                        student_code=student_code,
                    )
                    if gender:
                        EnrollmentService.save_student_metadata(db, new_user.user_id, gender=gender)
                    enrolled_orm.append(enrollment)
            except Exception as exc:
                db.rollback()
                logger.warning("Row %d import failed for class %s: %s", row_num, class_id, exc)
                errors.append(
                    StudentImportErrorItem(row=row_num, message=str(exc))
                )

        enriched = EnrollmentService.enrich_enrollments_out(db, enrolled_orm)
        logger.info(
            "Domain Event: EVT-ACAD-STUDENTS_IMPORTED - class_id: %s, imported: %d, errors: %d",
            class_id,
            len(enriched),
            len(errors),
        )
        return StudentImportExcelResponse(
            imported_count=len(enriched),
            enrolled_students=enriched,
            errors=errors,
        )
