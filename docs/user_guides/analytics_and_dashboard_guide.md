# Business User Guide: Báo Cáo Phân Tích & Biểu Đồ Năng Lực (Analytics & Dashboards)

> **File Name**: `docs/user_guides/analytics_and_dashboard_guide.md`  
> **Created At**: `2026-09-20` | **Created By**: `Tam Khang`  
> **Updated At**: `2026-09-20` | **Updated By**: `Tam Khang`  
> **Status**: `Ready to use`

---

## 1. Tổng Quan Nghiệp Vụ (Business Overview)

Hệ thống phân tích hành vi và năng lực học tập của SmartLMS giúp chuyển đổi dữ liệu làm bài thô thành các báo cáo trực quan đa chiều:
1. **Biểu đồ mạng nhện (Radar Chart)**: Trực quan hóa năng lực học sinh trên 6 mức độ nhận thức (Nhớ, Hiểu, Vận dụng, Phân tích, Đánh giá, Sáng tạo).
2. **Theo dõi hành vi & Cảnh báo nộp bài sát giờ (Last-minute Alert)**: Phát hiện học sinh thường xuyên dồn bài tập nộp vào những phút cuối cùng trước hạn chót.
3. **Phổ điểm & Thống kê câu hỏi hay sai**: Giúp giáo viên nhận diện nhanh các lỗ hổng kiến thức chung của lớp học.
4. **Nhận xét năng lực học tập**: Hệ thống đưa ra nhận xét tự động về khả năng học tập, điểm mạnh và điểm cần cải thiện của học sinh.

---

## 2. Diễn Giải Các Chỉ Số & Biểu Đồ

### 2.1. Biểu đồ Radar năng lực học tập (Cognitive Radar Chart)
Biểu đồ đánh giá mức độ thuần thục của học sinh theo thang điểm 10 trên từng năng lực:
* **Góc Nhớ / Biết**: Đo lường khả năng ghi nhớ công thức, định nghĩa và tính chất cơ bản.
* **Góc Hiểu**: Đo lường khả năng giải thích, so sánh và suy luận logic từ kiến thức đã học.
* **Góc Vận dụng**: Đo lường khả năng áp dụng công thức vào giải quyết các bài toán tiêu chuẩn.
* **Góc Vận dụng cao / Phân tích**: Đo lường khả năng giải các bài toán tổng hợp, kết hợp nhiều chủ đề.

### 2.2. Chỉ số hành vi nộp bài sát giờ (Last-minute Submission)
* **Khái niệm**: Học sinh hoàn thành và nộp bài trong khoảng thời gian **dưới 15% tổng thời lượng** trước hạn nộp (`due_at`).
* **Ý nghĩa sư phạm**: Cảnh báo giáo viên về thói quen trì hoãn (procrastination) của học sinh, giúp giáo viên kịp thời nhắc nhở và đôn đốc.

---

## 3. Hướng Dẫn Thao Tác Từng Bước

### Đối với Giáo viên:
1. Truy cập **Bảng điều khiển** (`/teacher`):
   - **Giáo viên bộ môn**: Xem phổ điểm theo từng bài tập đã giao, thống kê các câu hỏi có tỷ lệ làm sai cao nhất của lớp để chuẩn bị nội dung sửa bài trên lớp.
   - **Giáo viên chủ nhiệm**: Xem danh sách học sinh có tần suất làm bài giảm sút hoặc có nhiều bài nộp sát giờ trong tuần.
2. Tại trang **Chấm bài** (`/teacher/grading`): Xem phân tích thời gian làm bài thực tế của từng học sinh để đánh giá mức độ đầu tư cho bài tập.

### Đối với Học sinh:
1. Truy cập **Bảng điều khiển học sinh** (`/student`):
   - Xem biểu đồ mạng nhện đánh giá năng lực của mình theo từng môn học.
   - Nhấp vào biểu đồ để mở bảng phân tích chuyên sâu chi tiết từng chủ đề.
   - Đọc nhận xét đánh giá năng lực của giáo viên và hệ thống.
2. Tự luyện tập:
   - Sử dụng công cụ **Sinh đề luyện tập AI** tại trang bài tập để củng cố các phần kiến thức mình đạt điểm thấp trên biểu đồ radar.
