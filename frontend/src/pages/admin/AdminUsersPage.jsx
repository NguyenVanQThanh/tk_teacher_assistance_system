// File Name: AdminUsersPage.jsx
// Description: Comprehensive User Management screen for Admin portal with role filtering, batch selection, search, pagination, and Excel sync.
// Created At: 2026-09-19
// Created By: Tam Khang
// Updated At: 2026-09-19
// Updated By: Tam Khang

import React, { useState, useMemo } from 'react';
import { 
  Download, 
  UserPlus, 
  Search, 
  X, 
  RotateCw, 
  ChevronDown, 
  Eye, 
  EyeOff,
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
  ShieldAlert,
  Trash2,
  GraduationCap,
  Contact,
  Phone,
  Calendar,
  ArrowRight,
  Info,
  Sparkles,
  UserX
} from 'lucide-react';
import './AdminUsersPage.css';

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

  // Modals state
  const [selectedUser, setSelectedUser] = useState(null);
  const [isViewModalOpen, setIsViewModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);
  const [isExportModalOpen, setIsExportModalOpen] = useState(false);
  const [toastMessage, setToastMessage] = useState(null);

  // Deactivate User Modal State (from 3-dots action)
  const [isDeactivateModalOpen, setIsDeactivateModalOpen] = useState(false);
  const [userToDeactivate, setUserToDeactivate] = useState(null);
  const [deactivateReason, setDeactivateReason] = useState('Tạm nghỉ công tác / Nghỉ thai sản');
  const [customDeactivateReason, setCustomDeactivateReason] = useState('');
  const [sendDeactivateEmail, setSendDeactivateEmail] = useState(true);

  // Add User Form State matching the modal design
  const [newUserForm, setNewUserForm] = useState({
    roleType: 'student', // 'student' | 'teacher'
    code: 'HS2024108',
    fullName: '',
    birthDate: '2008-05-18',
    gender: 'Nam',
    phone: '0912 345 678',
    classRoom: 'Lớp 12A1 (Chuyên Toán)',
    academicYear: 'Niên khóa 2024 - 2025 (Hiện tại)',
    parentName: '',
    parentPhone: '0987 654 321',
    department: 'Tổ Toán - Tin',
    qualification: 'Thạc sĩ Sư phạm',
    teacherEmail: '',
    password: 'Password@123',
    showPassword: false,
    isActiveImmediately: true
  });

  const handleAutoGenerateCode = () => {
    const prefix = newUserForm.roleType === 'student' ? 'HS' : 'GV';
    const year = 2024;
    const rand = Math.floor(100 + Math.random() * 900);
    const newCode = `${prefix}${year}${rand}`;
    setNewUserForm(prev => ({ ...prev, code: newCode }));
    showToast(`Đã tự động tạo mã định danh: ${newCode}`);
  };

  const handleRoleTypeChange = (role) => {
    const prefix = role === 'student' ? 'HS' : 'GV';
    const year = 2024;
    const rand = Math.floor(100 + Math.random() * 900);
    setNewUserForm(prev => ({
      ...prev,
      roleType: role,
      code: `${prefix}${year}${rand}`
    }));
  };

  const handleCreateNewUser = (e) => {
    e.preventDefault();
    if (!newUserForm.fullName.trim()) {
      showToast('Vui lòng nhập họ và tên đầy đủ.');
      return;
    }

    const isStudent = newUserForm.roleType === 'student';
    const newUserObj = {
      id: newUserForm.code || `US${Date.now()}`,
      code: newUserForm.code,
      fullName: newUserForm.fullName.trim(),
      email: isStudent 
        ? `${newUserForm.fullName.trim().toLowerCase().replace(/\s+/g, '.')}.${newUserForm.code.toLowerCase()}@student.clarity.edu.vn`
        : `${newUserForm.fullName.trim().toLowerCase().replace(/\s+/g, '.')}@clarity.edu.vn`,
      avatarText: newUserForm.fullName.trim().split(' ').slice(-2).map(w => w[0]).join('').toUpperCase() || (isStudent ? 'HS' : 'GV'),
      avatarBg: isStudent ? '#EDE9FE' : '#F3ECFF',
      avatarColor: isStudent ? '#6D28D9' : '#5B32A8',
      role: isStudent ? 'Học sinh' : 'Giáo viên',
      roleKey: isStudent ? 'student' : 'teacher',
      department: isStudent ? newUserForm.classRoom : newUserForm.department,
      lastLoginRelative: 'Chưa đăng nhập',
      lastLoginDate: 'Chưa hoạt động',
      status: newUserForm.isActiveImmediately ? 'active' : 'pending',
      phone: newUserForm.phone,
      createdAt: '19/09/2024 - 10:00',
      academicYear: '2024 - 2025',
      allAcademicYears: ['2024 - 2025']
    };

    setUsers(prev => [newUserObj, ...prev]);
    setIsAddModalOpen(false);
    showToast(`Đã thêm thành công ${newUserObj.role} "${newUserObj.fullName}" vào hệ thống!`);
    
    setNewUserForm(prev => ({
      ...prev,
      fullName: '',
      parentName: '',
      teacherEmail: ''
    }));
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
  };

  const handleConfirmDeactivate = () => {
    if (!userToDeactivate) return;
    const finalReason = deactivateReason === 'Lý do khác'
      ? (customDeactivateReason.trim() || 'Lý do khác')
      : deactivateReason;

    setUsers(prev => prev.map(u => u.id === userToDeactivate.id ? { ...u, status: 'locked', lockReason: finalReason } : u));
    setIsDeactivateModalOpen(false);
    showToast(`Đã vô hiệu hóa tài khoản của ${userToDeactivate.fullName} thành công (Lý do: ${finalReason}).`);
  };

  // Active user list data matching the screenshot
  const [users, setUsers] = useState([
    {
      id: 'GV2018042',
      code: 'GV2018042',
      fullName: 'ThS. Lê Nguyên',
      email: 'le.nguyen@clarity.edu.vn',
      avatarUrl: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&q=80&w=120',
      role: 'Giáo viên',
      roleKey: 'teacher',
      department: 'Tổ Toán - Tin',
      lastLoginRelative: '10 phút trước',
      lastLoginDate: '14/10/2024 - 10:24',
      status: 'active', // 'active' | 'pending' | 'locked'
      phone: '0912345678',
      createdAt: '15/08/2018 - 08:30',
      academicYear: '2024 - 2025',
      allAcademicYears: ['2020 - 2021', '2021 - 2022', '2022 - 2023', '2023 - 2024', '2024 - 2025']
    },
    {
      id: 'HS2022019',
      code: 'HS2022019',
      fullName: 'Trần Minh Phong',
      email: 'phong.tm22@student.clarity.edu.vn',
      avatarUrl: 'https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?auto=format&fit=crop&q=80&w=120',
      role: 'Học sinh',
      roleKey: 'student',
      department: '12A1',
      lastLoginRelative: 'Hôm nay',
      lastLoginDate: '14/10/2024 - 08:15',
      status: 'active',
      phone: '0987654321',
      createdAt: '05/09/2022 - 07:15',
      academicYear: '2024 - 2025',
      allAcademicYears: ['2022 - 2023', '2023 - 2024', '2024 - 2025']
    },
    {
      id: 'AD2015001',
      code: 'AD2015001',
      fullName: 'Nguyễn Văn A',
      email: 'admin.anv@clarity.edu.vn',
      avatarText: 'NA',
      avatarBg: '#F3ECFF',
      avatarColor: '#5B32A8',
      role: 'Quản trị viên',
      roleKey: 'admin',
      department: 'Phòng CNTT & Dữ liệu',
      lastLoginRelative: 'Vừa xong',
      lastLoginDate: '14/10/2024 - 10:48',
      status: 'active',
      phone: '0999000001',
      createdAt: '01/06/2015 - 08:00',
      academicYear: '2024 - 2025',
      allAcademicYears: ['2021 - 2022', '2022 - 2023', '2023 - 2024', '2024 - 2025']
    },
    {
      id: 'HS2023108',
      code: 'HS2023108',
      fullName: 'Trần Thị Lan',
      email: 'lan.tt23@student.clarity.edu.vn',
      avatarUrl: 'https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&q=80&w=120',
      role: 'Học sinh',
      roleKey: 'student',
      department: '10A3',
      lastLoginRelative: 'Hôm qua',
      lastLoginDate: '13/10/2024 - 16:40',
      status: 'pending',
      phone: '0933112233',
      createdAt: '25/08/2023 - 10:20',
      academicYear: '2024 - 2025',
      allAcademicYears: ['2023 - 2024', '2024 - 2025']
    },
    {
      id: 'GV2016021',
      code: 'GV2016021',
      fullName: 'Lê Phương Duy',
      email: 'duy.lp@clarity.edu.vn',
      avatarText: 'PD',
      avatarBg: '#EDE9FE',
      avatarColor: '#6D28D9',
      role: 'Giáo viên',
      roleKey: 'teacher',
      department: 'Tổ Ngoại ngữ',
      lastLoginRelative: '3 ngày trước',
      lastLoginDate: '11/10/2024 - 09:12',
      status: 'active',
      phone: '0944556677',
      createdAt: '12/08/2016 - 14:10',
      academicYear: '2024 - 2025',
      allAcademicYears: ['2021 - 2022', '2022 - 2023', '2023 - 2024', '2024 - 2025']
    },
    {
      id: 'HS2022412',
      code: 'HS2022412',
      fullName: 'Vũ Hoàng Gia Bảo',
      email: 'bao.vhg22@student.clarity.edu.vn',
      avatarUrl: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&q=80&w=120',
      role: 'Học sinh',
      roleKey: 'student',
      department: '11A4',
      lastLoginRelative: '2 tuần trước',
      lastLoginDate: '28/09/2024 - 14:02',
      status: 'locked',
      phone: '0977889900',
      createdAt: '02/09/2022 - 11:05',
      academicYear: '2024 - 2025',
      allAcademicYears: ['2022 - 2023', '2023 - 2024', '2024 - 2025']
    },
    {
      id: 'NV2019005',
      code: 'NV2019005',
      fullName: 'Hoàng Mỹ Dung',
      email: 'dung.hm@clarity.edu.vn',
      avatarText: 'HD',
      avatarBg: '#F5F3FF',
      avatarColor: '#4C1D95',
      role: 'Giáo vụ',
      roleKey: 'staff',
      department: 'Phòng Khảo thí & ĐBCL',
      lastLoginRelative: 'Hôm nay',
      lastLoginDate: '14/10/2024 - 07:30',
      status: 'active',
      phone: '0901234567',
      createdAt: '18/09/2019 - 09:00',
      academicYear: '2024 - 2025',
      allAcademicYears: ['2022 - 2023', '2023 - 2024', '2024 - 2025']
    },
    {
      id: 'HS2022301',
      code: 'HS2022301',
      fullName: 'Đỗ Minh Trí',
      email: 'tri.dm22@student.clarity.edu.vn',
      avatarUrl: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&q=80&w=120',
      role: 'Học sinh',
      roleKey: 'student',
      department: '11A2',
      lastLoginRelative: 'Hôm nay',
      lastLoginDate: '14/10/2024 - 09:40',
      status: 'active',
      phone: '0918765432',
      createdAt: '05/09/2022 - 08:00',
      academicYear: '2024 - 2025',
      allAcademicYears: ['2022 - 2023', '2023 - 2024', '2024 - 2025']
    },
    {
      id: 'GV2017015',
      code: 'GV2017015',
      fullName: 'ThS. Phạm Thanh Hà',
      email: 'ha.pt@clarity.edu.vn',
      avatarText: 'TH',
      avatarBg: '#FCE7F3',
      avatarColor: '#BE185D',
      role: 'Giáo viên',
      roleKey: 'teacher',
      department: 'Tổ Ngữ văn',
      lastLoginRelative: '2 ngày trước',
      lastLoginDate: '12/10/2024 - 15:20',
      status: 'active',
      phone: '0922334455',
      createdAt: '10/08/2017 - 10:15',
      academicYear: '2024 - 2025',
      allAcademicYears: ['2021 - 2022', '2022 - 2023', '2023 - 2024', '2024 - 2025']
    },
    {
      id: 'HS2023055',
      code: 'HS2023055',
      fullName: 'Ngô Bảo Châu',
      email: 'chau.nb23@student.clarity.edu.vn',
      avatarText: 'BC',
      avatarBg: '#FEF3C7',
      avatarColor: '#B45309',
      role: 'Học sinh',
      roleKey: 'student',
      department: '10A1',
      lastLoginRelative: '4 ngày trước',
      lastLoginDate: '10/10/2024 - 11:30',
      status: 'pending',
      phone: '0966778899',
      createdAt: '28/08/2023 - 14:00',
      academicYear: '2024 - 2025',
      allAcademicYears: ['2023 - 2024', '2024 - 2025']
    }
  ]);

  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => {
      setToastMessage(null);
    }, 3500);
  };

  // Filtered users calculation
  const filteredUsers = useMemo(() => {
    return users.filter(user => {
      // Tab filter
      if (activeTab === 'students' && user.roleKey !== 'student') return false;
      if (activeTab === 'teachers' && user.roleKey !== 'teacher') return false;
      if (activeTab === 'pending' && user.status !== 'pending' && user.status !== 'locked') return false;

      // Status dropdown filter
      if (statusFilter !== 'all') {
        if (statusFilter === 'active' && user.status !== 'active') return false;
        if (statusFilter === 'pending' && user.status !== 'pending') return false;
        if (statusFilter === 'locked' && user.status !== 'locked') return false;
      }

      // Grade dropdown filter
      if (gradeFilter !== 'all') {
        if (gradeFilter === 'k10' && !user.department.includes('10')) return false;
        if (gradeFilter === 'k11' && !user.department.includes('11')) return false;
        if (gradeFilter === 'k12' && !user.department.includes('12')) return false;
      }

      // Department dropdown filter
      if (deptFilter !== 'all' && !user.department.toLowerCase().includes(deptFilter.toLowerCase())) {
        return false;
      }

      // Search query filter
      if (searchQuery.trim()) {
        const query = searchQuery.trim().toLowerCase();
        const matchCode = user.code.toLowerCase().includes(query);
        const matchName = user.fullName.toLowerCase().includes(query);
        const matchEmail = user.email.toLowerCase().includes(query);
        const matchDept = user.department.toLowerCase().includes(query);
        if (!matchCode && !matchName && !matchEmail && !matchDept) return false;
      }

      return true;
    });
  }, [users, activeTab, statusFilter, gradeFilter, deptFilter, searchQuery]);

  // Paginated users calculation (max 10 rows per page by default)
  const paginatedUsers = useMemo(() => {
    const startIndex = (currentPage - 1) * pageSize;
    return filteredUsers.slice(startIndex, startIndex + pageSize);
  }, [filteredUsers, currentPage, pageSize]);

  // Selection handlers
  const handleSelectAll = (e) => {
    if (e.target.checked) {
      setSelectedIds(filteredUsers.map(u => u.id));
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

  // Toggle user active / locked (Soft state update)
  const handleToggleLockUser = (user) => {
    const newStatus = user.status === 'locked' ? 'active' : 'locked';
    setUsers(prev => prev.map(u => u.id === user.id ? { ...u, status: newStatus } : u));
    showToast(newStatus === 'locked' ? `Đã tạm khóa tài khoản ${user.fullName}.` : `Đã mở khóa tài khoản ${user.fullName}.`);
  };

  // Soft delete user (updates status to 'locked')
  const handleSoftDeleteUser = (user) => {
    if (window.confirm(`Bạn có chắc chắn muốn vô hiệu hóa tài khoản ${user.fullName}?`)) {
      setUsers(prev => prev.map(u => u.id === user.id ? { ...u, status: 'locked' } : u));
      showToast(`Đã chuyển tài khoản ${user.fullName} sang trạng thái Tạm khóa (Soft Delete).`);
    }
  };

  const handleResetFilters = () => {
    setSearchQuery('');
    setGradeFilter('all');
    setDeptFilter('all');
    setStatusFilter('all');
    setActiveTab('all');
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
            onClick={() => setActiveTab('all')}
          >
            Tất cả (2,578)
          </button>
          <button 
            type="button" 
            className={`users-tab-pill ${activeTab === 'students' ? 'active' : ''}`}
            onClick={() => setActiveTab('students')}
          >
            Học sinh (2,450)
          </button>
          <button 
            type="button" 
            className={`users-tab-pill ${activeTab === 'teachers' ? 'active' : ''}`}
            onClick={() => setActiveTab('teachers')}
          >
            Giáo viên (112)
          </button>
          <button 
            type="button" 
            className={`users-tab-pill ${activeTab === 'pending' ? 'active' : ''}`}
            onClick={() => setActiveTab('pending')}
          >
            Chờ kích hoạt / Khóa (18)
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
              placeholder="Tìm theo tên, mã hoặc email..." 
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
            />
            {searchQuery && (
              <button 
                type="button" 
                className="filter-search-clear"
                onClick={() => setSearchQuery('')}
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
              onChange={e => setGradeFilter(e.target.value)}
            >
              <option value="all">Tất cả khối lớp</option>
              <option value="k10">Khối 10</option>
              <option value="k11">Khối 11</option>
              <option value="k12">Khối 12</option>
            </select>
            <ChevronDown size={14} className="filter-select-arrow" />
          </div>

          {/* Department Dropdown */}
          <div className="filter-select-wrapper">
            <select 
              className="filter-select"
              value={deptFilter}
              onChange={e => setDeptFilter(e.target.value)}
            >
              <option value="all">Tất cả bộ môn</option>
              <option value="Toán">Tổ Toán - Tin</option>
              <option value="Ngoại ngữ">Tổ Ngoại ngữ</option>
              <option value="Ngữ văn">Tổ Ngữ văn</option>
              <option value="Vật lý">Tổ Vật lý</option>
              <option value="CNTT">Phòng CNTT & Dữ liệu</option>
              <option value="Khảo thí">Phòng Khảo thí & ĐBCL</option>
            </select>
            <ChevronDown size={14} className="filter-select-arrow" />
          </div>

          {/* Status Dropdown */}
          <div className="filter-select-wrapper">
            <select 
              className="filter-select"
              value={statusFilter}
              onChange={e => setStatusFilter(e.target.value)}
            >
              <option value="all">Tất cả trạng thái</option>
              <option value="active">Hoạt động</option>
              <option value="pending">Chờ duyệt</option>
              <option value="locked">Tạm khóa</option>
            </select>
            <ChevronDown size={14} className="filter-select-arrow" />
          </div>

          {/* Reset Filters Icon Button */}
          <button 
            type="button" 
            className="filter-btn-reset" 
            title="Đặt lại bộ lọc"
            onClick={handleResetFilters}
          >
            <RotateCw size={15} />
          </button>
        </div>
      </section>

      {/* 4. Active Filters Tag Row */}
      {filterTags.length > 0 && (
        <section className="users-active-tags-row">
          <span className="tags-label">Đang lọc theo:</span>
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

      {/* 5. User Data Table */}
      <section className="users-table-card">
        <div className="users-table-scroll-wrapper">
          <table className="users-table">
            <thead>
              <tr>
                <th className="col-checkbox">
                  <input 
                    type="checkbox" 
                    className="custom-table-checkbox"
                    checked={filteredUsers.length > 0 && selectedIds.length === filteredUsers.length}
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
              {filteredUsers.length === 0 ? (
                <tr>
                  <td colSpan="8" className="empty-table-cell">
                    <AlertCircle size={28} className="empty-icon" />
                    <p>Không tìm thấy người dùng nào phù hợp với bộ lọc.</p>
                  </td>
                </tr>
              ) : (
                paginatedUsers.map(user => {
                  const isSelected = selectedIds.includes(user.id);
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

                      {/* User Avatar + Name + Email */}
                      <td className="col-user">
                        <div className="table-user-block">
                          {user.avatarUrl ? (
                            <img src={user.avatarUrl} alt={user.fullName} className="user-avatar-img" />
                          ) : (
                            <div 
                              className="user-avatar-badge" 
                              style={{ backgroundColor: user.avatarBg, color: user.avatarColor }}
                            >
                              {user.avatarText}
                            </div>
                          )}
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
                            <span className="user-email-text">{user.email}</span>
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
                        {user.roleKey === 'staff' && (
                          <span className="role-pill staff">Giáo vụ</span>
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
                        {user.status === 'pending' && (
                          <span className="user-status-pill pending">
                            <span className="status-dot amber"></span>
                            Chờ duyệt
                          </span>
                        )}
                        {user.status === 'locked' && (
                          <span className="user-status-pill locked">
                            <span className="status-dot purple"></span>
                            Tạm khóa
                          </span>
                        )}
                      </td>

                      {/* Action Icons */}
                      <td className="col-actions text-right">
                        <div className="table-row-actions">
                          {/* View details */}
                          <button 
                            type="button" 
                            className="table-action-icon-btn" 
                            title="Xem chi tiết hồ sơ"
                            onClick={() => {
                              setSelectedUser(user);
                              setIsViewModalOpen(true);
                            }}
                          >
                            <Eye size={17} />
                          </button>

                          {/* Edit user */}
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

                          {/* Quick lock / unlock */}
                          <button 
                            type="button" 
                            className={`table-action-icon-btn ${user.status === 'locked' ? 'text-locked' : ''}`}
                            title={user.status === 'locked' ? 'Mở khóa tài khoản' : 'Tạm khóa tài khoản'}
                            onClick={() => handleToggleLockUser(user)}
                          >
                            {user.status === 'locked' ? <Lock size={16} /> : <Unlock size={16} />}
                          </button>

                          {/* More options / Ba chấm: Vô hiệu hóa tài khoản */}
                          <button 
                            type="button" 
                            className="table-action-icon-btn" 
                            title="Tùy chọn khác / Vô hiệu hóa tài khoản"
                            onClick={() => handleOpenDeactivateModal(user)}
                          >
                            <MoreVertical size={16} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* 6. Pagination Footer */}
        <div className="users-pagination-footer">
          <div className="pagination-info">
            Hiển thị <strong>{filteredUsers.length === 0 ? 0 : (currentPage - 1) * pageSize + 1}-{Math.min(currentPage * pageSize, filteredUsers.length)}</strong> trong số <strong>2,578</strong> người dùng
          </div>

          <div className="pagination-controls">
            <div className="pagination-page-size-selector">
              <span>Hàng trên trang:</span>
              <select 
                value={pageSize}
                onChange={e => setPageSize(Number(e.target.value))}
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
                disabled={currentPage === 1}
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
              >
                <ChevronLeft size={16} />
              </button>
              <button type="button" className="page-num-btn active">1</button>
              <button type="button" className="page-num-btn">2</button>
              <button type="button" className="page-num-btn">3</button>
              <span className="page-num-ellipsis">...</span>
              <button type="button" className="page-num-btn">258</button>
              <button 
                type="button" 
                className="page-nav-btn"
                onClick={() => setCurrentPage(p => p + 1)}
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
              Hệ thống hỗ trợ nhập liệu hàng loạt qua file Excel (SMAS/VnEdu) với mẫu chuẩn hóa.
            </p>
          </div>
        </div>

        <div className="sync-banner-actions">
          <button 
            type="button" 
            className="btn-sync-download-template"
            onClick={() => showToast('Đang tải tập tin mẫu Excel (SMAS/VnEdu)...')}
          >
            Tải file mẫu Excel
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
                <div className="user-detail-avatar-large">
                  {selectedUser.avatarUrl ? (
                    <img src={selectedUser.avatarUrl} alt={selectedUser.fullName} />
                  ) : (
                    <div 
                      className="user-avatar-badge-large"
                      style={{ backgroundColor: selectedUser.avatarBg, color: selectedUser.avatarColor }}
                    >
                      {selectedUser.avatarText}
                    </div>
                  )}
                </div>
                <div className="user-detail-header-meta">
                  <h3>{selectedUser.fullName}</h3>
                  <p>{selectedUser.email}</p>
                  <span className={`role-pill ${selectedUser.roleKey}`}>{selectedUser.role}</span>
                </div>
              </div>

              <div className="user-detail-info-grid">
                <div className="info-item">
                  <span className="info-label">Mã định danh:</span>
                  <span className="info-value font-mono">{selectedUser.code}</span>
                </div>
                <div className="info-item">
                  <span className="info-label">Lớp / Bộ môn:</span>
                  <span className="info-value">{selectedUser.department}</span>
                </div>
                <div className="info-item">
                  <span className="info-label">Số điện thoại:</span>
                  <span className="info-value">{selectedUser.phone || 'Chưa cập nhật'}</span>
                </div>
                <div className="info-item">
                  <span className="info-label">Trạng thái:</span>
                  <span className={`user-status-pill ${selectedUser.status}`}>
                    {selectedUser.status === 'active' ? 'Hoạt động' : selectedUser.status === 'pending' ? 'Chờ duyệt' : 'Tạm khóa'}
                  </span>
                </div>
                <div className="info-item">
                  <span className="info-label">Ngày tạo tài khoản:</span>
                  <span className="info-value font-medium">{selectedUser.createdAt || '15/08/2021 - 08:30'}</span>
                </div>
                <div className="info-item">
                  <span className="info-label">Đăng nhập gần nhất:</span>
                  <span className="info-value">{selectedUser.lastLoginDate}</span>
                </div>
                <div className="info-item">
                  <span className="info-label">Niên khóa hiện tại:</span>
                  <div className="current-academic-year-box">
                    <span className="info-value font-bold text-purple">{selectedUser.academicYear || '2024 - 2025'}</span>
                    <span className="current-year-badge">Hiện tại</span>
                  </div>
                </div>
                <div className="info-item col-span-2">
                  <span className="info-label">Tất cả niên khóa:</span>
                  <div className="academic-years-pill-list">
                    {(selectedUser.allAcademicYears || [selectedUser.academicYear || '2024 - 2025']).map(year => {
                      const isCurrent = year === (selectedUser.academicYear || '2024 - 2025');
                      return (
                        <span 
                          key={year} 
                          className={`academic-year-tag ${isCurrent ? 'current' : ''}`}
                        >
                          {year}
                          {isCurrent && <span className="year-dot"></span>}
                        </span>
                      );
                    })}
                  </div>
                </div>
              </div>

              <div className="admin-modal-footer">
                <button 
                  type="button" 
                  className="admin-btn-cancel" 
                  onClick={() => setIsViewModalOpen(false)}
                >
                  Đóng
                </button>
                <button 
                  type="button" 
                  className="admin-btn-primary"
                  onClick={() => {
                    setIsViewModalOpen(false);
                    setIsEditModalOpen(true);
                  }}
                >
                  <Edit2 size={15} />
                  <span>Chỉnh sửa</span>
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
              <h3 className="admin-modal-title">Chỉnh sửa thông tin: {selectedUser.fullName}</h3>
              <button type="button" className="admin-modal-close" onClick={() => setIsEditModalOpen(false)}>
                <X size={20} />
              </button>
            </div>
            <form onSubmit={e => {
              e.preventDefault();
              setIsEditModalOpen(false);
              showToast(`Đã lưu thay đổi cho người dùng ${selectedUser.fullName}!`);
            }} className="admin-modal-body">
              <div className="admin-form-group">
                <label className="admin-form-label">Họ và tên *</label>
                <input 
                  type="text" 
                  className="admin-form-input" 
                  value={selectedUser.fullName}
                  onChange={e => setSelectedUser(p => ({ ...p, fullName: e.target.value }))}
                  required 
                />
              </div>

              <div className="admin-form-group">
                <label className="admin-form-label">Email trường *</label>
                <input 
                  type="email" 
                  className="admin-form-input" 
                  value={selectedUser.email}
                  onChange={e => setSelectedUser(p => ({ ...p, email: e.target.value }))}
                  required 
                />
              </div>

              <div className="admin-form-row">
                <div className="admin-form-group flex-1">
                  <label className="admin-form-label">Lớp / Bộ môn</label>
                  <input 
                    type="text" 
                    className="admin-form-input" 
                    value={selectedUser.department}
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
                    <option value="active">Hoạt động</option>
                    <option value="pending">Chờ duyệt</option>
                    <option value="locked">Tạm khóa</option>
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

      {/* MODAL: Thêm người dùng mới (Matching reference design) */}
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
                  {/* Mã định danh */}
                  <div className="admin-form-group">
                    <div className="form-label-with-action">
                      <label className="admin-form-label">Mã định danh *</label>
                      <button 
                        type="button" 
                        className="btn-auto-generate"
                        onClick={handleAutoGenerateCode}
                      >
                        Tạo tự động
                      </button>
                    </div>
                    <div className="input-with-icon-right">
                      <input 
                        type="text" 
                        className="admin-form-input input-highlight-code"
                        value={newUserForm.code}
                        onChange={e => setNewUserForm(p => ({ ...p, code: e.target.value }))}
                        required 
                      />
                      <span className="input-right-icon text-success">
                        <CheckCircle2 size={16} />
                      </span>
                    </div>
                  </div>

                  {/* Họ và tên đầy đủ */}
                  <div className="admin-form-group">
                    <label className="admin-form-label">Họ và tên đầy đủ *</label>
                    <input 
                      type="text" 
                      className="admin-form-input" 
                      placeholder="Ví dụ: Nguyễn Văn Hoàng"
                      value={newUserForm.fullName}
                      onChange={e => setNewUserForm(p => ({ ...p, fullName: e.target.value }))}
                      required 
                    />
                  </div>

                  {/* Ngày sinh & Giới tính */}
                  <div className="admin-form-row">
                    <div className="admin-form-group flex-1">
                      <label className="admin-form-label">Ngày sinh</label>
                      <div className="input-with-icon-right">
                        <input 
                          type="text" 
                          className="admin-form-input" 
                          placeholder="MM/DD/YYYY"
                          value={newUserForm.birthDate}
                          onChange={e => setNewUserForm(p => ({ ...p, birthDate: e.target.value }))}
                        />
                        <span className="input-right-icon text-muted">
                          <Calendar size={15} />
                        </span>
                      </div>
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

                  {/* Số điện thoại người dùng */}
                  <div className="admin-form-group">
                    <label className="admin-form-label">
                      {newUserForm.roleType === 'student' ? 'Số điện thoại học sinh (Đăng nhập)' : 'Số điện thoại giáo viên (Đăng nhập)'}
                    </label>
                    <div className="input-with-icon-left">
                      <span className="input-left-icon">
                        <Phone size={15} />
                      </span>
                      <input 
                        type="text" 
                        className="admin-form-input" 
                        placeholder="0912 345 678"
                        value={newUserForm.phone}
                        onChange={e => setNewUserForm(p => ({ ...p, phone: e.target.value }))}
                      />
                    </div>
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
                        onChange={e => setNewUserForm(p => ({ ...p, parentName: e.target.value }))}
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

                  {/* SĐT phụ huynh / Email công vụ */}
                  <div className="admin-form-group">
                    <label className="admin-form-label">
                      {newUserForm.roleType === 'student' ? 'Số điện thoại phụ huynh / Người giám hộ' : 'Email công vụ'}
                    </label>
                    <div className="input-with-icon-left">
                      <span className="input-left-icon">
                        {newUserForm.roleType === 'student' ? <Contact size={15} /> : <Phone size={15} />}
                      </span>
                      <input 
                        type="text" 
                        className="admin-form-input" 
                        placeholder={newUserForm.roleType === 'student' ? "0987 654 321" : "giaovien@clarity.edu.vn"}
                        value={newUserForm.parentPhone}
                        onChange={e => setNewUserForm(p => ({ ...p, parentPhone: e.target.value }))}
                      />
                    </div>
                  </div>

                  {/* Mật khẩu khởi tạo */}
                  <div className="admin-form-group">
                    <label className="admin-form-label">Mật khẩu khởi tạo</label>
                    <div className="input-with-icon-right">
                      <input 
                        type={newUserForm.showPassword ? "text" : "password"}
                        className="admin-form-input font-mono" 
                        value={newUserForm.password}
                        onChange={e => setNewUserForm(p => ({ ...p, password: e.target.value }))}
                      />
                      <button 
                        type="button" 
                        className="input-right-btn"
                        onClick={() => setNewUserForm(p => ({ ...p, showPassword: !p.showPassword }))}
                        title={newUserForm.showPassword ? "Ẩn mật khẩu" : "Hiện mật khẩu"}
                      >
                        {newUserForm.showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                      </button>
                    </div>
                    <span className="input-helper-text">
                      Mật khẩu mặc định hoặc hệ thống sẽ gửi mật mã qua email.
                    </span>
                  </div>

                  {/* Kích hoạt ngay checkbox */}
                  <div className="admin-form-checkbox-row">
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

      {/* MODAL: Vô hiệu hóa tài khoản (Triggered by 3 dots filter / action) */}
      {isDeactivateModalOpen && userToDeactivate && (
        <div className="admin-modal-backdrop" onClick={() => setIsDeactivateModalOpen(false)}>
          <div className="admin-modal-card modal-deactivate-user" onClick={e => e.stopPropagation()}>
            {/* Close button */}
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
              {/* Top Warning Icon */}
              <div className="deactivate-icon-wrapper">
                <div className="deactivate-icon-circle">
                  <UserX size={26} strokeWidth={2.2} />
                </div>
              </div>

              {/* Title & Description */}
              <h3 className="deactivate-modal-title">Vô hiệu hóa tài khoản?</h3>
              <p className="deactivate-modal-desc">
                Bạn có chắc chắn muốn vô hiệu hóa tài khoản của <strong>{userToDeactivate.fullName}</strong> (<strong>{userToDeactivate.code}</strong>)? Người dùng này sẽ tạm thời không thể đăng nhập vào LMS và truy cập các lớp giảng dạy.
              </p>

              {/* User Preview Capsule */}
              <div className="deactivate-user-preview">
                <div className="preview-user-avatar">
                  {userToDeactivate.avatarUrl ? (
                    <img src={userToDeactivate.avatarUrl} alt={userToDeactivate.fullName} />
                  ) : (
                    <div 
                      className="preview-avatar-badge"
                      style={{ backgroundColor: userToDeactivate.avatarBg, color: userToDeactivate.avatarColor }}
                    >
                      {userToDeactivate.avatarText}
                    </div>
                  )}
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

              {/* Form Group: Reason */}
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

              {/* Conditional custom reason input when 'Lý do khác' is selected */}
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

              {/* Checkbox: Send email */}
              <div className="admin-form-checkbox-row deactivate-checkbox-row">
                <label className="custom-checkbox-label">
                  <input 
                    type="checkbox" 
                    checked={sendDeactivateEmail}
                    onChange={e => setSendDeactivateEmail(e.target.checked)}
                    className="custom-checkbox-input"
                  />
                  <span className="checkbox-text">
                    Gửi email thông báo tự động tới {userToDeactivate.roleKey === 'teacher' ? 'giảng viên' : 'học sinh'}
                  </span>
                </label>
              </div>

              {/* Footer Actions */}
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

      {/* MODAL: Nhập Excel */}
      {isImportModalOpen && (
        <div className="admin-modal-backdrop" onClick={() => setIsImportModalOpen(false)}>
          <div className="admin-modal-card modal-lg" onClick={e => e.stopPropagation()}>
            <div className="admin-modal-header">
              <h3 className="admin-modal-title">Nhập danh sách người dùng từ Excel</h3>
              <button type="button" className="admin-modal-close" onClick={() => setIsImportModalOpen(false)}>
                <X size={20} />
              </button>
            </div>
            <div className="admin-modal-body">
              <div className="excel-dropzone">
                <FileSpreadsheet size={42} className="excel-dropzone-icon" />
                <h4>Kéo thả tập tin Excel (.xlsx, .xls) vào đây</h4>
                <p>hoặc nhấn để chọn tệp tin từ máy tính</p>
                <input type="file" accept=".xlsx, .xls" style={{ display: 'none' }} id="excel-file-input" />
                <label htmlFor="excel-file-input" className="btn-browse-file">Chọn tệp tin</label>
              </div>

              <div className="excel-instructions">
                <h5>Lưu ý định dạng:</h5>
                <ul>
                  <li>Chỉ hỗ trợ tệp định dạng chuẩn SMAS, VnEdu hoặc mẫu của SmartLMS.</li>
                  <li>Dữ liệu bắt buộc: Mã định danh, Họ và tên, Email, Vai trò, Lớp/Bộ môn.</li>
                </ul>
              </div>

              <div className="admin-modal-footer">
                <button type="button" className="admin-btn-cancel" onClick={() => setIsImportModalOpen(false)}>
                  Đóng
                </button>
                <button 
                  type="button" 
                  className="admin-btn-primary"
                  onClick={() => {
                    setIsImportModalOpen(false);
                    showToast('Đang xử lý dữ liệu nhập từ Excel (25 học sinh mới được thêm)...');
                  }}
                >
                  Tiến hành nhập dữ liệu
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
                Tải xuống danh sách toàn bộ {filteredUsers.length} người dùng đang được hiển thị theo bộ lọc.
              </p>
              <div className="admin-form-group">
                <label className="admin-form-label">Định dạng tập tin</label>
                <div className="export-options-row">
                  <label className="export-option-box">
                    <input type="radio" name="usersExportFormat" defaultChecked />
                    <span>Bảng tính Excel (.xlsx)</span>
                  </label>
                  <label className="export-option-box">
                    <input type="radio" name="usersExportFormat" />
                    <span>Tệp CSV (.csv)</span>
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
                  onClick={() => {
                    setIsExportModalOpen(false);
                    showToast('Đang tải xuống tệp danh sách người dùng...');
                  }}
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
