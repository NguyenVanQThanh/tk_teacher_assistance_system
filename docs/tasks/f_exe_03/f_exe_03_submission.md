> Path: `docs/tasks/f_exe_03/f_exe_03_submission.md`
> Slice: `SL-EXE-03` · Type: `feature` · Size: `large` · SP: `5`
> Depends on: `F-EXE-02`, `F-EXE-04`
> Status: `draft`
> Created At: `2026-07-28`
> Updated At: `2026-07-28`

# Task — `F-EXE-03` Student Submission (Làm bài & nộp bài)

**Author:** AI Agent
**Updated By:** AI Agent

## Mô tả Task
Triển khai module làm bài & nộp bài (`StudentExerciseAttempt`) bao gồm:
1. Alembic migration: tạo bảng `student_exercise_attempts` nếu chưa tồn tại (theo `base_sql_erd.sql` §4.2 — Sprint 2 chỉ dùng `start_time`, `end_time`, `total_time_seconds`, `score`, `detailed_results`, `is_finished`; `behavior_logs`/`focus_score` để cột sẵn cho Sprint 3, không xử lý logic).
2. SQLAlchemy model: `StudentExerciseAttempt` trong `models/models.py`.
3. Pydantic validation: `AttemptSubmitRequest` (`answers: list[AnswerInput]`, mỗi item đúng 1 trong `answer_option_id`/`answer_text` theo `question_type`).
4. Repository layer: `AttemptRepository` — tìm attempt đang mở theo `(student_id, assignment_id)`, lấy attempt kèm quyền truy cập.
5. Service layer: `AttemptService` — `start_attempt` (validate ghi danh + chặn trùng attempt mở), `submit_attempt` (gọi `GradingService` từ F-EXE-04, cập nhật `end_time`/`total_time_seconds`/`score`/`is_finished`), `get_attempt` (RBAC: chủ attempt hoặc GV dạy lớp).
6. API Routers: `app/modules/exercise/routers/attempts.py`.
7. Seed permission mới `EXE_ATTEMPT_SUBMIT` (role Student), `EXE_ATTEMPT_VIEW` (role Student/Teacher/Admin).
8. Unit & Integration tests pass 100%.

## Technical Workflow

```
Bước 1: Alembic Migration
  └── alembic revision --autogenerate -m "create student_exercise_attempts table"

Bước 2: SQLAlchemy Model
  └── models/models.py: StudentExerciseAttempt

Bước 3: Pydantic Schemas
  └── app/modules/exercise/schemas.py: AttemptStartOut, AnswerInput, AttemptSubmitRequest, AttemptOut

Bước 4: Repository Layer
  └── app/modules/exercise/repository.py: AttemptRepository (find_open_attempt, get_by_id)

Bước 5: Service Layer & Grading Integration
  └── app/modules/exercise/services/attempt_service.py: start_attempt (student_class check), submit_attempt (gọi grading_service.grade_attempt trong cùng transaction), get_attempt (scoping qua assignment.class_id)

Bước 6: API Router & Dependency Injection
  └── app/modules/exercise/routers/attempts.py: require_perm & get_current_user

Bước 7: Seed Permissions
  └── app/scripts/seed.py: thêm EXE_ATTEMPT_SUBMIT (Student), EXE_ATTEMPT_VIEW (Student/Teacher/Admin)

Bước 8: Automated Testing Verification
  └── pytest tests/exercise/integration/test_attempts.py & test_attempt_service.py -> Pass 100%
```

## Kết quả kiểm thử
- (chưa thực thi — task ở trạng thái `draft`, cập nhật khi triển khai xong)
