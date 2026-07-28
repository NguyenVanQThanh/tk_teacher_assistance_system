> Path: `docs/tasks/f_exe_01/f_exe_01_exercises.md`
> Slice: `SL-EXE-01` · Type: `feature` · Size: `large` · SP: `5`
> Depends on: `F-ACAD-04`
> Status: `draft`
> Created At: `2026-07-28`
> Updated At: `2026-07-28`

# Task — `F-EXE-01` Exercise Bank (Đề bài tập, câu hỏi & đáp án)

**Author:** AI Agent
**Updated By:** AI Agent

## Mô tả Task
Triển khai module kho đề bài tập (`Exercise`, `Question`, `AnswerOption`) bao gồm:
1. Alembic migration: thêm cột `status` cho `exercises`; tạo bảng `questions`, `answer_options` nếu chưa tồn tại trong DB thực tế (đối chiếu `models/models.py` hiện tại — chưa có 3 model này, cần bổ sung).
2. SQLAlchemy models: `Exercise`, `Question`, `AnswerOption` trong `models/models.py`.
3. Pydantic validation: `ExerciseCreate/Update`, `QuestionCreate/Update` (strip title, Enum `question_type`/`difficulty`, validate `answer_options` bắt buộc đúng 1 `is_correct=true` khi `MultipleChoice`).
4. Repository layer: `ExerciseRepository`, `QuestionRepository` — optional filter theo `status`/`subject_id`/`created_by`, hàm `restore`.
5. Service layer: `ExerciseService` — kiểm tra `teacher_subjects` scoping khi tạo đề (AS-01 sprint 2), CRUD + soft-delete + restore.
6. API Routers: `app/modules/exercise/routers/exercises.py`, `questions.py` — endpoints theo PART B của `f_exe_01_exercises_spec.md`, bảo vệ bởi `EXE_EXERCISE_MANAGE`/`EXE_EXERCISE_VIEW`.
7. Seed permission mới `EXE_EXERCISE_MANAGE`, `EXE_EXERCISE_VIEW` — map cho role Teacher (cả 2) và Admin (cả 2).
8. Unit & Integration tests pass 100%.

## Technical Workflow

```
Bước 1: Alembic Migration
  └── alembic revision --autogenerate -m "add exercise status and question/answer tables"

Bước 2: SQLAlchemy Models
  └── models/models.py: Exercise, Question, AnswerOption

Bước 3: Pydantic Schemas
  └── app/modules/exercise/schemas.py: ExerciseCreate/Update/Out, QuestionCreate/Update/Out, AnswerOptionCreate/Out

Bước 4: Repository Layer
  └── app/modules/exercise/repository.py: ExerciseRepository, QuestionRepository (filter Optional, restore)

Bước 5: Service Layer & Scoping
  └── app/modules/exercise/services/exercise_service.py: create (check teacher_subjects), list/detail (scoping), update, delete, restore
  └── app/modules/exercise/services/question_service.py: add_question (validate answer_options), update, delete

Bước 6: API Router & Dependency Injection
  └── app/modules/exercise/routers/exercises.py, questions.py: require_perm & get_current_user

Bước 7: Seed Permissions
  └── app/scripts/seed.py: thêm EXE_EXERCISE_MANAGE/VIEW, map role Teacher + Admin

Bước 8: Automated Testing Verification
  └── pytest tests/exercise/integration/test_exercises.py & test_exercise_service.py -> Pass 100%
```

## Kết quả kiểm thử
- (chưa thực thi — task ở trạng thái `draft`, cập nhật khi triển khai xong)
