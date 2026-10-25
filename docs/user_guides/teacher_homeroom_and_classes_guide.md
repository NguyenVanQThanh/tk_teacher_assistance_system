# Business User Guide: Quản Lý Lớp Học & Công Tác Chủ Nhiệm (Classes & Homeroom)

> **File Name**: `docs/user_guides/teacher_homeroom_and_classes_guide.md`  
> **Created At**: `2026-09-20` | **Created By**: `Tam Khang`  
> **Updated At**: `2026-09-20` | **Updated By**: `Tam Khang`  
> **Status**: `Ready to use`

---

## 1. Tổng Quan Nghiệp Vụ (Business Overview)

Hệ thống SmartLMS phân tách rõ 2 vai trò quản lý lớp học của Giáo viên:
1. **Giáo viên Bộ môn (Subject Teacher)**:
   - Theo dõi danh sách các lớp học được phân công giảng dạy (Data Scoping).
   - Xem sĩ số lớp, danh sách học sinh và điểm trung bình bộ môn.
   - Quản lý các bài tập đã giao theo từng lớp và hủy giao bài an toàn.
2. **Giáo viên Chủ nhiệm (Homeroom Teacher)**:
   - Nắm bắt toàn diện sĩ số, biến động chuyên cần, điểm rèn luyện và hồ sơ học sinh lớp chủ nhiệm.
   - Theo dõi tổng thể học lực các môn, danh sách học sinh có nguy cơ sa sút hoặc có dấu hiệu nộp bài sát giờ (last-minute).
   - Đặt câu hỏi khảo sát / câu hỏi kiểm tra nhanh cho lớp chủ nhiệm.

---

## 2. Luồng Nghiệp Vụ (Business Flow)

```
[Giáo viên]
     │
     ├─► Quản lý Lớp bộ môn (/teacher/classes)
     │        ├─► Xem thẻ tổng quan các lớp dạy: Mã lớp, Khối, Sĩ số, Môn phụ trách
     │        └─► Bấm vào từng lớp -> Trang Chi tiết lớp học (/teacher/classes/:classId)
     │                 ├─► Tab "Danh sách học sinh": Tìm kiếm, xem mã HS, điểm TB
     │                 └─► Tab "Bài tập đã giao": Theo dõi hạn nộp, hủy giao bài
     │
     └─► Quản lý Lớp chủ nhiệm (/teacher/homeroom)
              ├─► Thống kê Sĩ số lớp (Tổng số, Nam, Nữ, Đoàn viên/Đội viên)
              ├─► Danh sách học sinh lớp chủ nhiệm: Họ tên, Ngày sinh, SĐT phụ huynh, Điểm TB tích lũy
              ├─► Theo dõi chuyên cần & Cảnh báo học sinh cần lưu ý (sa sút tần suất làm bài)
              └─► Đặt câu hỏi khảo sát / câu hỏi sinh hoạt lớp nhanh
```

---

## 3. Các Quy Tắc Nghiệp Vụ & Phân Quyền Dữ Liệu (Data Scoping)

| Tiêu chí | Giáo viên Bộ môn | Giáo viên Chủ nhiệm |
| :--- | :--- | :--- |
| **Phạm vi xem lớp (Class Scope)** | Chỉ hiển thị các lớp có phân công giảng dạy trong bảng `teacher_assignments`. | Hiển thị lớp được chỉ định làm chủ nhiệm (`homeroom_teacher_id`). |
| **Quyền Giao bài** | Giao đề thi thuộc môn mình dạy cho lớp. | Giao bài môn mình dạy và xem tổng quan kết quả các môn của lớp chủ nhiệm. |
| **Bảo mật thông tin cá nhân** | Xem Mã học sinh, Họ tên, Điểm bài tập bộ môn. | Được xem đầy đủ thông tin liên lạc của Phụ huynh, ghi chú rèn luyện và lịch sử chuyên cần. |

---

## 4. Hướng Dẫn Thao Tác Từng Bước (Step-by-Step Guide)

### Bước 1: Quản lý lớp giảng dạy bộ môn
1. Đăng nhập tài khoản Giáo viên, chọn menu **Lớp học** (`/teacher/classes`).
2. Giao diện hiển thị danh sách các lớp bạn được phân công giảng dạy trong năm học.
3. Nhấp vào nút **"Xem chi tiết lớp"** trên thẻ lớp mong muốn.
4. Tại trang chi tiết lớp học:
   - **Tab Học sinh**: Xem danh bạ lớp học sinh, tìm kiếm học sinh theo tên hoặc mã.
   - **Tab Bài tập đã giao**: Xem toàn bộ các bài kiểm tra/bài tập đang giao cho lớp này, theo dõi số lượng học sinh đã nộp và hủy giao bài nếu cần.

### Bước 2: Quản lý lớp chủ nhiệm
1. Chọn menu **Lớp chủ nhiệm** (`/teacher/homeroom`).
2. Xem bảng tổng quan sĩ số, tỷ lệ chuyên cần và danh sách học sinh lớp chủ nhiệm.
3. Để tìm kiếm học sinh: Nhập từ khóa tên học sinh hoặc mã học sinh vào ô tìm kiếm.
4. Xem danh sách cảnh báo học sinh cần đôn đốc (nộp bài sát giờ hoặc chưa hoàn thành bài tập tuần).
