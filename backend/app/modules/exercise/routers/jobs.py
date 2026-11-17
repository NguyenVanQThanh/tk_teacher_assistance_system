"""
File Name: jobs.py
Description: Per-user view of background jobs (progress, ETA, history) for the job tray in the frontend.
Created At: 2026-11-17
Created By: AI Agent
Updated At: 2026-11-17
Updated By: AI Agent
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.background_jobs import get_job, list_jobs
from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user
from models.models import User

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


@router.get("")
def my_jobs(active: bool = Query(False, description="Only queued/running jobs"),
            limit: int = Query(20, ge=1, le=50),
            db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> List[dict]:
    """The caller's jobs, newest first."""
    return list_jobs(db, current_user.user_id, active_only=active, limit=limit)


@router.get("/{job_id}")
def job_detail(job_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> dict:
    """One job of the caller: status, progress, stage, ETA and result/error."""
    job = get_job(db, job_id, current_user.user_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail={"code": "ERR-EXE-AI_JOB_NOT_FOUND", "message": "Job not found."})
    return job
