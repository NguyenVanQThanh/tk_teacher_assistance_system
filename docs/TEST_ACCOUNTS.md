# Test Accounts Reference (Danh Sách Tài Khoản Kiểm Thử)

> Created At: 2026-10-07
> Created By: Tam Khang
> Updated At: 2026-10-07
> Updated By: Tam Khang

Tài liệu cung cấp danh sách tài khoản phục vụ kiểm thử tự động (Automation Test) và kiểm thử thủ công (Manual Testing) toàn bộ hệ thống SmartLMS.

---

## 1. Tài khoản Giáo Viên (Teacher)

Tất cả tài khoản giáo viên sử dụng chung mật khẩu chuẩn: **`Teacher@1234`**

| Số điện thoại (Phone) | Email | Họ và tên | Chuyên môn / Lớp phụ trách | Mục đích kiểm thử |
| :--- | :--- | :--- | :--- | :--- |
| **`0999000002`** | `teacher@school.com` | Thầy Nguyễn Văn A | Chủ nhiệm 12A1, Giảng dạy Toán 12 | **Tài khoản giáo viên chính** (Full dữ liệu bài tập, chấm thi, phân công) |
| **`0988000001`** | `teacher_auto_test@school.com` | Thầy Automation Tester | Giảng dạy Toán 12A1 | **Tài khoản dành riêng cho Playwright Automation Test** |
| **`0999000004`** | `teacher_an@school.com` | Thầy Nguyễn Văn An | Bộ môn Toán | Kiểm thử phân quyền & danh sách lớp |
| **`0999000005`** | `teacher_mai@school.com` | Cô Trần Thị Mai | Bộ môn Vật lý | Kiểm thử bài tập & chấm điểm Vật lý |
| **`0999000006`** | `teacher_long@school.com` | Thầy Lê Hoàng Long | Bộ môn Hóa học | Kiểm thử bài tập & đề thi Hóa học |

---

## 2. Tài khoản Học Sinh (Student)

Tất cả tài khoản học sinh sử dụng chung mật khẩu chuẩn: **`Student@1234`**

| Số điện thoại (Phone) | Email | Họ và tên | Lớp | Mã học sinh |
| :--- | :--- | :--- | :--- | :--- |
| **`0999100001`** | `student_nam@school.com` | Nguyễn Hoàng Nam | 12A1 | HS120001 |
| **`0999100002`** | `student_mai_anh@school.com` | Trần Thị Mai Anh | 12A1 | HS120002 |
| **`0999100003`** | `student_duc@school.com` | Lê Văn Đức | 12A1 | HS120003 |
| **`0999100004`** | `student_tuan@school.com` | Phạm Minh Tuấn | 12A1 | HS120004 |
| **`0999100005`** | `student_thao@school.com` | Đặng Thu Thảo | 12A1 | HS120005 |

---

## 3. Tài khoản Quản Trị Viên (Admin)

Mật khẩu chuẩn: **`Admin@1234`**

| Số điện thoại (Phone) | Email | Họ và tên | Vai trò |
| :--- | :--- | :--- | :--- |
| **`0999000001`** | `admin@school.com` | Quản trị viên Hệ thống | Admin (Toàn quyền hệ thống) |

---

## 4. Cách chạy lại script tạo tài khoản

```bash
python backend/app/scripts/seed_test_accounts.py
```
