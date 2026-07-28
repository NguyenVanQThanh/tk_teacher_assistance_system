> Path: `docs/tasks/f_exe_05/f_exe_05_question_import.md`
> Slice: `SL-EXE-05` · Type: `feature` · Size: `medium` · SP: `3`
> Depends on: `F-EXE-01`
> Status: `draft`
> Created At: `2026-07-28`
> Updated At: `2026-07-28`

# Task — `F-EXE-05` Question Import (Nhập câu hỏi từ file docx/pdf theo template)

**Author:** AI Agent
**Updated By:** AI Agent

## Mô tả Task
Triển khai import hàng loạt câu hỏi từ file `.docx`/`.pdf` theo template cố định (regex, không AI):
1. Thêm dependency `python-docx`, `pdfplumber` vào `requirements.txt`.
2. `ImportParserService.extract_text(file, content_type)` — đọc text thuần từ `.docx`/`.pdf`.
3. `ImportParserService.parse_questions(text)` — regex tách theo `Câu N.`, parse `[NB]/[TH]/[VD]`, `[TU]`, đáp án `*A./B./...`, dòng `Đáp án:` — trả về `list[ParsedQuestion]` hoặc `list[ParseError]` (all-or-nothing, không câu nào insert nếu có 1 câu lỗi).
4. API Router: `POST /api/v1/exercises/{exercise_id}/questions/import` (multipart) — validate file type/size, gọi parser, nếu hợp lệ thì lặp gọi `QuestionService.add_question()` (tái dùng nguyên vẹn từ F-EXE-01) trong 1 transaction.
5. Seed permission mới `EXE_QUESTION_IMPORT` — map role Teacher + Admin.
6. Unit tests cho parser (đủ 6 AC trong spec) + integration test cho endpoint.

## Technical Workflow

```
Bước 1: Dependencies
  └── requirements.txt: python-docx, pdfplumber

Bước 2: Parser Service
  └── app/modules/exercise/services/import_parser_service.py:
        extract_text(file, content_type) -> str
        parse_questions(text) -> ParseResult(questions=[...], errors=[...])

Bước 3: API Router
  └── app/modules/exercise/routers/questions.py: import_questions endpoint
        - Kiểm tra content_type (.docx/.pdf), size limit
        - Gọi parser -> nếu errors không rỗng: raise 422 ERR-EXE-IMPORT_INVALID_QUESTION (toàn bộ error list)
        - Nếu hợp lệ: for each parsed question -> QuestionService.add_question() trong cùng transaction

Bước 4: Seed Permissions
  └── app/scripts/seed.py: thêm EXE_QUESTION_IMPORT (Teacher, Admin)

Bước 5: Automated Testing Verification
  └── tests/exercise/unit/test_import_parser_service.py: test_parse_valid_docx, test_parse_missing_correct_answer,
        test_parse_multiple_correct_answers, test_parse_missing_dap_an_for_tu, test_unsupported_file_type,
        test_unreadable_pdf_no_text_layer
  └── tests/exercise/integration/test_question_import.py: full endpoint flow -> Pass 100%
```

## Kết quả kiểm thử
- (chưa thực thi — task ở trạng thái `draft`, cập nhật khi triển khai xong)
