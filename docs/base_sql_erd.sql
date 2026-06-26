-- =====================================================================
-- SMARTLMS — HỆ THỐNG QUẢN LÝ BÀI TẬP & PHÂN TÍCH HÀNH VI HỌC TẬP
-- KỊCH BẢN KHỞI TẠO CƠ SỞ DỮ LIỆU (PostgreSQL) — PHIÊN BẢN HỢP NHẤT
-- =====================================================================
-- Sắp xếp theo nhóm domain + thứ tự phụ thuộc khóa ngoại, chạy tuần tự
-- từ trên xuống là tạo được toàn bộ schema.
--
-- BỐ CỤC:
--   1. PHÂN QUYỀN & TÀI KHOẢN (RBAC)
--   2. CƠ CẤU TỔ CHỨC (môn / lớp / ghi danh / phân công)
--   3. HỌC LIỆU & BÀI TẬP (tài liệu / đề / câu hỏi / đáp án)
--   4. GIAO BÀI & PHÂN TÍCH HÀNH VI (giao bài / lượt làm bài)
--   5. TƯƠNG TÁC & CÁ NHÂN HÓA (thông báo / mục tiêu / gợi ý)
--   6. INDEX CHIẾN LƯỢC
--
-- LƯU Ý (cố ý hoãn — làm khi vào đúng module cần):
--   • users.last_login_at (giám sát trực tuyến)
--   • trigger tự cập nhật updated_at (hiện xử lý ở tầng ứng dụng)
--   • trigger tự đồng bộ exercises.total_questions theo bảng questions
-- =====================================================================

-- Kích hoạt extension UUID để tự sinh ID bảo mật
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";


-- =====================================================================
-- 1. PHÂN QUYỀN & TÀI KHOẢN (RBAC)
-- =====================================================================
-- Mô hình phân quyền MỊN THEO PERMISSION (usecase), không chỉ theo role:
--   - Endpoint khai báo require_perm('CODE').
--   - Role là một "gói" permission (role_permissions) — Admin chỉnh runtime.
--   - Override theo user (user_permissions): allow/deny cho từng cá nhân.
--   - Tập quyền hiệu lực = role_permissions ∪ user(allow) − user(deny).
--     => DENY ưu tiên cao nhất; mặc định fail-closed (không có quyền = chặn).

-- 1.1 VAI TRÒ
CREATE TABLE roles (
    role_id INT PRIMARY KEY,
    role_name VARCHAR(50) NOT NULL UNIQUE
);

-- Khởi tạo 3 vai trò mặc định
INSERT INTO roles (role_id, role_name) VALUES
(1, 'Admin'),
(2, 'HocSinh'),
(3, 'GiaoVien');

-- 1.2 TÀI KHOẢN TẬP TRUNG
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phone VARCHAR(20) UNIQUE,
    email VARCHAR(100) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,           -- Chỉ lưu hash (bcrypt), không lưu plaintext
    full_name VARCHAR(100) NOT NULL,
    birthday DATE,
    role_id INT NOT NULL REFERENCES roles(role_id),
    status VARCHAR(20) DEFAULT 'Active',           -- Active, Inactive, Blocked
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 1.3 DANH MỤC QUYỀN — mỗi quyền = 1 usecase/endpoint
CREATE TABLE permissions (
    permission_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    permission_code VARCHAR(100) NOT NULL UNIQUE,  -- Mã usecase, vd: 'EXERCISE_CREATE'
    name VARCHAR(150) NOT NULL,                    -- Tên hiển thị cho Admin
    description TEXT,
    module VARCHAR(50),                            -- Nhóm theo module: auth, exercise, dashboard...
    http_method VARCHAR(10),                       -- Metadata endpoint (GET/POST/...) — tùy chọn
    url_pattern VARCHAR(255),                      -- Metadata endpoint (vd: '/api/v1/exercises') — tùy chọn
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 1.4 GÁN QUYỀN CHO VAI TRÒ — Admin chỉnh bảng này để phân quyền
CREATE TABLE role_permissions (
    role_id INT NOT NULL REFERENCES roles(role_id) ON DELETE CASCADE,
    permission_id UUID NOT NULL REFERENCES permissions(permission_id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, -- Audit: thời điểm gán
    PRIMARY KEY (role_id, permission_id)
);

-- 1.5 OVERRIDE QUYỀN THEO TỪNG USER — cấp thêm/thu hồi riêng cho 1 cá nhân
CREATE TABLE user_permissions (
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    permission_id UUID NOT NULL REFERENCES permissions(permission_id) ON DELETE CASCADE,
    effect VARCHAR(5) NOT NULL DEFAULT 'allow',    -- 'allow' | 'deny' (deny ưu tiên cao nhất)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, -- Cập nhật khi đổi effect
    PRIMARY KEY (user_id, permission_id),
    CONSTRAINT chk_user_perm_effect CHECK (effect IN ('allow', 'deny'))
);


-- =====================================================================
-- 2. CƠ CẤU TỔ CHỨC
-- =====================================================================

-- 2.1 DANH MỤC MÔN HỌC
CREATE TABLE subjects (
    subject_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    subject_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2.2 LỚP HỌC
CREATE TABLE classes (
    class_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    class_name VARCHAR(50) NOT NULL UNIQUE,
    homeroom_teacher_id UUID REFERENCES users(user_id) ON DELETE SET NULL, -- Giáo viên chủ nhiệm
    academic_year VARCHAR(20),                     -- Ví dụ: '2025-2026'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2.3 HỌC SINH THUỘC LỚP (ghi danh)
CREATE TABLE student_class (
    student_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    class_id UUID NOT NULL REFERENCES classes(class_id) ON DELETE CASCADE,
    student_code VARCHAR(50) UNIQUE,               -- Mã số học sinh định danh riêng
    PRIMARY KEY (student_id, class_id)
);

-- 2.4 PHÂN CÔNG GIÁO VIÊN BỘ MÔN (giáo viên nào dạy môn nào ở lớp nào)
CREATE TABLE teacher_subjects (
    teacher_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    class_id UUID NOT NULL REFERENCES classes(class_id) ON DELETE CASCADE,
    subject_id UUID NOT NULL REFERENCES subjects(subject_id) ON DELETE CASCADE,
    PRIMARY KEY (teacher_id, class_id, subject_id)
);


-- =====================================================================
-- 3. HỌC LIỆU & BÀI TẬP
-- =====================================================================

-- 3.1 TÀI LIỆU KIẾN THỨC NỀN — giáo viên tải lên làm đầu vào cho AI sinh đề
CREATE TABLE documents (
    document_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    uploaded_by UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    subject_id UUID REFERENCES subjects(subject_id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    file_url VARCHAR(500),                         -- Đường dẫn file gốc (PDF/Word/Giáo án)
    file_type VARCHAR(20),                         -- pdf, docx, text
    raw_content TEXT,                              -- Văn bản trích xuất / nhập trực tiếp cho AI
    status VARCHAR(20) DEFAULT 'Uploaded',         -- Uploaded, Processing, Ready, Failed
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3.2 KHO ĐỀ / BÀI TẬP
CREATE TABLE exercises (
    exercise_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    subject_id UUID NOT NULL REFERENCES subjects(subject_id) ON DELETE CASCADE,
    created_by UUID NOT NULL REFERENCES users(user_id), -- Giáo viên tạo đề
    total_questions INT DEFAULT 0,                 -- (hoãn) sẽ tự đồng bộ bằng trigger ở version sau
    ai_metadata JSONB,                             -- Ma trận kiến thức đầu vào cho AI sinh câu hỏi
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3.3 CÂU HỎI CHI TIẾT — tách cấu trúc để GV biên tập từng câu & AI ghi vào
CREATE TABLE questions (
    question_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    exercise_id UUID NOT NULL REFERENCES exercises(exercise_id) ON DELETE CASCADE,
    document_id UUID REFERENCES documents(document_id) ON DELETE SET NULL, -- Nguồn nếu do AI sinh
    content TEXT NOT NULL,
    question_type VARCHAR(20) NOT NULL DEFAULT 'MultipleChoice', -- MultipleChoice, ShortAnswer
    difficulty VARCHAR(20),                        -- NhanBiet, ThongHieu, VanDung
    correct_answer TEXT,                           -- Đáp án cho tự luận ngắn (trắc nghiệm dùng answer_options)
    explanation TEXT,                              -- Lời giải
    display_order INT DEFAULT 0,                   -- Thứ tự câu trong đề
    is_ai_generated BOOLEAN DEFAULT FALSE,         -- AI sinh hay GV tự nhập
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3.4 ĐÁP ÁN LỰA CHỌN (cho câu hỏi trắc nghiệm)
CREATE TABLE answer_options (
    option_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question_id UUID NOT NULL REFERENCES questions(question_id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    is_correct BOOLEAN DEFAULT FALSE,
    display_order INT DEFAULT 0
);


-- =====================================================================
-- 4. GIAO BÀI & PHÂN TÍCH HÀNH VI
-- =====================================================================

-- 4.1 BÀI TẬP ĐƯỢC GIAO CHO LỚP
CREATE TABLE class_assignments (
    assignment_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    class_id UUID NOT NULL REFERENCES classes(class_id) ON DELETE CASCADE,
    exercise_id UUID NOT NULL REFERENCES exercises(exercise_id) ON DELETE CASCADE,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    due_at TIMESTAMP WITH TIME ZONE                -- Hạn nộp (phục vụ cảnh báo tiến độ)
);

-- 4.2 THEO DÕI HÀNH VI & KẾT QUẢ LÀM BÀI (trọng tâm Learning Analytics)
CREATE TABLE student_exercise_attempts (
    attempt_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    assignment_id UUID NOT NULL REFERENCES class_assignments(assignment_id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,

    -- Số liệu phân tích hành vi học tập
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    total_time_seconds INT,                        -- Tổng thời gian làm bài thực tế (giây)
    focus_score INT,                               -- Chỉ số tập trung (hệ thống tự tính)
    behavior_logs JSONB,                           -- Chuỗi hành vi: chuyển tab, dừng ở mỗi câu...

    -- Kết quả & đánh giá năng lực
    score NUMERIC(5, 2),                           -- Điểm số (vd: 8.50)
    detailed_results JSONB,                        -- Đáp án từng câu + ma trận năng lực (NB/TH/VD)
    is_finished BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);


-- =====================================================================
-- 5. TƯƠNG TÁC & CÁ NHÂN HÓA
-- =====================================================================

-- 5.1 THÔNG BÁO / CẢNH BÁO (nhắc hạn nộp, cảnh báo tiến độ)
CREATE TABLE notifications (
    notification_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,                     -- DeadlineReminder, ProgressAlert, System
    title VARCHAR(255) NOT NULL,
    message TEXT,
    related_assignment_id UUID REFERENCES class_assignments(assignment_id) ON DELETE CASCADE,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5.2 MỤC TIÊU HỌC TẬP CỦA HỌC SINH (đặt mục tiêu điểm để hệ thống điều hướng ôn luyện)
CREATE TABLE student_goals (
    goal_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    subject_id UUID NOT NULL REFERENCES subjects(subject_id) ON DELETE CASCADE,
    target_score NUMERIC(5, 2),                    -- Mục tiêu điểm (vd: 9.00)
    target_date DATE,
    status VARCHAR(20) DEFAULT 'Active',           -- Active, Achieved, Expired
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (student_id, subject_id)                -- Mỗi HS 1 mục tiêu đang theo dõi / môn
);

-- 5.3 GỢI Ý LỘ TRÌNH HỌC (khuyến nghị sư phạm / vùng kiến thức cần bổ sung)
CREATE TABLE learning_recommendations (
    recommendation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    subject_id UUID REFERENCES subjects(subject_id) ON DELETE SET NULL,
    content JSONB,                                 -- Vùng kiến thức hổng + lộ trình ôn luyện
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);


-- =====================================================================
-- 6. INDEX CHIẾN LƯỢC
-- =====================================================================

-- --- RBAC ---
CREATE INDEX idx_role_permissions_permission ON role_permissions(permission_id); -- tra ngược role theo quyền
CREATE INDEX idx_user_permissions_user       ON user_permissions(user_id);        -- tính tập quyền hiệu lực
CREATE INDEX idx_permissions_module          ON permissions(module);              -- lọc quyền theo module

-- --- Phân tích hành vi & kết quả ---
CREATE INDEX idx_attempts_student    ON student_exercise_attempts(student_id);    -- HS xem lại lịch sử
CREATE INDEX idx_attempts_assignment ON student_exercise_attempts(assignment_id); -- GV theo dõi cả lớp
-- GIN: truy vấn sâu vào dữ liệu JSONB phức tạp
CREATE INDEX idx_attempts_behavior_logs    ON student_exercise_attempts USING gin (behavior_logs);
CREATE INDEX idx_attempts_detailed_results ON student_exercise_attempts USING gin (detailed_results);

-- --- Học liệu & bài tập ---
CREATE INDEX idx_questions_exercise      ON questions(exercise_id);          -- câu hỏi theo đề
CREATE INDEX idx_answer_options_question ON answer_options(question_id);     -- phương án theo câu
CREATE INDEX idx_documents_uploader      ON documents(uploaded_by);          -- kho học liệu của GV

-- --- Tương tác & cá nhân hóa ---
CREATE INDEX idx_notifications_user_unread ON notifications(user_id, is_read);    -- hộp thông báo chưa đọc
CREATE INDEX idx_student_goals_student     ON student_goals(student_id);          -- mục tiêu theo HS
CREATE INDEX idx_recommendations_student   ON learning_recommendations(student_id);
CREATE INDEX idx_recommendations_content   ON learning_recommendations USING gin (content);
