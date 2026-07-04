# models/sprint_0.py
import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, DateTime, CheckConstraint, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from models.base import Base

# =====================================================================
# 1. QUẢN LÝ TÀI KHOẢN & PHÂN QUYỀN
# =====================================================================

class User(Base):
    __tablename__ = 'users'

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone = Column(String(20), unique=True, nullable=True)
    email = Column(String(100), unique=True, nullable=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    birthday = Column(Date, nullable=True)
    role_id = Column(UUID(as_uuid=True), ForeignKey('roles.role_id'), nullable=False) # Lưu ý: Bạn cần định nghĩa bảng roles trước nếu có lỗi
    status = Column(String(20), default='Active')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Permission(Base):
    __tablename__ = 'permissions'

    permission_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    permission_code = Column(String(100), unique=True, nullable=False)
    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    module = Column(String(50), nullable=True)
    http_method = Column(String(10), nullable=True)
    url_pattern = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class RolePermission(Base):
    __tablename__ = 'role_permissions'

    role_id = Column(UUID(as_uuid=True), ForeignKey('roles.role_id', ondelete='CASCADE'), nullable=False)
    permission_id = Column(UUID(as_uuid=True), ForeignKey('permissions.permission_id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        PrimaryKeyConstraint('role_id', 'permission_id'),
    )


class UserPermission(Base):
    __tablename__ = 'user_permissions'

    user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    permission_id = Column(UUID(as_uuid=True), ForeignKey('permissions.permission_id', ondelete='CASCADE'), nullable=False)
    effect = Column(String(5), nullable=False, default='allow')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        PrimaryKeyConstraint('user_id', 'permission_id'),
        CheckConstraint("effect IN ('allow', 'deny')", name='chk_user_perm_effect'),
    )


# =====================================================================
# 2. CƠ CẤU TỔ CHỨC
# =====================================================================

class Subject(Base):
    __tablename__ = 'subjects'

    subject_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subject_name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Class(Base):
    __tablename__ = 'classes'

    class_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    class_name = Column(String(50), unique=True, nullable=False)
    homeroom_teacher_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='SET NULL'), nullable=True)
    academic_year = Column(String(20), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class StudentClass(Base):
    __tablename__ = 'student_class'

    student_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    class_id = Column(UUID(as_uuid=True), ForeignKey('classes.class_id', ondelete='CASCADE'), nullable=False)
    student_code = Column(String(50), unique=True, nullable=True)

    __table_args__ = (
        PrimaryKeyConstraint('student_id', 'class_id'),
    )


class TeacherSubject(Base):
    __tablename__ = 'teacher_subjects'

    teacher_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    class_id = Column(UUID(as_uuid=True), ForeignKey('classes.class_id', ondelete='CASCADE'), nullable=False)
    subject_id = Column(UUID(as_uuid=True), ForeignKey('subjects.subject_id', ondelete='CASCADE'), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint('teacher_id', 'class_id', 'subject_id'),
    )


# =====================================================================
# 3. HỌC LIỆU & BÀI TẬP
# =====================================================================

class Document(Base):
    __tablename__ = 'documents'

    document_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    subject_id = Column(UUID(as_uuid=True), ForeignKey('subjects.subject_id', ondelete='SET NULL'), nullable=True)
    title = Column(String(255), nullable=False)
    file_url = Column(String(500), nullable=True)
    file_type = Column(String(20), nullable=True)
    raw_content = Column(Text, nullable=True)
    status = Column(String(20), default='Uploaded')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
class Role(Base):
    __tablename__ = 'roles'
    
    role_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

