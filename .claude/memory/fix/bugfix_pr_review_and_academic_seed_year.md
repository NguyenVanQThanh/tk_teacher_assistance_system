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
