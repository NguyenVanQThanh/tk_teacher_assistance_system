# File Name: seed_exercises_data.py
# Description: Idempotent database seed script for exercises, questions, and answer options with standard LaTeX formatting.
# Created At: 2026-09-01
# Created By: Tam Khang
# Updated At: 2026-09-01
# Updated By: Tam Khang

import os
import sys
import uuid
from pathlib import Path

# Ensure UTF-8 output encoding on Windows console
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Ensure backend root is in sys.path
backend_root = str(Path(__file__).resolve().parent.parent.parent)
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.models import User, Subject, Exercise, Question, AnswerOption

load_dotenv()

DB_USERNAME = os.environ.get("DB_USERNAME") or os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME")

DATABASE_URL = f"postgresql+psycopg2://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def seed_sample_exercises():
    session = SessionLocal()
    try:
        print("--- [1] Finding Sample Teacher and Subjects ---")
        teacher = session.query(User).filter(User.phone == "0999000002").first()
        if not teacher:
            raise ValueError("Sample Teacher (0999000002) not found. Run seed_academic_data.py first.")

        math_subj = session.query(Subject).filter(Subject.subject_name == "Toán học").first()
        phys_subj = session.query(Subject).filter(Subject.subject_name == "Vật lý").first()
        chem_subj = session.query(Subject).filter(Subject.subject_name == "Hóa học").first()
        bio_subj = session.query(Subject).filter(Subject.subject_name == "Sinh học").first()
        hist_subj = session.query(Subject).filter(Subject.subject_name == "Lịch sử").first()

        if not math_subj or not phys_subj:
            raise ValueError("Subjects not found. Run seed_academic_data.py first.")

        exercises_blueprint = [
            {
                "title": "Kiểm tra 15p – Đạo hàm & Cực trị",
                "subject": math_subj,
                "ai_metadata": {"grade": "12", "duration": "15 phút", "type": "quiz"},
                "questions": [
                    {
                        "content": "Cho hàm số $y = f(x)$ có đạo hàm $f'(x) = x(x - 1)(x + 2)^3$ trên $\\mathbb{R}$. Số điểm cực trị của hàm số đã cho là:",
                        "difficulty": "Thông hiểu",
                        "question_type": "MultipleChoice",
                        "correct_answer": "A",
                        "options": [
                            {"content": "$3$", "is_correct": True, "order": 1},
                            {"content": "$2$", "is_correct": False, "order": 2},
                            {"content": "$1$", "is_correct": False, "order": 3},
                            {"content": "$4$", "is_correct": False, "order": 4},
                        ]
                    },
                    {
                        "content": "Tìm đạo hàm của hàm số $f(x) = (2x^2 + 1)^3$ tại điểm $x = 1$:",
                        "difficulty": "Vận dụng",
                        "question_type": "MultipleChoice",
                        "correct_answer": "B",
                        "options": [
                            {"content": "$36$", "is_correct": False, "order": 1},
                            {"content": "$108$", "is_correct": True, "order": 2},
                            {"content": "$54$", "is_correct": False, "order": 3},
                            {"content": "$72$", "is_correct": False, "order": 4},
                        ]
                    },
                    {
                        "content": "Giá trị cực đại của hàm số $y = x^3 - 3x + 2$ là:",
                        "difficulty": "Nhận biết",
                        "question_type": "MultipleChoice",
                        "correct_answer": "C",
                        "options": [
                            {"content": "$0$", "is_correct": False, "order": 1},
                            {"content": "$2$", "is_correct": False, "order": 2},
                            {"content": "$4$", "is_correct": True, "order": 3},
                            {"content": "$-1$", "is_correct": False, "order": 4},
                        ]
                    },
                    {
                        "content": "Hàm số $y = -x^4 + 2x^2 + 1$ đồng biến trên khoảng nào dưới đây?",
                        "difficulty": "Thông hiểu",
                        "question_type": "MultipleChoice",
                        "correct_answer": "A",
                        "options": [
                            {"content": "$(-\\infty; -1)$", "is_correct": True, "order": 1},
                            {"content": "$(-1; 1)$", "is_correct": False, "order": 2},
                            {"content": "$(0; +\\infty)$", "is_correct": False, "order": 3},
                            {"content": "$(-1; 0)$", "is_correct": False, "order": 4},
                        ]
                    }
                ]
            },
            {
                "title": "Bài tập về nhà – Quang hình học & Khúc xạ",
                "subject": phys_subj,
                "ai_metadata": {"grade": "11", "duration": "45 phút", "type": "homework"},
                "questions": [
                    {
                        "content": "Hiện tượng khúc xạ ánh sáng là hiện tượng tia sáng tới khi truyền qua mặt phân cách giữa hai môi trường trong suốt:",
                        "difficulty": "Nhận biết",
                        "question_type": "MultipleChoice",
                        "correct_answer": "A",
                        "options": [
                            {"content": "Bị gãy khúc tại mặt phân cách", "is_correct": True, "order": 1},
                            {"content": "Bị hắt trở lại môi trường cũ", "is_correct": False, "order": 2},
                            {"content": "Truyền thẳng không đổi hướng", "is_correct": False, "order": 3},
                            {"content": "Bị hấp thụ hoàn toàn", "is_correct": False, "order": 4},
                        ]
                    },
                    {
                        "content": "Chiết suất tuyệt đối của một môi trường trong suốt $n$ luôn thỏa mãn:",
                        "difficulty": "Nhận biết",
                        "question_type": "MultipleChoice",
                        "correct_answer": "B",
                        "options": [
                            {"content": "$n < 1$", "is_correct": False, "order": 1},
                            {"content": "$n \\ge 1$", "is_correct": True, "order": 2},
                            {"content": "$n = 0$", "is_correct": False, "order": 3},
                            {"content": "$n < 0$", "is_correct": False, "order": 4},
                        ]
                    },
                    {
                        "content": "Một tia sáng đi từ nước ($n = \\frac{4}{3}$) ra không khí với góc tới $i = 30^\\circ$. Góc khúc xạ $r$ xấp xỉ bằng:",
                        "difficulty": "Vận dụng",
                        "question_type": "MultipleChoice",
                        "correct_answer": "C",
                        "options": [
                            {"content": "$38.5^\\circ$", "is_correct": False, "order": 1},
                            {"content": "$45.0^\\circ$", "is_correct": False, "order": 2},
                            {"content": "$41.8^\\circ$", "is_correct": True, "order": 3},
                            {"content": "$22.0^\\circ$", "is_correct": False, "order": 4},
                        ]
                    }
                ]
            },
            {
                "title": "Kiểm tra cuối kỳ – Đại số và Giải tích 10",
                "subject": math_subj,
                "ai_metadata": {"grade": "10", "duration": "60 phút", "type": "test"},
                "questions": [
                    {
                        "content": "Tập xác định của hàm số $y = \\sqrt{2x - 4}$ là:",
                        "difficulty": "Nhận biết",
                        "question_type": "MultipleChoice",
                        "correct_answer": "D",
                        "options": [
                            {"content": "$(-\\infty; 2]$", "is_correct": False, "order": 1},
                            {"content": "$(2; +\\infty)$", "is_correct": False, "order": 2},
                            {"content": "$\\mathbb{R} \\setminus \\{2\\}$", "is_correct": False, "order": 3},
                            {"content": "$[2; +\\infty)$", "is_correct": True, "order": 4},
                        ]
                    },
                    {
                        "content": "Đỉnh của parabol $y = -x^2 + 4x - 3$ có tọa độ là:",
                        "difficulty": "Thông hiểu",
                        "question_type": "MultipleChoice",
                        "correct_answer": "B",
                        "options": [
                            {"content": "$I(-2; -1)$", "is_correct": False, "order": 1},
                            {"content": "$I(2; 1)$", "is_correct": True, "order": 2},
                            {"content": "$I(1; 0)$", "is_correct": False, "order": 3},
                            {"content": "$I(2; -3)$", "is_correct": False, "order": 4},
                        ]
                    },
                    {
                        "content": "Phương trình $x^2 - 2(m + 1)x + m^2 = 0$ có hai nghiệm phân biệt khi và chỉ khi:",
                        "difficulty": "Vận dụng",
                        "question_type": "MultipleChoice",
                        "correct_answer": "A",
                        "options": [
                            {"content": "$m > -\\frac{1}{2}$", "is_correct": True, "order": 1},
                            {"content": "$m < -\\frac{1}{2}$", "is_correct": False, "order": 2},
                            {"content": "$m \\ge -\\frac{1}{2}$", "is_correct": False, "order": 3},
                            {"content": "$m \\ne 0$", "is_correct": False, "order": 4},
                        ]
                    }
                ]
            },
            {
                "title": "Bài tập về nhà – Hình học không gian Oxyz",
                "subject": math_subj,
                "ai_metadata": {"grade": "12", "duration": "30 phút", "type": "homework"},
                "questions": [
                    {
                        "content": "Trong không gian $Oxyz$, cho mặt phẳng $(P): 2x - y + 3z - 4 = 0$. Vectơ pháp tuyến của $(P)$ là:",
                        "difficulty": "Nhận biết",
                        "question_type": "MultipleChoice",
                        "correct_answer": "A",
                        "options": [
                            {"content": "$\\vec{n} = (2; -1; 3)$", "is_correct": True, "order": 1},
                            {"content": "$\\vec{n} = (2; 1; 3)$", "is_correct": False, "order": 2},
                            {"content": "$\\vec{n} = (-2; 1; 3)$", "is_correct": False, "order": 3},
                            {"content": "$\\vec{n} = (2; -1; -4)$", "is_correct": False, "order": 4},
                        ]
                    },
                    {
                        "content": "Khoảng cách từ điểm $M(1; 2; -3)$ đến mặt phẳng $(Oxy)$ bằng:",
                        "difficulty": "Thông hiểu",
                        "question_type": "MultipleChoice",
                        "correct_answer": "C",
                        "options": [
                            {"content": "$1$", "is_correct": False, "order": 1},
                            {"content": "$2$", "is_correct": False, "order": 2},
                            {"content": "$3$", "is_correct": True, "order": 3},
                            {"content": "$\\sqrt{14}$", "is_correct": False, "order": 4},
                        ]
                    }
                ]
            },
            {
                "title": "Ôn tập chương 2 – Hóa học hữu cơ & Hidrocacbon",
                "subject": chem_subj if chem_subj else math_subj,
                "ai_metadata": {"grade": "11", "duration": "45 phút", "type": "quiz"},
                "questions": [
                    {
                        "content": "Công thức phân tử tổng quát của dãy đồng đẳng ankan là:",
                        "difficulty": "Nhận biết",
                        "question_type": "MultipleChoice",
                        "correct_answer": "B",
                        "options": [
                            {"content": "$\\text{C}_n\\text{H}_{2n} \\ (n \\ge 2)$", "is_correct": False, "order": 1},
                            {"content": "$\\text{C}_n\\text{H}_{2n+2} \\ (n \\ge 1)$", "is_correct": True, "order": 2},
                            {"content": "$\\text{C}_n\\text{H}_{2n-2} \\ (n \\ge 2)$", "is_correct": False, "order": 3},
                            {"content": "$\\text{C}_n\\text{H}_{2n-6} \\ (n \\ge 6)$", "is_correct": False, "order": 4},
                        ]
                    },
                    {
                        "content": "Khí metan ($\\text{CH}_4$) phản ứng đặc trưng với khí clo ($\\text{Cl}_2$) ngoài ánh sáng theo cơ chế nào?",
                        "difficulty": "Thông hiểu",
                        "question_type": "MultipleChoice",
                        "correct_answer": "A",
                        "options": [
                            {"content": "Phản ứng thế", "is_correct": True, "order": 1},
                            {"content": "Phản ứng cộng", "is_correct": False, "order": 2},
                            {"content": "Phản ứng tách", "is_correct": False, "order": 3},
                            {"content": "Phản ứng trùng hợp", "is_correct": False, "order": 4},
                        ]
                    }
                ]
            },
            {
                "title": "Kiểm tra 15p – Este và Lipit (Hóa học 12)",
                "subject": chem_subj if chem_subj else math_subj,
                "ai_metadata": {"grade": "12", "duration": "15 phút", "type": "quiz"},
                "questions": [
                    {
                        "content": "Este etyl axetat có công thức phân tử là:",
                        "difficulty": "Nhận biết",
                        "question_type": "MultipleChoice",
                        "correct_answer": "B",
                        "options": [
                            {"content": "$\\text{CH}_3\\text{COOCH}_3$", "is_correct": False, "order": 1},
                            {"content": "$\\text{CH}_3\\text{COOC}_2\\text{H}_5$", "is_correct": True, "order": 2},
                            {"content": "$\\text{HCOOC}_2\\text{H}_5$", "is_correct": False, "order": 3},
                            {"content": "$\\text{C}_2\\text{H}_5\\text{COOCH}_3$", "is_correct": False, "order": 4},
                        ]
                    },
                    {
                        "content": "Thủy phân hoàn toàn $8.8\\text{ gam}$ etyl axetat trong dung dịch $\\text{NaOH}$ dư thu được khối lượng muối natri axetat là:",
                        "difficulty": "Vận dụng",
                        "question_type": "MultipleChoice",
                        "correct_answer": "A",
                        "options": [
                            {"content": "$8.2\\text{ gam}$", "is_correct": True, "order": 1},
                            {"content": "$6.8\\text{ gam}$", "is_correct": False, "order": 2},
                            {"content": "$9.4\\text{ gam}$", "is_correct": False, "order": 3},
                            {"content": "$10.2\\text{ gam}$", "is_correct": False, "order": 4},
                        ]
                    }
                ]
            },
            {
                "title": "Kiểm tra 15p – Cơ chế di truyền và biến dị (Sinh học 12)",
                "subject": bio_subj if bio_subj else math_subj,
                "ai_metadata": {"grade": "12", "duration": "15 phút", "type": "quiz"},
                "questions": [
                    {
                        "content": "Một phân tử ADN mạch kép có số nuclêôtit loại A chiếm $20\\%$. Tỉ lệ nuclêôtit loại G của phân tử này là:",
                        "difficulty": "Thông hiểu",
                        "question_type": "MultipleChoice",
                        "correct_answer": "C",
                        "options": [
                            {"content": "$20\\%$", "is_correct": False, "order": 1},
                            {"content": "$40\\%$", "is_correct": False, "order": 2},
                            {"content": "$30\\%$", "is_correct": True, "order": 3},
                            {"content": "$10\\%$", "is_correct": False, "order": 4},
                        ]
                    },
                    {
                        "content": "Quá trình nhân đôi ADN diễn ra theo nguyên tắc nào sau đây?",
                        "difficulty": "Nhận biết",
                        "question_type": "MultipleChoice",
                        "correct_answer": "A",
                        "options": [
                            {"content": "Bổ sung và bán bảo toàn", "is_correct": True, "order": 1},
                            {"content": "Bảo toàn hoàn toàn", "is_correct": False, "order": 2},
                            {"content": "Khuôn mẫu gián đoạn", "is_correct": False, "order": 3},
                            {"content": "Tự do ngẫu nhiên", "is_correct": False, "order": 4},
                        ]
                    }
                ]
            },
            {
                "title": "Kiểm tra 15p – Cách mạng tháng Tám năm 1945 (Lịch sử 12)",
                "subject": hist_subj if hist_subj else math_subj,
                "ai_metadata": {"grade": "12", "duration": "15 phút", "type": "quiz"},
                "questions": [
                    {
                        "content": "Chủ tịch Hồ Chí Minh đọc bản Tuyên ngôn Độc lập khai sinh ra nước Việt Nam Dân chủ Cộng hòa vào ngày nào?",
                        "difficulty": "Nhận biết",
                        "question_type": "MultipleChoice",
                        "correct_answer": "A",
                        "options": [
                            {"content": "Ngày 02/09/1945", "is_correct": True, "order": 1},
                            {"content": "Ngày 19/08/1945", "is_correct": False, "order": 2},
                            {"content": "Ngày 23/08/1945", "is_correct": False, "order": 3},
                            {"content": "Ngày 25/08/1945", "is_correct": False, "order": 4},
                        ]
                    },
                    {
                        "content": "Sự kiện nào đánh dấu bước ngoặt quyết định của phong trào giải phóng dân tộc Việt Nam năm 1945?",
                        "difficulty": "Thông hiểu",
                        "question_type": "MultipleChoice",
                        "correct_answer": "D",
                        "options": [
                            {"content": "Hội nghị thành lập Mặt trận Việt Minh", "is_correct": False, "order": 1},
                            {"content": "Khởi nghĩa Ba Tơ", "is_correct": False, "order": 2},
                            {"content": "Chỉ thị Nhật - Pháp bắn nhau", "is_correct": False, "order": 3},
                            {"content": "Thắng lợi của Cách mạng tháng Tám năm 1945", "is_correct": True, "order": 4},
                        ]
                    }
                ]
            }
        ]

        print("--- [2] Updating Exercises, Questions and Options with LaTeX ---")
        for ex_data in exercises_blueprint:
            existing_ex = session.query(Exercise).filter(
                Exercise.title == ex_data["title"],
                Exercise.created_by == teacher.user_id,
            ).first()

            if existing_ex:
                # Remove old questions to re-seed clean LaTeX questions
                session.query(Question).filter(Question.exercise_id == existing_ex.exercise_id).delete()
                new_ex = existing_ex
                new_ex.total_questions = len(ex_data["questions"])
                new_ex.ai_metadata = ex_data["ai_metadata"]
                new_ex.status = "ACTIVE"
            else:
                new_ex = Exercise(
                    exercise_id=uuid.uuid4(),
                    title=ex_data["title"],
                    subject_id=ex_data["subject"].subject_id,
                    created_by=teacher.user_id,
                    total_questions=len(ex_data["questions"]),
                    ai_metadata=ex_data["ai_metadata"],
                    status="ACTIVE"
                )
                session.add(new_ex)
                session.flush()

            for q_idx, q_data in enumerate(ex_data["questions"], start=1):
                new_q = Question(
                    question_id=uuid.uuid4(),
                    exercise_id=new_ex.exercise_id,
                    content=q_data["content"],
                    question_type=q_data["question_type"],
                    difficulty=q_data["difficulty"],
                    correct_answer=q_data["correct_answer"],
                    display_order=q_idx,
                    status="ACTIVE"
                )
                session.add(new_q)
                session.flush()

                for opt_data in q_data.get("options", []):
                    new_opt = AnswerOption(
                        option_id=uuid.uuid4(),
                        question_id=new_q.question_id,
                        content=opt_data["content"],
                        is_correct=opt_data["is_correct"],
                        display_order=opt_data["order"]
                    )
                    session.add(new_opt)

            print(f"Updated Exercise: '{new_ex.title}' with {len(ex_data['questions'])} LaTeX formatted questions.")

        session.commit()
        print("\nAll LaTeX formatted sample exercises updated successfully!")

    except Exception as e:
        session.rollback()
        print(f"Error seeding exercises: {e}")
        raise e
    finally:
        session.close()


if __name__ == "__main__":
    seed_sample_exercises()
