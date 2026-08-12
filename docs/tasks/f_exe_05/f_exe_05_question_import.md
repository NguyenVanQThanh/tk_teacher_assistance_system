> Path: `docs/tasks/f_exe_05/f_exe_05_question_import.md`
> Slice: `SL-EXE-05` · Type: `feature` · Size: `medium` · SP: `3`
> Depends on: `F-EXE-01`
> Status: `ready to test`
> Created At: `2026-07-28`
> Updated At: `2026-08-09`



# Task — `F-EXE-05` Question Import (Nhập câu hỏi từ file docx/pdf theo template + File đáp án)

**Author:** Tam Khang
**Updated By:** Tam Khang

## Mô tả Task
Triển khai import hàng loạt câu hỏi từ file `.docx`/`.pdf` theo template đề thi Bộ GD&ĐT (regex/matrix, không AI):
1. Thêm dependency `python-docx`, `pdfplumber`, `python-multipart` vào `requirements.txt`.
2. Database Schema: Bổ sung cờ `TrueFalse` trong `QuestionTypeEnum` và cột `image_url` (nullable) vào bảng `questions` + model mapping.
3. `ImportParserService.extract_docx_content` / `extract_pdf_content` — trích xuất text thuần, bảng biểu và tệp hình ảnh đính kèm từ `.docx`/`.pdf`.
4. `ImportParserService.parse_questions(text, images)` — regex tách theo `Câu N.`, parse 3 phần (Phần I MCQ, Phần II Đúng/Sai, Phần III Trả lời ngắn), parse tag `[NB]/[TH]/[VD]` (nếu thiếu -> `None`), tách các lựa chọn với nhãn `A.`, `A)`, `A/`... và gán tệp ảnh `image_url`.
5. `ImportParserService.parse_answer_keys(text_or_tables, test_code)` — parse 3 dạng đáp án: Bảng matrix đáp án nhiều mã đề (Mã đề 0121, 0122...), Bảng đáp án 1 mã đề duy nhất (`Câu` | `Đáp án`), và Dạng danh sách dòng (`1. A`, `1. a) Đ, b) S...`, `1. 450`).
6. `ImportParserService.merge_questions_and_answers(questions, answers)` — ghép câu hỏi và đáp án đúng, validate toàn bộ (all-or-nothing, trả về error list nếu có câu sai).
7. API Router: `POST /api/v1/exercises/{exercise_id}/questions/import` (multipart: `question_file`, optional `answer_file`, optional `test_code`).
8. Seed permission mới `EXE_QUESTION_IMPORT` — map role Teacher + Admin.
9. Unit tests & Integration tests cho parser và endpoint (100% passed).

## Technical Workflow

```
Bước 1: Database & Dependencies
  └── requirements.txt: python-docx, pdfplumber, python-multipart
  └── models/models.py: add image_url to Question model
  └── schemas.py: add TrueFalse to QuestionTypeEnum, add image_url to schemas

Bước 2: Parser Service
  └── app/modules/exercise/services/import_parser_service.py:
        extract_docx_content / extract_pdf_content -> (text, tables, images)
        parse_questions(text, images) -> ParsedQuestions
        parse_answer_keys(text_or_tables, test_code) -> ParsedAnswers
        merge_questions_and_answers(...) -> Result(questions=[...], errors=[...])

Bước 3: API Router
  └── app/modules/exercise/routers/exercises.py: import_questions endpoint
        - Kiểm tra content_type (.docx/.pdf), size limit
        - Gọi parser -> nếu errors không rỗng: raise 422 ERR-EXE-IMPORT_INVALID_QUESTION (toàn bộ error list)
        - Nếu hợp lệ: for each parsed question -> QuestionService.add_question() trong cùng transaction

Bước 4: Seed Permissions
  └── app/scripts/seed.py: thêm EXE_QUESTION_IMPORT (Teacher, Admin)

Bước 5: Automated Testing Verification
  └── tests/exercise/unit/test_import_parser_service.py: unit test 3 phần câu hỏi, optional difficulty (None),
        đáp án bảng matrix mã đề, bảng 1 mã đề, đáp án danh sách dòng, trích xuất hình ảnh.
  └── tests/exercise/test_question_import.py: full endpoint flow -> Pass 100%
```

## Kết quả kiểm thử
- `pytest tests/exercise/unit/test_import_parser_service.py` -> 9/9 passed.
- `pytest tests/exercise/test_question_import.py` -> 2/2 passed.
- `pytest` (Toàn bộ suite 136 tests) -> 136/136 passed (100%).


