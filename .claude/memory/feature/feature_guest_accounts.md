File Name: feature_guest_accounts.md
Created At: 2026-11-16
Created By: AI Agent
Updated At: 2026-11-16
Updated By: AI Agent

### Summary
Guest accounts (Teacher and Student roles) with no registration, plus related account fixes (profile save, academic year setting, admin credential flow). Shipped as two PRs: #72 (backend + admin, squash merged) and #73 (frontend). Branch `feat/guest-accounts-and-account-fixes` was split because the review bot vetoed the 64-file diff; do not reuse it.

### Feature Specifications
- `POST /api/v1/auth/guest {role, guest_key?}`: creates or resumes a guest (`users.is_guest=true`, `phone="guest_"+12 hex` = 18 chars, `users.phone` is String(20)). Admin role rejected via `AdminUserService.reject_admin_role`.
- Resume: a matching ACTIVE `guest_key` (hashed in `guest_key_hash`) of the same role returns the same account and `guest_key=null`; a wrong key creates a new guest.
- Caps (all in `app/core/config.py`, env overridable): `GUEST_CREATE_PER_IP_HOUR=5`, `GUEST_CREATE_GLOBAL_HOUR=200`, `GUEST_AI_LIMIT=3` (counts all exercises of the guest, soft-deleted included), `GUEST_DOC_LIMIT=3` (counts soft-deleted documents too), `GUEST_ACCESS_ENABLED=true`.
- Permission allow-list: `GUEST_ALLOWED_PERMISSIONS` in `app/scripts/rbac_seed.py`, intersected in `PermissionService.get_effective_permissions` for guests (role cache stays shared; clamp is applied after).
- Guest student: personal assignments (`class_assignments.class_id` NULL, `owner_student_id` = student). Must send `grade` (10-12) because there is no class; otherwise 422 `ERR-EXE-AI_GRADE_REQUIRED`.
- Guest teacher: exercises land in the bank without an assignment; subject scope check skipped in `create_exercise`; schedule routes return 403 `ERR-AUTH-GUEST_FORBIDDEN`.
- Admin side: guests excluded from dashboard stats, `is_guest` filter on user list, guest password reset rejected (403 `ERR-ADMIN-GUEST_PASSWORD_LOCKED`). Admin create/reset no longer accept a chosen password (auto-generated, shown once in `CredentialModal`).
- Names: `app/core/names.py` accepts only Unicode letters and single spaces. `-` and `'` are rejected on purpose (user decision, asked twice).
- Frontend: `GuestLock`, `ProtectedRoute` guest allow-list (`/teacher/exercises`, `/teacher/documents`, `/student/exercises`), guest key kept in localStorage across logout on purpose (resume same account and quota). Upload sends `subject_id`; academic year is `YYYY-YYYY` everywhere (display adds spaces).

### Bug & Feature Context
Bot review ("agent-review / review") rejected the PRs many rounds. Most findings were false positives; verified facts so they are not re-investigated:
- `enrolled = own_personal or db.query(...).first()` yields bool/object, not a Query. Test `test_guest_student_cannot_read_or_start_class_assignment`.
- Class-less flow (taking, start, submit, history, dashboard) returns 200 for guest students; `class_name` has fallbacks ("Lớp" / "Lớp học").
- `users.phone` length fits (test `test_guest_phone_fits_column`; SQLite does not enforce VARCHAR so keep that test).
- `owner_student_id` column comes from earlier migration `a1c3e5f7b9d2`.
- `updateProfile` exists on dev (`frontend/src/services/api.js`); backend upload takes `subject_id`.
- Real bugs found and fixed: missing grade, upload cap ignored soft-deleted docs, per-IP race, deny-row permission model (replaced by allow-list), X-Forwarded-For first entry spoofable, no global cap, per-guest AI/doc cap race, reports year state not following profile, profile toast never cleared.

### Solution & Technical Details
- Concurrency: `pg_advisory_xact_lock(hashtext(key))` on PostgreSQL only (keys `guest_create:<ip>`, `guest_create:global`, `guest_quota:<user_id>`). SQLite (tests) has no lock, so races are not covered by tests; verify on Postgres if concerned.
- `client_ip` (`app/core/config.py`): honors `CF-Connecting-IP` then the Nth-from-right `X-Forwarded-For` entry (`TRUSTED_PROXY_HOPS`, default 1) ONLY when `TRUST_PROXY_HEADERS=true`. Behind Cloudflare Tunnel it must be true, otherwise all guests share the proxy IP and everyone gets 429 after 5 guests/hour. Wired as a GitHub Actions Variable in `deploy.yml`, merged into `deploy/.env.prod` by `remote-deploy.sh`.
- Migration `d1e2f3a4b5c6_add_guest_users.py` (head after merge): adds `is_guest`, `guest_key_hash`, `guest_ip`, makes `class_id` nullable with a CHECK; downgrade raises if class-less assignments exist.
- Cleanup: `python -m app.scripts.purge_stale_guests [days]` soft-deletes (status DELETED) stale guests, never hard deletes.
- Error codes added with Vietnamese messages in `frontend/src/utils/errorMessages.js`: AUTH-GUEST_DISABLED, AUTH-GUEST_FORBIDDEN, AUTH-GUEST_RATE_LIMITED, AUTH-ROLE_NOT_FOUND, ADMIN-ADMIN_PASSWORD_LOCKED, ADMIN-GUEST_PASSWORD_LOCKED, ADMIN-INVALID_ACADEMIC_YEAR, DOC-GUEST_LIMIT, EXE-AI_GRADE_REQUIRED, EXE-GUEST_AI_LIMIT, NOTIFICATION-NOT_FOUND (underscore, not hyphen).
- Key files: `backend/app/modules/auth/routers/auth.py`, `auth/services/permission_service.py`, `exercise/services/ai_exercise_service.py`, `exercise/services/assignment_service.py`, `exercise/services/attempt_service.py`, `document/routers/documents.py`, `admin/services/user_service.py`, `admin/state_store.py`, `backend/tests/auth/integration/test_guest.py`; frontend `components/common/GuestLock.jsx`, `ProtectedRoute.jsx`, `context/AuthContext.jsx`, `pages/admin/AdminUsersPage.jsx`.
- Tests at merge: backend 581 passed; frontend build and selfchecks pass.
- Windows gotcha: files are CRLF + UTF-8; scripted edits need `open(p, newline='', encoding='utf-8')` or edits silently fail.
