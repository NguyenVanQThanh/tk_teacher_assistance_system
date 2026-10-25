> Path: `docs/tasks/f_exe_03/f_exe_03_submission.md`
> Slice: `SL-EXE-03` · Type: `feature` · Size: `large` · SP: `5`
> Depends on: `F-EXE-02`, `F-EXE-04`
> Status: `ready to test`
> Created At: `2026-07-28`
> Updated At: `2026-08-05`

# Task — `F-EXE-03` Student Submission (Làm bài & nộp bài)

**Author:** Tam Khang
**Updated By:** Tam Khang

## Mô tả Task
Triển khai module làm bài & nộp bài (`StudentExerciseAttempt`) bao gồm:
1. Alembic migration: tạo bảng `student_exercise_attempts` (`alembic/versions/5a3b2c4d5e6f_create_student_exercise_attempts_table.py`).
2. SQLAlchemy model: `StudentExerciseAttempt` trong `models/models.py` (hỗ trợ cột `status` cho soft-delete).
3. Pydantic validation: `AttemptStartOut`, `AnswerInput`, `AttemptSubmitRequest`, `AttemptOut` trong `app/modules/exercise/schemas.py`.
4. Repository layer: `AttemptRepository` trong `app/modules/exercise/repository.py` — hỗ trợ `find_open_attempt`, `create`, `get_by_id`, `update`.
5. Service layer: `AttemptService` trong `app/modules/exercise/services/attempt_service.py` — `start_attempt` (validate ghi danh + chặn trùng attempt mở), `submit_attempt` (gọi `GradingService` từ F-EXE-04, cập nhật `end_time`/`total_time_seconds`/`score`/`is_finished`), `get_attempt` (RBAC: chủ attempt hoặc GV dạy lớp).
6. Auto-Grading Engine: `GradingService` trong `app/modules/exercise/services/grading_service.py` — tự động chấm câu `MultipleChoice` (thang điểm 10) và lưu `pending_manual_grade` cho `ShortAnswer`.
7. API Routers: `app/modules/exercise/routers/attempts.py` với Dependency Injection `get_attempt_service`.
8. Seed permission mới `EXE_ATTEMPT_SUBMIT` (role Student), `EXE_ATTEMPT_VIEW` (role Student/Teacher/Admin).
9. Unit & Integration tests pass 100%.

## Technical Workflow

```
Bước 1: Alembic Migration
  └── alembic/versions/5a3b2c4d5e6f_create_student_exercise_attempts_table.py

Bước 2: SQLAlchemy Model
  └── models/models.py: StudentExerciseAttempt (với status VARCHAR(20) DEFAULT 'ACTIVE')

Bước 3: Pydantic Schemas
  └── app/modules/exercise/schemas.py: AttemptStartOut, AnswerInput, AttemptSubmitRequest, AttemptOut

Bước 4: Repository Layer
  └── app/modules/exercise/repository.py: AttemptRepository (find_open_attempt, get_by_id, create, update)

Bước 5: Service Layer & Grading Integration
  └── app/modules/exercise/services/grading_service.py (Auto-grading Engine)
  └── app/modules/exercise/services/attempt_service.py: start_attempt (student_class check), submit_attempt (gọi grading_service.grade_attempt), get_attempt (scoping)

Bước 6: API Router & Dependency Injection
  └── app/modules/exercise/routers/attempts.py: require_perm & get_current_user, get_attempt_service DI provider

Bước 7: Seed Permissions
  └── app/scripts/seed.py: thêm EXE_ATTEMPT_SUBMIT (Student), EXE_ATTEMPT_VIEW (Student/Teacher/Admin)

Bước 8: Automated Testing Verification
  └── pytest tests/exercise/test_attempts.py -> Pass 100%
```

## Kết quả kiểm thử
- `pytest tests/exercise/test_attempts.py -v` -> PASSED 100% (Full attempt lifecycle, scoping & auto-grading).
- `pytest tests/exercise/ -v` -> PASSED 100% (5/5 tests passed).
- `pytest tests/ -v` -> PASSED 100% (120/120 tests passed across all system modules).

