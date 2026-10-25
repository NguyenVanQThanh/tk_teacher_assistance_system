// File Name: TeacherProfileModal.jsx
// Description: Interactive Modal for Teacher Profile Information and Security / Password Management.
// Created At: 2026-09-01
// Created By: Tam Khang
// Updated At: 2026-09-01
// Updated By: Tam Khang

import React, { useState, useEffect } from 'react';
import { 
  X, 
  User, 
  Shield, 
  Mail, 
  Phone, 
  MapPin, 
  Building2, 
  GraduationCap, 
  BadgeCheck, 
  CheckCircle2, 
  Lock, 
  Eye, 
  EyeOff, 
  KeyRound, 
  Smartphone, 
  History, 
  Save, 
  Edit3, 
  Camera, 
  AlertCircle
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { getTeacherProfileDefaults } from '../../utils/teacherSubjectHelper';
import './TeacherProfileModal.css';

export default function TeacherProfileModal({ 
  isOpen, 
  onClose, 
  defaultTab = 'profile' 
}) {
  if (!isOpen) return null;

  const { user } = useAuth();
  const profileDefaults = getTeacherProfileDefaults(user);

  const [activeTab, setActiveTab] = useState(defaultTab);
  const [toastMessage, setToastMessage] = useState(null);

  useEffect(() => {
    setActiveTab(defaultTab);
  }, [defaultTab]);

  // Profile state
  const [isEditingProfile, setIsEditingProfile] = useState(false);
  const [profileForm, setProfileForm] = useState({
    fullName: user?.full_name || 'Nguyễn Văn A',
    title: 'GV.',
    gender: 'Nam',
    dob: '1985-08-15',
    citizenId: '001085012345',
    email: user?.email || 'giaovien.mau@eduglobal.edu.vn',
    phone: user?.phone || '0912 345 678',
    address: 'Số 144 Xuân Thủy, Cầu Giấy, Hà Nội',
    school: 'Trường THPT Chuyên',
    department: profileDefaults.department,
    position: profileDefaults.position,
    degree: profileDefaults.degree,
    startYear: '2015',
    teacherCode: profileDefaults.teacherCode
  });

  // Re-sync profile form when user changes
  useEffect(() => {
    if (user) {
      const defs = getTeacherProfileDefaults(user);
      setProfileForm(prev => ({
        ...prev,
        fullName: user.full_name || prev.fullName,
        email: user.email || prev.email,
        phone: user.phone || prev.phone,
        department: defs.department,
        position: defs.position,
        degree: defs.degree,
        teacherCode: defs.teacherCode
      }));
    }
  }, [user]);

  // Security state
  const [passwordForm, setPasswordForm] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  });
  const [showCurrentPass, setShowCurrentPass] = useState(false);
  const [showNewPass, setShowNewPass] = useState(false);
  const [showConfirmPass, setShowConfirmPass] = useState(false);
  const [twoFactorEnabled, setTwoFactorEnabled] = useState(true);

  // Save profile changes
  const handleSaveProfile = (e) => {
    e.preventDefault();
    setIsEditingProfile(false);
    setToastMessage('Đã cập nhật thông tin hồ sơ cá nhân thành công!');
    setTimeout(() => setToastMessage(null), 3000);
  };

  // Change password handler
  const handleChangePassword = (e) => {
    e.preventDefault();
    if (!passwordForm.currentPassword || !passwordForm.newPassword || !passwordForm.confirmPassword) {
      alert('Vui lòng điền đầy đủ các trường mật khẩu.');
      return;
    }
    if (passwordForm.newPassword !== passwordForm.confirmPassword) {
      alert('Mật khẩu mới và xác nhận mật khẩu không trùng khớp!');
      return;
    }
    if (passwordForm.newPassword.length < 8) {
      alert('Mật khẩu mới phải có tối thiểu 8 ký tự!');
      return;
    }

    setPasswordForm({
      currentPassword: '',
      newPassword: '',
      confirmPassword: ''
    });
    setToastMessage('Đã đổi mật khẩu thành công! Vui lòng sử dụng mật khẩu mới cho lần đăng nhập sau.');
    setTimeout(() => setToastMessage(null), 3500);
  };

  // Password strength checker
  const getPasswordStrength = (pass) => {
    if (!pass) return { score: 0, text: '', color: '#E2E8F0' };
    let score = 0;
    if (pass.length >= 8) score += 1;
    if (/[A-Z]/.test(pass)) score += 1;
    if (/[0-9]/.test(pass)) score += 1;
    if (/[^A-Za-z0-9]/.test(pass)) score += 1;

    if (score <= 1) return { score: 1, text: 'Yếu', color: '#EF4444' };
    if (score <= 3) return { score: 2, text: 'Trung bình', color: '#F59E0B' };
    return { score: 3, text: 'Mạnh & An toàn', color: '#10B981' };
  };

  const passStrength = getPasswordStrength(passwordForm.newPassword);
  const initial = profileForm.fullName ? profileForm.fullName.split(' ').map(n => n[0]).slice(-2).join('').toUpperCase() : 'GV';

  return (
    <div className="teacher-profile-modal-overlay" onClick={onClose}>
      <div className="teacher-profile-modal-window" onClick={(e) => e.stopPropagation()}>
        {/* Toast Alert */}
        {toastMessage && (
          <div className="modal-inner-toast">
            <CheckCircle2 size={16} />
            <span>{toastMessage}</span>
          </div>
        )}

        {/* Modal Header */}
        <div className="profile-modal-top-bar">
          <div className="modal-title-with-tabs">
            <button
              type="button"
              className={`modal-nav-tab-btn ${activeTab === 'profile' ? 'active' : ''}`}
              onClick={() => setActiveTab('profile')}
            >
              <User size={16} />
              <span>Hồ sơ & Thông tin cá nhân</span>
            </button>

            <button
              type="button"
              className={`modal-nav-tab-btn ${activeTab === 'security' ? 'active' : ''}`}
              onClick={() => setActiveTab('security')}
            >
              <Shield size={16} />
              <span>Bảo mật & Đổi mật khẩu</span>
            </button>
          </div>

          <button 
            type="button" 
            className="btn-modal-close-icon" 
            onClick={onClose}
            title="Đóng cửa sổ"
          >
            <X size={20} />
          </button>
        </div>

        {/* Modal Body */}
        <div className="profile-modal-scroll-body">
          {/* Hero Profile Banner */}
          <div className="modal-hero-profile-banner">
            <div className="modal-hero-avatar-wrap">
              <div className="modal-avatar-circle">
                <span>{initial}</span>
              </div>
              <button 
                type="button" 
                className="btn-avatar-camera"
                title="Thay đổi ảnh đại diện"
                onClick={() => alert('Chọn ảnh mới từ thiết bị')}
              >
                <Camera size={13} />
              </button>
            </div>

            <div className="modal-hero-info">
              <div className="hero-name-badge-row">
                <h3 className="modal-teacher-name">{profileForm.title} {profileForm.fullName}</h3>
                <span className="modal-working-badge">Đang công tác</span>
              </div>
              <div className="modal-meta-pills-row">
                <span className="meta-pill"><GraduationCap size={12} /> {profileForm.position}</span>
                <span className="meta-pill"><Building2 size={12} /> {profileForm.school}</span>
                <span className="meta-pill code-badge"><BadgeCheck size={12} /> Mã GV: {profileForm.teacherCode}</span>
              </div>
            </div>

            {activeTab === 'profile' && !isEditingProfile && (
              <button 
                type="button" 
                className="btn-enable-edit"
                onClick={() => setIsEditingProfile(true)}
              >
                <Edit3 size={14} />
                <span>Chỉnh sửa hồ sơ</span>
              </button>
            )}
          </div>

          {/* Tab 1: Personal Profile Info */}
          {activeTab === 'profile' && (
            <form onSubmit={handleSaveProfile} className="profile-form-sections-stack">
              {/* Section 1: Thông tin cơ bản */}
              <div className="modal-section-card">
                <div className="section-head-row">
                  <div className="section-title-wrap">
                    <User size={16} className="text-purple-600" />
                    <h4 className="section-title-text">Thông tin cơ bản</h4>
                  </div>
                  {isEditingProfile && (
                    <span className="editing-badge-alert">Đang chỉnh sửa</span>
                  )}
                </div>

                <div className="modal-form-grid-3">
                  <div className="form-item-field">
                    <label className="item-label">Họ và tên</label>
                    <input
                      type="text"
                      disabled={!isEditingProfile}
                      value={profileForm.fullName}
                      onChange={(e) => setProfileForm({ ...profileForm, fullName: e.target.value })}
                      className="modal-text-input"
                    />
                  </div>

                  <div className="form-item-field">
                    <label className="item-label">Giới tính</label>
                    <select
                      disabled={!isEditingProfile}
                      value={profileForm.gender}
                      onChange={(e) => setProfileForm({ ...profileForm, gender: e.target.value })}
                      className="modal-text-input"
                    >
                      <option value="Nam">Nam</option>
                      <option value="Nữ">Nữ</option>
                      <option value="Khác">Khác</option>
                    </select>
                  </div>

                  <div className="form-item-field">
                    <label className="item-label">Ngày sinh</label>
                    <input
                      type="date"
                      disabled={!isEditingProfile}
                      value={profileForm.dob}
                      onChange={(e) => setProfileForm({ ...profileForm, dob: e.target.value })}
                      className="modal-text-input"
                    />
                  </div>

                  <div className="form-item-field">
                    <label className="item-label">Số CCCD / CMND</label>
                    <input
                      type="text"
                      disabled={!isEditingProfile}
                      value={profileForm.citizenId}
                      onChange={(e) => setProfileForm({ ...profileForm, citizenId: e.target.value })}
                      className="modal-text-input"
                    />
                  </div>

                  <div className="form-item-field">
                    <label className="item-label">Mã số giáo viên</label>
                    <input
                      type="text"
                      disabled
                      value={profileForm.teacherCode}
                      className="modal-text-input readonly-bg"
                    />
                  </div>
                </div>
              </div>

              {/* Section 2: Thông tin liên hệ */}
              <div className="modal-section-card">
                <div className="section-head-row">
                  <div className="section-title-wrap">
                    <Mail size={16} className="text-purple-600" />
                    <h4 className="section-title-text">Thông tin liên hệ</h4>
                  </div>
                </div>

                <div className="modal-form-grid-3">
                  <div className="form-item-field">
                    <label className="item-label">Email công vụ</label>
                    <input
                      type="email"
                      disabled={!isEditingProfile}
                      value={profileForm.email}
                      onChange={(e) => setProfileForm({ ...profileForm, email: e.target.value })}
                      className="modal-text-input"
                    />
                  </div>

                  <div className="form-item-field">
                    <label className="item-label">Số điện thoại</label>
                    <input
                      type="tel"
                      disabled={!isEditingProfile}
                      value={profileForm.phone}
                      onChange={(e) => setProfileForm({ ...profileForm, phone: e.target.value })}
                      className="modal-text-input"
                    />
                  </div>

                  <div className="form-item-field">
                    <label className="item-label">Địa chỉ</label>
                    <input
                      type="text"
                      disabled={!isEditingProfile}
                      value={profileForm.address}
                      onChange={(e) => setProfileForm({ ...profileForm, address: e.target.value })}
                      className="modal-text-input"
                    />
                  </div>
                </div>
              </div>

              {/* Section 3: Công tác & Chuyên môn */}
              <div className="modal-section-card">
                <div className="section-head-row">
                  <div className="section-title-wrap">
                    <GraduationCap size={16} className="text-purple-600" />
                    <h4 className="section-title-text">Thông tin công tác & Chuyên môn</h4>
                  </div>
                </div>

                <div className="modal-form-grid-3">
                  <div className="form-item-field">
                    <label className="item-label">Đơn vị công tác</label>
                    <input
                      type="text"
                      disabled={!isEditingProfile}
                      value={profileForm.school}
                      onChange={(e) => setProfileForm({ ...profileForm, school: e.target.value })}
                      className="modal-text-input"
                    />
                  </div>

                  <div className="form-item-field">
                    <label className="item-label">Tổ chuyên môn</label>
                    <input
                      type="text"
                      disabled={!isEditingProfile}
                      value={profileForm.department}
                      onChange={(e) => setProfileForm({ ...profileForm, department: e.target.value })}
                      className="modal-text-input"
                    />
                  </div>

                  <div className="form-item-field">
                    <label className="item-label">Nhiệm vụ / Vị trí</label>
                    <input
                      type="text"
                      disabled={!isEditingProfile}
                      value={profileForm.position}
                      onChange={(e) => setProfileForm({ ...profileForm, position: e.target.value })}
                      className="modal-text-input"
                    />
                  </div>

                  <div className="form-item-field">
                    <label className="item-label">Trình độ đào tạo</label>
                    <input
                      type="text"
                      disabled={!isEditingProfile}
                      value={profileForm.degree}
                      onChange={(e) => setProfileForm({ ...profileForm, degree: e.target.value })}
                      className="modal-text-input"
                    />
                  </div>

                  <div className="form-item-field">
                    <label className="item-label">Năm bắt đầu công tác</label>
                    <input
                      type="number"
                      disabled={!isEditingProfile}
                      value={profileForm.startYear}
                      onChange={(e) => setProfileForm({ ...profileForm, startYear: e.target.value })}
                      className="modal-text-input"
                    />
                  </div>
                </div>
              </div>

              {/* Bottom Actions */}
              {isEditingProfile && (
                <div className="modal-profile-bottom-actions">
                  <button
                    type="button"
                    className="btn-modal-cancel-edit"
                    onClick={() => setIsEditingProfile(false)}
                  >
                    Hủy bỏ
                  </button>
                  <button
                    type="submit"
                    className="btn-modal-save-profile"
                  >
                    <Save size={16} />
                    <span>Lưu thay đổi</span>
                  </button>
                </div>
              )}
            </form>
          )}

          {/* Tab 2: Security & Password */}
          {activeTab === 'security' && (
            <div className="security-form-sections-stack">
              {/* Change Password Card */}
              <div className="modal-section-card">
                <div className="section-head-row">
                  <div className="section-title-wrap">
                    <KeyRound size={16} className="text-purple-600" />
                    <h4 className="section-title-text">Đổi mật khẩu tài khoản</h4>
                  </div>
                </div>

                <form onSubmit={handleChangePassword} className="change-pass-modal-form">
                  <div className="pass-fields-col">
                    {/* Current Password */}
                    <div className="form-item-field">
                      <label className="item-label">Mật khẩu hiện tại</label>
                      <div className="password-box-relative">
                        <input
                          type={showCurrentPass ? 'text' : 'password'}
                          required
                          value={passwordForm.currentPassword}
                          onChange={(e) => setPasswordForm({ ...passwordForm, currentPassword: e.target.value })}
                          placeholder="Nhập mật khẩu hiện tại..."
                          className="modal-text-input pass-input-padding"
                        />
                        <button
                          type="button"
                          className="btn-eye-toggle"
                          onClick={() => setShowCurrentPass(!showCurrentPass)}
                        >
                          {showCurrentPass ? <EyeOff size={16} /> : <Eye size={16} />}
                        </button>
                      </div>
                    </div>

                    {/* New Password */}
                    <div className="form-item-field">
                      <label className="item-label">Mật khẩu mới</label>
                      <div className="password-box-relative">
                        <input
                          type={showNewPass ? 'text' : 'password'}
                          required
                          value={passwordForm.newPassword}
                          onChange={(e) => setPasswordForm({ ...passwordForm, newPassword: e.target.value })}
                          placeholder="Nhập mật khẩu mới (tối thiểu 8 ký tự)..."
                          className="modal-text-input pass-input-padding"
                        />
                        <button
                          type="button"
                          className="btn-eye-toggle"
                          onClick={() => setShowNewPass(!showNewPass)}
                        >
                          {showNewPass ? <EyeOff size={16} /> : <Eye size={16} />}
                        </button>
                      </div>

                      {passwordForm.newPassword && (
                        <div className="strength-meter-row">
                          <div className="strength-track">
                            <div 
                              className="strength-fill"
                              style={{ 
                                width: `${(passStrength.score / 3) * 100}%`,
                                backgroundColor: passStrength.color 
                              }}
                            />
                          </div>
                          <span className="strength-text" style={{ color: passStrength.color }}>
                            Độ mạnh: {passStrength.text}
                          </span>
                        </div>
                      )}
                    </div>

                    {/* Confirm Password */}
                    <div className="form-item-field">
                      <label className="item-label">Xác nhận mật khẩu mới</label>
                      <div className="password-box-relative">
                        <input
                          type={showConfirmPass ? 'text' : 'password'}
                          required
                          value={passwordForm.confirmPassword}
                          onChange={(e) => setPasswordForm({ ...passwordForm, confirmPassword: e.target.value })}
                          placeholder="Nhập lại mật khẩu mới..."
                          className="modal-text-input pass-input-padding"
                        />
                        <button
                          type="button"
                          className="btn-eye-toggle"
                          onClick={() => setShowConfirmPass(!showConfirmPass)}
                        >
                          {showConfirmPass ? <EyeOff size={16} /> : <Eye size={16} />}
                        </button>
                      </div>
                    </div>
                  </div>

                  <div className="pass-guidelines-box">
                    <span className="guideline-head">Quy chuẩn mật khẩu:</span>
                    <ul className="guideline-list">
                      <li className={passwordForm.newPassword.length >= 8 ? 'done' : ''}>Tối thiểu 8 ký tự</li>
                      <li className={/[A-Z]/.test(passwordForm.newPassword) ? 'done' : ''}>Có ít nhất 1 chữ in hoa (A-Z)</li>
                      <li className={/[0-9]/.test(passwordForm.newPassword) ? 'done' : ''}>Có ít nhất 1 chữ số (0-9)</li>
                      <li className={/[^A-Za-z0-9]/.test(passwordForm.newPassword) ? 'done' : ''}>Có ký tự đặc biệt (!@#$%^&*...)</li>
                    </ul>
                  </div>

                  <div className="pass-actions-row">
                    <button type="submit" className="btn-submit-new-pass">
                      <Lock size={15} />
                      <span>Cập nhật mật khẩu mới</span>
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
