<!--
File Name: ADMIN_TRACKER.md
Description: Comprehensive tracker for Admin role use cases across Backend, Frontend, and Testing.
Created At: 2026-09-30
Created By: Tam Khang
Updated At: 2026-10-07
Updated By: Tam Khang
-->

# Admin Role Use Cases Tracker

> Path: `docs/ADMIN_TRACKER.md` · Role: **Administrator (Admin)**  
> Created By: `Tam Khang` · Updated By: `Tam Khang` · Updated At: `2026-10-07`  
> Scope: System administration, account management, academic structure, roles & permissions, analytics & monitoring.

| Use Case | BE | FE | Test |
| :--- | :---: | :---: | :---: |
| **1. Authentication & System Access** | | | |
| Admin authentication with phone/email and password (`POST /api/v1/auth/login`) | [x] | [x] | [x] |
| Admin profile retrieval and active token verification (`GET /api/v1/auth/me`) | [x] | [x] | [x] |
| Admin password change with current password confirmation (`POST /api/v1/auth/change-password`) | [x] | | |
| Admin secure session logout and token revocation (`POST /api/v1/auth/logout`) | [x] | [x] | [x] |
| Protected Admin routing & persistent admin layout guard (`AdminLayout`) | [x] | [x] | [x] |
| **2. Admin Dashboard & Operations Monitoring** | | | |
| Real-time core KPIs retrieval: students, teachers, classes, attendance rate (`GET /api/v1/admin/dashboard/stats`) | [x] | [x] | [x] |
| Dynamic LMS traffic and engagement area spline chart data (`GET /api/v1/admin/dashboard/activity-chart`) | [x] | [x] | [x] |
| Interactive weekly vs. monthly timeframe toggle for traffic chart | [x] | [x] | [x] |
| Infrastructure and AI API status monitoring card | [x] | [x] | [x] |
| Pending approval requests queue listing (`GET /api/v1/admin/dashboard/requests`) | [x] | [x] | [x] |
| One-click approval of administrative requests (`POST /api/v1/admin/dashboard/requests/{id}/approve`) | [x] | [x] | [x] |
| One-click rejection of administrative requests (`POST /api/v1/admin/dashboard/requests/{id}/reject`) | [x] | [x] | [x] |
| System audit logs timeline listing (`GET /api/v1/admin/dashboard/audit-logs`) | [x] | [x] | [x] |
| Audit trail modal dialog with severity color indicators | [x] | [x] | [x] |
| **3. User Management (`/admin/users`)** | | | |
| Paginated user directory with search by keyword and multi-filters (`GET /api/v1/admin/users`) | [x] | [x] | [x] |
| Filter users by role tabs (All, Students, Teachers, Pending) | [x] | [x] | [x] |
| Filter users by grade, department, account status, and academic year | [x] | [x] | [x] |
| Dynamic filter tags row with instant clear capability | [x] | [x] | [x] |
| Auto-generate unique identifier code for student/teacher (`GET /api/v1/admin/users/generate-code`) | [x] | [x] | [x] |
| Check unique identifier code collision (`GET /api/v1/admin/users/check-code`) | [x] | [x] | [x] |
| Strict Vietnamese Full Name validation (blocking digits & special characters) | [x] | [x] | [x] |
| Strict Vietnamese 10-digit Phone validation (`0\d{9}`) | [x] | [x] | [x] |
| Strict segmented DD/MM/YYYY birth date input with leap year & calendar validation | [x] | [x] | [x] |
| Minimum age verification by role (Student >= 16, Teacher >= 22) | [x] | [x] | [x] |
| Create user with auto default password and notification dispatch (`POST /api/v1/admin/users`) | [x] | [x] | [x] |
| View detailed user information modal | [x] | [x] | [x] |
| Update user profile information (`PUT /api/v1/admin/users/{id}`) | [x] | [x] | [x] |
| Toggle user account status: Active, Inactive, Suspended (`PATCH /api/v1/admin/users/{id}/status`) | [x] | [x] | [x] |
| Soft delete user with status `DELETED` (`DELETE /api/v1/admin/users/{id}`) | [x] | [x] | [x] |
| Restore soft-deleted user to `ACTIVE` status (`POST /api/v1/admin/users/{id}/restore`) | [x] | [x] | [x] |
| Reset user password with auto-generated credential dispatch (`POST /api/v1/admin/users/{id}/reset-password`) | [x] | [x] | [x] |
| Export user list to Excel / CSV file (`GET /api/v1/admin/users/export-excel`) | [x] | [x] | [x] |
| Import users from structured Excel template (`POST /api/v1/admin/users/import-excel`) | [x] | [x] | [x] |
| **4. School & Classes Management (`/admin/classes`)** | | | |
| School classes directory listing with grade filters K10, K11, K12 (`GET /api/v1/classes`) | [x] | [x] | [x] |
| Filter classes by homeroom assignment status and student capacity | [x] | | |
| View class details, capacity bar, and enrolled student roster (`GET /api/v1/classes/{id}`) | [x] | | |
| Create new class with room, grade, capacity, and academic year (`POST /api/v1/classes`) | [x] | | |
| Update class information and room assignment (`PUT /api/v1/classes/{id}`) | [x] | | |
| Soft delete class record (`DELETE /api/v1/classes/{id}`) | [x] | | |
| Assign or change Homeroom Teacher for class | [x] | | |
| View and manage subject teachers assigned to class (`GET/POST /api/v1/classes/{id}/teacher-subjects`) | [x] | | |
| Enroll students into class with student code (`POST /api/v1/classes/{id}/students`) | [x] | | |
| Unenroll / transfer students between classes | [x] | | |
| Export class roster and academic enrollment to Excel | [x] | | |
| **5. Roles & Permissions Management (`/admin/roles`)** | | | |
| View system roles list with member count and descriptions (`GET /api/v1/admin/roles`) | | [x] | |
| Grouped permissions matrix by module: academic, exercise, admin, tracking (`GET /api/v1/admin/permissions`) | | [x] | |
| Toggle / update permissions assigned to roles (`PUT /api/v1/admin/roles/{id}/permissions`) | | | |
| View individual user effective permissions with role inheritance (`GET /api/v1/admin/users/{id}/permissions`) | | | |
| Individual permission override (Grant override / Revoke override with Deny-precedence) | | | |
| Create new custom role with description | | | |
| Assign users to roles modal dialog | | | |
| **6. Reports & Academic Analytics (`/admin/reports`)** | | | |
| Academic year and semester filter controls for reports | | [x] | |
| Overall GPA score distribution across grades and classes | | [x] | |
| Dual-spline academic performance vs. student engagement trend charts | | [x] | |
| Bloom cognitive taxonomy distribution donut chart (Recognition, Understanding, Application) | | [x] | |
| Early intervention alerts list for at-risk students | | [x] | |
| Send notification / email alert to teachers and parents of at-risk students | | | |
| Export comprehensive school academic report to PDF / Excel | | | |
| **7. System Settings (`/admin/settings`)** | | | |
| School institutional profile configuration (name, motto, address, logo) | | [x] | |
| Academic year and semester dates configuration | | [x] | |
| Authentication and security policy configuration (session timeout, lockout rules) | | [x] | |
| System storage quota, backup scheduling, and log retention settings | | | |
| Automated SMS and email notification templates configuration | | | |
