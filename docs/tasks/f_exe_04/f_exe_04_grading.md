> Path: `docs/tasks/f_exe_04/f_exe_04_grading.md`
> Slice: `SL-EXE-04` · Type: `service` · Size: `small` · SP: `2`
> Depends on: `F-EXE-01`
> Status: `ready to test`
> Created At: `2026-07-28`
> Updated At: `2026-08-08`

# Task — `F-EXE-04` Auto Grading (Chấm điểm tự động trắc nghiệm)

**Author:** Tam Khang
**Updated By:** Tam Khang

## Mô tả Task
Triển khai service chấm điểm tự động (không có router/endpoint riêng — được `F-EXE-03` gọi trực tiếp):
1. `GradingService.grade_attempt(exercise_questions, answers) -> (score, detailed_results)`.
2. Logic: `MultipleChoice` so khớp `answer_option_id` với `answer_options.is_correct`; `ShortAnswer` đánh dấu `pending_manual_grade=true`, không cộng điểm.
3. Trọng số đều nhau: `10 / tổng số câu MultipleChoice` mỗi câu đúng; nếu không có câu `MultipleChoice` nào -> `score = None`.
4. Không trả điểm undefined cho câu học sinh không trả lời — coi là sai (`is_correct=false`).
5. Unit tests đầy đủ 5 AC (§A.4 `f_exe_04_grading_spec.md`), không cần integration test riêng (được cover qua integration test của `F-EXE-03`).

## Technical Workflow

```
Bước 1: Service Implementation
  └── app/modules/exercise/services/grading_service.py: grade_attempt(questions, answer_options_map, answers)

Bước 2: Unit Tests
  └── tests/exercise/unit/test_grading_service.py:
        - test_all_correct_multiplechoice
        - test_one_wrong_multiplechoice
        - test_short_answer_pending_manual_grade
        - test_missing_answer_counts_as_wrong
        - test_all_short_answer_score_is_null

Bước 3: Integration vào F-EXE-03
  └── app/modules/exercise/services/attempt_service.py: gọi grading_service.grade_attempt() trong submit_attempt()
```

## Kết quả kiểm thử
- **Unit Tests:** 5/5 test cases trong `tests/exercise/unit/test_grading_service.py` vượt qua thành công (AC-01 -> AC-05).
- **Integration Tests:** 100% test cases trong `tests/exercise/test_attempts.py` đã passed.

