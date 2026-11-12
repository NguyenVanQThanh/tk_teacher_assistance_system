File Name: bugfix_test_font_cross_platform.md
Created At: 2026-11-13
Created By: AI Agent
Updated At: 2026-11-13
Updated By: AI Agent

### Summary
Fixed 20 failing exercise unit tests on Linux CI (merge feat/rag-sgk into dev) caused by a hardcoded Windows font path.

### Feature Specifications
N/A (test-only fix).

### Bug & Feature Context
- Tests built PDFs/images with `C:/Windows/Fonts/arial.ttf`.
- On GitHub Actions (ubuntu) the file does not exist: `FzErrorSystem: cannot open ...arial.ttf` (pymupdf) and `OSError: cannot open resource` (PIL).
- Affected: exam_sequence, exam_structure, figure_detection, figure_scan, part_relabel, skeleton_match tests.

### Solution & Technical Details
- New helper `backend/tests/exercise/unit/_font.py` exposing `FONT`: first existing of Windows Arial, Linux DejaVu/Liberation, macOS Arial, else matplotlib bundled `DejaVuSans.ttf` (matplotlib is in requirements.txt).
- Replaced hardcoded path in test_exam_structure, test_part_relabel, test_question_regions, test_skeleton_match, test_figure_scan, test_figure_detection.
- Local result: 157 passed in tests/exercise/unit.
