# File Name: update_passwords.py
# Description: Script to reset sample user passwords.
# Created At: 2026-08-30
# Created By: Tam Khang
# Updated At: 2026-08-30
# Updated By: Tam Khang

import os
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.models import User
from app.core.security import get_password_hash, verify_password

DB_USERNAME = os.environ.get("DB_USERNAME")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME")

db_url = f"postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(db_url)
Session = sessionmaker(bind=engine)
session = Session()

accounts = [
    ("0999000001", "Admin@1234"),
    ("0999000002", "Teacher@1234"),
    ("0999000003", "Student@1234"),
]

for phone, plain_pw in accounts:
    user = session.query(User).filter(User.phone == phone).first()
    if user:
        user.password_hash = get_password_hash(plain_pw)
        session.commit()
        print(f"Updated {phone} -> verified: {verify_password(plain_pw, user.password_hash)}")
    else:
        print(f"User {phone} not found")

session.close()
