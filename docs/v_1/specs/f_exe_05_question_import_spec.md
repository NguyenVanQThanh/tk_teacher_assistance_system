# Feature Spec — `F-EXE-05` Question Import (Nhập câu hỏi từ file docx/pdf theo template)

> Path: `docs/v_1/specs/f_exe_05_question_import_spec.md` · Sprint: [sprint_2_overview.md](../sprints/sprint_2_overview.md)
> Created At: `2026-07-28`
> Created By: `AI Agent`
> Updated At: `2026-07-28`
> Updated By: `AI Agent`

---

## Document Header

| Field | Giá trị |
|---|---|
| Feature ID | `F-EXE-05` |
| Feature name | Question Import — Nhập hàng loạt câu hỏi từ file `.docx`/`.pdf` theo template cố định |
| Module(s) | `exercise` |
| Sprint(s) allocated | `SPRINT-02` |
| Lane | `standard` |
| Spec version | `v1.0` |
| Last updated | `2026-07-28` |
| Source binding | `f_exe_01_exercises_spec.md` (`QuestionService.add_question` được tái dùng) · `.claude/rules/coding_rules.md` |

---

# PART A — Business

> **Owner:** AI Agent · **Gate:** G3

## A.1 Feature Summary

Cho phép **Giáo viên** tải lên 1 file `.docx` hoặc `.pdf` soạn theo **template cố định** (không phải AI hiểu file tự do) để nhập hàng loạt câu hỏi + đáp án vào 1 đề (`exercise`) đã tồn tại, thay vì gọi API thêm từng câu một. Parser đọc text theo pattern regex, **không** dùng AI/NLP. File không đúng cú pháp → từ chối toàn bộ (all-or-nothing), kèm danh sách lỗi cụ thể theo từng câu để GV sửa và import lại.

> **Ranh giới rõ với Sprint 4 (AI Generation):** feature này không "hiểu" nội dung tài liệu — chỉ regex-parse một cú pháp đánh dấu câu hỏi/đáp án đã quy định trước. Upload tài liệu giáo án tự do rồi để AI tự tách câu hỏi là phạm vi `documents` + AI Generation, không thuộc đây.

## A.2 Template cú pháp bắt buộc

**`.docx` / `.pdf` (văn bản thuần, không cần format đặc biệt ngoài các dấu hiệu dưới):**

```
Câu 1. [NB] 2 + 2 x 3 bằng bao nhiêu?
*A. 8
B. 12
C. 6
D. 10

Câu 2. [TH] Nghiệm của phương trình x + 5 = 0 là?
*A. x = -5
B. x = 5

Câu 3. [VD] [TU] Trình bày cách giải phương trình bậc nhất một ẩn.
Đáp án: Chuyển vế, quy đồng, rút gọn ẩn số.
```

Quy ước:
- `Câu N.` mở đầu mỗi câu (N là số thứ tự, chỉ dùng xác định ranh giới câu, không lưu vào DB).
- `[NB]`/`[TH]`/`[VD]` ngay sau số câu → map `difficulty` = `NhanBiet`/`ThongHieu`/`VanDung`. Thiếu tag → mặc định `NhanBiet`.
- Có `[TU]` → câu tự luận (`ShortAnswer`), dòng `Đáp án: ...` bắt buộc → map `correct_answer`. Không có `[TU]` → mặc định trắc nghiệm (`MultipleChoice`).
- Trắc nghiệm: các dòng `A.`/`B.`/`C.`/`D.` là đáp án; dấu `*` đầu dòng đánh dấu đáp án đúng — **bắt buộc đúng 1 dấu `*`** trong 1 câu, tối thiểu 2 đáp án.
- Câu cách nhau bằng dòng trống.

## A.3 User Stories

| Story ID | As (role) | I want (capability) | So that (value) |
|---|---|---|---|
| US-01 | Teacher | tải lên file `.docx`/`.pdf` soạn sẵn nhiều câu hỏi | không phải gọi API thêm từng câu một, tiết kiệm thời gian |
| US-02 | Teacher | nhận thông báo lỗi rõ ràng theo từng câu nếu file sai định dạng | sửa đúng chỗ sai và import lại nhanh |

## A.4 Business Workflow

```
[Client Request: POST /api/v1/exercises/{exercise_id}/questions/import, multipart file]
       │
       ▼
 1. Authentication & Permission Check
    └── Yêu cầu quyền EXE_QUESTION_IMPORT (map role Teacher) + exercise thuộc quyền GV (scoping như F-EXE-01)
       │
       ▼
 2. File Type & Size Validation
    ├── Chỉ chấp nhận .docx (python-docx) hoặc .pdf (pypdf/pdfplumber) -> Raise 415 ERR-EXE-IMPORT_FILE_TYPE_UNSUPPORTED
    └── Giới hạn kích thước file (config, mặc định 5MB) -> Raise 413 nếu vượt
       │
       ▼
 3. Text Extraction & Regex Parsing
    ├── Trích xuất toàn bộ text thuần từ file
    ├── Tách theo pattern "Câu N." thành từng block câu hỏi
    └── Với mỗi block: parse difficulty tag, question_type tag, nội dung, đáp án/đáp án đúng
       │
       ▼
 4. Validate từng câu (dùng lại rule của QuestionCreate ở F-EXE-01)
    ├── Câu nào sai (thiếu *, nhiều hơn 1 *, thiếu Đáp án: cho ShortAnswer, <2 đáp án...) -> ghi vào error_list kèm số thứ tự câu
    └── Nếu error_list không rỗng -> Raise 422 ERR-EXE-IMPORT_INVALID_QUESTION, trả về toàn bộ error_list, KHÔNG insert bất kỳ câu nào
       │
       ▼
 5. Nếu toàn bộ hợp lệ: Gọi QuestionService.add_question() cho từng câu trong 1 transaction DB duy nhất
       │
       ▼
 6. Output: danh sách QuestionOut vừa tạo (kèm question_id, answer_option_id)
```

## A.5 Acceptance Criteria

| AC ID | REQ | Given | When | Then |
|---|---|---|---|---|
| AC-01 | REQ-EXE-041 | File `.docx` đúng template, 3 câu hợp lệ | `POST .../questions/import` | 201, trả về 3 `QuestionOut` |
| AC-02 | REQ-EXE-041 | File `.txt` hoặc `.xlsx` | `POST .../questions/import` | 415 `ERR-EXE-IMPORT_FILE_TYPE_UNSUPPORTED` |
| AC-03 | REQ-EXE-042 | File có 1 câu trắc nghiệm không đánh dấu `*` đáp án đúng nào | `POST .../questions/import` | 422 `ERR-EXE-IMPORT_INVALID_QUESTION`, không câu nào được insert (kể cả câu hợp lệ khác trong cùng file) |
| AC-04 | REQ-EXE-042 | File có câu `[TU]` nhưng thiếu dòng `Đáp án:` | `POST .../questions/import` | 422 `ERR-EXE-IMPORT_INVALID_QUESTION` |
| AC-05 | REQ-EXE-043 | File `.pdf` rỗng hoặc không trích xuất được text (file ảnh scan) | `POST .../questions/import` | 422 `ERR-EXE-IMPORT_PARSE_FAILED` |
| AC-06 | REQ-EXE-041 | Teacher import vào exercise không thuộc quyền mình (không dạy môn đó) | `POST .../questions/import` | 404 `ERR-EXE-EXERCISE_NOT_FOUND` (ẩn tồn tại, nhất quán với F-EXE-01 AC-05) |

## A.6 Out of Scope

- OCR cho PDF ảnh scan (không có text layer) — không hỗ trợ, trả lỗi `ERR-EXE-IMPORT_PARSE_FAILED`.
- Tự nhận diện câu hỏi trong file không theo template (dùng AI/NLP) — thuộc Sprint 4 AI Generation.
- Import từ Excel/CSV — chưa có nhu cầu, thêm khi có yêu cầu thực tế.

---

# PART B — Architecture & API Design

> **Owner:** AI Agent · **Gate:** G4

### Endpoints

1. `POST /api/v1/exercises/{exercise_id}/questions/import`: Nhập hàng loạt câu hỏi (multipart/form-data, field `file`). Yêu cầu `EXE_QUESTION_IMPORT`.

### Kiến trúc

```
Router (questions.py: import_questions)
   └── ImportParserService (app/modules/exercise/services/import_parser_service.py)
         ├── extract_text(file, content_type) — python-docx / pdfplumber
         └── parse_questions(text) -> list[ParsedQuestion] | list[ParseError]
   └── QuestionService.add_question() — tái dùng nguyên vẹn từ F-EXE-01, không viết logic tạo câu hỏi mới
```

### Dependencies mới

| Thư viện | Mục đích | Ghi chú |
|---|---|---|
| `python-docx` | Đọc text từ `.docx` | Thêm vào `requirements.txt` |
| `pdfplumber` | Đọc text từ `.pdf` | Thêm vào `requirements.txt`; chỉ đọc text layer, không OCR |

### Database Boundary

Không có bảng mới — chỉ ghi vào `questions`/`answer_options` đã tạo ở `F-EXE-01`, qua đúng service layer đã có (tránh trùng logic validate).
