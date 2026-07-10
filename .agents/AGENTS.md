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

