# Feature Spec — `F-DOC-01` Teacher Document Repository & Resource Management

> Path: `docs/v_1/specs/f_doc_01_document_repository_spec.md` · Sprint: SPRINT-04
> Created At: `2026-09-20`
> Created By: `Tam Khang`
> Updated At: `2026-09-20`
> Updated By: `Tam Khang`

---

## Document Header

| Field | Giá trị |
|---|---|
| Feature ID | `F-DOC-01` |
| Feature name | Teacher Document Repository & Resource Management — Quản lý Kho Học liệu & Tài liệu Giảng dạy |
| Module(s) | `document`, `teacher` |
| Sprint(s) allocated | `SPRINT-04` |
| Lane | `standard` |
| Spec version | `v1.0` |
| Last updated | `2026-09-20` |
| Source binding | `business_overview.md` · `f_exe_01_exercises_spec.md` · `.claude/rules/coding_rules.md` |

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

Cung cấp kho lưu trữ và chia sẻ học liệu số phục vụ giảng dạy cho Giáo viên:
1. **Quản lý tài liệu đa định dạng**: Lưu trữ file giáo án, bài giảng trình chiếu, tài liệu tham khảo dạng PDF, DOCX, PPTX.
2. **Phân loại & Tìm kiếm đa tiêu chí**: Lọc tài liệu theo Khối lớp (10, 11, 12), Môn học (Toán, Lý, Hóa,...) và loại tài liệu.
3. **Xem trước & Tải về trực quan**: Cho phép giáo viên xem trước nội dung tài liệu trực tiếp trên trình duyệt mà không cần tải về máy.
4. **Chính sách Xóa mềm (Soft Delete)**: Đảm bảo tài liệu khi xóa chỉ chuyển sang trạng thái `DELETED` và có thể khôi phục khi cần thiết.

---

## A.2 User Stories

| Story ID | As (role) | I want (capability) | So that (value) |
|---|---|---|---|
| **US-01** | Giáo viên (Teacher) | Tải lên tài liệu giảng dạy và phân loại theo môn/khối | Xây dựng kho học liệu cá nhân phục vụ giảng dạy. |
| **US-02** | Giáo viên (Teacher) | Tìm kiếm và xem trước tài liệu nhanh chóng | Dễ dàng tra cứu học liệu khi soạn bài. |
| **US-03** | Giáo viên (Teacher) | Xóa các tài liệu cũ không còn sử dụng | Dọn dẹp kho tài liệu mà vẫn đảm bảo an toàn dữ liệu qua cơ chế xóa mềm. |

---

## A.3 REQ Registry

| REQ ID | Mô tả ngắn | Priority | Status | Linked Story |
|---|---|---|---|---|
| **REQ-DOC-01** | Tải lên tài liệu học liệu đính kèm metadata (môn, khối, tiêu đề) | P0 | Active | US-01 |
| **REQ-DOC-02** | Danh sách tài liệu có phân trang và lọc theo môn/khối | P0 | Active | US-01, US-02 |
| **REQ-DOC-03** | Xem trước (Preview) tài liệu PDF/DOCX | P1 | Active | US-02 |
| **REQ-DOC-04** | Xóa mềm tài liệu (`status = 'DELETED'`) | P1 | Active | US-03 |
