# File Name: main.py
# Description: Main entry point of the FastAPI application.
# Created At: 2026-07-17
# Created By: Tam Khang
# Updated At: 2026-07-21
# Updated By: Tam Khang

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from fastapi import FastAPI
from app.modules.auth.routers.auth import router as auth_router
from app.modules.academic.routers.subjects import router as subjects_router

app = FastAPI(title="SmartLMS API", version="1.0.0")

# Register routers
app.include_router(auth_router)
app.include_router(subjects_router)

@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)