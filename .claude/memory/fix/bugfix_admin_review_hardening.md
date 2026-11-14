File Name: bugfix_admin_review_hardening.md
Created At: 2026-11-14
Created By: AI Agent
Updated At: 2026-11-14
Updated By: AI Agent

### Summary
Fixed six review findings on the admin portal (roles, settings, reports, student import, class grade filter) and added admin account restrictions: no new admins, no admin deletion, no self-blocking.

### Feature Specifications
- Admin role cannot be created, imported, promoted, or assigned via any API/UI (403 `ERR-ADMIN-ADMIN_ROLE_LOCKED`). Existing admins keep their role on profile edit.
- Admin accounts cannot be soft-deleted (403 `ERR-ADMIN-ADMIN_DELETE_LOCKED`), via `DELETE /{id}` or `PATCH /{id}/status` with DELETED.
- A signed-in admin cannot deactivate, suspend, or delete their own account (403 `ERR-ADMIN-SELF_BLOCK_LOCKED`). UI hides those actions for own row.
- Role member assignment blocks self role change and demoting the last active Admin.
- AI API key is stored unmasked internally, always returned masked. `ai-ping` returns `not_configured` when no key; it never calls the provider.
- Backup snapshot `audit_logs` count excludes `INTERNAL_STATE` rows.
- Reports return zeros when data is empty (no fabricated baselines); attempts filtered by grade/department/year through class assignments.
- Grade filter matches the leading digit run exactly (grade 1 no longer matches 10A1).
- Imported/manually created students get a random unknown password; admin must reset it to enable login.

- Admin role permission matrix is read-only (403 `ERR-ADMIN-ADMIN_PERMS_LOCKED`) to prevent self-lockout.
- Dashboard stats and activity chart return zeros when empty (no fabricated numbers); activity chart loads only window rows and uses COUNT/SUM for totals.
- `list_state_items` prefix match escapes LIKE wildcards (`_`, `%`).

- Third review round:
  - An Admin account's role can never change via user edit or `/roles/admin/members` (covers last-admin demotion). The Admin role cannot be cloned as a template (403).
  - Student import is atomic per row (`db.begin_nested()` savepoint plus a commit per row). `commit=False` flags added to `ClassRepository`/`EnrollmentRepository` create/update, `upsert_state` and the metadata savers. Class create/update and its metadata now commit together in the router.
  - Import rejects emails/phones owned by soft-deleted users with a clear row error instead of a unique-constraint crash.
  - Reports: academic_year filter is strict (no fallback to other years); each filter is applied independently; per-grade exercise count and score buckets are computed from that grade's classes only.
  - Class/student metadata loads by exact key via `list_state_items_by_keys` (no prefix scan of all rows).
  - Dashboard stats: growth fields are real 30-day vs previous-30-day percent change, `None` when there is no baseline. `attendance_rate` is the attempt completion rate (no attendance data exists), `None` when no attempts. Frontend dashboard defaults are zeros.
  - Not a bug, left as is: the `url_pattern="/api/v1/admin/roles"` on UI permissions is never matched, because `require_perm` checks `permission_code` only.

### Bug & Feature Context
- Review report flagged: unrestricted admin role assignment; internal state rows leaking into audit counts; API key masked before save (real key lost) and ping always "connected"; shared default password `Student@1234` plus per-row commit leaving orphan users; `startswith` grade filter; fabricated report numbers.
- Second review round: reports.py `.join()` lost its `ClassAssignment` target during a scripted edit (would 500 every default analytics request); fixed. Dashboard/repository fabricated fallbacks removed.
- Meta state still lives in AuditLog rows (keyed lookup now, but a dedicated table would be cleaner; needs Alembic migration).
- Seed scripts still use `Student@1234` (not changed). Admin accounts exist only via seeding.

### Solution & Technical Details
- `backend/app/modules/admin/routers/roles.py`: admin assignment block, self-change block, last-admin guard.
- `backend/app/modules/admin/routers/settings.py`: `_load_raw_settings` vs `_load_settings`, ping status, backup count filter.
- `backend/app/modules/admin/routers/reports.py`: removed baselines, attempts joined via `ClassAssignment`.
- `backend/app/modules/admin/services/user_service.py`: `reject_admin_role`, `reject_self_block`, `_is_admin_user`.
- `backend/app/modules/admin/routers/dashboard.py`, `backend/app/modules/admin/repository.py`, `backend/app/modules/admin/state_store.py`: fallback removal, windowed queries, LIKE escape.
- `backend/app/modules/admin/routers/users.py`: passes `acting_user_id`.
- `backend/app/modules/admin/services/user_import_service.py`: admin alias removed.
- `backend/app/modules/academic/services/enrollment_service.py`: `secrets.token_urlsafe` password, flush + single commit.
- `backend/app/modules/academic/services/class_service.py`, `routers/classes.py`: `matches_grade` helper.
- `frontend/src/pages/admin/AdminUsersPage.jsx`, `AdminSettingsPage.jsx`: hidden actions, `isSelf` via `useAuth().user.user_id`, ping toast.
- `.claude/rules/coding_rules.md`: section 9 Admin Account Restrictions.
- Tests: full backend suite 539 passed. New: `tests/admin/test_admin_account_locks.py`, `tests/academic/test_student_import_atomic.py`. Frontend not run; verify `/auth/me` exposes `user_id` for `isSelf`.
