"""
File Name: repository.py
Description: Repository layer for authentication module, querying user database records.
Created At: 2026-07-16
Created By: Tam Khang
Updated At: 2026-07-16
Updated By: Tam Khang
"""
from typing import Optional
from sqlalchemy.orm import Session
from models.models import User

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
