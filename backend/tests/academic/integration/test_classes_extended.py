# File Name: test_classes_extended.py
# Description: Integration tests for enriched ClassOut/EnrollmentOut, available-students, export-csv, and import-excel endpoints.
# Created At: 2026-11-14
# Created By: Tam Khang
# Updated At: 2026-11-14
# Updated By: Tam Khang

import io
import uuid
from datetime import date

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.rate_limit import reset_login_failures
from models.models import User


@pytest.fixture(autouse=True)
def _reset_rate_limits():
    reset_login_failures("0987654321")


def _admin_headers(client: TestClient) -> dict:
    res = client.post("/api/v1/auth/login", json={"phone": "0987654321", "password": "password123"})
    assert res.status_code == status.HTTP_200_OK
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


class TestExtendedAcademicClasses:
    def test_enriched_class_and_enrollment_available_and_csv(self, client: TestClient, db_session):
        headers = _admin_headers(client)
        teacher = db_session.query(User).filter(User.phone == "0912345678").first()
        student = db_session.query(User).filter(User.phone == "0934567890").first()

        # Create class with room_name and specialization
        create_res = client.post(
            "/api/v1/classes",
            headers=headers,
            json={
                "class_name": "10A9",
                "school_year": "2025-2026",
                "homeroom_teacher_id": str(teacher.user_id),
                "room_name": "Room B204",
                "specialization": "Natural Sciences",
            },
        )
        assert create_res.status_code == status.HTTP_201_CREATED
        cls_data = create_res.json()
        class_id = cls_data["class_id"]
        assert cls_data["homeroom_teacher_name"] == teacher.full_name
        assert cls_data["homeroom_teacher_code"].startswith("GV-")
        assert cls_data["student_count"] == 0
        assert cls_data["room_name"] == "Room B204"
        assert cls_data["specialization"] == "Natural Sciences"

        # Before enrollment, seeded student appears in available-students
        avail_before = client.get(f"/api/v1/classes/available-students?class_id={class_id}", headers=headers)
        assert avail_before.status_code == status.HTTP_200_OK
        avail_ids_before = [i["student_id"] for i in avail_before.json()["items"]]
        assert str(student.user_id) in avail_ids_before

        # Enroll existing student with gender
        enroll_res = client.post(
            f"/api/v1/classes/{class_id}/students",
            headers=headers,
            json={
                "student_id": str(student.user_id),
                "student_code": "HS1099",
                "gender": "Female",
            },
        )
        assert enroll_res.status_code == status.HTTP_201_CREATED
        assert enroll_res.json()["gender"] == "Female"
        assert enroll_res.json()["email"] == student.email

        # Enriched class now shows student_count == 1
        cls_detail = client.get(f"/api/v1/classes/{class_id}", headers=headers)
        assert cls_detail.status_code == status.HTTP_200_OK
        assert cls_detail.json()["student_count"] == 1

        # Enriched students list shows student_code, gender, dob
        stu_list = client.get(f"/api/v1/classes/{class_id}/students", headers=headers)
        assert stu_list.status_code == status.HTTP_200_OK
        assert len(stu_list.json()) == 1
        assert stu_list.json()[0]["student_code"] == "HS1099"
        assert stu_list.json()[0]["gender"] == "Female"

        # Enrolled student is excluded from available-students
        avail_after = client.get(f"/api/v1/classes/available-students?class_id={class_id}", headers=headers)
        assert avail_after.status_code == status.HTTP_200_OK
        avail_ids_after = [i["student_id"] for i in avail_after.json()["items"]]
        assert str(student.user_id) not in avail_ids_after

        # Export CSV
        csv_res = client.get("/api/v1/classes/export-csv", headers=headers)
        assert csv_res.status_code == status.HTTP_200_OK
        csv_text = csv_res.content.decode("utf-8-sig")
        assert "10A9" in csv_text
        assert "Room B204" in csv_text

    def test_import_students_excel_csv_and_xlsx(self, client: TestClient, db_session):
        from openpyxl import Workbook

        headers = _admin_headers(client)
        student = db_session.query(User).filter(User.phone == "0934567890").first()

        cls_res = client.post(
            "/api/v1/classes",
            headers=headers,
            json={"class_name": "11C5", "school_year": "2025-2026"},
        )
        assert cls_res.status_code == status.HTTP_201_CREATED
        class_id = cls_res.json()["class_id"]

        # 1. CSV import with 1 existing student, 1 new student, and 1 invalid underage row
        csv_content = (
            "full_name,student_code,email,phone,birthday,gender\n"
            f"{student.full_name},HS1101,{student.email},{student.phone},2007-04-01,Male\n"
            "New Imported Student,HS1102,new_imp_stu@test.com,0908111222,2007-09-12,Female\n"
            "Too Young Student,HS1103,young@test.com,0908111333,2020-01-01,Male\n"
        ).encode("utf-8")

        imp_csv = client.post(
            f"/api/v1/classes/{class_id}/students/import-excel",
            headers=headers,
            files={"file": ("students.csv", io.BytesIO(csv_content), "text/csv")},
        )
        assert imp_csv.status_code == status.HTTP_200_OK
        csv_payload = imp_csv.json()
        assert csv_payload["imported_count"] == 2
        assert len(csv_payload["errors"]) == 1
        assert csv_payload["errors"][0]["row"] == 4

        # 2. XLSX import
        wb = Workbook()
        ws = wb.active
        ws.append(["Họ và tên", "Mã học sinh", "Email", "Số điện thoại", "Ngày sinh", "Giới tính"])
        ws.append(["Excel Student", "HS1104", "excel_stu@test.com", "0908444555", "15/08/2007", "Female"])
        xlsx_buf = io.BytesIO()
        wb.save(xlsx_buf)
        xlsx_buf.seek(0)

        imp_xlsx = client.post(
            f"/api/v1/classes/{class_id}/students/import-excel",
            headers=headers,
            files={
                "file": (
                    "students.xlsx",
                    xlsx_buf,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
        )
        assert imp_xlsx.status_code == status.HTTP_200_OK
        xlsx_payload = imp_xlsx.json()
        assert xlsx_payload["imported_count"] == 1
        assert xlsx_payload["enrolled_students"][0]["student_name"] == "Excel Student"
        assert xlsx_payload["enrolled_students"][0]["dob"] == "2007-08-15"
        assert xlsx_payload["enrolled_students"][0]["gender"] == "Female"
