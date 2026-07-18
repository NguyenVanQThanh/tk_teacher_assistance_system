File Name: business_overview.md
Description: Tong hop nghiep vu (business) tu SRS v1.0 va anh xa theo tung sprint trien khai
Created At: 2026-07-18
Created By: AI Agent
Updated At: 2026-07-18
Updated By: AI Agent

# Tổng quan nghiệp vụ — SmartLMS

> Nguồn: `docs/HỆ THỐNG QUẢN LÍ BÀI TẬP KẾT HỢP PHÂN TÍCH HÀNH VI.pdf` (SRS v1.0, BA soạn 17/06/2026).
> Mục đích tài liệu: tổng hợp toàn bộ business requirement trong SRS và ánh xạ (map) từng yêu cầu vào đúng sprint triển khai, để đối chiếu ngược khi viết feature spec hoặc audit phạm vi.

---

## 1. Bối cảnh & vấn đề nghiệp vụ (từ SRS §1.1)

| # | Vấn đề hiện tại | Hệ quả |
|---|---|---|
| 1 | GV không kiểm soát được tần suất học thực tế của HS ở nhà | Chỉ thấy bài nộp cuối cùng, không biết HS học trong bao lâu, có dồn sát giờ không |
| 2 | Thiếu công cụ trực quan hóa năng lực | GV & HS không có biểu đồ/đa chiều để đánh giá điểm mạnh — yếu — tiến độ |
| 3 | Áp lực biên soạn bài tập cá nhân hóa | Tạo bộ đề đa dạng, bám sát bài giảng tốn nhiều thời gian công sức GV |

## 2. Mục tiêu chiến lược (SRS §1.3)

1. Đo lường chi tiết hành vi học tập (thời gian, tần suất).
2. Trực quan hóa năng lực lớp học (báo cáo, biểu đồ).
3. Thúc đẩy năng lực tự học của học sinh (dữ liệu tự đánh giá + lộ trình riêng).
4. Tối ưu hóa nguồn lực biên soạn (AI tạo sinh bài tập từ tài liệu GV).

---

## 3. Phạm vi chức năng — 4 phân hệ nghiệp vụ (SRS §2)

### 3.1. Module 1 — Tracking (Quản lý & theo dõi hành vi làm bài)
- **Chức năng**: ghi vết thời gian làm bài (bắt đầu/tạm dừng/nộp), giám sát tần suất trực tuyến, cảnh báo tiến độ nộp bài.
- **Luồng nghiệp vụ**: hệ thống tự động ghi thời điểm bắt đầu/tạm dừng/nộp; đo tổng thời gian HS thực sự tương tác với giao diện câu hỏi.
- **Đầu ra**: chỉ số thời gian làm bài trung bình, biểu đồ tần suất truy cập theo giờ/ngày của từng HS.
- **Vai trò chính**: Giáo viên (người tiêu thụ dữ liệu), Học sinh (nguồn phát sinh sự kiện).

### 3.2. Module 2 — AI Generation (Tạo sinh bài tập bằng AI)
- **Chức năng**: tải lên tài liệu kiến thức nền tảng, cấu hình tiêu chí bài tập, phê duyệt/biên tập câu hỏi AI tạo ra.
- **Luồng nghiệp vụ**:
  1. GV tải lên tài liệu (PDF, Word, giáo án, hoặc nhập text).
  2. Chọn cấu hình: số lượng câu hỏi, dạng bài (trắc nghiệm / tự luận ngắn), độ khó (Nhận biết / Thông hiểu / Vận dụng).
  3. AI phân tích tài liệu và sinh bộ bài tập mẫu.
  4. GV chỉnh sửa/duyệt trước khi giao bài.
- **Đầu ra**: bộ bài tập hoàn chỉnh lưu vào kho học liệu.
- **Ràng buộc phi chức năng**: AI phải trả kết quả ≤ 15–30 giây với tài liệu dưới 20 trang.

### 3.3. Module 3 — Teacher Dashboard (Dashboard phân tích cho giáo viên)
- **Chức năng**: thống kê năng lực tổng quan của lớp, phân tích chi tiết hành vi cá nhân, báo cáo phổ điểm & dạng bài hay sai.
- **Luồng nghiệp vụ**:
  - Biểu đồ cột/đường phổ điểm lớp học.
  - Danh sách HS có dấu hiệu sa sút tần suất làm bài hoặc nộp sát giờ (last-minute submission).
  - Khuyến nghị sư phạm dựa trên vùng kiến thức lớp đang hổng.
- **Đầu ra**: báo cáo trực quan hóa năng lực định kỳ (xuất PDF/Excel).
- **Ràng buộc phi chức năng**: dashboard tải < 3 giây với dữ liệu 1 lớp (~50 HS).

### 3.4. Module 4 — Student Dashboard (Dashboard tự đánh giá cho học sinh)
- **Chức năng**: xem số liệu học tập cá nhân theo môn, theo dõi tiến độ hoàn thành mục tiêu, gợi ý lộ trình học tập riêng.
- **Luồng nghiệp vụ**:
  - HS theo dõi tổng số bài đã làm, tỷ lệ chính xác, thời gian phân bổ theo môn.
  - Hệ thống gợi ý vùng kiến thức cần bổ sung dựa trên dữ liệu phân tích năng lực.
  - HS thiết lập mục tiêu điểm số → hệ thống điều hướng bài tập ôn luyện.
- **Đầu ra**: biểu đồ Radar (mạng nhện) thể hiện năng lực đa môn + gợi ý lộ trình học.

## 4. Yêu cầu phi chức năng (SRS §3)

| Nhóm | Yêu cầu |
|---|---|
| Bảo mật (Security) | Mã hóa toàn bộ dữ liệu cá nhân & kết quả học tập. RBAC nghiêm ngặt: HS không xem được dữ liệu hành vi của HS khác; GV chỉ quản lý HS thuộc lớp mình phụ trách. |
| Hiệu năng (Performance) | AI tạo bài ≤ 15–30s (tài liệu < 20 trang). Dashboard tải < 3s (lớp ~50 HS). |
| UX/UI | Dashboard tối giản, trực quan (biểu đồ cột/tròn/radar), responsive (desktop + mobile). |

---

## 5. Ánh xạ Business → Sprint

Đối chiếu 4 phân hệ SRS với lộ trình sprint hiện tại trong [README.md](../../README.md#7-lộ-trình-sprint). Sprint 0/1/2 là hạ tầng kỹ thuật & nghiệp vụ nền (không có trong 4 module SRS gốc nhưng là điều kiện tiên quyết); Sprint 3–6 ánh xạ trực tiếp 1-1 với 4 module SRS.

| Sprint | Tên | Nguồn gốc | Nghiệp vụ SRS liên quan | Trạng thái |
|---|---|---|---|---|
| **S0** | Foundation & Auth | Hạ tầng kỹ thuật (không thuộc 4 module SRS) | NFR Bảo mật/RBAC (§3) — tiền đề phân quyền cho toàn bộ 4 module | ✅ Hoàn thành |
| **S1** | Academic Org (môn học, lớp, ghi danh, phân công GV) | Hạ tầng nghiệp vụ (không thuộc 4 module SRS) | Điều kiện tiên quyết cho "GV chỉ quản lý HS thuộc lớp mình phụ trách" (§3 Security) | Chưa bắt đầu |
| **S2** | Bài tập lõi (câu hỏi, giao bài, làm & chấm điểm) | Hạ tầng dữ liệu cho Module 1 & 2 | Nền dữ liệu `exercises`/`questions`/`student_exercise_attempts` — điều kiện để Tracking (M1) và AI Generation (M2) có dữ liệu để vận hành | Chưa bắt đầu |
| **S3** | Tracking | **Module 1 — Tracking** | Ghi vết thời gian làm bài, giám sát tần suất, cảnh báo tiến độ nộp bài (SRS §2, dòng 1) | Chưa bắt đầu |
| **S4** | AI Generation | **Module 2 — AI Generation** | Upload tài liệu, cấu hình tiêu chí, AI sinh đề, GV duyệt/biên tập (SRS §2, dòng 2) | Chưa bắt đầu |
| **S5** | Teacher Dashboard | **Module 3 — Teacher Dashboard** | Phổ điểm lớp, phân tích hành vi cá nhân, khuyến nghị sư phạm, xuất báo cáo (SRS §2, dòng 3) | Chưa bắt đầu |
| **S6** | Student Dashboard | **Module 4 — Student Dashboard** | Số liệu theo môn, mục tiêu điểm số, gợi ý lộ trình, biểu đồ radar (SRS §2, dòng 4) | Chưa bắt đầu |

### Ghi chú ánh xạ
- **S0–S2** không xuất hiện trực tiếp trong bảng 4-module của SRS §2, nhưng là hạ tầng bắt buộc: SRS giả định đã có tài khoản (RBAC), cơ cấu tổ chức (lớp/môn/ghi danh), và dữ liệu bài tập/câu hỏi trước khi Tracking hay AI Generation có ý nghĩa.
- **NFR hiệu năng** (AI ≤ 15–30s, dashboard < 3s) áp dụng trực tiếp cho S4 (AI Generation) và S5–S6 (Dashboard) — cần đưa vào Acceptance Criteria (PART A) và benchmark test (PART D) của các spec tương ứng.
- **NFR bảo mật/RBAC** ("HS không xem dữ liệu hành vi của HS khác", "GV chỉ quản lý lớp mình") đã được đặt nền ở S0 (permission-based RBAC) nhưng cần enforcement cụ thể ở tầng data-access khi triển khai S3 (Tracking) và S5 (Teacher Dashboard) — ví dụ: filter theo `teacher_subjects`/`student_class`.
- Nếu muốn đổi thứ tự hoặc gộp sprint (vd gộp S1+S2), cập nhật đồng thời bảng "Lộ trình Sprint" ở [README.md §7](../../README.md#7-lộ-trình-sprint) để hai tài liệu không lệch nhau.

## 6. Tham chiếu

- SRS gốc: [docs/HỆ THỐNG QUẢN LÍ BÀI TẬP KẾT HỢP PHÂN TÍCH HÀNH VI.pdf](../HỆ%20THỐNG%20QUẢN%20LÍ%20BÀI%20TẬP%20KẾT%20HỢP%20PHÂN%20TÍCH%20HÀNH%20VI.pdf)
- Lộ trình sprint: [README.md §7](../../README.md#7-lộ-trình-sprint)
- Chi tiết Sprint 0: [sprint_0_overview.md](sprints/sprint_0_overview.md)
- ERD tham chiếu: [docs/base_sql_erd.sql](../base_sql_erd.sql)
