/*
File Name: errorMessages.js
Description: Central mapping from backend error codes / HTTP failures to Vietnamese user-facing messages.
Created At: 2026-11-15
Created By: AI Agent
Updated At: 2026-11-15
Updated By: AI Agent
*/

export const ERROR_CODE_MESSAGES = {
  // Academic
  'ERR-ACAD-ALREADY_ENROLLED': 'Học sinh đã được ghi danh vào lớp này.',
  'ERR-ACAD-ASSIGNMENT_EXISTS': 'Phân công giảng dạy này đã tồn tại.',
  'ERR-ACAD-ASSIGNMENT_NOT_FOUND': 'Không tìm thấy phân công giảng dạy.',
  'ERR-ACAD-CLASS_ACCESS_DENIED': 'Bạn không có quyền truy cập lớp học này.',
  'ERR-ACAD-CLASS_DUPLICATE_NAME': 'Tên lớp học đã tồn tại.',
  'ERR-ACAD-CLASS_NOT_FOUND': 'Không tìm thấy lớp học.',
  'ERR-ACAD-DUPLICATE_STUDENT_CODE': 'Mã học sinh đã tồn tại.',
  'ERR-ACAD-ENROLLMENT_NOT_FOUND': 'Không tìm thấy thông tin ghi danh.',
  'ERR-ACAD-INVALID_HEAD_TEACHER': 'Tổ trưởng bộ môn không hợp lệ.',
  'ERR-ACAD-INVALID_HOMEROOM_TEACHER': 'Giáo viên chủ nhiệm không hợp lệ.',
  'ERR-ACAD-INVALID_STUDENT_ROLE': 'Người dùng được chọn không phải là học sinh.',
  'ERR-ACAD-INVALID_TEACHER_ROLE': 'Người dùng được chọn không phải là giáo viên.',
  'ERR-ACAD-MISSING_STUDENT_INFO': 'Thiếu thông tin bắt buộc của học sinh.',
  'ERR-ACAD-ROLE_NOT_FOUND': 'Không tìm thấy vai trò.',
  'ERR-ACAD-STUDENT_NOT_FOUND': 'Không tìm thấy học sinh.',
  'ERR-ACAD-SUBJECT_DUPLICATE_NAME': 'Tên môn học đã tồn tại.',
  'ERR-ACAD-SUBJECT_NOT_FOUND': 'Không tìm thấy môn học.',
  // Admin
  'ERR-ADMIN-ADMIN_DELETE_LOCKED': 'Không thể xóa tài khoản quản trị viên.',
  'ERR-ADMIN-ADMIN_PERMS_LOCKED': 'Không thể thay đổi quyền của quản trị viên.',
  'ERR-ADMIN-ADMIN_ROLE_LOCKED': 'Không thể thay đổi vai trò quản trị viên.',
  'ERR-ADMIN-BACKUP_NOT_FOUND': 'Không tìm thấy bản sao lưu.',
  'ERR-ADMIN-DUPLICATE_CODE': 'Mã người dùng đã tồn tại.',
  'ERR-ADMIN-DUPLICATE_EMAIL': 'Email đã được sử dụng.',
  'ERR-ADMIN-DUPLICATE_PHONE': 'Số điện thoại đã được sử dụng.',
  'ERR-ADMIN-EMPTY_FILE': 'Tệp tải lên không có nội dung.',
  'ERR-ADMIN-FILE_TOO_LARGE': 'Tệp tải lên quá lớn.',
  'ERR-ADMIN-FILE_TYPE': 'Định dạng tệp không được hỗ trợ.',
  'ERR-ADMIN-INVALID_BIRTHDAY': 'Ngày sinh không hợp lệ.',
  'ERR-ADMIN-INVALID_PERMISSIONS': 'Danh sách quyền không hợp lệ.',
  'ERR-ADMIN-INVALID_ROLE': 'Vai trò không hợp lệ.',
  'ERR-ADMIN-INVALID_ROLE_CODE': 'Mã vai trò không hợp lệ.',
  'ERR-ADMIN-INVALID_STATUS': 'Trạng thái không hợp lệ.',
  'ERR-ADMIN-MISSING_COLUMN': 'Tệp thiếu cột bắt buộc. Vui lòng dùng tệp mẫu.',
  'ERR-ADMIN-REQUEST_NOT_FOUND': 'Không tìm thấy yêu cầu.',
  'ERR-ADMIN-ROLE_EXISTS': 'Vai trò đã tồn tại.',
  'ERR-ADMIN-ROLE_NOT_FOUND': 'Không tìm thấy vai trò.',
  'ERR-ADMIN-SCHEDULE_NOT_FOUND': 'Không tìm thấy lịch gửi báo cáo.',
  'ERR-ADMIN-SELF_BLOCK_LOCKED': 'Bạn không thể khóa hoặc xóa chính tài khoản của mình.',
  'ERR-ADMIN-SELF_ROLE_CHANGE': 'Bạn không thể thay đổi vai trò của chính mình.',
  'ERR-ADMIN-STUDENT_AGE_UNDER_16': 'Học sinh phải từ 16 tuổi trở lên.',
  'ERR-ADMIN-TEACHER_AGE_UNDER_22': 'Giáo viên phải từ 22 tuổi trở lên.',
  'ERR-ADMIN-TOO_MANY_ROWS': 'Tệp có quá nhiều dòng.',
  'ERR-ADMIN-UNKNOWN_PERMISSIONS': 'Danh sách quyền chứa quyền không tồn tại.',
  'ERR-ADMIN-USER_NOT_FOUND': 'Không tìm thấy người dùng.',
  // Auth
  'ERR-AUTH-ACCOUNT_BLOCKED': 'Tài khoản đã bị khóa. Vui lòng liên hệ quản trị viên.',
  'ERR-AUTH-ACCOUNT_INACTIVE': 'Tài khoản chưa được kích hoạt.',
  'ERR-AUTH-DUPLICATE_FIELD': 'Thông tin đã tồn tại trong hệ thống.',
  'ERR-AUTH-FORBIDDEN': 'Bạn không có quyền thực hiện thao tác này.',
  'ERR-AUTH-INVALID_CREDENTIALS': 'Tên đăng nhập hoặc mật khẩu không đúng.',
  'ERR-AUTH-INVALID_TOKEN': 'Phiên đăng nhập không hợp lệ hoặc đã hết hạn. Vui lòng đăng nhập lại.',
  'ERR-AUTH-MISSING_TOKEN': 'Bạn chưa đăng nhập. Vui lòng đăng nhập để tiếp tục.',
  'ERR-AUTH-OWNER_ONLY': 'Chỉ chủ sở hữu mới được thực hiện thao tác này.',
  'ERR-AUTH-PASSWORD_REUSE': 'Mật khẩu mới không được trùng mật khẩu cũ.',
  'ERR-AUTH-PERMISSION_DENIED': 'Bạn không có quyền thực hiện thao tác này.',
  'ERR-AUTH-TOO_MANY_ATTEMPTS': 'Bạn đã thử quá nhiều lần. Vui lòng thử lại sau.',
  // Documents
  'ERR-DOC-DUPLICATE_FILE': 'Tài liệu này đã được tải lên trước đó.',
  'ERR-DOC-FILE_TOO_LARGE': 'Tệp tài liệu quá lớn.',
  'ERR-DOC-INGEST_RUNNING': 'Tài liệu đang được xử lý. Vui lòng thử lại sau.',
  'ERR-DOC-INVALID_FILE_TYPE': 'Định dạng tài liệu không được hỗ trợ.',
  'ERR-DOC-INVALID_METADATA': 'Thông tin tài liệu không hợp lệ.',
  'ERR-DOC-INVALID_TITLE': 'Tiêu đề tài liệu không hợp lệ.',
  'ERR-DOC-NOT_FOUND': 'Không tìm thấy tài liệu.',
  'ERR-DOC-PERMISSION_DENIED': 'Bạn không có quyền với tài liệu này.',
  // Exercises
  'ERR-EXE-AI_BAD_REQUEST': 'Yêu cầu tạo bài tập bằng AI không hợp lệ.',
  'ERR-EXE-AI_BUSY': 'Hệ thống AI đang bận. Vui lòng thử lại sau ít phút.',
  'ERR-EXE-AI_CHAPTER_REQUIRED': 'Vui lòng chọn ít nhất một chương.',
  'ERR-EXE-AI_EMPTY_MATRIX': 'Vui lòng chọn số lượng câu hỏi lớn hơn 0.',
  'ERR-EXE-AI_FILE_NO_TEXT': 'Không đọc được nội dung văn bản trong tệp. Hãy dùng tệp có chữ (không phải ảnh quét).',
  'ERR-EXE-AI_FILE_TOO_LARGE': 'Tệp tải lên phải nhỏ hơn 1 MB.',
  'ERR-EXE-AI_FILE_TYPE': 'Định dạng tệp không được hỗ trợ (chỉ PDF, DOCX, TXT).',
  'ERR-EXE-AI_GENERATION_FAILED': 'AI chưa tạo được bài tập lúc này. Vui lòng thử lại.',
  'ERR-EXE-AI_INVALID_CHAPTER': 'Chương đã chọn không hợp lệ. Vui lòng chọn lại.',
  'ERR-EXE-AI_INVALID_PAYLOAD': 'Dữ liệu tạo bài tập bằng AI không hợp lệ.',
  'ERR-EXE-AI_LENGTH_REQUIRED': 'Không xác định được kích thước tệp tải lên.',
  'ERR-EXE-AI_MATRIX_TOO_LARGE': 'Số lượng câu hỏi yêu cầu vượt quá giới hạn.',
  'ERR-EXE-AI_GRADE_REQUIRED': 'Vui lòng chọn khối lớp (10-12) để tạo bài tập AI.',
  'ERR-EXE-AI_NO_CLASS': 'Bạn chưa thuộc lớp học nào nên chưa thể tạo bài tập AI.',
  'ERR-EXE-AI_PAYLOAD_REQUIRED': 'Thiếu dữ liệu tạo bài tập bằng AI.',
  'ERR-EXE-AI_TEACHER_ONLY': 'Chức năng này chỉ dành cho giáo viên.',
  'ERR-EXE-ANSWER_KEY_OWNER_ONLY': 'Chỉ người tạo bài tập mới xem được đáp án.',
  'ERR-EXE-ASSIGNMENT_EXPIRED': 'Bài tập đã hết hạn nộp.',
  'ERR-EXE-ASSIGNMENT_HAS_ATTEMPTS': 'Bài tập đã có lượt làm bài nên không thể thay đổi.',
  'ERR-EXE-ASSIGNMENT_NOT_FOUND': 'Không tìm thấy bài tập được giao.',
  'ERR-EXE-ATTEMPT_ACCESS_DENIED': 'Bạn không có quyền truy cập lượt làm bài này.',
  'ERR-EXE-ATTEMPT_ALREADY_OPEN': 'Bạn đang có một lượt làm bài chưa nộp.',
  'ERR-EXE-ATTEMPT_ALREADY_SUBMITTED': 'Lượt làm bài này đã được nộp.',
  'ERR-EXE-ATTEMPT_LIMIT_REACHED': 'Bạn đã hết số lượt làm bài cho phép.',
  'ERR-EXE-ATTEMPT_NOT_FOUND': 'Không tìm thấy lượt làm bài.',
  'ERR-EXE-ATTEMPT_NOT_OWNER': 'Lượt làm bài này không thuộc về bạn.',
  'ERR-EXE-CLASS_ACCESS_DENIED': 'Bạn không có quyền truy cập lớp học này.',
  'ERR-EXE-DUPLICATE_ASSIGNMENT': 'Bài tập đã được giao cho lớp này.',
  'ERR-EXE-EXERCISE_NOT_FOUND': 'Không tìm thấy bài tập.',
  'ERR-EXE-IMAGE_EMPTY': 'Ảnh tải lên không có nội dung.',
  'ERR-EXE-IMAGE_TOO_LARGE': 'Ảnh tải lên quá lớn.',
  'ERR-EXE-IMAGE_TYPE_NOT_ALLOWED': 'Định dạng ảnh không được hỗ trợ.',
  'ERR-EXE-IMPORT_DUPLICATE_FILE': 'Tệp này đã được nhập trước đó.',
  'ERR-EXE-IMPORT_FILE_TOO_LARGE': 'Tệp nhập quá lớn.',
  'ERR-EXE-IMPORT_FILE_TYPE_UNSUPPORTED': 'Định dạng tệp nhập không được hỗ trợ.',
  'ERR-EXE-IMPORT_INVALID_QUESTION': 'Tệp chứa câu hỏi không hợp lệ.',
  'ERR-EXE-INVALID_CURSOR': 'Tham số phân trang không hợp lệ.',
  'ERR-EXE-INVALID_SUBJECT_SCOPE': 'Môn học không nằm trong phạm vi của bạn.',
  'ERR-EXE-NOT_AN_EXAM': 'Bài tập này không phải bài kiểm tra.',
  'ERR-EXE-PDF_BUSY': 'Hệ thống đang xử lý tệp PDF khác. Vui lòng thử lại sau.',
  'ERR-EXE-QUESTION_NOT_FOUND': 'Không tìm thấy câu hỏi.',
  'ERR-EXE-STUDENT_NOT_ENROLLED': 'Học sinh chưa thuộc lớp được giao bài.',
  'ERR-EXE-SUBJECT_NOT_FOUND': 'Không tìm thấy môn học.',
  // User
  'ERR-USER-INVALID_AGE_STUDENT': 'Tuổi của học sinh không hợp lệ.',
};

const GENERIC = 'Đã xảy ra lỗi. Vui lòng thử lại sau.';

const STATUS_MESSAGES = {
  400: 'Yêu cầu không hợp lệ.',
  401: 'Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.',
  403: 'Bạn không có quyền thực hiện thao tác này.',
  404: 'Không tìm thấy dữ liệu yêu cầu.',
  409: 'Dữ liệu bị trùng hoặc xung đột với dữ liệu hiện có.',
  413: 'Tệp tải lên quá lớn.',
  415: 'Định dạng tệp không được hỗ trợ.',
  422: 'Dữ liệu nhập không hợp lệ. Vui lòng kiểm tra lại.',
  429: 'Bạn thao tác quá nhanh. Vui lòng thử lại sau.',
};

/**
 * Convert any thrown error into a Vietnamese message. Never returns backend text.
 * @param {*} err Axios error or any value.
 * @param {string} [fallback] Vietnamese message used when nothing more specific applies.
 */
export function getErrorMessage(err, fallback) {
  const generic = fallback || GENERIC;
  const res = err?.response;
  if (!res) {
    if (err?.code === 'ECONNABORTED' || /timeout/i.test(err?.message || '')) {
      return 'Máy chủ phản hồi quá chậm. Vui lòng thử lại.';
    }
    if (err?.request || err?.message === 'Network Error') {
      return 'Không thể kết nối tới máy chủ. Vui lòng kiểm tra kết nối mạng.';
    }
    return generic;
  }
  const detail = res.data?.detail;
  const code = detail && typeof detail === 'object' && !Array.isArray(detail) ? detail.code : undefined;
  if (code) {
    if (ERROR_CODE_MESSAGES[code]) return ERROR_CODE_MESSAGES[code];
    console.error('Unmapped backend error code:', code, detail);
    return generic;
  }
  if (res.status === 422) return STATUS_MESSAGES[422];
  if (res.status >= 500) return 'Máy chủ gặp sự cố. Vui lòng thử lại sau.';
  if (STATUS_MESSAGES[res.status]) return STATUS_MESSAGES[res.status];
  console.error('Unhandled error response:', res.status, detail);
  return generic;
}
