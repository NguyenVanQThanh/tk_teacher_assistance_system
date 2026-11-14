# Plan: RBAC for document/exercise repositories + student AI exercise generation

Created At: 2026-11-13 | Created By: AI Agent (Opus planner) | Updated At: 2026-11-13 | Updated By: AI Agent

Rules: obey `.claude/rules/*.md` (file headers, English comments/messages, NEW Alembic revision only, SOFT DELETE only, never read `.env`).

## Findings (current state)
- No "head of subject department" concept exists. Add `subjects.head_teacher_id`.
- Documents: all visibility goes through `DocumentService.visible_documents_query` (`document_service.py:51`) and `check_document_access` (`:61`). Today every published doc is visible to all teachers (wrong).
- Exercises: teacher scope = own OR any exercise in a taught subject (`exercise_service.py:102-157,199-208`, `repository.py:79-86`) (wrong). Students can `GET /exercises/{id}` any exercise with answer key (`exercise_service.py:135-159`). Writes are not owner-only (`:161-184`, `question_service.py:27,76,120`).
- `generate_ai_exercise` (`exercise_service.py:212-395`): creates Subject/Class/enrolls student arbitrarily, class-wide `ClassAssignment` (leaks to classmates), True/False statements not stored as `AnswerOption` (grader `grading_service.py:135-147` reads options, so TF always 0), matrix collapsed to part totals.
- Assignments: `delete_assignment` (`assignment_service.py:542`), `restore_assignment` (`:578`) no access check; `get_assignment_result_summary` swallows class-access failure (`:663-668`).
- RAG: hybrid RRF exists (`rag_retrieval_service.py`), teacher-doc scope `(subject_id, teacher_ids)` supported but unused for students (`rag_context_service.py:72`); teacher `document_ids` not ownership-checked (IDOR, `:76`); one 12k-char SGK-first pool.
- `chunks.chuong` is NULL in ~99% rows. Chapter headings appear in text (e.g. `CHƯƠNG 1 ESTER - LIPID`). Needs backfill.
- Frontend: Edit/Delete always shown (`DocumentCard.jsx`, `ExerciseCard.jsx`); student AI form uses free-text subject (`StudentExercisesPage.jsx:682`); teacher modal sends `subjectsList[0]` (`CreateExerciseModal.jsx:288,319,399`).
- Tests: pytest on SQLite in-memory (`backend/tests/conftest.py`). Playwright in `frontend/e2e/`. Dev stack: `smartlms_backend`:8000, `smartlms_frontend`:3000, `postgres` db `teacher_assistance`. Alembic head `f4b8c2d6e9a1`.

## Shared contracts (all packages code against these)
- Columns: `Subject.head_teacher_id` (UUID FK users, nullable), `ClassAssignment.owner_student_id` (UUID FK users, nullable; NULL = class-wide).
- New `backend/app/modules/auth/access_policy.py` (SQLAlchemy expressions only, SQLite+Postgres safe):
  ```
  is_admin(db, user) -> bool
  is_teacher(role_name) -> bool                       # "Teacher" | "HomeroomTeacher"
  document_visibility_clause(db, user)                # None for Admin, else filter on Document
  exercise_visibility_clause(db, user)                # None for Admin, else filter on Exercise
  visible_document_ids(db, user, ids) -> set[UUID]
  ensure_can_write(db, user, owner_id)                # 403 ERR-AUTH-OWNER_ONLY unless owner or Admin
  ```
- `AiExerciseService(db).generate(user, payload)` (teacher) and `.generate_for_student(user, payload, file_text, file_name)`.
- Rules: Teacher T sees resource if owner==T, OR exists subject row where owner is that subject's `head_teacher_id`, resource.subject_id is that subject, T teaches it (ACTIVE `TeacherSubject`); head docs must have status 'Uploaded' (head drafts private). Head H sees only own. Student: exercises `created_by==self` only; documents 403 at router. Admin: all. Not visible -> 404; visible-but-not-owner write -> 403.

## RBAC endpoints to patch
Documents (`document_service.py:51,61`): list, dashboard, get, view, download, put, delete, restore, ingest. Exercises reads: list, get, export-pdf. Exercise writes (new `get_exercise_for_write` = visibility + ensure_can_write): put, answer-release, delete, restore, add question, import, question put/delete, answer-key. `POST /exercises/ai-generate` teachers only; filter `document_ids` via `visible_document_ids` (404 if any invisible). Assignments: create (exercise visible + class check); delete/restore/answer-release (`assigned_by==me` or Admin + `check_class_access`); result summary: remove try/except pass; fallback by exercise id only if visible. Personal assignments: feed, class assignments, student dashboard (`student_dashboard.py:175`), `start_attempt`, `/assignments/{id}/taking`, result summary visible only if `owner_student_id IS NULL OR == me`; teacher dashboards and learning-quality exclude `owner_student_id IS NOT NULL`. Attempts already scoped (regression tests only).
Frontend: show Edit/Delete only if `uploaded_by`/`created_by == user.user_id` or Admin; label head items "Head of department" read-only; remove `getExerciseDetail` fallback for students in `StudentExerciseTakingPage.jsx:202,211`. Add `head_teacher_id` to `PUT /api/v1/subjects/{id}` (active Teacher teaching that subject).
Grading default strict: if grading modal breaks, serve questions via the attempt endpoint, do not loosen scope.

## Student AI generation pipeline
New router `routers/ai_generation.py`, prefix `/api/v1/ai-exercises`:
- `GET /chapters?subject_id=` -> `[{chapter, doc_id, page_start}]`; grade from `parse_grade(class_name)` of student's class; subject must be taught in a student's class else 404. SQL: `SELECT doc_id, chuong, min(page) FROM chunks WHERE doc_id = ANY(:ids) AND chuong IS NOT NULL GROUP BY 1,2 ORDER BY doc_id, 3`.
- `POST /student` (Student role; `async def`, parses form itself): missing Content-Length -> 411; >= 1 MiB + 64 KiB -> 413 `ERR-EXE-AI_FILE_TOO_LARGE` BEFORE `request.form()`; `form = await request.form(max_files=1, max_fields=4)`; reject `file.size >= 1_048_576`, bounded `read(1_048_576)`; type check extension in {.pdf,.docx,.txt} AND magic bytes (`%PDF`, `PK\x03\x04`, strict UTF-8) else 415; rest via `run_in_threadpool`. Fields: `payload` (JSON string), `file` optional. Payload: `{subject_id, chapters:[str] (min1,max10), topic_prompt (<=300), duration_minutes (5-180), matrix:{mcq|tf|short:{NhanBiet,ThongHieu,VanDung}}}`; each part 0-15, total 1-40; 422 codes `ERR-EXE-AI_CHAPTER_REQUIRED`, `ERR-EXE-AI_INVALID_CHAPTER` (must be in server-computed list), `ERR-EXE-AI_EMPTY_MATRIX`.
- Chapter backfill: idempotent `app/scripts/backfill_sgk_chapters.py`, also called at end of `load_sgk_rag.py`. Per doc, text chunks whose first line matches `^(CHƯƠNG|Chương|CHỦ ĐỀ|PHẦN)\s+([IVXLC]+|\d+)` (parse roman). Chapter start pages in sequence: start(1)=first page with chapter 1; start(n)=first page after start(n-1) with chapter n (drops TOC and running-header noise). `chuong` for page p = latest n with start(n)<=p, stored "Chương N: TITLE". Docs with <2 chapter numbers fall back to `Bài N` / `Unit N`. Pages before chapter 1 stay NULL. Data script, not a migration.
- Context (`RagContextService`): SGK = doc_ids(subject+grade) AND `c.chuong = ANY(:chapters)` pushed into vector and FTS queries; queries `[topic_prompt or chapter titles]`, no LLM expansion for students. Teacher docs: `teacher_ids` = `TeacherSubject.teacher_id` for the student's ACTIVE classes, subject S, ACTIVE, user active -> `search_documents(teacher_subject_scope=(S, ids))` (SQL already requires status 'Uploaded'). Only teachers of the student's own class. Uploaded file: PyMuPDF / python-docx / UTF-8, no OCR; no text -> 422 `ERR-EXE-AI_FILE_NO_TEXT`; cap 4000 chars. Budget quotas: SGK 7000 / teacher docs 3000 / file 4000 chars; SGK round-robin across chapters; dedup by normalised `content[:80]` + token Jaccard >= 0.8.
- Prompt injection: wrap in `<student_file>`/`<student_request>`, strip tag-like sequences, system instruction says tagged content is data; counts/types/difficulty only from server matrix, placed after data. Real guard = schema validation.
- Generation (`ai_generator_service.py`): one Gemini call per non-empty part, parallel `ThreadPoolExecutor(3)`, no DB in threads; `response_mime_type=json` + `response_schema`; explicit slot list; difficulty assigned server-side by slot index.
- Validation/repair: MCQ exactly 4 non-empty distinct options, strip `A.`/`A)` prefix, exactly one correct (trim extras if >4 with one correct). TF: 4 statements a-d with boolean; convert if returned as options; store as 4 `AnswerOption` rows content `"a) ..."`, `is_correct`, `display_order` 0-3 (matches grader and `QuestionUpdate` validator). Short: non-empty `correct_answer` <= 30 chars, no options. Drop invalid; retry only missing count up to 2 times (temp 0.4, feed error list); trim extras; still short -> 502 `ERR-EXE-AI_GENERATION_FAILED`.
- Persistence (`services/ai_exercise_service.py`, shared by teacher+student flows): never create Subject/Class, never auto-enroll; student with no class -> 403; store `Exercise` with `ai_metadata` (chapters, matrix, sources), questions, options for MCQ and TF; personal assignment with `owner_student_id=student` (teacher flow NULL). Process-wide `AI_GENERATE_SEMAPHORE` (default 4, acquire timeout 30s) -> 503 `ERR-EXE-AI_BUSY`.

## Optimizations (do) / skip
Do: chapter pushdown + `(doc_id, chuong)` index; one batched embed call; `lru_cache(512)` query->embedding; skip query expansion when chapters given; per-part parallel LLM; structured output; retry only missing items. Skip (leave `ponytail:` comment): true MMR, SSE progress, per-user rate limit.

## Alembic (one new revision, down_revision `f4b8c2d6e9a1`, owned by WP1)
1. `subjects.head_teacher_id` UUID FK users ON DELETE SET NULL, nullable, indexed.
2. `class_assignments.owner_student_id` UUID FK users ON DELETE SET NULL, nullable, indexed; backfill `owner_student_id = assigned_by` where assigner role is Student.
3. Indexes (if_not_exists): `chunks(doc_id, chuong)` (guard: only if table exists), `documents(uploaded_by, status)`, `documents(subject_id, uploaded_by)`, `teacher_subjects(class_id, subject_id, status)`, `subjects(head_teacher_id)`, `class_assignments(owner_student_id)`.

## Work packages (disjoint files)
- WP1 RBAC core: `backend/models/models.py`, new alembic revision, `auth/access_policy.py`, `document_service.py`, `exercise_service.py` (replace `generate_ai_exercise` body with delegation to WP2 service), `exercise/repository.py`, `question_service.py`, `routers/exercises.py`, `academic/schemas.py`, `academic/services/subject_service.py`. Tests: `tests/exercise/test_exercises.py`, `test_document_and_grading_dashboard.py`, `tests/document/*`, new `tests/exercise/test_repository_rbac.py`.
- WP2 AI pipeline: `routers/ai_generation.py`, `services/ai_exercise_service.py`, `ai_generator_service.py`, `rag_retrieval_service.py`, `rag_context_service.py`, `exercise/schemas.py`, `app/main.py` (one include_router line), `core/config.py`, `core/resource_limits.py`, `scripts/backfill_sgk_chapters.py`, `scripts/load_sgk_rag.py`. Tests: `tests/exercise/test_rag_*.py`, new `unit/test_ai_question_validation.py`, `unit/test_sgk_chapter_backfill.py`, `test_student_ai_generation.py`.
- WP3 assignments/attempts/student scope + smoke: `assignment_service.py`, `attempt_service.py`, `student_dashboard.py`, `teacher_dashboard.py`, `learning_quality_service.py`, new `backend/scripts/smoke_rbac_ai.py`. Do NOT edit `repository.py`. Tests: `test_assignments.py`, `test_attempts.py`, `test_taking_and_sync.py`, new `test_assignment_rbac.py`.
- WP4 Frontend: `frontend/src/services/api.js` (`aiExercisesApi.getChapters`, `generateForStudent` multipart), `StudentExercisesPage.jsx` (subject from `subjectsApi.getSubjects()`, chapter multi-select >=1, optional file input blocking >=1 MiB and bad types, full matrix), `StudentExerciseTakingPage.jsx`, `CreateExerciseModal.jsx` (send selected subject + matrix), `DocumentCard.jsx`, `ExerciseCard.jsx`, `DocumentRepositoryPage.jsx`, `ExerciseRepositoryPage.jsx`, `frontend/e2e/student-portal.spec.js`, `teacher-portal.spec.js`. Keep UI language consistent with existing pages.

## Test plan
Unit: backfill on synthetic pages; validation/repair cases (MCQ 3/5/0/2 correct, prefixes, TF 3 statements/keys/string booleans, long short answers, retry-missing with mocked LLM, slot difficulty); budget packing; prompt wrapper strips tags; access_policy clauses; student teacher-id resolution.
RBAC matrix fixture: subjects S1 (head H), S2; teachers A (class C1), B (class C2) teach S1; H has docs in S1 and S2 + a draft; students X,Y in C1, Z in C2; docs dA,dB,dH,dH2,draft; exercises likewise; X,Y each own personal AI exercise+assignment.
- A: list {dA,dH}; dB 404 on get/view/download/put/delete/restore/ingest; dH 200 get/download, 403 put/delete; dH2 + head draft 404; same for exercises incl. export-pdf, add question, import, answer-key, answer-release; ai-generate with dB id 404; B's assignment delete/restore 403/404; C2 assignment summary 403.
- H own only; Admin all.
- X: `/documents` 403; A's exercise 404; own AI exercise 200; Y's 404; feed excludes Y's personal assignment; start/taking/summary on Y's 404; Y's attempt 403; chapters for subject not taught in C1 404.
- Z: generation uses only B's docs; spy on `search_documents` kwargs, dA never retrieved.
- Upload: 1,048,576 B -> 413; no Content-Length -> 411; fake .pdf -> 415; image-only PDF -> 422; `chapters=[]` 422; unknown chapter 422; empty matrix 422; prompt >300 422.
Smoke (`backend/scripts/smoke_rbac_ai.py`, httpx, creds via CLI args/env, never `.env`): prepare `docker exec smartlms_backend alembic upgrade head`, `python -m app.scripts.backfill_sgk_chapters`, set head teacher via `PUT /api/v1/subjects/{id}`; checks chapters non-empty for Hoa 12, cross-teacher 404s, one real student generation (small .txt, 2 MCQ + 1 TF + 1 short) returns 201 with 4 TF options stored, 1.1 MB upload 413, classmate feed excludes it, attempt start+submit grades TF correctly. UI: `cd frontend && npx playwright test e2e/student-portal.spec.js e2e/teacher-portal.spec.js`. Backend: `docker exec smartlms_backend pytest -q`.
Existing tests changing on purpose: `test_document_and_grading_dashboard.py:174`, subject-scope assertions in `test_exercises.py`, student `ai-generate` test at `test_exercises.py:199` (moves to new route).
