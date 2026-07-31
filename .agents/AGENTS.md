# Agent System Rules

Before starting any coding task, analyzing requirements, or modifying files in this repository, you **MUST** read, understand, and strictly follow the configuration and rule files located in the `.claude/` directory:

1. **Coding Rules & Architecture**: See `.claude/rules/coding_rules.md` for standards regarding code headers, comments, logging restrictions, architecture, and security rules (especially regarding `.env` files).
2. **Feature Completion & Memory**: See `.claude/rules/memory_and_completion_rules.md` for the strict workflow on asking for user confirmation and creating detailed `.md` memory files inside `.claude/memory/feature/` or `.claude/memory/fix/` after finishing tasks.

**CRITICAL**: These rules apply to all agent interactions within this project. You must apply these guidelines (headers, logging, architecture, memory creation, etc.) consistently on every task.

## 3. Task File Workflow & Headers
Khi quản lý hoặc tạo các file task (trong thư mục `docs/tasks/`), Agent cần tuân thủ quy chuẩn trạng thái và cấu trúc header sau:

### Trạng thái của Task (Status)
- **`draft`**: Trạng thái mặc định khi task mới được tạo hoặc bàn giao.
- **`in progress`**: Trạng thái khi Agent đang thực hiện triển khai code cho task này.
- **`ready to test`**: Trạng thái sau khi Agent hoàn thành cài đặt code cho task và đã tự kiểm tra, sẵn sàng cho User test.
- **`done`**: Trạng thái sau khi User kiểm tra hoạt động thành công và xác nhận hoàn thành task.

### Cấu trúc Header của File Task
Mỗi file task phải có phần header chứa tối thiểu các trường sau để dễ theo dõi:
```markdown
> Path: `docs/tasks/<tên_spec>/<tên_task_file>.md`
> Slice: `<mã_slice>` · Type: `<loại_task>` · Size: `<kích_thước>` · SP: `<story_points>`
> Depends on: `<các_task_phụ_thuộc>`
> Status: `<trạng_thái>`
> Created At: `YYYY-MM-DD`
> Updated At: `YYYY-MM-DD`
```
Agent phải cập nhật trường `Updated At` và `Status` mỗi khi có thay đổi trạng thái của task.

## 4. Tác giả & Người cập nhật (Created By / Updated By)
Trong tất cả các file mã nguồn, file task, file tài liệu, hoặc bất kỳ tài nguyên nào được tạo mới hoặc cập nhật bởi Agent, trường thông tin tác giả (`Created By`) và người cập nhật (`Updated By`) **BẮT BUỘC** phải ghi tên là: `Tam Khang`. Tuyệt đối không sử dụng `AI Agent` hay bất kỳ tên nào khác.

## 5. Ngôn ngữ hiển thị (User-Facing Language)
Tất cả những nội dung hiển thị trên trang web/giao diện người dùng hoặc phản hồi trực tiếp mà người dùng có thể đọc được (ví dụ: mô tả trường dữ liệu hiển thị, nhãn, thông báo lỗi, thông điệp phản hồi) **BẮT BUỘC** phải được viết bằng **Tiếng Việt**. Các thành phần kỹ thuật khác như mã nguồn, tên biến, tên hàm, chú thích (comments), tài liệu kỹ thuật (docstrings) vẫn viết bằng **Tiếng Anh**.

## 6. Chính sách Xóa dữ liệu (Soft Delete Policy)
Hệ thống **CHỈ CHẤP NHẬN** cơ chế Xóa mềm (**Soft Delete**) đối với tất cả các tài nguyên/thực thể dữ liệu trong toàn bộ hệ thống (ví dụ: cập nhật trạng thái `status` sang `DELETED` hoặc cờ xóa). Tuyệt đối **KHÔNG** sử dụng Xóa cứng (**Hard Delete**). Mọi thiết kế hoặc yêu cầu tính năng trước đây nếu chỉ định Hard Delete đều **BẮT BUỘC** phải chuyển đổi hoàn toàn sang Soft Delete.

