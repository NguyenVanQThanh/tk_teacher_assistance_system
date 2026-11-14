File Name: bugfix_review_findings_sse_ticket_regrade.md
Created At: 2026-11-13
Created By: AI Agent
Updated At: 2026-11-13
Updated By: AI Agent

### Summary
Fixed code-review findings: SSE auth leak, regrade scoping, attempt listing filter, ai_metadata leak, "Other" regrade bug; also CI font failures.

### Feature Specifications
- SSE `/api/v1/sync/stream` auth: Bearer header or 30s single-purpose ticket (`?ticket=`) from `POST /api/v1/sync/stream-ticket`. Access JWT in the URL is rejected; ticket is rejected on all other endpoints (`typ=sse`).
- Stream re-checks the user (blocked/inactive/deleted) every tick; stops on client disconnect.
- Students get only whitelisted `ai_metadata` keys on `/assignments/{id}/taking`.
- Answer-key regrade only touches attempts of classes the teacher can access (admin: all).
- `GET /api/v1/attempts?student_id=` filter is honoured.

### Bug & Feature Context
- Access JWT in SSE URL leaked via history/proxy logs.
- Regrade affected every class using the exercise; `student_id` filter was ignored; `topic_prompt`/`document_ids` leaked to students; manual overrides ignored for "Other" questions.
- 20 CI tests failed on Linux: hardcoded Windows font path.

### Solution & Technical Details
- `core/security.py` (`create_stream_ticket`), `auth/dependencies.py` (`resolve_user_from_token(expect_ticket)`, `ensure_active_user`), `exercise/routers/sync.py`, `main.py` (log mask for token/ticket), frontend `services/api.js` `subscribeVersionStream` (fetch ticket per connect).
- `grading_service.regrade_exercise(class_ids)`, `attempt_service.update_answer_key_and_regrade`, `assignment_service._STUDENT_SAFE_META_KEYS`.
- Font: `backend/tests/exercise/unit/_font.py` cross-platform resolver.
- Tests: `tests/exercise/test_taking_and_sync.py` (ticket flow, `TestReviewHardening`).

### Round 2 review fixes (2026-11-13)
- Answer key: only exercise owner or Admin may change it (403 `ERR-EXE-ANSWER_KEY_OWNER_ONLY`). The key is shared by all classes, so `GradingService.regrade_exercise(exercise_id)` rescores finished attempts of every class (no `class_ids` param anymore); per-attempt logic in `GradingService.rescore()`.
- Late window (confirmed by user): an open attempt can be resumed/submitted until `due_at` + exercise duration (`duration_minutes`, default 45); afterwards 403 `ERR-EXE-ASSIGNMENT_EXPIRED`. Helper `open_attempt_deadline()` in `assignment_service.py`.
- `update_attempt_grade`: `teacher_total_score` stored only when the submitted score differs from the auto-computed total (tolerance 0.05); otherwise cleared so answer-key regrade still applies. Known edge: attempts with only manual questions and UI fallback score 0 still pin 0.
- `X-Data-Version` middleware skips requests without `Authorization`.
- `/notifications` loads attempts once and passes them to `get_grading_dashboard(attempts=...)`.
- `PdfExportService.register_fonts` is now public; CSV formula-injection guard covers tab/CR.
- Tests: `test_answer_key_owner_only_and_regrades_all_classes`, `test_open_attempt_window_closes_after_due_plus_duration`, `test_grade_save_with_auto_total_does_not_pin_score`, `tests/exercise/unit/test_grading_report_service.py`.
- False positives: list endpoint answer leak, migration chain/Postgres-only SQL (single head, DB is Postgres/pgvector).
