# Feature Spec — `F-EXE-05` Question Import & Math OCR Document Pipeline

> Path: `docs/v_1/specs/f_exe_05_question_import_spec.md` · Sprint: [sprint_2_overview.md](../sprints/sprint_2_overview.md)
> Created At: `2026-07-28`
> Created By: `Tam Khang`
> Updated At: `2026-08-16`
> Updated By: `Tam Khang`

---

## Document Header

| Field | Giá trị |
|---|---|
| Feature ID | `F-EXE-05` |
| Feature name | Question Import & Math OCR Pipeline — Nhập câu hỏi từ Docx/PDF, Phân tích Layout, OCR Toán học & Xuất bản Đa định dạng |
| Module(s) | `exercise` |
| Sprint(s) allocated | `SPRINT-02` (Core Parser & Import) / `SPRINT-04` (Advanced OCR Pipeline) |
| Lane | `standard` |
| Spec version | `v3.0` |
| Last updated | `2026-08-16` |
| Source binding | `docs/tasks/f_exe_05/OCR_Math_Document_Pipeline_Architecture.md` · `f_exe_01_exercises_spec.md` · `.claude/rules/coding_rules.md` |

---

# PART A — Business

> **Owner:** Tam Khang · **Gate:** G3

## A.1 Feature Summary

Tính năng cho phép **Giáo viên** tải lên tài liệu đề thi (`.docx`, Native `.pdf`, hoặc Scanned `.pdf` / hình ảnh scan) kèm file/phần đáp án theo định dạng chuẩn THPT Quốc gia của Bộ GD&ĐT để tự động nhận diện cấu trúc, bóc tách câu hỏi, nhận diện công thức toán học chuyên sâu (Mathematical Expression Recognition — MER), lưu trữ có cấu trúc vào Database, hiển thị tương tác trên Web qua HTML5/KaTeX và xuất bản lại đa định dạng (PDF/XeLaTeX, Markdown, LaTeX, HTML).

Hệ thống hoạt động theo pipeline nhận diện phân cấp: **Page $\rightarrow$ Layout Detection $\rightarrow$ Block $\rightarrow$ Segment (Text / Math / Image)**, phân biệt rõ công thức toán dạng **Inline Math** (`$ ... $` / `\( ... \)`) và **Display Math** (`$$ ... $$` / `\[ ... \]`), bảo toàn tọa độ Bounding Box (`bbox`), độ tin cậy (`confidence`), và hỗ trợ hàng đợi xử lý bất đồng bộ (Async Job Queue) cho các tệp tài liệu lớn.

---

## A.2 Quy tắc Template, Cú pháp & Pipeline Architecture

### 1. Tag Mức độ khó (Difficulty Tags)
- `[NB]`: Nhận biết (`NhanBiet`)
- `[TH]`: Thông hiểu (`ThongHieu`)
- `[VD]`: Vận dụng (`VanDung`)
- **Quy tắc:** Nếu **không** gắn tag độ khó ở đầu câu, hệ thống mặc định để **trống (`None` / null)**.

### 2. Ba phần / loại câu hỏi (Question Parts & Types)
File đề thi gồm 3 Phần chính theo cấu trúc chuẩn:
- **Phần I: Trắc nghiệm 4 lựa chọn (`MultipleChoice`):** Gồm 1 câu hỏi chính và 4 lựa chọn `A`, `B`, `C`, `D` (hoặc `a`, `b`, `c`, `d`). Ký tự phân cách sau nhãn: `.`, `)`, `/` (ví dụ: `A.`, `A)`, `A/`).
- **Phần II: Trắc nghiệm Đúng / Sai (`TrueFalse`):** Gồm 1 mệnh đề chính và 4 ý `a)`, `b)`, `c)`, `d)`. Mỗi ý có trạng thái **Đúng** hoặc **Sai**.
- **Phần III: Trả lời ngắn (`ShortAnswer`):** Gồm 1 nội dung câu hỏi chính, kết quả đáp án là số hoặc chuỗi ngắn.

---

### 3. Pipeline Xử lý OCR Tài Liệu Toán Học (Math Document OCR Architecture)

```text
                     ┌─ Native PDF / Docx ─→ Direct Text + OMML / BBox Extraction
Document (PDF/Docx) ─┤
                     └─ Scanned PDF / Image ─→ High-Res Render (300-400 DPI)
                                                    ↓
                                         Document Layout Analysis
                                                    ↓
                                ┌───────────────────┼────────────────────┐
                                ↓                   ↓                    ↓
                              TEXT             INLINE MATH          DISPLAY MATH
                                ↓                   ↓                    ↓
                          Text OCR/Parser      Math OCR → LaTeX     Math OCR → LaTeX
                                └───────────────────┼────────────────────┘
                                                    ↓
                                         LaTeX Syntax & KaTeX Validation
                                                    ↓
                                         Reading-Order Reconstruction
                                                    ↓
                                           Structured Document JSON
                                                    ↓
                                                Database
                                             ↙             ↘
                                       HTML Renderer      Exporter
                                        (KaTeX/MathJax)    (XeLaTeX/PDF/Markdown)
```

#### A. Phân loại đầu vào (Input Detection):
- **Native PDF / Docx:** Chứa sẵn text layer hoặc Word OMML equations. Sử dụng `PyMuPDF` (`fitz`) / `python-docx` để trích xuất text và tọa độ; chỉ crop và chạy Math OCR cho các vùng công thức bị vỡ hoặc thiếu semantic.
- **Scanned PDF / Image:** Render toàn bộ trang với độ phân giải tối ưu `300 DPI` (hoặc `400 DPI` cho chữ nhỏ) $\rightarrow$ Tiền xử lý ảnh (Deskew, Denoise, Contrast Adjustment).

#### B. Phân tích Layout (Layout Detection & Segmentation):
- Hệ thống **không** phân loại theo từng dòng đơn lẻ (`line`) mà phân chia theo phân cấp:
  `Page` $\rightarrow$ `Block` (question, answer, paragraph, table, figure) $\rightarrow$ `Segment` (`text`, `math`, `image`).
- Công cụ hỗ trợ: `PaddleOCR / PP-Structure`, `Docling`, hoặc Custom Layout Model.

#### C. Nhận diện Công thức Toán học (Mathematical Expression Recognition — MER):
- Sử dụng mô hình nhận diện công thức chuyên dụng (`UniMERNet`, `PaddleOCR Formula`, `pix2tex / LaTeX-OCR`).
- Chuyển đổi chính xác các dạng toán THPT: vector `\vec{v}`, phân số `\frac{a}{b}`, căn bậc hai `\sqrt{x}`, tích phân `\int`, giới hạn `\lim`, ma trận, số mũ và chỉ số dưới.

---

### 4. Cấu trúc Lưu trữ Dữ liệu Phân đoạn (Structured Document & Segment Model)

Để tránh trộn lẫn dữ liệu (`DATA`) và cách hiển thị (`PRESENTATION`), hệ thống chuẩn hóa lưu trữ theo cấu trúc JSON phân đoạn:

```json
{
  "question_number": 1,
  "part": "Part1",
  "question_type": "MultipleChoice",
  "difficulty": "NhanBiet",
  "segments": [
    {
      "type": "text",
      "content": "Cho hàm số "
    },
    {
      "type": "math",
      "display": false,
      "latex": "f(x)=x^3-3x^2+2",
      "confidence": 0.98,
      "bbox": [120, 45, 260, 68]
    },
    {
      "type": "text",
      "content": ". Giá trị cực đại của hàm số là:"
    }
  ],
  "content_markdown": "Cho hàm số f(x)=x³-3x²+2. Giá trị cực đại của hàm số là:",
  "content_latex": "Cho hàm số $f(x)=x^3-3x^2+2$. Giá trị cực đại của hàm số là:",
  "image_url": null,
  "needs_review": false
}
```

- **`content_markdown`:** Văn bản thuần quy đổi ký hiệu Unicode (ví dụ: `v⃗ = a⃗ + b⃗`, `x²`, `t₁`, `(a)/(b)`) để hiển thị siêu nhẹ và nhanh trên Web / Mobile App.
- **`content_latex`:** Văn bản giữ nguyên cú pháp LaTeX chuẩn để render qua KaTeX / MathJax hoặc xuất bản tài liệu PDF/Word chất lượng cao.
- **`segments` (Optional/Advanced):** Mảng các block thành phần kèm tọa độ BBox và độ tin cậy phục vụ Editor chỉnh sửa trực quan.

---

### 5. Ba Lớp Dữ Liệu Toán Học & Kiểm Định Công Thức (Formula Validation)

1. **Ba lớp dữ liệu:**
   - **`RAW`:** Output thô từ mô hình Math OCR.
   - **`NORMALIZED`:** Chuỗi LaTeX đã chuẩn hóa khoảng trắng, dấu ngoặc `{}`, lệnh ký hiệu toán học.
   - **`VERIFIED`:** Dữ liệu sau khi Giáo viên kiểm tra/chỉnh sửa trên giao diện Review UI (không bao giờ bị ghi đè khi tái chạy OCR).

2. **Cơ chế Validation & Confidence Score:**
   - **Syntax Validation:** Kiểm tra cân bằng ngoặc `{}`, cú pháp lệnh `\frac{...}{...}`, `\sqrt{...}`, `\left...\right`.
   - **Render Check:** Parse thử qua KaTeX parser; nếu gặp lỗi cú pháp $\rightarrow$ đánh dấu `needs_review = true`.
   - **Confidence Threshold:**
     - `confidence >= 0.95`: Tự động chấp thuận (Auto-Accept).
     - `0.80 <= confidence < 0.95`: Bình thường, chấp nhận hiển thị.
     - `confidence < 0.80` hoặc lỗi render: Gắn cờ cảnh báo `needs_review = true` để Giáo viên kiểm tra lại.

---

### 6. Hình ảnh minh họa & Bounding Box (Question Images & Figures)
- Trích xuất ảnh nhúng từ Docx hoặc crop vùng hình vẽ minh họa từ PDF/Image theo tọa độ `bbox`.
- Lưu trữ tệp ảnh độc lập vào Storage (`uploads/questions/` hoặc S3/MinIO), gán đường dẫn URL vào `image_url`.

---

### 7. Định dạng Tệp / Phần Đáp án (Answer Keys)
Hỗ trợ 3 định dạng đáp án phổ biến:
- **Dạng 1 (Bảng matrix nhiều Mã đề):** Cột `Câu`, các cột `Mã đề 0121`, `Mã đề 0122`... Cho phép chọn mã đề tương ứng khi import.
- **Dạng 2 (Bảng 1 Mã đề duy nhất):** Gồm 2 cột `Câu` (hoặc `STT`) và `Đáp án`.
- **Dạng 3 (Danh sách dòng chữ):** `1. A`, `2. a) Đ, b) S, c) Đ, d) S`, `3. 450`...

---

## A.3 User Stories

| Story ID | As (role) | I want (capability) | So that (value) |
|---|---|---|---|
| US-01 | Teacher | tải lên tệp đề thi (`.docx`, `.pdf`, ảnh scan) kèm file đáp án | tự động import hàng loạt câu hỏi chuẩn THPT QG vào ngân hàng đề |
| US-02 | Teacher | hệ thống tự động nhận diện công thức toán học (MER) và chuyển sang LaTeX chuẩn | không phải gõ lại công thức toán phức tạp thủ công |
| US-03 | Teacher | hệ thống sinh đồng thời phiên bản Markdown Unicode và LaTeX | hiển thị câu hỏi mượt mà trên app và render công thức sắc nét |
| US-04 | Teacher | xem danh sách các câu hỏi có độ tin cậy thấp hoặc lỗi cú pháp để review và chỉnh sửa trực quan | đảm bảo độ chính xác 100% của đề thi |
| US-05 | Teacher | xuất đề bài ra file PDF chuẩn (qua XeLaTeX), LaTeX hoặc Markdown | in ấn và phát đề thi với chất lượng typographic chuyên nghiệp |

---

## A.4 Business Workflow

```text
[Client Request: POST /api/v1/exercises/{exercise_id}/questions/import]
 (multipart form-data: question_file, optional answer_file, optional test_code)
       │
       ▼
 1. Authentication & Permission Check (EXE_QUESTION_IMPORT)
       │
       ▼
 2. File Validation (.docx / .pdf / image, max size limit)
       │
       ▼
 3. Extraction & Math Parsing Pipeline
    ├── If .docx: Extract text, OMML math equations, embedded images
    ├── If Native .pdf: PyMuPDF text & vector extraction + layout detection
    ├── If Scanned .pdf/image: 300 DPI render -> Layout detection -> Text/Math OCR
    ├── Run LaTeX Normalization & KaTeX validation
    ├── Convert to Markdown Unicode representation
    └── Separate into Part I (MCQ), Part II (TrueFalse), Part III (ShortAnswer)
       │
       ▼
 4. Answer Key Parsing (Table Matrix / Text List) & Matching with Test Code
       │
       ▼
 5. Validation Check & Consistency Check
    ├── Check all required fields & correct options
    └── If errors exist -> return 422 with structured error list (all-or-nothing)
       │
       ▼
 6. Save to Database in single Transaction
    └── Populate Question records (content, content_markdown, content_latex, image_url)
```

---

## A.5 Acceptance Criteria

| AC ID | REQ | Given | When | Then |
|---|---|---|---|---|
| AC-01 | REQ-EXE-041 | File `.docx` gồm cả 3 phần + Bảng đáp án hợp lệ | `POST .../questions/import` | 201 Created, trả về danh sách `QuestionOut` gồm đầy đủ `content_markdown` và `content_latex` |
| AC-02 | REQ-EXE-041 | Câu hỏi chứa công thức vector `\vec{v} = \vec{a} + \vec{b}` | `POST .../questions/import` | 201 Created, `content_latex` giữ `\vec{v} = \vec{a} + \vec{b}`, `content_markdown` chuyển thành `v⃗ = a⃗ + b⃗` |
| AC-03 | REQ-EXE-041 | Câu hỏi không gắn tag `[NB]`/`[TH]`/`[VD]` | `POST .../questions/import` | 201 Created, câu hỏi được lưu với `difficulty = None` |
| AC-04 | REQ-EXE-041 | Câu hỏi có chứa hình ảnh minh họa trong tệp `.docx`/`.pdf` | `POST .../questions/import` | 201 Created, hình ảnh được trích xuất và gán vào `image_url` |
| AC-05 | REQ-EXE-042 | Bảng đáp án có nhiều Mã đề (0121, 0122...) và client chọn `test_code=0121` | `POST .../questions/import` | 201 Created, đáp án của Mã đề 0121 được áp dụng chính xác cho đề |
| AC-06 | REQ-EXE-042 | File đề thi thiếu đáp án cho 1 câu ở Phần II | `POST .../questions/import` | 422 `ERR-EXE-IMPORT_INVALID_QUESTION`, từ chối lưu toàn bộ |
| AC-07 | REQ-EXE-041 | File `.txt` hoặc định dạng không được hỗ trợ | `POST .../questions/import` | 415 `ERR-EXE-IMPORT_FILE_TYPE_UNSUPPORTED` |
| AC-08 | REQ-EXE-043 | Người dùng yêu cầu xuất PDF đề bài | `GET .../export/pdf` | 200 OK, trả về file PDF render chuẩn vector kèm font toán học |

---

# PART B — Architecture & API Design

> **Owner:** Tam Khang · **Gate:** G4

### Endpoints

1. `POST /api/v1/exercises/{exercise_id}/questions/import`
   - **Summary:** Bulk import questions synchronously from docx/pdf templates.
   - **Content-Type:** `multipart/form-data`
   - **Form Parameters:**
     - `question_file`: UploadFile (required, `.docx` or `.pdf`)
     - `answer_file`: Optional[UploadFile] (optional separate answer key file)
     - `test_code`: Optional[str] (optional target test code, e.g. `"0121"`)
   - **Permissions:** `EXE_QUESTION_IMPORT`

2. `GET /api/v1/exercises/{exercise_id}/export/pdf`
   - **Summary:** Export exercise to high-quality PDF document with LaTeX math formatting.
   - **Permissions:** `EXE_EXERCISE_VIEW`

3. *(Sprint 4 Expansion)* `POST /api/v1/exercises/{exercise_id}/ocr/jobs`
   - **Summary:** Asynchronous background OCR processing for large scanned PDF/image documents with job progress status polling.

---

### Schema Changes & Models

1. **`models/models.py` (`Question` model):**
   - `content = Column(Text, nullable=False)` (Default primary question stem)
   - `content_markdown = Column(Text, nullable=True)` (Formatted plain Markdown with converted Unicode math expressions)
   - `content_latex = Column(Text, nullable=True)` (Raw text containing standard LaTeX math expressions)
   - `image_url = Column(String(500), nullable=True)` (Extracted figure URL)
   - `difficulty = Column(String(20), nullable=True)` (Optional `NhanBiet`, `ThongHieu`, `VanDung` or `None`)
   - `status = Column(String(20), default='ACTIVE', nullable=False)` (Soft delete support)

2. **`app/modules/exercise/schemas.py` (`QuestionTypeEnum` & Question Schemas):**
   - `QuestionTypeEnum`: `MultipleChoice`, `TrueFalse`, `ShortAnswer`
   - `QuestionCreate` / `QuestionUpdate` / `QuestionOut`: Includes `content_markdown`, `content_latex`, `image_url`, `difficulty`, `answer_options`.

3. **`ImportParserService` (`app/modules/exercise/services/import_parser_service.py`):**
   - `extract_docx_content(file_bytes)`: Extracts text, OMML math formulas (`<m:oMath>`), tables, and inline images.
   - `extract_pdf_content(file_bytes)`: Uses `marker-pdf` / `PyMuPDF` with fallback to `pdfplumber` for math formula extraction.
   - `convert_latex_to_markdown(raw_text)`: Scans `$ ... $` / `$$ ... $$` math blocks, converting LaTeX math notation (`\vec{v}`, `\frac{a}{b}`, exponents, subscripts, symbols) into clean Markdown Unicode representations.
   - `parse_questions(text, images)`: Parses Part 1, Part 2, Part 3 question blocks and populates `content_markdown` and `content_latex`.
   - `parse_answer_keys(text_or_tables, test_code)`: Parses Table Matrix (Mã đề) and Text List formats.
   - `merge_questions_and_answers(questions, answers)`: Validates and combines parsed questions with correct answers.

---

## Changelog

| Version | Date | Author | Thay đổi |
|---|---|---|---|
| v1.0 | 2026-07-28 | Tam Khang | Khởi tạo spec cho Feature F-EXE-05 Import câu hỏi từ file docx/pdf |
| v2.0 | 2026-08-09 | Tam Khang | Cập nhật bổ sung trích xuất PDF qua marker-pdf/pdfplumber và quy tắc parse đáp án matrix |
| v2.1 | 2026-08-15 | Tam Khang | Bổ sung quy định nhận diện (detection) và quy đổi công thức toán LaTeX sang Markdown/Unicode, lưu trữ riêng 2 trường `content_markdown` & `content_latex` |
| v3.0 | 2026-08-16 | Tam Khang | Nâng cấp toàn diện kiến trúc OCR Math Document Pipeline: phân cấp Page $\rightarrow$ Block $\rightarrow$ Segment, nhận diện Mathematical Expression Recognition (MER), phân biệt Inline/Display Math, Bounding Box, Validation KaTeX & Confidence score, và Export đa định dạng |



