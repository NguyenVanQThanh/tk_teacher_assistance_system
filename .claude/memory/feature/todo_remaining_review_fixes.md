File Name: todo_remaining_review_fixes.md
Created At: 2026-11-12
Created By: AI Agent
Updated At: 2026-11-12
Updated By: AI Agent

### Summary
Open items left after the student/teacher screen review-and-fix round. Everything else in that round was implemented (not yet confirmed by the user).

### Feature Specifications
Not done:
- Student dashboard: AI competency assessment section (needs spec; radar and feedback cards still use mock fallbacks).
- Teacher: export gradebook of a whole class for ALL subjects (only own subject for class; all subjects only in per-student modal CSV).
- Teacher: XLSX export (no XLSX library installed; CSV and PDF only).
- Teacher library: "share" button (no such code exists; verify what was meant).
- Teacher exercise edit: parts 2/3 rendered as boxes (unconfirmed, check in browser after caret fix in MathTextEditor).
- Grading: short-answer stored as text is an import/data issue; True/False key not editable via PUT /exercises/{id}/answer-key.
- Student schedules stored only in localStorage (soft delete flag); no backend table or Alembic migration.
- Student notifications still mock; teacher notifications derived from data, no read state.
- StudentDetailModal: AI-assignments table and semester subject-scores table still sample data; rank on student modals uses mock grades.
- Assign popup: fixed due date (7 days) and max_attempts 1, no inputs.
- Exam lock is client-side only, not enforced server-side.
- Teacher timetable still hardcoded WEEKLY_TEMPLATE with Math-flavoured names.

### Bug & Feature Context
See git diff on branch fix/report for what was changed.

### Solution & Technical Details
Key new files: backend/app/modules/exercise/services/grading_report_service.py, frontend/src/components/teacher/AssignExercisesDialog.jsx, frontend/src/utils/gradeClassification.js, frontend/src/utils/gradebookExport.js.
