# Feature Spec — `F-ACAD-05` Teacher Schedule & Timetable Management

> Path: `docs/v_1/specs/f_acad_05_teacher_schedule_spec.md` · Sprint: [sprint_4_overview.md](../sprints/sprint_4_overview.md)  
> Created At: `2026-09-20`  
> Created By: `Tam Khang`  
> Updated At: `2026-09-23`  
> Updated By: `Tam Khang`  

---

## Document Header

| Field | Giá trị |
|---|---|
| **Feature ID** | `F-ACAD-05` |
| **Feature Name** | Teacher Schedule & Timetable Management — Quản lý Thời khóa biểu và Lịch giảng dạy |
| **Module(s)** | `academic`, `teacher` |
| **Sprint(s) Allocated** | `SPRINT-04` |
| **Spec Version** | `v1.1` |
| **Last Updated** | `2026-09-23` |
| **Source Binding** | `business_overview.md` · `f_acad_02_classes_spec.md` · `f_acad_04_teacher_assignment_spec.md` |

---

# PART A — Business & Requirements

> **Owner:** Tam Khang · **Gate:** G3

## A.1 Feature Summary

Cung cấp công cụ quản lý lịch kiểm tra, khảo thí và ghi chú công việc sư phạm cho Giáo viên:
1. **Lịch kiểm tra trực quan**: Hiển thị các lịch kiểm tra trong tuần/tháng theo lớp, môn học và thời gian bắt đầu/kết thúc.
2. **Phân loại mức độ ưu tiên & khẩn cấp (Urgency Tagging)**: Đánh dấu màu sắc trực quan theo tính chất sự kiện (`critical`, `high`, `teaching`).
3. **Phát hiện trùng lịch (Conflict Detection)**: Tự động phát hiện và chặn trùng giờ kiểm tra của giáo viên.
4. **Ghi chú nhắc nhở sư phạm (Teacher Notes)**: Tạo các ghi chú công việc nhanh (nhắc lớp nộp bài, chuẩn bị đề in sẵn) theo từng ngày.

## A.2 User Stories

| Story ID | As (Role) | I Want (Capability) | So That (Value) |
|---|---|---|---|
| **US-01** | Teacher | Xem lịch kiểm tra hàng tuần và chi tiết từng ngày theo lớp | Chủ động chuẩn bị đề thi và kế hoạch kiểm tra cho các lớp. |
| **US-02** | Teacher | Thêm mới hoặc điều chỉnh lịch kiểm tra và mức độ khẩn cấp | Quản lý tiến độ khảo thí và kiểm tra đánh giá của học sinh. |
| **US-03** | Teacher | Lưu ghi chú công việc gắn với ngày cụ thể và đánh dấu hoàn thành | Không bỏ sót các đầu việc sư phạm quan trọng. |
---

# PART B — Technical Specifications & API Contracts

## B.1 API Endpoints

### 1. `GET /api/v1/teacher/schedules`
* **Permission**: `SCHED_TEACHER_VIEW`
* **Query Params**:
  * `year`: int (mặc định: năm hiện tại, vd: 2026)
  * `month`: int (1..12)
  * `grade`: str (tùy chọn: `10` | `11` | `12` | `all`)
  * `urgency`: str (tùy chọn: `critical` | `high` | `teaching`)
* **Response `200 OK`**:
```json
[
  {
    "id": "2fa85f64-5717-4562-b3fc-2c963f66af10",
    "title": "Toán Đại số - Khảo sát hàm số",
    "class_id": "3ba85f64-5717-4562-b3fc-2c963f66af11",
    "class_name": "10A1",
    "grade": "10",
    "schedule_date": "2026-10-15",
    "start_time": "07:30",
    "end_time": "09:00",
    "urgency": "teaching",
    "notes": "Nhắc lớp nộp bài tập về nhà",
    "status": "ACTIVE"
  }
]
```

### 2. `POST /api/v1/teacher/schedules`
* **Permission**: `SCHED_TEACHER_MANAGE`
* **Request Body**:
```json
{
  "title": "Kiểm tra 15p Hình học",
  "class_id": "3ba85f64-5717-4562-b3fc-2c963f66af11",
  "schedule_date": "2026-10-16",
  "start_time": "08:15",
  "end_time": "09:00",
  "urgency": "critical",
  "notes": "Chuẩn bị đề in sẵn"
}
```
* **Validation**:
  * Nếu trùng giờ kiểm tra của giáo viên -> Lỗi `ERR-SCHED-TIME_CONFLICT` (`409 Conflict`).
* **Response `201 Created`**: Schedule Object.

### 3. `DELETE /api/v1/teacher/schedules/{schedule_id}`
* **Permission**: `SCHED_TEACHER_MANAGE`
* **Response `204 No Content`** (Soft delete: `status = 'DELETED'`).

### 4. `POST /api/v1/teacher/schedules/{schedule_id}/restore`
* **Permission**: `SCHED_TEACHER_MANAGE`
* **Response `200 OK`**: Schedule Object với `status = 'ACTIVE'`.

### 5. `GET /api/v1/teacher/notes` & `POST /api/v1/teacher/notes`
* **Permission**: `SCHED_TEACHER_MANAGE`
* **Request Body (POST)**:
```json
{
  "note_date": "2026-10-15",
  "content": "Gặp phụ huynh em Trần Thị Lan lúc 10h",
  "is_completed": false
}
```
* **Response `201 Created`**: Note Object.
