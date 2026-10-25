# File Name: update_passwords.py
# Description: Script to reset sample user passwords.
# Created At: 2026-08-30
# Created By: Tam Khang
# Updated At: 2026-09-12
# Updated By: Tam Khang

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Ensure UTF-8 output encoding on Windows console
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

backend_root = str(Path(__file__).resolve().parent.parent.parent)
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

load_dotenv()

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.models import User, Role
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

json_path = os.path.join(os.path.dirname(__file__), "seed_accounts_info.json")
if os.path.exists(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        accounts = json.load(f)
else:
    accounts = [
        {"phone": "0999000001", "password_plain": "Admin@1234"},
        {"phone": "0999000002", "password_plain": "Teacher@1234"},
        {"phone": "0999000003", "password_plain": "Student@1234"},
    ]

updated_count = 0
for acc in accounts:
    phone = acc.get("phone")
    plain_pw = acc.get("password_plain", "Student@1234" if "student" in acc.get("email", "") else "Teacher@1234")
    user = session.query(User).filter(User.phone == phone).first()
    if user:
        user.password_hash = get_password_hash(plain_pw)
        if user.status not in ["Active", "ACTIVE"]:
            user.status = "ACTIVE"
        session.flush()
        updated_count += 1
        print(f"Updated {phone} ({user.full_name}) -> verified: {verify_password(plain_pw, user.password_hash)}")

session.commit()
session.close()
print(f"Successfully updated {updated_count} accounts.")
