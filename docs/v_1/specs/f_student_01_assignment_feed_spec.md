# Feature Spec — `F-STUDENT-01` Student Unified Assignment Feed (Cổng Bài tập Học sinh)

> Path: `docs/v_1/specs/f_student_01_assignment_feed_spec.md` · Sprint: [sprint_3_overview.md](../sprints/sprint_3_overview.md)  
> Created At: `2026-09-23`  
> Created By: `Tam Khang`  
> Updated At: `2026-09-23`  
> Updated By: `Tam Khang`  

---

## Document Header

| Field | Giá trị |
|---|---|
| **Feature ID** | `F-STUDENT-01` |
| **Feature Name** | Student Unified Assignment Feed — Cổng Tra cứu Danh sách Bài tập Tập trung |
| **Module(s)** | `exercise`, `academic` |
| **Sprint(s) Allocated** | `SPRINT-03` |
| **Spec Version** | `v1.0` |
| **Last Updated** | `2026-09-23` |
| **Source Binding** | `models/models.py` (`student_class`, `class_assignments`, `student_exercise_attempts`, `exercises`) · `f_exe_02_assignments_spec.md` · `f_exe_03_submission_spec.md` |

---

# PART A — Business & Requirements

> **Owner:** Tam Khang · **Gate:** G3

## A.1 Feature Summary

Cung cấp API hiệu năng cao cho **Học sinh (Student)** tra cứu toàn bộ danh sách bài tập đã được giao từ tất cả các lớp mà học sinh đang theo học:
* Tự động tổng hợp thông tin: Môn học, tên bài tập, loại bài tập (Kiểm tra 15p, 1 tiết, Bài tập về nhà), giáo viên giao, hạn nộp (`due_at`), thời lượng làm bài (`duration_minutes`).
* Tính toán trạng thái làm bài theo thời gian thực của học sinh:
  * `NOT_STARTED`: Chưa làm bài.
  * `IN_PROGRESS`: Đang có một lượt làm bài mở (chưa nộp).
  * `SUBMITTED`: Đã nộp bài và đang chờ duyệt/chấm điểm.
  * `GRADED`: Đã có điểm số chính thức.
  * `OVERDUE`: Đã quá hạn nộp và chưa hoàn thành.
* Cung cấp số lần đã làm (`attempts_count`) và điểm số cao nhất (`highest_score`).

## A.2 User Stories

| Story ID | As (Role) | I Want (Capability) | So That (Value) |
|---|---|---|---|
| **US-01** | Student | Xem tất cả bài tập cần làm từ tất cả các môn trong một màn hình duy nhất | Không bị bỏ sót bài tập hoặc hạn nộp |
| **US-02** | Student | Lọc bài tập theo môn học hoặc theo trạng thái (Cần làm / Đã nộp / Quá hạn) | Tập trung ưu tiên làm các bài tập gấp |
| **US-03** | Student | Xem điểm số cao nhất và số lần đã thử sức với bài tập | Đánh giá tiến độ học tập của bản thân |

---

# PART B — Technical Specifications & API Contracts

## B.1 API Endpoints

### 1. `GET /api/v1/student/assignments`
* **Permission**: `STUDENT_ASSIGNMENT_VIEW` & User Role `Student`
* **Query Params**:
  * `status`: `all` | `pending` | `in_progress` | `submitted` | `graded` | `overdue` (mặc định: `all`)
  * `subject_id`: UUID (lọc theo môn học cụ thể)
  * `page`: int (mặc định: 1)
  * `page_size`: int (mặc định: 10)
* **Response `200 OK`**:
```json
{
  "items": [
    {
      "assignment_id": "8fa85f64-5717-4562-b3fc-2c963f66afb1",
      "exercise_id": "7ca85f64-5717-4562-b3fc-2c963f66afa2",
      "exercise_title": "Kiểm tra 15p - Đạo hàm & Khảo sát hàm số",
      "exercise_type": "classroom",
      "subject_id": "4da85f64-5717-4562-b3fc-2c963f66af01",
      "subject_name": "Toán Học",
      "class_id": "2ba85f64-5717-4562-b3fc-2c963f66af11",
      "class_name": "10A1",
      "teacher_name": "Thầy Nguyễn Văn A",
      "assigned_at": "2026-09-20T08:00:00Z",
      "due_at": "2026-09-25T23:59:59Z",
      "duration_minutes": 15,
      "total_questions": 12,
      "submission_status": "NOT_STARTED",
      "is_overdue": false,
      "attempts_count": 0,
      "highest_score": null,
      "latest_attempt_id": null
    }
  ],
  "total": 6,
  "page": 1,
  "page_size": 10,
  "total_pages": 1
}
```
