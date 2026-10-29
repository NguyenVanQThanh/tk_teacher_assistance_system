# File Name: bugfix_homeroom_teacher_dashboard_and_quality.md
# Created At: 2026-10-29
# Created By: Tam Khang
# Updated At: 2026-10-30
# Updated By: Tam Khang

### Summary
Fixed the homeroom teacher dashboard learning quality card and class selection flow, addressed PR review feedback regarding IDOR vulnerability, eliminated all fabricated benchmark data, restored radar chart visibility and points for grade cohort averages, removed filter dropdown from the dashboard card, strictly isolated score calculations to the current academic year (`2026-2027`), linked recent submissions directly to the grading detail modal, synchronized submission ordering across Dashboard and Grading pages, fixed modal close loop and cramped modal sizing, eliminated fake Math fallback questions by seeding genuine questions for computer science exercises, and resolved premature rendering by enforcing high-UX loading states until backend responses are fully received.

### Feature Specifications
- **Submission Ordering Synchronization**: Both "Bài nộp gần đây" on the Teacher Dashboard and "Chấm điểm và phản hồi" on `/teacher/grading` strictly sort by submission/completion timestamp (`func.coalesce(end_time, start_time, created_at).desc()`).
- **Interactive Modal Closing & URL Search Params**: Closing the grading modal (`handleCloseModal`) cleanly deletes `attempt_id` and `submission_id` from the URL search parameters and resets state without triggering an infinite reopening loop. Backdrop click and the Escape key also dismiss the modal.
- **Spacious & Modern Modal UI**: Enlarged modal dimensions (`max-width: 1280px; width: 95%; height: 90vh;`) providing a spacious, clean two-column layout for student submission content and grading rubric controls.
- **Authentic Subject-Specific Questions**: Replaced hardcoded math dummy fallback questions in `GradingFeedbackModal` with genuine Question and AnswerOption database records for `Bài tập tin` (Tin học) and `Tiếng Anh`, ensuring proper subject-specific questions (ALU, TCP, Python) appear for student submissions.
- **Recent Submissions Click-Through**: Clicking on any record row or the "Chấm bài" action in "Bài nộp gần đây" redirects to `/teacher/grading?attempt_id=${id}`, which automatically opens the interactive `GradingFeedbackModal` for that specific attempt.
- **Frontend Waiting on Backend with Loading Spinners (UX)**: Front-end does not render placeholder or empty structures prematurely before backend responses complete. Dashboards and data tables render dedicated animated loaders (`Loader2`) until the response is fully resolved.
- **Current Academic Year Scope & No Filter**: The teacher dashboard learning quality card strictly displays the homeroom class of the active academic year (`2026-2027`) without filter dropdowns.
- **Radar Chart Visibility & Data Points**: The radar chart renders both the homeroom class (purple) and grade cohort average (blue) with distinct polygons, high-contrast borders, dedicated circle data points (`<circle>` dots), and hover tooltips (`<title>`).
- **Academic Year Isolation**: Average subject scores for the homeroom class and grade cohort are strictly computed from attempts and classes belonging to the current academic year (`2026-2027`), completely ignoring previous academic years.
- **Strict Authorization & IDOR Protection**: `class_id` query param on `/api/v1/teacher/dashboard` and `/api/v1/teacher/learning-quality` validates that the caller is authorized for the target class; returns `404 Not Found` if missing and `403 Forbidden` if caller lacks permission.
- **Genuine Data without Fabrication**: Radar scores and pedagogical notes reflect actual student attempt database records. Subjects without attempts evaluate to 0.0 without hardcoded default scores or invented variance subtractions.
- **Strict Grade Cohort Matching**: Uses regex matching (`^{grade}[^\d]`) to avoid false positives (e.g., class `11A12` or `112` cannot match grade `12`).
- **One Homeroom Class Per Academic Year Rule**: A teacher cannot be assigned as homeroom teacher to multiple classes within the same academic year.

### Bug & Feature Context
- **Issue 1 (Submissions Desync Between Dashboard and Grading)**: Dashboard sorted by `start_time.desc()`, while `AttemptRepository.list_attempts` sorted by `created_at.desc()`. Because seed attempts had `created_at` timestamps newer than their actual submission times, the grading page displayed older attempts at the top (e.g., Hoàng Tuấn Kiệt from 27/10) instead of the latest submissions (Nguyễn Hoàng Nam from 29/10).
- **Issue 2 (Modal Unable to Close & Reopening Loop)**: When clicking the close "X" or "Hủy" button, `setGradingSubmission(null)` cleared local state, but `attempt_id` remained in `searchParams`. The auto-open `useEffect` listened to `gradingSubmission`, so it immediately re-executed and reopened the modal.
- **Issue 3 (Cramped Modal Sizing)**: On desktop monitors, `max-width: 1100px` made the grading modal feel narrow and restricted ("màn hình nhỏ").
- **Issue 4 (Incorrect Math Questions on Computer Science Exercise)**: Exercise `Bài tập tin` had 0 questions in the database, causing `GradingFeedbackModal` to fall back to hardcoded math calculus questions ("Tìm đạo hàm...").
- **Issue 5 (Recent Submissions Disconnected)**: Clicking records in "Bài nộp gần đây" previously only opened the general grading page without highlighting or opening the selected submission.
- **Issue 6 (Premature Rendering UX)**: Front-end rendered dashboards before backend responses resolved, briefly flashing default mock notes and empty statistics before real data arrived.

### Solution & Technical Details
- **Unified Attempt Ordering**:
  - In `backend/app/modules/exercise/repository.py` (`AttemptRepository.list_attempts`) and `backend/app/modules/exercise/routers/teacher_dashboard.py`, standardized query sorting to `func.coalesce(StudentExerciseAttempt.end_time, StudentExerciseAttempt.start_time, StudentExerciseAttempt.created_at).desc()`.
- **Modal Close Bugfix & Auto-Open Ref**:
  - In `TeacherGradingPage.jsx`, introduced `autoOpenedAttemptIdRef` to record auto-opened attempt IDs, and `handleCloseModal` to delete `attempt_id` and `submission_id` from URL search parameters on close.
  - In `GradingFeedbackModal.jsx`, added backdrop overlay click-to-close (`onClick={onClose}`) with `e.stopPropagation()` on the window, and registered an Escape keydown event listener.
- **Enlarged Sizing in CSS**:
  - In `GradingFeedbackModal.css`, updated `.grading-modal-window` to `width: 95%; max-width: 1280px; height: 90vh; max-height: 94vh;` and `.grading-modal-body` to `grid-template-columns: 1.22fr 0.88fr; height: calc(100% - 64px);`.
- **Timezone Synchronization (UTC vs UTC+7)**:
  - In `backend/app/modules/exercise/routers/teacher_dashboard.py`, converted attempt timestamps to Vietnam timezone (`timezone(timedelta(hours=7))`) before formatting `strftime("%d/%m, %H:%M")`.
  - In `frontend/src/pages/teacher/TeacherGradingPage.jsx`, standardized date formatting with `formatSubmissionTime` to `${day}/${month}, ${hours}:${minutes}`, guaranteeing identical timestamps (e.g. `29/10, 18:35`) across Dashboard, Grading roster, and Modal header.
- **Database Seeding of Real UTF-8 Questions**:
  - In `backend/app/scripts/seed_questions_utf8.py`, seeded authentic UTF-8 Question and AnswerOption records for `Bài tập tin` (`60fa9f84-009f-4e88-b66e-bb2e6333d854`) covering Computer Science curriculum (ALU in Von Neumann architecture, TCP protocol reliability, Python `def` function keyword) without character corruption.
  - Updated `detailed_results` for all attempts of `Bài tập tin` to reference the real question and option UUIDs.
  - Updated `GradingFeedbackModal.jsx` to fetch attempt and exercise details dynamically and show an empty state notice instead of fake math questions if an exercise lacks questions.

### Files Modified & Created
- `backend/app/modules/exercise/repository.py` (modified)
- `backend/app/modules/exercise/routers/teacher_dashboard.py` (modified)
- `frontend/src/pages/teacher/TeacherGradingPage.jsx` (modified)
- `frontend/src/components/teacher/GradingFeedbackModal.jsx` (modified)
- `frontend/src/components/teacher/GradingFeedbackModal.css` (modified)
- `backend/app/scripts/seed_academic_data.py` (modified)
- `backend/tests/academic/test_seed_academic_year.py` (modified)
- `frontend/src/components/teacher/RecentSubmissionsTable.jsx` (modified)
- `frontend/src/components/teacher/RecentSubmissionsTable.css` (modified)
- `frontend/src/components/teacher/RecentSubmissionsSummaryCard.jsx` (modified)
- `frontend/src/pages/teacher/HomeroomTeacherDashboard.jsx` (modified)
- `frontend/src/pages/teacher/SubjectTeacherDashboard.jsx` (modified)
- `frontend/src/pages/teacher/TeacherDashboard.css` (modified)
- `frontend/src/components/teacher/LearningQualityCard.jsx` (modified)
- `frontend/src/components/teacher/RadarChart.jsx` (modified)
- `backend/app/modules/exercise/services/learning_quality_service.py` (modified)
- `backend/tests/exercise/test_learning_quality.py` (modified)
- `.claude/memory/fix/bugfix_homeroom_teacher_dashboard_and_quality.md` (modified)

