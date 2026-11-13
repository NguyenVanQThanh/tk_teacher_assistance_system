# File Name: seed.py
# Description: Script to seed the initial database with roles, permissions, and role-permission mappings.
# Created At: 2026-07-17
# Created By: Tam Khang
# Updated At: 2026-11-14
# Updated By: AI Agent

import os
import sys
from pathlib import Path

# Ensure backend root is in sys.path
backend_root = str(Path(__file__).resolve().parent.parent.parent)
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.scripts.rbac_seed import seed_rbac

# Load environment variables
load_dotenv()

# Read database configuration from the environment
DB_USERNAME = os.environ.get("DB_USERNAME") or os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME")

if not all([DB_USERNAME, DB_PASSWORD, DB_NAME]):
    raise ValueError("Missing database configuration in environment variables")

DATABASE_URL = f"postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def seed_data():
    """Seed roles, permissions and role-permission mappings (idempotent).

    The data itself lives in app/scripts/rbac_seed.py so production can reuse it
    from bootstrap_admin.py without importing this CLI module.
    """
    session = SessionLocal()
    try:
        print("Initializing database seed data...")
        seed_rbac(session)
        session.commit()
        print("Database seed process completed successfully!")

    except Exception as e:
        session.rollback()
        print(f"An error occurred while seeding data: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    seed_data()
