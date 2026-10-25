# Feature Spec — `F-DASH-01` Teacher Analytics Dashboard

> Path: `docs/v_1/specs/f_dash_01_teacher_dashboard_spec.md` · Sprint: SPRINT-04
> Created At: `2026-09-20`
> Created By: `Tam Khang`
> Updated At: `2026-09-20`
> Updated By: `Tam Khang`

---

## Document Header

| Field | Giá trị |
|---|---|
| Feature ID | `F-DASH-01` |
| Feature name | Teacher Analytics Dashboard — Bảng điều khiển phân tích sư phạm cho Giáo viên bộ môn và Giáo viên chủ nhiệm |
| Module(s) | `analytics`, `teacher` |
| Sprint(s) allocated | `SPRINT-04` |
| Lane | `standard` |
| Spec version | `v1.0` |
| Last updated | `2026-09-20` |
| Source binding | `business_overview.md` · `f_exe_04_grading_spec.md` · `f_acad_02_classes_spec.md` |

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

Cung cấp hai góc nhìn phân tích chuyên biệt cho Giáo viên:
1. **Giáo viên Bộ môn (`SubjectTeacherDashboard`)**: Phổ điểm theo từng bài tập, biểu đồ mạng nhện đánh giá năng lực các lớp phụ trách, danh sách câu hỏi có tỷ lệ làm sai cao nhất, và danh sách bài tập đang chờ chấm.
2. **Giáo viên Chủ nhiệm (`HomeroomTeacherDashboard`)**: Thống kê sĩ số lớp chủ nhiệm, theo dõi tỷ lệ chuyên cần, biến động học lực tổng thể các môn, và danh sách học sinh có nguy cơ sa sút hoặc có dấu hiệu nộp bài sát giờ (last-minute submission).

---

## A.2 User Stories

| Story ID | As (role) | I want (capability) | So that (value) |
|---|---|---|---|
| **US-01** | Giáo viên Bộ môn | Xem phổ điểm và câu hỏi hay làm sai của lớp | Điều chỉnh nội dung giảng dạy và giải thích kỹ phần kiến thức học sinh còn yếu. |
| **US-02** | Giáo viên Chủ nhiệm | Xem báo cáo tổng quan học lực và danh sách học sinh nộp bài sát giờ | Kịp thời phối hợp với phụ huynh và học sinh để đôn đốc việc học tập. |
| **US-03** | Giáo viên | Nhận thông báo số lượng bài nộp mới cần chấm | Tối ưu hóa thời gian xử lý bài tập và chấm điểm kịp thời. |

---

## A.3 REQ Registry

| REQ ID | Mô tả ngắn | Priority | Status | Linked Story |
|---|---|---|---|---|
| **REQ-DASH-01** | Thống kê số lượng bài chờ chấm theo lớp và môn học | P0 | Active | US-01, US-03 |
| **REQ-DASH-02** | Phân tích phổ điểm (dưới 5, 5-6.5, 6.5-8, 8-10) theo bài tập | P0 | Active | US-01 |
| **REQ-DASH-03** | Tính toán biểu đồ mạng nhện năng lực lớp học theo 6 mức độ | P1 | Active | US-01 |
| **REQ-DASH-04** | Nhận diện và cảnh báo học sinh nộp bài sát giờ (dưới 15% thời gian còn lại) | P1 | Active | US-02 |
| **REQ-DASH-05** | Tổng hợp sĩ số và thông tin chuyên cần lớp chủ nhiệm | P1 | Active | US-02 |
