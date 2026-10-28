> Path: `docs/tasks/f_doc_01/f_doc_01_document_repository.md`
> Slice: `SL-DOC-01` · Type: `feature` · Size: `large` · SP: `5`
> Depends on: `F-AUTH-01`, `F-ACAD-01`
> Status: `ready to test`
> Created At: `2026-10-27`
> Updated At: `2026-10-28`

# Task — `F-DOC-01` Teacher Document Repository (Kho Học liệu & Quản lý Tài liệu)

**Created By:** Tam Khang  
**Updated By:** Tam Khang  

## Mô tả Task
Triển khai phân hệ Kho Tài liệu & Học liệu Số (`/api/v1/documents`) và tích hợp với `DocumentRepositoryPage.jsx`:
1. Alembic Migration: Cập nhật bảng `documents` bổ sung các trường metadata (`grade`, `document_type`, `file_size`, `mime_type`, `description`, `is_public`, `download_count`, chuẩn hóa `status = 'ACTIVE'` hỗ trợ Soft Delete).
2. Storage & Service Layer (`DocumentStorageService`, `DocumentService`):
   - Hỗ trợ upload file `.pdf`, `.docx`, `.pptx`, `.xlsx` (tối đa 50MB), lưu trữ an toàn vào thư mục băm (`uploads/documents/YYYY/MM/UUID.ext`).
   - Lọc đa tiêu chí (`subject_id`, `grade`, `document_type`, `search`), phân trang.
   - Xem chi tiết, cập nhật metadata, tải file (`/download`), xem trước (`/preview-url`), xóa mềm (`status = 'DELETED'`) và khôi phục (`/restore`).
3. Tích hợp Frontend: Khai báo `documentsApi` trong `frontend/src/services/api.js` và kết nối vào `DocumentRepositoryPage.jsx`, `UploadDocumentModal.jsx`, `DocumentPreviewModal.jsx`, `EditDocumentModal.jsx`.

## Checklist Thực Hiện
- [x] Tạo Alembic migration cập nhật bảng `documents`.
- [x] Seed permissions `DOC_DOCUMENT_MANAGE` và `DOC_DOCUMENT_VIEW`.
- [x] Xây dựng 8 endpoints dưới `/api/v1/documents`.
- [x] Cập nhật `frontend/src/services/api.js` và nối hoàn chỉnh với `DocumentRepositoryPage.jsx`.
- [x] Viết Unit & Integration Tests (`pytest tests/document/`) đạt 100% pass rate.

