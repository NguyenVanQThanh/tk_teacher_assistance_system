# Sprint 4 — Kho Học liệu, Lịch Giảng dạy & Bảng Điều khiển Phân tích (Document Repository, Schedule & Analytics Dashboards)

> Path: `docs/v_1/sprints/sprint_4_overview.md` · Module(s): `document`, `academic`, `teacher`, `analytics`  
> Created At: `2026-09-23`  
> Created By: `Tam Khang`  
> Updated At: `2026-10-27`  
> Updated By: `Tam Khang`  

---

## 1. Mục tiêu Sprint (Sprint Objectives)

Triển khai nhóm tính năng **Ưu tiên 2 (Priority 2)** nhằm số hóa toàn diện học liệu số, công tác lập kế hoạch giảng dạy của Giáo viên và các bảng điều khiển phân tích năng lực (Dashboards), thay thế toàn bộ Mock Data còn lại trên Frontend:

1. **Kho Tài liệu & Học liệu Số (Document Repository - `F-DOC-01`)**: Xây dựng phân hệ upload, lưu trữ, quản lý metadata, phân loại theo môn học / khối lớp, xem trước (preview), tải xuống an toàn và xóa mềm/khôi phục tài liệu giảng dạy.
2. **Thời khóa biểu & Lịch Giảng dạy Giáo viên (Teacher Schedule & Timetable - `F-ACAD-05`)**: Xây dựng hệ thống quản lý lịch dạy, ca dạy, phòng học, phát hiện trùng lịch (conflict detection), phân loại mức độ khẩn cấp (Urgency Tagging) và danh sách ghi chú công việc sư phạm theo ngày.
3. **Bảng Điều khiển Phân tích Sư phạm cho Giáo viên (Teacher Analytics Dashboard - `F-DASH-01`)**: Cung cấp API thống kê số bài chờ chấm, phổ điểm, biểu đồ mạng nhện năng lực lớp học 6 trục, và cảnh báo học sinh nộp bài sát giờ cho `SubjectTeacherDashboard.jsx` và `HomeroomTeacherDashboard.jsx`.
4. **Bảng Điều khiển Tự đánh giá & Sinh đề AI cho Học sinh (Student Self-Evaluation Dashboard & AI Practice - `F-DASH-02`)**: Cung cấp API biểu đồ mạng nhện đa môn, nhận xét năng lực học tập và API sinh đề tự luyện tập bằng AI cho `StudentDashboard.jsx` và `StudentExercisesPage.jsx`.
5. **Tích hợp Frontend**: Kết nối trực tiếp [frontend/src/services/api.js](file:///e:/tk_teacher_assistance_system/frontend/src/services/api.js) với [DocumentRepositoryPage.jsx](file:///e:/tk_teacher_assistance_system/frontend/src/pages/teacher/DocumentRepositoryPage.jsx), [TeacherSchedulePage.jsx](file:///e:/tk_teacher_assistance_system/frontend/src/pages/teacher/TeacherSchedulePage.jsx), [TeacherDashboard.jsx](file:///e:/tk_teacher_assistance_system/frontend/src/pages/teacher/TeacherDashboard.jsx) và [StudentDashboard.jsx](file:///e:/tk_teacher_assistance_system/frontend/src/pages/student/StudentDashboard.jsx).

---

## 2. Thông tin Tổng quan (Sprint Metadata)

| Thuộc tính | Giá trị |
|:---|:---|
| **Sprint ID** | `SPRINT-04` |
| **Trạng thái** | `planning` |
| **Công nghệ Backend** | FastAPI · SQLAlchemy 2.0 · PostgreSQL · Alembic · Pydantic v2 · Python-Multipart · Local/S3 Storage Adapter |
| **Công nghệ Frontend** | React 18 · Axios Client · Lucide React · CSS Grid Calendar System |
| **Phụ thuộc** | `F-AUTH-01` (Auth/RBAC Core), `F-ACAD-01..04` (Môn học, lớp học, phân công giảng dạy), `F-EXE-01..06` (Bài tập, khảo thí, chấm điểm) |
| **Bảng CSDL liên quan** | `documents`, `teacher_schedules`, `teacher_notes`, `subjects`, `classes`, `users`, `student_exercise_attempts`, `notifications` |

---

## 3. Quyết định Thiết kế & Giả định Nghiệp vụ (Assumptions & Decisions)

| # | Quyết định | Lý do & Căn cứ kỹ thuật |
|:---|:---|:---|
| **AS-01** | **Chính sách Xóa mềm 100% (Soft Delete Policy)**: Tất cả tài liệu học liệu, lịch giảng dạy và ghi chú khi xóa chỉ chuyển `status` sang `DELETED`. Cung cấp endpoint `RESTORE` để khôi phục dữ liệu tức thì. | Tuân thủ Quy tắc 6 của hệ thống và bảo toàn dữ liệu học liệu qua các năm học. |
| **AS-02** | **Quản lý Lưu trữ File An toàn**: Hỗ trợ định dạng file: `.pdf`, `.docx`, `.doc`, `.pptx`, `.ppt`, `.xlsx`, dung lượng tối đa 50MB/file. File được lưu theo cấu trúc thư mục hashed trên đĩa cứng (`uploads/documents/YYYY/MM/UUID.ext`), che giấu đường dẫn thực trên server. | Đảm bảo tính bảo mật của tài nguyên giáo dục và tránh xung đột tên file. |
| **AS-03** | **Phân quyền Phạm vi Tài liệu (Document RBAC Scoping)**: Giáo viên có thể tải lên tài liệu cá nhân (chỉ GV đó thấy) hoặc tài liệu công khai toàn trường/tổ bộ môn (`is_public = true`). Giáo viên chỉ có quyền chỉnh sửa/xóa tài liệu do chính mình tải lên. Admin có toàn quyền quản trị. | Đảm bảo quyền tác giả của giáo viên và tăng tính chia sẻ trong tổ chuyên môn. |
| **AS-04** | **Phát hiện Trùng lịch (Conflict Detection)**: Khi giáo viên thêm hoặc sửa lịch kiểm tra, Backend tự động kiểm tra xem khung giờ (`start_time` - `end_time`) trong cùng một ngày có bị trùng với lịch kiểm tra khác của cùng giáo viên hay không. | Ngăn chặn việc xếp trùng lịch gây gián đoạn công tác giảng dạy thực tế. |
| **AS-05** | **Phân loại Mức độ Khẩn cấp (Urgency Tagging Dictionary)**: Lịch kiểm tra hỗ trợ các nhóm phân loại chuẩn hóa: `critical` (Khẩn cấp / Kiểm tra), `high` (Ưu tiên cao), `teaching` (Lịch giảng dạy). | Đồng bộ dữ liệu hiển thị màu sắc trên lưới thời khóa biểu của Frontend. |

---

## 4. Danh mục Features trong Sprint (Features List)

| Feature ID | Tên tính năng | Module | Tài liệu Spec / File Task | Trạng thái |
|:---|:---|:---|:---|:---:|
| `F-DOC-01` | **Teacher Document Repository** (Kho Học liệu & Quản lý Tài liệu) | `document` / `teacher` | [f_doc_01_document_repository_spec.md](../specs/f_doc_01_document_repository_spec.md) · [f_doc_01_document_repository.md](../../tasks/f_doc_01/f_doc_01_document_repository.md) | `planning` |
| `F-ACAD-05` | **Teacher Schedule & Timetable** (Thời khóa biểu & Lịch Giảng dạy) | `academic` / `teacher` | [f_acad_05_teacher_schedule_spec.md](../specs/f_acad_05_teacher_schedule_spec.md) · [f_acad_05_teacher_schedule.md](../../tasks/f_acad_05/f_acad_05_teacher_schedule.md) | `planning` |
| `F-DASH-01` | **Teacher Analytics Dashboard** (Bảng điều khiển phân tích cho GV Bộ môn & GVCN) | `analytics` / `teacher` | [f_dash_01_teacher_dashboard_spec.md](../specs/f_dash_01_teacher_dashboard_spec.md) · [f_dash_01_teacher_dashboard.md](../../tasks/f_dash_01/f_dash_01_teacher_dashboard.md) | `planning` |
| `F-DASH-02` | **Student Self-Evaluation Dashboard & AI Practice** (Dashboard tự đánh giá & AI sinh đề tự luyện) | `analytics` / `student` | [f_dash_02_student_dashboard_spec.md](../specs/f_dash_02_student_dashboard_spec.md) · [f_dash_02_student_dashboard.md](../../tasks/f_dash_02/f_dash_02_student_dashboard.md) | `planning` |

---

## 5. Chi tiết API Endpoints cần xây dựng

### 5.1. Phân hệ Kho Học liệu (`/api/v1/documents`)

```text
POST   /api/v1/documents/upload                Tải lên tài liệu mới kèm metadata (multipart/form-data)
GET    /api/v1/documents                       Danh sách tài liệu (Filter: subject_id, grade, type, search, pagination)
GET    /api/v1/documents/{id}                  Lấy thông tin chi tiết tài liệu
PUT    /api/v1/documents/{id}                  Cập nhật metadata tài liệu (tiêu đề, mô tả, môn học, khối lớp, tags)
DELETE /api/v1/documents/{id}                  Xóa mềm tài liệu (status = 'DELETED')
POST   /api/v1/documents/{id}/restore          Khôi phục tài liệu đã xóa mềm
GET    /api/v1/documents/{id}/download         Tải file tài liệu về máy (hỗ trợ Resume Download & Content-Disposition)
GET    /api/v1/documents/{id}/preview-url      Lấy URL xem trước tài liệu trực tuyến (PDF Stream / Image View)
```

### 5.2. Phân hệ Lịch Giảng dạy & Thời khóa biểu (`/api/v1/teacher/schedules`)

```text
GET    /api/v1/teacher/schedules               Lấy danh sách lịch dạy (Filter: month, year, week, grade, urgency)
POST   /api/v1/teacher/schedules               Tạo mới một tiết dạy / lịch kiểm tra (có validate trùng lịch)
GET    /api/v1/teacher/schedules/{id}          Xem chi tiết một ca dạy
PUT    /api/v1/teacher/schedules/{id}          Cập nhật thông tin ca dạy (thời gian, phòng học, tính chất)
DELETE /api/v1/teacher/schedules/{id}          Xóa mềm ca dạy (status = 'DELETED')
POST   /api/v1/teacher/schedules/{id}/restore  Khôi phục ca dạy đã xóa
GET    /api/v1/teacher/schedules/day/{date}    Lấy danh sách tiết dạy và timeline chi tiết trong ngày chỉ định

GET    /api/v1/teacher/notes                   Lấy danh sách ghi chú công việc theo ngày/tháng
POST   /api/v1/teacher/notes                   Thêm ghi chú công việc mới
PUT    /api/v1/teacher/notes/{id}              Cập nhật ghi chú (nội dung, trạng thái hoàn thành is_completed)
DELETE /api/v1/teacher/notes/{id}              Xóa mềm ghi chú công việc (status = 'DELETED')
```

### 5.3. Phân hệ Dashboard & Sinh đề AI (`/api/v1/analytics` & `/api/v1/ai`)

```text
GET    /api/v1/teacher/dashboard/summary       Thống kê nhanh cho GV (số bài chờ chấm, lớp dạy hôm nay, bài nộp gần đây)
GET    /api/v1/teacher/dashboard/radar         Dữ liệu biểu đồ mạng nhện 6 trục & nhận xét chất lượng học tập của lớp
GET    /api/v1/student/dashboard/overview      Dữ liệu biểu đồ mạng nhện đa môn, nhận xét năng lực & lịch học của học sinh
POST   /api/v1/exercises/generate-ai           AI sinh câu hỏi tự động từ chủ đề / tài liệu theo ma trận nhận thức (NB/TH/VD)
```

---

## 6. Sơ đồ Luồng Thực thi (Execution & Dependency Graph)

```mermaid
graph TD
    subgraph "Backend Phase 1: Kho Tài liệu (F-DOC-01)"
        A1[Alembic Migration: Cập nhật bảng documents] --> A2[Document Schemas & File Upload Validator]
        A2 --> A3[DocumentStorageService & Local/S3 File Manager]
        A3 --> A4[DocumentRepository & DocumentService CRUD/Restore]
        A4 --> A5[FastAPI Document Router: /api/v1/documents]
    end

    subgraph "Backend Phase 2: Lịch Giảng dạy (F-ACAD-05)"
        B1[Alembic Migration: Tạo bảng teacher_schedules & teacher_notes] --> B2[Schedule Schemas & Validation DTOs]
        B2 --> B3[ScheduleConflictDetectorService]
        B3 --> B4[TeacherScheduleRepository & Service CRUD/Restore]
        B4 --> B5[FastAPI Schedule Router: /api/v1/teacher/schedules]
    end

    subgraph "Backend Phase 3: Dashboards & AI Generation (F-DASH-01 & F-DASH-02)"
        D1[AnalyticsService: Radar 6 trục, Phổ điểm & Last-minute Alert] --> D2[FastAPI Dashboard Routers: /api/v1/teacher/dashboard & /api/v1/student/dashboard]
        D3[AiQuestionGeneratorService] --> D4[POST /api/v1/exercises/generate-ai]
    end

    subgraph "Phase 4: Frontend Integration"
        C1[Cập nhật frontend/src/services/api.js: documentsApi, scheduleApi, analyticsApi]
        A5 --> C1
        B5 --> C1
        D2 --> C1
        D4 --> C1
        C1 --> E1[Tích hợp DocumentRepositoryPage.jsx]
        C1 --> E2[Tích hợp TeacherSchedulePage.jsx]
        C1 --> E3[Tích hợp TeacherDashboard.jsx & StudentDashboard.jsx]
    end
```

---

## 7. Tiêu chuẩn Hoàn thành (Definition of Done — Sprint 4)

| ✓ | Tiêu chí Kiểm thử & Nghiệp vụ | Trạng thái |
|:---:|:---|:---:|
| ☐ | **Alembic Migrations**: Sinh và áp dụng migration cập nhật bảng `documents` và tạo bảng `teacher_schedules`, `teacher_notes` với cột `status` (`ACTIVE`, `INACTIVE`, `DELETED`). | `pending` |
| ☐ | **Document Upload & Storage**: Upload file thành công, kiểm soát đúng định dạng (.pdf, .docx, .pptx) và dung lượng, lưu file an toàn trên server. | `pending` |
| ☐ | **Document CRUD & Soft Delete**: Lọc tài liệu theo môn học, khối lớp, phân trang mượt mà; xóa mềm và khôi phục hoạt động 100%. | `pending` |
| ☐ | **Schedule Conflict Check**: API bắt lỗi và trả về mã lỗi `ERR-SCHED-TIME_CONFLICT` khi trùng ca dạy hoặc trùng phòng học. | `pending` |
| ☐ | **Teacher Notes CRUD**: Tạo, sửa, tick chọn hoàn thành và xóa mềm ghi chú công việc gắn với ngày học thành công. | `pending` |
| ☐ | **Dashboards & AI Generator API**: Cung cấp dữ liệu thật cho biểu đồ Radar giáo viên/học sinh và sinh đề tự luyện tập bằng AI. | `pending` |
| ☐ | **Tích hợp Frontend**: Kết nối hoàn chỉnh [DocumentRepositoryPage.jsx](file:///e:/tk_teacher_assistance_system/frontend/src/pages/teacher/DocumentRepositoryPage.jsx), [TeacherSchedulePage.jsx](file:///e:/tk_teacher_assistance_system/frontend/src/pages/teacher/TeacherSchedulePage.jsx), [TeacherDashboard.jsx](file:///e:/tk_teacher_assistance_system/frontend/src/pages/teacher/TeacherDashboard.jsx) và [StudentDashboard.jsx](file:///e:/tk_teacher_assistance_system/frontend/src/pages/student/StudentDashboard.jsx) với Backend API, loại bỏ toàn bộ mock state. | `pending` |
| ☐ | **Kiểm thử Tự động (Pytest)**: Viết và chạy thành công 100% bộ unit/integration tests cho module `document`, `schedule` và `analytics`. | `pending` |
| ☐ | **Chuẩn Code & Header**: Tuân thủ Quy tắc Coding Standards (100% comments bằng tiếng Anh, tác giả `Tam Khang`). | `pending` |

---

## 8. Danh mục Catalogs, Permissions & Error Codes khởi tạo

### 8.1. Danh mục Quyền hạn Mới (Permissions)
* `DOC_DOCUMENT_MANAGE`: Quyền tải lên, chỉnh sửa, xóa và khôi phục tài liệu học liệu.
* `DOC_DOCUMENT_VIEW`: Quyền xem danh sách, xem trước và tải về tài liệu học liệu.
* `SCHED_TEACHER_MANAGE`: Quyền tạo mới, chỉnh sửa, xóa lịch dạy và ghi chú công việc của giáo viên.
* `SCHED_TEACHER_VIEW`: Quyền xem lịch giảng dạy và thời khóa biểu của giáo viên.
* `DASH_TEACHER_VIEW`: Quyền xem báo cáo phân tích sư phạm trên Dashboard giáo viên.
* `DASH_STUDENT_VIEW`: Quyền xem báo cáo tự đánh giá năng lực trên Dashboard học sinh.

### 8.2. Danh mục Mã Lỗi Mới (Error Codes)
* `ERR-DOC-FILE_TYPE_UNSUPPORTED`: Định dạng file tải lên không nằm trong danh mục hỗ trợ.
* `ERR-DOC-FILE_SIZE_EXCEEDED`: Dung lượng file vượt quá giới hạn 50MB.
* `ERR-DOC-DOCUMENT_NOT_FOUND`: Tài liệu không tồn tại hoặc đã bị xóa.
* `ERR-DOC-ACCESS_DENIED`: Không có quyền thao tác trên tài liệu riêng tư của giáo viên khác.
* `ERR-SCHED-SCHEDULE_NOT_FOUND`: Lịch kiểm tra không tồn tại trong hệ thống.
* `ERR-SCHED-TIME_CONFLICT`: Khung giờ kiểm tra bị trùng với một lịch kiểm tra khác đã tồn tại.
* `ERR-SCHED-INVALID_TIME_RANGE`: Thời gian kết thúc phải diễn ra sau thời gian bắt đầu.
