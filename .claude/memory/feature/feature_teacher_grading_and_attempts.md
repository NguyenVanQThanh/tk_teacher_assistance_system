File Name: feature_teacher_grading_and_attempts.md
Created At: 2026-09-12
Created By: Tam Khang
Updated At: 2026-09-12
Updated By: Tam Khang

### Summary
Completed end-to-end integration of the Teacher Grading & Student Attempts module (`F-EXE-03` / `F-EXE-04`), connecting real attempt submissions, automatic score evaluation, and manual grade/feedback overrides between Backend and Frontend.

### Feature Specifications
- **AC-01 (Attempt Listing & Scoping)**: Teachers can list and filter student exercise submissions across classes they teach. Role-based scoping ensures teachers only access submissions belonging to their assigned classes.
- **AC-02 (Attempt Detail & Auto-Grading Results)**: Full attempt details provide per-question evaluation breakdown (MultipleChoice correct/incorrect matching and ShortAnswer manual grading flags).
- **AC-03 (Teacher Grade & Feedback Update)**: Teachers can override the score (validated 0.0 to 10.0) and attach personalized feedback notes (`PUT /api/v1/attempts/{id}/grade`).
- **AC-04 (Frontend Interactive Grading Dashboard)**:
  - `TeacherGradingPage`: Real-time statistics (total submissions, average score, pass rate), class/subject/status filters, and search.
  - `GradingFeedbackModal`: Real-time question inspection, answer option comparison, score recomputation, quick feedback templates, and auto-jump to the next pending submission.

### Solution & Technical Details
- **Backend Schemas**: [schemas.py](file:///e:/tk_teacher_assistance_system/backend/app/modules/exercise/schemas.py) added `AttemptListItemOut` and `AttemptGradeUpdateRequest`.
- **Backend Repository**: [repository.py](file:///e:/tk_teacher_assistance_system/backend/app/modules/exercise/repository.py) implemented `AttemptRepository.list_attempts` with `joinedload` on `student`, `class_obj`, and `exercise`.
- **Backend Service**: [attempt_service.py](file:///e:/tk_teacher_assistance_system/backend/app/modules/exercise/services/attempt_service.py) implemented `list_attempts` and `update_attempt_grade` with class access validation.
- **Backend Router**: [attempts.py](file:///e:/tk_teacher_assistance_system/backend/app/modules/exercise/routers/attempts.py) exposed `GET /api/v1/attempts` and `PUT /api/v1/attempts/{id}/grade`.
- **Frontend Client**: [api.js](file:///e:/tk_teacher_assistance_system/frontend/src/services/api.js) added `attemptsApi` methods.
- **Frontend Pages & Modals**:
  - [TeacherGradingPage.jsx](file:///e:/tk_teacher_assistance_system/frontend/src/pages/teacher/TeacherGradingPage.jsx)
  - [GradingFeedbackModal.jsx](file:///e:/tk_teacher_assistance_system/frontend/src/components/teacher/GradingFeedbackModal.jsx)
