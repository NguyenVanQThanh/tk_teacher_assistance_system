> Path: `docs/tasks/f_exe_05/f_exe_05_pdf_export.md`
> Slice: `SL-EXE-05` · Type: `feature` · Size: `medium` · SP: `3`
> Depends on: `F-EXE-05`
> Status: `ready to test`
> Created At: `2026-08-12`
> Updated At: `2026-08-12`


# Task — `F-EXE-05` Export Exercise to PDF (Xuất đề thi ra file PDF từ DB kèm LaTeX)

**Author:** Tam Khang  
**Updated By:** Tam Khang  

## Mô tả Task
Triển khai tính năng xuất đề thi từ cơ sở dữ liệu PostgreSQL ra file PDF theo chuẩn cấu trúc đề thi THPT QG của Bộ GD&ĐT:
1. Thêm dependency `reportlab` và `matplotlib` vào `requirements.txt`.
2. `PdfExportService`: Render công thức toán học dạng LaTeX (`$ ... $`) bằng `matplotlib.mathtext` thành hình ảnh công thức.
3. Phân loại câu hỏi thành 3 Phần chính: Phần I (Trắc nghiệm 4 lựa chọn), Phần II (Trắc nghiệm Đúng/Sai), Phần III (Trả lời ngắn) kèm hình ảnh minh họa nếu có (`image_url`).
4. Tự động sinh bảng đáp án ở cuối trang PDF.
5. API Router: `GET /api/v1/exercises/{exercise_id}/export/pdf` (yêu cầu quyền `EXE_EXERCISE_VIEW` hoặc `EXE_QUESTION_IMPORT`).
6. Unit tests & Integration tests cho service và endpoint.

## Technical Workflow

```
Bước 1: Dependencies & Font Setup
  └── requirements.txt: reportlab, matplotlib
  └── Font Unicode: Đăng ký Arial/DejaVuSans cho ReportLab để hỗ trợ Tiếng Việt

Bước 2: Service Layer
  └── app/modules/exercise/services/pdf_export_service.py:
        render_latex_to_image(latex_str) -> BytesIO
        generate_exercise_pdf(exercise) -> bytes

Bước 3: API Router
  └── app/modules/exercise/routers/exercises.py: export_exercise_pdf endpoint
        - Kiểm tra quyền truy cập bài tập
        - Gọi PdfExportService.generate_exercise_pdf()
        - Trả về Response(content=pdf_bytes, media_type="application/pdf")

Bước 4: Automated Testing Verification
  └── tests/exercise/unit/test_pdf_export_service.py
  └── tests/exercise/test_exercises.py
```
