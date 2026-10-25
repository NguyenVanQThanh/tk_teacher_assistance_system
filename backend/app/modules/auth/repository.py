"""
File Name: repository.py
Description: Repository layer for authentication module, querying user database records.
Created At: 2026-07-16
Created By: Tam Khang
Updated At: 2026-07-16
Updated By: Tam Khang
"""
import uuid
from typing import Optional
from sqlalchemy.orm import Session
from models.models import User, Role

class UserRepository:
    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[User]:
        """
        Retrieve a user from the database by email address.
        """
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def get_by_phone(db: Session, phone: str) -> Optional[User]:
        """
        Retrieve a user from the database by phone number.
        """
        return db.query(User).filter(User.phone == phone).first()
    @staticmethod
    def create(db: Session, full_name: str,role_id: uuid.UUID, phone: str, password_hash: str) -> User:
        """
        Create a new user.
        """
        user = User(full_name=full_name,role_id=role_id, phone=phone, password_hash=password_hash)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

class RoleRepository:
    @staticmethod
    def get_by_name(db: Session, name: str) -> Optional[User]:
        """
        Retrieve a role from the database by name.
        """
        return db.query(Role).filter(Role.name == name).first()
