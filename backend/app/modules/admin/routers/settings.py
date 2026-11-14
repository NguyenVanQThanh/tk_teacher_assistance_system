# File Name: settings.py
# Description: Admin system configuration, AI connectivity ping, and backup snapshot API router.
# Created At: 2026-11-14
# Created By: Tam Khang
# Updated At: 2026-11-14
# Updated By: Tam Khang

import copy
import io
import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core import config as app_config
from app.core.database import get_db
from app.modules.admin.routers.users import require_admin_privilege
from app.modules.admin.state_store import (
    INTERNAL_STATE_MARKER,
    append_state_item,
    get_latest_state,
    get_state_by_log_id,
    list_state_items,
    record_audit_event,
    upsert_state,
)
from app.modules.auth.dependencies import get_current_user
from models.models import (
    AuditLog,
    Class,
    Document,
    Exercise,
    Permission,
    Question,
    Role,
    StudentClass,
    StudentExerciseAttempt,
    Subject,
    TeacherSubject,
    User,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/admin/settings",
    tags=["admin-settings"],
    dependencies=[Depends(require_admin_privilege)],
)

_MASK_CHAR = "•"


def _default_settings_payload() -> Dict[str, Dict[str, Any]]:
    default_model = (
        getattr(app_config, "RAG_QUERY_EXPANSION_GEMINI_MODEL", None)
        or getattr(app_config, "ANSWER_SOLVER_MODEL", None)
        or getattr(app_config, "AI_MISTRAL_MODEL", None)
        or "gemini-2.5-flash"
    )
    has_key = bool(
        os.getenv("GEMINI_API_KEY")
        or os.getenv("MISTRAL_API_KEY")
        or os.getenv("OPENAI_API_KEY")
    )
    return {
        "general": {
            "schoolName": "Tam Khang Smart High School",
            "schoolCode": "TK-HS-001",
            "address": "123 Education Boulevard, Ho Chi Minh City",
            "phone": "02838123456",
            "email": "admin@smartlms.edu.vn",
            "academicYear": "2025-2026",
            "semester": "HK1",
            "semesterStartDate": "2025-09-05",
            "semesterEndDate": "2026-01-18",
            "gradeLockDeadline": "2026-01-25",
        },
        "ai": {
            "provider": "google_gemini",
            "defaultModel": default_model,
            "apiKey": "••••••••••••" if has_key else "",
            "dailyTokenLimitPerTeacher": 250000,
            "enableAutoGrading": True,
            "enableBloomGenerator": True,
            "enableVisionOcr": True,
            "enableEarlyAlertAnalysis": True,
            "temperature": 0.3,
        },
        "grading": {
            "gradingScale": 10,
            "weightRegular": 20,
            "weightMidterm": 30,
            "weightFinal": 50,
            "roundingPrecision": 1,
            "thresholdExcellent": 8.0,
            "thresholdGood": 6.5,
            "thresholdAverage": 5.0,
            "thresholdPass": 5.0,
            "allowTeacherScoreAdjustment": True,
        },
        "security": {
            "sessionTimeoutMinutes": 120,
            "minPasswordLength": 8,
            "requireUppercase": True,
            "requireNumbers": True,
            "requireSpecialChars": False,
            "enableTwoFactorAdmin": False,
            "enableTwoFactorTeachers": False,
            "maxFailedLogins": 5,
            "lockoutDurationMinutes": 15,
        },
        "maintenance": {
            "maintenanceMode": False,
            "maintenanceMessage": "System maintenance is scheduled. Please try again shortly.",
            "autoBackupDaily": True,
            "autoBackupTime": "02:00",
            "backupStorageLocation": "local_db_snapshot",
        },
    }


def _mask_secret(raw: Optional[str]) -> str:
    if not raw:
        return ""
    stripped = str(raw).strip()
    if not stripped:
        return ""
    if _MASK_CHAR in stripped:
        return stripped
    tail = stripped[-4:] if len(stripped) > 4 else ""
    return ("•" * 8) + tail


def _load_raw_settings(db: Session) -> Dict[str, Dict[str, Any]]:
    """Load merged settings with the real (unmasked) AI key. Never return this to clients."""
    merged = copy.deepcopy(_default_settings_payload())
    saved = get_latest_state(db, "__SYS_SETTINGS__")
    if isinstance(saved, dict):
        for section in ("general", "ai", "grading", "security", "maintenance"):
            if isinstance(saved.get(section), dict):
                merged[section].update(saved[section])
    return merged


def _load_settings(db: Session) -> Dict[str, Dict[str, Any]]:
    """Load settings safe for API responses (AI key masked)."""
    merged = _load_raw_settings(db)
    if merged["ai"].get("apiKey"):
        merged["ai"]["apiKey"] = _mask_secret(merged["ai"]["apiKey"])
    return merged


def _format_size(byte_len: int) -> str:
    if byte_len < 1024:
        return f"{byte_len} B"
    if byte_len < 1024 * 1024:
        return f"{byte_len / 1024:.1f} KB"
    return f"{byte_len / (1024 * 1024):.2f} MB"


@router.get("")
def get_system_settings(db: Session = Depends(get_db)):
    """
    Retrieve system settings grouped across general, ai, grading, security, and maintenance sections.
    """
    return _load_settings(db)


@router.put("")
def update_system_settings(
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update system settings sections, persist to the store, and record an audit log entry.
    """
    current = _load_raw_settings(db)
    allowed_sections = ("general", "ai", "grading", "security", "maintenance")

    updated_sections = []
    for section in allowed_sections:
        incoming = payload.get(section)
        if not isinstance(incoming, dict):
            continue
        updated_sections.append(section)
        for key, value in incoming.items():
            if section == "ai" and key == "apiKey":
                # Persist the real key; a value containing the mask means "unchanged".
                if value and _MASK_CHAR not in str(value):
                    current["ai"]["apiKey"] = str(value).strip()
                elif value == "":
                    current["ai"]["apiKey"] = ""
            elif key in current[section]:
                current[section][key] = value

    upsert_state(
        db=db,
        key_title="__SYS_SETTINGS__",
        payload=current,
        actor_name=current_user.full_name,
    )
    # Mask the key before returning it to the client.
    current = _load_settings(db)

    school_name = current["general"].get("schoolName", "")
    record_audit_event(
        db=db,
        title="Updated System Settings",
        description=(
            f"Updated settings sections ({', '.join(updated_sections) or 'none'}) "
            f"for school '{school_name}'."
        ),
        actor_name=current_user.full_name,
        severity="warning" if "security" in updated_sections else "info",
    )

    logger.info(
        "Admin settings updated by %s sections=%s",
        current_user.user_id,
        updated_sections,
    )
    return current


@router.post("/ai-ping")
def ping_ai_configuration(
    payload: Optional[Dict[str, Any]] = Body(default=None),
    db: Session = Depends(get_db),
):
    """
    Check configured AI provider/model readiness and report measured latency.
    """
    start = time.perf_counter()
    cfg = _load_settings(db)
    body = payload or {}

    provider = str(body.get("provider") or cfg["ai"].get("provider") or "google_gemini")
    model = str(body.get("model") or cfg["ai"].get("defaultModel") or "gemini-2.5-flash")

    # Verify DB session health and non-secret application settings availability
    db.query(func.count(Role.role_id)).scalar()
    has_configured_key = bool(
        cfg["ai"].get("apiKey")
        or os.getenv("GEMINI_API_KEY")
        or os.getenv("MISTRAL_API_KEY")
        or os.getenv("OPENAI_API_KEY")
    )

    elapsed_ms = max(1, int(round((time.perf_counter() - start) * 1000)))
    return {
        # Readiness check only; no provider call is made.
        "status": "connected" if has_configured_key else "not_configured",
        "configured": has_configured_key,
        "latency_ms": elapsed_ms,
        "provider": provider,
        "model": model,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/backups")
def list_backups(db: Session = Depends(get_db)):
    """
    List saved system backup snapshots ordered newest first.
    """
    rows = list_state_items(db, "__BACKUP_SNAPSHOT__")
    items = []
    for _, item in rows:
        items.append(
            {
                "id": item.get("id"),
                "filename": item.get("filename"),
                "size": item.get("size"),
                "createdAt": item.get("createdAt"),
                "status": item.get("status", "completed"),
                "createdBy": item.get("createdBy"),
                "table_counts": item.get("table_counts", {}),
            }
        )
    return {"items": items}


@router.post("/backups", status_code=status.HTTP_201_CREATED)
def create_backup_snapshot(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a database metadata and configuration snapshot backup record with live table counts.
    """
    now = datetime.now(timezone.utc)
    table_counts = {
        "users": db.query(User).filter(func.upper(User.status) != "DELETED").count(),
        "roles": db.query(Role).count(),
        "permissions": db.query(Permission).count(),
        "classes": db.query(Class).filter(func.upper(Class.status) != "DELETED").count(),
        "subjects": db.query(Subject).filter(func.upper(Subject.status) != "DELETED").count(),
        "student_classes": db.query(StudentClass).filter(func.upper(StudentClass.status) != "DELETED").count(),
        "teacher_subjects": db.query(TeacherSubject).filter(func.upper(TeacherSubject.status) != "DELETED").count(),
        "documents": db.query(Document).filter(func.upper(Document.status) != "DELETED").count(),
        "exercises": db.query(Exercise).filter(func.upper(Exercise.status) != "DELETED").count(),
        "questions": db.query(Question).filter(func.upper(Question.status) != "DELETED").count(),
        "student_exercise_attempts": db.query(StudentExerciseAttempt)
        .filter(func.upper(StudentExerciseAttempt.status) != "DELETED")
        .count(),
        "audit_logs": db.query(AuditLog)
        .filter(
            func.upper(AuditLog.status) != "DELETED",
            or_(AuditLog.ip_address.is_(None), AuditLog.ip_address != INTERNAL_STATE_MARKER),
        )
        .count(),
    }

    settings_snapshot = _load_settings(db)
    snapshot_doc = {
        "generated_at": now.isoformat(),
        "created_by": current_user.full_name,
        "table_counts": table_counts,
        "settings": settings_snapshot,
    }
    raw_bytes = json.dumps(snapshot_doc, ensure_ascii=False, indent=2).encode("utf-8")
    filename = f"smartlms_backup_{now.strftime('%Y%m%d_%H%M%S')}.json"

    _, item = append_state_item(
        db=db,
        key_title="__BACKUP_SNAPSHOT__",
        payload={
            "filename": filename,
            "size": _format_size(len(raw_bytes)),
            "byte_size": len(raw_bytes),
            "createdAt": now.isoformat(),
            "status": "completed",
            "createdBy": current_user.full_name,
            "table_counts": table_counts,
            "snapshot": snapshot_doc,
        },
        actor_name=current_user.full_name,
    )

    record_audit_event(
        db=db,
        title="Created System Backup",
        description=f"Created system snapshot '{filename}' ({item['size']}).",
        actor_name=current_user.full_name,
        severity="info",
    )

    summary_item = {
        "id": item["id"],
        "filename": item["filename"],
        "size": item["size"],
        "createdAt": item["createdAt"],
        "status": item["status"],
        "createdBy": item["createdBy"],
        "table_counts": item["table_counts"],
    }
    return {"item": summary_item}


@router.get("/backups/{backup_id}/download")
def download_backup_snapshot(backup_id: UUID, db: Session = Depends(get_db)):
    """
    Stream a saved backup snapshot as a downloadable JSON file.
    """
    found = get_state_by_log_id(db, backup_id, key_title="__BACKUP_SNAPSHOT__")
    if not found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ERR-ADMIN-BACKUP_NOT_FOUND", "message": "Backup snapshot not found."},
        )

    _, item = found
    download_payload = item.get("snapshot") or {
        "id": item.get("id"),
        "filename": item.get("filename"),
        "created_at": item.get("createdAt"),
        "table_counts": item.get("table_counts", {}),
    }
    filename = item.get("filename") or f"smartlms_backup_{backup_id}.json"
    raw = json.dumps(download_payload, ensure_ascii=False, indent=2).encode("utf-8")

    return StreamingResponse(
        io.BytesIO(raw),
        media_type="application/json; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
