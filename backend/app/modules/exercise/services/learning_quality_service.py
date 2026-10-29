# File Name: learning_quality_service.py
# Description: Service for computing homeroom class learning quality radar metrics and dynamic grade-level comparison remarks based strictly on genuine student attempt data.
# Created At: 2026-10-29
# Created By: Tam Khang
# Updated At: 2026-10-29
# Updated By: Tam Khang

from datetime import date
import re
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func

from models.models import (
    User, Class, StudentClass, TeacherSubject, Subject,
    ClassAssignment, Exercise, StudentExerciseAttempt
)

RADAR_AXES = [
    {"name": "Toán Học", "keywords": ["toán"]},
    {"name": "Vật Lí", "keywords": ["vật lý", "vật lí", "vật"]},
    {"name": "Hóa Học", "keywords": ["hóa học", "hóa"]},
    {"name": "Tiếng Anh", "keywords": ["tiếng anh", "anh"]},
    {"name": "Lịch Sử", "keywords": ["lịch sử", "sử"]},
    {"name": "Tin học", "keywords": ["tin học", "tin"]},
]


class LearningQualityService:
    """
    Computes academic quality metrics for homeroom teacher dashboards,
    including class average scores per subject, grade cohort benchmarks,
    and comparative pedagogical observations strictly from real database records.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_homeroom_learning_quality(
        self,
        teacher_user: User,
        class_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Calculates radar subject scores (class average vs grade cohort average)
        and comparative observations for the target homeroom class.
        Strictly computes from actual student exercise attempts without fabricated benchmarks.
        """
        today = date.today()
        start_year = today.year if today.month >= 8 else today.year - 1
        current_year = f"{start_year}-{start_year + 1}"

        # 1. Resolve target homeroom class
        target_class = None
        if class_id:
            target_class = self.db.query(Class).filter(
                Class.class_id == class_id,
                Class.status != "DELETED"
            ).first()

        # Priority 1: Homeroom class assigned to current user in current academic year
        if not target_class:
            target_class = self.db.query(Class).filter(
                Class.homeroom_teacher_id == teacher_user.user_id,
                Class.academic_year == current_year,
                Class.status != "DELETED"
            ).first()

        # If teacher has no homeroom class assigned in current academic year, return clean empty state
        if not target_class:
            return {
                "class_name": "",
                "grade_name": "",
                "radar_data": [
                    {"subject_name": axis["name"], "class_score": 0.0, "grade_score": 0.0}
                    for axis in RADAR_AXES
                ],
                "feedback_notes": [
                    f"Giáo viên chưa được phân công làm giáo viên chủ nhiệm trong năm học hiện tại ({current_year})."
                ]
            }

        # 2. Extract Grade Cohort (e.g. "12" from "12A1" -> "Khối 12")
        clean_name = target_class.class_name.strip()
        grade_match = re.match(r"^(\d{1,2})", clean_name)
        grade_num = grade_match.group(1) if grade_match else ""
        grade_label = f"Khối {grade_num}" if grade_num else "Khối"

        # Query active classes in the SAME academic year
        year_classes = self.db.query(Class).filter(
            Class.academic_year == target_class.academic_year,
            Class.status != "DELETED"
        ).all()

        # Match classes that strictly start with grade_num followed by a non-digit character or end of string
        # This matches '12A1', '12A2', '12B' but NEVER '11A12' or '112'
        if grade_num:
            grade_pattern = re.compile(rf"^{re.escape(grade_num)}(?:[^\d]|$)")
            grade_classes = [c for c in year_classes if grade_pattern.match(c.class_name.strip())]
        else:
            grade_classes = [target_class]

        grade_class_ids = [c.class_id for c in grade_classes]
        if target_class.class_id not in grade_class_ids:
            grade_class_ids.append(target_class.class_id)

        # 3. Retrieve all active subjects in database
        all_subjects = self.db.query(Subject).filter(Subject.status != "DELETED").all()

        # 4. Compute genuine class average and grade cohort average per radar axis from database attempts
        radar_data = []
        for axis in RADAR_AXES:
            axis_name = axis["name"]
            matched_subject = None
            for s in all_subjects:
                s_lower = s.subject_name.lower()
                if any(kw in s_lower for kw in axis["keywords"]):
                    matched_subject = s
                    break

            c_score = 0.0
            g_score = 0.0

            if matched_subject:
                # Average score of all graded attempts for students of target_class in the current academic year
                class_avg = self.db.query(func.avg(StudentExerciseAttempt.score)).join(
                    ClassAssignment, StudentExerciseAttempt.assignment_id == ClassAssignment.assignment_id
                ).join(
                    Class, ClassAssignment.class_id == Class.class_id
                ).join(
                    Exercise, ClassAssignment.exercise_id == Exercise.exercise_id
                ).filter(
                    Class.class_id == target_class.class_id,
                    Class.academic_year == target_class.academic_year,
                    Class.status != "DELETED",
                    ClassAssignment.status != "DELETED",
                    Exercise.subject_id == matched_subject.subject_id,
                    Exercise.status != "DELETED",
                    StudentExerciseAttempt.status != "DELETED",
                    StudentExerciseAttempt.score.isnot(None)
                ).scalar()

                # Average score of all graded attempts across all classes in the grade cohort in the current academic year
                grade_avg = self.db.query(func.avg(StudentExerciseAttempt.score)).join(
                    ClassAssignment, StudentExerciseAttempt.assignment_id == ClassAssignment.assignment_id
                ).join(
                    Class, ClassAssignment.class_id == Class.class_id
                ).join(
                    Exercise, ClassAssignment.exercise_id == Exercise.exercise_id
                ).filter(
                    Class.class_id.in_(grade_class_ids),
                    Class.academic_year == target_class.academic_year,
                    Class.status != "DELETED",
                    ClassAssignment.status != "DELETED",
                    Exercise.subject_id == matched_subject.subject_id,
                    Exercise.status != "DELETED",
                    StudentExerciseAttempt.status != "DELETED",
                    StudentExerciseAttempt.score.isnot(None)
                ).scalar()

                if class_avg is not None:
                    c_score = round(float(class_avg), 1)
                if grade_avg is not None:
                    g_score = round(float(grade_avg), 1)

            radar_data.append({
                "subject_name": axis_name,
                "class_score": c_score,
                "grade_score": g_score
            })

        # 5. Formulate genuine qualitative observations comparing class against grade
        display_class_name = f"Lớp {clean_name}" if not clean_name.lower().startswith("lớp") else clean_name
        feedback_notes = self._generate_grade_comparison_notes(
            display_class_name,
            grade_label,
            radar_data
        )

        return {
            "class_name": display_class_name,
            "grade_name": grade_label,
            "radar_data": radar_data,
            "feedback_notes": feedback_notes
        }

    def _generate_grade_comparison_notes(
        self,
        class_name: str,
        grade_label: str,
        radar_items: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Generates qualitative feedback points based strictly on genuine attempt data.
        Does not fabricate benchmarks when attempts are missing or exclusive to target class.
        """
        # Subjects with actual attempt scores
        attempted = [item for item in radar_items if item["class_score"] > 0 or item["grade_score"] > 0]
        if not attempted:
            return [
                f"{class_name} chưa có dữ liệu bài tập nào được chấm điểm trong năm học này.",
                "Khuyến nghị giáo viên giao bài tập định kỳ để hệ thống tổng hợp và phân tích chất lượng học tập."
            ]

        class_attempted = [item for item in attempted if item["class_score"] > 0]
        if not class_attempted:
            return [
                f"{class_name} chưa có học sinh nộp bài tập nào để ghi nhận điểm trung bình.",
                f"Một số lớp khác trong {grade_label} đã có kết quả làm bài tập."
            ]

        notes = []
        class_avg = sum(item["class_score"] for item in class_attempted) / len(class_attempted)
        grade_avg = sum(item["grade_score"] for item in class_attempted) / len(class_attempted)
        diff_avg = round(class_avg - grade_avg, 1)

        # Check if other classes in the grade cohort have attempt data
        has_different_grade_data = any(item["class_score"] != item["grade_score"] for item in class_attempted)

        if not has_different_grade_data:
            # Only target_class has attempt data in the grade cohort
            notes.append(
                f"Điểm trung bình các môn của {class_name} đạt {class_avg:.1f} điểm "
                f"(phản ánh trực tiếp từ kết quả làm bài của lớp; chưa có thêm lớp khác trong {grade_label} nộp bài để so sánh đối chuẩn)."
            )
            best = max(class_attempted, key=lambda x: x["class_score"])
            lowest = min(class_attempted, key=lambda x: x["class_score"])
            notes.append(
                f"Môn đạt điểm trung bình cao nhất lớp là {best['subject_name']} ({best['class_score']:.1f} điểm)."
            )
            if lowest["subject_name"] != best["subject_name"]:
                notes.append(
                    f"Môn {lowest['subject_name']} có điểm trung bình thấp nhất lớp ({lowest['class_score']:.1f} điểm), "
                    f"cần chú ý đôn đốc học sinh luyện tập thêm."
                )
            notes.append(
                "Khuyến nghị GVCN phối hợp giáo viên bộ môn duy trì kiểm tra và giao bài tập định kỳ."
            )
            return notes

        # When genuine grade cohort comparison exists (other classes have attempts)
        if diff_avg > 0:
            notes.append(
                f"Điểm trung bình chung của {class_name} đạt {class_avg:.1f} điểm, "
                f"cao hơn mức bình quân toàn {grade_label} ({grade_avg:.1f} điểm) (+{diff_avg:.1f} điểm)."
            )
        elif diff_avg < 0:
            notes.append(
                f"Điểm trung bình chung của {class_name} đạt {class_avg:.1f} điểm, "
                f"thấp hơn mức bình quân toàn {grade_label} ({grade_avg:.1f} điểm) ({diff_avg:.1f} điểm)."
            )
        else:
            notes.append(
                f"Điểm trung bình chung của {class_name} đạt {class_avg:.1f} điểm, "
                f"tương đương với mức bình quân chung của toàn {grade_label}."
            )

        outperforming = [item for item in class_attempted if item["class_score"] > item["grade_score"]]
        outperforming.sort(key=lambda x: (x["class_score"] - x["grade_score"]), reverse=True)

        underperforming = [item for item in class_attempted if item["class_score"] < item["grade_score"]]
        underperforming.sort(key=lambda x: (x["grade_score"] - x["class_score"]), reverse=True)

        if outperforming:
            top_strs = [
                f"{item['subject_name']} (+{item['class_score'] - item['grade_score']:.1f})"
                for item in outperforming[:2]
            ]
            notes.append(
                f"Các môn thế mạnh vượt trội so với toàn khối: {' và '.join(top_strs)}."
            )
        else:
            best = max(class_attempted, key=lambda x: x["class_score"])
            notes.append(
                f"Môn {best['subject_name']} đạt điểm cao nhất trong lớp ({best['class_score']:.1f} điểm)."
            )

        if underperforming:
            weak_strs = [
                f"{item['subject_name']} ({item['class_score']:.1f} so với khối {item['grade_score']:.1f})"
                for item in underperforming[:2]
            ]
            notes.append(
                f"Cần tập trung cải thiện môn {' và '.join(weak_strs)} để thu hẹp khoảng cách với khối."
            )
            target_sub = underperforming[0]["subject_name"]
            notes.append(
                f"Khuyến nghị GVCN phối hợp giáo viên bộ môn {target_sub} tổ chức phụ đạo cho học sinh."
            )
        else:
            notes.append(
                "Khuyến nghị GVCN tiếp tục phát huy kết quả học tập và khuyến khích học sinh giải các bài tập nâng cao."
            )

        return notes
