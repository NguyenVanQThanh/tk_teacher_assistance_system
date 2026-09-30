# Task: Admin Dashboard Live Metrics, Approval Workflow & Audit Trail Integration

> Path: `docs/tasks/f_admin_dashboard/task_admin_dashboard.md`  
> Slice: `F-ADMIN-DASH-SL01` · Type: `feature` · Size: `M` · SP: `5`  
> Depends on: `f_auth_01_spec.md`, `f_admin_01_user_management_spec.md`  
> Status: `ready to test`  
> Created At: `2026-09-30`  
> Updated At: `2026-09-30`  
> Created By: `Tam Khang`  
> Updated By: `Tam Khang`  

## 1. Overview
Connect the Admin Dashboard (`/admin`) end-to-end to the backend FastAPI application and PostgreSQL database:
- Real database tables and migrations for `approval_requests` and `audit_logs` adhering strictly to the system's Soft Delete policy.
- Dashboard API endpoints:
  - `GET /api/v1/admin/dashboard/stats`: Returns live count of active students, teachers, classes, and system attendance rate.
  - `GET /api/v1/admin/dashboard/activity-chart`: Provides dynamic data points for weekly and monthly area charts.
  - `GET /api/v1/admin/dashboard/requests`: Fetches all approval requests from the database.
  - `POST /api/v1/admin/dashboard/requests/{id}/approve`: Approves a request with reviewer attribution and records an audit log.
  - `POST /api/v1/admin/dashboard/requests/{id}/reject`: Rejects a request with reviewer attribution and records an audit log.
  - `GET /api/v1/admin/dashboard/audit-logs`: Lists recent administrative audit logs.
- Integrated frontend service `adminDashboardApi` in `frontend/src/services/api.js` and hooked into `AdminDashboard.jsx`.
- Verified with automated test suite (14/14 tests passed in `backend/tests/admin/`) and successful Vite production build.
