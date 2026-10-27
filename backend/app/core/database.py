# File Name: database.py
# Description: Database session setup and get_db dependency.
# Created At: 2026-07-17
# Created By: Tam Khang
# Updated At: 2026-09-27
# Updated By: Tam Khang

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

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

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    f"postgresql+psycopg2://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
