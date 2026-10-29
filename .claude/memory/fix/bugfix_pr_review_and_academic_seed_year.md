File Name: bugfix_pr_review_and_academic_seed_year.md
Created At: 2026-10-29
Created By: AI Agent
Updated At: 2026-10-29
Updated By: AI Agent

## Summary

Addressed document and teacher-schedule review findings, then corrected the academic seed year responsible for the remaining TC-06 browser test failure. The user confirmed the previous fixes and requested this record and the seed correction. The final Chromium E2E run completed with 29 passed in 1.1 minutes.

## Feature Specifications

- Teacher-schedule and document routes require Teacher, HomeroomTeacher, or Admin roles. Students receive HTTP 403.
- Non-owner, non-admin document access is limited to Uploaded documents. Draft, Archived, and DELETED documents are restricted to their owner or an administrator.
- Document list ALL means non-deleted statuses; deleted documents require an explicit status filter and remain ownership-restricted.
- Document update statuses accept Uploaded, Draft, and Archived, not ACTIVE or DELETED. Deletion remains a soft-delete operation.
- Download counters use an atomic SQL increment.
- Repository presentation no longer fabricates views or ratings. The previous nonfunctional pagination controls were removed.
- Seeded class academic years roll over in August, matching TeacherClassesPage.jsx. July 31, 2026 resolves to 2025-2026; August 1, 2026 and January 1, 2027 resolve to 2026-2027.
- The existing seed class update behavior is retained: matching active sample classes are updated rather than duplicated.

## Bug & Feature Context

TC-06 expected class 12A1 on the teacher class page. The page defaults to the current academic year, but seed_academic_data.py fixed all three sample classes to 2023-2024. The classes therefore existed but were filtered out in October 2026.

Initial test runs also encountered unrelated local infrastructure: another application served IPv6 localhost:3000, and another container occupied host port 8000. A frontend API base URL pointed browser requests at that other backend. These environment failures were distinguished from application regressions.

## Solution & Technical Details

### Previous review changes

- backend/app/modules/auth/dependencies.py: shared role dependency.
- backend/app/modules/exercise/routers/teacher_schedule.py: teacher/admin role gating.
- backend/app/modules/document/routers/documents.py: role gating and current-user propagation to list queries.
- backend/app/modules/document/services/document_service.py: status/ownership visibility and atomic download increment.
- backend/app/modules/document/schemas.py: canonical update statuses.
- backend/models/models.py: grade and document type server defaults.
- backend/alembic/versions/a1c7e9d04b52_backfill_document_grade_and_type.py: new backfill/default migration; existing applied migrations were not edited.
- backend/app/scripts/seed_remaining_class_students.py: require an injected SEED_STUDENT_PASSWORD rather than a fallback password.
- frontend/src/pages/teacher/DocumentRepositoryPage.jsx: request ALL non-deleted statuses, remove fabricated metrics and pagination controls.
- frontend/src/components/documents/DocumentDetailView.jsx and .css: retain only the tracked download metric.

### Academic seed correction

- backend/app/scripts/seed_academic_data.py: derive academic_year from date.today(), with an August rollover; assign it to all three sample class records.
- backend/tests/academic/test_seed_academic_year.py: stdlib unittest evaluates the actual seed assignments through AST extraction, avoiding database, environment-file, and account-export side effects. Covers both sides of the August boundary and January.
- frontend/playwright.config.js: use http://127.0.0.1:3000 to avoid the unrelated IPv6 localhost listener.

### Verification

- `python backend/tests/academic/test_seed_academic_year.py`: passed, including three boundary cases.
- Only the academic class section was executed against the isolated Docker pg_e2e database. Repeated execution retained exactly three active classes, all with academic_year 2026-2027. Other seed sections and account export were not executed for this correction.
- `npm --prefix frontend exec -- playwright test --config=frontend/playwright.config.js --reporter=list`: 29 passed, including teacher TC-06.
- `git diff --check`: passed.
- Earlier HTTP smoke checks confirmed student rejection, Draft listing behavior, ACTIVE rejection, and a count of 20 after 20 concurrent downloads.

### Environment and remaining limitations

- Docker services remained running. Frontend: http://127.0.0.1:3000. Backend host port: 18001. PostgreSQL used the isolated tk_teacher_assistance_system_pg_e2e volume; the original data volume was preserved.
- A temporary Compose override supplied the alternative backend port, isolated database volume, and empty frontend API base URL for same-origin proxying. These runtime overrides are not a committed deployment configuration.
- Existing docker-compose.yml memory-limit edits were not authored or reverted during this fix.
- The current document visibility policy is status-based plus a role gate, not a persisted is_public flag. The original is_public parameter remains unimplemented; do not infer private Uploaded document support from this fix.
- The repository currently fetches at most 100 documents and does not provide complete pagination beyond that limit.
- Dashboard visibility and direct file serving were not established as secured by the TC-06 correction or the broad existing E2E suite.
- No commit or push was performed.

## Follow-up: second AI review round (2026-10-29)

- Dashboard leak: `get_document_dashboard` now uses the same `visible_documents_query` as list, so totals, storage, by-subject/type and `recent_documents` exclude other users' Draft/Archived documents. Admin sees all.
- Admin check: service uses one case-insensitive `DocumentService.is_admin`, consistent with `require_roles`.
- Schedule notes: `GET /api/v1/teacher/schedule/notes` is read-only; default-note seeding removed (deleted notes no longer reappear). Frontend shows an empty state.
- Subject filter: `DocumentRepositoryPage.jsx` maps backend subject names to the filter keys (`math`, `physics`, ...) and keeps `subjectName` for display; unknown subjects map to `other`.
- Removed unused `isMounted`. `restore_document` was already correct (`get_document_by_id` does not filter DELETED).
- Verified over HTTP: teacher B cannot see teacher A's draft in dashboard/list/detail (404), A and Admin can; delete then restore works; deleting all notes keeps the list empty. E2E 29/29.

## Follow-up: third and fourth review rounds (2026-10-29)

- Soft-deleted documents: `check_document_access` returns 404 for DELETED on every route except restore (`allow_deleted=True`). PUT can no longer resurrect a deleted document.
- Seed script: password check moved from import time to `get_student_password()`, called only when seeding runs.
- `TeacherClassesPage.jsx`: 10s polling and `focus` listener removed. Refresh happens only on tab visibility, at most every 30s and never while another refresh runs. `loadData` is stable (user id read through a ref).
- `ScheduleNoteCreate`: the `date` field shadowed the `date` type inside the class body, so `note_date: Optional[date]` was typed `Optional[None]` and every `note_date` payload returned 422. Now annotated with the `Date` alias; invalid `date` strings return 400 instead of silently becoming today.
- `list_documents`: grade and document_type filters use `coalesce` so legacy NULL rows match their display defaults.
- Not bugs, verified: `/dashboard` is declared before `/{document_id}`; alembic has a single head `a1c7e9d04b52`.
- Known gap: an invalid `note_date` (as opposed to `date`) returns pydantic's standard 422.

## Follow-up: fifth review round and PR split (2026-10-29)

- Bot blocked the PR for diff size (+1,803/-1,250 vs `dev`, 37 files). Work was split into small PRs against `dev`, merged in order (#12, #9, #8, #14, #16, #17, #18, #19): schedule notes and `require_roles`; documents; auth permissions and seed fixes; homeroom pages; grading card and `assignment_title`; grading page; classes CSS; classes page. After the last merge `dev` matched the original branch tree (except `docker-compose.yml`).
- Stacked split branches conflicted once `dev` squash-merged the earlier PRs. Fix: rebuild the branch from `origin/dev`, cherry-pick its own commit, force-push with lease. Prefer branching each small PR from `dev` after the previous one merges.
- Document metadata: upload and update validate `grade` in {10, 11, 12} and `document_type` in {lecture, exam, reference} (`ALLOWED_GRADES`, `ALLOWED_DOCUMENT_TYPES` in `document/schemas.py`) so dashboard buckets and list filters agree.
- Download: `GET /{id}/download` returns 404 before counting when the file is missing on disk; the UI shows an error toast instead of saving a corrupt file.
- Schedule page: removed hard-coded fallback notes and local-only `local-` notes. Save and delete failures show an error toast and leave the list unchanged.
- Tests added in `backend/tests/exercise/test_document_and_grading_dashboard.py`: student 403, other teacher's Draft 404, metadata validation. pytest 7/7, E2E 29/29.
- Known gap: repository page still loads at most 100 documents (no pagination).
