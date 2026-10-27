# File Name: main.py
# Description: Main entry point of the FastAPI application.
# Created At: 2026-07-17
# Created By: Tam Khang
# Updated At: 2026-10-04 17:27:00
# Updated By: Tam Khang

import sys
from pathlib import Path

# Ensure backend root is always in python sys.path
backend_root = str(Path(__file__).resolve().parent.parent)
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.modules.auth.routers.auth import router as auth_router
from app.modules.academic.routers.subjects import router as subjects_router
from app.modules.academic.routers.classes import router as classes_router
from app.modules.academic.routers.enrollments import router as enrollments_router
from app.modules.academic.routers.teacher_assignments import router as teacher_assignments_router
from app.modules.exercise.routers.exercises import router as exercises_router
from app.modules.exercise.routers.questions import router as questions_router
from app.modules.exercise.routers.assignments import router as assignments_router
from app.modules.exercise.routers.attempts import router as attempts_router
from app.modules.document.routers.documents import router as documents_router
from app.modules.admin.routers.users import router as admin_users_router
from app.modules.admin.routers.dashboard import router as admin_dashboard_router
from app.modules.exercise.routers.student_dashboard import router as student_dashboard_router
from app.modules.exercise.routers.teacher_schedule import router as teacher_schedule_router
from app.modules.exercise.routers.teacher_dashboard import router as teacher_dashboard_router

app = FastAPI(title="SmartLMS API", version="1.0.0")

# Enable CORS for Frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_router)
app.include_router(subjects_router)
app.include_router(classes_router)
app.include_router(enrollments_router)
app.include_router(teacher_assignments_router)
app.include_router(exercises_router)
app.include_router(questions_router)
app.include_router(assignments_router)
app.include_router(attempts_router)
app.include_router(documents_router)
app.include_router(admin_users_router)
app.include_router(admin_dashboard_router)
app.include_router(student_dashboard_router)
app.include_router(teacher_schedule_router)
app.include_router(teacher_dashboard_router)

@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0.1"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)