"""
File Name: seed.py
Description: Script to seed the initial database with sample roles.
Created At: 2026-07-05
Created By: Thanh Nguyen
Updated At: 2026-07-05
Updated By: Thanh Nguyen
"""

import os
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

from models.base import Base
from models.models import Role, Permission

# Load environment variables
load_dotenv()

# Read database configuration from the environment
DB_USERNAME = os.environ.get("DB_USERNAME")
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
    session = SessionLocal()
    try:
        # 1. Check if data already exists to avoid duplication
        if session.query(Role).first() is not None:
            print("Database already contains sample data!")
            return

        print("Initializing sample data...")

        # 2. Create sample Roles
        admin_role = Role(name="Admin", description="System Administrator")
        teacher_role = Role(name="Teacher", description="Teacher")
        student_role = Role(name="Student", description="Student")

        session.add_all([admin_role, teacher_role, student_role])
        session.commit()
        print("Successfully seeded sample data into Roles table!")

    except Exception as e:
        session.rollback()
        print(f"An error occurred while seeding data: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    seed_data()
