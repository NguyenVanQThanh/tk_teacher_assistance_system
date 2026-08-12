# Feature Spec — `F-EXE-05` Question Import (Nhập câu hỏi từ file docx/pdf theo template + File đáp án)

> Path: `docs/v_1/specs/f_exe_05_question_import_spec.md` · Sprint: [sprint_2_overview.md](../sprints/sprint_2_overview.md)
> Created At: `2026-07-28`
> Created By: `Tam Khang`
> Updated At: `2026-08-09`
> Updated By: `Tam Khang`

---

## Document Header

| Field | Giá trị |
|---|---|
| Feature ID | `F-EXE-05` |
| Feature name | Question Import — Nhập hàng loạt câu hỏi từ file `.docx`/`.pdf` theo template cố định + File/Phần đáp án |
| Module(s) | `exercise` |
| Sprint(s) allocated | `SPRINT-02` |
| Lane | `standard` |
| Spec version | `v2.0` |
| Last updated | `2026-08-09` |
| Source binding | `f_exe_01_exercises_spec.md` (`QuestionService.add_question` được tái dùng) · `.claude/rules/coding_rules.md` |

---

# PART A — Business

> **Owner:** Tam Khang · **Gate:** G3

## A.1 Feature Summary

Cho phép **Giáo viên** tải lên tệp đề thi (`.docx` hoặc `.pdf`) và/hoặc tệp đáp án đi kèm (hoặc phần đáp án ở cuối tệp đề thi) soạn theo chuẩn cấu trúc đề thi THPT QG của Bộ GD&ĐT để nhập hàng loạt câu hỏi + đáp án vào một đề bài (`exercise`) đã tồn tại.

Parser đọc text và bảng biểu theo pattern regex/matrix, trích xuất cả **hình ảnh minh họa** đính kèm trong câu hỏi. Parser **không** dùng AI/NLP. File không đúng cú pháp → từ chối toàn bộ (all-or-nothing), kèm danh sách lỗi cụ thể theo từng câu để GV sửa và import lại.

## A.2 Quy tắc Template & Cú pháp bắt buộc

### 1. Tag Mức độ khó (Difficulty Tags)
- `[NB]`: Nhận biết (`NhanBiet`)
- `[TH]`: Thông hiểu (`ThongHieu`)
- `[VD]`: Vận dụng (`VanDung`)
- **Quy tắc:** Nếu **không** gắn tag độ khó ở đầu câu, hệ thống mặc định để **trống (`None` / null)**.

### 2. Ba phần / loại câu hỏi (Question Parts & Types)

File đề thi gồm 3 Phần chính:

- **Phần I: Trắc nghiệm 4 lựa chọn (`MultipleChoice`):**
  - Mỗii câu gồm 1 câu hỏi chính và 4 lựa chọn `A`, `B`, `C`, `D` hoặc `a`, `b`, `c`, `d`.
  - Ký tự phân cách sau nhãn đáp án: dấu chấm `.`, ngoặc đơn `)`, xược `/` (ví dụ: `A.`, `A)`, `A/`, `a.`, `a)`, `a/`).
  - Trong tệp đề thi **không** đánh dấu đáp án đúng (`*`).

- **Phần II: Trắc nghiệm Đúng / Sai (`TrueFalse`):**
  - Mỗi câu gồm 1 mệnh đề/câu hỏi chính và 4 ý/lựa chọn `A, B, C, D` hoặc `a, b, c, d` (hoặc `a)`, `b)`, `c)`, `d)`).
  - Ký tự phân cách sau nhãn: `.`, `)`, `/`.
  - Mỗi ý có trạng thái **Đúng** hoặc **Sai** (xác định qua tệp/phần đáp án).

- **Phần III: Trả lời ngắn (`ShortAnswer`):**
  - Mỗi câu gồm 1 nội dung câu hỏi chính (không có lựa chọn A/B/C/D).
  - Kết quả đáp án (số hoặc chuỗi trả lời ngắn) được xác định qua tệp/phần đáp án.

### 3. Ký hiệu Toán học & Chuẩn LaTeX (LaTeX Math Notation)
- Các công thức, ký hiệu toán học (phương trình, bất phương trình, căn thức, tích phân, hình học...) được khuyến khích viết theo chuẩn LaTeX dạng `$ ... $` (inline) hoặc `$$ ... $$` (display block).
- *Ví dụ:* `$y = f(x) = x^3 - 3x^2 + 2$`, `$\log_2(x - 1) < 3$`, `$SA = a\sqrt{2}$`, `$\frac{a^3\sqrt{2}}{3}$`.
- Parser giữ nguyên các chuỗi định dạng LaTeX để phục vụ hiển thị KaTeX / MathJax trên giao diện Web và App.

### 4. Hình ảnh mô tả câu hỏi (Question Embedded Images)
- Cả 3 phần đều hỗ trợ chèn hình ảnh minh họa trong tệp `.docx` (hoặc `.pdf`).
- Parser tự động trích xuất các hình ảnh thuộc block câu hỏi, lưu trữ và gắn URL hình ảnh (`image_url`) vào câu hỏi tương ứng.

### 5. Định dạng Tệp / Phần Đáp án (Answer Keys)

Đáp án được cung cấp qua phần đáp án ở cuối tệp đề hoặc tải tệp đáp án riêng. Hệ thống hỗ trợ 3 dạng trình bày đáp án:

#### Dạng 1: Bảng matrix đáp án (Table Matrix) cho nhiều Mã đề (VD: Mã đề 0121, 0122, ...)
- **Phần I (Trắc nghiệm 4 lựa chọn):** Bảng có cột `Câu`, các cột `Mã đề XXXX`. Tế bào chứa chữ cái đáp án đúng (`A`, `B`, `C`, `D`).
- **Phần II (Trắc nghiệm Đúng/Sai):** Bảng có cột `Câu`, các cột `Mã đề XXXX`. Mỗi tế bào chứa 4 ý: `a) Sai`, `b) Sai`, `c) Đúng`, `d) Đúng` (hoặc `a) Đ, b) S...`).
- **Phần III (Trả lời ngắn):** Bảng có cột `Câu`, các cột `Mã đề XXXX`. Mỗi tế bào chứa giá trị đáp án (VD: `450`, `0,66`, `1,5`, `-5`).

#### Dạng 2: Bảng đáp án chỉ cho 1 Mã đề (Single Test Code Table)
- **Cấu trúc:** Bảng gồm cột `Câu` (hoặc `STT`) và cột `Đáp án` (hoặc tiêu đề tên Mã đề duy nhất).
- **Phần I:** Tế bào tương ứng từng câu chứa nhãn đáp án đúng (`A`, `B`, `C`, `D`).
- **Phần II:** Tế bào chứa 4 ý Đúng/Sai (VD: `a) Đúng, b) Sai, c) Đúng, d) Sai` hoặc `a) Đ, b) S...`).
- **Phần III:** Tế bào chứa giá trị trả lời ngắn (VD: `450`, `0,66`, `1,5`).

#### Dạng 3: Dạng danh sách dòng chữ (Text List Format)
- **Phần I:** `1. A` hoặc `1.A` hoặc `1: A` hoặc `Câu 1: A`.
- **Phần II:** `1. a) Đ, b) S, c) Đ, d) S` hoặc `1. a) Đúng, b) Sai, c) Đúng, d) Sai` hoặc viết thành các dòng `a) Đúng`, `b) Sai`...
- **Phần III:** `1. 450` hoặc `1. 0,66` hoặc `Câu 1: 450`.

## A.3 User Stories

| Story ID | As (role) | I want (capability) | So that (value) |
|---|---|---|---|
| US-01 | Teacher | tải lên file đề thi + file đáp án (bảng mã đề hoặc danh sách) dạng `.docx`/`.pdf` | nhập hàng loạt câu hỏi cả 3 phần theo chuẩn đề thi Bộ GD&ĐT |
| US-02 | Teacher | hệ thống trích xuất tự động hình ảnh đính kèm trong câu hỏi | không cần cắt ảnh và upload thủ công từng câu |
| US-03 | Teacher | nhận thông báo lỗi chi tiết theo từng câu/dòng nếu file sai cú pháp | dễ dàng kiểm tra và sửa lỗi trước khi import lại |

## A.4 Business Workflow

```
[Client Request: POST /api/v1/exercises/{exercise_id}/questions/import]
 (multipart form-data: question_file, optional answer_file, optional test_code)
       │
       ▼
 1. Authentication & Permission Check (EXE_QUESTION_IMPORT)
       │
       ▼
 2. File Validation (.docx / .pdf, max 10MB)
       │
       ▼
 3. Question Extraction & Regex Parsing
    ├── Extract text & embedded images from question_file
    ├── Separate sections: Part I (MCQ), Part II (TrueFalse), Part III (ShortAnswer)
    ├── Parse difficulty tags: [NB], [TH], [VD] -> None if missing
    └── Extract embedded image -> save file to upload storage -> get image_url
       │
       ▼
 4. Answer Key Parsing (Table Matrix or Text List)
    ├── If answer table matrix with multiple test codes (Mã đề): match selected test_code (default first code)
    ├── Map Part I answers (A/B/C/D) to Question choices
    ├── Map Part II answers (a, b, c, d True/False) to Question item options
    └── Map Part III answers (Short Answer string) to correct_answer
       │
       ▼
 5. Validation Check
    ├── If validation fails (missing answer for question, invalid option...) -> return 422 with full error list
    └── All-or-nothing: NO database insertion if any question is invalid
       │
       ▼
 6. Save to Database in single Transaction
    └── Loop call QuestionService.add_question() -> update exercise.total_questions -> return list[QuestionOut]
```

## A.5 Acceptance Criteria

| AC ID | REQ | Given | When | Then |
|---|---|---|---|---|
| AC-01 | REQ-EXE-041 | File `.docx` gồm cả 3 phần + Bảng đáp án hợp lệ | `POST .../questions/import` | 201 Created, trả về danh sách `QuestionOut` có `question_type` chuẩn |
| AC-02 | REQ-EXE-041 | Câu hỏi không gắn tag `[NB]`/`[TH]`/`[VD]` | `POST .../questions/import` | 201 Created, câu hỏi được lưu với `difficulty = None` |
| AC-03 | REQ-EXE-041 | Câu hỏi có chứa hình ảnh minh họa trong tệp `.docx` | `POST .../questions/import` | 201 Created, hình ảnh được trích xuất và gán vào `image_url` |
| AC-04 | REQ-EXE-042 | Bảng đáp án có nhiều Mã đề (0121, 0122...) và client chọn `test_code=0121` | `POST .../questions/import` | 201 Created, đáp án của Mã đề 0121 được áp dụng cho đề |
| AC-05 | REQ-EXE-042 | File đề thi thiếu đáp án cho 1 câu ở Phần II | `POST .../questions/import` | 422 `ERR-EXE-IMPORT_INVALID_QUESTION`, không insert bất kỳ câu nào |
| AC-06 | REQ-EXE-041 | File `.txt` hoặc định dạng không được hỗ trợ | `POST .../questions/import` | 415 `ERR-EXE-IMPORT_FILE_TYPE_UNSUPPORTED` |

---

# PART B — Architecture & API Design

> **Owner:** Tam Khang · **Gate:** G4

### Endpoints

1. `POST /api/v1/exercises/{exercise_id}/questions/import`
   - **Content-Type:** `multipart/form-data`
   - **Form Parameters:**
     - `question_file`: UploadFile (required, `.docx` or `.pdf`)
     - `answer_file`: Optional[UploadFile] (optional separate answer key file)
     - `test_code`: Optional[str] (optional target test code, e.g. `"0121"`)
   - **Permissions:** `EXE_QUESTION_IMPORT`

### Schema Changes & Models

1. **`models/models.py` (`Question` model):**
   - Add `image_url = Column(String(500), nullable=True)`
   - `difficulty` allows `None`

2. **`app/modules/exercise/schemas.py` (`QuestionTypeEnum`):**
   - Add `TrueFalse = "TrueFalse"` to `QuestionTypeEnum`
   - Add `image_url: Optional[str] = None` to `QuestionCreate`, `QuestionUpdate`, `QuestionOut`

3. **`ImportParserService` (`app/modules/exercise/services/import_parser_service.py`):**
   - `extract_text_and_images(file)`: Reads docx paragraphs/tables and saves inline BLOB images.
   - `extract_pdf_content(file_bytes)`: Uses `marker-pdf` (with fallback to `pdfplumber`) to convert PDF documents into Markdown with embedded LaTeX math formulas (`$ ... $`). Reads device setting dynamically from environment variable `TORCH_DEVICE` (`cpu` / `cuda`).
   - `parse_questions(text, images)`: Parses Part 1, Part 2, Part 3 question blocks.
   - `parse_answer_keys(text_or_tables, test_code)`: Parses Table Matrix (Mã đề) and Text List formats.
   - `merge_questions_and_answers(questions, answers)`: Validates and combines parsed questions with correct answers.


