File Name: feature_exercise_kind_answer_release.md
Created At: 2026-11-13
Created By: AI Agent
Updated At: 2026-11-13
Updated By: AI Agent

### Summary
Added `exercise_kind` (EXAM/PRACTICE) and a teacher-controlled "answer release" flag for exams; replaced native alert/confirm with themed toast/confirm.

### Feature Specifications
- `exercises.exercise_kind` (default PRACTICE) replaces guessing the kind from the title. Backfill: title containing "đề thi" -> EXAM.
- For EXAM exercises, students see questions but NOT answers/explanations until the teacher releases them per assignment (`class_assignments.answers_released_at`).
- Release button (green; outline = hidden, solid = released) sits beside the X button on exercise cards, plus the grading page, home recent-submissions item and class "Bai tap da giao" tab.
- One kind tag per exercise.
- Long answer boxes wrap/grow instead of scrolling.
- All native alert/confirm replaced by `components/common/toast.jsx` and `confirmDialog.jsx`.

### Bug & Feature Context
Feature. Teachers needed to show answers only after all students finished.

### Solution & Technical Details
- Endpoints: `PUT /api/v1/assignments/{id}/answer-release`, `PUT /api/v1/exercises/{id}/answer-release` (EXAM only, all active assignments).
- `AttemptService.redact_for_owner` strips answers for the owner while hidden.
- Migrations: `b1d3e5f7a9c2_add_answers_released_at_to_class_assignments.py`, `c2e4f6a8b0d1_add_exercise_kind_to_exercises.py`.
- Files: `backend/models/models.py`, `exercise/schemas.py`, `services/{assignment,attempt}_service.py`, `routers/{assignments,exercises,attempts,teacher_dashboard}.py`, frontend `AnswerReleaseButton.jsx`, `ExerciseCard.jsx`, `TeacherGradingPage.jsx`, `RecentSubmissionsSummaryCard.jsx`, `TeacherClassDetailPage.jsx`.
- Tests: `tests/exercise/unit/test_exam_answer_redaction.py`.
