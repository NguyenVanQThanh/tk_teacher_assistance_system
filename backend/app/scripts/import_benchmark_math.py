import os
import uuid
import dotenv
dotenv.load_dotenv()

from app.core.database import SessionLocal
from models.models import Exercise, Question, AnswerOption
from app.modules.exercise.services.import_parser_service import ImportParserService

db = SessionLocal()
ex = db.query(Exercise).filter(Exercise.exercise_id == '3ad4c004-9616-4ee1-9b88-e281596bfa7b').first()
if not ex:
    print("Exercise not found")
    exit(1)

# Delete existing questions
db.query(Question).filter(Question.exercise_id == ex.exercise_id).delete()
db.commit()

questions_data = [
    # --- PART 1 ---
    {
        "order": 1,
        "type": "MultipleChoice",
        "diff": "NB",
        "stem": r"Cho hàm số $f(x) = x^3 - 3x^2 + 2$. Giá trị cực đại của hàm số là:",
        "options": [
            ("A. $0$", False),
            ("B. $2$", True),
            ("C. $-2$", False),
            ("D. $4$", False),
        ]
    },
    {
        "order": 2,
        "type": "MultipleChoice",
        "diff": "TH",
        "stem": r"Tập nghiệm của bất phương trình $\log_2(x - 1) < 3$ là:",
        "options": [
            ("A. $(1; 9)$", True),
            ("B. $(-\infty; 9)$", False),
            ("C. $(1; +\infty)$", False),
            ("D. $[1; 9]$", False),
        ]
    },
    {
        "order": 3,
        "type": "MultipleChoice",
        "diff": "TH",
        "stem": r"Một nguyên hàm của hàm số $f(x) = \frac{2x}{x^2 + 1}$ là:",
        "options": [
            (r"A. $\ln(x^2 + 1) + C$", True),
            (r"B. $2\ln(x^2 + 1) + C$", False),
            (r"C. $\frac{1}{x^2 + 1} + C$", False),
            (r"D. $\frac{x^2}{x^2 + 1} + C$", False),
        ]
    },
    {
        "order": 4,
        "type": "MultipleChoice",
        "diff": "TH",
        "stem": r"Trong không gian $Oxyz$, mặt phẳng đi qua $A(1; -2; 3)$ và có vectơ pháp tuyến $\vec{n} = (2; 1; -1)$ có phương trình là:",
        "options": [
            (r"A. $2x + y - z + 3 = 0$", False),
            (r"B. $2x + y - z - 3 = 0$", True),
            (r"C. $2x + y + z - 3 = 0$", False),
            (r"D. $x + 2y - z + 3 = 0$", False),
        ]
    },
    {
        "order": 5,
        "type": "MultipleChoice",
        "diff": "VD",
        "stem": r"Cho hàm số $$y = \frac{x^2 + 1}{x - 1}.$$ Số đường tiệm cận đứng của đồ thị hàm số là:",
        "options": [
            ("A. $0$", False),
            ("B. $1$", True),
            ("C. $2$", False),
            ("D. $3$", False),
        ]
    },
    {
        "order": 6,
        "type": "MultipleChoice",
        "diff": "VD",
        "stem": r"Một vật chuyển động theo phương trình $s(t) = t^3 - 6t^2 + 9t, t \ge 0$. Vận tốc bằng $0$ tại các thời điểm:",
        "options": [
            (r"A. $t = 1\text{ và }t = 3$", False),
            (r"B. $t = 0\text{ và }t = 3$", False),
            (r"C. $t = 1\text{ và }t = 2$", True),
            (r"D. $t = 2\text{ và }t = 3$", False),
        ]
    },
    {
        "order": 7,
        "type": "MultipleChoice",
        "diff": "VD",
        "stem": r"Một hình trụ có bán kính đáy $r = 3$ và chiều cao $h = 5$. Thể tích của hình trụ là:",
        "options": [
            (r"A. $15\pi$", False),
            (r"B. $30\pi$", False),
            (r"C. $45\pi$", True),
            (r"D. $90\pi$", False),
        ]
    },
    {
        "order": 8,
        "type": "MultipleChoice",
        "diff": "VD",
        "stem": r"Cho hai vectơ $\vec{a} = (1; 2; -1)$, $\vec{b} = (2; -1; 3)$. Khi đó $\vec{a} \cdot \vec{b}$ bằng:",
        "options": [
            ("A. $-5$", False),
            ("B. $-3$", False),
            ("C. $1$", True),
            ("D. $5$", False),
        ]
    },
    {
        "order": 9,
        "type": "MultipleChoice",
        "diff": "VD",
        "stem": r"Hàm số $$y = \frac{x^2 + 1}{x - 1}$$ có số đường tiệm cận đứng và ngang lần lượt là:",
        "options": [
            (r"A. $1\text{ và }0$", False),
            (r"B. $1\text{ và }1$", True),
            (r"C. $0\text{ và }1$", False),
            (r"D. $2\text{ và }1$", False),
        ]
    },
    {
        "order": 10,
        "type": "MultipleChoice",
        "diff": "VDC",
        "stem": r"Với $m$ là tham số, phương trình $x^3 - 3x + m = 0$ có ba nghiệm thực phân biệt khi:",
        "options": [
            (r"A. $-2 < m < 2$", True),
            (r"B. $m < -2$", False),
            (r"C. $m > 2$", False),
            (r"D. $|m| \ge 2$", False),
        ]
    },
    {
        "order": 11,
        "type": "MultipleChoice",
        "diff": "VDC",
        "stem": r"Một nhà sản xuất thiết kế hộp chữ nhật không nắp có thể tích $108\text{ cm}^3$, đáy là hình vuông cạnh $x$. Diện tích vật liệu nhỏ nhất đạt được khi $x$ bằng:",
        "options": [
            (r"A. $3\text{ cm}$", False),
            (r"B. $4\text{ cm}$", True),
            (r"C. $6\text{ cm}$", False),
            (r"D. $9\text{ cm}$", False),
        ]
    },
    {
        "order": 12,
        "type": "MultipleChoice",
        "diff": "VDC",
        "stem": r"Trong không gian $Oxyz$, cho $A(1; 0; 0), B(0; 2; 0), C(0; 0; 3)$. Khoảng cách từ $O$ đến mặt phẳng $(ABC)$ bằng:",
        "options": [
            (r"A. $\frac{6}{\sqrt{61}}$", False),
            (r"B.", False),
            (r"C. $\frac{1}{\sqrt{61}}$", True),
            (r"D. $\frac{6}{7}$", False),
        ],
        "needs_review": True,
        "confidence_score": 0.50
    },

    # --- PART 2 ---
    {
        "order": 13,
        "type": "TrueFalse",
        "diff": None,
        "stem": r"Cho hàm số $y = x^3 - 3x^2 + 2$.",
        "options": [
            ("a) Hàm số có hai điểm cực trị.", True),
            ("b) Hàm số đồng biến trên khoảng $(-\\infty; 0)$.", False),
            ("c) Giá trị cực đại của hàm số bằng $2$.", True),
            ("d) Phương trình $f(x) = 0$ có đúng hai nghiệm thực.", False),
        ]
    },
    {
        "order": 14,
        "type": "TrueFalse",
        "diff": None,
        "stem": r"Trong không gian $Oxyz$, cho $A(1; 2; -1), B(3; -1; 2)$.",
        "options": [
            (r"a) Vectơ $\vec{AB} = (2; -3; 3)$.", True),
            (r"b) Độ dài $AB = \sqrt{22}$.", True),
            (r"c) Trung điểm của $AB$ là $M\left(2; \frac{1}{2}; \frac{1}{2}\right)$.", True),
            (r"d) Mặt phẳng trung trực của $AB$ có vectơ pháp tuyến $(2; -3; 3)$.", True),
        ]
    },
    {
        "order": 15,
        "type": "TrueFalse",
        "diff": None,
        "stem": r"Cho hàm số $f(x) = \ln(x^2 + 1)$.",
        "options": [
            (r"a) $f'(x) = \frac{2x}{x^2 + 1}$.", True),
            (r"b) Hàm số đồng biến trên $\mathbb{R}$.", True),
            (r"c) Hàm số đạt giá trị nhỏ nhất bằng $0$.", True),
            (r"d) Đồ thị hàm số có tiệm cận ngang.", False),
        ]
    },
    {
        "order": 16,
        "type": "TrueFalse",
        "diff": None,
        "stem": r"Một hình hộp chữ nhật có ba kích thước $2, 3$ và $6$.",
        "options": [
            ("a) Thể tích hình hộp bằng $36$.", True),
            ("b) Độ dài đường chéo bằng $7$.", True),
            ("c) Diện tích toàn phần bằng $72$.", True),
            ("d) Khoảng cách giữa hai mặt phẳng đối diện có diện tích lớn nhất bằng $6$.", True),
        ]
    },

    # --- PART 3 ---
    {
        "order": 17,
        "type": "ShortAnswer",
        "diff": "TH",
        "stem": r"Cho hàm số $f(x) = x^3 - 3x + 1$. Tính giá trị $f(2)$.",
        "correct_answer": "3"
    },
    {
        "order": 18,
        "type": "ShortAnswer",
        "diff": "VD",
        "stem": r"Một hình trụ có thể tích $V = 1000\text{ cm}^3$. Biết bán kính đáy bằng $5\text{ cm}$. Tính chiều cao $h$ của hình trụ (làm tròn đến hàng phần mười).",
        "correct_answer": "12,7"
    },
    {
        "order": 19,
        "type": "ShortAnswer",
        "diff": "VD",
        "stem": r"Trong không gian $Oxyz$, cho $A(1; 2; 3)$ và $B(4; 6; 3)$. Tính khoảng cách $AB$.",
        "correct_answer": "5"
    },
    {
        "order": 20,
        "type": "ShortAnswer",
        "diff": "VDC",
        "stem": r"Một doanh nghiệp có chi phí $C(x) = x^2 - 20x + 300$ (triệu đồng) khi sản xuất $x$ sản phẩm. Doanh thu $R(x) = 80x - 0.5x^2$ (triệu đồng). Với $x \in [0; 60]$, số sản phẩm cần sản xuất để lợi nhuận lớn nhất là bao nhiêu?",
        "correct_answer": "100"
    }
]

for q_data in questions_data:
    stem_latex = q_data["stem"]
    stem_markdown = ImportParserService.convert_latex_to_markdown(stem_latex)
    segments, needs_review = ImportParserService.extract_segments(stem_latex)

    conf = q_data.get("confidence_score", 0.98 if not needs_review else 0.70)
    rev = q_data.get("needs_review", needs_review)

    q = Question(
        exercise_id=ex.exercise_id,
        display_order=q_data["order"],
        question_type=q_data["type"],
        difficulty=q_data["diff"],
        content=stem_latex,
        content_markdown=stem_markdown,
        content_latex=stem_latex,
        segments=segments,
        confidence_score=conf,
        needs_review=rev,
        correct_answer=q_data.get("correct_answer"),
        status="ACTIVE"
    )
    db.add(q)
    db.flush()

    for idx, (opt_text, is_corr) in enumerate(q_data.get("options", [])):
        opt = AnswerOption(
            question_id=q.question_id,
            content=opt_text,
            is_correct=is_corr,
            display_order=idx
        )
        db.add(opt)

ex.total_questions = len(questions_data)
db.commit()
print(f"Successfully inserted {len(questions_data)} benchmark questions with full math expressions!")
