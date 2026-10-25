# File Name: models.py
# Description: Re-export SQLAlchemy models for the academic module.
# Created At: 2026-07-21
# Created By: Tam Khang
# Updated At: 2026-07-23
# Updated By: Tam Khang

from models.models import Subject, Class, StudentClass, TeacherSubject

__all__ = ["Subject", "Class", "StudentClass", "TeacherSubject"]



