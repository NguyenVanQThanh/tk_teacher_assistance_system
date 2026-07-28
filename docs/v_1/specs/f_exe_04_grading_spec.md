# Feature Spec — `F-EXE-04` Auto Grading (Chấm điểm tự động trắc nghiệm)

> Path: `docs/v_1/specs/f_exe_04_grading_spec.md` · Sprint: [sprint_2_overview.md](../sprints/sprint_2_overview.md)
> Created At: `2026-07-28`
> Created By: `AI Agent`
> Updated At: `2026-07-28`
> Updated By: `AI Agent`

---

## Document Header

| Field | Giá trị |
|---|---|
| Feature ID | `F-EXE-04` |
| Feature name | Auto Grading — Chấm điểm tự động câu trắc nghiệm |
| Module(s) | `exercise` |
| Sprint(s) allocated | `SPRINT-02` |
| Lane | `standard` |
| Spec version | `v1.0` |
| Last updated | `2026-07-28` |
| Source binding | `docs/base_sql_erd.sql` (`student_exercise_attempts.score`, `detailed_results`) · `f_exe_03_submission_spec.md` (gọi grading khi submit) · `f_exe_01_exercises_spec.md` (`questions`, `answer_options`) · `.claude/rules/coding_rules.md` |

---

# PART A — Business

> **Owner:** AI Agent · **Gate:** G3

## A.1 Feature Summary

Không phải là feature độc lập có endpoint riêng — là **service nội bộ** (`GradingService`) được `F-EXE-03` gọi tại thời điểm nộp bài. Chấm điểm tự động cho câu `MultipleChoice` bằng so khớp `answer_option_id` học sinh chọn với `answer_options.is_correct = true`. Câu `ShortAnswer` không tự chấm — đánh dấu `pending_manual_grade: true` trong `detailed_results`, không tính vào điểm.

## A.2 User Stories

| Story ID | As (role) | I want (capability) | So that (value) |
|---|---|---|---|
| US-01 | Student | nhận điểm ngay khi nộp bài trắc nghiệm | biết kết quả tức thì, không chờ GV chấm |
| US-02 | Teacher | xem điểm và câu đúng/sai của học sinh | đánh giá năng lực nhanh |

## A.3 Business Workflow (Chấm điểm)

```
[GradingService.grade_attempt(attempt, answers)]
       │
       ▼
 1. Lấy toàn bộ questions của exercise (qua assignment.exercise_id)
       │
       ▼
 2. Với mỗi question:
    ├── question_type = MultipleChoice:
    │     ├── Tìm answer_option_id học sinh chọn trong answers
    │     ├── So khớp answer_options.is_correct -> is_correct_answer = true/false
    │     └── Cộng vào tổng điểm nếu đúng (trọng số đều nhau: 10 / tổng số câu MultipleChoice)
    └── question_type = ShortAnswer:
          └── Ghi answer_text vào detailed_results, đánh dấu pending_manual_grade=true, không cộng điểm
       │
       ▼
 3. score = round(tổng điểm đạt được, 2) — thang điểm 10 (NUMERIC(5,2) theo schema)
       │
       ▼
 4. detailed_results (JSONB) = {
      "questions": [
        {"question_id": ..., "question_type": ..., "student_answer": ..., "is_correct": true/false/null, "pending_manual_grade": false/true}
      ]
    }
       │
       ▼
 5. Trả (score, detailed_results) cho F-EXE-03 lưu vào student_exercise_attempts
```

## A.4 Acceptance Criteria

| AC ID | REQ | Given | When | Then |
|---|---|---|---|---|
| AC-01 | REQ-EXE-031 | Đề toàn câu `MultipleChoice`, HS chọn đúng hết | Submit attempt | `score = 10.00`, mọi câu `is_correct=true` |
| AC-02 | REQ-EXE-031 | Đề toàn câu `MultipleChoice`, HS chọn sai 1 câu (đề 5 câu) | Submit attempt | `score = 8.00`, câu sai `is_correct=false` |
| AC-03 | REQ-EXE-032 | Đề có câu `ShortAnswer` | Submit attempt | câu đó `is_correct=null`, `pending_manual_grade=true`, không cộng vào `score` |
| AC-04 | REQ-EXE-031 | Học sinh không trả lời 1 câu (thiếu trong answers) | Submit attempt | Câu đó tính là sai (`is_correct=false`), không lỗi 4xx |
| AC-05 | REQ-EXE-033 | Đề chỉ toàn câu `ShortAnswer` (không có câu nào chấm được tự động) | Submit attempt | `score = null`, tất cả `pending_manual_grade=true` — chờ GV chấm tay ở sprint sau |

## A.5 Out of Scope

- Chấm tự luận bằng AI/NLP so khớp ngữ nghĩa — Sprint 4/5.
- Giao diện GV chấm tay câu tự luận — chưa có endpoint, chỉ lưu dữ liệu `pending_manual_grade` làm nền.
- Trọng số điểm khác nhau theo độ khó (`difficulty`) — Sprint 2 dùng trọng số đều; nếu nghiệp vụ cần trọng số theo `NhanBiet/ThongHieu/VanDung`, bổ sung ở spec version sau (đánh dấu `TODO` trong code, không tự ý thêm ở sprint này).

---

# PART B — Architecture

> **Owner:** AI Agent · **Gate:** G4

### Vị trí trong kiến trúc

`GradingService` đặt tại `app/modules/exercise/services/grading_service.py`, được `AttemptService.submit()` (F-EXE-03) gọi trong cùng transaction DB khi nộp bài — không có router/endpoint riêng.

### Database Boundary

| Table | Op |
|---|---|
| `student_exercise_attempts` | UPDATE (`score`, `detailed_results`, `is_finished`, `end_time`, `total_time_seconds`) |
| `questions`, `answer_options` | READ only |
