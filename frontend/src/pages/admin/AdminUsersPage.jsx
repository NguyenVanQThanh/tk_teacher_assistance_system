// File Name: AdminUsersPage.jsx
// Description: Comprehensive User Management screen for Admin portal with strict name, phone, and DD/MM/YYYY date validations, auto-generated unique identifier code, backend connection, and original layout aesthetics.
// Created At: 2026-09-19
// Created By: Tam Khang
// Updated At: 2026-09-29
// Updated By: Tam Khang

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { 
  Download, 
  UserPlus, 
  Search, 
  X, 
  RotateCw, 
  ChevronDown, 
  Eye, 
  Edit2, 
  MoreVertical, 
  Lock, 
  Unlock, 
  FileSpreadsheet, 
  CheckCircle2, 
  AlertCircle, 
  HelpCircle,
  ChevronLeft,
  ChevronRight,
  Trash2,
  GraduationCap,
  Contact,
  Phone,
  Calendar,
  ArrowRight,
  Info,
  UserX,
  Key,
  Copy,
  Check
} from 'lucide-react';
import { adminUsersApi } from '../../services/api';
import './AdminUsersPage.css';

// Strict Calendar Date Validation (e.g. rejects 31/02/2020)
const validateCalendarDate = (dateStr) => {
  if (!dateStr || dateStr.length < 10) {
    return { valid: false, message: 'Vui lòng nhập đầy đủ ngày sinh định dạng DD/MM/YYYY.' };
  }
  const parts = dateStr.split('/');
  if (parts.length !== 3) {
    return { valid: false, message: 'Định dạng ngày sinh phải là DD/MM/YYYY.' };
  }
  const day = parseInt(parts[0], 10);
  const month = parseInt(parts[1], 10);
  const year = parseInt(parts[2], 10);

  if (isNaN(day) || isNaN(month) || isNaN(year)) {
    return { valid: false, message: 'Ngày tháng năm phải là chữ số hợp lệ.' };
  }

  if (month < 1 || month > 12) {
    return { valid: false, message: 'Tháng không hợp lệ (phải từ 01 đến 12).' };
  }

  const currentYear = new Date().getFullYear();
  if (year < 1920 || year > currentYear) {
    return { valid: false, message: `Năm sinh không hợp lệ (từ 1920 đến ${currentYear}).` };
  }

  // Days in month check (including leap years)
  const isLeapYear = (year % 4 === 0 && year % 100 !== 0) || (year % 400 === 0);
  const daysInMonths = [31, isLeapYear ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  const maxDays = daysInMonths[month - 1];

  if (day < 1 || day > maxDays) {
    if (month === 2) {
      return { 
        valid: false, 
        message: `Ngày không hợp lệ: Tháng 02 năm ${year} ${isLeapYear ? 'chỉ có tối đa 29 ngày (năm nhuận)' : 'chỉ có tối đa 28 ngày (năm không nhuận)'} - không tồn tại ngày ${parts[0]}/02/${year}!` 
      };
    }
    const monthNames = ['', '01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12'];
    return { 
      valid: false, 
      message: `Ngày không hợp lệ: Tháng ${monthNames[month]} chỉ có tối đa ${maxDays} ngày - không tồn tại ngày ${parts[0]}/${monthNames[month]}/${year}!` 
    };
  }

  // Check future date
  const today = new Date();
  const inputDate = new Date(year, month - 1, day);
  if (inputDate > today) {
    return { valid: false, message: 'Ngày sinh không thể ở tương lai.' };
  }

  return { valid: true, day, month, year };
};

// Age calculation helper
const calculateAgeFromDMY = (day, month, year) => {
  const today = new Date();
  let age = today.getFullYear() - year;
  const m = today.getMonth() - (month - 1);
  if (m < 0 || (m === 0 && today.getDate() < day)) {
    age--;
  }
  return age;
};

// Convert DD/MM/YYYY to YYYY-MM-DD for Backend API
const convertDMYtoISO = (dmyStr) => {
  if (!dmyStr || dmyStr.length < 10) return null;
  const parts = dmyStr.split('/');
  if (parts.length === 3) {
    return `${parts[2]}-${parts[1].padStart(2, '0')}-${parts[0].padStart(2, '0')}`;
  }
  return dmyStr;
};

// Strict DD/MM/YYYY Segmented Date Input Component
function DateOfBirthInput({ value, onChange, roleType, error, onErrorChange }) {
  const dayRef = useRef(null);
  const monthRef = useRef(null);
  const yearRef = useRef(null);

  const parts = (value || '').split('/');
  const day = parts[0] || '';
  const month = parts[1] || '';
  const year = parts[2] || '';

  const emitChange = (d, m, y) => {
    let combined = '';
    if (d || m || y) {
      combined = `${d}${m || y ? '/' : ''}${m}${y ? '/' : ''}${y}`;
    }
    onChange(combined);

    if (d.length === 2 && m.length === 2 && y.length === 4) {
      const fullDate = `${d}/${m}/${y}`;
      const check = validateCalendarDate(fullDate);
      if (!check.valid) {
        onErrorChange(check.message);
      } else {
        const age = calculateAgeFromDMY(check.day, check.month, check.year);
        if (roleType === 'student' && age < 16) {
          onErrorChange(`Học sinh phải từ 16 tuổi trở lên (Tuổi tính theo ngày sinh: ${age} tuổi).`);
        } else if (roleType === 'teacher' && age < 22) {
          onErrorChange(`Giáo viên phải từ 22 tuổi trở lên (Tuổi tính theo ngày sinh: ${age} tuổi).`);
        } else {
          onErrorChange(null);
        }
      }
    } else {
      if (error) onErrorChange(null);
    }
  };

  const handleDayKeyDown = (e) => {
    if (!/[0-9]/.test(e.key) && !['Backspace', 'Delete', 'ArrowLeft', 'ArrowRight', 'Tab', 'Enter'].includes(e.key)) {
      if (e.key === '/') {
        e.preventDefault();
        if (day.length > 0) {
          const padded = day.padStart(2, '0');
          emitChange(padded, month, year);
          monthRef.current?.focus();
        }
      } else {
        e.preventDefault();
      }
    }
    if (e.key === 'ArrowRight' && dayRef.current?.selectionStart === day.length) {
      monthRef.current?.focus();
    }
  };

  const handleDayChange = (e) => {
    const raw = e.target.value.replace(/\D/g, '').slice(0, 2);
    emitChange(raw, month, year);
    if (raw.length === 2) {
      monthRef.current?.focus();
      monthRef.current?.select();
    }
  };

  const handleMonthKeyDown = (e) => {
    if (!/[0-9]/.test(e.key) && !['Backspace', 'Delete', 'ArrowLeft', 'ArrowRight', 'Tab', 'Enter'].includes(e.key)) {
      if (e.key === '/') {
        e.preventDefault();
        if (month.length > 0) {
          const padded = month.padStart(2, '0');
          emitChange(day, padded, year);
          yearRef.current?.focus();
        }
      } else {
        e.preventDefault();
      }
    }
    if (e.key === 'Backspace' && month.length === 0) {
      dayRef.current?.focus();
    }
    if (e.key === 'ArrowLeft' && monthRef.current?.selectionStart === 0) {
      dayRef.current?.focus();
    }
    if (e.key === 'ArrowRight' && monthRef.current?.selectionStart === month.length) {
      yearRef.current?.focus();
    }
  };

  const handleMonthChange = (e) => {
    const raw = e.target.value.replace(/\D/g, '').slice(0, 2);
    emitChange(day, raw, year);
    if (raw.length === 2) {
      yearRef.current?.focus();
      yearRef.current?.select();
    }
  };

  const handleYearKeyDown = (e) => {
    if (!/[0-9]/.test(e.key) && !['Backspace', 'Delete', 'ArrowLeft', 'ArrowRight', 'Tab', 'Enter'].includes(e.key)) {
      e.preventDefault();
    }
    if (e.key === 'Backspace' && year.length === 0) {
      monthRef.current?.focus();
    }
    if (e.key === 'ArrowLeft' && yearRef.current?.selectionStart === 0) {
      monthRef.current?.focus();
    }
  };

  const handleYearChange = (e) => {
    const raw = e.target.value.replace(/\D/g, '').slice(0, 4);
    emitChange(day, month, raw);
  };

  const handlePaste = (e) => {
    e.preventDefault();
    const pasteText = e.clipboardData.getData('text').trim();
    let d = '', m = '', y = '';
    if (pasteText.includes('/')) {
      const p = pasteText.split('/');
      if (p.length === 3) {
        d = p[0].replace(/\D/g, '').slice(0, 2);
        m = p[1].replace(/\D/g, '').slice(0, 2);
        y = p[2].replace(/\D/g, '').slice(0, 4);
      }
    } else if (pasteText.includes('-')) {
      const p = pasteText.split('-');
      if (p.length === 3 && p[0].length === 4) {
        y = p[0].replace(/\D/g, '').slice(0, 4);
        m = p[1].replace(/\D/g, '').slice(0, 2);
        d = p[2].replace(/\D/g, '').slice(0, 2);
      }
    } else {
      const digits = pasteText.replace(/\D/g, '');
      if (digits.length >= 8) {
        d = digits.slice(0, 2);
        m = digits.slice(2, 4);
        y = digits.slice(4, 8);
      }
    }
    if (d || m || y) {
      emitChange(d, m, y);
    }
  };

  return (
    <div 
      className={`dob-input-container ${error ? 'has-error' : ''}`} 
      onPaste={handlePaste}
      onClick={(e) => {
        if (e.target === e.currentTarget) {
          if (!day) dayRef.current?.focus();
          else if (!month) monthRef.current?.focus();
          else if (!year) yearRef.current?.focus();
          else yearRef.current?.focus();
        }
      }}
    >
      <input
        ref={dayRef}
        type="text"
        inputMode="numeric"
        className="dob-segment-input dob-day"
        placeholder="DD"
        value={day}
        maxLength={2}
        onKeyDown={handleDayKeyDown}
        onChange={handleDayChange}
      />
      <span className="dob-divider">/</span>
      <input
        ref={monthRef}
        type="text"
        inputMode="numeric"
        className="dob-segment-input dob-month"
        placeholder="MM"
        value={month}
        maxLength={2}
        onKeyDown={handleMonthKeyDown}
        onChange={handleMonthChange}
      />
      <span className="dob-divider">/</span>
      <input
        ref={yearRef}
        type="text"
        inputMode="numeric"
        className="dob-segment-input dob-year"
        placeholder="YYYY"
        value={year}
        maxLength={4}
        onKeyDown={handleYearKeyDown}
        onChange={handleYearChange}
      />
      <span className="dob-calendar-icon">
        <Calendar size={15} />
      </span>
    </div>
  );
}

export default function AdminUsersPage() {
  // State for tabs & filters
  const [activeTab, setActiveTab] = useState('all'); // 'all' | 'students' | 'teachers' | 'pending'
  const [searchQuery, setSearchQuery] = useState('');
  const [gradeFilter, setGradeFilter] = useState('all');
  const [deptFilter, setDeptFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [selectedIds, setSelectedIds] = useState([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  // Active filter tags state
  const [filterTags, setFilterTags] = useState([
    { id: 'role', label: 'Tất cả vai trò' },
    { id: 'year', label: 'Niên khóa: 2024 - 2025' }
  ]);

  // Data state
  const [users, setUsers] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(false);

  // Modals state
  const [selectedUser, setSelectedUser] = useState(null);
  const [isViewModalOpen, setIsViewModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);
  const [isExportModalOpen, setIsExportModalOpen] = useState(false);
  const [toastMessage, setToastMessage] = useState(null);

  // Action dropdown menu state for table rows
  const [activeMenuUserId, setActiveMenuUserId] = useState(null);
  const menuRef = useRef(null);

  // Credential Result Modal (shows generated password & copy button)
  const [credentialResult, setCredentialResult] = useState(null);
  const [copiedPassword, setCopiedPassword] = useState(false);

  // Deactivate User Modal State (from 3-dots action)
  const [isDeactivateModalOpen, setIsDeactivateModalOpen] = useState(false);
  const [userToDeactivate, setUserToDeactivate] = useState(null);
  const [deactivateReason, setDeactivateReason] = useState('Tạm nghỉ công tác / Nghỉ thai sản');
  const [customDeactivateReason, setCustomDeactivateReason] = useState('');
  const [sendDeactivateEmail, setSendDeactivateEmail] = useState(true);

  // Add User Form State matching the modal design
  const [newUserForm, setNewUserForm] = useState({
    roleType: 'student', // 'student' | 'teacher'
    code: `HS${new Date().getFullYear()}${Math.floor(1000 + Math.random() * 9000)}`,
    fullName: '',
    birthDate: '', // Managed strictly as DD/MM/YYYY
    gender: 'Nam',
    phone: '',
    classRoom: 'Lớp 12A1 (Chuyên Toán)',
    academicYear: 'Niên khóa 2024 - 2025 (Hiện tại)',
    parentName: '',
    parentPhone: '',
    department: 'Tổ Toán - Tin',
    qualification: 'Thạc sĩ Sư phạm',
    teacherEmail: '',
    isActiveImmediately: true
  });

  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => {
      setToastMessage(null);
    }, 4000);
  };

  // Close 3-dots action menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setActiveMenuUserId(null);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Field Error States for strict validations
  const [nameError, setNameError] = useState(null);
  const [phoneError, setPhoneError] = useState(null);
  const [birthDateError, setBirthDateError] = useState(null);

  // Fetch users from Backend API
  const fetchUsers = useCallback(async () => {
    setLoading(true);
    try {
      let roleParam = undefined;
      if (activeTab === 'students') roleParam = 'student';
      else if (activeTab === 'teachers') roleParam = 'teacher';

      let statusParam = undefined;
      if (activeTab === 'pending') {
        statusParam = 'INACTIVE';
      } else if (statusFilter !== 'all') {
        statusParam = statusFilter.toUpperCase();
      }

      const params = {
        page: currentPage,
        page_size: pageSize,
        search: searchQuery.trim() || undefined,
        role: roleParam,
        status: statusParam,
        grade: gradeFilter === 'all' ? undefined : gradeFilter,
        department: deptFilter === 'all' ? undefined : deptFilter,
      };

      const data = await adminUsersApi.getUsers(params);
      const mapped = (data.items || []).map(u => ({
        id: u.id,
        code: u.code || `US${String(u.id).slice(0, 8).toUpperCase()}`,
        fullName: u.full_name,
        email: u.email || 'Chưa cập nhật email',
        phone: u.phone || '',
        birthday: u.birthday || '',
        role: u.role === 'Student' ? 'Học sinh' : (u.role === 'Teacher' ? 'Giáo viên' : 'Quản trị viên'),
        roleKey: (u.role || '').toLowerCase(),
        department: u.class_name || u.department || 'Chưa phân bổ',
        lastLoginRelative: u.last_login_relative || 'Chưa hoạt động',
        lastLoginDate: u.created_at ? new Date(u.created_at).toLocaleDateString('vi-VN') : 'Mới tạo',
        status: (u.status || 'ACTIVE').toLowerCase(), // 'active', 'inactive', 'suspended', 'deleted'
        avatarText: (u.full_name || 'US').trim().split(' ').slice(-2).map(w => w[0]).join('').toUpperCase(),
        avatarBg: (u.role || '').toLowerCase() === 'student' ? '#EDE9FE' : '#F3ECFF',
        avatarColor: (u.role || '').toLowerCase() === 'student' ? '#6D28D9' : '#5B32A8',
        rawUser: u
      }));

      setUsers(mapped);
      setTotalCount(data.total || 0);
      setTotalPages(data.total_pages || 1);
    } catch (err) {
      console.error('Failed to load user list:', err);
      showToast('Lỗi khi tải danh sách người dùng từ hệ thống.');
    } finally {
      setLoading(false);
    }
  }, [activeTab, statusFilter, gradeFilter, deptFilter, searchQuery, currentPage, pageSize]);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  // Auto-generate code from backend (guaranteed unique, read-only in input)
  const handleAutoGenerateCode = async (roleOverride) => {
    const roleToUse = roleOverride || newUserForm.roleType;
    try {
      const res = await adminUsersApi.generateCode(roleToUse);
      if (res && res.code) {
        setNewUserForm(prev => ({ ...prev, code: res.code }));
        showToast(`Đã tự động tạo mã định danh duy nhất: ${res.code}`);
        return;
      }
    } catch {
      // Fallback unique code
      const prefix = roleToUse === 'teacher' ? 'GV' : 'HS';
      const year = new Date().getFullYear();
      const rand = Math.floor(1000 + Math.random() * 9000);
      setNewUserForm(prev => ({ ...prev, code: `${prefix}${year}${rand}` }));
    }
  };

  const handleRoleTypeChange = (role) => {
    setNewUserForm(prev => ({ ...prev, roleType: role }));
    handleAutoGenerateCode(role);
  };

  // Full name input handler: DISALLOWS NUMBERS AND SPECIAL CHARACTERS
  const handleFullNameKeyDown = (e) => {
    if (
      !/^[a-zA-Z\sàáảãạăắằẳẵặâấầẩẫậđèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵÀÁẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬĐÈÉẺẼẸÊẾỀỂỄỆÌÍỈĨỊÒÓỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÙÚỦŨỤƯỨỪỬỮỰỲÝỶỸỴ]$/.test(e.key) &&
      !['Backspace', 'Delete', 'ArrowLeft', 'ArrowRight', 'Tab', 'Enter', 'Home', 'End'].includes(e.key)
    ) {
      e.preventDefault();
      setNameError('Họ và tên chỉ được nhập chữ cái và khoảng trắng, không chứa chữ số hoặc ký tự đặc biệt.');
    }
  };

  const handleFullNameChange = (e) => {
    const filtered = e.target.value.replace(/[^a-zA-Z\sàáảãạăắằẳẵặâấầẩẫậđèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵÀÁẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬĐÈÉẺẼẸÊẾỀỂỄỆÌÍỈĨỊÒÓỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÙÚỦŨỤƯỨỪỬỮỰỲÝỶỸỴ]/g, '');
    setNewUserForm(p => ({ ...p, fullName: filtered }));
    if (filtered.trim().length >= 2) {
      setNameError(null);
    }
  };

  // Phone input handler: ONLY ALLOWS DIGITS (MAX 10, STARTING WITH 0)
  const handlePhoneKeyDown = (e) => {
    if (!/[0-9]/.test(e.key) && !['Backspace', 'Delete', 'ArrowLeft', 'ArrowRight', 'Tab', 'Enter', 'Home', 'End'].includes(e.key)) {
      e.preventDefault();
      setPhoneError('Số điện thoại chỉ được nhập chữ số, không được điền chữ hay ký tự đặc biệt.');
    }
  };

  const handlePhoneChange = (e) => {
    const digitsOnly = e.target.value.replace(/\D/g, '').slice(0, 10);
    setNewUserForm(p => ({ ...p, phone: digitsOnly }));
    if (digitsOnly.length > 0 && !digitsOnly.startsWith('0')) {
      setPhoneError('Số điện thoại phải bắt đầu bằng chữ số 0.');
    } else if (digitsOnly.length === 10) {
      setPhoneError(null);
    } else {
      setPhoneError(null);
    }
  };

  // Open Add User Modal with refreshed unique code and reset validation errors
  const handleOpenAddModal = () => {
    setIsAddModalOpen(true);
    setNameError(null);
    setPhoneError(null);
    setBirthDateError(null);
    handleAutoGenerateCode(newUserForm.roleType);
  };

  // Submit Add User with thorough validation
  const handleCreateNewUser = async (e) => {
    e.preventDefault();

    // 1. Full name validation: must be at least 2 chars, letters and spaces only
    const trimmedName = newUserForm.fullName.trim();
    if (!trimmedName || trimmedName.length < 2) {
      setNameError('Vui lòng nhập họ và tên đầy đủ (tối thiểu 2 ký tự).');
      showToast('Vui lòng nhập họ và tên đầy đủ.');
      return;
    }

    const nameRegex = /^[a-zA-Z\sàáảãạăắằẳẵặâấầẩẫậđèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵÀÁẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬĐÈÉẺẼẸÊẾỀỂỄỆÌÍỈĨỊÒÓỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÙÚỦŨỤƯỨỪỬỮỰỲÝỶỸỴ]+$/;
    if (!nameRegex.test(trimmedName)) {
      setNameError('Họ và tên không được chứa chữ số hoặc ký tự đặc biệt.');
      showToast('Họ và tên không được chứa chữ số hoặc ký tự đặc biệt.');
      return;
    }

    // 2. Birthday validation: format DD/MM/YYYY, calendar check, age check
    const dateCheck = validateCalendarDate(newUserForm.birthDate);
    if (!dateCheck.valid) {
      setBirthDateError(dateCheck.message);
      showToast(dateCheck.message);
      return;
    }

    const age = calculateAgeFromDMY(dateCheck.day, dateCheck.month, dateCheck.year);
    if (newUserForm.roleType === 'student' && age < 16) {
      setBirthDateError(`Học sinh phải từ 16 tuổi trở lên (Tuổi hiện tại theo ngày sinh: ${age} tuổi).`);
      showToast(`Học sinh phải từ 16 tuổi trở lên (Tuổi hiện tại theo ngày sinh: ${age} tuổi).`);
      return;
    }
    if (newUserForm.roleType === 'teacher' && age < 22) {
      setBirthDateError(`Giáo viên phải từ 22 tuổi trở lên (Tuổi hiện tại theo ngày sinh: ${age} tuổi).`);
      showToast(`Giáo viên phải từ 22 tuổi trở lên (Tuổi hiện tại theo ngày sinh: ${age} tuổi).`);
      return;
    }

    // 3. Phone validation: exactly 10 digits starting with 0
    if (!newUserForm.phone || !/^0\d{9}$/.test(newUserForm.phone)) {
      setPhoneError('Số điện thoại phải gồm đúng 10 chữ số và bắt đầu bằng số 0 (ví dụ: 0912345678).');
      showToast('Số điện thoại phải gồm đúng 10 chữ số và bắt đầu bằng số 0.');
      return;
    }

    setLoading(true);
    try {
      const isStudent = newUserForm.roleType === 'student';
      const emailToUse = isStudent
        ? `${trimmedName.toLowerCase().replace(/\s+/g, '.')}.${newUserForm.code.toLowerCase()}@student.clarity.edu.vn`
        : `${trimmedName.toLowerCase().replace(/\s+/g, '.')}@clarity.edu.vn`;

      const payload = {
        full_name: trimmedName,
        role: isStudent ? 'Student' : 'Teacher',
        phone: newUserForm.phone,
        email: emailToUse,
        birthday: convertDMYtoISO(newUserForm.birthDate),
        code: newUserForm.code,
        department: isStudent ? null : newUserForm.department,
        class_name: isStudent ? newUserForm.classRoom : null,
        status: newUserForm.isActiveImmediately ? 'ACTIVE' : 'INACTIVE',
        is_active_immediately: newUserForm.isActiveImmediately
      };

      const res = await adminUsersApi.createUser(payload);

      setIsAddModalOpen(false);
      showToast(`Tạo thành công ${res.role === 'Student' ? 'Học sinh' : 'Giáo viên'} "${res.full_name}". Mật khẩu mặc định đã tự động sinh và gửi qua SMS / hệ thống.`);

      // Reset form
      setNewUserForm({
        roleType: 'student',
        code: '',
        fullName: '',
        birthDate: '',
        gender: 'Nam',
        phone: '',
        classRoom: 'Lớp 12A1 (Chuyên Toán)',
        academicYear: 'Niên khóa 2024 - 2025 (Hiện tại)',
        parentName: '',
        parentPhone: '',
        department: 'Tổ Toán - Tin',
        qualification: 'Thạc sĩ Sư phạm',
        teacherEmail: '',
        isActiveImmediately: true
      });
      setNameError(null);
      setPhoneError(null);
      setBirthDateError(null);

      await fetchUsers();
    } catch (err) {
      const errMsg = err.response?.data?.detail?.message || err.response?.data?.detail || err.message || 'Lỗi khi tạo người dùng.';
      showToast(`Lỗi: ${errMsg}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveDraft = () => {
    setIsAddModalOpen(false);
    showToast(`Đã lưu bản nháp thông tin người dùng "${newUserForm.fullName || newUserForm.code}".`);
  };

  const getDeactivateReasonsByRole = (roleKey) => {
    if (roleKey === 'teacher') {
      return [
        'Tạm nghỉ công tác / Nghỉ thai sản',
        'Chuyển trường / Chuyển công tác',
        'Hết hạn hợp đồng giảng dạy',
        'Nghỉ hưu theo chế độ',
        'Vi phạm quy định chuyên môn / Kỷ luật',
        'Lý do khác'
      ];
    }
    if (roleKey === 'student') {
      return [
        'Bảo lưu kết quả học tập / Tạm dừng học',
        'Chuyển trường / Chuyển nơi cư trú',
        'Đình chỉ học tập có thời hạn',
        'Đã tốt nghiệp / Hoàn thành chương trình',
        'Nghỉ học vì lý do sức khỏe',
        'Lý do khác'
      ];
    }
    return [
      'Điều chuyển công tác nội bộ',
      'Hết nhiệm kỳ quản trị / Bàn giao nhân sự',
      'Tạm ngưng quyền truy cập hệ thống',
      'Vi phạm quy định bảo mật',
      'Lý do khác'
    ];
  };

  const handleOpenDeactivateModal = (user) => {
    setUserToDeactivate(user);
    const reasons = getDeactivateReasonsByRole(user.roleKey);
    setDeactivateReason(reasons[0]);
    setCustomDeactivateReason('');
    setSendDeactivateEmail(true);
    setIsDeactivateModalOpen(true);
    setActiveMenuUserId(null);
  };

  const handleConfirmDeactivate = async () => {
    if (!userToDeactivate) return;
    const finalReason = deactivateReason === 'Lý do khác'
      ? (customDeactivateReason.trim() || 'Lý do khác')
      : deactivateReason;

    try {
      await adminUsersApi.updateStatus(userToDeactivate.id, 'SUSPENDED', finalReason);
      setIsDeactivateModalOpen(false);
      showToast(`Đã vô hiệu hóa tài khoản của ${userToDeactivate.fullName} thành công (Lý do: ${finalReason}).`);
      await fetchUsers();
    } catch (err) {
      showToast('Lỗi khi cập nhật trạng thái vô hiệu hóa.');
    }
  };

  // Quick toggle lock / unlock
  const handleToggleLockUser = async (user) => {
    const isLocked = user.status === 'locked' || user.status === 'suspended';
    const targetStatus = isLocked ? 'ACTIVE' : 'SUSPENDED';
    try {
      await adminUsersApi.updateStatus(user.id, targetStatus);
      showToast(targetStatus === 'SUSPENDED' ? `Đã tạm khóa tài khoản ${user.fullName}.` : `Đã mở khóa tài khoản ${user.fullName}.`);
      await fetchUsers();
    } catch (err) {
      showToast('Lỗi khi thay đổi trạng thái tài khoản.');
    }
  };

  // Soft delete user (updates status to 'DELETED')
  const handleSoftDeleteUser = async (user) => {
    setActiveMenuUserId(null);
    if (window.confirm(`Bạn có chắc chắn muốn xóa mềm (Soft Delete) tài khoản ${user.fullName}? Tài khoản sẽ chuyển sang trạng thái DELETED và bảo toàn lịch sử dữ liệu.`)) {
      try {
        await adminUsersApi.deleteUser(user.id);
        showToast(`Đã chuyển tài khoản ${user.fullName} sang trạng thái Xóa mềm (DELETED).`);
        await fetchUsers();
      } catch (err) {
        showToast('Lỗi khi thực hiện xóa mềm tài khoản.');
      }
    }
  };

  // Restore user
  const handleRestoreUser = async (user) => {
    setActiveMenuUserId(null);
    try {
      await adminUsersApi.restoreUser(user.id);
      showToast(`Đã khôi phục tài khoản ${user.fullName} về trạng thái Hoạt động.`);
      await fetchUsers();
    } catch (err) {
      showToast('Lỗi khi khôi phục tài khoản.');
    }
  };

  // Reset password
  const handleResetPassword = async (user) => {
    setActiveMenuUserId(null);
    if (window.confirm(`Bạn có chắc muốn đặt lại mật khẩu cho ${user.fullName}? Mật khẩu mặc định mới sẽ tự động tạo và gửi thông báo qua SMS/hệ thống.`)) {
      setLoading(true);
      try {
        const res = await adminUsersApi.resetPassword(user.id);
        setCredentialResult({
          title: 'Mật khẩu đã được đặt lại thành công!',
          fullName: user.fullName,
          code: user.code,
          role: user.role,
          phone: user.phone,
          email: user.email,
          temporaryPassword: res.temporary_password,
          notificationChannel: res.notification_channel || 'SMS & Thông báo hệ thống',
          notificationMessage: res.notification_message
        });
        showToast(`Đã đặt lại mật khẩu cho ${user.fullName}. Mật khẩu mới đã tự động gửi qua SMS/hệ thống.`);
      } catch (err) {
        showToast('Lỗi khi đặt lại mật khẩu.');
      } finally {
        setLoading(false);
      }
    }
  };

  // Update user in Edit Modal
  const handleUpdateUserSubmit = async (e) => {
    e.preventDefault();
    if (!selectedUser) return;

    const trimmedName = selectedUser.fullName.trim();
    if (!trimmedName || trimmedName.length < 2) {
      showToast('Họ và tên không được để trống (tối thiểu 2 ký tự).');
      return;
    }

    if (selectedUser.birthday) {
      const parts = selectedUser.birthday.split('-');
      if (parts.length === 3) {
        const age = calculateAgeFromDMY(parseInt(parts[2], 10), parseInt(parts[1], 10), parseInt(parts[0], 10));
        if (selectedUser.roleKey === 'student' && age < 16) {
          showToast(`Học sinh phải từ 16 tuổi trở lên (Tuổi hiện tại: ${age} tuổi).`);
          return;
        }
        if (selectedUser.roleKey === 'teacher' && age < 22) {
          showToast(`Giáo viên phải từ 22 tuổi trở lên (Tuổi hiện tại: ${age} tuổi).`);
          return;
        }
      }
    }

    setLoading(true);
    try {
      const payload = {
        full_name: trimmedName,
        phone: selectedUser.phone ? selectedUser.phone.replace(/\D/g, '') : null,
        email: selectedUser.email || null,
        birthday: selectedUser.birthday || null,
        status: selectedUser.status ? selectedUser.status.toUpperCase() : 'ACTIVE'
      };

      await adminUsersApi.updateUser(selectedUser.id, payload);
      setIsEditModalOpen(false);
      showToast(`Đã lưu thay đổi cho người dùng ${selectedUser.fullName}.`);
      await fetchUsers();
    } catch (err) {
      const errMsg = err.response?.data?.detail?.message || err.message || 'Lỗi khi cập nhật.';
      showToast(`Lỗi: ${errMsg}`);
    } finally {
      setLoading(false);
    }
  };

  // Export to Excel / CSV
  const handleExportSubmit = async () => {
    setIsExportModalOpen(false);
    showToast('Đang tạo và tải xuống tập tin danh sách người dùng...');
    try {
      const blob = await adminUsersApi.exportExcel({
        search: searchQuery.trim() || undefined,
        role: activeTab === 'all' ? undefined : (activeTab === 'students' ? 'student' : (activeTab === 'teachers' ? 'teacher' : undefined)),
        status: statusFilter === 'all' ? undefined : statusFilter.toUpperCase(),
        grade: gradeFilter === 'all' ? undefined : gradeFilter,
        department: deptFilter === 'all' ? undefined : deptFilter
      });

      const url = window.URL.createObjectURL(new Blob([blob], { type: 'text/csv;charset=utf-8;' }));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'danh_sach_nguoi_dung_smartlms.csv');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      showToast('Tải xuống tập tin thành công!');
    } catch (err) {
      showToast('Lỗi khi xuất danh sách.');
    }
  };

  // Import from Excel / CSV
  const handleImportFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    setLoading(true);
    showToast('Đang tiến hành nhập dữ liệu người dùng...');
    try {
      const res = await adminUsersApi.importExcel(formData);
      setIsImportModalOpen(false);
      showToast(`Nhập dữ liệu hoàn tất! Thành công: ${res.successful_count}/${res.total_processed} tài khoản.`);
      await fetchUsers();
    } catch (err) {
      const errMsg = err.response?.data?.detail?.message || 'Lỗi khi nhập file Excel.';
      showToast(`Lỗi: ${errMsg}`);
    } finally {
      setLoading(false);
    }
  };

  // Selection handlers
  const handleSelectAll = (e) => {
    if (e.target.checked) {
      setSelectedIds(users.map(u => u.id));
    } else {
      setSelectedIds([]);
    }
  };

  const handleToggleSelect = (id) => {
    setSelectedIds(prev => {
      if (prev.includes(id)) {
        return prev.filter(item => item !== id);
      } else {
        return [...prev, id];
      }
    });
  };

  const handleResetFilters = () => {
    setSearchQuery('');
    setGradeFilter('all');
    setDeptFilter('all');
    setStatusFilter('all');
    setActiveTab('all');
    setCurrentPage(1);
    showToast('Đã đặt lại tất cả bộ lọc về mặc định.');
  };

  const removeFilterTag = (tagId) => {
    setFilterTags(prev => prev.filter(t => t.id !== tagId));
  };

  const clearAllFilterTags = () => {
    setFilterTags([]);
    handleResetFilters();
  };

  return (
    <div className="admin-users-page-container">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="admin-toast">
          <CheckCircle2 size={18} />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* 1. Header Section */}
      <section className="users-page-header">
        <div className="users-header-title-block">
          <div className="users-header-title-row">
            <span className="users-title-accent-bar"></span>
            <h1 className="users-page-title">Quản lý người dùng</h1>
          </div>
          <p className="users-page-subtitle">
            Quản lý danh sách, thông tin tài khoản, phân quyền và trạng thái hoạt động của học sinh, giáo viên và nhân sự trong toàn trường.
          </p>
        </div>

        <div className="users-header-actions">
          <button 
            type="button" 
            className="btn-export-list"
            onClick={() => setIsExportModalOpen(true)}
          >
            <Download size={16} strokeWidth={2} />
            <span>Xuất danh sách</span>
          </button>

          <button 
            type="button" 
            className="btn-add-user"
            onClick={() => setIsAddModalOpen(true)}
          >
            <UserPlus size={16} strokeWidth={2} />
            <span>+ Thêm người dùng mới</span>
          </button>
        </div>
      </section>

      {/* 2. Tab Pills Row */}
      <section className="users-tabs-section">
        <div className="users-tabs-list">
          <button 
            type="button" 
            className={`users-tab-pill ${activeTab === 'all' ? 'active' : ''}`}
            onClick={() => { setActiveTab('all'); setCurrentPage(1); }}
          >
            Tất cả ({totalCount})
          </button>
          <button 
            type="button" 
            className={`users-tab-pill ${activeTab === 'students' ? 'active' : ''}`}
            onClick={() => { setActiveTab('students'); setCurrentPage(1); }}
          >
            Học sinh
          </button>
          <button 
            type="button" 
            className={`users-tab-pill ${activeTab === 'teachers' ? 'active' : ''}`}
            onClick={() => { setActiveTab('teachers'); setCurrentPage(1); }}
          >
            Giáo viên
          </button>
          <button 
            type="button" 
            className={`users-tab-pill ${activeTab === 'pending' ? 'active' : ''}`}
            onClick={() => { setActiveTab('pending'); setCurrentPage(1); }}
          >
            Chờ kích hoạt / Khóa
          </button>
        </div>

        <div className="users-selection-counter-block">
          <span className="users-selected-count-text">
            Đã chọn: <strong>{selectedIds.length}</strong>
          </span>
          <button 
            type="button" 
            className="users-refresh-icon-btn" 
            title="Làm mới danh sách"
            onClick={() => {
              setSelectedIds([]);
              fetchUsers();
              showToast('Đã làm mới danh sách dữ liệu.');
            }}
          >
            <RotateCw size={15} />
          </button>
        </div>
      </section>

      {/* 3. Main Filter Bar */}
      <section className="users-filter-bar-container">
        <div className="users-filter-bar">
          {/* Search Input */}
          <div className="filter-search-box">
            <Search size={16} className="filter-search-icon" />
            <input 
              type="text" 
              className="filter-search-input" 
              placeholder="Tìm theo họ tên, mã định danh hoặc số điện thoại..." 
              value={searchQuery}
              onChange={e => {
                setSearchQuery(e.target.value);
                setCurrentPage(1);
              }}
            />
            {searchQuery && (
              <button 
                type="button" 
                className="filter-search-clear"
                onClick={() => { setSearchQuery(''); setCurrentPage(1); }}
              >
                <X size={14} />
              </button>
            )}
          </div>

          {/* Grade Dropdown */}
          <div className="filter-select-wrapper">
            <select 
              className="filter-select"
              value={gradeFilter}
              onChange={e => { setGradeFilter(e.target.value); setCurrentPage(1); }}
            >
              <option value="all">Tất cả khối lớp</option>
              <option value="10">Khối 10</option>
              <option value="11">Khối 11</option>
              <option value="12">Khối 12</option>
            </select>
            <ChevronDown size={14} className="filter-select-arrow" />
          </div>

          {/* Department Dropdown */}
          <div className="filter-select-wrapper">
            <select 
              className="filter-select"
              value={deptFilter}
              onChange={e => { setDeptFilter(e.target.value); setCurrentPage(1); }}
            >
              <option value="all">Tất cả bộ môn</option>
              <option value="Toán">Tổ Toán - Tin</option>
              <option value="Ngoại ngữ">Tổ Ngoại ngữ</option>
              <option value="Ngữ văn">Tổ Ngữ văn</option>
              <option value="Vật lý">Tổ Vật lý</option>
              <option value="Hóa học">Tổ Hóa học</option>
              <option value="Sinh học">Tổ Sinh học</option>
              <option value="Lịch sử">Tổ Lịch sử</option>
            </select>
            <ChevronDown size={14} className="filter-select-arrow" />
          </div>

          {/* Status Dropdown */}
          <div className="filter-select-wrapper">
            <select 
              className="filter-select"
              value={statusFilter}
              onChange={e => { setStatusFilter(e.target.value); setCurrentPage(1); }}
            >
              <option value="all">Tất cả trạng thái</option>
              <option value="active">Hoạt động (ACTIVE)</option>
              <option value="inactive">Chờ kích hoạt (INACTIVE)</option>
              <option value="suspended">Tạm khóa (SUSPENDED)</option>
              <option value="deleted">Đã xóa mềm (DELETED)</option>
            </select>
            <ChevronDown size={14} className="filter-select-arrow" />
          </div>

          {/* Reset Filters Button (matching original style) */}
          <button 
            type="button" 
            className="filter-btn-reset"
            onClick={handleResetFilters}
            title="Đặt lại bộ lọc"
          >
            <RotateCw size={14} />
            <span>Đặt lại</span>
          </button>
        </div>

        {/* 4. Active Tags Row (matching original layout) */}
        {filterTags.length > 0 && (
          <section className="users-active-tags-row">
            <span className="tags-label">Bộ lọc đang áp dụng:</span>
            <div className="tags-list">
              {filterTags.map(tag => (
                <span key={tag.id} className="active-tag-chip">
                  <span>{tag.label}</span>
                  <button type="button" onClick={() => removeFilterTag(tag.id)}>
                    <X size={12} />
                  </button>
                </span>
              ))}
            </div>
            <button type="button" className="tags-clear-all" onClick={clearAllFilterTags}>
              Xóa tất cả
            </button>
          </section>
        )}
      </section>

      {/* 5. User Data Table (matching original layout and styling) */}
      <section className="users-table-card">
        <div className="users-table-scroll-wrapper">
          <table className="users-table">
            <thead>
              <tr>
                <th className="col-checkbox">
                  <input 
                    type="checkbox" 
                    className="custom-table-checkbox"
                    checked={users.length > 0 && selectedIds.length === users.length}
                    onChange={handleSelectAll}
                  />
                </th>
                <th className="col-code">MÃ ĐỊNH DANH</th>
                <th className="col-user">HỌ VÀ TÊN & LIÊN HỆ</th>
                <th className="col-role">VAI TRÒ</th>
                <th className="col-dept">LỚP / BỘ MÔN</th>
                <th className="col-last-login">ĐĂNG NHẬP GẦN NHẤT</th>
                <th className="col-status">TRẠNG THÁI</th>
                <th className="col-actions text-right">THAO TÁC</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="8" className="loading-table-cell">
                    <div className="loading-spinner"></div>
                    <p>Đang tải dữ liệu người dùng từ hệ thống...</p>
                  </td>
                </tr>
              ) : users.length === 0 ? (
                <tr>
                  <td colSpan="8" className="empty-table-cell">
                    <AlertCircle size={28} className="empty-icon" />
                    <p>Không tìm thấy người dùng nào phù hợp với bộ lọc.</p>
                  </td>
                </tr>
              ) : (
                users.map(user => {
                  const isSelected = selectedIds.includes(user.id);
                  const isDeleted = user.status === 'deleted';
                  const isMenuOpen = activeMenuUserId === user.id;

                  return (
                    <tr key={user.id} className={isSelected ? 'row-selected' : ''}>
                      {/* Checkbox */}
                      <td className="col-checkbox">
                        <input 
                          type="checkbox" 
                          className="custom-table-checkbox"
                          checked={isSelected}
                          onChange={() => handleToggleSelect(user.id)}
                        />
                      </td>

                      {/* Code identifier link */}
                      <td className="col-code">
                        <button 
                          type="button" 
                          className="user-code-link"
                          onClick={() => {
                            setSelectedUser(user);
                            setIsViewModalOpen(true);
                          }}
                        >
                          {user.code}
                        </button>
                      </td>

                      {/* User Avatar + Name + Contact */}
                      <td className="col-user">
                        <div className="table-user-block">
                          <div 
                            className="user-avatar-badge" 
                            style={{ backgroundColor: user.avatarBg, color: user.avatarColor }}
                          >
                            {user.avatarText}
                          </div>
                          <div className="user-meta-block">
                            <span 
                              className="user-full-name"
                              onClick={() => {
                                setSelectedUser(user);
                                setIsViewModalOpen(true);
                              }}
                            >
                              {user.fullName}
                            </span>
                            <span className="user-email-text">{user.phone ? `SĐT: ${user.phone}` : user.email}</span>
                          </div>
                        </div>
                      </td>

                      {/* Role Pill */}
                      <td className="col-role">
                        {user.roleKey === 'teacher' && (
                          <span className="role-pill teacher">Giáo viên</span>
                        )}
                        {user.roleKey === 'student' && (
                          <span className="role-pill student">Học sinh</span>
                        )}
                        {user.roleKey === 'admin' && (
                          <span className="role-pill admin">Quản trị viên</span>
                        )}
                      </td>

                      {/* Department / Class */}
                      <td className="col-dept">
                        <span className="user-dept-text">{user.department}</span>
                      </td>

                      {/* Last Login */}
                      <td className="col-last-login">
                        <div className="last-login-block">
                          <span className="login-relative-time">{user.lastLoginRelative}</span>
                          <span className="login-datetime">{user.lastLoginDate}</span>
                        </div>
                      </td>

                      {/* Status Pill */}
                      <td className="col-status">
                        {user.status === 'active' && (
                          <span className="user-status-pill active">
                            <span className="status-dot green"></span>
                            Hoạt động
                          </span>
                        )}
                        {user.status === 'inactive' && (
                          <span className="user-status-pill pending">
                            <span className="status-dot amber"></span>
                            Chờ kích hoạt
                          </span>
                        )}
                        {user.status === 'suspended' && (
                          <span className="user-status-pill locked">
                            <span className="status-dot purple"></span>
                            Tạm khóa
                          </span>
                        )}
                        {user.status === 'deleted' && (
                          <span className="user-status-pill locked" style={{ backgroundColor: '#FEE2E2', color: '#991B1B' }}>
                            <span className="status-dot" style={{ backgroundColor: '#DC2626' }}></span>
                            Đã xóa mềm
                          </span>
                        )}
                      </td>

                      {/* Action Icons (Matching EXACT original layout with 6 buttons) */}
                      <td className="col-actions text-right">
                        <div className="table-row-actions">
                          {/* 1. View details */}
                          <button 
                            type="button" 
                            className="table-action-icon-btn" 
                            title="Xem chi tiết hồ sơ"
                            onClick={() => {
                              setSelectedUser(user);
                              setIsViewModalOpen(true);
                            }}
                          >
                            <Eye size={16} />
                          </button>

                          {/* 2. Edit user */}
                          <button 
                            type="button" 
                            className="table-action-icon-btn" 
                            title="Chỉnh sửa thông tin"
                            onClick={() => {
                              setSelectedUser(user);
                              setIsEditModalOpen(true);
                            }}
                          >
                            <Edit2 size={16} />
                          </button>

                          {/* 3. Reset password */}
                          <button 
                            type="button" 
                            className="table-action-icon-btn text-warning" 
                            title="Đặt lại mật khẩu"
                            onClick={() => handleResetPassword(user)}
                          >
                            <Key size={16} />
                          </button>

                          {/* 4. Quick lock / unlock */}
                          <button 
                            type="button" 
                            className={`table-action-icon-btn ${user.status === 'suspended' ? 'text-locked' : ''}`}
                            title={user.status === 'suspended' ? 'Mở khóa tài khoản' : 'Tạm khóa tài khoản'}
                            onClick={() => handleToggleLockUser(user)}
                          >
                            {user.status === 'suspended' ? <Lock size={16} /> : <Unlock size={16} />}
                          </button>

                          {/* 5. Soft delete user */}
                          <button 
                            type="button" 
                            className="table-action-icon-btn text-danger" 
                            title="Xóa mềm tài khoản"
                            onClick={() => handleSoftDeleteUser(user)}
                          >
                            <Trash2 size={16} />
                          </button>

                          {/* 6. More options (3 dots dropdown menu) */}
                          <div className="table-action-menu-wrapper" ref={isMenuOpen ? menuRef : null}>
                            <button 
                              type="button" 
                              className="table-action-icon-btn" 
                              title="Tùy chọn khác"
                              onClick={() => setActiveMenuUserId(isMenuOpen ? null : user.id)}
                            >
                              <MoreVertical size={16} />
                            </button>

                            {/* Dropdown Menu */}
                            {isMenuOpen && (
                              <div className="table-action-menu-dropdown">
                                <button 
                                  type="button" 
                                  className="table-action-menu-item"
                                  onClick={() => {
                                    setActiveMenuUserId(null);
                                    handleOpenDeactivateModal(user);
                                  }}
                                >
                                  <UserX size={14} />
                                  <span>Vô hiệu hóa có lý do</span>
                                </button>

                                {isDeleted && (
                                  <button 
                                    type="button" 
                                    className="table-action-menu-item success"
                                    onClick={() => {
                                      setActiveMenuUserId(null);
                                      handleRestoreUser(user);
                                    }}
                                  >
                                    <RotateCw size={14} />
                                    <span>Khôi phục tài khoản</span>
                                  </button>
                                )}
                              </div>
                            )}
                          </div>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* 6. Pagination Footer (Matching original layout) */}
        <div className="users-pagination-footer">
          <div className="pagination-info">
            Hiển thị <strong>{users.length === 0 ? 0 : (currentPage - 1) * pageSize + 1}-{Math.min(currentPage * pageSize, totalCount)}</strong> trong số <strong>{totalCount}</strong> người dùng
          </div>

          <div className="pagination-controls">
            <div className="pagination-page-size-selector">
              <span>Hàng trên trang:</span>
              <select 
                value={pageSize}
                onChange={e => {
                  setPageSize(Number(e.target.value));
                  setCurrentPage(1);
                }}
                className="page-size-select"
              >
                <option value={10}>10</option>
                <option value={25}>25</option>
                <option value={50}>50</option>
              </select>
            </div>

            <div className="pagination-nav-buttons">
              <button 
                type="button" 
                className="page-nav-btn" 
                disabled={currentPage <= 1}
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
              >
                <ChevronLeft size={16} />
              </button>
              
              <span className="page-num-btn active">{currentPage}</span>
              <span style={{ fontSize: '13px', color: '#6B7280', margin: '0 4px' }}>/ {totalPages} trang</span>

              <button 
                type="button" 
                className="page-nav-btn"
                disabled={currentPage >= totalPages}
                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
              >
                <ChevronRight size={16} />
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* 7. Bottom Sync Banner */}
      <section className="users-sync-banner">
        <div className="sync-banner-left">
          <div className="sync-banner-icon-box">
            <HelpCircle size={22} />
          </div>
          <div className="sync-banner-text">
            <h4 className="sync-banner-title">
              Cần đồng bộ danh sách học sinh từ cơ sở dữ liệu Bộ GD&ĐT?
            </h4>
            <p className="sync-banner-desc">
              Hệ thống hỗ trợ nhập liệu hàng loạt qua file Excel / CSV với mẫu chuẩn hóa (tự động cấp mật khẩu và thông báo SMS).
            </p>
          </div>
        </div>

        <div className="sync-banner-actions">
          <button 
            type="button" 
            className="btn-sync-download-template"
            onClick={handleExportSubmit}
          >
            Tải file mẫu Excel / CSV
          </button>
          <button 
            type="button" 
            className="btn-sync-import-excel"
            onClick={() => setIsImportModalOpen(true)}
          >
            <FileSpreadsheet size={16} />
            <span>Nhập Excel</span>
          </button>
        </div>
      </section>

      {/* MODAL: Xem chi tiết người dùng */}
      {isViewModalOpen && selectedUser && (
        <div className="admin-modal-backdrop" onClick={() => setIsViewModalOpen(false)}>
          <div className="admin-modal-card" onClick={e => e.stopPropagation()}>
            <div className="admin-modal-header">
              <h3 className="admin-modal-title">Chi tiết tài khoản người dùng</h3>
              <button type="button" className="admin-modal-close" onClick={() => setIsViewModalOpen(false)}>
                <X size={20} />
              </button>
            </div>
            <div className="admin-modal-body">
              <div className="user-detail-card">
                <div 
                  className="user-avatar-badge-large"
                  style={{ backgroundColor: selectedUser.avatarBg, color: selectedUser.avatarColor }}
                >
                  {selectedUser.avatarText}
                </div>
                <div className="user-detail-header-meta">
                  <h3>{selectedUser.fullName}</h3>
                  <p>{selectedUser.email}</p>
                  <span className={`role-pill ${selectedUser.roleKey}`}>
                    {selectedUser.role}
                  </span>
                </div>
              </div>

              <div className="user-detail-info-grid">
                <div className="info-item">
                  <span className="info-label">Mã định danh:</span>
                  <strong className="info-value font-mono">{selectedUser.code}</strong>
                </div>
                <div className="info-item">
                  <span className="info-label">Số điện thoại:</span>
                  <span className="info-value">{selectedUser.phone || 'Chưa cập nhật'}</span>
                </div>
                <div className="info-item">
                  <span className="info-label">Ngày sinh:</span>
                  <span className="info-value">{selectedUser.birthday || 'Chưa cập nhật'}</span>
                </div>
                <div className="info-item">
                  <span className="info-label">Lớp / Phòng ban:</span>
                  <span className="info-value">{selectedUser.department}</span>
                </div>
                <div className="info-item">
                  <span className="info-label">Trạng thái:</span>
                  <span className="info-value font-bold" style={{ textTransform: 'uppercase' }}>{selectedUser.status}</span>
                </div>
                <div className="info-item">
                  <span className="info-label">Ngày khởi tạo:</span>
                  <span className="info-value">{selectedUser.lastLoginDate}</span>
                </div>
              </div>

              <div className="admin-modal-footer">
                <button type="button" className="admin-btn-primary" onClick={() => setIsViewModalOpen(false)}>
                  Đóng
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* MODAL: Chỉnh sửa người dùng */}
      {isEditModalOpen && selectedUser && (
        <div className="admin-modal-backdrop" onClick={() => setIsEditModalOpen(false)}>
          <div className="admin-modal-card" onClick={e => e.stopPropagation()}>
            <div className="admin-modal-header">
              <h3 className="admin-modal-title">Chỉnh sửa thông tin người dùng</h3>
              <button type="button" className="admin-modal-close" onClick={() => setIsEditModalOpen(false)}>
                <X size={20} />
              </button>
            </div>
            <form onSubmit={handleUpdateUserSubmit} className="admin-modal-body">
              <div className="admin-form-group">
                <label className="admin-form-label">Họ và tên *</label>
                <input 
                  type="text" 
                  className="admin-form-input" 
                  value={selectedUser.fullName}
                  onChange={e => {
                    const filtered = e.target.value.replace(/[^a-zA-Z\sàáảãạăắằẳẵặâấầẩẫậđèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵÀÁẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬĐÈÉẺẼẸÊẾỀỂỄỆÌÍỈĨỊÒÓỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÙÚỦŨỤƯỨỪỬỮỰỲÝỶỸỴ]/g, '');
                    setSelectedUser(p => ({ ...p, fullName: filtered }));
                  }}
                  required 
                />
              </div>

              <div className="admin-form-group">
                <label className="admin-form-label">Số điện thoại liên hệ</label>
                <input 
                  type="tel" 
                  className="admin-form-input" 
                  value={selectedUser.phone || ''}
                  placeholder="0912345678"
                  onChange={e => {
                    const digits = e.target.value.replace(/\D/g, '').slice(0, 10);
                    setSelectedUser(p => ({ ...p, phone: digits }));
                  }}
                />
              </div>

              <div className="admin-form-group">
                <label className="admin-form-label">Ngày sinh (YYYY-MM-DD)</label>
                <input 
                  type="date" 
                  className="admin-form-input" 
                  value={selectedUser.birthday || ''}
                  onChange={e => setSelectedUser(p => ({ ...p, birthday: e.target.value }))}
                />
                <span className="input-helper-text">
                  Học sinh yêu cầu từ 16 tuổi trở lên, giáo viên yêu cầu từ 22 tuổi trở lên.
                </span>
              </div>

              <div className="admin-form-row">
                <div className="admin-form-group flex-1">
                  <label className="admin-form-label">Lớp / Bộ môn</label>
                  <input 
                    type="text" 
                    className="admin-form-input" 
                    value={selectedUser.department || ''}
                    onChange={e => setSelectedUser(p => ({ ...p, department: e.target.value }))}
                  />
                </div>
                <div className="admin-form-group flex-1">
                  <label className="admin-form-label">Trạng thái</label>
                  <select 
                    className="admin-form-select"
                    value={selectedUser.status}
                    onChange={e => setSelectedUser(p => ({ ...p, status: e.target.value }))}
                  >
                    <option value="active">Hoạt động (ACTIVE)</option>
                    <option value="inactive">Chờ kích hoạt (INACTIVE)</option>
                    <option value="suspended">Tạm khóa (SUSPENDED)</option>
                    <option value="deleted">Đã xóa mềm (DELETED)</option>
                  </select>
                </div>
              </div>

              <div className="admin-modal-footer">
                <button type="button" className="admin-btn-cancel" onClick={() => setIsEditModalOpen(false)}>
                  Hủy
                </button>
                <button type="submit" className="admin-btn-primary">
                  Lưu thay đổi
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: Thêm người dùng mới (Strict validations, DD/MM/YYYY auto mask, auto unique code) */}
      {isAddModalOpen && (
        <div className="admin-modal-backdrop" onClick={() => setIsAddModalOpen(false)}>
          <div className="admin-modal-card modal-add-user" onClick={e => e.stopPropagation()}>
            {/* Modal Header */}
            <div className="admin-modal-header add-user-modal-header">
              <div className="add-user-title-group">
                <div className="add-user-icon-box">
                  <UserPlus size={20} />
                </div>
                <div className="add-user-title-meta">
                  <h3 className="add-user-modal-title">Thêm người dùng mới</h3>
                  <p className="add-user-modal-subtitle">
                    Nhập thông tin tài khoản và thiết lập vai trò trên hệ thống LMS toàn trường
                  </p>
                </div>
              </div>
              <button 
                type="button" 
                className="admin-modal-close" 
                onClick={() => setIsAddModalOpen(false)}
                title="Đóng"
              >
                <X size={20} />
              </button>
            </div>

            {/* Modal Body Form */}
            <form onSubmit={handleCreateNewUser} className="admin-modal-body add-user-modal-body">
              {/* Role Type Selector */}
              <div className="add-user-role-section">
                <div className="add-user-section-label">PHÂN LOẠI VAI TRÒ NGƯỜI DÙNG</div>
                <div className="add-user-role-buttons">
                  <button
                    type="button"
                    className={`role-choice-btn ${newUserForm.roleType === 'student' ? 'active' : ''}`}
                    onClick={() => handleRoleTypeChange('student')}
                  >
                    <GraduationCap size={18} />
                    <span>Học sinh</span>
                  </button>

                  <button
                    type="button"
                    className={`role-choice-btn ${newUserForm.roleType === 'teacher' ? 'active' : ''}`}
                    onClick={() => handleRoleTypeChange('teacher')}
                  >
                    <Contact size={18} />
                    <span>Giáo viên</span>
                  </button>
                </div>
              </div>

              {/* 2-Column Form Fields Grid */}
              <div className="add-user-form-grid">
                {/* Column 1 (Left) */}
                <div className="add-user-form-col">
                  {/* Mã định danh (Tự động tạo, ReadOnly, Không tự ý chỉnh sửa) */}
                  <div className="admin-form-group">
                    <div className="form-label-with-action">
                      <label className="admin-form-label">Mã định danh *</label>
                      <button 
                        type="button" 
                        className="btn-auto-generate"
                        onClick={() => handleAutoGenerateCode(newUserForm.roleType)}
                        title="Tạo lại mã ngẫu nhiên mới duy nhất từ hệ thống"
                      >
                        Tạo tự động
                      </button>
                    </div>
                    <div className="input-with-icon-right">
                      <input 
                        type="text" 
                        className="admin-form-input input-highlight-code"
                        value={newUserForm.code}
                        readOnly={true}
                        title="Mã định danh được tạo tự động và không được tự ý chỉnh sửa để tránh trùng lặp"
                        style={{ cursor: 'not-allowed', backgroundColor: '#F8F6FC', color: '#4D308D', fontWeight: 700 }}
                        required 
                      />
                      <span className="input-right-icon text-success">
                        <CheckCircle2 size={16} />
                      </span>
                    </div>
                    <span className="input-helper-text" style={{ fontSize: '11px', color: '#6B7280' }}>
                      Mã tự động tạo theo chuẩn hệ thống, chống trùng lặp.
                    </span>
                  </div>

                  {/* Họ và tên đầy đủ (Không chứa số hay ký tự đặc biệt) */}
                  <div className="admin-form-group">
                    <label className="admin-form-label">Họ và tên đầy đủ *</label>
                    <input 
                      type="text" 
                      className={`admin-form-input ${nameError ? 'has-error' : ''}`} 
                      placeholder="Ví dụ: Nguyễn Văn Hoàng"
                      value={newUserForm.fullName}
                      onKeyDown={handleFullNameKeyDown}
                      onChange={handleFullNameChange}
                      required 
                    />
                    {nameError ? (
                      <span className="field-error-text">{nameError}</span>
                    ) : (
                      <span className="input-helper-text" style={{ fontSize: '11px', color: '#6B7280' }}>
                        Chỉ cho phép nhập chữ cái và khoảng trắng, không nhập số hoặc ký tự đặc biệt.
                      </span>
                    )}
                  </div>

                  {/* Ngày sinh (DD/MM/YYYY) & Giới tính */}
                  <div className="admin-form-row">
                    <div className="admin-form-group flex-1">
                      <label className="admin-form-label">Ngày sinh (Ngày/Tháng/Năm) *</label>
                      <DateOfBirthInput
                        value={newUserForm.birthDate}
                        onChange={val => setNewUserForm(p => ({ ...p, birthDate: val }))}
                        roleType={newUserForm.roleType}
                        error={birthDateError}
                        onErrorChange={setBirthDateError}
                      />
                      {birthDateError ? (
                        <span className="field-error-text">{birthDateError}</span>
                      ) : (
                        <span className="input-helper-text" style={{ fontSize: '11px', color: '#6B7280' }}>
                          {newUserForm.roleType === 'student' ? 'Học sinh >= 16 tuổi (tự động DD/MM/YYYY)' : 'Giáo viên >= 22 tuổi (tự động DD/MM/YYYY)'}
                        </span>
                      )}
                    </div>

                    <div className="admin-form-group flex-1">
                      <label className="admin-form-label">Giới tính</label>
                      <div className="select-dropdown-wrapper">
                        <select 
                          className="admin-form-select"
                          value={newUserForm.gender}
                          onChange={e => setNewUserForm(p => ({ ...p, gender: e.target.value }))}
                        >
                          <option value="Nam">Nam</option>
                          <option value="Nữ">Nữ</option>
                          <option value="Khác">Khác</option>
                        </select>
                        <ChevronDown size={14} className="select-arrow-icon" />
                      </div>
                    </div>
                  </div>

                  {/* Số điện thoại (Chỉ cho phép nhập 10 chữ số, không nhập chữ) */}
                  <div className="admin-form-group">
                    <label className="admin-form-label">
                      {newUserForm.roleType === 'student' ? 'Số điện thoại học sinh *' : 'Số điện thoại giáo viên *'}
                    </label>
                    <div className="input-with-icon-left">
                      <span className="input-left-icon">
                        <Phone size={15} />
                      </span>
                      <input 
                        type="text" 
                        className={`admin-form-input font-mono ${phoneError ? 'has-error' : ''}`} 
                        placeholder="0912345678"
                        value={newUserForm.phone}
                        onKeyDown={handlePhoneKeyDown}
                        onChange={handlePhoneChange}
                        maxLength={10}
                        required
                      />
                    </div>
                    {phoneError ? (
                      <span className="field-error-text">{phoneError}</span>
                    ) : (
                      <span className="input-helper-text" style={{ fontSize: '11px', color: '#6B7280' }}>
                        Chỉ cho phép nhập số, gồm đúng 10 chữ số bắt đầu bằng số 0.
                      </span>
                    )}
                  </div>
                </div>

                {/* Column 2 (Right) */}
                <div className="add-user-form-col">
                  {/* Lớp học / Tổ bộ môn */}
                  <div className="admin-form-group">
                    <label className="admin-form-label">
                      {newUserForm.roleType === 'student' ? 'Lớp học' : 'Tổ bộ môn chuyên môn'}
                    </label>
                    <div className="select-dropdown-wrapper">
                      {newUserForm.roleType === 'student' ? (
                        <select 
                          className="admin-form-select"
                          value={newUserForm.classRoom}
                          onChange={e => setNewUserForm(p => ({ ...p, classRoom: e.target.value }))}
                        >
                          <option value="Lớp 12A1 (Chuyên Toán)">Lớp 12A1 (Chuyên Toán)</option>
                          <option value="Lớp 12A2 (Chuyên Lý)">Lớp 12A2 (Chuyên Lý)</option>
                          <option value="Lớp 11B1 (Cơ bản)">Lớp 11B1 (Cơ bản)</option>
                          <option value="Lớp 10A3 (Ngoại ngữ)">Lớp 10A3 (Ngoại ngữ)</option>
                        </select>
                      ) : (
                        <select 
                          className="admin-form-select"
                          value={newUserForm.department}
                          onChange={e => setNewUserForm(p => ({ ...p, department: e.target.value }))}
                        >
                          <option value="Tổ Toán - Tin">Tổ Toán - Tin</option>
                          <option value="Tổ Ngữ văn">Tổ Ngữ văn</option>
                          <option value="Tổ Ngoại ngữ">Tổ Ngoại ngữ</option>
                          <option value="Tổ Vật lý">Tổ Vật lý</option>
                          <option value="Tổ Hóa học">Tổ Hóa học</option>
                          <option value="Tổ Sinh học">Tổ Sinh học</option>
                          <option value="Tổ Lịch sử">Tổ Lịch sử</option>
                        </select>
                      )}
                      <ChevronDown size={14} className="select-arrow-icon" />
                    </div>
                  </div>

                  {/* Niên khóa áp dụng */}
                  <div className="admin-form-group">
                    <label className="admin-form-label">Niên khóa áp dụng</label>
                    <div className="select-dropdown-wrapper">
                      <select 
                        className="admin-form-select"
                        value={newUserForm.academicYear}
                        onChange={e => setNewUserForm(p => ({ ...p, academicYear: e.target.value }))}
                      >
                        <option value="Niên khóa 2024 - 2025 (Hiện tại)">Niên khóa 2024 - 2025 (Hiện tại)</option>
                        <option value="Niên khóa 2023 - 2024">Niên khóa 2023 - 2024</option>
                      </select>
                      <ChevronDown size={14} className="select-arrow-icon" />
                    </div>
                  </div>

                  {/* Tên phụ huynh / Bằng cấp */}
                  <div className="admin-form-group">
                    <label className="admin-form-label">
                      {newUserForm.roleType === 'student' ? 'Tên phụ huynh / Người giám hộ' : 'Trình độ / Bằng cấp'}
                    </label>
                    {newUserForm.roleType === 'student' ? (
                      <input 
                        type="text" 
                        className="admin-form-input" 
                        placeholder="Ví dụ: Nguyễn Văn Hải (Bố)"
                        value={newUserForm.parentName}
                        onChange={e => {
                          const filtered = e.target.value.replace(/[^a-zA-Z\sàáảãạăắằẳẵặâấầẩẫậđèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵÀÁẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬĐÈÉẺẼẸÊẾỀỂỄỆÌÍỈĨỊÒÓỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÙÚỦŨỤƯỨỪỬỮỰỲÝỶỸỴ()]/g, '');
                          setNewUserForm(p => ({ ...p, parentName: filtered }));
                        }}
                      />
                    ) : (
                      <input 
                        type="text" 
                        className="admin-form-input" 
                        placeholder="Ví dụ: Thạc sĩ Sư phạm Toán"
                        value={newUserForm.qualification}
                        onChange={e => setNewUserForm(p => ({ ...p, qualification: e.target.value }))}
                      />
                    )}
                  </div>

                  {/* SĐT phụ huynh / SĐT liên hệ */}
                  <div className="admin-form-group">
                    <label className="admin-form-label">
                      {newUserForm.roleType === 'student' ? 'Số điện thoại phụ huynh' : 'Số điện thoại dự phòng'}
                    </label>
                    <div className="input-with-icon-left">
                      <span className="input-left-icon">
                        {newUserForm.roleType === 'student' ? <Contact size={15} /> : <Phone size={15} />}
                      </span>
                      <input 
                        type="text" 
                        className="admin-form-input font-mono" 
                        placeholder="0987654321"
                        value={newUserForm.parentPhone}
                        onChange={e => {
                          const digits = e.target.value.replace(/\D/g, '').slice(0, 10);
                          setNewUserForm(p => ({ ...p, parentPhone: digits }));
                        }}
                        maxLength={10}
                      />
                    </div>
                  </div>

                  {/* Kích hoạt ngay checkbox */}
                  <div className="admin-form-checkbox-row" style={{ marginTop: '16px' }}>
                    <label className="custom-checkbox-label">
                      <input 
                        type="checkbox" 
                        checked={newUserForm.isActiveImmediately}
                        onChange={e => setNewUserForm(p => ({ ...p, isActiveImmediately: e.target.checked }))}
                        className="custom-checkbox-input"
                      />
                      <span className="checkbox-text">Kích hoạt tài khoản ngay sau khi tạo</span>
                    </label>
                  </div>
                </div>
              </div>

              {/* Batch Import Notice Banner */}
              <div className="add-user-import-banner">
                <div className="import-banner-left">
                  <Info size={16} className="import-banner-info-icon" />
                  <span className="import-banner-text">
                    Cần thêm nhiều người dùng cùng lúc? Nhập tự động từ bảng dữ liệu SMAS / VnEdu.
                  </span>
                </div>
                <button 
                  type="button" 
                  className="btn-link-import-excel"
                  onClick={() => {
                    setIsAddModalOpen(false);
                    setIsImportModalOpen(true);
                  }}
                >
                  <span>Nhập từ Excel / CSV</span>
                  <ArrowRight size={14} />
                </button>
              </div>

              {/* Modal Footer */}
              <div className="add-user-modal-footer">
                <button 
                  type="button" 
                  className="btn-add-modal-cancel" 
                  onClick={() => setIsAddModalOpen(false)}
                >
                  Hủy bỏ
                </button>
                <div className="add-user-footer-right">
                  <button 
                    type="button" 
                    className="btn-add-modal-draft"
                    onClick={handleSaveDraft}
                  >
                    Lưu bản nháp
                  </button>
                  <button 
                    type="submit" 
                    className="btn-add-modal-submit"
                  >
                    <UserPlus size={16} />
                    <span>+ Tạo người dùng mới</span>
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      )}


      {/* MODAL: Vô hiệu hóa tài khoản */}
      {isDeactivateModalOpen && userToDeactivate && (
        <div className="admin-modal-backdrop" onClick={() => setIsDeactivateModalOpen(false)}>
          <div className="admin-modal-card modal-deactivate-user" onClick={e => e.stopPropagation()}>
            <div className="deactivate-modal-header">
              <button 
                type="button" 
                className="admin-modal-close" 
                onClick={() => setIsDeactivateModalOpen(false)}
                title="Đóng"
              >
                <X size={20} />
              </button>
            </div>

            <div className="deactivate-modal-body">
              <div className="deactivate-icon-wrapper">
                <div className="deactivate-icon-circle">
                  <UserX size={26} strokeWidth={2.2} />
                </div>
              </div>

              <h3 className="deactivate-modal-title">Vô hiệu hóa tài khoản?</h3>
              <p className="deactivate-modal-desc">
                Bạn có chắc chắn muốn vô hiệu hóa tài khoản của <strong>{userToDeactivate.fullName}</strong> (<strong>{userToDeactivate.code}</strong>)? Người dùng này sẽ tạm thời không thể đăng nhập vào LMS và truy cập các lớp giảng dạy.
              </p>

              <div className="deactivate-user-preview">
                <div 
                  className="preview-avatar-badge"
                  style={{ backgroundColor: userToDeactivate.avatarBg, color: userToDeactivate.avatarColor }}
                >
                  {userToDeactivate.avatarText}
                </div>

                <div className="preview-user-meta">
                  <h4 className="preview-user-name">{userToDeactivate.fullName}</h4>
                  <p className="preview-user-sub">
                    {userToDeactivate.email} • {userToDeactivate.department}
                  </p>
                </div>

                <div className="preview-user-role">
                  <span className={`preview-role-pill ${userToDeactivate.roleKey}`}>
                    {userToDeactivate.role}
                  </span>
                </div>
              </div>

              <div className="admin-form-group deactivate-reason-group">
                <label className="admin-form-label">Lý do vô hiệu hóa *</label>
                <div className="select-dropdown-wrapper">
                  <select 
                    className="admin-form-select"
                    value={deactivateReason}
                    onChange={e => setDeactivateReason(e.target.value)}
                  >
                    {getDeactivateReasonsByRole(userToDeactivate.roleKey).map(reason => (
                      <option key={reason} value={reason}>{reason}</option>
                    ))}
                  </select>
                  <ChevronDown size={14} className="select-arrow-icon" />
                </div>
              </div>

              {deactivateReason === 'Lý do khác' && (
                <div className="admin-form-group custom-reason-group">
                  <label className="admin-form-label">Ghi rõ lý do khác *</label>
                  <textarea 
                    className="admin-form-textarea"
                    rows={2}
                    placeholder="Nhập chi tiết lý do vô hiệu hóa tài khoản..."
                    value={customDeactivateReason}
                    onChange={e => setCustomDeactivateReason(e.target.value)}
                    required
                    autoFocus
                  />
                  <span className="input-helper-text">
                    Nội dung này sẽ được ghi nhận vào nhật ký kiểm toán hệ thống.
                  </span>
                </div>
              )}

              <div className="admin-form-checkbox-row deactivate-checkbox-row">
                <label className="custom-checkbox-label">
                  <input 
                    type="checkbox" 
                    checked={sendDeactivateEmail}
                    onChange={e => setSendDeactivateEmail(e.target.checked)}
                    className="custom-checkbox-input"
                  />
                  <span className="checkbox-text">
                    Gửi thông báo tự động tới {userToDeactivate.roleKey === 'teacher' ? 'giáo viên' : 'học sinh'}
                  </span>
                </label>
              </div>

              <div className="deactivate-modal-footer">
                <button 
                  type="button" 
                  className="btn-deactivate-cancel" 
                  onClick={() => setIsDeactivateModalOpen(false)}
                >
                  Hủy bỏ
                </button>
                <button 
                  type="button" 
                  className="btn-deactivate-confirm"
                  onClick={handleConfirmDeactivate}
                >
                  <UserX size={16} />
                  <span>Vô hiệu hóa tài khoản</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* MODAL: Nhập Excel / CSV */}
      {isImportModalOpen && (
        <div className="admin-modal-backdrop" onClick={() => setIsImportModalOpen(false)}>
          <div className="admin-modal-card modal-lg" onClick={e => e.stopPropagation()}>
            <div className="admin-modal-header">
              <h3 className="admin-modal-title">Nhập danh sách người dùng từ Excel / CSV</h3>
              <button type="button" className="admin-modal-close" onClick={() => setIsImportModalOpen(false)}>
                <X size={20} />
              </button>
            </div>
            <div className="admin-modal-body">
              <div className="excel-dropzone">
                <FileSpreadsheet size={42} className="excel-dropzone-icon" />
                <h4>Kéo thả tập tin (.xlsx, .csv) vào đây</h4>
                <p>hoặc nhấn để chọn tệp tin từ máy tính</p>
                <input 
                  type="file" 
                  accept=".csv, .xlsx, .xls" 
                  style={{ display: 'none' }} 
                  id="excel-file-input" 
                  onChange={handleImportFileChange}
                />
                <label htmlFor="excel-file-input" className="btn-browse-file">Chọn tệp tin</label>
              </div>

              <div className="excel-instructions">
                <h5>Lưu ý định dạng:</h5>
                <ul>
                  <li>Hỗ trợ tệp CSV hoặc bảng tính chuẩn SMAS, VnEdu.</li>
                  <li>Cột dữ liệu: Họ và tên, Vai trò (Student/Teacher), Số điện thoại, Email.</li>
                  <li>Hệ thống sẽ tự động khởi tạo mật khẩu mặc định an toàn và gửi thông báo SMS cho từng người dùng hợp lệ.</li>
                </ul>
              </div>

              <div className="admin-modal-footer">
                <button type="button" className="admin-btn-cancel" onClick={() => setIsImportModalOpen(false)}>
                  Đóng
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* MODAL: Xuất danh sách */}
      {isExportModalOpen && (
        <div className="admin-modal-backdrop" onClick={() => setIsExportModalOpen(false)}>
          <div className="admin-modal-card" onClick={e => e.stopPropagation()}>
            <div className="admin-modal-header">
              <h3 className="admin-modal-title">Xuất danh sách người dùng</h3>
              <button type="button" className="admin-modal-close" onClick={() => setIsExportModalOpen(false)}>
                <X size={20} />
              </button>
            </div>
            <div className="admin-modal-body">
              <p className="admin-modal-desc">
                Tải xuống danh sách toàn bộ <strong>{totalCount}</strong> người dùng hiện tại theo các bộ lọc đang chọn.
              </p>
              <div className="admin-form-group">
                <label className="admin-form-label">Định dạng tập tin xuất</label>
                <div className="export-options-row">
                  <label className="export-option-box">
                    <input type="radio" name="usersExportFormat" defaultChecked />
                    <span>Bảng tính Excel (.csv / UTF-8)</span>
                  </label>
                </div>
              </div>

              <div className="admin-modal-footer">
                <button type="button" className="admin-btn-cancel" onClick={() => setIsExportModalOpen(false)}>
                  Hủy
                </button>
                <button 
                  type="button" 
                  className="admin-btn-primary"
                  onClick={handleExportSubmit}
                >
                  <Download size={16} />
                  <span>Tải xuống</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
