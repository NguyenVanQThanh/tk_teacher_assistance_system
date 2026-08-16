"""
File Name: models.py
Description: Database models definition for Sprint 0 & Sprint 2 tables (User, Role, Permission, Exercise, Question, AnswerOption, etc.).
Created At: 2026-07-04
Created By: Tam Khang
Updated At: 2026-08-09
Updated By: Tam Khang
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, DateTime, CheckConstraint, PrimaryKeyConstraint, Boolean, JSON, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from models.base import Base


# =====================================================================
# 1. ACCOUNT MANAGEMENT & AUTHORIZATION
# =====================================================================

class User(Base):
    __tablename__ = 'users'

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone = Column(String(20), unique=True, nullable=True)
    email = Column(String(100), unique=True, nullable=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    birthday = Column(Date, nullable=True)
    role_id = Column(UUID(as_uuid=True), ForeignKey('roles.role_id'), nullable=False) # Note: You need to define the roles table first if errors occur
    status = Column(String(20), default='ACTIVE')
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
# 2. ORGANIZATIONAL STRUCTURE
# =====================================================================

class Subject(Base):
    __tablename__ = 'subjects'

    subject_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subject_name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), default='ACTIVE', nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Class(Base):
    __tablename__ = 'classes'

    class_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    class_name = Column(String(50), unique=True, nullable=False)
    homeroom_teacher_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='SET NULL'), nullable=True)
    academic_year = Column(String(20), nullable=True)
    status = Column(String(20), default='ACTIVE', nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class StudentClass(Base):
    __tablename__ = 'student_class'

    student_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    class_id = Column(UUID(as_uuid=True), ForeignKey('classes.class_id', ondelete='CASCADE'), nullable=False)
    student_code = Column(String(50), unique=True, nullable=True)
    status = Column(String(20), default='ACTIVE', nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint('student_id', 'class_id'),
    )


class TeacherSubject(Base):
    __tablename__ = 'teacher_subjects'

    teacher_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    class_id = Column(UUID(as_uuid=True), ForeignKey('classes.class_id', ondelete='CASCADE'), nullable=False)
    subject_id = Column(UUID(as_uuid=True), ForeignKey('subjects.subject_id', ondelete='CASCADE'), nullable=False)
    status = Column(String(20), default='ACTIVE', nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint('teacher_id', 'class_id', 'subject_id'),
    )


# =====================================================================
# 3. LEARNING MATERIALS & ASSIGNMENTS
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


class Exercise(Base):
    __tablename__ = 'exercises'

    exercise_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    subject_id = Column(UUID(as_uuid=True), ForeignKey('subjects.subject_id', ondelete='CASCADE'), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    total_questions = Column(Integer, default=0)
    ai_metadata = Column(JSON, nullable=True)
    status = Column(String(20), default='ACTIVE', nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    questions = relationship("Question", back_populates="exercise", cascade="all, delete-orphan")


class Question(Base):
    __tablename__ = 'questions'

    question_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    exercise_id = Column(UUID(as_uuid=True), ForeignKey('exercises.exercise_id', ondelete='CASCADE'), nullable=False)
    document_id = Column(UUID(as_uuid=True), ForeignKey('documents.document_id', ondelete='SET NULL'), nullable=True)
    content = Column(Text, nullable=False)
    content_markdown = Column(Text, nullable=True)
    content_latex = Column(Text, nullable=True)
    segments = Column(JSON, nullable=True)
    confidence_score = Column(Numeric(5, 2), nullable=True)
    needs_review = Column(Boolean, default=False, nullable=False)
    question_type = Column(String(20), nullable=False, default='MultipleChoice')
    difficulty = Column(String(20), nullable=True)
    correct_answer = Column(Text, nullable=True)
    explanation = Column(Text, nullable=True)
    display_order = Column(Integer, default=0)
    image_url = Column(String(500), nullable=True)
    is_ai_generated = Column(Boolean, default=False)
    status = Column(String(20), default='ACTIVE', nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    exercise = relationship("Exercise", back_populates="questions")
    answer_options = relationship("AnswerOption", back_populates="question", cascade="all, delete-orphan")


class AnswerOption(Base):
    __tablename__ = 'answer_options'

    option_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id = Column(UUID(as_uuid=True), ForeignKey('questions.question_id', ondelete='CASCADE'), nullable=False)
    content = Column(Text, nullable=False)
    is_correct = Column(Boolean, default=False)
    display_order = Column(Integer, default=0)

    question = relationship("Question", back_populates="answer_options")


class ClassAssignment(Base):
    __tablename__ = 'class_assignments'

    assignment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    class_id = Column(UUID(as_uuid=True), ForeignKey('classes.class_id', ondelete='CASCADE'), nullable=False)
    exercise_id = Column(UUID(as_uuid=True), ForeignKey('exercises.exercise_id', ondelete='CASCADE'), nullable=False)
    assigned_by = Column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    due_at = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(20), default='ACTIVE', nullable=False)

    class_obj = relationship("Class", backref="assignments")
    exercise = relationship("Exercise", backref="assignments")
    assigner = relationship("User", backref="created_assignments")



class Role(Base):
    __tablename__ = 'roles'
    
    role_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())


class StudentExerciseAttempt(Base):
    __tablename__ = 'student_exercise_attempts'

    attempt_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    assignment_id = Column(UUID(as_uuid=True), ForeignKey('class_assignments.assignment_id', ondelete='CASCADE'), nullable=False)
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    end_time = Column(DateTime(timezone=True), nullable=True)
    total_time_seconds = Column(Integer, nullable=True)
    score = Column(Numeric(5, 2), nullable=True)
    detailed_results = Column(JSON, nullable=True)
    is_finished = Column(Boolean, default=False, nullable=False)
    status = Column(String(20), default='ACTIVE', nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    student = relationship("User", backref="exercise_attempts")
    assignment = relationship("ClassAssignment", backref="attempts")



