File Name: feature_rbac_and_student_ai_generation.md
Created At: 2026-11-13
Created By: AI Agent
Updated At: 2026-11-13
Updated By: AI Agent

### Summary
Added resource-level RBAC to the document and exercise repositories, a head-of-subject-department role managed by Admin, and a rebuilt student AI exercise generator that uses SGK chunks (filtered by chapter), the class teachers' documents and an optional small upload as context. SGK RAG data was also plugged into the dev/prod Docker stack. Full plan: `docs/plan_rbac_ai_generation.md`.

### Feature Specifications
- **Visibility.** A teacher sees only resources they own, plus those owned by the head of a subject they teach (head's documents must be `Uploaded`; head drafts stay private). Heads see only their own. Students see only exercises they created and never documents (router returns 403). Admin sees everything.
- **Errors.** Invisible resource -> 404. Visible but not owner (writes) -> 403 (`ERR-AUTH-OWNER_ONLY`, documents keep `ERR-DOC-PERMISSION_DENIED`). Head resources are read-only for department teachers.
- **One head per subject.** `subjects.head_teacher_id` is a single column, so assigning a new head replaces the old one. The head must be an active Teacher with an ACTIVE `TeacherSubject` on that subject (422 `ERR-ACAD-INVALID_HEAD_TEACHER`).
- **Admin API** (permission `ACAD_SUBJECT_HEAD_ASSIGN`, Admin only): `GET /api/v1/subjects/{id}/head-teacher-candidates`, `PUT /api/v1/subjects/{id}/head-teacher` with `{teacher_id}` (null clears). `head_teacher_id` is no longer accepted by `PUT /subjects/{id}`. UI: `/admin/subjects`.
- **Student AI generation** (`/api/v1/ai-exercises`): `GET /chapters?subject_id=` and multipart `POST /student` (`payload` JSON + optional `file`). Requires subject, at least 1 chapter (max 10), prompt up to 300 chars, matrix per part (mcq/tf/short x NhanBiet/ThongHieu/VanDung, each part 0-15, total 1-40). File must be under 1 MiB, types pdf/docx/txt (413/415/411 checks before the body is read; magic bytes verified; no-text -> 422).
- **Context.** SGK chunks restricted to subject+grade docs and chosen chapters (hybrid vector + tsv, RRF), plus documents of the teachers who teach the student's own class for that subject, plus the uploaded text. Per-source character quotas: SGK 7000 / teacher docs 3000 / file 4000, dedup by normalized text + Jaccard. Student text is wrapped in tags and treated as data (prompt-injection guard).
- **Question templates.** MCQ exactly 4 distinct options with one correct; True/False 4 statements a-d stored as 4 `AnswerOption` rows (earlier code stored them only in `segments`, so TF always scored 0); short answer <= 30 chars. Invalid items are dropped and only the missing count is re-requested (max 2 retries); still short -> 502 `ERR-EXE-AI_GENERATION_FAILED`. Difficulty is assigned server-side by slot.
- **Personal assignments.** Student-generated exercises create a `ClassAssignment` with `owner_student_id = student`; classmates cannot see, start, take or read results (404). Teacher dashboards and learning-quality exclude them. No Subject/Class is auto-created and no student is auto-enrolled (no class -> 403 `ERR-EXE-AI_NO_CLASS`).
- **LLM order.** Mistral first (`AI_MISTRAL_MODEL`, default `mistral-large-latest`, JSON mode), Gemini as fallback (needs `api_version="v1beta"` for `system_instruction`/`response_schema`). Gemini free tier had a 20 requests/day quota, which is why Mistral leads.
- **Frontend.** Student AI form: subject select, chapter multi-select, optional file with client-side size/type check, full matrix. Edit/Delete shown only to owners or Admin; others' head items show a "Tổ trưởng bộ môn" badge. Students no longer fall back to `GET /exercises/{id}` (that endpoint needs `EXE_EXERCISE_VIEW`, which students lack); they use `/assignments/{id}/taking`, which hides the answer key.

### Bug & Feature Context
Bugs found in the previous implementation and fixed here:
- Teachers saw every other teacher's published documents, and every exercise in a taught subject.
- Students could fetch any exercise with its answer key.
- Student-generated exercises leaked to the whole class; a student without a class was silently enrolled in an arbitrary one; a Subject could be created on the fly.
- Several assignment endpoints (delete, restore, result summary) lacked ownership/class checks; `get_attempt` let classmates read each other's attempts.
- Teacher `document_ids` for RAG were not ownership-checked (IDOR).
- `chunks.chuong` was NULL for about 99% of SGK rows, so a chapter picker had nothing to list.

### Solution & Technical Details
- **Central policy:** `backend/app/modules/auth/access_policy.py` (`document_visibility_clause`, `exercise_visibility_clause`, `visible_document_ids`, `ensure_can_write`); SQLAlchemy expressions only, so it works on SQLite tests and Postgres.
- **Migrations (new, none edited):** `a1c3e5f7b9d2` adds `subjects.head_teacher_id`, `class_assignments.owner_student_id` (backfilled for student assigners) and indexes (including `chunks(doc_id, chuong)`); `b2d4f6a8c0e1` seeds `ACAD_SUBJECT_HEAD_ASSIGN` and grants it to Admin.
- **Chapter backfill:** `backend/app/scripts/backfill_sgk_chapters.py` (also run at the end of `load_sgk_rag.py`); idempotent, parses `CHƯƠNG N` headings in sequence to drop table-of-contents noise, falls back to `Bài N`/`Unit N`. It is a data script, not a migration, because chunks are restored after migrations. Docs such as Tin học end up with many fallback labels.
- **AI pipeline:** `routers/ai_generation.py`, `services/ai_exercise_service.py`, `ai_generator_service.py` (one LLM call per part in parallel, validation/repair), `rag_retrieval_service.py`, `rag_context_service.py`, config `AI_GENERATE_CONCURRENCY`/`AI_PART_WORKERS`/`AI_PART_MAX_RETRIES`, semaphore -> 503 `ERR-EXE-AI_BUSY`. Mistral may name the question field `question`; the validator accepts it as an alias.
- **Other backend files:** `document_service.py`, `exercise_service.py`, `question_service.py`, `exercise/repository.py`, `routers/exercises.py`, `assignment_service.py`, `attempt_service.py`, `student_dashboard.py`, `teacher_dashboard.py`, `learning_quality_service.py`, `academic/{schemas,routers/subjects,services/subject_service}.py`, `models/models.py`.
- **SGK data deployment:** `docker-compose.yml` mounts `./sgk_data:/sgk_data:ro`; `deploy/scripts/setup_sgk.sh [dev|prod]` brings the stack up and verifies chunks (15364), sgk_docs (41), images (5360) and the API key. `vectors.dump` and `images.tar` go in `sgk_data/` (gitignored). `load_sgk.sh` only restores into empty targets.
- **Seed:** `seed_academic_data.py` step `[5b]` assigns 7 subject heads (Toán 0999000002, Hóa 0999000005, Lý 0999000004, Anh 0999000006, Văn 0999000007, Sinh 0999000008, Sử 0999000009). That script already fails later at the student step with `student_class_student_code_key` on existing data; this predates the change.
- **Frontend:** `services/api.js`, `StudentExercisesPage.jsx`, `StudentExerciseTakingPage.jsx`, `CreateExerciseModal.jsx`, `DocumentCard.jsx`, `ExerciseCard.jsx`, `DocumentRepositoryPage.jsx`, `ExerciseRepositoryPage.jsx`, new `pages/admin/AdminSubjectsPage.jsx` (route in `App.jsx`, `AdminSidebar.jsx`, `AdminLayout.jsx`).
- **Tests:** backend `test_repository_rbac.py`, `test_assignment_rbac.py`, `test_student_ai_generation.py`, `unit/test_ai_question_validation.py`, `unit/test_sgk_chapter_backfill.py`; `tests/conftest.py` clears `MISTRAL_API_KEY` so tests never hit real APIs. Playwright `e2e/admin-subjects.spec.js` plus new cases in the student/teacher specs. Smoke: `backend/scripts/smoke_rbac_ai.py` (credentials via CLI/env only), run against the dev stack: 33/33.
- **Verified:** pytest 484 pass, Playwright 36/36, smoke 33/33, migrations applied to the dev DB.

### Known gaps / next steps
- Not tested: restore/ingest of head-owned documents returning 403; answer-release on a head exercise; a student in another class never retrieving a different class's teacher documents.
- No test covers the old head losing department visibility after reassignment.
- Grading by a teacher on another teacher's exercise now gets 404 from `getExerciseDetail` (`GradingFeedbackModal.jsx` falls back to null); if it breaks, serve questions via the attempt endpoint, do not loosen scope.
- True MMR, SSE progress for generation and a per-user rate limit were skipped on purpose.
- Chapter lists for Tin học, Ngữ văn and Tiếng Anh are noisier than Hóa/Toán.
- Nothing was committed at the time of writing.
