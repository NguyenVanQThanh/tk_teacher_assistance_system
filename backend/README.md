# SmartLMS — Backend Service (FastAPI)

## 1. Overview
The backend service of SmartLMS built with Python 3.11+, FastAPI, SQLAlchemy 2.0, PostgreSQL, and Alembic.

## 2. Directory Structure
```text
backend/
├── alembic/              # Database migration scripts
├── alembic.ini           # Alembic configuration
├── app/                  # Application source code
│   ├── core/             # Core settings, database session, security, error handlers
│   ├── modules/          # Domain modules (auth, academic, exercise, etc.)
│   ├── scripts/          # Seed data & utility scripts
│   └── main.py           # FastAPI entrypoint
├── models/               # SQLAlchemy ORM models & declarative base
├── tests/                # Test suites (unit, integration, e2e)
├── requirements.txt      # Python dependencies
├── pytest.ini            # Pytest configuration
├── migration.sql         # SQL schema baseline
└── .env.example          # Sample environment variables
```

## 3. Setup & Running Locally

### Prerequisites
- Python 3.11+
- PostgreSQL 16+

### Steps
1. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux/macOS:
   source .venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   Copy `.env.example` to `.env` and fill in your database credentials:
   ```bash
   cp .env.example .env
   ```

4. Run Database Migrations:
   ```bash
   alembic upgrade head
   ```

5. Start the development server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

6. Run Tests:
   ```bash
   pytest
   ```
