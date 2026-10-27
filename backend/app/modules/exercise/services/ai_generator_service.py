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
        part3_count: int
    ) -> List[Dict[str, Any]]:
        """
        Generates a list of question specifications with parts Part1 (MultipleChoice),
        Part2 (TrueFalse), and Part3 (ShortAnswer).
        Tries Gemini API first if configured; falls back to topic-based generator.
        """
        api_key = GeminiVisionParserService.get_api_key()
        if api_key:
            try:
                ai_questions = cls._call_gemini_generator(
                    api_key=api_key,
                    subject_name=subject_name,
                    grade_name=grade_name,
                    topic_prompt=topic_prompt,
                    part1_count=part1_count,
                    part2_count=part2_count,
                    part3_count=part3_count
                )
                if ai_questions and len(ai_questions) >= (part1_count + part2_count + part3_count):
                    return ai_questions
            except Exception as e:
                logger.warning(f"Gemini AI generation failed: {e}. Falling back to topic generator.")

        return cls._generate_curriculum_questions(
            subject_name=subject_name,
            grade_name=grade_name,
            topic_prompt=topic_prompt,
            part1_count=part1_count,
            part2_count=part2_count,
            part3_count=part3_count
        )

    @classmethod
    def _call_gemini_generator(
        cls,
        api_key: str,
        subject_name: str,
        grade_name: str,
        topic_prompt: str,
        part1_count: int,
        part2_count: int,
        part3_count: int
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

        user_prompt = f"""Tạo đề luyện tập môn {subject_name} ({grade_name}) theo chủ đề: "{topic_prompt}".
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

        # 4. DEFAULT / GENERAL CURRICULUM GENERATOR
        else:
            part1_pool = [
                {
                    "content": f"Theo chương trình {subject_name} {grade_name}, khái niệm cơ bản nào gắn liền mật thiết với chủ đề '{topic_prompt}'?",
                    "options": [
                        (f"Nắm vững các quy luật và tính chất cốt lõi của {topic_prompt}.", True),
                        (f"Bỏ qua các nguyên lý nền tảng để học mẹo giải nhanh.", False),
                        (f"Chỉ vận dụng lý thuyết mà không cần làm bài tập minh họa.", False),
                        (f"Chỉ ghi nhớ kết quả cuối cùng mà không hiểu bản chất hiện tượng.", False)
                    ],
                    "explanation": f"Nắm vững nguyên lý và phương pháp bản chất là chìa khóa xử lý chuyên đề {topic_prompt}."
                },
                {
                    "content": f"Khi phân tích nội dung về '{topic_prompt}', bước đầu tiên quan trọng nhất là:",
                    "options": [
                        ("Xác định chính xác các dữ kiện và đại lượng đã cho.", True),
                        ("Áp dụng công thức ngẫu nhiên bất kỳ.", False),
                        ("Ước lượng cảm tính kết quả.", False),
                        ("Bỏ qua các điều kiện xác định của bài toán.", False)
                    ],
                    "explanation": "Đọc kĩ đề và xác định dữ kiện là tiền đề của mọi phương pháp tư duy khoa học."
                },
                {
                    "content": f"Trong các bài tập chuyên đề '{topic_prompt}', dạng câu hỏi thường gặp nhất là:",
                    "options": [
                        ("Nhận biết các định nghĩa và vận dụng công thức tính toán cơ bản.", True),
                        ("Chứng minh các mệnh đề không có căn cứ thực nghiệm.", False),
                        ("Chỉ tập trung vào kiến thức ngoài sách giáo khoa.", False),
                        ("Các câu hỏi chỉ mang tính phỏng đoán lý thuyết.", False)
                    ],
                    "explanation": "Cấu trúc đề thi bám sát chuẩn kiến thức kĩ năng nhận biết và thông hiểu."
                },
                {
                    "content": f"Phương pháp tối ưu để rèn luyện kỹ năng giải nhanh các câu hỏi về '{topic_prompt}' là:",
                    "options": [
                        ("Hệ thống hóa kiến thức bằng sơ đồ tư duy và luyện tập có bấm giờ.", True),
                        ("Học vẹt đáp án mẫu mà không tự tay tính toán lại.", False),
                        ("Luyện đề một cách ngắt quãng và không tổng kết sai sót.", False),
                        ("Chỉ làm các câu hỏi khó vượt quá phân phối chương trình.", False)
                    ],
                    "explanation": "Sơ đồ hóa kiến thức và luyện phản xạ thời gian giúp nâng cao độ chính xác."
                },
                {
                    "content": f"Giá trị ứng dụng thực tiễn của chủ đề '{topic_prompt}' trong đời sống là:",
                    "options": [
                        ("Giải thích các hiện tượng khoa học và ứng dụng trong công nghệ, đời sống.", True),
                        ("Không có ứng dụng nào trong thực tế sản xuất và sinh hoạt.", False),
                        ("Chỉ có giá trị trên các trang giấy thi.", False),
                        ("Thay thế hoàn toàn mọi phương pháp nghiên cứu khác.", False)
                    ],
                    "explanation": "Mọi bài học trong chương trình đều gắn kết chặt chẽ với thực tiễn đời sống xã hội."
                }
            ]
            part2_pool = [
                {
                    "content": f"Xét các nhận định sau liên quan đến chuyên đề '{topic_prompt}'. Chọn Đúng / Sai cho từng mệnh đề:",
                    "segments": [
                        {"key": "a", "statement": f"Chủ đề '{topic_prompt}' là một nội dung trọng tâm của chương trình {subject_name} {grade_name}.", "is_correct": True},
                        {"key": "b", "statement": "Học sinh cần nắm vững phương pháp giải các dạng bài tập điển hình để đạt kết quả cao.", "is_correct": True},
                        {"key": "c", "statement": "Các câu hỏi trong chuyên đề này không tuân theo các quy luật chuẩn mực của môn học.", "is_correct": False},
                        {"key": "d", "statement": "Việc phân tích dữ liệu và rèn luyện tư duy logic giúp giải quyết chính xác các câu hỏi vận dụng.", "is_correct": True}
                    ],
                    "explanation": f"Học và rèn luyện theo đúng phương pháp khoa học là điều kiện tiên quyết cho chuyên đề {topic_prompt}."
                }
            ]
            part3_pool = [
                {
                    "content": f"Trong chuyên đề '{topic_prompt}', hệ số quy đổi chuẩn hoặc số mức độ phân loại thường được sử dụng là:",
                    "correct_answer": "4",
                    "explanation": "4 mức độ: Nhận biết, Thông hiểu, Vận dụng, Vận dụng cao."
                },
                {
                    "content": f"Số phương án lựa chọn trong mỗi câu trắc nghiệm nhiều lựa chọn chuẩn là bao nhiêu?",
                    "correct_answer": "4",
                    "explanation": "Gồm 4 phương án A, B, C, D."
                }
            ]

        # Assemble Part 1 questions
        for i in range(part1_count):
            template = part1_pool[i % len(part1_pool)]
            q_obj = {
                "part": "Part1",
                "question_type": "MultipleChoice",
                "difficulty": "NhanBiet" if i < 2 else ("ThongHieu" if i < 4 else "VanDung"),
                "content": f"Câu {i + 1}: {template['content']}",
                "content_markdown": template['content'],
                "explanation": template.get("explanation"),
                "answer_options": [
                    {"content": opt[0], "is_correct": opt[1], "display_order": idx}
                    for idx, opt in enumerate(template["options"])
                ]
            }
            questions.append(q_obj)

        # Assemble Part 2 questions
        for j in range(part2_count):
            template = part2_pool[j % len(part2_pool)]
            q_num = part1_count + j + 1
            q_obj = {
                "part": "Part2",
                "question_type": "TrueFalse",
                "difficulty": "ThongHieu" if j == 0 else "VanDung",
                "content": f"Câu {q_num}: {template['content']}",
                "content_markdown": template['content'],
                "explanation": template.get("explanation"),
                "segments": template.get("segments", [])
            }
            questions.append(q_obj)

        # Assemble Part 3 questions
        for k in range(part3_count):
            template = part3_pool[k % len(part3_pool)]
            q_num = part1_count + part2_count + k + 1
            q_obj = {
                "part": "Part3",
                "question_type": "ShortAnswer",
                "difficulty": "VanDung" if k == 0 else "VanDungCao",
                "content": f"Câu {q_num}: {template['content']}",
                "content_markdown": template['content'],
                "explanation": template.get("explanation"),
                "correct_answer": template.get("correct_answer", "0")
            }
            questions.append(q_obj)

        return questions
