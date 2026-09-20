// File Name: AdminRolesPage.jsx
// Description: Comprehensive Roles & Permissions management screen for Admin portal with master-detail layout, module grouping, and interactive toggle matrix.
// Created At: 2026-09-19
// Created By: Tam Khang
// Updated At: 2026-09-20
// Updated By: Tam Khang

import React, { useState } from 'react';
import { 
  ShieldCheck, 
  Shield, 
  Key, 
  Users, 
  RotateCcw, 
  Download, 
  Plus, 
  UserCheck, 
  CheckCircle2, 
  AlertCircle, 
  BookOpen, 
  FileText, 
  ChevronRight, 
  UserPlus, 
  Save, 
  X, 
  GraduationCap, 
  HelpCircle,
  Clock,
  Sparkles
} from 'lucide-react';
import './AdminRolesPage.css';

export default function AdminRolesPage() {
  const [activeRoleId, setActiveRoleId] = useState('subject_teacher');
  const [toastMessage, setToastMessage] = useState(null);

  // Modals state
  const [isAddRoleModalOpen, setIsAddRoleModalOpen] = useState(false);
  const [isAddUserModalOpen, setIsAddUserModalOpen] = useState(false);
  const [isViewMembersModalOpen, setIsViewMembersModalOpen] = useState(false);
  const [isExportModalOpen, setIsExportModalOpen] = useState(false);

  // New role form state
  const [newRole, setNewRole] = useState({
    name: '',
    code: '',
    description: '',
    cloneFrom: 'subject_teacher'
  });

  const [newUserToAssign, setNewUserToAssign] = useState('');

  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => {
      setToastMessage(null);
    }, 3500);
  };

  // Roles list matching the mockup
  const [roles, setRoles] = useState([
    {
      id: 'admin',
      name: 'Quản trị viên',
      description: 'Toàn quyền quản trị hệ thống',
      memberCount: 16,
      icon: Shield,
      iconBg: '#F3ECFF',
      iconColor: '#4D308D',
      status: 'active'
    },
    {
      id: 'head_teacher',
      name: 'Tổ trưởng chuyên môn',
      description: 'Duyệt giáo án, giám sát bộ môn',
      memberCount: 14,
      icon: ShieldCheck,
      iconBg: '#EDE9FE',
      iconColor: '#6D28D9',
      status: 'active'
    },
    {
      id: 'subject_teacher',
      name: 'Giáo viên bộ môn',
      description: 'Lớp phụ trách, Chấm bài & Soạn đề',
      memberCount: 112,
      icon: UserCheck,
      iconBg: '#F3ECFF',
      iconColor: '#4D308D',
      status: 'active'
    },
    {
      id: 'academic_staff',
      name: 'Giáo vụ đào tạo',
      description: 'Hồ sơ học sinh & Điểm danh lớp',
      memberCount: 6,
      icon: BookOpen,
      iconBg: '#FEF3C7',
      iconColor: '#D97706',
      status: 'active'
    },
    {
      id: 'student_parent',
      name: 'Học sinh & Phụ huynh',
      description: 'Học tập trực tuyến, Nộp bài tập',
      memberCount: 2450,
      icon: GraduationCap,
      iconBg: '#E6F8EE',
      iconColor: '#059669',
      status: 'active'
    }
  ]);

  // Permission groups with permissions state for the currently active role
  const [permissionsState, setPermissionsState] = useState({
    subject_teacher: {
      // Group 1
      view_schedule: true,
      create_class: false,
      assign_teaching: false,
      // Group 2
      ai_exercise: true,
      auto_grade: true,
      publish_exam: true, // approval required
      edit_score_closed: false,
      // Group 3
      view_students: true,
      edit_transcript: false
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
      edit_transcript: true
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
      edit_transcript: false
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
      edit_transcript: true
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
      edit_transcript: false
    }
  });

  const activeRole = roles.find(r => r.id === activeRoleId) || roles[0];
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
  const handleSaveChanges = () => {
    showToast(`Đã lưu cập nhật ma trận phân quyền cho vai trò "${activeRole.name}"!`);
  };

  // Add new role submit
  const handleAddRoleSubmit = (e) => {
    e.preventDefault();
    if (!newRole.name || !newRole.code) return;

    const newId = newRole.code.toLowerCase().replace(/[^a-z0-9]/g, '_');
    const roleItem = {
      id: newId,
      name: newRole.name,
      description: newRole.description || 'Vai trò tùy chỉnh hệ thống',
      memberCount: 0,
      icon: Key,
      iconBg: '#F3ECFF',
      iconColor: '#4D308D',
      status: 'active'
    };

    setRoles(prev => [...prev, roleItem]);
    setPermissionsState(prev => ({
      ...prev,
      [newId]: { ...(prev[newRole.cloneFrom] || prev.subject_teacher) }
    }));
    setActiveRoleId(newId);
    setIsAddRoleModalOpen(false);
    showToast(`Đã tạo thành công vai trò "${roleItem.name}"!`);
    setNewRole({ name: '', code: '', description: '', cloneFrom: 'subject_teacher' });
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
                <activeRole.icon size={22} />
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
              >
                <Save size={15} />
                <span>Lưu thay đổi</span>
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
                  <option value="subject_teacher">Giáo viên bộ môn (Khuyên dùng)</option>
                  <option value="academic_staff">Giáo vụ đào tạo</option>
                  <option value="head_teacher">Tổ trưởng chuyên môn</option>
                  <option value="admin">Quản trị viên</option>
                </select>
              </div>

              <div className="admin-modal-footer">
                <button type="button" className="admin-btn-cancel" onClick={() => setIsAddRoleModalOpen(false)}>
                  Hủy
                </button>
                <button type="submit" className="admin-btn-primary">
                  Tạo vai trò
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
            <form onSubmit={e => {
              e.preventDefault();
              if (!newUserToAssign) return;
              setRoles(prev => prev.map(r => r.id === activeRoleId ? { ...r, memberCount: r.memberCount + 1 } : r));
              setIsAddUserModalOpen(false);
              showToast(`Đã gán ${newUserToAssign} vào vai trò "${activeRole.name}"!`);
              setNewUserToAssign('');
            }} className="admin-modal-body">
              <p className="admin-modal-desc">
                Tài khoản được gán sẽ ngay lập tức được hưởng các quyền hạn tương ứng của vai trò <strong>{activeRole.name}</strong>.
              </p>

              <div className="admin-form-group">
                <label className="admin-form-label">Chọn tài khoản người dùng</label>
                <select 
                  className="admin-form-select"
                  value={newUserToAssign}
                  onChange={e => setNewUserToAssign(e.target.value)}
                  required
                >
                  <option value="">-- Chọn tài khoản từ hệ thống --</option>
                  <option value="ThS. Lê Nguyên (le.nguyen@clarity.edu.vn)">ThS. Lê Nguyên (le.nguyen@clarity.edu.vn)</option>
                  <option value="Cô Mai Lan (lan.mai@clarity.edu.vn)">Cô Mai Lan (lan.mai@clarity.edu.vn)</option>
                  <option value="Thầy Lê Phương Duy (duy.lp@clarity.edu.vn)">Thầy Lê Phương Duy (duy.lp@clarity.edu.vn)</option>
                  <option value="Hoàng Mỹ Dung (dung.hm@clarity.edu.vn)">Hoàng Mỹ Dung (dung.hm@clarity.edu.vn)</option>
                </select>
              </div>

              <div className="admin-modal-footer">
                <button type="button" className="admin-btn-cancel" onClick={() => setIsAddUserModalOpen(false)}>
                  Hủy
                </button>
                <button type="submit" className="admin-btn-primary" disabled={!newUserToAssign}>
                  Xác nhận gán
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
                <div className="member-drawer-item">
                  <div className="member-drawer-avatar">LN</div>
                  <div className="member-drawer-meta">
                    <h4>ThS. Lê Nguyên</h4>
                    <p>le.nguyen@clarity.edu.vn • Tổ Toán - Tin</p>
                  </div>
                  <span className="member-drawer-status">Đang hoạt động</span>
                </div>

                <div className="member-drawer-item">
                  <div className="member-drawer-avatar">ML</div>
                  <div className="member-drawer-meta">
                    <h4>Cô Mai Lan</h4>
                    <p>lan.mai@clarity.edu.vn • Tổ Toán - Tin</p>
                  </div>
                  <span className="member-drawer-status">Đang hoạt động</span>
                </div>

                <div className="member-drawer-item">
                  <div className="member-drawer-avatar">PD</div>
                  <div className="member-drawer-meta">
                    <h4>Thầy Lê Phương Duy</h4>
                    <p>duy.lp@clarity.edu.vn • Tổ Ngoại ngữ</p>
                  </div>
                  <span className="member-drawer-status">Đang hoạt động</span>
                </div>
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
                Tải xuống tập tin cấu hình ma trận phân quyền hệ thống cho cả 5 vai trò.
              </p>
              <div className="admin-form-group">
                <label className="admin-form-label">Định dạng xuất</label>
                <div className="export-options-row">
                  <label className="export-option-box">
                    <input type="radio" name="rbacExportFormat" defaultChecked />
                    <span>Tệp cấu hình JSON (.json)</span>
                  </label>
                  <label className="export-option-box">
                    <input type="radio" name="rbacExportFormat" />
                    <span>Bảng ma trận Excel (.xlsx)</span>
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
                  onClick={() => {
                    setIsExportModalOpen(false);
                    showToast('Đang tải xuống ma trận phân quyền RBAC...');
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
