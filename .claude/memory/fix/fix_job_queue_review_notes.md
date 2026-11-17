File Name: fix_job_queue_review_notes.md
Created At: 2026-11-17
Created By: AI Agent
Updated At: 2026-11-17
Updated By: AI Agent

### Summary
Log of automated code-review findings on branch feat/job-queue: which were real (fixed) and which were verified NOT to be defects, so later reviews do not redo the analysis.

### Feature Specifications
Not applicable (review log).

### Bug & Feature Context
Rejected after verification:
- "Import handler lacks write-access re-check": `_import_questions_impl` calls `get_exercise_for_write` at run time; `_import` also re-checks `EXE_QUESTION_IMPORT`.
- "SimpleNamespace upload breaks import": the impl only uses `.filename` and `.file.read()`.
- "Frontend lacks startAiExercise/startForStudent/awaitedJobs": all exported from frontend/src/services/api.js.
- "Status queued breaks old clients": `pollLoop` only terminates on done/error.
- "deepseek-v4-1-flash-1017 is not a Mistral model": verified live through the Mistral API.
- "Part3 numbers over 4 chars fail generation": by design (4-cell answer sheet); retries carry slot-specific errors.
- "redact_for_owner leaks key to non-owners": `get_attempt` returns 403 to other students and requires class access for teachers.
- "Heartbeat/progress blocked by the import FOR UPDATE lock": the lock lives until the first commit; accepted.

Real findings, fixed: per-user cap race (advisory lock), stale outcome overwrite (`_finish` guard), duplicate exercise/import (`hold_ownership`), recovery stealing live jobs (heartbeat + stale cutoff), orphaned RUNNING jobs counting against the cap (periodic recovery every 60s), N+1 ETA queries, file payload left after recovery failure.

### Solution & Technical Details
See feature_job_queue.md and feature_ai_question_quality.md in ../feature/. Possible future work: explicit role guard in `redact_for_owner`, QUESTION_IMPORT as queue-and-close, a flag letting class PRACTICE assignments show answers after finishing.
