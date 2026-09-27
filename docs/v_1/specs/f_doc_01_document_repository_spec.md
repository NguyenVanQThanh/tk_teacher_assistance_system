# Feature Spec — `F-DOC-01` Teacher Document Repository & Resource Management

> Path: `docs/v_1/specs/f_doc_01_document_repository_spec.md` · Sprint: [sprint_4_overview.md](../sprints/sprint_4_overview.md)  
> Created At: `2026-09-20`  
> Created By: `Tam Khang`  
> Updated At: `2026-09-23`  
> Updated By: `Tam Khang`  

---

## Document Header

| Field | Giá trị |
|---|---|
| **Feature ID** | `F-DOC-01` |
| **Feature Name** | Teacher Document Repository & Resource Management — Quản lý Kho Học liệu & Tài liệu Giảng dạy |
| **Module(s)** | `document`, `teacher` |
| **Sprint(s) Allocated** | `SPRINT-04` |
| **Spec Version** | `v1.1` |
| **Last Updated** | `2026-09-23` |
| **Source Binding** | `business_overview.md` · `models/models.py` · `.claude/rules/coding_rules.md` |

---

# PART A — Business & Requirements

> **Owner:** Tam Khang · **Gate:** G3

## A.1 Feature Summary

Cung cấp kho lưu trữ và chia sẻ học liệu số phục vụ giảng dạy cho Giáo viên:
1. **Quản lý tài liệu đa định dạng**: Lưu trữ file giáo án, tài liệu tham khảo dạng `.pdf`, `.docx`, `.xlsx`.
2. **Phân loại & Tìm kiếm đa tiêu chí**: Lọc tài liệu theo Khối lớp (10, 11, 12), Môn học (Toán, Lý, Hóa,...) và loại tài liệu (`lecture`, `exam`, `reference`).
3. **Xem trước & Tải về trực quan**: Cho phép giáo viên xem trước nội dung tài liệu trực tiếp trên trình duyệt hoặc tải file về máy an toàn.
4. **Chính sách Xóa mềm (Soft Delete)**: Đảm bảo tài liệu khi xóa chỉ chuyển sang trạng thái `DELETED` và có thể khôi phục khi cần thiết (`POST /restore`).

## A.2 User Stories

| Story ID | As (Role) | I Want (Capability) | So That (Value) |
|---|---|---|---|
| **US-01** | Teacher | Tải lên tài liệu giảng dạy và phân loại theo môn/khối | Xây dựng kho học liệu cá nhân phục vụ giảng dạy. |
| **US-02** | Teacher | Tìm kiếm và xem trước tài liệu nhanh chóng | Dễ dàng tra cứu học liệu khi soạn bài. |
| **US-03** | Teacher | Xóa các tài liệu cũ không còn sử dụng và khôi phục khi cần | Dọn dẹp kho tài liệu mà vẫn đảm bảo an toàn dữ liệu qua cơ chế xóa mềm. |
| **US-04** | Teacher | Chuyển đổi tài liệu sang tạo đề bài tập mới | Tái sử dụng nội dung tài liệu để sinh câu hỏi kiểm tra. |

---

# PART B — Technical Specifications & API Contracts

## B.1 API Endpoints

### 1. `POST /api/v1/documents/upload`
* **Permission**: `DOC_DOCUMENT_MANAGE` & Role `Teacher`/`Admin`
* **Request**: `multipart/form-data`
  * `file`: File upload (`.pdf`, `.docx`, `.xlsx`, tối đa 50MB)
  * `title`: str (bắt buộc, 3..255 ký tự)
  * `subject_id`: UUID (bắt buộc)
  * `grade`: str (bắt buộc, vd: `"10"`, `"11"`, `"12"`)
  * `document_type`: str (`lecture` | `exam` | `reference`)
  * `description`: str (tùy chọn)
  * `is_public`: bool (mặc định: `false`)
* **Response `201 Created`**: Document Object.

### 2. `GET /api/v1/documents`
* **Permission**: `DOC_DOCUMENT_VIEW`
* **Query Params**:
  * `subject_id`: UUID (tùy chọn)
  * `grade`: str (tùy chọn)
  * `document_type`: str (tùy chọn)
  * `search`: str (tìm kiếm theo tiêu đề, mô tả, tên file)
  * `page`: int (mặc định 1), `page_size`: int (mặc định 12)
* **Response `200 OK`**:
```json
{
  "items": [
    {
      "id": "1fa85f64-5717-4562-b3fc-2c963f66af01",
      "title": "Chuyên đề Đạo hàm & Khảo sát hàm số 12",
      "file_name": "chuyen_de_dao_ham_12.pdf",
      "file_size": 2458120,
      "mime_type": "application/pdf",
      "subject_id": "4da85f64-5717-4562-b3fc-2c963f66af01",
      "subject_name": "Toán Học",
      "grade": "12",
      "document_type": "lecture",
      "author_id": "5ea85f64-5717-4562-b3fc-2c963f66af02",
      "author_name": "Thầy Nguyễn Văn A",
      "status": "ACTIVE",
      "download_count": 14,
      "created_at": "2026-09-10T14:30:00Z"
    }
  ],
  "total": 24,
  "page": 1,
  "page_size": 12,
  "total_pages": 2
}
```

### 3. `GET /api/v1/documents/{document_id}/download`
* **Permission**: `DOC_DOCUMENT_VIEW`
* **Response `200 OK`**: File Stream (`Content-Disposition: attachment; filename="..."`).

### 4. `DELETE /api/v1/documents/{document_id}`
* **Permission**: `DOC_DOCUMENT_MANAGE`
* **Response `204 No Content`** (Soft delete: `status = 'DELETED'`).

### 5. `POST /api/v1/documents/{document_id}/restore`
* **Permission**: `DOC_DOCUMENT_MANAGE`
* **Response `200 OK`**: Document Object với `status = 'ACTIVE'`.
