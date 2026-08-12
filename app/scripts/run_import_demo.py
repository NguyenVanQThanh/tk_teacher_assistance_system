# File Name: run_import_demo.py
# Description: Demo script to run ImportParserService on sample_template_bgd.docx and display parsed output.
# Created At: 2026-08-09
# Created By: Tam Khang
# Updated At: 2026-08-09
# Updated By: Tam Khang

import json
import os
import sys

# Ensure UTF-8 output on Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.modules.exercise.services.import_parser_service import ImportParserService

def main():
    file_path = "sample_template_bgd.docx"
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found.")
        return

    with open(file_path, "rb") as f:
        file_bytes = f.read()

    print(f"--- Running ImportParserService on {file_path} ---")
    result = ImportParserService.parse_document(
        file_bytes=file_bytes,
        filename=file_path,
        answer_file_bytes=None,
        answer_filename=None,
        test_code="0121"
    )

    if result.errors:
        print("\n[ERRORS ENCOUNTERED]:")
        for err in result.errors:
            print(f"- Question {err.question_number}: {err.message}")

    print(f"\n[PARSED QUESTIONS SUCCESS] (Total: {len(result.questions)} questions)")
    for q in result.questions:
        print("=" * 60)
        print(f"Câu {q.question_number} | Part: {q.part} | Type: {q.question_type.value} | Difficulty: {q.difficulty.value if q.difficulty else 'None'}")
        print(f"Nội dung: {q.content}")
        if q.image_url:
            print(f"Image URL: {q.image_url}")
        if q.correct_answer:
            print(f"Đáp án ngắn: {q.correct_answer}")

        if q.answer_options:
            print("Lựa chọn / Các ý:")
            for opt in q.answer_options:
                correct_str = "[ĐÚNG / TRUE]" if opt.is_correct else "[SAI / FALSE]"
                print(f"  - {opt.content}  --> {correct_str}")

if __name__ == "__main__":
    main()
