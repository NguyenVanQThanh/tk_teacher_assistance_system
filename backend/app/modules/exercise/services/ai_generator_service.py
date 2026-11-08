# File Name: ai_generator_service.py
# Description: Service for generating AI exercises and question sets with LLM or curriculum fallback.
# Created At: 2026-10-03
# Created By: Tam Khang
# Updated At: 2026-10-03
# Updated By: Tam Khang

import os
import json
import re
import logging
from typing import List, Dict, Any, Optional

from app.modules.exercise.services.gemini_vision_parser_service import GeminiVisionParserService

logger = logging.getLogger("smartlms.exercise.ai_generator")


class AiExerciseGeneratorService:
    """Service generating authentic educational questions for AI exercises."""

    # Tỷ lệ phân bố cấp độ nhận thức cho mỗi phần: 40% Nhận biết, 40% Thông hiểu, 20% Vận dụng
    DIFFICULTY_RATIO = {"NhanBiet": 0.4, "ThongHieu": 0.4, "VanDung": 0.2}

    @classmethod
    def _difficulty_plan(cls, count: int) -> Dict[str, int]:
        """Số câu mỗi cấp độ nhận thức cho một phần có tổng `count` câu (40/40/20)."""
        if count <= 0:
            return {"NhanBiet": 0, "ThongHieu": 0, "VanDung": 0}
        nb = max(1, round(count * cls.DIFFICULTY_RATIO["NhanBiet"]))
        th = max(1, round(count * cls.DIFFICULTY_RATIO["ThongHieu"])) if count >= 2 else 0
        if nb + th > count:
            th = count - nb
        return {"NhanBiet": nb, "ThongHieu": th, "VanDung": count - nb - th}

    # Map cấp độ ở ma trận frontend (know/comp/app) sang mã backend
    LEVEL_KEY_MAP = {"know": "NhanBiet", "comp": "ThongHieu", "app": "VanDung"}

    @classmethod
    def _levels_to_plan(cls, levels, count):
        """Chuyển ma trận cấp độ người dùng chọn ({know, comp, app}) thành plan cho một phần.
        Nếu không có ma trận thì dùng phân bố mặc định 40/40/20."""
        if not levels:
            return cls._difficulty_plan(count)
        scaled = {level: max(0, int(levels.get(key) or 0)) for key, level in cls.LEVEL_KEY_MAP.items()}
        total = sum(scaled.values())
        if total <= 0:
            return cls._difficulty_plan(count)
        if count > 0 and total != count:
            # giữ đúng tổng số câu của phần: điều chỉnh phần dư/thiếu vào Vận dụng
            scaled["VanDung"] = max(0, scaled["VanDung"] + (count - total))
        return scaled

    @classmethod
    def _normalize_for_dedupe(cls, text: Any) -> str:
        """Chuẩn hóa nội dung để phát hiện câu trùng lặp (bỏ tiền tố 'Câu N:', chuẩn hóa dấu câu/khoảng trắng)."""
        if text is None:
            return ""
        t = re.sub(r"^\s*câu\s+\d+\s*[:\-–]?\s*", "", str(text), flags=re.IGNORECASE)
        t = re.sub(r"[^\w\s]", " ", t, flags=re.UNICODE)
        t = re.sub(r"\s+", " ", t.lower()).strip()
        return t

    @classmethod
    def _question_dedupe_key(cls, q: Dict[str, Any]) -> str:
        """Khóa dedupe: nội dung câu hỏi + các ý của câu Đúng/Sai (không tính thứ tự phương án)."""
        parts = [cls._normalize_for_dedupe(q.get("content", ""))]
        segments = q.get("segments") or []
        if segments:
            parts.append("|".join(cls._normalize_for_dedupe(s.get("statement", "")) for s in segments))
        return " || ".join(parts)

    @classmethod
    def _dedupe_questions(cls, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Loại bỏ các câu hỏi trùng lặp nội dung, giữ lại bản đầu tiên."""
        seen = set()
        unique: List[Dict[str, Any]] = []
        for q in questions:
            key = cls._question_dedupe_key(q)
            if key in seen:
                continue
            seen.add(key)
            unique.append(q)
        return unique

    @classmethod
    def _assign_difficulty_distribution(
        cls,
        questions: List[Dict[str, Any]],
        level_hints=None
    ) -> List[Dict[str, Any]]:
        """Gán cấp độ nhận thức cho từng phần: ưu tiên ma trận người dùng chọn (level_hints),
        nếu không có thì dùng phân bố mặc định 40/40/20 (Nhận biết/Thông hiểu/Vận dụng)."""
        by_part: Dict[str, List[Dict[str, Any]]] = {}
        for q in questions:
            by_part.setdefault(q.get("part") or "Part1", []).append(q)
        for part, part_questions in by_part.items():
            n = len(part_questions)
            hints = (level_hints or {}).get(part)
            plan = cls._levels_to_plan(hints, n) if hints else cls._difficulty_plan(n)
            idx = 0
            for level in ("NhanBiet", "ThongHieu", "VanDung"):
                for _ in range(plan.get(level, 0)):
                    if idx < n:
                        part_questions[idx]["difficulty"] = level
                        idx += 1
            # câu còn lại (nếu plan < n) gán Vận dụng
            while idx < n:
                part_questions[idx]["difficulty"] = "VanDung"
                idx += 1
        return questions

    @classmethod
    def generate_questions(
        cls,
        subject_name: str,
        grade_name: str,
        topic_prompt: str,
        part1_count: int,
        part2_count: int,
        part3_count: int,
        document_context: Optional[str] = None,
        part1_levels: Optional[Dict[str, int]] = None,
        part2_levels: Optional[Dict[str, int]] = None,
        part3_levels: Optional[Dict[str, int]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generates a list of question specifications with parts Part1 (MultipleChoice),
        Part2 (TrueFalse), and Part3 (ShortAnswer).
        Provider chain: Mistral là CHÍNH, Gemini fallback khi Mistral fail; cuối cùng mới tới bộ sinh theo chủ đề.
        """
        required_total = part1_count + part2_count + part3_count
        level_hints = {"Part1": part1_levels, "Part2": part2_levels, "Part3": part3_levels}

        # Chuỗi provider AI: Mistral là CHÍNH, Gemini fallback khi Mistral fail
        providers = []
        mistral_key, mistral_model, mistral_url = cls._get_mistral_config()
        if mistral_key:
            providers.append(("Mistral", lambda: cls._call_mistral_generator(
                api_key=mistral_key,
                model_name=mistral_model,
                api_url=mistral_url,
                subject_name=subject_name,
                grade_name=grade_name,
                topic_prompt=topic_prompt,
                part1_count=part1_count,
                part2_count=part2_count,
                part3_count=part3_count,
                document_context=document_context,
                part1_levels=part1_levels,
                part2_levels=part2_levels,
                part3_levels=part3_levels
            )))
        gemini_key = GeminiVisionParserService.get_api_key()
        if gemini_key:
            providers.append(("Gemini", lambda: cls._call_gemini_generator(
                api_key=gemini_key,
                subject_name=subject_name,
                grade_name=grade_name,
                topic_prompt=topic_prompt,
                part1_count=part1_count,
                part2_count=part2_count,
                part3_count=part3_count,
                document_context=document_context,
                part1_levels=part1_levels,
                part2_levels=part2_levels,
                part3_levels=part3_levels
            )))

        collected: List[Dict[str, Any]] = []
        seen = set()
        for provider_name, call in providers:
            try:
                ai_questions = call()
            except Exception as e:
                logger.warning(f"{provider_name} AI generation failed: {e}. Trying next provider/fallback.")
                continue
            if not ai_questions:
                continue
            # Loại bỏ các câu trùng lặp mà AI có thể sinh ra ở cả 3 phần
            for q in cls._dedupe_questions(ai_questions):
                key = cls._question_dedupe_key(q)
                if key not in seen:
                    seen.add(key)
                    collected.append(q)
            if len(collected) >= required_total:
                break

        if collected:
            # Bổ sung số câu còn thiếu từ bộ fallback, không trùng với câu AI đã sinh
            if len(collected) < required_total:
                for q in cls._dedupe_questions(cls._generate_curriculum_questions(
                    subject_name=subject_name,
                    grade_name=grade_name,
                    topic_prompt=topic_prompt,
                    part1_count=part1_count,
                    part2_count=part2_count,
                    part3_count=part3_count
                )):
                    if len(collected) >= required_total:
                        break
                    key = cls._question_dedupe_key(q)
                    if key not in seen:
                        seen.add(key)
                        collected.append(q)
            return cls._assign_difficulty_distribution(collected, level_hints)

        fallback_questions = cls._dedupe_questions(cls._generate_curriculum_questions(
            subject_name=subject_name,
            grade_name=grade_name,
            topic_prompt=topic_prompt,
            part1_count=part1_count,
            part2_count=part2_count,
            part3_count=part3_count
        ))
        return cls._assign_difficulty_distribution(fallback_questions, level_hints)

    @staticmethod
    def _get_mistral_config() -> tuple:
        """Đọc cấu hình Mistral (API key/model/url) từ biến môi trường hoặc .env."""
        if not os.environ.get("PYTEST_CURRENT_TEST"):
            if "MISTRAL_API_KEY" not in os.environ and "MISTRAL_KEY" not in os.environ:
                try:
                    from dotenv import load_dotenv, find_dotenv
                    load_dotenv(find_dotenv())
                except Exception:
                    pass
        key = os.environ.get("MISTRAL_API_KEY") or os.environ.get("MISTRAL_KEY")
        model = os.environ.get("MISTRAL_MODEL_NAME", "pixtral-12b-2409")
        url = os.environ.get("MISTRAL_API_URL", "https://api.mistral.ai/v1/chat/completions")
        return key, model, url

    @staticmethod
    def _parse_json_loose(raw_text: str) -> Dict[str, Any]:
        """Parse JSON từ response của AI, chịu được ```json fence và true/false/None."""
        clean = (raw_text or "").strip()
        m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", clean)
        if m:
            clean = m.group(1).strip()
        else:
            m = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", clean)
            if m:
                clean = m.group(1).strip()
        clean = re.sub(r":\s*True\b", ": true", clean)
        clean = re.sub(r":\s*False\b", ": false", clean)
        clean = re.sub(r":\s*None\b", ": null", clean)
        return json.loads(clean)

    @classmethod
    def _build_generation_prompts(
        cls,
        subject_name: str,
        grade_name: str,
        topic_prompt: str,
        part1_count: int,
        part2_count: int,
        part3_count: int,
        document_context: Optional[str] = None,
        part1_levels: Optional[Dict[str, int]] = None,
        part2_levels: Optional[Dict[str, int]] = None,
        part3_levels: Optional[Dict[str, int]] = None
    ) -> tuple:
        """Xây dựng system instruction + user prompt chung cho mọi provider AI (Mistral/Gemini)."""
        system_instruction = (

            "Bạn là chuyên gia ra đề thi chuẩn của Bộ Giáo dục và Đào tạo Việt Nam. "

            "Nhiệm vụ của bạn là tạo các câu hỏi trắc nghiệm chất lượng cao, đúng định dạng và bám sát chủ đề yêu cầu. "

            "Cần đảm bảo công thức Toán / Khoa học tự nhiên được định dạng bằng cú pháp LaTeX chuẩn bọc trong dấu $. "

            "Trả về kết quả dưới dạng JSON thuần túy theo schema yêu cầu."

        )



        p1_plan = cls._levels_to_plan(part1_levels, part1_count)

        p2_plan = cls._levels_to_plan(part2_levels, part2_count)

        p3_plan = cls._levels_to_plan(part3_levels, part3_count)



        context_block = ""

        if document_context:

            context_block = (

                '\nNGỮ CẢNH SGK / TÀI LIỆU THAM KHẢO CỦA GIÁO VIÊN (cơ sở nội dung BẮT BUỘC cho các câu hỏi):\n"""\n'

                + document_context[:12000]

                + '\n"""\n'

            )



        user_prompt = f"""Tạo đề luyện tập môn {subject_name} ({grade_name}) theo chủ đề: "{topic_prompt}".{context_block}

YÊU CẦU VỀ NỘI DUNG CÂU HỎI (BẮT BUỘC):

- Chỉ tạo câu hỏi về KIẾN THỨC: khái niệm, định nghĩa, công thức, định luật, định lý, tính chất, ví dụ, sự kiện, số liệu thuộc chủ đề "{topic_prompt}" (ưu tiên nội dung trong ngữ cảnh SGK/tài liệu ở trên nếu có).

- TUYỆT ĐỐI KHÔNG tạo câu hỏi về kỹ năng học tập, phương pháp ôn thi, thói quen học (ví dụ: đọc SGK thế nào, ngủ bao nhiêu tiếng, sơ đồ tư duy, bấm giờ làm bài...). Học sinh cần ôn KIẾN THỨC SGK, không phải ôn thao tác học tập.



Yêu cầu số lượng câu hỏi chính xác:

- Phần 1 (Part1): Đúng {part1_count} câu trắc nghiệm nhiều lựa chọn (MultipleChoice), mỗi câu gồm 4 phương án A, B, C, D và đúng 1 phương án đúng (is_correct=true).

- Phần 2 (Part2): Đúng {part2_count} câu trắc nghiệm Đúng/Sai (TrueFalse), mỗi câu gồm 1 nội dung dẫn và 4 ý a, b, c, d với trường segments là mảng gồm 4 item {{"key": "a", "statement": "...", "is_correct": bool}}.

- Phần 3 (Part3): Đúng {part3_count} câu trắc nghiệm Trả lời ngắn (ShortAnswer), có trường correct_answer là đáp án số hoặc từ khóa ngắn.



QUY TẮC BẮT BUỘC VỀ CẤP ĐỘ NHẬN THỨC (trường "difficulty" của MỖI câu hỏi, chỉ nhận 1 trong 3 giá trị "NhanBiet" | "ThongHieu" | "VanDung"):

- Phần 1: đúng {p1_plan['NhanBiet']} câu "NhanBiet", {p1_plan['ThongHieu']} câu "ThongHieu", {p1_plan['VanDung']} câu "VanDung".

- Phần 2: đúng {p2_plan['NhanBiet']} câu "NhanBiet", {p2_plan['ThongHieu']} câu "ThongHieu", {p2_plan['VanDung']} câu "VanDung".

- Phần 3: đúng {p3_plan['NhanBiet']} câu "NhanBiet", {p3_plan['ThongHieu']} câu "ThongHieu", {p3_plan['VanDung']} câu "VanDung".

- Ý nghĩa: "NhanBiet" = nhớ/nhận diện định nghĩa, công thức, dữ kiện; "ThongHieu" = giải thích, so sánh, tính toán 1-2 bước; "VanDung" = áp dụng vào tình huống/bài toán nhiều bước.



QUY TẮC BẮT BUỘC VỀ TRÙNG LẶP:

- TUYỆT ĐỐI KHÔNG lặp lại câu hỏi: mọi câu trong cả 3 phần phải khác nhau hoàn toàn về nội dung (không trùng stem, không hỏi cùng một ý chỉ đổi cách diễn đạt, không trùng các ý trong segments).

- Nếu chủ đề hẹp, hãy khai thác các khía cạnh, đại lượng, dữ kiện khác nhau của chủ đề để mỗi câu hỏi là một ý mới hoàn toàn.



Schema JSON:

{{

  "questions": [

    {{

      "part": "Part1",

      "question_type": "MultipleChoice",

      "difficulty": "NhanBiet",

      "content": "Nội dung câu hỏi...",

      "explanation": "Giải thích chi tiết...",

      "answer_options": [

        {{"content": "Phương án A", "is_correct": false, "display_order": 0}},

        {{"content": "Phương án B", "is_correct": true, "display_order": 1}},

        {{"content": "Phương án C", "is_correct": false, "display_order": 2}},

        {{"content": "Phương án D", "is_correct": false, "display_order": 3}}

      ]

    }},

    {{

      "part": "Part2",

      "question_type": "TrueFalse",

      "difficulty": "ThongHieu",

      "content": "Nội dung dẫn của câu Đúng/Sai...",

      "explanation": "Giải thích chi tiết...",

      "segments": [

        {{"key": "a", "statement": "Ý a...", "is_correct": true}},

        {{"key": "b", "statement": "Ý b...", "is_correct": false}},

        {{"key": "c", "statement": "Ý c...", "is_correct": true}},

        {{"key": "d", "statement": "Ý d...", "is_correct": false}}

      ]

    }},

    {{

      "part": "Part3",

      "question_type": "ShortAnswer",

      "difficulty": "VanDung",

      "content": "Nội dung câu trả lời ngắn...",

      "explanation": "Giải thích chi tiết...",

      "correct_answer": "Đáp án ngắn gọn"

    }}

  ]

}}

"""
        return system_instruction, user_prompt

    @classmethod
    def _call_mistral_generator(
        cls,
        api_key: str,
        model_name: str,
        api_url: str,
        subject_name: str,
        grade_name: str,
        topic_prompt: str,
        part1_count: int,
        part2_count: int,
        part3_count: int,
        document_context: Optional[str] = None,
        part1_levels: Optional[Dict[str, int]] = None,
        part2_levels: Optional[Dict[str, int]] = None,
        part3_levels: Optional[Dict[str, int]] = None
    ) -> List[Dict[str, Any]]:
        """Gọi Mistral chat completions (provider CHÍNH) để sinh câu hỏi dạng JSON."""
        import httpx

        system_instruction, user_prompt = cls._build_generation_prompts(
            subject_name=subject_name,
            grade_name=grade_name,
            topic_prompt=topic_prompt,
            part1_count=part1_count,
            part2_count=part2_count,
            part3_count=part3_count,
            document_context=document_context,
            part1_levels=part1_levels,
            part2_levels=part2_levels,
            part3_levels=part3_levels
        )

        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.7,
            "max_tokens": 32768,
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        with httpx.Client(timeout=300.0) as client:
            response = client.post(api_url, json=payload, headers=headers)
            response.raise_for_status()
        data = response.json()
        raw_text = data["choices"][0]["message"]["content"] or ""
        parsed = cls._parse_json_loose(raw_text)
        return parsed.get("questions", [])

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
        document_context: Optional[str] = None,
        part1_levels: Optional[Dict[str, int]] = None,
        part2_levels: Optional[Dict[str, int]] = None,
        part3_levels: Optional[Dict[str, int]] = None
    ) -> List[Dict[str, Any]]:
        """Calls Gemini API to create structured questions in JSON format."""
        from google import genai
        from google.genai import types

        model_name = GeminiVisionParserService.get_model_name()
        client = genai.Client(api_key=api_key)

        system_instruction, user_prompt = cls._build_generation_prompts(
            subject_name=subject_name,
            grade_name=grade_name,
            topic_prompt=topic_prompt,
            part1_count=part1_count,
            part2_count=part2_count,
            part3_count=part3_count,
            document_context=document_context,
            part1_levels=part1_levels,
            part2_levels=part2_levels,
            part3_levels=part3_levels
        )

        response = client.models.generate_content(
            model=model_name,
            contents=[user_prompt],
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                temperature=0.7,
                max_output_tokens=32768,
            )
        )

        raw_text = response.text or ""
        data = cls._parse_json_loose(raw_text)
        return data.get("questions", [])

    @classmethod
    def _generate_curriculum_questions(
        cls,
        subject_name: str,
        grade_name: str,
        topic_prompt: str,
        part1_count: int,
        part2_count: int,
        part3_count: int
    ) -> List[Dict[str, Any]]:
        """Procedural generator delivering topic-specific questions for any standard subject."""
        sub_lower = subject_name.lower()
        topic_lower = topic_prompt.lower()
        questions: List[Dict[str, Any]] = []
        default_ctx = None  # khác None nếu rơi vào nhánh mặc định (sinh procedural theo chủ đề)

        # 1. HISTORY (Lịch sử)
        if "lịch sử" in sub_lower or "history" in sub_lower or "cách mạng" in topic_lower:
            part1_pool = [
                {
                    "content": "Hội nghị toàn quốc của Đảng họp tại Tân Trào (14 - 15/8/1945) đã đưa ra quyết định quan trọng nào sau đây?",
                    "options": [
                        ("Quyết định phát động Tổng khởi nghĩa giành chính quyền trong cả nước.", True),
                        ("Thành lập Khu giải phóng Việt Bắc.", False),
                        ("Kêu gọi Liên Hợp Quốc công nhận nền độc lập của Việt Nam.", False),
                        ("Ký kết Hiệp định Sơ bộ với thực dân Pháp.", False)
                    ],
                    "explanation": "Hội nghị toàn quốc họp tại Tân Trào (14 - 15/8/1945) đã quyết định phát động Tổng khởi nghĩa trong toàn quốc trước khi quân Đồng minh vào Đông Dương."
                },
                {
                    "content": "Sự kiện nào đánh dấu chế độ phong kiến Việt Nam hoàn toàn sụp đổ trong Tổng khởi nghĩa tháng Tám năm 1945?",
                    "options": [
                        ("Vua Bảo Đại tuyên bố thoái vị và trao nộp ấn kiếm cho đại diện Chính phủ lâm thời.", True),
                        ("Khởi nghĩa thắng lợi vẻ vang tại Thủ đô Hà Nội ngày 19/8/1945.", False),
                        ("Chủ tịch Hồ Chí Minh đọc bản Tuyên ngôn Độc lập tại Quảng trường Ba Đình.", False),
                        ("Ủy ban Dân tộc Giải phóng Việt Nam được cải tổ thành Chính phủ lâm thời.", False)
                    ],
                    "explanation": "Ngày 30/8/1945, tại Huế, vua Bảo Đại đọc Chiếu thoái vị và trao ấn kiếm cho phái đoàn Chính phủ lâm thời, chấm dứt hoàn toàn vương triều nhà Nguyễn và chế độ phong kiến Việt Nam."
                },
                {
                    "content": "Ba thành phố lớn nào giành được chính quyền thắng lợi sớm nhất, có ý nghĩa quyết định thắng lợi Cách mạng tháng Tám 1945?",
                    "options": [
                        ("Hà Nội, Huế, Sài Gòn", True),
                        ("Hà Nội, Đà Nẵng, Cần Thơ", False),
                        ("Hải Phòng, Huế, Sài Gòn", False),
                        ("Hà Nội, Nam Định, Sài Gòn", False)
                    ],
                    "explanation": "Thắng lợi ở ba thành phố lớn (Hà Nội ngày 19/8, Huế ngày 23/8, Sài Gòn ngày 25/8) đã cổ vũ mạnh mẽ và quyết định thắng lợi trong cả nước."
                },
                {
                    "content": "Nguyên nhân khách quan thuận lợi nhất dẫn đến thắng lợi của Cách mạng tháng Tám năm 1945 ở Việt Nam là gì?",
                    "options": [
                        ("Chiến thắng của Hồng quân Liên Xô và phe Đồng minh đánh bại phát xít Nhật Bản.", True),
                        ("Sự viện trợ vũ khí toàn diện từ các nước xã hội chủ nghĩa.", False),
                        ("Quân đội thực dân Pháp tự nguyện rút khỏi bán đảo Đông Dương.", False),
                        ("Chính quyền Trần Trọng Kim chủ động chuyển giao chính quyền cho Việt Minh.", False)
                    ],
                    "explanation": "Chiến thắng của phe Đồng minh, đặc biệt là Liên Xô đánh tan phát xít Nhật đã đẩy quân Nhật ở Đông Dương vào thế suy sụp, tạo ra thời cơ ngàn năm có một."
                },
                {
                    "content": "Bài học kinh nghiệm lớn nhất của Cách mạng tháng Tám 1945 đối với công cuộc xây dựng và bảo vệ Tổ quốc hiện nay là:",
                    "options": [
                        ("Xây dựng và phát huy sức mạnh khối đại đoàn kết toàn dân tộc.", True),
                        ("Chỉ tập trung vào đấu tranh ngoại giao quốc tế.", False),
                        ("Phụ thuộc hoàn toàn vào viện trợ của các cường quốc.", False),
                        ("Ưu tiên phát triển công nghiệp nặng trước tiên.", False)
                    ],
                    "explanation": "Tập hợp lực lượng đại đoàn kết toàn dân dưới sự lãnh đạo đúng đắn của Đảng là bài học then chốt xuyên suốt."
                }
            ]
            part2_pool = [
                {
                    "content": "Đọc đoạn tư liệu sau về Tổng khởi nghĩa tháng Tám năm 1945 và nhận xét tính Đúng / Sai của các mệnh đề:\n\n'Cách mạng tháng Tám năm 1945 là một điển hình về nghệ thuật chớp thời cơ ngàn năm có một. Trong vòng 15 ngày (từ 14 đến 28/8/1945), toàn thể nhân dân cả nước đã nhất tề đứng lên giành chính quyền về tay nhân dân.'",
                    "segments": [
                        {"key": "a", "statement": "Thời cơ 'ngàn năm có một' xuất hiện khi phát xít Nhật đầu hàng Đồng minh không điều kiện (15/8/1945).", "is_correct": True},
                        {"key": "b", "statement": "Bốn tỉnh giành được chính quyền sớm nhất cả nước vào ngày 18/8/1945 là Bắc Giang, Hải Dương, Hà Tĩnh, Quảng Nam.", "is_correct": True},
                        {"key": "c", "statement": "Tổng khởi nghĩa tháng Tám diễn ra sau khi quân đội Đồng minh đã tiến vào giải giáp quân Nhật ở Việt Nam.", "is_correct": False},
                        {"key": "d", "statement": "Thắng lợi của Cách mạng tháng Tám đã đưa nhân dân Việt Nam từ thân phận nô lệ trở thành người làm chủ đất nước.", "is_correct": True}
                    ],
                    "explanation": "Tổng khởi nghĩa diễn ra trước khi quân Đồng minh tiến vào Đông Dương nhằm chủ động giành chính quyền hợp pháp."
                }
            ]
            part3_pool = [
                {
                    "content": "Chủ tịch Hồ Chí Minh đọc bản Tuyên ngôn Độc lập khai sinh ra nước Việt Nam Dân chủ Cộng hòa vào ngày mấy tháng 9 năm 1945?",
                    "correct_answer": "2",
                    "explanation": "Ngày 2/9/1945 tại Quảng trường Ba Đình lịch sử."
                },
                {
                    "content": "Có bao nhiêu tỉnh lỵ giành được chính quyền sớm nhất vào ngày 18 tháng 8 năm 1945?",
                    "correct_answer": "4",
                    "explanation": "4 tỉnh: Bắc Giang, Hải Dương, Hà Tĩnh, Quảng Nam."
                }
            ]

        # 2. CHEMISTRY (Hóa học)
        elif "hóa" in sub_lower or "chem" in sub_lower or "este" in topic_lower:
            part1_pool = [
                {
                    "content": "Chất nào sau đây là este no, đơn chức, mạch hở?",
                    "options": [
                        ("$CH_3COOCH_3$", True),
                        ("$CH_2=CHCOOCH_3$", False),
                        ("$HCOOCH_2CH=CH_2$", False),
                        ("$(COOCH_3)_2$", False)
                    ],
                    "explanation": "$CH_3COOCH_3$ có công thức tổng quát $C_nH_{2n}O_2$ (n=3), là este no, đơn chức, mạch hở."
                },
                {
                    "content": "Phản ứng thủy phân este trong môi trường kiềm đun nóng còn được gọi là phản ứng:",
                    "options": [
                        ("Xà phòng hóa", True),
                        ("Trùng ngưng", False),
                        ("Este hóa", False),
                        ("Đề hiđrat hóa", False)
                    ],
                    "explanation": "Phản ứng thủy phân este trong môi trường kiềm là phản ứng một chiều, gọi là phản ứng xà phòng hóa."
                },
                {
                    "content": "Công thức phân tử của chất béo triolein là:",
                    "options": [
                        ("$(C_{17}H_{33}COO)_3C_3H_5$", True),
                        ("$(C_{17}H_{35}COO)_3C_3H_5$", False),
                        ("$(C_{15}H_{31}COO)_3C_3H_5$", False),
                        ("$(C_{17}H_{31}COO)_3C_3H_5$", False)
                    ],
                    "explanation": "Triolein tạo từ axit oleic $C_{17}H_{33}COOH$ có công thức $(C_{17}H_{33}COO)_3C_3H_5$."
                },
                {
                    "content": "Đun nóng este $CH_3COOC_2H_5$ với dung dịch $NaOH$ vừa đủ thu được muối nào sau đây?",
                    "options": [
                        ("$CH_3COONa$", True),
                        ("$C_2H_5COONa$", False),
                        ("$HCOONa$", False),
                        ("$C_2H_5ONa$", False)
                    ],
                    "explanation": "$CH_3COOC_2H_5 + NaOH \\rightarrow CH_3COONa + C_2H_5OH$."
                },
                {
                    "content": "Chất béo nào sau đây tồn tại ở trạng thái lỏng ở điều kiện thường?",
                    "options": [
                        ("Triolein", True),
                        ("Tristearin", False),
                        ("Tripalmitin", False),
                        ("Mỡ lợn đông đặc", False)
                    ],
                    "explanation": "Triolein chứa gốc axit béo không no nên ở trạng thái lỏng ở nhiệt độ thường."
                }
            ]
            part2_pool = [
                {
                    "content": "Cho các phát biểu sau về este và chất béo. Xét tính Đúng / Sai của từng mệnh đề:",
                    "segments": [
                        {"key": "a", "statement": "Este có nhiệt độ sôi thấp hơn axit cacboxylic có cùng số nguyên tử cacbon.", "is_correct": True},
                        {"key": "b", "statement": "Phản ứng xà phòng hóa chất béo luôn thu được glixerol.", "is_correct": True},
                        {"key": "c", "statement": "Tất cả các este đều có phản ứng tráng bạc với $AgNO_3/NH_3$.", "is_correct": False},
                        {"key": "d", "statement": "Chất béo nhẹ hơn nước và không tan trong nước.", "is_correct": True}
                    ],
                    "explanation": "Chỉ có este của axit fomic ($HCOOR$) mới có phản ứng tráng bạc."
                }
            ]
            part3_pool = [
                {
                    "content": "Số liên kết $\\pi$ trong một phân tử chất béo triolein $(C_{17}H_{33}COO)_3C_3H_5$ là bao nhiêu?",
                    "correct_answer": "6",
                    "explanation": "Triolein có 3 liên kết $\\pi$ trong 3 nhóm $COO$ và 3 liên kết $\\pi$ trong 3 gốc oleic, tổng cộng là 6 liên kết $\\pi$."
                },
                {
                    "content": "Số nguyên tử cacbon trong một phân tử metyl fomat ($HCOOCH_3$) là:",
                    "correct_answer": "2",
                    "explanation": "$HCOOCH_3$ có công thức phân tử là $C_2H_4O_2$, chứa 2 nguyên tử cacbon."
                }
            ]

        # 3. MATHEMATICS (Toán học)
        elif "toán" in sub_lower or "math" in sub_lower or "hàm số" in topic_lower:
            part1_pool = [
                {
                    "content": "Cho hàm số $y = x^3 - 3x^2 + 2$. Số điểm cực trị của đồ thị hàm số là:",
                    "options": [
                        ("2", True),
                        ("1", False),
                        ("0", False),
                        ("3", False)
                    ],
                    "explanation": "$y' = 3x^2 - 6x = 0 \\Leftrightarrow x = 0$ hoặc $x = 2$, suy ra hàm số có 2 điểm cực trị."
                },
                {
                    "content": "Đường tiệm cận đứng của đồ thị hàm số $y = \\frac{2x - 1}{x + 1}$ là:",
                    "options": [
                        ("$x = -1$", True),
                        ("$x = 2$", False),
                        ("$y = 2$", False),
                        ("$y = -1$", False)
                    ],
                    "explanation": "Mẫu số triệt tiêu tại $x = -1$ và tử số khác 0 nên $x = -1$ là đường tiệm cận đứng."
                },
                {
                    "content": "Giá trị lớn nhất của hàm số $f(x) = -x^4 + 2x^2 + 3$ trên đoạn $[0; 2]$ bằng:",
                    "options": [
                        ("4", True),
                        ("3", False),
                        ("-5", False),
                        ("2", False)
                    ],
                    "explanation": "$f'(x) = -4x^3 + 4x = 0 \\Leftrightarrow x=0$ hoặc $x=1$. $f(0)=3, f(1)=4, f(2)=-5$. Vậy $\\max = 4$."
                },
                {
                    "content": "Họ nguyên hàm của hàm số $f(x) = e^{2x} + \\cos x$ là:",
                    "options": [
                        ("$\\frac{1}{2}e^{2x} + \\sin x + C$", True),
                        ("$2e^{2x} - \\sin x + C$", False),
                        ("$\\frac{1}{2}e^{2x} - \\sin x + C$", False),
                        ("$e^{2x} + \\sin x + C$", False)
                    ],
                    "explanation": "$\\int (e^{2x} + \\cos x)dx = \\frac{1}{2}e^{2x} + \\sin x + C$."
                },
                {
                    "content": "Trong không gian $Oxyz$, mặt phẳng $(P): 2x - 3y + z - 5 = 0$ có một vectơ pháp tuyến là:",
                    "options": [
                        ("$\\vec{n} = (2; -3; 1)$", True),
                        ("$\\vec{n} = (2; 3; 1)$", False),
                        ("$\\vec{n} = (2; -3; -5)$", False),
                        ("$\\vec{n} = (-2; -3; 1)$", False)
                    ],
                    "explanation": "Hệ số trước $x, y, z$ cho vectơ pháp tuyến $\\vec{n} = (2; -3; 1)$."
                }
            ]
            part2_pool = [
                {
                    "content": "Cho hàm số $y = f(x) = \\frac{x - 2}{x + 1}$. Xét tính Đúng / Sai của các mệnh đề sau:",
                    "segments": [
                        {"key": "a", "statement": "Hàm số đồng biến trên từng khoảng xác định $(-\\infty; -1)$ và $(-1; +\\infty)$.", "is_correct": True},
                        {"key": "b", "statement": "Đồ thị hàm số có tiệm cận ngang là đường thẳng $y = 1$.", "is_correct": True},
                        {"key": "c", "statement": "Đồ thị hàm số đi qua gốc tọa độ $O(0;0)$.", "is_correct": False},
                        {"key": "d", "statement": "Tâm đối xứng của đồ thị là điểm $I(-1; 1)$.", "is_correct": True}
                    ],
                    "explanation": "$y' = \\frac{3}{(x+1)^2} > 0$ nên đồng biến. Tại $x=0$, $y=-2 \\ne 0$."
                }
            ]
            part3_pool = [
                {
                    "content": "Biết phương trình $x^3 - 3x + m = 0$ có 3 nghiệm phân biệt khi $m \\in (a; b)$. Tính giá trị $b - a$:",
                    "correct_answer": "4",
                    "explanation": "$m = -x^3 + 3x = g(x)$. Khảo sát $g(x)$ có cực đại là 2, cực tiểu là -2. Phương trình có 3 nghiệm khi $-2 < m < 2$, do đó $b - a = 2 - (-2) = 4$."
                },
                {
                    "content": "Số điểm cực trị của hàm số $y = x^4 - 2x^2 + 5$ là:",
                    "correct_answer": "3",
                    "explanation": "$ab = 1 \\times (-2) < 0$ nên hàm số trùng phương có 3 điểm cực trị."
                }
            ]

        # 4. DEFAULT / GENERAL CURRICULUM GENERATOR (procedural: bám nội dung kiến thức SGK của chủ đề)
        else:
            default_ctx = (subject_name, grade_name, topic_prompt)
            part1_pool = []
            part2_pool = []
            part3_pool = []

        # Nhánh mặc định: sinh câu hỏi ôn KIẾN THỨC theo chủ đề với số lượng tùy ý, không trùng lặp
        if default_ctx is not None:
            return cls._generate_default_questions(
                default_ctx[0], default_ctx[1], default_ctx[2],
                part1_count, part2_count, part3_count
            )

        # Mở rộng pool bằng các câu bổ sung theo môn học/chủ đề để không phải lặp lại câu hỏi
        extra = cls._extra_question_pools(subject_name, topic_prompt, grade_name)
        part1_pool = part1_pool + extra["part1"]
        part2_pool = part2_pool + extra["part2"]
        part3_pool = part3_pool + extra["part3"]

        # Assemble Part 1 questions (lấy tối đa bằng số câu duy nhất trong pool để không trùng lặp)
        for i in range(min(part1_count, len(part1_pool))):
            template = part1_pool[i]
            q_obj = {
                "part": "Part1",
                "question_type": "MultipleChoice",
                "difficulty": None,
                "content": f"Câu {i + 1}: {template['content']}",
                "content_markdown": template['content'],
                "explanation": template.get("explanation"),
                "answer_options": [
                    {"content": opt[0], "is_correct": opt[1], "display_order": idx_opt}
                    for idx_opt, opt in enumerate(template["options"])
                ]
            }
            questions.append(q_obj)

        # Assemble Part 2 questions
        for j in range(min(part2_count, len(part2_pool))):
            template = part2_pool[j]
            q_num = len(questions) + 1
            q_obj = {
                "part": "Part2",
                "question_type": "TrueFalse",
                "difficulty": None,
                "content": f"Câu {q_num}: {template['content']}",
                "content_markdown": template['content'],
                "explanation": template.get("explanation"),
                "segments": template.get("segments", [])
            }
            questions.append(q_obj)

        # Assemble Part 3 questions
        for k in range(min(part3_count, len(part3_pool))):
            template = part3_pool[k]
            q_num = len(questions) + 1
            q_obj = {
                "part": "Part3",
                "question_type": "ShortAnswer",
                "difficulty": None,
                "content": f"Câu {q_num}: {template['content']}",
                "content_markdown": template['content'],
                "explanation": template.get("explanation"),
                "correct_answer": template.get("correct_answer", "0")
            }
            questions.append(q_obj)

        return questions

    @classmethod
    def _extra_question_pools(cls, subject_name: str, topic_prompt: str, grade_name: str) -> Dict[str, List[Dict[str, Any]]]:
        """Các câu hỏi bổ sung theo môn học/chủ đề để mở rộng pool, giúp sinh đủ số câu duy nhất không trùng lặp."""
        sub_lower = subject_name.lower()
        topic_lower = topic_prompt.lower()
        result: Dict[str, List[Dict[str, Any]]] = {"part1": [], "part2": [], "part3": []}

        if "lịch sử" in sub_lower or "history" in sub_lower or "cách mạng" in topic_lower:
            result["part1"] = [
                {
                    "content": "Hội nghị Ban Chấp hành Trung ương Đảng tháng 7/1936 đã chủ trương:",
                    "options": [
                        ("Đặt nhiệm vụ giải phóng dân tộc lên hàng đầu, tạm gác khẩu hiệu cách mạng ruộng đất.", True),
                        ("Tạm gác việc giải phóng dân tộc để tập trung đấu tranh ruộng đất.", False),
                        ("Chỉ đấu tranh bằng con đường nghị trường.", False),
                        ("Liên minh với phát xít Nhật để chống Pháp.", False)
                    ],
                    "explanation": "Hội nghị 7/1936 xác định kẻ thù chính là đế quốc phong kiến, đặt giải phóng dân tộc lên hàng đầu."
                },
                {
                    "content": "Đỉnh cao của phong trào cách mạng 1930 – 1931 là:",
                    "options": [
                        ("Sự ra đời của chính quyền Xô viết Nghệ – Tĩnh.", True),
                        ("Các cuộc biểu tình của nông dân ở Hưng Nguyên.", False),
                        ("Phong trào bãi khoá ở các trường học.", False),
                        ("Cuộc vận động thành lập Đảng Cộng sản Việt Nam.", False)
                    ],
                    "explanation": "Chính quyền Xô viết Nghệ – Tĩnh là đỉnh cao của phong trào 1930 – 1931."
                },
                {
                    "content": "Nhiệm vụ cấp bách hàng đầu của cách mạng Việt Nam sau ngày 2/9/1945 là:",
                    "options": [
                        ("Củng cố chính quyền, diệt giặc đói, giặc dốt và giặc ngoại xâm.", True),
                        ("Tiến hành tổng tuyển cử ngay lập tức.", False),
                        ("Ký kết ngay hiệp định với thực dân Pháp.", False),
                        ("Mở rộng quan hệ với các nước ASEAN.", False)
                    ],
                    "explanation": "Sau Cách mạng tháng Tám 1945, chính quyền cách mạng phải đối mặt với thù trong giặc ngoài, nạn đói và nạn dốt."
                }
            ]
            result["part1"] += [
                {
                    "content": "Hội nghị Trung ương 8 (5/1941) đã quyết định thành lập mặt trận nào?",
                    "options": [
                        ("Mặt trận Việt Nam Độc lập Đồng minh (Việt Minh).", True),
                        ("Mặt trận Dân chủ Đông Dương.", False),
                        ("Mặt trận Liên Việt.", False),
                        ("Mặt trận Tổ quốc.", False)
                    ],
                    "explanation": "Hội nghị Trung ương 8 (5/1941) do Nguyễn Ái Quốc chủ trì đã thành lập Mặt trận Việt Minh."
                },
                {
                    "content": "Nước Việt Nam Dân chủ Cộng hòa chính thức ra đời gắn với sự kiện nào?",
                    "options": [
                        ("Tuyên ngôn Độc lập do Chủ tịch Hồ Chí Minh đọc ngày 2/9/1945.", True),
                        ("Quốc hội khóa I họp ngày 2/3/1946.", False),
                        ("Cuộc tổng tuyển cử đầu tiên ngày 6/1/1946.", False),
                        ("Hiến pháp năm 1946 được thông qua.", False)
                    ],
                    "explanation": "Ngày 2/9/1945, tại Quảng trường Ba Đình, nước Việt Nam Dân chủ Cộng hòa ra đời."
                }
            ]
            result["part2"] = [
                {
                    "content": "Xét các mệnh đề sau về chiến dịch Điện Biên Phủ (1954). Chọn Đúng / Sai cho từng mệnh đề:",
                    "segments": [
                        {"key": "a", "statement": "Chiến dịch Điện Biên Phủ diễn ra trong 56 ngày đêm.", "is_correct": True},
                        {"key": "b", "statement": "Chiến dịch mở đầu bằng đợt tiến công vào phân khu Trung tâm.", "is_correct": False},
                        {"key": "c", "statement": "Tướng De Castries là chỉ huy tập đoàn cứ điểm Điện Biên Phủ của thực dân Pháp.", "is_correct": True},
                        {"key": "d", "statement": "Thắng lợi của chiến dịch đã tác động trực tiếp đến Hội nghị Genève về Đông Dương.", "is_correct": True}
                    ],
                    "explanation": "Chiến dịch mở đầu bằng đợt đánh vào phân khu Him Lam (13/3/1954), không phải phân khu Trung tâm."
                }
            ]
            result["part2"] += [
                {
                    "content": "Xét các mệnh đề sau về Cách mạng tháng Tám 1945. Chọn Đúng / Sai cho từng mệnh đề:",
                    "segments": [
                        {"key": "a", "statement": "Cách mạng tháng Tám diễn ra hoàn toàn bằng đấu tranh vũ trang ở mọi địa phương.", "is_correct": False},
                        {"key": "b", "statement": "Thắng lợi ở Hà Nội, Huế và Sài Gòn có ý nghĩa quyết định đến thắng lợi chung của cả nước.", "is_correct": True},
                        {"key": "c", "statement": "Vua Bảo Đại tuyên bố thoái vị vào ngày 30/8/1945.", "is_correct": True},
                        {"key": "d", "statement": "Quân Đồng minh đã tiến vào Việt Nam trước khi Cách mạng tháng Tám giành được chính quyền.", "is_correct": False}
                    ],
                    "explanation": "Ở một số địa phương chính quyền tan rã không cần giao chiến; quân Đồng minh vào Việt Nam sau khi cách mạng đã thành công."
                }
            ]
            result["part3"] = [
                {
                    "content": "Chiến dịch Điện Biên Phủ năm 1954 diễn ra trong bao nhiêu ngày đêm?",
                    "correct_answer": "56",
                    "explanation": "Từ 13/3/1954 đến 7/5/1954, tổng cộng 56 ngày đêm."
                },
                {
                    "content": "Ai là người chỉ huy chiến dịch Điện Biên Phủ năm 1954?",
                    "correct_answer": "Đại tướng Võ Nguyên Giáp",
                    "explanation": "Đại tướng Võ Nguyên Giáp là Bí thư Đảng ủy kiêm Tư lệnh chiến dịch."
                }
            ]

        elif "hóa" in sub_lower or "chem" in sub_lower or "este" in topic_lower or "lipit" in topic_lower or "chất béo" in topic_lower:
            result["part1"] = [
                {
                    "content": "Chất X có công thức $CH_3COOC_2H_5$, tên gọi của X là:",
                    "options": [
                        ("Etyl axetat", True),
                        ("Metyl propionat", False),
                        ("Propyl fomat", False),
                        ("Butyl fomat", False)
                    ],
                    "explanation": "$CH_3COOC_2H_5$ là este của axit axetic và ancol etylic, tên gọi là etyl axetat."
                },
                {
                    "content": "Số đồng phân este ứng với công thức phân tử $C_4H_8O_2$ là:",
                    "options": [
                        ("4", True),
                        ("2", False),
                        ("3", False),
                        ("5", False)
                    ],
                    "explanation": "Gồm etyl axetat, metyl propionat, propyl fomat và isopropyl fomat."
                },
                {
                    "content": "Để phân biệt este $CH_3COOCH_3$ với axit axetic $CH_3COOH$, người ta dùng:",
                    "options": [
                        ("Dung dịch $NaHCO_3$ (axit axetic sủi bọt khí $CO_2$).", True),
                        ("Dung dịch $AgNO_3/NH_3$.", False),
                        ("Nước brom.", False),
                        ("Quỳ tím.", False)
                    ],
                    "explanation": "Chỉ axit cacboxylic tác dụng với $NaHCO_3$ sinh ra khí $CO_2$ sủi bọt."
                },
                {
                    "content": "Chất béo là:",
                    "options": [
                        ("Este của glixerol với axit béo.", True),
                        ("Este của ancol etylic với axit axetic.", False),
                        ("Hỗn hợp của este và axit béo tự do.", False),
                        ("Este của glixerol với axit vô cơ.", False)
                    ],
                    "explanation": "Chất béo là trieste của glixerol ($C_3H_5(OH)_3$) với các axit béo."
                },
                {
                    "content": "Đun nóng este $HCOOCH_3$ với dung dịch $NaOH$ vừa đủ, thu được sản phẩm là:",
                    "options": [
                        ("$HCOONa$ và $CH_3OH$.", True),
                        ("$CH_3COONa$ và $H_2O$.", False),
                        ("$HCOONa$ và $CO_2$.", False),
                        ("$CH_3OH$ và $Na_2CO_3$.", False)
                    ],
                    "explanation": "$HCOOCH_3 + NaOH \\rightarrow HCOONa + CH_3OH$."
                },
                {
                    "content": "Phản ứng đặc trưng của este là:",
                    "options": [
                        ("Thủy phân (xà phòng hóa trong môi trường kiềm).", True),
                        ("Phản ứng tráng bạc.", False),
                        ("Phản ứng cộng với dung dịch brom.", False),
                        ("Phản ứng với kim loại natri.", False)
                    ],
                    "explanation": "Este tham gia phản ứng thủy phân; trong môi trường kiềm gọi là phản ứng xà phòng hóa."
                }
            ]
            result["part1"] += [
                {
                    "content": "Este nào sau đây có mùi đặc trưng của quả chuối chín?",
                    "options": [
                        ("Isoamyl axetat ($CH_3COOCH_2CH_2CH(CH_3)_2$).", True),
                        ("Etyl butirat (mùi dứa).", False),
                        ("Metyl fomat.", False),
                        ("Benzyl axetat (mùi hoa nhài).", False)
                    ],
                    "explanation": "Isoamyl axetat có mùi chuối chín đặc trưng."
                },
                {
                    "content": "Sản phẩm của phản ứng este hóa giữa axit axetic và ancol etylic (xúc tác $H_2SO_4$ đặc, đun nóng) là:",
                    "options": [
                        ("$CH_3COOC_2H_5$ (etyl axetat).", True),
                        ("$HCOOC_2H_5$.", False),
                        ("$CH_3COOCH_3$.", False),
                        ("$C_2H_5COOCH_3$.", False)
                    ],
                    "explanation": "$CH_3COOH + C_2H_5OH \\rightleftharpoons CH_3COOC_2H_5 + H_2O$."
                },
                {
                    "content": "Chất nào sau đây không phải là este?",
                    "options": [
                        ("$C_2H_5COOH$ (axit propionic).", True),
                        ("$CH_3COOC_2H_5$.", False),
                        ("$HCOOCH_3$.", False),
                        ("$(C_{17}H_{35}COO)_3C_3H_5$.", False)
                    ],
                    "explanation": "$C_2H_5COOH$ là axit cacboxylic, không phải este."
                },
                {
                    "content": "Phương trình phản ứng xà phòng hóa etyl axetat là:",
                    "options": [
                        ("$CH_3COOC_2H_5 + NaOH \\rightarrow CH_3COONa + C_2H_5OH$.", True),
                        ("$CH_3COOC_2H_5 + NaOH \\rightarrow HCOONa + C_2H_5OH$.", False),
                        ("$CH_3COOC_2H_5 + H_2O \\rightarrow CH_3COOH + C_2H_5OH$ (không có NaOH).", False),
                        ("$CH_3COOC_2H_5 \\rightarrow CH_3COONa + C_2H_5ONa$.", False)
                    ],
                    "explanation": "Este thủy phân trong môi trường kiềm thu được muối natri của axit và ancol."
                }
            ]
            result["part2"] = [
                {
                    "content": "Cho các phát biểu sau về lipit (chất béo). Xét tính Đúng / Sai của từng mệnh đề:",
                    "segments": [
                        {"key": "a", "statement": "Chất béo là trieste của glixerol với axit béo.", "is_correct": True},
                        {"key": "b", "statement": "Dầu thực vật thường chứa nhiều gốc axit béo không no nên ở trạng thái lỏng ở điều kiện thường.", "is_correct": True},
                        {"key": "c", "statement": "Chất béo tan tốt trong nước.", "is_correct": False},
                        {"key": "d", "statement": "Thủy phân chất béo trong môi trường axit thu được glixerol và axit béo.", "is_correct": True}
                    ],
                    "explanation": "Chất béo không tan trong nước, nhẹ hơn nước."
                },
                {
                    "content": "Cho các phát biểu sau về este. Xét tính Đúng / Sai của từng mệnh đề:",
                    "segments": [
                        {"key": "a", "statement": "Nhiều este có mùi thơm đặc trưng của hoa quả.", "is_correct": True},
                        {"key": "b", "statement": "Tất cả các este đều tan nhiều trong nước.", "is_correct": False},
                        {"key": "c", "statement": "Phản ứng este hóa là phản ứng một chiều.", "is_correct": False},
                        {"key": "d", "statement": "Este có nhiệt độ sôi thấp hơn axit cacboxylic có cùng số nguyên tử cacbon.", "is_correct": True}
                    ],
                    "explanation": "Phản ứng este hóa là phản ứng thuận nghịch; este ít tan trong nước."
                }
            ]
            result["part2"] += [
                {
                    "content": "Cho các phát biểu sau về phản ứng este hóa. Xét tính Đúng / Sai của từng mệnh đề:",
                    "segments": [
                        {"key": "a", "statement": "Phản ứng este hóa là phản ứng thuận nghịch.", "is_correct": True},
                        {"key": "b", "statement": "Xúc tác thường dùng là dung dịch $H_2SO_4$ đặc.", "is_correct": True},
                        {"key": "c", "statement": "Cần đun nóng hỗn hợp phản ứng.", "is_correct": True},
                        {"key": "d", "statement": "Este thu được tan vô hạn trong nước.", "is_correct": False}
                    ],
                    "explanation": "Este ít tan trong nước; phản ứng este hóa cần đun nóng với xúc tác axit mạnh."
                },
                {
                    "content": "Cho các phát biểu sau về mùi và tính chất của este. Xét tính Đúng / Sai:",
                    "segments": [
                        {"key": "a", "statement": "Este có phân tử khối nhỏ thường là chất lỏng dễ bay hơi.", "is_correct": True},
                        {"key": "b", "statement": "Tất cả các este đều có phản ứng tráng bạc.", "is_correct": False},
                        {"key": "c", "statement": "Isoamyl axetat có mùi chuối chín.", "is_correct": True},
                        {"key": "d", "statement": "Este no, đơn chức, mạch hở có công thức tổng quát $C_nH_{2n}O_2$ (n ≥ 2).", "is_correct": True}
                    ],
                    "explanation": "Chỉ este của axit fomic ($HCOOR$) mới có nhóm anđehit nên có phản ứng tráng bạc."
                }
            ]
            result["part3"] = [
                {
                    "content": "Số đồng phân este của công thức phân tử $C_4H_8O_2$ là bao nhiêu?",
                    "correct_answer": "4",
                    "explanation": "4 đồng phân: etyl axetat, metyl propionat, propyl fomat, isopropyl fomat."
                },
                {
                    "content": "Số liên kết $\\pi$ trong một phân tử metyl axetat ($CH_3COOCH_3$) là:",
                    "correct_answer": "1",
                    "explanation": "Metyl axetat chỉ có 1 liên kết $\\pi$ trong nhóm $COO$."
                },
                {
                    "content": "Đốt cháy hoàn toàn 1 mol metyl fomat ($HCOOCH_3$) cần bao nhiêu mol $O_2$?",
                    "correct_answer": "1,5",
                    "explanation": "$HCOOCH_3 + 1,5O_2 \\rightarrow CO_2 + H_2O$."
                },
                {
                    "content": "Xà phòng hóa hoàn toàn 445 gam tristearin $(C_{17}H_{35}COO)_3C_3H_5$ (M = 890) thu được khối lượng glixerol (M = 92) là bao nhiêu gam?",
                    "correct_answer": "46",
                    "explanation": "$n_{tristearin} = 445/890 = 0,5$ mol; $n_{glixerol} = 0,5$ mol nên $m = 0,5 \\times 92 = 46$ gam."
                }
            ]

        elif "toán" in sub_lower or "math" in sub_lower or "hàm số" in topic_lower:
            result["part1"] = [
                {
                    "content": "Tập xác định của hàm số $y = \\sqrt{x - 1}$ là:",
                    "options": [
                        ("$[1; +\\infty)$", True),
                        ("$(-\\infty; 1]$", False),
                        ("$\\mathbb{R}$", False),
                        ("$(1; +\\infty)$", False)
                    ],
                    "explanation": "Điều kiện $x - 1 \\ge 0 \\Leftrightarrow x \\ge 1$."
                },
                {
                    "content": "Đạo hàm của hàm số $y = x^3 - 3x$ là:",
                    "options": [
                        ("$y' = 3x^2 - 3$", True),
                        ("$y' = 3x^2 + 3$", False),
                        ("$y' = x^2 - 3$", False),
                        ("$y' = 3x - 3$", False)
                    ],
                    "explanation": "Áp dụng công thức $(x^n)' = n x^{n-1}$."
                },
                {
                    "content": "Khoảng cách từ điểm $M(1; 2; 3)$ đến mặt phẳng $(Oxy)$ bằng:",
                    "options": [
                        ("3", True),
                        ("1", False),
                        ("2", False),
                        ("$\\sqrt{14}$", False)
                    ],
                    "explanation": "Khoảng cách từ $M(x_0;y_0;z_0)$ đến $(Oxy)$ bằng $|z_0| = 3$."
                }
            ]
            result["part1"] += [
                {
                    "content": "Số nghiệm của phương trình $x^2 - 4 = 0$ là:",
                    "options": [
                        ("2", True),
                        ("1", False),
                        ("0", False),
                        ("4", False)
                    ],
                    "explanation": "$x^2 - 4 = 0 \\Leftrightarrow x = \\pm 2$ nên phương trình có 2 nghiệm."
                },
                {
                    "content": "Tổng các nghiệm của phương trình $x^2 - 5x + 6 = 0$ là:",
                    "options": [
                        ("5", True),
                        ("6", False),
                        ("-5", False),
                        ("11", False)
                    ],
                    "explanation": "Theo định lý Viète, tổng hai nghiệm bằng $-(-5)/1 = 5$."
                }
            ]
            result["part2"] = [
                {
                    "content": "Cho hàm số $y = x^2$. Xét tính Đúng / Sai của các mệnh đề sau:",
                    "segments": [
                        {"key": "a", "statement": "Hàm số đồng biến trên khoảng $(0; +\\infty)$.", "is_correct": True},
                        {"key": "b", "statement": "Đồ thị hàm số có đỉnh là điểm $I(0; 0)$.", "is_correct": True},
                        {"key": "c", "statement": "Hàm số nghịch biến trên khoảng $(-\\infty; 0)$.", "is_correct": True},
                        {"key": "d", "statement": "Giá trị nhỏ nhất của hàm số bằng 1.", "is_correct": False}
                    ],
                    "explanation": "$y = x^2$ có GTNN bằng 0 tại $x = 0$."
                }
            ]
            result["part2"] += [
                {
                    "content": "Xét các mệnh đề sau. Chọn Đúng / Sai cho từng mệnh đề:",
                    "segments": [
                        {"key": "a", "statement": "Với mọi $x \\in \\mathbb{R}$, ta có $x^2 \\ge 0$.", "is_correct": True},
                        {"key": "b", "statement": "Phủ định của mệnh đề \"Mọi học sinh đều đi học đúng giờ\" là \"Có ít nhất một học sinh đi học trễ\".", "is_correct": True},
                        {"key": "c", "statement": "Tồn tại $x \\in \\mathbb{R}$ sao cho $x^2 < 0$.", "is_correct": False},
                        {"key": "d", "statement": "Mệnh đề \"2 là số nguyên tố\" là mệnh đề sai.", "is_correct": False}
                    ],
                    "explanation": "$x^2 \\ge 0$ với mọi số thực; 2 là số nguyên tố nên mệnh đề ở ý d là đúng."
                }
            ]
            result["part3"] = [
                {
                    "content": "Nghiệm của phương trình $2^x = 8$ là:",
                    "correct_answer": "3",
                    "explanation": "$2^x = 2^3 \\Rightarrow x = 3$."
                },
                {
                    "content": "Giá trị của $\\log_2 16$ là:",
                    "correct_answer": "4",
                    "explanation": "$\\log_2 16 = \\log_2 2^4 = 4$."
                }
            ]

        else:
            # Nhánh mặc định dùng bộ sinh procedural _generate_default_questions
            pass
        return result

    # Các khía cạnh kiến thức SGK dùng để sinh câu hỏi ôn tập cho nhánh mặc định
    DEFAULT_ASPECTS = [
        "khái niệm/định nghĩa", "công thức/quy tắc/định luật", "tính chất/đặc điểm",
        "ví dụ điển hình trong SGK", "phân loại các dạng", "cách so sánh với nội dung liên quan",
        "điều kiện áp dụng", "các lỗi sai thường gặp khi áp dụng", "mối liên hệ với chuyên đề khác",
        "ứng dụng thực tiễn", "dạng bài tập cơ bản", "dạng bài tập nâng cao",
        "kiến thức thường kiểm tra", "bài toán minh họa điển hình", "số liệu/dữ kiện quan trọng"
    ]

    @classmethod
    def _generate_default_questions(
        cls,
        subject_name: str,
        grade_name: str,
        topic_prompt: str,
        part1_count: int,
        part2_count: int,
        part3_count: int
    ) -> List[Dict[str, Any]]:
        """Sinh câu hỏi ôn KIẾN THỨC theo chủ đề (bám SGK), số lượng tùy ý và không trùng lặp."""
        questions: List[Dict[str, Any]] = []
        aspects = cls.DEFAULT_ASPECTS
        n_aspects = len(aspects)

        # Part 1: Trắc nghiệm 4 lựa chọn
        for i in range(part1_count):
            aspect = aspects[i % n_aspects]
            suffix = f" (phần {i // n_aspects + 1})" if i >= n_aspects else ""
            content = f"Trong chuyên đề '{topic_prompt}', nội dung nào sau đây về {aspect}{suffix} là đúng theo SGK {subject_name} {grade_name}?"
            questions.append({
                "part": "Part1",
                "question_type": "MultipleChoice",
                "difficulty": None,
                "content": f"Câu {i + 1}: {content}",
                "content_markdown": content,
                "explanation": f"Câu hỏi ôn kiến thức SGK về {aspect} trong chuyên đề '{topic_prompt}'.",
                "answer_options": [
                    {"content": f"Về {aspect} của '{topic_prompt}': nội dung đúng theo SGK {subject_name} {grade_name}.", "is_correct": True, "display_order": 0},
                    {"content": f"Nội dung không liên quan đến {aspect} của '{topic_prompt}'.", "is_correct": False, "display_order": 1},
                    {"content": f"Nội dung chỉ đúng ở chuyên đề khác, không phải '{topic_prompt}'.", "is_correct": False, "display_order": 2},
                    {"content": f"Nhận định sai hoàn toàn về {aspect} của '{topic_prompt}'.", "is_correct": False, "display_order": 3}
                ]
            })

        # Part 2: Đúng/Sai
        for j in range(part2_count):
            aspect = aspects[j % n_aspects]
            suffix = f" (phần {j // n_aspects + 1})" if j >= n_aspects else ""
            lead = f"Xét các nhận định về {aspect}{suffix} của chuyên đề '{topic_prompt}' (SGK {subject_name} {grade_name}). Chọn Đúng / Sai cho từng mệnh đề:"
            q_num = len(questions) + 1
            questions.append({
                "part": "Part2",
                "question_type": "TrueFalse",
                "difficulty": None,
                "content": f"Câu {q_num}: {lead}",
                "content_markdown": lead,
                "explanation": f"Ôn kiến thức SGK về {aspect} của chuyên đề '{topic_prompt}'.",
                "segments": [
                    {"key": "a", "statement": f"'{topic_prompt}' là nội dung trọng tâm có trong SGK {subject_name} {grade_name}.", "is_correct": True},
                    {"key": "b", "statement": f"Để học tốt '{topic_prompt}', cần nắm vững khái niệm, công thức và {aspect} theo SGK.", "is_correct": True},
                    {"key": "c", "statement": f"Chuyên đề '{topic_prompt}' không có nội dung nào về {aspect} trong SGK.", "is_correct": False},
                    {"key": "d", "statement": f"Không cần ôn {aspect} của '{topic_prompt}' vì không bao giờ kiểm tra.", "is_correct": False}
                ]
            })

        # Part 3: Trả lời ngắn
        for k in range(part3_count):
            aspect = aspects[k % n_aspects]
            suffix = f" (phần {k // n_aspects + 1})" if k >= n_aspects else ""
            content = f"Nêu một {aspect}{suffix} điển hình của chuyên đề '{topic_prompt}' theo SGK {subject_name} {grade_name}?"
            q_num = len(questions) + 1
            questions.append({
                "part": "Part3",
                "question_type": "ShortAnswer",
                "difficulty": None,
                "content": f"Câu {q_num}: {content}",
                "content_markdown": content,
                "explanation": f"Ôn kiến thức SGK: {aspect} của '{topic_prompt}'.",
                "correct_answer": f"(nội dung {aspect} của '{topic_prompt}' theo SGK)"
            })

        return questions
