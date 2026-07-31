# File Name: main.py
# Description: Main entry point of the FastAPI application.
# Created At: 2026-07-17
# Created By: Tam Khang
# Updated At: 2026-07-23
# Updated By: Tam Khang

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from fastapi import FastAPI
from app.modules.auth.routers.auth import router as auth_router
from app.modules.academic.routers.subjects import router as subjects_router
from app.modules.academic.routers.classes import router as classes_router
from app.modules.academic.routers.enrollments import router as enrollments_router
from app.modules.academic.routers.teacher_assignments import router as teacher_assignments_router
from app.modules.exercise.routers.exercises import router as exercises_router
from app.modules.exercise.routers.questions import router as questions_router
from app.modules.exercise.routers.assignments import router as assignments_router

app = FastAPI(title="SmartLMS API", version="1.0.0")

# Register routers
# Trigger uvicorn reload to refresh in-memory permission cache
app.include_router(auth_router)
app.include_router(subjects_router)
app.include_router(classes_router)
app.include_router(enrollments_router)
app.include_router(teacher_assignments_router)
app.include_router(exercises_router)
app.include_router(questions_router)
app.include_router(assignments_router)





@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)