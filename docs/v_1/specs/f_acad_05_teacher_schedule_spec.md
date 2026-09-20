# Feature Spec — `F-ACAD-05` Teacher Schedule & Timetable Management

> Path: `docs/v_1/specs/f_acad_05_teacher_schedule_spec.md` · Sprint: SPRINT-04
> Created At: `2026-09-20`
> Created By: `Tam Khang`
> Updated At: `2026-09-20`
> Updated By: `Tam Khang`

---

## Document Header

| Field | Giá trị |
|---|---|
| Feature ID | `F-ACAD-05` |
| Feature name | Teacher Schedule & Timetable Management — Quản lý Thời khóa biểu và Lịch giảng dạy của Giáo viên |
| Module(s) | `academic`, `teacher` |
| Sprint(s) allocated | `SPRINT-04` |
| Lane | `standard` |
| Spec version | `v1.0` |
| Last updated | `2026-09-20` |
| Source binding | `business_overview.md` · `f_acad_02_classes_spec.md` · `f_acad_04_teacher_assignment_spec.md` |

### Gate status

| Gate | Bao trùm | Owner | Approver | Status | Date |
|---|---|---|---|---|---|
| G3 Business | PART A | Tam Khang | Tam Khang | `approved` | 2026-09-20 |
| G4 Architecture | PART B | Tam Khang | Tam Khang | `approved` | 2026-09-20 |
| G6 Design | PART C | Tam Khang | Tam Khang | `approved` | 2026-09-20 |
| G6.5 Coding | PART D | Tam Khang | Tam Khang | `ready` | 2026-09-20 |
| G7+ Tracking | PART E | Tam Khang | Tam Khang | `live` | 2026-09-20 |

---

# PART A — Business

> **Owner:** Tam Khang · **Gate:** G3

## A.1 Feature Summary

Cung cấp công cụ quản lý lịch giảng dạy, thời khóa biểu và ghi chú công việc sư phạm cho Giáo viên:
1. **Thời khóa biểu trực quan**: Hiển thị các tiết dạy trong tuần/tháng theo lớp, phòng học, môn học và thời gian bắt đầu/kết thúc.
2. **Phân loại mức độ ưu tiên & khẩn cấp (Urgency Tagging)**: Đánh dấu màu sắc trực quan theo tính chất sự kiện (Khẩn cấp / Kiểm tra, Tiết giảng dạy chuẩn, Sự kiện AI, Họp chuyên môn).
3. **Ghi chú nhắc nhở học sinh (Teacher Notes)**: Tạo các ghi chú công việc nhanh (nhắc lớp nộp bài, chuẩn bị đề kiểm tra) theo từng ngày.

---

## A.2 User Stories

| Story ID | As (role) | I want (capability) | So that (value) |
|---|---|---|---|
| **US-01** | Giáo viên (Teacher) | Xem lịch dạy hàng tuần và chi tiết từng ngày | Chủ động sắp xếp giáo án và lịch lên lớp. |
| **US-02** | Giáo viên (Teacher) | Thêm lịch dạy bổ sung hoặc lịch kiểm tra định kỳ | Theo dõi tiến độ giảng dạy của các lớp phụ trách. |
| **US-03** | Giáo viên (Teacher) | Lưu ghi chú công việc gắn với ngày cụ thể | Không bỏ sót các đầu việc quan trọng như nhắc học sinh nộp bài hoặc chuẩn bị thiết bị thí nghiệm. |

---

## A.3 REQ Registry

| REQ ID | Mô tả ngắn | Priority | Status | Linked Story |
|---|---|---|---|---|
| **REQ-SCHED-01** | Hiển thị lịch dạy theo lưới tuần/tháng có phân loại màu | P0 | Active | US-01 |
| **REQ-SCHED-02** | Xem chi tiết tiết dạy (Môn, Lớp, Phòng học, Thời gian) | P0 | Active | US-01 |
| **REQ-SCHED-03** | Thêm mới lịch dạy / tiết phụ đạo | P1 | Active | US-02 |
| **REQ-SCHED-04** | CRUD danh sách ghi chú công việc theo ngày | P1 | Active | US-03 |
