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
