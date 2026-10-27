# File Name: dashboard.py
# Description: API routers for Admin Dashboard, statistics, approval requests, and audit logs.
# Created At: 2026-09-30
# Created By: Tam Khang
# Updated At: 2026-09-30
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
    timeframe: str = Query("week", description="Chart timeframe: 'week' or 'month'")
):
    """
    Retrieve activity metrics for the area curve chart.
    """
    if timeframe == "month":
        points = [
            ActivityChartPoint(day="Tuần 1", visits=12400, x=70, y=170),
            ActivityChartPoint(day="Tuần 2", visits=15800, x=210, y=125),
            ActivityChartPoint(day="Tuần 3 (Đỉnh)", visits=19400, x=380, y=65, is_peak=True),
            ActivityChartPoint(day="Tuần 4", visits=14600, x=550, y=140),
        ]
        lecture_views = 62200
        assignments_submitted = 14350
    else:
        points = [
            ActivityChartPoint(day="T2", visits=850, x=50, y=190),
            ActivityChartPoint(day="T3", visits=1450, x=140, y=155),
            ActivityChartPoint(day="T4", visits=2250, x=230, y=105),
            ActivityChartPoint(day="T5", visits=2350, x=320, y=100),
            ActivityChartPoint(day="T6 (Đỉnh)", visits=2840, x=410, y=70, is_peak=True),
            ActivityChartPoint(day="T7", visits=2200, x=500, y=110),
            ActivityChartPoint(day="CN", visits=1250, x=590, y=165),
        ]
        lecture_views = 14200
        assignments_submitted = 3489

    return DashboardActivityResponse(
        timeframe=timeframe,
        points=points,
        lecture_views=lecture_views,
        assignments_submitted=assignments_submitted,
        last_updated_relative="10 minutes ago",
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
