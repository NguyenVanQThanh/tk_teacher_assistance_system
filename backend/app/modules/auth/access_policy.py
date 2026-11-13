# File Name: access_policy.py
# Description: Central RBAC policy for documents and exercises (visibility clauses and owner-only write checks).
# Created At: 2026-11-13
# Created By: AI Agent
# Updated At: 2026-11-13
# Updated By: AI Agent

from typing import Iterable, Optional, Set
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import and_, exists, false, or_
from sqlalchemy.orm import Session

from models.models import Document, Exercise, Role, Subject, TeacherSubject, User

TEACHER_ROLES = {"teacher", "homeroomteacher"}


def _role_name(db: Session, user: User) -> str:
    role = db.query(Role).filter(Role.role_id == user.role_id).first()
    return (role.name if role else "").lower()


def is_admin(db: Session, user: User) -> bool:
    """Return True when the user's role is Admin (case-insensitive)."""
    return _role_name(db, user) == "admin"


def is_teacher(role_name: str) -> bool:
    """Return True for the 'Teacher' and 'HomeroomTeacher' role names."""
    return (role_name or "").lower() in TEACHER_ROLES


def _head_shared_clause(user: User, subject_col, owner_col):
    """True when the resource owner heads the resource's subject and the user actively teaches that subject."""
    return exists().where(
        and_(
            Subject.subject_id == subject_col,
            Subject.head_teacher_id == owner_col,
            Subject.status != "DELETED",
            TeacherSubject.subject_id == Subject.subject_id,
            TeacherSubject.teacher_id == user.user_id,
            TeacherSubject.status == "ACTIVE",
        )
    )


def document_visibility_clause(db: Session, user: User):
    """Filter on Document for the user; None means unrestricted (Admin). Students see nothing."""
    role = _role_name(db, user)
    if role == "admin":
        return None
    if not is_teacher(role):
        return false()
    # Own documents, or published documents authored by the head of a subject the teacher teaches.
    return or_(
        Document.uploaded_by == user.user_id,
        and_(
            Document.status == "Uploaded",
            _head_shared_clause(user, Document.subject_id, Document.uploaded_by),
        ),
    )


def exercise_visibility_clause(db: Session, user: User):
    """Filter on Exercise for the user; None means unrestricted (Admin). Students see only their own."""
    role = _role_name(db, user)
    if role == "admin":
        return None
    if not is_teacher(role):
        return Exercise.created_by == user.user_id
    return or_(
        Exercise.created_by == user.user_id,
        _head_shared_clause(user, Exercise.subject_id, Exercise.created_by),
    )


def visible_document_ids(db: Session, user: User, ids: Optional[Iterable[UUID]]) -> Set[UUID]:
    """Return the subset of the given document ids the user may see (non-deleted)."""
    id_list = list(ids or [])
    if not id_list:
        return set()
    query = db.query(Document.document_id).filter(
        Document.document_id.in_(id_list), Document.status != "DELETED"
    )
    clause = document_visibility_clause(db, user)
    if clause is not None:
        query = query.filter(clause)
    return {row[0] for row in query.all()}


def ensure_can_write(db: Session, user: User, owner_id: Optional[UUID]) -> None:
    """Raise 403 ERR-AUTH-OWNER_ONLY unless the user is the owner or an Admin."""
    if owner_id is not None and owner_id == user.user_id:
        return
    if is_admin(db, user):
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={"code": "ERR-AUTH-OWNER_ONLY", "message": "Only the owner can modify this resource."},
    )
