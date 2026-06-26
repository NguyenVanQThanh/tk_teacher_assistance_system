-- =====================================================================
-- HỆ THỐNG QUẢN LÝ BÀI TẬP VÀ PHÂN TÍCH HÀNH VI HỌC TẬP
-- KỊCH BẢN KHỞI TẠO CƠ SỞ DỮ LIỆU ĐÃ TỐI ƯU (POSTGRESQL)
-- =====================================================================

-- Kích hoạt extension UUID để tự động tạo chuỗi ID bảo mật
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Comment: Ctrl + /

-- 1. BẢNG PHÂN QUYỀN (ROLES)
CREATE TABLE roles (
    role_id INT PRIMARY KEY, 
    role_name VARCHAR(50) NOT NULL UNIQUE
);

-- Khởi tạo các vai trò mặc định
INSERT INTO roles (role_id, role_name) VALUES 
(1, 'Admin'),
(2, 'HocSinh'),
(3, 'GiaoVien');

-- 2. BẢNG TÀI KHOẢN TẬP TRUNG (USERS)
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phone VARCHAR(20) UNIQUE,
    email VARCHAR(100) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    birthday DATE,
    role_id INT NOT NULL REFERENCES roles(role_id),
    status VARCHAR(20) DEFAULT 'Active', -- Active, Inactive, Blocked
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. BẢNG DANH MỤC MÔN HỌC (SUBJECTS)
CREATE TABLE subjects (
    subject_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    subject_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. BẢNG LỚP HỌC (CLASSES)
CREATE TABLE classes (
    class_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    class_name VARCHAR(50) NOT NULL UNIQUE,
    homeroom_teacher_id UUID REFERENCES users(user_id) ON DELETE SET NULL, -- Liên kết tới Giáo viên chủ nhiệm
    academic_year VARCHAR(20), -- Ví dụ: '2025-2026'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. BẢNG CHI TIẾT HỌC SINH THUỘC LỚP (STUDENT_CLASS)
CREATE TABLE student_class (
    student_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    class_id UUID NOT NULL REFERENCES classes(class_id) ON DELETE CASCADE,
    student_code VARCHAR(50) UNIQUE, -- Mã số học sinh định danh riêng
    PRIMARY KEY (student_id, class_id)
);

-- 6. BẢNG PHÂN CÔNG GIÁO VIÊN BỘ MÔN (TEACHER_SUBJECTS)
CREATE TABLE teacher_subjects (
    teacher_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    class_id UUID NOT NULL REFERENCES classes(class_id) ON DELETE CASCADE,
    subject_id UUID NOT NULL REFERENCES subjects(subject_id) ON DELETE CASCADE,
    PRIMARY KEY (teacher_id, class_id, subject_id)
);

-- 7. BẢNG KHO ĐỀ / BÀI TẬP (EXERCISES)
CREATE TABLE exercises (
    exercise_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    subject_id UUID NOT NULL REFERENCES subjects(subject_id) ON DELETE CASCADE,
    created_by UUID NOT NULL REFERENCES users(user_id), -- Giáo viên tạo đề
    total_questions INT DEFAULT 0,
    ai_metadata JSONB, -- Cấu trúc ma trận kiến thức đầu vào phục vụ AI sinh câu hỏi câu hỏi tự động
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 8. BẢNG CHI TIẾT BÀI TẬP ĐƯỢC GIAO CHO LỚP (CLASS_ASSIGNMENTS)
CREATE TABLE class_assignments (
    assignment_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    class_id UUID NOT NULL REFERENCES classes(class_id) ON DELETE CASCADE,
    exercise_id UUID NOT NULL REFERENCES exercises(exercise_id) ON DELETE CASCADE,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    due_at TIMESTAMP WITH TIME ZONE
);

-- 9. BẢNG THEO DÕI CHI TIẾT HÀNH VI & KẾT QUẢ LÀM BÀI (STUDENT_EXERCISE_ATTEMPTS)
CREATE TABLE student_exercise_attempts (
    attempt_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    assignment_id UUID NOT NULL REFERENCES class_assignments(assignment_id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    
    -- Số liệu phân tích hành vi học tập (Learning Behavior Analytics)
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    total_time_seconds INT, -- Tổng thời gian làm bài thực tế (tính ra giây)
    focus_score INT, -- Chỉ số tập trung (hệ thống tự tính toán dựa trên hành vi)
    behavior_logs JSONB, -- Lưu chi tiết chuỗi hành vi: chuyển tab, thời gian dừng ở mỗi câu...
    
    -- Kết quả và Đánh giá năng lực
    score NUMERIC(5, 2), -- Điểm số chi tiết (Ví dụ: 8.50)
    detailed_results JSONB, -- Đáp án từng câu và ma trận năng lực (Nhận biết, Thông hiểu, Vận dụng)
    is_finished BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================================
-- TẠO CÁC INDEX CHIẾN LƯỢC ĐỂ TỐI ƯU TRUY VẤN
-- =====================================================================

-- Tối ưu tốc độ cho tính năng: "Học sinh xem lại lịch sử và tự đánh giá năng lực cá nhân"
CREATE INDEX idx_attempts_student ON student_exercise_attempts(student_id);

-- Tối ưu tốc độ cho tính năng: "Giáo viên theo dõi tiến độ và hành vi của cả lớp trong 1 bài tập"
CREATE INDEX idx_attempts_assignment ON student_exercise_attempts(assignment_id);

-- GIN Index để tăng tốc độ phân tích và truy vấn sâu vào bên trong dữ liệu cấu trúc JSONB phức tạp
CREATE INDEX idx_attempts_behavior_logs ON student_exercise_attempts USING gin (behavior_logs);
CREATE INDEX idx_attempts_detailed_results ON student_exercise_attempts USING gin (detailed_results);


-- =====================================================================
-- =====================================================================
-- BỔ SUNG v1.1 — CÁC BẢNG PHỦ KÍN PHẠM VI CHỨC NĂNG SRS (Sprint S2 -> S6)
-- Mục tiêu: đóng kín các module còn thiếu bảng (Tạo sinh AI, Cảnh báo,
--           Mục tiêu học tập, Câu hỏi có cấu trúc, Gợi ý lộ trình).
-- Ghi chú: chỉ bổ sung BẢNG MỚI, không sửa cấu trúc bảng gốc v1.0.
--          Việc thêm cột vào bảng có sẵn sẽ làm ở version sau (v1.2+).
-- =====================================================================

-- 10. BẢNG TÀI LIỆU KIẾN THỨC NỀN (DOCUMENTS)
-- Phục vụ Module 2 (AI Generation): Giáo viên tải lên tài liệu nguồn.
CREATE TABLE documents (
    document_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    uploaded_by UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE, -- Giáo viên tải lên
    subject_id UUID REFERENCES subjects(subject_id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    file_url VARCHAR(500), -- Đường dẫn lưu trữ file gốc (PDF/Word/Giáo án)
    file_type VARCHAR(20), -- pdf, docx, text
    raw_content TEXT, -- Nội dung văn bản trích xuất hoặc nhập trực tiếp, làm đầu vào cho AI
    status VARCHAR(20) DEFAULT 'Uploaded', -- Uploaded, Processing, Ready, Failed
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 11. BẢNG CÂU HỎI CHI TIẾT (QUESTIONS)
-- Tách câu hỏi ra cấu trúc quan hệ để Giáo viên BIÊN TẬP từng câu (Module 2)
-- và là đích để AI ghi câu hỏi sinh tự động vào.
CREATE TABLE questions (
    question_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    exercise_id UUID NOT NULL REFERENCES exercises(exercise_id) ON DELETE CASCADE,
    document_id UUID REFERENCES documents(document_id) ON DELETE SET NULL, -- Tài liệu nguồn (nếu do AI sinh)
    content TEXT NOT NULL, -- Nội dung câu hỏi
    question_type VARCHAR(20) NOT NULL DEFAULT 'MultipleChoice', -- MultipleChoice, ShortAnswer
    difficulty VARCHAR(20), -- NhanBiet, ThongHieu, VanDung
    correct_answer TEXT, -- Đáp án đúng cho dạng tự luận ngắn (trắc nghiệm dùng answer_options)
    explanation TEXT, -- Lời giải / giải thích đáp án
    display_order INT DEFAULT 0, -- Thứ tự hiển thị câu trong đề
    is_ai_generated BOOLEAN DEFAULT FALSE, -- Phân biệt câu do AI sinh hay Giáo viên tự nhập
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 12. BẢNG ĐÁP ÁN LỰA CHỌN (ANSWER_OPTIONS)
-- Các phương án cho câu hỏi trắc nghiệm.
CREATE TABLE answer_options (
    option_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question_id UUID NOT NULL REFERENCES questions(question_id) ON DELETE CASCADE,
    content TEXT NOT NULL, -- Nội dung phương án
    is_correct BOOLEAN DEFAULT FALSE, -- Đánh dấu phương án đúng
    display_order INT DEFAULT 0
);

-- 13. BẢNG THÔNG BÁO / CẢNH BÁO (NOTIFICATIONS)
-- Phục vụ Module 1: "Cảnh báo tiến độ nộp bài" và nhắc hạn.
CREATE TABLE notifications (
    notification_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE, -- Người nhận thông báo
    type VARCHAR(50) NOT NULL, -- DeadlineReminder, ProgressAlert, System
    title VARCHAR(255) NOT NULL,
    message TEXT,
    related_assignment_id UUID REFERENCES class_assignments(assignment_id) ON DELETE CASCADE, -- Bài tập liên quan (nếu có)
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 14. BẢNG MỤC TIÊU HỌC TẬP CỦA HỌC SINH (STUDENT_GOALS)
-- Phục vụ Module 4: Học sinh thiết lập mục tiêu điểm số để hệ thống điều hướng ôn luyện.
CREATE TABLE student_goals (
    goal_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    subject_id UUID NOT NULL REFERENCES subjects(subject_id) ON DELETE CASCADE,
    target_score NUMERIC(5, 2), -- Mục tiêu điểm số (Ví dụ: 9.00)
    target_date DATE, -- Mốc thời gian muốn đạt
    status VARCHAR(20) DEFAULT 'Active', -- Active, Achieved, Expired
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (student_id, subject_id) -- Mỗi học sinh chỉ có 1 mục tiêu đang theo dõi trên mỗi môn
);

-- 15. BẢNG GỢI Ý LỘ TRÌNH HỌC (LEARNING_RECOMMENDATIONS)
-- Phục vụ Module 3 & 4: lưu vết khuyến nghị sư phạm / vùng kiến thức cần bổ sung.
CREATE TABLE learning_recommendations (
    recommendation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    subject_id UUID REFERENCES subjects(subject_id) ON DELETE SET NULL,
    content JSONB, -- Vùng kiến thức hổng + lộ trình ôn luyện do hệ thống/AI gợi ý
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ---------------------------------------------------------------------
-- INDEX CHIẾN LƯỢC CHO CÁC BẢNG BỔ SUNG v1.1
-- ---------------------------------------------------------------------

-- Lấy nhanh danh sách câu hỏi theo đề (màn hình GV biên tập / HS làm bài)
CREATE INDEX idx_questions_exercise ON questions(exercise_id);

-- Lấy nhanh các phương án theo câu hỏi
CREATE INDEX idx_answer_options_question ON answer_options(question_id);

-- Truy vấn tài liệu theo người tải lên (kho học liệu của GV)
CREATE INDEX idx_documents_uploader ON documents(uploaded_by);

-- Tối ưu hộp thông báo: lấy thông báo chưa đọc của 1 người dùng
CREATE INDEX idx_notifications_user_unread ON notifications(user_id, is_read);

-- Tối ưu Dashboard học sinh: tra mục tiêu theo học sinh
CREATE INDEX idx_student_goals_student ON student_goals(student_id);

-- Truy vấn gợi ý lộ trình mới nhất theo học sinh
CREATE INDEX idx_recommendations_student ON learning_recommendations(student_id);

-- GIN Index cho phân tích sâu nội dung gợi ý dạng JSONB
CREATE INDEX idx_recommendations_content ON learning_recommendations USING gin (content);


-- =====================================================================
-- =====================================================================
-- BỔ SUNG v1.2 — RBAC MỊN THEO PERMISSION (Sprint 0 / F-AUTH-01)
-- Mục tiêu: nâng phân quyền từ mức ROLE thô lên mức PERMISSION (usecase),
--           cho phép Admin gán/sửa quyền cho từng vai trò lúc runtime,
--           và override quyền cho từng user (allow/deny).
-- Mô hình: Usecase permission code. Endpoint khai báo require_perm('CODE').
--          Tập quyền hiệu lực của 1 user:
--            effective = role_permissions(role)  ∪  user_permissions(allow)
--                        − user_permissions(deny)        -- deny ưu tiên cao nhất
-- =====================================================================

-- 16. BẢNG DANH MỤC QUYỀN (PERMISSIONS) — mỗi quyền = 1 usecase/endpoint
CREATE TABLE permissions (
    permission_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    permission_code VARCHAR(100) NOT NULL UNIQUE, -- Mã usecase, vd: 'EXERCISE_CREATE'
    name VARCHAR(150) NOT NULL, -- Tên hiển thị cho Admin
    description TEXT,
    module VARCHAR(50), -- Nhóm theo module: auth, exercise, dashboard...
    http_method VARCHAR(10), -- Metadata tham chiếu endpoint (GET/POST/PUT/DELETE) - tùy chọn
    url_pattern VARCHAR(255), -- Metadata tham chiếu endpoint (vd: '/api/v1/exercises') - tùy chọn
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 17. GÁN QUYỀN CHO VAI TRÒ (ROLE_PERMISSIONS) — Admin chỉnh bảng này để phân quyền
CREATE TABLE role_permissions (
    role_id INT NOT NULL REFERENCES roles(role_id) ON DELETE CASCADE,
    permission_id UUID NOT NULL REFERENCES permissions(permission_id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, -- Audit: thời điểm gán quyền cho vai trò
    PRIMARY KEY (role_id, permission_id)
);

-- 18. OVERRIDE QUYỀN THEO TỪNG USER (USER_PERMISSIONS)
-- Cấp thêm (allow) hoặc thu hồi (deny) quyền riêng cho 1 user, ưu tiên hơn quyền theo role.
CREATE TABLE user_permissions (
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    permission_id UUID NOT NULL REFERENCES permissions(permission_id) ON DELETE CASCADE,
    effect VARCHAR(5) NOT NULL DEFAULT 'allow', -- 'allow' | 'deny' (deny ưu tiên cao nhất)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, -- Audit: thời điểm tạo override
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, -- Cập nhật khi đổi effect (allow<->deny)
    PRIMARY KEY (user_id, permission_id),
    CONSTRAINT chk_user_perm_effect CHECK (effect IN ('allow', 'deny'))
);

-- ---------------------------------------------------------------------
-- INDEX CHO RBAC v1.2
-- ---------------------------------------------------------------------

-- Tra ngược: những vai trò nào đang có 1 quyền cụ thể (màn hình Admin quản trị quyền)
CREATE INDEX idx_role_permissions_permission ON role_permissions(permission_id);

-- Tra nhanh override của 1 user khi tính tập quyền hiệu lực mỗi request
CREATE INDEX idx_user_permissions_user ON user_permissions(user_id);

-- Lọc danh mục quyền theo module (màn hình Admin nhóm quyền)
CREATE INDEX idx_permissions_module ON permissions(module);

