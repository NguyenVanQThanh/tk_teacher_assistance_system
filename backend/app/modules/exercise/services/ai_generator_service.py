# File Name: ai_generator_service.py
# Description: Service for generating AI exercises and question sets with LLM or curriculum fallback.
# Created At: 2026-10-03
# Created By: Tam Khang
# Updated At: 2026-10-03
# Updated By: Tam Khang

import os
import json
import logging
from typing import List, Dict, Any, Optional

from app.modules.exercise.services.gemini_vision_parser_service import GeminiVisionParserService

logger = logging.getLogger("smartlms.exercise.ai_generator")


class AiExerciseGeneratorService:
    """Service generating authentic educational questions for AI exercises."""

    @classmethod
    def generate_questions(
        cls,
        subject_name: str,
        grade_name: str,
        topic_prompt: str,
        part1_count: int,
        part2_count: int,
        part3_count: int,
        context: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Generates Part1 (MultipleChoice), Part2 (TrueFalse) and Part3 (ShortAnswer) questions with Gemini,
        grounded on the retrieved textbook/teacher context.
        Raises RuntimeError on failure: placeholder questions are never fabricated.
        """
        api_key = GeminiVisionParserService.get_api_key()
        if not api_key:
            raise RuntimeError("AI generation is not configured (missing API key).")
        total = part1_count + part2_count + part3_count
        try:
            questions = cls._call_gemini_generator(
                api_key=api_key,
                subject_name=subject_name,
                grade_name=grade_name,
                topic_prompt=topic_prompt,
                part1_count=part1_count,
                part2_count=part2_count,
                part3_count=part3_count,
                context=context,
            )
        except Exception as e:
            logger.error("Gemini AI generation failed: %s", e)
            raise RuntimeError("AI generation failed.") from e
        if not questions or len(questions) < total:
            raise RuntimeError("AI returned fewer questions than requested.")
        return questions

    @classmethod
    def _call_gemini_generator(
        cls,
        api_key: str,
        subject_name: str,
        grade_name: str,
        topic_prompt: str,
        part1_count: int,
        part2_count: int,
        part3_count: int,
        context: str = ""
    ) -> List[Dict[str, Any]]:
        """Calls Gemini API to create structured questions in JSON format."""
        from google import genai
        from google.genai import types

        model_name = GeminiVisionParserService.get_model_name()
        client = genai.Client(api_key=api_key)

        system_instruction = (
            "Bạn là chuyên gia ra đề thi chuẩn của Bộ Giáo dục và Đào tạo Việt Nam. "
            "Nhiệm vụ của bạn là tạo các câu hỏi trắc nghiệm chất lượng cao, đúng định dạng và bám sát chủ đề yêu cầu. "
            "Cần đảm bảo công thức Toán / Khoa học tự nhiên được định dạng bằng cú pháp LaTeX chuẩn bọc trong dấu $. "
            "Trả về kết quả dưới dạng JSON thuần túy theo schema yêu cầu."
        )

        ctx_block = ""
        if context:
            ctx_block = (
                "Tài liệu tham khảo (nguồn tin cậy, đã gắn nhãn). Câu hỏi PHẢI bám sát nội dung này. "
                "[SGK ...] là sách giáo khoa (ưu tiên), [GV ...] là tài liệu giáo viên (bổ sung). "
                "Chỉ dùng LÝ THUYẾT, định nghĩa, tính chất, ví dụ trong SGK để tự biên soạn câu hỏi MỚI; "
                "KHÔNG sao chép, diễn đạt lại hay mô phỏng câu hỏi/đề thi/ma trận đề có trong tài liệu. "
                "Không bịa kiến thức ngoài tài liệu; thêm trường source_ref là nhãn nguồn đã dùng.\n"
                f"<tai_lieu>\n{context}\n</tai_lieu>\n\n"
            )
        user_prompt = f"""{ctx_block}Tạo đề luyện tập môn {subject_name} ({grade_name}) theo chủ đề: "{topic_prompt}".
Yêu cầu số lượng câu hỏi chính xác:
- Phần 1 (Part1): Đúng {part1_count} câu trắc nghiệm nhiều lựa chọn (MultipleChoice), mỗi câu gồm 4 phương án A, B, C, D và đúng 1 phương án đúng (is_correct=true).
- Phần 2 (Part2): Đúng {part2_count} câu trắc nghiệm Đúng/Sai (TrueFalse), mỗi câu gồm 1 nội dung dẫn và 4 ý a, b, c, d với trường segments là mảng gồm 4 item {{"key": "a", "statement": "...", "is_correct": bool}}.
- Phần 3 (Part3): Đúng {part3_count} câu trắc nghiệm Trả lời ngắn (ShortAnswer), có trường correct_answer là đáp án số hoặc từ khóa ngắn.

Schema JSON:
{{
  "questions": [
    {{
      "part": "Part1",
      "question_type": "MultipleChoice",
      "difficulty": "NhanBiet",
      "source_ref": "Nhãn nguồn đã dùng (tuỳ chọn), vd: SGK Hóa học 12 tr.14",
      "content": "Nội dung câu hỏi...",
      "explanation": "Giải thích chi tiết...",
      "answer_options": [
        {{"content": "Phương án A", "is_correct": false, "display_order": 0}},
        {{"content": "Phương án B", "is_correct": true, "display_order": 1}},
        {{"content": "Phương án C", "is_correct": false, "display_order": 2}},
        {{"content": "Phương án D", "is_correct": false, "display_order": 3}}
      ]
    }}
  ]
}}
"""

        response = client.models.generate_content(
            model=model_name,
            contents=[user_prompt],
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                temperature=0.7,
                max_output_tokens=8192,
            )
        )

        raw_text = response.text or ""
        data = json.loads(raw_text)
        return data.get("questions", [])
