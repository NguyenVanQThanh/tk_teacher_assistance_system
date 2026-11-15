File Name: feature_teacher_create_exercise_split_editor.md
Created At: 2026-11-16
Created By: AI Agent
Updated At: 2026-11-16
Updated By: AI Agent

### Summary
Redesigned the teacher "create exercise directly" page (`/teacher/exercises/create-manual`) to match the exercise edit screen: question list on the left, math editor with live preview on the right. Also fixed three unrelated issues found while running the full test suite (login redirect race, missing error messages, notification error code).

### Feature Specifications
- Basic info card: title, exercise kind (EXAM/PRACTICE), subject, grade, duration, optional open time and due time.
- Shared formula toolbar: subject tabs (math, physics, chemistry, Greek), image upload, quadratic equation, table insert.
- Left column: question cards (number, level, snippet, type), add question, active highlight.
- Right column per question: level select, delete, `MathTextEditor` content, question type switch (MultipleChoice, TrueFalse with 4 statements, ShortAnswer, Other with sub-questions), solution guide, live preview.
- Switching type uses `convertAnswerSetup` and asks for confirmation when answer data would be lost.
- Save validates a non-empty title and at least one question with content, creates the exercise, then adds each non-empty question in order.
- Deliberately skipped: per-question score (the edit screen does not persist it), unsaved-changes guard, table segment editor.

### Bug & Feature Context
- Login redirect race: `LoginPage.jsx` called `navigate()` inside a 500 ms `setTimeout` after login. Navigating within that window (for example clicking a sidebar item) was overridden and sent back to the dashboard. This made `admin-subjects.spec.js` TC-SUBJ-01 fail.
- The e2e CORS errors in admin tests were not a CORS problem. The DB was two migrations behind (`users.phone NOT NULL`, `notifications` table), so `/api/v1/notifications/unread-count` returned 500 without CORS headers. Fixed by running `alembic upgrade head` on the dev DB.
- `errorMessages.selfcheck.mjs` failed: missing mappings for `ERR-ACAD-INVALID_PHONE` and `ERR-NOTIFICATION-NOT-FOUND` (the backend code used `-` instead of the `_` convention).
- TC-STU-02 clicked the centre of the pending assignments card and hit a task row, which navigates away. Exposed once the login delay was removed.

### Solution & Technical Details
- Rewrote `frontend/src/pages/teacher/CreateExerciseManualPage.jsx`; reuses `EditExerciseModal.css` and `CreateExerciseManualPage.css`.
- `frontend/src/components/documents/EditExerciseModal.jsx`: now exports `QUESTION_TYPES`, `normalizeQType`, `OPTION_LETTERS`, `fourSlots`, `convertAnswerSetup`, `buildQuestionPayload` so both screens share one payload builder.
- `frontend/src/pages/LoginPage.jsx`: removed the delayed navigate; the `isAuthenticated` effect handles the redirect and honours `location.state.from`. The success banner now barely shows.
- `frontend/src/utils/errorMessages.js`: added the two mappings.
- `backend/app/modules/notification/routers/notifications.py`: code renamed to `ERR-NOTIFICATION-NOT_FOUND` (backend restart needed).
- Tests: added TC-05a in `frontend/e2e/teacher-portal.spec.js`; TC-STU-02 in `frontend/e2e/student-portal.spec.js` now waits for `networkidle` and clicks the card title.
- Result: e2e 43/43 pass, `npm run test:unit` pass.
