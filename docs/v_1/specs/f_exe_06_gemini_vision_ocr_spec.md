# Feature Spec — `F-EXE-06` AI Gemini Vision OCR & Math Exam Document Parser

> Path: `docs/v_1/specs/f_exe_06_gemini_vision_ocr_spec.md` · Sprint: SPRINT-03 / SPRINT-04
> Created At: `2026-09-02`
> Created By: `Tam Khang`
> Updated At: `2026-09-02`
> Updated By: `Tam Khang`

---

## Document Header

| Field | Giá trị |
|---|---|
| Feature ID | `F-EXE-06` |
| Feature name | AI Gemini Vision OCR & Math Exam Document Parser — Nhận diện & Bóc tách Đề thi Toán học / KHTN bằng Google Gemini Multimodal Vision |
| Module(s) | `exercise` |
| Sprint(s) allocated | `SPRINT-03` / `SPRINT-04` |
| Lane | `standard` |
| Spec version | `v1.0` |
| Last updated | `2026-09-02` |
| Source binding | `f_exe_05_question_import_spec.md` · `f_exe_01_exercises_spec.md` · `.claude/rules/coding_rules.md` |

### Gate status

| Gate | Bao trùm | Owner | Approver | Status | Date |
|---|---|---|---|---|---|
| G3 Business | PART A | Tam Khang | Tam Khang | `approved` | 2026-09-02 |
| G4 Architecture | PART B | Tam Khang | Tam Khang | `approved` | 2026-09-02 |
| G6 Design | PART C | Tam Khang | Tam Khang | `approved` | 2026-09-02 |
| G6.5 Coding | PART D | Tam Khang | Tam Khang | `ready` | 2026-09-02 |
| G7+ Tracking | PART E | Tam Khang | Tam Khang | `live` | 2026-09-02 |

---

# PART A — Business

> **Owner:** Tam Khang · **Gate:** G3

## A.1 Feature Summary

Tính năng nâng cấp bộ bóc tách đề thi (`ImportParserService`) bằng cách tích hợp trực tiếp **Google Gemini Multimodal Vision API (`gemini-1.5-pro` / `gemini-1.5-flash` / `gemini-2.5-flash`)**. 

Khi Giáo viên tải lên file PDF/Ảnh đề thi Toán học (hoặc Khoa học tự nhiên), hệ thống sẽ render từng trang sang ảnh độ nét cao và gửi đến Gemini Vision với Structured Output Schema. Gemini Vision sẽ tự động nhận diện chính xác 100% nội dung câu hỏi, bọc toàn bộ công thức toán học dưới chuẩn `$LaTeX$`, nhận diện bảng biến thiên, đồ thị, ma trận, hình học không gian, và phân tách chuẩn xác 3 phần câu hỏi theo format mới của Bộ GD&ĐT (Phần I: Trắc nghiệm 4 lựa chọn, Phần II: Đúng/Sai, Phần III: Trả lời ngắn).

---

## A.2 User Stories

| Story ID | As (role) | I want (capability) | So that (value) |
|---|---|---|---|
| **US-01** | Giáo viên (Teacher) | Tải lên đề thi PDF/Ảnh chứa công thức Toán, bảng biến thiên, hình học phức tạp | Hệ thống tự động bóc tách thành các câu hỏi trắc nghiệm hoàn chỉnh kèm công thức LaTeX chuẩn xác mà không cần nhập tay. |
| **US-02** | Giáo viên (Teacher) | Bóc tách tự động bảng đáp án và giải chi tiết từ file đính kèm | Hệ thống tự động đánh dấu đáp án đúng cho từng câu hỏi (Phần I, II, III). |
| **US-03** | Quản trị viên (Admin) | Cấu hình linh hoạt API Key và lựa chọn model Gemini (`gemini-1.5-flash` cho tốc độ hoặc `gemini-1.5-pro` cho độ chính xác tối đa) | Tối ưu chi phí và hiệu năng vận hành hệ thống. |

---

## A.3 REQ Registry

| REQ ID | Mô tả ngắn | Priority | Status | Linked Story |
|---|---|---|---|---|
| **REQ-001** | Trích xuất PDF/Ảnh trang đề thi sang định dạng hình ảnh chuẩn (PNG 300 DPI). | P0 | `approved` | US-01 |
| **REQ-002** | Tích hợp Google Gemini Vision API gửi trang ảnh kèm Prompt có Structured JSON Schema. | P0 | `approved` | US-01 |
| **REQ-003** | Tự động phân loại 3 phần: Phần I (4 lựa chọn), Phần II (Đúng/Sai), Phần III (Trả lời ngắn). | P0 | `approved` | US-01 |
| **REQ-004** | Nhận diện và format chuẩn các cấu trúc Toán học đặc biệt (Bảng biến thiên, Đồ thị, Phân số, Tích phân, Ma trận, Hình không gian) dưới dạng `$LaTeX$` hoặc `$$LaTeX$$`. | P0 | `approved` | US-01 |
| **REQ-005** | Tự động cắt (crop) và lưu trữ ảnh hình học/đồ thị đính kèm từng câu hỏi (`image_url`). | P1 | `approved` | US-01 |
| **REQ-006** | Hỗ trợ bóc tách file đáp án riêng biệt (Answer Key PDF/Ảnh/Bảng mã đề). | P0 | `approved` | US-02 |
| **REQ-007** | Cơ chế Fallback sang Local Parser (Regex/pdfplumber/docx) khi không có Internet/API Key hoặc lỗi mạng. | P1 | `approved` | US-03 |

---

## A.4 Acceptance Criteria (Feature-level)

- **AC-01 (Công thức Toán học):** Toàn bộ các công thức toán như $f(x)=x^3-3x^2+2$, $\log_2(x-1)<3$, $\int \frac{2x}{x^2+1}dx$, $\vec{n}=(2;1;-1)$ phải được bao đóng trong `$ ... $` và hiển thị hoàn hảo trên KaTeX.
- **AC-02 (Bảng biến thiên):** Được chuyển đổi thành cấu trúc Markdown/LaTeX Table hoặc thẻ HTML có format rõ ràng $x, y', y$ với các mũi tên $\nearrow, \searrow$.
- **AC-03 (Phân loại Đúng/Sai):** Mỗi câu hỏi Phần II phải bóc tách đủ 4 ý `a)`, `b)`, `c)`, `d)` với trạng thái Đúng (`True`) / Sai (`False`).
- **AC-04 (Tốc độ & Timeout):** Thời gian xử lý 1 trang đề thi qua `gemini-1.5-flash` không vượt quá 5 giây/trang.

---

# PART B — Architecture & Workflow

> **Owner:** Tam Khang · **Gate:** G4

## B.1 High-Level Architecture

```text
               ┌─────────────────────────────────────────────────────────────┐
               │                     Teacher Upload PDF/Image                │
               └──────────────────────────────┬──────────────────────────────┘
                                              ▼
               ┌─────────────────────────────────────────────────────────────┐
               │            Page Renderer (pypdfium2 / pdf2image)            │
               │         Convert PDF pages to High-Resolution Images         │
               └──────────────────────────────┬──────────────────────────────┘
                                              ▼
               ┌─────────────────────────────────────────────────────────────┐
               │              Gemini Vision Parser Service                   │
               │   • System Prompt: Vietnamese Math Exam Guidelines          │
               │   • Schema Enforcement: Structured JSON Pydantic Model      │
               │   • Model: gemini-1.5-flash / gemini-1.5-pro / 2.5-flash    │
               └──────────────────────────────┬──────────────────────────────┘
                                              ▼
               ┌─────────────────────────────────────────────────────────────┐
               │              Post-Processing & Validation Pipeline          │
               │   • KaTeX Syntax Validation                                 │
               │   • Answer Key Matching (from separate answer file)         │
               │   • Math Tokenizer & $LaTeX$ Boundary Verification          │
               └──────────────────────────────┬──────────────────────────────┘
                                              ▼
               ┌─────────────────────────────────────────────────────────────┐
               │          Database Persistence & Frontend Delivery           │
               │   • Insert into `questions` & `answer_options` tables       │
               │   • Immediate Reactive Display on Frontend with KaTeX       │
               └─────────────────────────────────────────────────────────────┘
```

---

## B.2 Gemini Vision Structured Output Schema

Gemini Vision API sẽ được cấu hình `response_schema` nghiêm ngặt theo chuẩn Pydantic:

```json
{
  "questions": [
    {
      "question_number": 1,
      "part": "Part1",
      "question_type": "MultipleChoice",
      "difficulty": "NhanBiet",
      "content": "Cho hàm số $f(x) = x^{3} - 3x^{2} + 2$. Giá trị cực đại của hàm số là:",
      "content_markdown": "Cho hàm số $f(x) = x^{3} - 3x^{2} + 2$. Giá trị cực đại của hàm số là:",
      "content_latex": "$f(x) = x^{3} - 3x^{2} + 2$",
      "answer_options": [
        {"content": "$0$", "is_correct": false, "display_order": 0},
        {"content": "$2$", "is_correct": true, "display_order": 1},
        {"content": "$-2$", "is_correct": false, "display_order": 2},
        {"content": "$4$", "is_correct": false, "display_order": 3}
      ]
    }
  ]
}
```

---

# PART C — API & Technical Design

> **Owner:** Tam Khang · **Gate:** G6

## C.1 Environment Configuration

Thêm các biến môi trường cấu hình trong `.env`:

```env
# Google Gemini API Settings
GEMINI_API_KEY=your_google_gemini_api_key_here
GEMINI_MODEL_NAME=gemini-1.5-flash
GEMINI_FALLBACK_MODEL=gemini-1.5-pro
GEMINI_MAX_OUTPUT_TOKENS=8192
GEMINI_TEMPERATURE=0.1
```

---

## C.2 Target Files & Service Layer Design

1. **`app/core/config.py`**:
   - Thêm các biến cấu hình Gemini API (`GEMINI_API_KEY`, `GEMINI_MODEL_NAME`).
2. **`app/modules/exercise/services/gemini_vision_parser_service.py` [NEW]**:
   - Chứa lớp `GeminiVisionParserService` đảm nhiệm:
     - Chuyển đổi PDF sang hình ảnh (`render_pdf_to_images`).
     - Gọi Google Gemini API với multimodal content (ảnh + prompt).
     - Parse và validate JSON response bằng Pydantic schema.
3. **`app/modules/exercise/services/import_parser_service.py` [MODIFY]**:
   - Tích hợp `GeminiVisionParserService` làm bộ parser ưu tiên số 1 cho file PDF/Ảnh.
   - Nếu không có `GEMINI_API_KEY` hoặc gặp sự cố mạng, tự động fallback sang `pdfplumber` / Regex truyền thống.

---

# PART D — Coding Context & Implementation

> **Owner:** Tam Khang · **Gate:** G6.5

## D.1 Python Dependencies

Đảm bảo các thư viện đã được cài đặt:
- `google-genai` hoặc `google-generativeai>=0.8.0`
- `pypdfium2>=4.30.0` (Render PDF ra ảnh siêu nhanh không phụ thuộc poppler C++ bên ngoài)
- `pillow>=10.0.0`
- `pydantic>=2.0.0`

---

## D.2 Sample System Prompt for Gemini

```text
Bạn là một chuyên gia số hóa đề thi Toán học và Khoa học tự nhiên của Bộ Giáo dục & Đào tạo Việt Nam.
Nhiệm vụ của bạn là bóc tách toàn bộ câu hỏi và các phương án từ hình ảnh đề thi được cung cấp thành định dạng JSON có cấu trúc.

Quy tắc bắt buộc:
1. Mọi công thức toán học, biểu thức, biến số, tọa độ, phân số, tích phân, logarit PHẢI được viết chuẩn cú pháp LaTeX và bao bọc trong dấu '$' (ví dụ: '$f(x) = \\frac{2x}{x^2+1}$', '$\\log_2(x-1) < 3$').
2. Bảng biến thiên phải được chuyển đổi thành bảng Markdown/LaTeX có format rõ ràng.
3. Phân biệt chính xác:
   - Phần I: Trắc nghiệm 4 lựa chọn (A, B, C, D)
   - Phần II: Trắc nghiệm Đúng/Sai với 4 ý a), b), c), d)
   - Phần III: Câu hỏi trả lời ngắn (ShortAnswer)
4. Độ khó nếu có các nhãn [NB], [TH], [VD], [VDC] thì map tương ứng sang: NhanBiet, ThongHieu, VanDung, VanDungCao. Nếu không có thì để null.
```

---

# PART E — Tracking & Verification

> **Owner:** Tam Khang · **Gate:** G7

## E.1 Verification Matrix

| Kịch bản kiểm thử | Dữ liệu đầu vào | Kỳ vọng |
|---|---|---|
| **Test 01: Đề Toán chứa Phân số & Logarit** | `docs/samples/de_kiem_tra_toan_12_...pdf` | Bóc tách 20 câu hỏi, công thức $LaTeX$ 100% không bị vỡ dòng. |
| **Test 02: Bảng biến thiên hàm số** | Trang PDF có bảng xét dấu/biến thiên | Hiển thị bảng cấu trúc đẹp trên KaTeX. |
| **Test 03: File đáp án riêng** | `docs/samples/dap_an_toan_12_...pdf` | Khớp đúng 100% đáp án đúng cho từng câu hỏi. |
| **Test 04: Fallback khi mất mạng** | Disable network / API key không hợp lệ | Hệ thống tự động chuyển sang chế độ fallback cũ mà không bị crash HTTP 500. |
