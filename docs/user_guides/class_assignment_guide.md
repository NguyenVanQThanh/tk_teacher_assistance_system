# Business User Guide: Tính Năng Giao Bài Tập Cho Lớp Học (Class Assignments)

> **File Name**: `docs/user_guides/class_assignment_guide.md`  
> **Created At**: `2026-09-12` | **Created By**: `Tam Khang`  
> **Updated At**: `2026-09-12` | **Updated By**: `Tam Khang`  
> **Status**: `Ready to use`

---

## 1. Tổng Quan Nghiệp Vụ (Business Overview)

Tính năng **Giao bài tập cho lớp học (Class Assignments)** là cầu nối nghiệp vụ giữa **Kho đề thi (Exercise Bank)** và **Lớp học (Academic Classes)**, giúp giáo viên:
1. Giao trực tiếp bất kỳ đề thi/bài tập trắc nghiệm nào trong kho đề cho lớp học mình đang phụ trách giảng dạy.
2. Thiết lập linh hoạt **Hạn nộp bài (Due Date & Time)** cho học sinh.
3. Theo dõi danh sách bài tập đang mở hoặc đã hết hạn tại trang chi tiết lớp học.
4. Hủy giao bài an toàn thông qua cơ chế **Xóa mềm (Soft Delete)** khi bài chưa có học sinh nộp bài.

---

## 2. Luồng Nghiệp Vụ Chi Tiết (Business Flow)

```
[Giáo viên] 
     │
     ├─► 1. Vào Kho đề thi (/teacher/exercises)
     │        │
     │        └─► Bấm biểu tượng "Chia sẻ / Giao bài" hoặc "Xem đề thi"
     │
     ├─► 2. Mở Modal "Giao bài tập cho lớp"
     │        ├─► Chọn lớp học phụ trách
     │        ├─► Chọn hạn nộp bài (Hỗ trợ chọn nhanh 1 ngày, 3 ngày, 1 tuần, 2 tuần)
     │        └─► Bấm "Xác nhận giao bài"
     │
     └─► 3. Quản lý tại Chi tiết lớp học (/teacher/classes/:classId)
              │
              └─► Chuyển sang Tab "Bài tập đã giao"
                     ├─► Xem danh sách bài: Tên đề, Số câu, Ngày giao, Hạn nộp, Trạng thái
                     ├─► Tìm kiếm bài tập đã giao theo từ khóa
                     └─► Hủy giao bài (Soft Delete)
```

---

## 3. Các Quy Tắc Nghiệp Vụ Cần Lưu Ý (Business Rules & Edge Cases)

| Quy tắc | Mô tả chi tiết | Xử lý hệ thống |
| :--- | :--- | :--- |
| **Phân quyền Giáo viên (Scoping)** | Giáo viên chỉ được giao đề thi thuộc môn học mà mình được phân công dạy tại lớp đó. | Nếu không được phân công dạy môn đó tại lớp, hệ thống trả về lỗi `403 Forbidden` (`ERR-EXE-CLASS_ACCESS_DENIED`). |
| **Hạn nộp bài (Due Date)** | Thời hạn nộp bài bắt buộc phải ở thời điểm tương lai. | Chặn gửi nếu ngày giờ nhỏ hơn hoặc bằng thời gian hiện tại (`422 Unprocessable Entity`). |
| **Chống giao trùng (Duplicate Check)** | Không được giao trùng lặp một đề thi đang hoạt động (ACTIVE) cho cùng một lớp học. | Hệ thống cảnh báo lỗi `409 Conflict` (`ERR-EXE-DUPLICATE_ASSIGNMENT`). |
| **Bảo vệ kết quả học sinh (Attempts Guard)** | Không thể hủy bài tập nếu đã có ít nhất một học sinh bắt đầu làm hoặc nộp bài. | Hệ thống chặn hủy và thông báo `409 Conflict` (`ERR-EXE-ASSIGNMENT_HAS_ATTEMPTS`). |
| **Chính sách Xóa mềm (Soft Delete)** | Mọi thao tác hủy giao bài đều chuyển trạng thái thành `DELETED` thay vì xóa vĩnh viễn khỏi cơ sở dữ liệu. | Dữ liệu được lưu vết đầy đủ phục vụ khôi phục hoặc kiểm toán (Audit Log). |

---

## 4. Hướng Dẫn Thao Tác Từng Bước (Step-by-Step Guide)

### Bước 1: Giao bài từ Kho đề thi
1. Truy cập vào **Kho bài tập**: `http://localhost:5173/teacher/exercises`.
2. Tìm đề thi mong muốn, nhấp vào nút **Chia sẻ / Giao bài** (icon Share trên góc phải bên dưới thẻ bài).
3. Tại Modal hiển thị:
   - Chọn lớp học trong danh sách dropdown.
   - Chọn hạn nộp bài (chọn ngày giờ hoặc dùng các nút gợi ý: **1 ngày**, **3 ngày**, **1 tuần**, **2 tuần**).
   - Nhấn **Xác nhận giao bài**.

### Bước 2: Xem và quản lý bài tập tại Chi tiết lớp học
1. Vào mục **Lớp học của tôi**: `http://localhost:5173/teacher/classes`.
2. Chọn lớp học tương ứng (ví dụ: `12A1`).
3. Nhấp vào Tab **"Bài tập đã giao"**:
   - Trạng thái **Đang mở** (Màu xanh lá): Bài tập còn hạn nộp.
   - Trạng thái **Đã hết hạn** (Màu xám): Bài tập đã quá hạn nộp.
4. Để hủy giao bài: Bấm vào biểu tượng **Thùng rác** tại dòng bài tập tương ứng và nhấn xác nhận.

---

## 5. Danh Sách API Liên Quan (API Reference)

| Method | Endpoint | Quyền yêu cầu | Chức năng |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/classes/{class_id}/assignments` | `EXE_ASSIGNMENT_MANAGE` | Tạo phân công bài tập cho lớp |
| `GET` | `/api/v1/classes/{class_id}/assignments` | `EXE_ASSIGNMENT_VIEW` | Lấy danh sách bài tập đã giao cho lớp |
| `DELETE` | `/api/v1/assignments/{assignment_id}` | `EXE_ASSIGNMENT_MANAGE` | Xóa mềm / Hủy giao bài tập |
| `POST` | `/api/v1/assignments/{assignment_id}/restore` | `EXE_ASSIGNMENT_MANAGE` | Khôi phục bài tập đã xóa |
