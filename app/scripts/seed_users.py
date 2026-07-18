# File Name: seed_users.py
# Description: Script to seed database with initial user accounts for each role.
# Created At: 2026-07-18
# Created By: Tam Khang
# Updated At: 2026-07-18
# Updated By: Tam Khang

import os
import sys
import uuid
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Force UTF-8 for stdout
sys.stdout.reconfigure(encoding='utf-8')

from models.models import User, Role
from app.core.security import get_password_hash

# Load environment variables
load_dotenv()

# Read database configuration from the environment
DB_USERNAME = os.environ.get("DB_USERNAME")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME")

if not all([DB_USERNAME, DB_PASSWORD, DB_NAME]):
    raise ValueError("Missing database configuration in environment variables")

DATABASE_URL = f"postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def seed_users():
    session = SessionLocal()
    try:
        print("Bắt đầu khởi tạo dữ liệu tài khoản mẫu...")
        
        # 1. Lấy thông tin các vai trò từ database
        roles = session.query(Role).all()
        if not roles:
            print("Lỗi: Không tìm thấy vai trò nào trong DB. Vui lòng chạy script seed.py trước.")
            return

        roles_dict = {role.name: role for role in roles}
        
        # Định nghĩa các tài khoản cần tạo cho từng vai trò
        accounts_to_seed = [
            {
                "phone": "0999000001",
                "email": "admin@school.com",
                "full_name": "Quản trị viên Hệ thống",
                "role_name": "Admin",
                "password_plain": "Admin@1234"
            },
            {
                "phone": "0999000002",
                "email": "teacher@school.com",
                "full_name": "Giáo viên Mẫu",
                "role_name": "Teacher",
                "password_plain": "Teacher@1234"
            },
            {
                "phone": "0999000003",
                "email": "student@school.com",
                "full_name": "Học sinh Mẫu",
                "role_name": "Student",
                "password_plain": "Student@1234"
            }
        ]

        seeded_accounts = []

        for acc in accounts_to_seed:
            role = roles_dict.get(acc["role_name"])
            if not role:
                print(f"Bỏ qua tài khoản {acc['full_name']} vì vai trò '{acc['role_name']}' không tồn tại trong DB.")
                continue

            # Kiểm tra xem tài khoản đã tồn tại chưa (qua số điện thoại hoặc email)
            existing_user = session.query(User).filter(
                (User.phone == acc["phone"]) | (User.email == acc["email"])
            ).first()

            if not existing_user:
                hashed_pw = get_password_hash(acc["password_plain"])
                new_user = User(
                    user_id=uuid.uuid4(),
                    phone=acc["phone"],
                    email=acc["email"],
                    password_hash=hashed_pw,
                    full_name=acc["full_name"],
                    role_id=role.role_id,
                    status="Active"
                )
                session.add(new_user)
                session.flush()
                print(f"Đã tạo tài khoản cho vai trò {acc['role_name']}: {acc['phone']} / {acc['email']}")
                
                seeded_accounts.append({
                    "user_id": str(new_user.user_id),
                    "phone": acc["phone"],
                    "email": acc["email"],
                    "full_name": acc["full_name"],
                    "role_name": acc["role_name"],
                    "password_plain": acc["password_plain"]
                })
            else:
                # Nếu đã tồn tại thì lấy thông tin hiển thị
                seeded_accounts.append({
                    "user_id": str(existing_user.user_id),
                    "phone": existing_user.phone,
                    "email": existing_user.email,
                    "full_name": existing_user.full_name,
                    "role_name": acc["role_name"],
                    "password_plain": "(Đã tồn tại trong DB - Sử dụng mật khẩu cũ)"
                })

        session.commit()
        print("Lưu dữ liệu thành công!")
        
        # 2. Ghi thông tin tài khoản mẫu ra file seed_data.json để lưu trữ tham chiếu
        output_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "seed_accounts_info.json")
        with open(output_file_path, "w", encoding="utf-8") as f:
            json.dump(seeded_accounts, f, indent=2, ensure_ascii=False)
            
        print(f"Đã lưu thông tin tài khoản mẫu vào file: {output_file_path}")
        
    except Exception as e:
        session.rollback()
        print(f"Đã xảy ra lỗi khi tạo dữ liệu mẫu: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    seed_users()
