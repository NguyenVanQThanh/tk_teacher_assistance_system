# Business User Guide: Khảo Thí Trực Tuyến & Làm Bài Tập Học Sinh (Student Exam Taking)

> **File Name**: `docs/user_guides/student_exam_taking_guide.md`  
> **Created At**: `2026-09-20` | **Created By**: `Tam Khang`  
> **Updated At**: `2026-09-20` | **Updated By**: `Tam Khang`  
> **Status**: `Ready to use`

---

## 1. Tổng Quan Nghiệp Vụ (Business Overview)

Hệ thống cung cấp cho Học sinh môi trường khảo thí trực tuyến hiện đại, hỗ trợ chuẩn 3 phần cấu trúc đề thi mới của Bộ GD&ĐT:
1. **Theo dõi danh sách bài tập được giao**: Xem các bài tập cần làm, hạn chót nộp bài và trạng thái hoàn thành.
2. **Chế độ phòng thi tập trung (Fullscreen Exam Mode)**: Đồng hồ đếm ngược chính xác, chống gian lận, tự động lưu câu trả lời vào bộ nhớ đệm.
3. **Thao tác làm bài đa dạng**:
   - Phần I: Chọn đáp án trắc nghiệm A, B, C, D.
   - Phần II: Tích chọn Đúng / Sai cho từng ý a, b, c, d.
   - Phần III: Nhập kết quả số qua bàn phím hoặc Bàn phím số ảo (Virtual Numpad).
4. **Tự động chấm điểm & Ghi vết hành vi**: Hệ thống đo đạc thời gian bắt đầu (`start_time`), thời gian nộp (`end_time`), tính tổng thời gian làm bài thực tế (`total_time_seconds`) và tự động nộp bài khi hết giờ.

---

## 2. Luồng Nghiệp Vụ Khảo Thí (Exam Taking Flow)

```
[Học sinh]
     │
     ├─► 1. Vào Kho bài tập học sinh (/student/exercises)
     │        ├─► Lọc theo môn học (Toán, Vật lý, Hóa học,...)
     │        ├─► Xem danh sách bài: Tiêu đề, Hạn nộp, Thời lượng, Trạng thái (Chưa làm / Đã nộp)
     │        └─► Nhấn "Bắt đầu làm bài"
     │
     ├─► 2. Phòng thi trực tuyến (/student/exercises/:id/taking)
     │        ├─► Kích hoạt đồng hồ đếm ngược (Countdown Timer)
     │        ├─► Bảng điều hướng câu hỏi (Question Matrix) theo dõi tiến độ
     │        ├─► Làm Phần I (MCQ) -> Làm Phần II (Đúng/Sai) -> Làm Phần III (Điền số)
     │        └─► Tự động lưu tiến độ làm bài
     │
     └─► 3. Nộp bài & Xem kết quả
              ├─► Học sinh nhấn "Nộp bài" hoặc Hệ thống tự động nộp khi hết thời gian
              ├─► Hệ thống tự động chấm điểm trắc nghiệm tức thì
              └─► Hiển thị phổ điểm, thời gian hoàn thành và lời giải chi tiết
```

---

## 3. Quy Tắc Chấm Điểm Chuẩn 3 Phần

| Phần thi | Quy tắc tính điểm chi tiết |
| :--- | :--- |
| **Phần I (MCQ)** | Mỗi câu đúng nhận trọn số điểm của câu đó (ví dụ: `0.25đ / câu`). |
| **Phần II (Đúng/Sai)** | Tính điểm bậc thang theo số ý con đúng trong câu:<br>• Đúng 1 ý: `0.10 điểm`<br>• Đúng 2 ý: `0.25 điểm`<br>• Đúng 3 ý: `0.50 điểm`<br>• Đúng 4 ý: `1.00 điểm` |
| **Phần III (Điền số)** | So khớp giá trị số đã nhập với đáp án chính xác của đề thi. Nhập đúng nhận trọn điểm câu hỏi. |

---

## 4. Hướng Dẫn Thao Tác Từng Bước (Step-by-Step Guide)

### Bước 1: Chọn bài tập cần làm
1. Đăng nhập với tài khoản Học sinh.
2. Tại menu **Bài tập** (`/student/exercises`), chọn bài tập có trạng thái *Đang mở*.
3. Nhấp vào nút **"Làm bài"**.

### Bước 2: Thao tác trong phòng thi
1. Kiểm tra thời gian làm bài còn lại ở thanh trạng thái trên cùng.
2. Sử dụng **Bảng câu hỏi** ở thanh bên phải để nhảy nhanh đến câu hỏi cần làm.
3. Đối với câu hỏi điền số (Phần III):
   - Nhấp vào ô nhập kết quả.
   - Nhập số từ bàn phím hoặc nhấn các nút trên **Bàn phím số ảo (Numpad)** trên màn hình.
4. Có thể tích cờ "Xem lại sau" đối với các câu hỏi chưa chắc chắn.

### Bước 3: Nộp bài
1. Sau khi hoàn thành tất cả các câu, nhấn nút **"Nộp bài"** ở góc trên bên phải.
2. Xác nhận trong hộp thoại nộp bài.
3. Hệ thống sẽ hiển thị bảng tóm tắt kết quả: Điểm số, số câu đúng/sai và thời gian làm bài.
