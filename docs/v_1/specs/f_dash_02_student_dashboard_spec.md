# Feature Spec — `F-DASH-02` Student Self-Evaluation Dashboard & AI Practice

> Path: `docs/v_1/specs/f_dash_02_student_dashboard_spec.md` · Sprint: SPRINT-04
> Created At: `2026-09-20`
> Created By: `Tam Khang`
> Updated At: `2026-09-20`
> Updated By: `Tam Khang`

---

## Document Header

| Field | Giá trị |
|---|---|
| Feature ID | `F-DASH-02` |
| Feature name | Student Self-Evaluation Dashboard & AI Practice — Bảng điều khiển tự đánh giá năng lực học sinh và Sinh bài tập luyện tập bằng AI |
| Module(s) | `student`, `analytics`, `ai` |
| Sprint(s) allocated | `SPRINT-04` |
| Lane | `standard` |
| Spec version | `v1.0` |
| Last updated | `2026-09-20` |
| Source binding | `business_overview.md` · `f_exe_03_submission_spec.md` · `f_exe_06_gemini_vision_ocr_spec.md` |

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

Cung cấp công cụ trực quan hóa tiến độ và năng lực tự học cho Học sinh:
1. **Biểu đồ Radar đa chiều**: Đánh giá năng lực nhận thức qua 6 bậc (Nhớ, Hiểu, Vận dụng, Phân tích, Đánh giá, Sáng tạo) theo từng môn học.
2. **Nhận xét năng lực học tập**: Hệ thống đưa ra các nhận xét tự động về năng lực học tập, điểm mạnh và điểm cần cải thiện của học sinh (hệ thống chỉ đưa ra nhận xét, đánh giá năng lực học tập, không thể gợi ý lộ trình học chi tiết).
3. **AI Practice Generator**: Tích hợp module AI cho phép học sinh tự tạo đề luyện tập ngắn theo chủ đề và độ khó mong muốn để tự củng cố kiến thức.

---

## A.2 User Stories

| Story ID | As (role) | I want (capability) | So that (value) |
|---|---|---|---|
| **US-01** | Học sinh (Student) | Xem biểu đồ mạng nhện năng lực học tập theo từng môn | Tự nhận biết vùng kiến thức mình đang đạt điểm cao hoặc còn yếu. |
| **US-02** | Học sinh (Student) | Đọc nhận xét về năng lực học tập từ hệ thống và giáo viên | Nắm bắt định hướng cải thiện kết quả học tập. |
| **US-03** | Học sinh (Student) | Sử dụng công cụ AI sinh bài tập tự luyện | Chủ động củng cố các dạng bài còn yếu ngay tại nhà. |

---

## A.3 REQ Registry

| REQ ID | Mô tả ngắn | Priority | Status | Linked Story |
|---|---|---|---|---|
| **REQ-STUDASH-01** | Tổng hợp điểm trung bình và tỷ lệ hoàn thành bài tập theo môn | P0 | Active | US-01 |
| **REQ-STUDASH-02** | Trực quan hóa biểu đồ mạng nhện 6 kỹ năng nhận thức | P1 | Active | US-01 |
| **REQ-STUDASH-03** | Hiển thị nhận xét đánh giá năng lực học tập | P1 | Active | US-02 |
| **REQ-STUDASH-04** | AI sinh câu hỏi tự luyện tập cá nhân hóa theo chủ đề | P2 | Active | US-03 |
