# File Name: dashboard.py
# Description: API routers for Admin Dashboard, statistics, approval requests, and audit logs.
# Created At: 2026-09-30
# Created By: Tam Khang
# Updated At: 2026-11-14
# Updated By: Tam Khang

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from models.models import User, Role, ApprovalRequest, AuditLog
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.services.permission_service import PermissionService
from app.modules.admin.schemas import (
    DashboardStatsResponse,
    DashboardActivityResponse,
    ActivityChartPoint,
    ApprovalRequestItem,
    ApprovalRequestActionResponse,
    AuditLogItem,
)
from app.modules.admin.repository import AdminDashboardRepository

router = APIRouter(prefix="/api/v1/admin/dashboard", tags=["admin-dashboard"])


def format_relative_time(dt: Optional[datetime]) -> str:
    """
    Format datetime into a user-friendly relative string.
    """
    if not dt:
        return "Recently"
    now = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    diff = now - dt
    seconds = int(diff.total_seconds())

    if seconds < 60:
        return "Just now"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    days = hours // 24
    if days == 1:
        return "Yesterday"
    return f"{days} days ago"


def map_request_to_schema(req: ApprovalRequest) -> ApprovalRequestItem:
    return ApprovalRequestItem(
        id=req.request_id,
        requester_name=req.requester_name,
        requester_sub=req.requester_sub,
        avatar_text=req.avatar_text,
        avatar_bg=req.avatar_bg,
        is_system=req.is_system,
        type=req.type,
        time=format_relative_time(req.created_at),
        status=req.status,
        reviewed_at=req.reviewed_at,
    )


def map_audit_log_to_schema(log: AuditLog) -> AuditLogItem:
    return AuditLogItem(
        id=log.log_id,
        title=log.title,
        description=log.description,
        actor_name=log.actor_name,
        ip_address=log.ip_address,
        severity=log.severity,
        time=format_relative_time(log.created_at),
        created_at=log.created_at,
    )


def require_admin_privilege(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> User:
    """
    Enforces that current user is an Administrator or possesses ADMIN permissions.
    """
    role = db.query(Role).filter(Role.role_id == current_user.role_id).first()
    role_name = role.name.lower() if role else ""
    if role_name == "admin":
        return current_user

    effective_perms = PermissionService.get_effective_permissions(db, current_user.user_id, current_user.role_id)
    if "ADMIN_USER_VIEW" in effective_perms or "ADMIN_USER_MANAGE" in effective_perms or "ADMIN_ROLE_MANAGE" in effective_perms:
        return current_user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={
            "code": "ERR-AUTH-FORBIDDEN",
            "message": "Administrative privileges required to access this endpoint."
        }
    )


@router.get("/stats", response_model=DashboardStatsResponse, dependencies=[Depends(require_admin_privilege)])
def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    Retrieve core KPI metrics for the Admin Dashboard.
    """
    stats_data = AdminDashboardRepository.get_stats(db)
    return DashboardStatsResponse(**stats_data)


@router.get("/activity-chart", response_model=DashboardActivityResponse, dependencies=[Depends(require_admin_privilege)])
def get_activity_chart(
    timeframe: str = Query("week", description="Chart timeframe: 'week' or 'month'"),
    db: Session = Depends(get_db),
):
    """
    Retrieve activity metrics for the area curve chart from live database records.
    """
    from datetime import datetime, timedelta, timezone
    from sqlalchemy import func, or_
    from models.models import AuditLog, Document, StudentExerciseAttempt, User

    now = datetime.now(timezone.utc)
    is_month = timeframe == "month"
    window_days = 28 if is_month else 7
    since = now - timedelta(days=window_days)

    def _to_utc(dt):
        if dt is None:
            return None
        return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)

    # Only load rows inside the chart window; totals are computed with COUNT/SUM in the DB.
    def _window(col, *extra):
        return [ts for (ts,) in db.query(col).filter(col >= since, *extra).all() if ts is not None]

    attempt_ok = StudentExerciseAttempt.status != "DELETED"
    doc_ok = Document.status != "DELETED"
    recent_events = [
        _to_utc(ts)
        for ts in (
            _window(StudentExerciseAttempt.created_at, attempt_ok)
            + _window(Document.created_at, doc_ok)
            + _window(User.created_at, User.status != "DELETED")
            + _window(
                AuditLog.created_at,
                AuditLog.status != "DELETED",
                or_(AuditLog.ip_address.is_(None), AuditLog.ip_address != "INTERNAL_STATE"),
                or_(AuditLog.title.is_(None), func.substr(AuditLog.title, 1, 2) != "__"),
            )
        )
    ]

    total_doc_downloads = int(db.query(func.coalesce(func.sum(Document.download_count), 0)).filter(doc_ok).scalar() or 0)
    total_docs = db.query(Document).filter(doc_ok).count()
    total_attempts = db.query(StudentExerciseAttempt).filter(attempt_ok).count()
    lecture_views = total_doc_downloads if total_doc_downloads > 0 else total_docs
    assignments_submitted = total_attempts

    if not recent_events:
        # No real activity: return zeroed points instead of fabricated sample data.
        if is_month:
            labels = ["Tuần 1", "Tuần 2", "Tuần 3", "Tuần 4"]
            x_coords = [70, 210, 380, 550]
        else:
            labels = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
            x_coords = [50, 140, 230, 320, 410, 500, 590]
        points = [
            ActivityChartPoint(day=lbl, visits=0, x=x_coords[i], y=190)
            for i, lbl in enumerate(labels)
        ]
    else:
        if is_month:
            labels = ["Tuần 1", "Tuần 2", "Tuần 3", "Tuần 4"]
            x_coords = [70, 210, 380, 550]
            counts = [0, 0, 0, 0]
            for ts in recent_events:
                days_ago = max(0, (now - ts).days)
                bucket_idx = min(3, 3 - min(3, days_ago // 7))
                counts[bucket_idx] += 1
        else:
            labels = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
            x_coords = [50, 140, 230, 320, 410, 500, 590]
            counts = [0] * 7
            for ts in recent_events:
                counts[ts.weekday()] += 1

        max_count = max(counts) if max(counts) > 0 else 1
        peak_idx = counts.index(max(counts))
        points = []
        for idx, label in enumerate(labels):
            val = counts[idx]
            is_peak = idx == peak_idx
            # Scale y smoothly into SVG chart canvas range [65..190] (lower y = higher bar/curve)
            y_val = int(round(190 - (val / max_count) * 125)) if max_count > 0 else 190
            display_label = f"{label} (Đỉnh)" if is_peak else label
            points.append(
                ActivityChartPoint(
                    day=display_label,
                    visits=val,
                    x=x_coords[idx],
                    y=y_val,
                    is_peak=is_peak,
                )
            )

    return DashboardActivityResponse(
        timeframe=timeframe,
        points=points,
        lecture_views=lecture_views,
        assignments_submitted=assignments_submitted,
        last_updated_relative="Just now",
    )


@router.get("/requests", response_model=List[ApprovalRequestItem], dependencies=[Depends(require_admin_privilege)])
def list_approval_requests(db: Session = Depends(get_db)):
    """
    List all pending and processed approval requests.
    """
    requests = AdminDashboardRepository.get_requests(db)
    return [map_request_to_schema(req) for req in requests]


@router.post("/requests/{request_id}/approve", response_model=ApprovalRequestActionResponse)
def approve_request(
    request_id: UUID,
    current_user: User = Depends(require_admin_privilege),
    db: Session = Depends(get_db)
):
    """
    Approve an administrative request.
    """
    request = AdminDashboardRepository.get_request_by_id(db, request_id)
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "ERR-ADMIN-REQUEST_NOT_FOUND",
                "message": f"Approval request with id {request_id} not found."
            }
        )

    updated_req = AdminDashboardRepository.update_request_status(
        db,
        request=request,
        new_status="approved",
        reviewer_id=current_user.user_id,
        review_note="Approved by Administrator."
    )

    # Log to audit trail
    audit_log = AuditLog(
        title=f"Phê duyệt yêu cầu: {updated_req.type}",
        description=f"Thực hiện bởi: {current_user.full_name} ({current_user.email})",
        actor_name=current_user.full_name,
        severity="info",
    )
    db.add(audit_log)
    db.commit()

    return ApprovalRequestActionResponse(
        message="Request approved successfully.",
        request=map_request_to_schema(updated_req)
    )


@router.post("/requests/{request_id}/reject", response_model=ApprovalRequestActionResponse)
def reject_request(
    request_id: UUID,
    current_user: User = Depends(require_admin_privilege),
    db: Session = Depends(get_db)
):
    """
    Reject an administrative request.
    """
    request = AdminDashboardRepository.get_request_by_id(db, request_id)
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "ERR-ADMIN-REQUEST_NOT_FOUND",
                "message": f"Approval request with id {request_id} not found."
            }
        )

    updated_req = AdminDashboardRepository.update_request_status(
        db,
        request=request,
        new_status="rejected",
        reviewer_id=current_user.user_id,
        review_note="Rejected by Administrator."
    )

    # Log to audit trail
    audit_log = AuditLog(
        title=f"Từ chối yêu cầu: {updated_req.type}",
        description=f"Thực hiện bởi: {current_user.full_name} ({current_user.email})",
        actor_name=current_user.full_name,
        severity="warning",
    )
    db.add(audit_log)
    db.commit()

    return ApprovalRequestActionResponse(
        message="Request rejected successfully.",
        request=map_request_to_schema(updated_req)
    )


@router.get("/audit-logs", response_model=List[AuditLogItem], dependencies=[Depends(require_admin_privilege)])
def get_audit_logs(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Retrieve recent audit logs.
    """
    logs = AdminDashboardRepository.get_audit_logs(db, limit=limit)
    return [map_audit_log_to_schema(log) for log in logs]
