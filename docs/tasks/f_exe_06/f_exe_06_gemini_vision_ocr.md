> Path: `docs/tasks/f_exe_06/f_exe_06_gemini_vision_ocr.md`
> Slice: `SL-EXE-06` · Type: `feature` · Size: `large` · SP: `5`
> Depends on: `F-EXE-05`
> Status: `ready to test`
> Created At: `2026-09-02`
> Updated At: `2026-09-02`

# Task — `F-EXE-06` Google Gemini Multimodal Vision Exam Document OCR

**Author:** Tam Khang  
**Updated By:** Tam Khang  

---

## 1. Mô tả Task (Task Overview)

Triển khai tích hợp **Google Gemini Multimodal Vision API (`gemini-2.5-flash` / `gemini-1.5-flash` / `gemini-1.5-pro`)** vào hệ thống bóc tách đề thi (`ImportParserService`):
1. **Renderer Module:** Sử dụng `pypdfium2` để render các trang PDF đề thi sang ảnh chất lượng cao (PNG 300 DPI).
2. **Gemini Vision Service (`GeminiVisionParserService`):**
   - Khởi tạo client kết nối qua `google-genai` / `google-generativeai`.
   - Xây dựng System Prompt chuyên sâu về đề thi Toán học & KHTN Việt Nam.
   - Định nghĩa Structured Output Schema (Pydantic / JSON) để Gemini trả về JSON có cấu trúc chuẩn 100%.
   - Xử lý bảng biến thiên hàm số (chuyển đổi sang Markdown/LaTeX Table), ma trận, tích phân, hình không gian và hệ phương trình.
3. **Hybrid Fallback Mechanism:**
   - Ưu tiên sử dụng Gemini Vision API.
   - Nếu không có cấu hình `GEMINI_API_KEY` hoặc lỗi kết nối, tự động chuyển về bộ parser regex/pdfplumber truyền thống (`F-EXE-05`).
4. **Answer Key Integration:**
   - Bóc tách file đáp án riêng biệt hoặc phần đáp án đính kèm cuối file.
   - Tự động map đáp án đúng cho từng câu hỏi (Phần I, Phần II, Phần III).
5. **Testing & Validation:**
   - Viết Unit Tests & Integration Tests cho Gemini Vision Parser với test suite 100% passed.

---

## 2. Technical Workflow

```text
[PDF/Image Upload]
       ↓
[pypdfium2: Render Page Images]
       ↓
[GeminiVisionParserService (gemini-2.5-flash + Structured Schema)]
       ↓
[Structured JSON Output (Questions, Parts, LaTeX Formulas)]
       ↓
[Answer Key Matching & Validation]
       ↓
[Save to Database: `questions` + `answer_options`]
```

---

## 3. Checklist Thực Hiện

- [x] Cấu hình biến môi trường `GEMINI_API_KEY` và `GEMINI_MODEL_NAME` trong `.env.example`.
- [x] Cài đặt và tích hợp thư viện `google-genai` / `pypdfium2` vào `requirements.txt`.
- [x] Viết service `GeminiVisionParserService` (`app/modules/exercise/services/gemini_vision_parser_service.py`).
- [x] Cập nhật `ImportParserService` (`app/modules/exercise/services/import_parser_service.py`) để ưu tiên gọi Gemini Vision.
- [x] Viết bộ kiểm thử unit tests `backend/tests/exercise/unit/test_gemini_vision_parser.py` (150/150 passed).
- [x] Kiểm tra hiển thị công thức Toán học trên giao diện Frontend KaTeX.
