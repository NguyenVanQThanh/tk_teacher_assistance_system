File Name: feature_job_queue.md
Created At: 2026-11-17
Created By: AI Agent
Updated At: 2026-11-17
Updated By: AI Agent

### Summary
Postgres-backed background job queue so users never wait on one screen. AI exercise generation (student and teacher) and question import are queued; the modal closes immediately and a floating JobTray shows stage, progress and ETA. On completion the owner gets a notification and lists reload.

### Feature Specifications
- Table `background_jobs` (migration `a2b3c4d5e6f7`). Kinds: `STUDENT_AI_EXERCISE`, `TEACHER_AI_EXERCISE`, `QUESTION_IMPORT` (backend/app/modules/exercise/jobs.py).
- Claim with `FOR UPDATE SKIP LOCKED`; in-process worker threads (`JOB_WORKERS`, default 2; 0 in tests).
- Public status: queued/running/done/error + `progress`, `stage`, `eta_seconds` (median of last 10 DONE jobs of the kind, else handler default), `queue_position`.
- Per-user cap `MAX_ACTIVE_PER_USER=3` -> 429 `ERR-EXE-AI_TOO_MANY_JOBS`; enqueue serialised per user with `pg_advisory_xact_lock`.
- Recovery: `recover_interrupted` re-queues RUNNING jobs whose `updated_at` is older than `STALE_SECONDS` (600) once (`MAX_ATTEMPTS=2`), then FAILED. A heartbeat thread touches `updated_at` every 30s. Runs at startup AND every 60s from the worker loop (otherwise orphaned jobs count against the cap until a restart).
- `_finish` commits the outcome first, then notifies in a separate try; it ignores the outcome when the job is no longer RUNNING or `attempts` changed (superseded run). Uploaded file content (`file_text`, `question_file`, `answer_file`) is scrubbed from the payload on finish and on recovery failure.
- Idempotency: `hold_ownership(session)` locks the job row (FOR UPDATE) and verifies status/attempt before non-idempotent writes (`_persist`, `_import`); a superseded run gets 409.
- Frontend: `components/common/JobTray.jsx` polls `/api/v1/jobs?active=true` every 4s, hides `awaitedJobs`, dispatches `jobs:finished`; `services/api.js` `startForStudent`/`startAiExercise` queue and return.

### Bug & Feature Context
- Original problem: 524 timeouts on long AI generation; in-memory job dict lost on restart.
- Review rounds raised: kind scoping of poll endpoints, user flood cap, durable outcome, multi-process recovery, duplicate execution, N+1 ETA queries (fixed: one estimate per kind in `list_jobs`).

### Solution & Technical Details
- Files: backend/app/core/background_jobs.py, backend/app/modules/exercise/jobs.py, routers/jobs.py, routers/ai_generation.py, routers/exercises.py, services/ai_exercise_service.py; tests/core/test_background_jobs.py, test_job_security.py; frontend JobTray.jsx, api.js, CreateExerciseModal.jsx, StudentExercisesPage.jsx.
- Known limits (deliberate): a superseded run can still spend LLM cost (only the write is blocked); the `hold_ownership` lock in import is released at the first commit; every backend ERR- code must be mapped in frontend utils/errorMessages.js (selfcheck enforces it).
