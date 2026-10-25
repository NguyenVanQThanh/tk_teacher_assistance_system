# Business User Guide: Tạo Bài Tập & Bóc Tách Đề Thi Bằng AI Gemini Vision

> **File Name**: `docs/user_guides/exercise_creation_and_ai_ocr_guide.md`  
> **Created At**: `2026-09-20` | **Created By**: `Tam Khang`  
> **Updated At**: `2026-09-20` | **Updated By**: `Tam Khang`  
> **Status**: `Ready to use`

---

## 1. Tổng Quan Nghiệp Vụ (Business Overview)

Tính năng **Tạo Bài Tập & Bóc Tách Đề Thi Bằng AI** cung cấp 2 phương thức biên soạn đề thi thông minh cho Giáo viên:
1. **Soạn đề thủ công (Manual Creator)**: Tự tạo câu hỏi theo cấu trúc chuẩn 3 phần mới của Bộ Giáo dục & Đào tạo, hỗ trợ gõ công thức Toán học chuẩn `$LaTeX$`, gắn nhãn mức độ nhận thức (Nhận biết, Thông hiểu, Vận dụng) và thiết lập thời lượng làm bài.
2. **Bóc tách đề thi thông minh bằng AI Gemini Multimodal Vision**: Giáo viên tải lên file PDF hoặc file ảnh đề thi Toán học/Khoa học tự nhiên. Hệ thống tự động nhận diện chữ viết, công thức `$LaTeX$`, bảng biến thiên, đồ thị hình học và tự động sinh danh sách câu hỏi trắc nghiệm hoàn chỉnh.

---

## 2. Luồng Nghiệp Vụ (Business Flow)

```
[Giáo viên]
     │
     ├─► Phương thức 1: Soạn đề thủ công (/teacher/exercises/create-manual)
     │        ├─► Nhập Tiêu đề đề thi, Môn học, Khối lớp, Thời gian làm bài (phút)
     │        ├─► Thêm câu hỏi Phần I: Trắc nghiệm 4 lựa chọn (A, B, C, D)
     │        ├─► Thêm câu hỏi Phần II: Đúng / Sai 4 ý con (a, b, c, d)
     │        ├─► Thêm câu hỏi Phần III: Trả lời ngắn / Điền số
     │        └─► Bấm "Lưu bài tập" -> Lưu vào Ngân hàng đề thi
     │
     └─► Phương thức 2: Bóc tách bằng AI Gemini Vision (Modal Tạo Đề Nhanh)
              ├─► Mở Modal "Tạo bài tập mới" từ Kho đề thi (/teacher/exercises)
              ├─► Nhập tiêu đề, chọn môn & khối lớp
              ├─► Tải lên file PDF hoặc Ảnh chụp đề thi
              ├─► AI Gemini Vision quét, trích xuất LaTeX và bảng đáp án
              ├─► Giáo viên xem trước (Preview), chỉnh sửa câu hỏi trực tiếp
              └─► Xác nhận lưu vào Ngân hàng đề thi
```

---

## 3. Cấu Trúc Đề Thi Chuẩn 3 Phần Của Bộ GD&ĐT

Hệ thống hỗ trợ đầy đủ 3 định dạng câu hỏi theo quy chuẩn khảo thí mới nhất:

| Phần | Tên định dạng | Cấu trúc dữ liệu | Cơ chế tính điểm |
| :--- | :--- | :--- | :--- |
| **Phần I** | **Trắc nghiệm nhiều lựa chọn (MCQ)** | 1 câu hỏi kèm 4 phương án A, B, C, D (chọn 1 đáp án đúng duy nhất). | Chọn đúng nhận trọn điểm câu hỏi (ví dụ: 0.25đ/câu). |
| **Phần II** | **Câu hỏi Đúng / Sai (True/False)** | 1 câu hỏi gồm 4 ý con riêng biệt (a, b, c, d). Học sinh chọn Đúng hoặc Sai cho từng ý. | Điểm lũy tiến theo số ý đúng: đúng 1 ý = 0.1đ, đúng 2 ý = 0.25đ, đúng 3 ý = 0.5đ, đúng cả 4 ý = 1.0đ. |
| **Phần III** | **Câu hỏi Trả lời ngắn (Short Answer)** | 1 câu hỏi yêu cầu giải toán và điền kết quả số (số nguyên hoặc số thập phân). | Học sinh nhập kết quả qua bàn phím số/Numpad ảo. Trùng khớp đáp án số nhận trọn điểm. |

---

## 4. Hướng Dẫn Thao Tác Từng Bước (Step-by-Step Guide)

### Cách 1: Bóc tách đề thi tự động bằng AI Gemini Vision
1. Truy cập **Kho bài tập**: `http://localhost:3000/teacher/exercises`.
2. Nhấn nút **"+ Tạo bài tập mới"** ở góc phải màn hình.
3. Trong Modal xuất hiện:
   - Nhập **Tên bài tập** (VD: *Đề kiểm tra 1 tiết Giải tích 12 - Chương 1*).
   - Chọn **Môn học** và **Khối lớp**.
   - Thiết lập **Thời gian làm bài** (VD: 45 phút).
4. Tại khu vực **Tải file đề thi**:
   - Chọn file PDF hoặc file ảnh đề thi từ máy tính (hỗ trợ kéo thả).
   - Có thể tải kèm file đáp án riêng nếu có.
5. Nhấn **"Tiến hành bóc tách bằng AI"**. Hệ thống sẽ gọi Gemini Vision OCR để bóc tách câu hỏi và công thức `$LaTeX$`.
6. Sau khi AI hoàn tất, danh sách câu hỏi sẽ hiển thị trực quan. Giáo viên có thể bấm **Sửa câu hỏi** để điều chỉnh nội dung nếu cần, sau đó bấm **"Hoàn tất & Lưu đề thi"**.

### Cách 2: Soạn đề thi thủ công
1. Tại trang **Kho bài tập**, nhấn vào menu mở rộng chọn **"Soạn đề chi tiết"** (hoặc truy cập `/teacher/exercises/create-manual`).
2. Điền thông tin chung của bài thi.
3. Lần lượt nhấn **"+ Thêm câu hỏi"** theo từng phần mong muốn:
   - Nhập nội dung câu hỏi (chèn công thức Toán dạng `$y = ax^3 + bx^2 + cx + d$`).
   - Nhập các phương án lựa chọn và tích chọn đáp án đúng.
   - Gắn nhãn mức độ nhận thức: *Nhận biết*, *Thông hiểu*, hoặc *Vận dụng*.
4. Nhấn **"Lưu và xuất bản đề thi"**.

---

## 5. Các Lưu Ý & Xử Lý Sự Cố Thường Gặp

| Tình huống | Nguyên nhân | Giải pháp |
| :--- | :--- | :--- |
| **Ảnh đề thi mờ hoặc bị nghiêng** | File scan chất lượng thấp khiến AI nhận diện nhầm ký tự. | Chụp lại ảnh rõ nét, đủ ánh sáng hoặc sử dụng file PDF gốc xuất từ Word/LaTeX. |
| **Công thức LaTeX bị hiển thị sai** | Thiếu dấu `$` hoặc cú pháp LaTeX chưa chuẩn. | Mở modal chỉnh sửa câu hỏi, bọc lại công thức trong cặp dấu `$...$` (VD: `$\frac{a}{b}$`). |
| **Xóa đề thi đã tạo** | Giáo viên không còn nhu cầu sử dụng đề thi này. | Nhấn nút **Xóa** trên thẻ bài tập. Hệ thống áp dụng **Xóa mềm (Soft Delete)**, chuyển trạng thái sang `DELETED` để đảm bảo an toàn dữ liệu. |
