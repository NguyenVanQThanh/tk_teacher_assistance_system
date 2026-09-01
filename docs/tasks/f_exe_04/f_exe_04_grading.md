> Path: `docs/tasks/f_exe_04/f_exe_04_grading.md`
> Slice: `SL-EXE-04` · Type: `service` · Size: `small` · SP: `2`
> Depends on: `F-EXE-01`
> Status: `ready to test`
> Created At: `2026-07-28`
> Updated At: `2026-09-01`

# Task — `F-EXE-04` Auto Grading, Teacher Review & Batch Cascade Regrading

**Author:** Tam Khang
**Updated By:** Tam Khang

## Mô tả Task
Triển khai service chấm điểm tự động, quy trình vòng đời duyệt điểm và cơ chế chấm lại hàng loạt khi sửa đáp án gốc (Grading & Batch Cascade Regrading Engine):
1. `GradingService.grade_attempt(exercise_questions, answers) -> (score, detailed_results)`.
2. **Quy chuẩn 3 trạng thái chấm bài (Workflow Statuses):**
   - **Chờ chấm (`pending_grading`):** Áp dụng cho các bài tập/câu hỏi chưa có đáp án tự động (bài tự luận/trên lớp cần GV chấm tay). Sau khi giáo viên chấm xong sẽ chuyển sang **Đã duyệt**.
   - **Chờ duyệt (`pending_review`):** Áp dụng cho các bài tập đã được hệ thống/AI chấm tự động, chờ giáo viên kiểm tra và duyệt kết quả để chuyển sang **Đã duyệt**.
   - **Đã duyệt (`approved`):** Giáo viên đã thông qua, chốt kết quả và điểm số cuối cùng.
3. **Quyền ghi đè của giáo viên & Chấm lại hàng loạt (Batch Regrading Mechanism):**
   - Giáo viên có toàn quyền chỉnh sửa kết quả từng câu (Đúng / Sai) và điều chỉnh điểm số trong cả 2 trạng thái **Chờ chấm** và **Chờ duyệt**.
   - **Đồng bộ Database & Chấm lại hàng loạt:** Khi giáo viên cập nhật lại đáp án chuẩn của một câu hỏi đã được hệ thống chấm trước đó:
     - Hệ thống cập nhật trường `is_correct` của bảng `answer_options` / `questions` trên Database.
     - Kích hoạt quy trình chấm lại tự động (`GradingService.regrade_exercise(exercise_id)`): Quét toàn bộ các bài làm (`attempts`) của học sinh thuộc đề thi này và tính toán lại điểm số, chi tiết từng câu và bảng thống kê kết quả.
4. Logic: `MultipleChoice` so khớp `answer_option_id` với `answer_options.is_correct`; `ShortAnswer` đánh dấu `pending_manual_grade=true`, không cộng điểm tự động nếu chưa có đáp án chuẩn.
5. Trọng số: `0.25đ` cho trắc nghiệm 4 lựa chọn & đúng/sai, `0.4đ` cho câu trả lời ngắn.

## Technical Workflow

```
Bước 1: Service Implementation & Batch Regrading Engine
  └── app/modules/exercise/services/grading_service.py: 
        - grade_attempt(questions, answer_options_map, answers)
        - update_answer_key_and_cascade_regrade(exercise_id, question_id, new_correct_option_id)

Bước 2: Unit Tests
  └── tests/exercise/unit/test_grading_service.py:
        - test_all_correct_multiplechoice
        - test_one_wrong_multiplechoice
        - test_short_answer_pending_manual_grade
        - test_missing_answer_counts_as_wrong
        - test_all_short_answer_score_is_null
        - test_cascade_regrade_on_answer_key_update

Bước 3: Integration vào F-EXE-03 & Teacher Grading Page
  └── app/modules/exercise/services/attempt_service.py: gọi grading_service.grade_attempt() trong submit_attempt()
  └── frontend/src/pages/teacher/TeacherGradingPage.jsx: 3 summary metric cards (Status Guide, Chờ chấm, Chờ duyệt), Teacher Override & Cascade Batch Regrade
```

## Kết quả kiểm thử
- **Unit Tests:** 5/5 test cases trong `tests/exercise/unit/test_grading_service.py` vượt qua thành công (AC-01 -> AC-05).
- **Integration Tests:** 100% test cases trong `tests/exercise/test_attempts.py` đã passed.



