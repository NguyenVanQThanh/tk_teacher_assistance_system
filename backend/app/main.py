# File Name: main.py
# Description: Main entry point of the FastAPI application.
# Created At: 2026-07-17
# Created By: Tam Khang
# Updated At: 2026-08-30
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

@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)