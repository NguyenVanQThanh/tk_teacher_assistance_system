# Business User Guide: Tính Năng Quản Lý Chấm Điểm & Bài Nộp Học Sinh (Teacher Grading)

> **File Name**: `docs/user_guides/teacher_grading_guide.md`  
> **Created At**: `2026-09-12` | **Created By**: `Tam Khang`  
> **Updated At**: `2026-09-12` | **Updated By**: `Tam Khang`  
> **Status**: `Ready to use`

---

## 1. Tổng Quan Nghiệp Vụ (Business Overview)

Module **Quản lý Chấm điểm & Phản hồi (Teacher Grading & Student Attempts)** cho phép giáo viên theo dõi và đánh giá toàn diện quá trình làm bài tập của học sinh:
1. Tự động chấm điểm các câu hỏi trắc nghiệm khách quan khi học sinh nộp bài.
2. Cung cấp giao diện bảng tổng hợp danh sách bài nộp, thống kê điểm trung bình, tỉ lệ đạt chuẩn ($\ge 5.0$).
3. Cho phép giáo viên mở từng bài nộp để kiểm tra câu trả lời của học sinh, điều chỉnh điểm số và gửi nhận xét/góp ý cá nhân hóa.
4. Hỗ trợ tính năng "Chấm & Chuyển tiếp" giúp tiết kiệm thời gian chấm bài hàng loạt.

---

## 2. Luồng Nghiệp Vụ Chấm Điểm (Grading Workflow)

```
[Học sinh nộp bài] 
     │
     ├─► Hệ thống tự động chấm trắc nghiệm & tạo Attempt (score, detailed_results)
     │
[Giáo viên] 
     │
     ├─► 1. Vào trang Chấm điểm (/teacher/grading)
     │        ├─► Xem thẻ tóm tắt: Tổng bài nộp, Điểm TB, Tỉ lệ đạt, Số bài chờ chấm/duyệt
     │        ├─► Lọc theo Lớp, Môn học, Trạng thái (Chờ chấm / Chờ duyệt / Đã duyệt)
     │        └─► Tìm kiếm theo tên học sinh hoặc tên bài tập
     │
     ├─► 2. Mở Modal Chấm điểm & Nhận xét (Grading Modal)
     │        ├─► Xem chi tiết từng câu hỏi trong đề & đáp án học sinh chọn
     │        ├─► Xem đáp án đúng của hệ thống & điểm thành phần
     │        ├─► Điều chỉnh điểm số (thang điểm 10)
     │        ├─► Nhập nhận xét hoặc dùng gợi ý nhanh / AI Feedback
     │        └─► Nhấn "Hoàn tất chấm" hoặc "Lưu & Chấm bài tiếp theo"
     │
     └─► 3. Hệ thống lưu điểm qua API (PUT /api/v1/attempts/:id/grade) & cập nhật bảng
```

---

## 3. Các Trạng Thái Bài Nộp (Submission Statuses)

| Trạng thái | Mã | Ý nghĩa |
| :--- | :--- | :--- |
| **Chờ chấm** | `pending_grading` | Bài làm có câu hỏi tự luận/trả lời ngắn hoặc chưa có điểm chính thức, cần giáo viên chấm thủ công. |
| **Chờ duyệt** | `pending_review` | Bài tập đã được hệ thống tự động chấm, chờ giáo viên kiểm tra lại và duyệt. |
| **Đã duyệt / Đã chấm** | `approved` | Bài nộp đã có điểm số hoàn chỉnh và nhận xét từ giáo viên. |

---

## 4. Hướng Dẫn Thao Tác Từng Bước

### Bước 1: Xem danh sách bài nộp
1. Đăng nhập tài khoản Giáo viên, vào menu **Chấm điểm**: `http://localhost:5173/teacher/grading`.
2. Sử dụng thanh công cụ để lọc danh sách bài nộp theo:
   - Khối lớp / Lớp học phụ trách.
   - Môn học (Toán, Vật lý, Hóa học, Tiếng Anh...).
   - Trạng thái bài nộp.
   - Tìm kiếm theo tên học sinh.

### Bước 2: Chấm điểm và gửi nhận xét
1. Nhấp vào dòng bài nộp của học sinh muốn chấm.
2. Tại Modal hiển thị:
   - Kiểm tra các câu hỏi trắc nghiệm (đánh dấu xanh lá nếu đúng, đỏ nếu sai).
   - Kiểm tra câu trả lời tự luận của học sinh.
   - Nhập điểm số vào ô **Điểm tổng kết**.
   - Chọn gợi ý nhận xét có sẵn hoặc tự soạn nội dung phản hồi cho học sinh.
3. Bấm **"Hoàn tất"** để lưu điểm hoặc bấm **"Lưu & Tiếp tục"** để chuyển ngay sang học sinh tiếp theo.

---

## 5. Danh Sách API Liên Quan

| Method | Endpoint | Quyền | Mô tả |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/attempts` | `EXE_ATTEMPT_VIEW` | Lấy danh sách bài nộp với bộ lọc (class_id, assignment_id, is_finished, search) |
| `GET` | `/api/v1/attempts/{attempt_id}` | `EXE_ATTEMPT_VIEW` | Lấy chi tiết bài làm của học sinh |
| `PUT` | `/api/v1/attempts/{attempt_id}/grade` | `EXE_ASSIGNMENT_MANAGE` | Giáo viên cập nhật điểm số và nhận xét |
| `POST` | `/api/v1/assignments/{assignment_id}/attempts` | `EXE_ATTEMPT_SUBMIT` | Học sinh bắt đầu làm bài |
| `PUT` | `/api/v1/attempts/{attempt_id}/submit` | `EXE_ATTEMPT_SUBMIT` | Học sinh nộp bài và kích hoạt tự động chấm |
