import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.base import Base
from models.models import Role, Permission

# Thay đổi URL này đúng với cấu hình PostgreSQL của bạn
DATABASE_URL = "postgresql://postgres:123456@localhost:5432/teacher_assistance"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def seed_data():
    session = SessionLocal()
    try:
        # 1. Kiểm tra xem đã có dữ liệu chưa để tránh trùng lặp
        if session.query(Role).first() is not None:
            print("Database đã có dữ liệu mẫu từ trước!")
            return

        print("Đang khởi tạo dữ liệu mẫu...")

        # 2. Tạo các Quyền (Roles) mẫu
        admin_role = Role(name="Admin", description="Quản trị viên hệ thống")
        teacher_role = Role(name="Teacher", description="Giáo viên")
        student_role = Role(name="Student", description="Học sinh")

        session.add_all([admin_role, teacher_role, student_role])
        session.commit()
        print("🎉 Đã nạp dữ liệu mẫu vào bảng Roles thành công!")

    except Exception as e:
        session.rollback()
        print(f"Có lỗi xảy ra khi nạp dữ liệu: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    seed_data()
