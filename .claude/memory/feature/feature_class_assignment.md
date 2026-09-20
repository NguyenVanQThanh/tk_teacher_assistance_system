File Name: feature_class_assignment.md
Created At: 2026-09-12
Created By: Tam Khang
Updated At: 2026-09-12
Updated By: Tam Khang

### Summary
Completed end-to-end integration of the Class Assignment feature (`F-EXE-02`), connecting the Exercise Bank with Academic Classes across both Backend and Frontend. Teachers can now assign exercises to classes with customizable due dates, view active/expired assignments in class details, and soft-delete/cancel assignments.

### Feature Specifications
- **AC-01 (Assignment Creation)**: Teachers can select an exercise and assign it to a target class by setting a valid future due date (`due_at > now`).
- **AC-02 (Teacher Scoping & Access Control)**: Enforces RBAC permissions (`EXE_ASSIGNMENT_MANAGE`, `EXE_ASSIGNMENT_VIEW`) and validates that the teacher is actively assigned to teach the corresponding subject in that class (`TeacherSubject`).
- **AC-03 (Duplicate Prevention)**: Prevents assigning the same active exercise multiple times to the same class (HTTP 409 Conflict).
- **AC-04 (Soft Delete & Lifecycle Management)**: Cancelling an assignment applies Soft Delete (`status = 'DELETED'`). If students have already submitted attempts, deletion is blocked to protect student grades.
- **AC-05 (Frontend Real-time Tab & Modals)**:
  - `AssignExerciseModal`: Interactive modal with quick due date presets (1 day, 3 days, 1 week, 2 weeks) and class selector.
  - `TeacherClassDetailPage`: Dynamic tab switcher between Student Roster and Assigned Exercises, displaying exercise title, question count, assignment date, due date, status badge, and cancellation action.

### Solution & Technical Details
- **Backend Schemas**: [schemas.py](file:///e:/tk_teacher_assistance_system/backend/app/modules/exercise/schemas.py) enriched `AssignmentOut` with `exercise_title` and `total_questions` using `@model_validator(mode="before")`.
- **Backend Repository**: [repository.py](file:///e:/tk_teacher_assistance_system/backend/app/modules/exercise/repository.py) optimized `AssignmentRepository.list_by_class_ids` using SQLAlchemy `joinedload(ClassAssignment.exercise)`.
- **Backend Router**: [assignments.py](file:///e:/tk_teacher_assistance_system/backend/app/modules/exercise/routers/assignments.py) exposes CRUD endpoints for class assignments.
- **Frontend API Client**: [api.js](file:///e:/tk_teacher_assistance_system/frontend/src/services/api.js) added `assignmentsApi` (`createAssignment`, `getClassAssignments`, `deleteAssignment`, `restoreAssignment`).
- **Frontend UI Components**:
  - [AssignExerciseModal.jsx](file:///e:/tk_teacher_assistance_system/frontend/src/components/exercises/AssignExerciseModal.jsx) & [AssignExerciseModal.css](file:///e:/tk_teacher_assistance_system/frontend/src/components/exercises/AssignExerciseModal.css).
  - [ExerciseRepositoryPage.jsx](file:///e:/tk_teacher_assistance_system/frontend/src/pages/teacher/ExerciseRepositoryPage.jsx) hooked modal into exercise card share button.
  - [ExercisePreviewModal.jsx](file:///e:/tk_teacher_assistance_system/frontend/src/components/exercises/ExercisePreviewModal.jsx) wired preview assign action with API.
  - [TeacherClassDetailPage.jsx](file:///e:/tk_teacher_assistance_system/frontend/src/pages/teacher/TeacherClassDetailPage.jsx) & [TeacherClassDetailPage.css](file:///e:/tk_teacher_assistance_system/frontend/src/pages/teacher/TeacherClassDetailPage.css) implemented dual tabs and assignments data table.
