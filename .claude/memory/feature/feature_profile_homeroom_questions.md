# File Name: feature_profile_homeroom_questions.md
# Created At: 2026-09-12
# Created By: Tam Khang
# Updated At: 2026-09-12
# Updated By: Tam Khang

### Summary
Comprehensive integration and end-to-end wiring of:
1. **Teacher Security & Profile Management**: Real-time user profile retrieval via `GET /api/v1/auth/me` and secure password updates via `POST /api/v1/auth/change-password`.
2. **Interactive Question Editing & Deletion**: Inline modification of question content, cognitive difficulty, correct answers, and soft deletion (`DELETE /api/v1/questions/{id}`) in `ExercisePreviewModal`.
3. **Teacher Homeroom & Class Student Roster Management**: Class switching and dynamic student list loading via `GET /api/v1/classes` and `GET /api/v1/classes/{class_id}/students` with eager relationship loading (`joinedload`).

---

### Feature Specifications
1. **Teacher Security & Profile (`TeacherProfilePage.jsx`)**:
   - Fetches current authenticated user data (`full_name`, `email`, `phone`, `role`, `user_id`) from `authApi.getMe()`.
   - Validates old password and new password length ($\ge 8$ chars) before dispatching `authApi.changePassword`.
   - Handles password security requirements (uppercase, numeric, special characters) with visual feedback and error messaging.

2. **Question Management (`ExercisePreviewModal.jsx`)**:
   - In-modal question inspection, editing, and soft-deletion.
   - For Multiple Choice: inline option editing and single-click correct answer designation.
   - For Short Answer: inline standard answer modification.
   - Calls `questionsApi.updateQuestion` (`PUT /api/v1/questions/{id}`) and `questionsApi.deleteQuestion` (`DELETE /api/v1/questions/{id}`).

3. **Homeroom Class & Student Roster (`TeacherHomeroomPage.jsx`)**:
   - Dynamically retrieves teacher's assigned classes from `classesApi.getClasses()`.
   - Allows class switching dropdown if multiple classes exist.
   - Retrieves enrolled students using `classesApi.getStudentsInClass(class_id)` with populated student profiles.

---

### Solution & Technical Details
- **Backend**:
  - `repository.py`: Added `options(joinedload(StudentClass.student))` to `EnrollmentRepository.filter_enrollments` to ensure student names and user profiles are loaded without secondary queries.
- **Frontend Services**:
  - `api.js`: Leveraged `authApi`, `classesApi`, `exercisesApi`, and `questionsApi`.
- **Frontend Components**:
  - `TeacherProfilePage.jsx`: Integrated `authApi.getMe()` and `authApi.changePassword()`.
  - `ExercisePreviewModal.jsx`: Added inline editor form, edit toggle, delete confirmation, and API synchronization.
  - `TeacherHomeroomPage.jsx`: Connected real class switching and student roster loading.

---

### Files Modified & Created
- `backend/app/modules/academic/repository.py`
- `frontend/src/pages/teacher/TeacherProfilePage.jsx`
- `frontend/src/components/exercises/ExercisePreviewModal.jsx`
- `frontend/src/pages/teacher/TeacherHomeroomPage.jsx`
