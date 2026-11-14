// File Name: AdminRolesPage.jsx
// Description: Comprehensive Roles & Permissions management screen for Admin portal with master-detail layout, module grouping, and interactive toggle matrix.
// Created At: 2026-09-19
// Created By: Tam Khang
// Updated At: 2026-11-14
// Updated By: Tam Khang

import React, { useState, useEffect, useCallback } from 'react';
import { 
  ShieldCheck, 
  Shield, 
  Key, 
  Users, 
  Download, 
  Plus, 
  UserCheck, 
  CheckCircle2, 
  BookOpen, 
  FileText, 
  UserPlus, 
  Save, 
  X, 
  GraduationCap
} from 'lucide-react';
import { adminRolesApi, adminUsersApi } from '../../services/api';
import './AdminRolesPage.css';

const ROLE_VISUAL_MAP = {
  admin: {
    nameVi: 'Quản trị viên',
    descriptionVi: 'Toàn quyền quản trị hệ thống',
    icon: Shield,
    iconBg: '#F3ECFF',
    iconColor: '#4D308D',
  },
  head_teacher: {
    nameVi: 'Tổ trưởng chuyên môn',
    descriptionVi: 'Duyệt giáo án, giám sát bộ môn',
    icon: ShieldCheck,
    iconBg: '#EDE9FE',
    iconColor: '#6D28D9',
  },
  subject_teacher: {
    nameVi: 'Giáo viên bộ môn',
    descriptionVi: 'Lớp phụ trách, Chấm bài & Soạn đề',
    icon: UserCheck,
    iconBg: '#F3ECFF',
    iconColor: '#4D308D',
  },
  academic_staff: {
    nameVi: 'Giáo vụ đào tạo',
    descriptionVi: 'Hồ sơ học sinh & Điểm danh lớp',
    icon: BookOpen,
    iconBg: '#FEF3C7',
    iconColor: '#D97706',
  },
  student_parent: {
    nameVi: 'Học sinh & Phụ huynh',
    descriptionVi: 'Học tập trực tuyến, Nộp bài tập',
    icon: GraduationCap,
    iconBg: '#E6F8EE',
    iconColor: '#059669',
  },
};

const FALLBACK_ROLES = [
  {
    id: 'admin',
    code: 'admin',
    name: 'Quản trị viên',
    description: 'Toàn quyền quản trị hệ thống',
    memberCount: 16,
    icon: Shield,
    iconBg: '#F3ECFF',
    iconColor: '#4D308D',
    status: 'active',
    isSystem: true,
  },
  {
    id: 'head_teacher',
    code: 'head_teacher',
    name: 'Tổ trưởng chuyên môn',
    description: 'Duyệt giáo án, giám sát bộ môn',
    memberCount: 14,
    icon: ShieldCheck,
    iconBg: '#EDE9FE',
    iconColor: '#6D28D9',
    status: 'active',
    isSystem: true,
  },
  {
    id: 'subject_teacher',
    code: 'subject_teacher',
    name: 'Giáo viên bộ môn',
    description: 'Lớp phụ trách, Chấm bài & Soạn đề',
    memberCount: 112,
    icon: UserCheck,
    iconBg: '#F3ECFF',
    iconColor: '#4D308D',
    status: 'active',
    isSystem: true,
  },
  {
    id: 'academic_staff',
    code: 'academic_staff',
    name: 'Giáo vụ đào tạo',
    description: 'Hồ sơ học sinh & Điểm danh lớp',
    memberCount: 6,
    icon: BookOpen,
    iconBg: '#FEF3C7',
    iconColor: '#D97706',
    status: 'active',
    isSystem: true,
  },
  {
    id: 'student_parent',
    code: 'student_parent',
    name: 'Học sinh & Phụ huynh',
    description: 'Học tập trực tuyến, Nộp bài tập',
    memberCount: 2450,
    icon: GraduationCap,
    iconBg: '#E6F8EE',
    iconColor: '#059669',
    status: 'active',
    isSystem: true,
  },
];

const FALLBACK_PERMISSIONS = {
  subject_teacher: {
    view_schedule: true,
    create_class: false,
    assign_teaching: false,
    ai_exercise: true,
    auto_grade: true,
    publish_exam: true,
    edit_score_closed: false,
    view_students: true,
    edit_transcript: false,
  },
  admin: {
    view_schedule: true,
    create_class: true,
    assign_teaching: true,
    ai_exercise: true,
    auto_grade: true,
    publish_exam: true,
    edit_score_closed: true,
    view_students: true,
    edit_transcript: true,
  },
  head_teacher: {
    view_schedule: true,
    create_class: false,
    assign_teaching: true,
    ai_exercise: true,
    auto_grade: true,
    publish_exam: true,
    edit_score_closed: true,
    view_students: true,
    edit_transcript: false,
  },
  academic_staff: {
    view_schedule: true,
    create_class: true,
    assign_teaching: false,
    ai_exercise: false,
    auto_grade: false,
    publish_exam: false,
    edit_score_closed: false,
    view_students: true,
    edit_transcript: true,
  },
  student_parent: {
    view_schedule: true,
    create_class: false,
    assign_teaching: false,
    ai_exercise: false,
    auto_grade: false,
    publish_exam: false,
    edit_score_closed: false,
    view_students: false,
    edit_transcript: false,
  },
};

const mapApiRoleToUi = (roleDto) => {
  const code = roleDto.code || roleDto.id;
  const visual = ROLE_VISUAL_MAP[code];
  const isSystem = Boolean(roleDto.isSystem || visual);
  return {
    id: code,
    code,
    roleId: roleDto.role_id || null,
    name: isSystem && visual ? visual.nameVi : (roleDto.name || code),
    description: isSystem && visual
      ? visual.descriptionVi
      : (roleDto.description || 'Vai trò tùy chỉnh hệ thống'),
    memberCount: typeof roleDto.memberCount === 'number' ? roleDto.memberCount : 0,
    icon: visual?.icon || Key,
    iconBg: visual?.iconBg || '#F3ECFF',
    iconColor: visual?.iconColor || '#4D308D',
    status: 'active',
    isSystem,
  };
};

const getInitials = (fullName) => {
  if (!fullName) return 'ND';
  const parts = String(fullName).trim().split(/\s+/);
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase();
};

const formatMemberStatus = (status) => {
  const normalized = String(status || 'ACTIVE').toUpperCase();
  if (normalized === 'ACTIVE') return 'Đang hoạt động';
  if (normalized === 'INACTIVE') return 'Chờ kích hoạt';
  if (normalized === 'SUSPENDED') return 'Tạm khóa';
  return normalized;
};

const triggerBlobDownload = (blobData, filename, mimeType) => {
  const blob = blobData instanceof Blob ? blobData : new Blob([blobData], { type: mimeType });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
};

export default function AdminRolesPage() {
  const [activeRoleId, setActiveRoleId] = useState('subject_teacher');
  const [toastMessage, setToastMessage] = useState(null);

  // Modals state
  const [isAddRoleModalOpen, setIsAddRoleModalOpen] = useState(false);
  const [isAddUserModalOpen, setIsAddUserModalOpen] = useState(false);
  const [isViewMembersModalOpen, setIsViewMembersModalOpen] = useState(false);
  const [isExportModalOpen, setIsExportModalOpen] = useState(false);

  // Async action states
  const [isSaving, setIsSaving] = useState(false);
  const [isCreatingRole, setIsCreatingRole] = useState(false);
  const [isAssigningUser, setIsAssigningUser] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [exportFormat, setExportFormat] = useState('json');

  // Role members and assignable users state
  const [roleMembers, setRoleMembers] = useState([]);
  const [isLoadingMembers, setIsLoadingMembers] = useState(false);
  const [systemUsers, setSystemUsers] = useState([]);
  const [isLoadingUsers, setIsLoadingUsers] = useState(false);

  // New role form state
  const [newRole, setNewRole] = useState({
    name: '',
    code: '',
    description: '',
    cloneFrom: 'subject_teacher',
  });

  const [newUserToAssign, setNewUserToAssign] = useState('');

  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => {
      setToastMessage(null);
    }, 3500);
  };

  // Roles list with initial fallback so UI renders immediately
  const [roles, setRoles] = useState(FALLBACK_ROLES);

  // Permission groups with permissions state for the currently active role
  const [permissionsState, setPermissionsState] = useState(FALLBACK_PERMISSIONS);

  const fetchRoles = useCallback(async () => {
    try {
      const res = await adminRolesApi.getRoles();
      if (res && Array.isArray(res.roles) && res.roles.length > 0) {
        const mappedRoles = res.roles.map(mapApiRoleToUi);
        setRoles(mappedRoles);
        setActiveRoleId((prev) =>
          mappedRoles.some((r) => r.id === prev) ? prev : mappedRoles[0].id
        );
      }
      if (res && res.permissions_matrix && typeof res.permissions_matrix === 'object') {
        setPermissionsState((prev) => ({
          ...prev,
          ...res.permissions_matrix,
        }));
      }
    } catch (err) {
      console.error('Failed to load RBAC roles and permissions:', err);
    }
  }, []);

  useEffect(() => {
    fetchRoles();
  }, [fetchRoles]);

  // Fetch members when View Role Members modal opens
  useEffect(() => {
    if (!isViewMembersModalOpen || !activeRoleId) return;
    let cancelled = false;

    const loadMembers = async () => {
      setIsLoadingMembers(true);
      try {
        const res = await adminRolesApi.getRoleMembers(activeRoleId);
        if (!cancelled) {
          setRoleMembers(Array.isArray(res?.items) ? res.items : []);
        }
      } catch (err) {
        console.error('Failed to load role members:', err);
        if (!cancelled) {
          setRoleMembers([]);
          showToast('Không thể tải danh sách thành viên của vai trò.');
        }
      } finally {
        if (!cancelled) {
          setIsLoadingMembers(false);
        }
      }
    };

    loadMembers();
    return () => {
      cancelled = true;
    };
  }, [isViewMembersModalOpen, activeRoleId]);

  // Fetch assignable users when Assign User modal opens
  useEffect(() => {
    if (!isAddUserModalOpen) return;
    let cancelled = false;

    const loadUsers = async () => {
      setIsLoadingUsers(true);
      try {
        const res = await adminUsersApi.getUsers({ page_size: 100 });
        if (!cancelled) {
          setSystemUsers(Array.isArray(res?.items) ? res.items : []);
        }
      } catch (err) {
        console.error('Failed to load users for role assignment:', err);
        if (!cancelled) {
          setSystemUsers([]);
          showToast('Không thể tải danh sách người dùng từ hệ thống.');
        }
      } finally {
        if (!cancelled) {
          setIsLoadingUsers(false);
        }
      }
    };

    loadUsers();
    return () => {
      cancelled = true;
    };
  }, [isAddUserModalOpen]);

  const activeRole = roles.find(r => r.id === activeRoleId) || roles[0];
  const ActiveRoleIcon = activeRole?.icon || Shield;
  const currentPermissions = permissionsState[activeRoleId] || {};

  // Toggle a single permission
  const handleTogglePermission = (permKey) => {
    setPermissionsState(prev => ({
      ...prev,
      [activeRoleId]: {
        ...prev[activeRoleId],
        [permKey]: !prev[activeRoleId]?.[permKey]
      }
    }));
  };

  // Group definitions
  const permissionGroups = [
    {
      id: 'academic',
      number: 1,
      title: '1. QUẢN LÝ ĐÀO TẠO & LỚP HỌC',
      icon: BookOpen,
      permissions: [
        {
          key: 'view_schedule',
          title: 'Xem thời khóa biểu toàn trường',
          desc: 'Tra cứu lịch phân công giảng dạy và ca trực bộ môn',
          type: 'standard'
        },
        {
          key: 'create_class',
          title: 'Tạo lớp học mới & Gán môn học',
          desc: 'Khởi tạo lớp mới, cấu hình tín chỉ và phân lớp học sinh',
          type: 'standard'
        },
        {
          key: 'assign_teaching',
          title: 'Phân công giảng dạy & Chủ nhiệm',
          desc: 'Chỉ định giáo viên phụ trách các lớp học hoặc thay thế giảng viên',
          type: 'standard'
        }
      ]
    },
    {
      id: 'exercises',
      number: 2,
      title: '2. QUẢN LÝ BÀI TẬP & ĐỀ THI',
      icon: FileText,
      permissions: [
        {
          key: 'ai_exercise',
          title: 'Tạo sinh bài tập bằng AI',
          desc: 'Sử dụng trợ lý LMS AI tạo đề trắc nghiệm, bài tập tự luận và ma trận câu hỏi',
          type: 'standard'
        },
        {
          key: 'auto_grade',
          title: 'Chấm điểm bài nộp & Nhận xét tự động',
          desc: 'Nhập điểm trực tiếp, chấm điểm theo barem rubric và nhận xét tiến độ học viên',
          type: 'standard'
        },
        {
          key: 'publish_exam',
          title: 'Duyệt & Xuất bản đề thi chính thức',
          desc: 'Gửi đề thi lên ngân hàng chung hoặc xuất đề cho các kỳ kiểm tra tập trung',
          type: 'approval' // requires approval badge
        },
        {
          key: 'edit_score_closed',
          title: 'Sửa điểm sau khi đã phê duyệt sổ cái',
          desc: 'Yêu cầu phúc khảo điểm chính thức sau khi kỳ thi đã đóng',
          type: 'standard'
        }
      ]
    },
    {
      id: 'students',
      number: 3,
      title: '3. QUẢN LÝ HỌC SINH & HỒ SƠ HỌC BẠ',
      icon: Users,
      permissions: [
        {
          key: 'view_students',
          title: 'Xem danh sách học sinh & Điểm quá trình',
          desc: 'Xem danh sách lớp phụ trách, theo dõi chuyên cần và biểu đồ học lực',
          type: 'standard'
        },
        {
          key: 'edit_transcript',
          title: 'Sửa thông tin học bạ điện tử',
          desc: 'Cập nhật hồ sơ gốc, học bạ và điểm rèn luyện cấp trường',
          type: 'standard'
        }
      ]
    }
  ];

  // Calculate active counts per group
  const getGroupActiveCount = (group) => {
    const total = group.permissions.length;
    const active = group.permissions.filter(p => currentPermissions[p.key]).length;
    return `${active}/${total} Quyền kích hoạt`;
  };

  // Save changes handler
  const handleSaveChanges = async () => {
    if (!activeRole || isSaving) return;
    setIsSaving(true);
    try {
      const payloadPerms = permissionsState[activeRoleId] || {};
      const res = await adminRolesApi.updatePermissions(activeRoleId, payloadPerms);
      if (res && res.permissions) {
        setPermissionsState((prev) => ({
          ...prev,
          [activeRoleId]: res.permissions,
        }));
      }
      showToast(`Đã lưu cập nhật ma trận phân quyền cho vai trò "${activeRole.name}"!`);
    } catch (err) {
      console.error('Failed to update role permissions:', err);
      const errMsg = err.response?.data?.detail?.message || err.message || 'Lỗi khi lưu phân quyền.';
      showToast(`Lỗi: ${errMsg}`);
    } finally {
      setIsSaving(false);
    }
  };

  // Add new role submit
  const handleAddRoleSubmit = async (e) => {
    e.preventDefault();
    if (!newRole.name.trim() || !newRole.code.trim() || isCreatingRole) return;

    setIsCreatingRole(true);
    try {
      const res = await adminRolesApi.createRole({
        name: newRole.name.trim(),
        code: newRole.code.trim(),
        description: newRole.description.trim(),
        template_role_code: newRole.cloneFrom,
      });

      const createdDto = res?.role || res;
      const roleItem = mapApiRoleToUi(createdDto);
      setRoles((prev) => [...prev, roleItem]);
      setPermissionsState((prev) => ({
        ...prev,
        [roleItem.id]: res?.permissions || { ...(prev[newRole.cloneFrom] || prev.subject_teacher || {}) },
      }));
      setActiveRoleId(roleItem.id);
      setIsAddRoleModalOpen(false);
      showToast(`Đã tạo thành công vai trò "${roleItem.name}"!`);
      setNewRole({ name: '', code: '', description: '', cloneFrom: 'subject_teacher' });
    } catch (err) {
      console.error('Failed to create role:', err);
      const errMsg = err.response?.data?.detail?.message || err.message || 'Không thể tạo vai trò mới.';
      showToast(`Lỗi: ${errMsg}`);
    } finally {
      setIsCreatingRole(false);
    }
  };

  // Assign user to active role submit
  const handleAssignUserSubmit = async (e) => {
    e.preventDefault();
    if (!newUserToAssign || !activeRole || isAssigningUser) return;

    setIsAssigningUser(true);
    try {
      const res = await adminRolesApi.assignRoleMember(activeRoleId, newUserToAssign);
      const selectedUser = systemUsers.find(
        (u) => String(u.id || u.user_id) === String(newUserToAssign)
      );
      const displayUserName = res?.full_name || selectedUser?.full_name || 'người dùng';
      setIsAddUserModalOpen(false);
      setNewUserToAssign('');
      showToast(`Đã gán ${displayUserName} vào vai trò "${activeRole.name}"!`);
      await fetchRoles();
    } catch (err) {
      console.error('Failed to assign user to role:', err);
      const errMsg = err.response?.data?.detail?.message || err.message || 'Không thể gán người dùng.';
      showToast(`Lỗi: ${errMsg}`);
    } finally {
      setIsAssigningUser(false);
    }
  };

  // Export RBAC configuration file download
  const handleExportRoles = async () => {
    if (isExporting) return;
    setIsExporting(true);
    try {
      const blob = await adminRolesApi.exportRoles(exportFormat);
      const ext = exportFormat === 'json' ? 'json' : 'csv';
      const mime = exportFormat === 'json' ? 'application/json;charset=utf-8;' : 'text/csv;charset=utf-8;';
      triggerBlobDownload(blob, `roles_permissions_export.${ext}`, mime);
      setIsExportModalOpen(false);
      showToast('Đã tải xuống ma trận phân quyền RBAC thành công!');
    } catch (err) {
      console.error('Failed to export RBAC matrix:', err);
      const errMsg = err.response?.data?.detail?.message || err.message || 'Không thể xuất cấu hình phân quyền.';
      showToast(`Lỗi: ${errMsg}`);
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="admin-roles-page-container">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="admin-toast">
          <CheckCircle2 size={18} />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* 1. Header Section */}
      <section className="roles-page-header">
        <div className="roles-header-title-block">
          <div className="roles-security-tag">
            <span>BẢO MẬT HỆ THỐNG</span>
            <span className="dot">•</span>
            <span className="tag-accent">RBAC MATRIX V2.4</span>
          </div>
          <div className="roles-header-title-row">
            <h1 className="roles-page-title">Phân quyền & Vai trò</h1>
            <Shield size={22} className="roles-title-icon" />
          </div>
          <p className="roles-page-subtitle">
            Quản lý nhóm vai trò, thiết lập ma trận quyền hạn chi tiết và phân quyền tài khoản người dùng theo tổ chức.
          </p>
        </div>

        <div className="roles-header-actions">
          <button 
            type="button" 
            className="btn-roles-export"
            onClick={() => setIsExportModalOpen(true)}
          >
            <Download size={16} strokeWidth={2} />
            <span>Xuất cấu hình quyền</span>
          </button>

          <button 
            type="button" 
            className="btn-roles-add"
            onClick={() => setIsAddRoleModalOpen(true)}
          >
            <Plus size={17} strokeWidth={2.4} />
            <span>+ Thêm vai trò mới</span>
          </button>
        </div>
      </section>

      {/* 2. Master-Detail Two Column Layout */}
      <section className="roles-master-detail-row">
        {/* LEFT COLUMN: Role Selector List */}
        <div className="roles-left-col">
          <div className="roles-left-header">
            <div className="roles-left-header-left">
              <h3 className="roles-left-title">Vai trò hệ thống</h3>
              <p className="roles-left-subtitle">Chọn vai trò để quản trị quyền</p>
            </div>
            <div className="roles-left-header-right">
              <span className="roles-count-pill">{roles.length} vai trò</span>
              <button 
                type="button" 
                className="btn-quick-add-role"
                title="Tạo vai trò mới"
                onClick={() => setIsAddRoleModalOpen(true)}
              >
                <Plus size={15} />
              </button>
            </div>
          </div>

          {/* Role Cards List */}
          <div className="roles-cards-list">
            {roles.map(role => {
              const Icon = role.icon;
              const isSelected = activeRoleId === role.id;

              return (
                <div 
                  key={role.id}
                  className={`role-item-card ${isSelected ? 'active' : ''}`}
                  onClick={() => setActiveRoleId(role.id)}
                >
                  <div className="role-item-top">
                    <div 
                      className="role-item-icon-box"
                      style={{ backgroundColor: role.iconBg, color: role.iconColor }}
                    >
                      <Icon size={18} strokeWidth={2.2} />
                    </div>
                    <div className="role-item-meta">
                      <h4 className="role-item-name">{role.name}</h4>
                      <p className="role-item-desc">{role.description}</p>
                    </div>
                    <div className="role-item-badge-pill">
                      {role.memberCount} người
                    </div>
                  </div>

                  {/* Active selection footer indicator */}
                  {isSelected && (
                    <div className="role-item-active-footer">
                      <span className="active-editing-text">
                        <span className="status-dot purple"></span>
                        Đang chọn chỉnh sửa
                      </span>
                      <button 
                        type="button" 
                        className="role-detail-members-link"
                        onClick={(e) => {
                          e.stopPropagation();
                          setIsViewMembersModalOpen(true);
                        }}
                      >
                        Chi tiết thành viên →
                      </button>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Bottom Security Rule Card */}
          <div className="roles-security-rule-box">
            <Shield size={20} className="rule-shield-icon" />
            <div className="rule-content">
              <h5 className="rule-title">Quy tắc kiểm soát vai trò</h5>
              <p className="rule-desc">
                Thay đổi quyền hạn vai trò sẽ được áp dụng ngay cho tất cả người dùng thuộc vai trò này sau lần đăng nhập kế tiếp.
              </p>
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN: Permission Matrix for Active Role */}
        <div className="roles-right-col">
          {/* Header of Active Role */}
          <div className="matrix-header-card">
            <div className="matrix-header-left">
              <div className="matrix-role-avatar">
                <ActiveRoleIcon size={22} />
              </div>
              <div className="matrix-role-info">
                <div className="matrix-role-title-row">
                  <h2 className="matrix-role-title">{activeRole.name}</h2>
                  <span className="matrix-role-status-badge">
                    <span className="status-dot green"></span>
                    Đang hoạt động
                  </span>
                </div>
                <p className="matrix-role-desc">
                  Phân quyền chi tiết cho nhóm {activeRole.memberCount} {activeRole.name.toLowerCase()} toàn trường
                </p>
              </div>
            </div>

            <div className="matrix-header-actions">
              <button 
                type="button" 
                className="btn-matrix-add-user"
                onClick={() => setIsAddUserModalOpen(true)}
              >
                <UserPlus size={15} />
                <span>+ Thêm người dùng</span>
              </button>

              <button 
                type="button" 
                className="btn-matrix-save"
                onClick={handleSaveChanges}
                disabled={isSaving}
              >
                <Save size={15} />
                <span>{isSaving ? 'Đang lưu...' : 'Lưu thay đổi'}</span>
              </button>
            </div>
          </div>

          {/* Permission Groups List */}
          <div className="permission-groups-container">
            {permissionGroups.map(group => {
              return (
                <div key={group.id} className="permission-group-card">
                  <div className="permission-group-header">
                    <div className="group-header-left">
                      <group.icon size={16} className="group-header-icon" />
                      <h4 className="group-header-title">{group.title}</h4>
                    </div>
                    <span className="group-active-counter-badge">
                      {getGroupActiveCount(group)}
                    </span>
                  </div>

                  <div className="permission-items-list">
                    {group.permissions.map(perm => {
                      const isChecked = !!currentPermissions[perm.key];
                      const isApproval = perm.type === 'approval' && isChecked;

                      return (
                        <div key={perm.key} className="permission-item-row">
                          <div className="perm-info-block">
                            <h5 className="perm-title">{perm.title}</h5>
                            <p className="perm-desc">{perm.desc}</p>
                          </div>

                          <div className="perm-action-block">
                            {/* Permission status pill label */}
                            {isApproval ? (
                              <span className="perm-status-badge approval">
                                Cần phê duyệt
                              </span>
                            ) : isChecked ? (
                              <span className="perm-status-badge enabled">
                                Cho phép
                              </span>
                            ) : (
                              <span className="perm-status-badge disabled">
                                Vô hiệu hóa
                              </span>
                            )}

                            {/* Toggle Switch */}
                            <label className="permission-switch">
                              <input 
                                type="checkbox" 
                                checked={isChecked}
                                onChange={() => handleTogglePermission(perm.key)}
                              />
                              <span className="switch-slider"></span>
                            </label>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* MODAL: Thêm vai trò mới */}
      {isAddRoleModalOpen && (
        <div className="admin-modal-backdrop" onClick={() => setIsAddRoleModalOpen(false)}>
          <div className="admin-modal-card" onClick={e => e.stopPropagation()}>
            <div className="admin-modal-header">
              <h3 className="admin-modal-title">Tạo vai trò hệ thống mới</h3>
              <button type="button" className="admin-modal-close" onClick={() => setIsAddRoleModalOpen(false)}>
                <X size={20} />
              </button>
            </div>
            <form onSubmit={handleAddRoleSubmit} className="admin-modal-body">
              <div className="admin-form-group">
                <label className="admin-form-label">Tên vai trò *</label>
                <input 
                  type="text" 
                  className="admin-form-input" 
                  placeholder="Ví dụ: Giám thị hành lang" 
                  value={newRole.name}
                  onChange={e => setNewRole(p => ({ ...p, name: e.target.value }))}
                  required 
                />
              </div>

              <div className="admin-form-group">
                <label className="admin-form-label">Mã định danh vai trò (Role Code) *</label>
                <input 
                  type="text" 
                  className="admin-form-input" 
                  placeholder="Ví dụ: HALL_SUPERVISOR" 
                  value={newRole.code}
                  onChange={e => setNewRole(p => ({ ...p, code: e.target.value }))}
                  required 
                />
              </div>

              <div className="admin-form-group">
                <label className="admin-form-label">Mô tả nhiệm vụ & phạm vi</label>
                <textarea 
                  className="admin-form-input" 
                  rows="3"
                  placeholder="Mô tả tóm tắt quyền hạn và trách nhiệm..."
                  value={newRole.description}
                  onChange={e => setNewRole(p => ({ ...p, description: e.target.value }))}
                />
              </div>

              <div className="admin-form-group">
                <label className="admin-form-label">Sao chép quyền từ vai trò có sẵn</label>
                <select 
                  className="admin-form-select"
                  value={newRole.cloneFrom}
                  onChange={e => setNewRole(p => ({ ...p, cloneFrom: e.target.value }))}
                >
                  {roles.map((r) => (
                    <option key={r.id} value={r.id}>
                      {r.name}{r.id === 'subject_teacher' ? ' (Khuyên dùng)' : ''}
                    </option>
                  ))}
                </select>
              </div>

              <div className="admin-modal-footer">
                <button type="button" className="admin-btn-cancel" onClick={() => setIsAddRoleModalOpen(false)}>
                  Hủy
                </button>
                <button type="submit" className="admin-btn-primary" disabled={isCreatingRole}>
                  {isCreatingRole ? 'Đang tạo...' : 'Tạo vai trò'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: Thêm người dùng vào vai trò */}
      {isAddUserModalOpen && (
        <div className="admin-modal-backdrop" onClick={() => setIsAddUserModalOpen(false)}>
          <div className="admin-modal-card" onClick={e => e.stopPropagation()}>
            <div className="admin-modal-header">
              <h3 className="admin-modal-title">Gán người dùng vào vai trò: {activeRole.name}</h3>
              <button type="button" className="admin-modal-close" onClick={() => setIsAddUserModalOpen(false)}>
                <X size={20} />
              </button>
            </div>
            <form onSubmit={handleAssignUserSubmit} className="admin-modal-body">
              <p className="admin-modal-desc">
                Tài khoản được gán sẽ ngay lập tức được hưởng các quyền hạn tương ứng của vai trò <strong>{activeRole.name}</strong>.
              </p>

              <div className="admin-form-group">
                <label className="admin-form-label">Chọn tài khoản người dùng</label>
                <select 
                  className="admin-form-select"
                  value={newUserToAssign}
                  onChange={e => setNewUserToAssign(e.target.value)}
                  disabled={isLoadingUsers}
                  required
                >
                  <option value="">
                    {isLoadingUsers ? '-- Đang tải danh sách người dùng... --' : '-- Chọn tài khoản từ hệ thống --'}
                  </option>
                  {systemUsers.map((u) => {
                    const uid = u.id || u.user_id;
                    const subInfo = [u.email, u.role].filter(Boolean).join(' • ');
                    return (
                      <option key={uid} value={uid}>
                        {u.full_name}{subInfo ? ` (${subInfo})` : ''}
                      </option>
                    );
                  })}
                </select>
              </div>

              <div className="admin-modal-footer">
                <button type="button" className="admin-btn-cancel" onClick={() => setIsAddUserModalOpen(false)}>
                  Hủy
                </button>
                <button type="submit" className="admin-btn-primary" disabled={!newUserToAssign || isAssigningUser}>
                  {isAssigningUser ? 'Đang gán...' : 'Xác nhận gán'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: Chi tiết thành viên */}
      {isViewMembersModalOpen && (
        <div className="admin-modal-backdrop" onClick={() => setIsViewMembersModalOpen(false)}>
          <div className="admin-modal-card modal-lg" onClick={e => e.stopPropagation()}>
            <div className="admin-modal-header">
              <h3 className="admin-modal-title">Danh sách thành viên ({activeRole.name} - {activeRole.memberCount} người)</h3>
              <button type="button" className="admin-modal-close" onClick={() => setIsViewMembersModalOpen(false)}>
                <X size={20} />
              </button>
            </div>
            <div className="admin-modal-body">
              <div className="members-drawer-list">
                {isLoadingMembers ? (
                  <p className="admin-modal-desc">Đang tải danh sách thành viên...</p>
                ) : roleMembers.length === 0 ? (
                  <p className="admin-modal-desc">Chưa có thành viên nào được gán vào vai trò này.</p>
                ) : (
                  roleMembers.map((member) => (
                    <div key={member.user_id} className="member-drawer-item">
                      <div className="member-drawer-avatar">{getInitials(member.full_name)}</div>
                      <div className="member-drawer-meta">
                        <h4>{member.full_name}</h4>
                        <p>
                          {[member.email || 'Chưa cập nhật email', member.phone].filter(Boolean).join(' • ')}
                        </p>
                      </div>
                      <span className="member-drawer-status">{formatMemberStatus(member.status)}</span>
                    </div>
                  ))
                )}
              </div>

              <div className="admin-modal-footer">
                <button type="button" className="admin-btn-cancel" onClick={() => setIsViewMembersModalOpen(false)}>
                  Đóng
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* MODAL: Xuất cấu hình quyền */}
      {isExportModalOpen && (
        <div className="admin-modal-backdrop" onClick={() => setIsExportModalOpen(false)}>
          <div className="admin-modal-card" onClick={e => e.stopPropagation()}>
            <div className="admin-modal-header">
              <h3 className="admin-modal-title">Xuất ma trận phân quyền RBAC</h3>
              <button type="button" className="admin-modal-close" onClick={() => setIsExportModalOpen(false)}>
                <X size={20} />
              </button>
            </div>
            <div className="admin-modal-body">
              <p className="admin-modal-desc">
                Tải xuống tập tin cấu hình ma trận phân quyền hệ thống cho toàn bộ {roles.length} vai trò.
              </p>
              <div className="admin-form-group">
                <label className="admin-form-label">Định dạng xuất</label>
                <div className="export-options-row">
                  <label className="export-option-box">
                    <input
                      type="radio"
                      name="rbacExportFormat"
                      value="json"
                      checked={exportFormat === 'json'}
                      onChange={() => setExportFormat('json')}
                    />
                    <span>Tệp cấu hình JSON (.json)</span>
                  </label>
                  <label className="export-option-box">
                    <input
                      type="radio"
                      name="rbacExportFormat"
                      value="csv"
                      checked={exportFormat === 'csv'}
                      onChange={() => setExportFormat('csv')}
                    />
                    <span>Bảng ma trận CSV / Excel (.csv)</span>
                  </label>
                </div>
              </div>

              <div className="admin-modal-footer">
                <button type="button" className="admin-btn-cancel" onClick={() => setIsExportModalOpen(false)}>
                  Đóng
                </button>
                <button 
                  type="button" 
                  className="admin-btn-primary"
                  onClick={handleExportRoles}
                  disabled={isExporting}
                >
                  <Download size={16} />
                  <span>{isExporting ? 'Đang tải...' : 'Tải xuống'}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
