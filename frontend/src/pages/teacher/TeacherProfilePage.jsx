// File Name: TeacherProfilePage.jsx
// Description: Teacher Profile and Security Settings page with tabs for Personal Information and Password/Security Management.
// Created At: 2026-09-01
// Created By: Tam Khang
// Updated At: 2026-09-01
// Updated By: Tam Khang

import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { 
  User, 
  Shield, 
  Mail, 
  Phone, 
  MapPin, 
  Building2, 
  GraduationCap, 
  Calendar, 
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
  XCircle,
  AlertCircle,
  Loader2
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { getTeacherProfileDefaults } from '../../utils/teacherSubjectHelper';
import { authApi } from '../../services/api';
import './TeacherProfilePage.css';

export default function TeacherProfilePage() {
  const { user } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();

  const profileDefaults = getTeacherProfileDefaults(user);

  // Active tab: 'profile' (Hồ sơ & Thông tin cá nhân) or 'security' (Bảo mật & Đổi mật khẩu)
  const initialTab = searchParams.get('tab') === 'security' ? 'security' : 'profile';
  const [activeTab, setActiveTab] = useState(initialTab);

  // Sync tab with URL
  useEffect(() => {
    const tabParam = searchParams.get('tab');
    if (tabParam === 'security') {
      setActiveTab('security');
    } else {
      setActiveTab('profile');
    }
  }, [searchParams]);

  const handleTabChange = (tabName) => {
    setActiveTab(tabName);
    setSearchParams({ tab: tabName });
  };

  // Toast notification
  const [toastMessage, setToastMessage] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);
  const [isChangingPass, setIsChangingPass] = useState(false);

  // --- Profile Info State ---
  const [isEditingProfile, setIsEditingProfile] = useState(false);
  const [profileForm, setProfileForm] = useState({
    fullName: user?.full_name || 'Giáo viên',
    title: 'GV.',
    gender: 'Nam',
    dob: '1985-08-15',
    citizenId: '001085012345',
    email: user?.email || '',
    phone: user?.phone || '',
    address: 'Số 144 Xuân Thủy, Cầu Giấy, Hà Nội',
    school: 'Trường THPT Chuyên',
    department: profileDefaults.department,
    position: profileDefaults.position,
    degree: profileDefaults.degree,
    startYear: '2015',
    teacherCode: profileDefaults.teacherCode
  });

  // Load and re-sync profile form from API and AuthContext
  useEffect(() => {
    let isMounted = true;
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

    async function loadMe() {
      try {
        const me = await authApi.getMe();
        if (isMounted && me) {
          const defs = getTeacherProfileDefaults(me);
          setProfileForm(prev => ({
            ...prev,
            fullName: me.full_name || prev.fullName,
            email: me.email || prev.email,
            phone: me.phone || prev.phone,
            department: defs.department,
            position: me.role ? `Giáo viên (${me.role})` : defs.position,
            degree: defs.degree,
            teacherCode: defs.teacherCode
          }));
        }
      } catch (err) {
        // Fallback to auth context
      }
    }
    loadMe();

    return () => {
      isMounted = false;
    };
  }, [user]);

  // --- Security & Password State ---
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
  const handleSaveProfile = async (e) => {
    e.preventDefault();
    try {
      await authApi.updateProfile({
        full_name: profileForm.fullName,
        email: profileForm.email,
        phone: profileForm.phone
      });
      setIsEditingProfile(false);
      setToastMessage('Đã cập nhật thông tin hồ sơ cá nhân thành công!');
    } catch (err) {
      setToastMessage('Lỗi khi cập nhật hồ sơ cá nhân.');
    }
    setTimeout(() => setToastMessage(null), 3500);
  };

  // Change password
  const handleChangePassword = async (e) => {
    e.preventDefault();
    setErrorMessage(null);
    if (!passwordForm.currentPassword || !passwordForm.newPassword || !passwordForm.confirmPassword) {
      setErrorMessage('Vui lòng điền đầy đủ các trường mật khẩu.');
      return;
    }
    if (passwordForm.newPassword !== passwordForm.confirmPassword) {
      setErrorMessage('Mật khẩu mới và xác nhận mật khẩu không khớp!');
      return;
    }
    if (passwordForm.newPassword.length < 8) {
      setErrorMessage('Mật khẩu mới phải có ít nhất 8 ký tự!');
      return;
    }

    try {
      setIsChangingPass(true);
      await authApi.changePassword({
        old_password: passwordForm.currentPassword,
        new_password: passwordForm.newPassword,
      });

      setPasswordForm({
        currentPassword: '',
        newPassword: '',
        confirmPassword: ''
      });
      setToastMessage('Đã đổi mật khẩu thành công! Vui lòng sử dụng mật khẩu mới cho lần đăng nhập tiếp theo.');
      setTimeout(() => setToastMessage(null), 4000);
    } catch (err) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'string' ? detail : detail?.message || 'Không thể đổi mật khẩu. Vui lòng kiểm tra lại mật khẩu hiện tại.';
      setErrorMessage(msg);
    } finally {
      setIsChangingPass(false);
    }
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
    <div className="profile-content-container">
          {/* Toast Notification */}
          {toastMessage && (
            <div className="profile-toast-alert">
              <CheckCircle2 size={16} />
              <span>{toastMessage}</span>
            </div>
          )}

          {/* Breadcrumb Header */}
          <div className="profile-page-header">
            <div className="profile-breadcrumb">
              <span className="crumb-root" onClick={() => navigate('/teacher')}>Trang chủ</span>
              <span className="crumb-sep">›</span>
              <span className="crumb-current">
                {activeTab === 'profile' ? 'Hồ sơ & Thông tin cá nhân' : 'Bảo mật & Đổi mật khẩu'}
              </span>
            </div>
            <h1 className="profile-main-title">
              {activeTab === 'profile' ? 'Hồ sơ & Thông tin cá nhân' : 'Bảo mật & Đổi mật khẩu'}
            </h1>
          </div>

          {/* Profile Main Banner Card */}
          <div className="teacher-hero-profile-card">
            <div className="hero-avatar-wrap">
              <div className="hero-avatar-circle">
                <span>{initial}</span>
              </div>
              <button 
                type="button" 
                className="btn-camera-upload" 
                title="Thay đổi ảnh đại diện"
                onClick={() => alert('Chọn ảnh mới từ thiết bị của bạn')}
              >
                <Camera size={15} />
              </button>
            </div>

            <div className="hero-info-col">
              <div className="hero-name-row">
                <h2 className="hero-teacher-name">{profileForm.title} {profileForm.fullName}</h2>
                <span className="hero-status-tag">Đang công tác</span>
              </div>
              <div className="hero-meta-grid">
                <span className="hero-meta-pill">
                  <GraduationCap size={13} /> {profileForm.position}
                </span>
                <span className="hero-meta-pill">
                  <Building2 size={13} /> {profileForm.school}
                </span>
                <span className="hero-meta-pill code-pill">
                  <BadgeCheck size={13} /> Mã GV: {profileForm.teacherCode}
                </span>
              </div>
            </div>

            <div className="hero-action-col">
              {activeTab === 'profile' && !isEditingProfile && (
                <button 
                  type="button" 
                  className="btn-edit-profile-action"
                  onClick={() => setIsEditingProfile(true)}
                >
                  <Edit3 size={15} />
                  <span>Chỉnh sửa hồ sơ</span>
                </button>
              )}
            </div>
          </div>

          {/* Tab Selection Bar */}
          <div className="profile-tabs-nav-bar">
            <button
              type="button"
              className={`profile-tab-btn ${activeTab === 'profile' ? 'active' : ''}`}
              onClick={() => handleTabChange('profile')}
            >
              <User size={16} />
              <span>Hồ sơ & Thông tin cá nhân</span>
            </button>

            <button
              type="button"
              className={`profile-tab-btn ${activeTab === 'security' ? 'active' : ''}`}
              onClick={() => handleTabChange('security')}
            >
              <Shield size={16} />
              <span>Bảo mật & Đổi mật khẩu</span>
            </button>
          </div>

          {/* Tab 1: Personal Information */}
          {activeTab === 'profile' && (
            <form onSubmit={handleSaveProfile} className="profile-tab-content">
              {/* Card 1: Thông tin cơ bản */}
              <div className="profile-section-card">
                <div className="section-card-header">
                  <div className="section-title-wrap">
                    <User size={18} className="section-header-icon" />
                    <h3 className="section-card-title">Thông tin cơ bản</h3>
                  </div>
                  {isEditingProfile && (
                    <span className="editing-indicator-badge">Đang chỉnh sửa</span>
                  )}
                </div>

                <div className="profile-form-grid-3">
                  <div className="profile-field-item">
                    <label className="field-title">Họ và tên</label>
                    <input
                      type="text"
                      disabled={!isEditingProfile}
                      value={profileForm.fullName}
                      onChange={(e) => setProfileForm({ ...profileForm, fullName: e.target.value })}
                      className="profile-input-control"
                    />
                  </div>

                  <div className="profile-field-item">
                    <label className="field-title">Giới tính</label>
                    <select
                      disabled={!isEditingProfile}
                      value={profileForm.gender}
                      onChange={(e) => setProfileForm({ ...profileForm, gender: e.target.value })}
                      className="profile-input-control"
                    >
                      <option value="Nam">Nam</option>
                      <option value="Nữ">Nữ</option>
                      <option value="Khác">Khác</option>
                    </select>
                  </div>

                  <div className="profile-field-item">
                    <label className="field-title">Ngày sinh</label>
                    <input
                      type="date"
                      disabled={!isEditingProfile}
                      value={profileForm.dob}
                      onChange={(e) => setProfileForm({ ...profileForm, dob: e.target.value })}
                      className="profile-input-control"
                    />
                  </div>

                  <div className="profile-field-item">
                    <label className="field-title">Số CCCD / CMND</label>
                    <input
                      type="text"
                      disabled={!isEditingProfile}
                      value={profileForm.citizenId}
                      onChange={(e) => setProfileForm({ ...profileForm, citizenId: e.target.value })}
                      className="profile-input-control"
                    />
                  </div>

                  <div className="profile-field-item">
                    <label className="field-title">Mã số giáo viên</label>
                    <input
                      type="text"
                      disabled
                      value={profileForm.teacherCode}
                      className="profile-input-control readonly-input"
                    />
                  </div>
                </div>
              </div>

              {/* Card 2: Thông tin liên hệ */}
              <div className="profile-section-card">
                <div className="section-card-header">
                  <div className="section-title-wrap">
                    <Mail size={18} className="section-header-icon" />
                    <h3 className="section-card-title">Thông tin liên hệ</h3>
                  </div>
                </div>

                <div className="profile-form-grid-3">
                  <div className="profile-field-item">
                    <label className="field-title">Email công vụ</label>
                    <input
                      type="email"
                      disabled={!isEditingProfile}
                      value={profileForm.email}
                      onChange={(e) => setProfileForm({ ...profileForm, email: e.target.value })}
                      className="profile-input-control"
                    />
                  </div>

                  <div className="profile-field-item">
                    <label className="field-title">Số điện thoại</label>
                    <input
                      type="tel"
                      disabled={!isEditingProfile}
                      value={profileForm.phone}
                      onChange={(e) => setProfileForm({ ...profileForm, phone: e.target.value })}
                      className="profile-input-control"
                    />
                  </div>

                  <div className="profile-field-item">
                    <label className="field-title">Địa chỉ thường trú</label>
                    <input
                      type="text"
                      disabled={!isEditingProfile}
                      value={profileForm.address}
                      onChange={(e) => setProfileForm({ ...profileForm, address: e.target.value })}
                      className="profile-input-control"
                    />
                  </div>
                </div>
              </div>

              {/* Card 3: Thông tin công tác & Chuyên môn */}
              <div className="profile-section-card">
                <div className="section-head-row">
                  <div className="section-title-wrap">
                    <GraduationCap size={18} className="section-header-icon" />
                    <h3 className="section-card-title">Thông tin công tác & Chuyên môn</h3>
                  </div>
                </div>

                <div className="profile-form-grid-3">
                  <div className="profile-field-item">
                    <label className="field-title">Đơn vị công tác</label>
                    <input
                      type="text"
                      disabled={!isEditingProfile}
                      value={profileForm.school}
                      onChange={(e) => setProfileForm({ ...profileForm, school: e.target.value })}
                      className="profile-input-control"
                    />
                  </div>

                  <div className="profile-field-item">
                    <label className="field-title">Tổ chuyên môn</label>
                    <input
                      type="text"
                      disabled={!isEditingProfile}
                      value={profileForm.department}
                      onChange={(e) => setProfileForm({ ...profileForm, department: e.target.value })}
                      className="profile-input-control"
                    />
                  </div>

                  <div className="profile-field-item">
                    <label className="field-title">Vị trí / Nhiệm vụ</label>
                    <input
                      type="text"
                      disabled={!isEditingProfile}
                      value={profileForm.position}
                      onChange={(e) => setProfileForm({ ...profileForm, position: e.target.value })}
                      className="profile-input-control"
                    />
                  </div>

                  <div className="profile-field-item">
                    <label className="field-title">Trình độ đào tạo</label>
                    <input
                      type="text"
                      disabled={!isEditingProfile}
                      value={profileForm.degree}
                      onChange={(e) => setProfileForm({ ...profileForm, degree: e.target.value })}
                      className="profile-input-control"
                    />
                  </div>

                  <div className="profile-field-item">
                    <label className="field-title">Năm bắt đầu công tác</label>
                    <input
                      type="number"
                      disabled={!isEditingProfile}
                      value={profileForm.startYear}
                      onChange={(e) => setProfileForm({ ...profileForm, startYear: e.target.value })}
                      className="profile-input-control"
                    />
                  </div>
                </div>
              </div>

              {/* Bottom Floating Save Actions */}
              {isEditingProfile && (
                <div className="profile-bottom-actions-row">
                  <button
                    type="button"
                    className="btn-profile-cancel"
                    onClick={() => setIsEditingProfile(false)}
                  >
                    Hủy bỏ
                  </button>
                  <button
                    type="submit"
                    className="btn-profile-save"
                  >
                    <Save size={16} />
                    <span>Lưu thay đổi hồ sơ</span>
                  </button>
                </div>
              )}
            </form>
          )}

          {/* Tab 2: Security & Password Management */}
          {activeTab === 'security' && (
            <div className="security-tab-content">
              {/* Change Password Card */}
              <div className="profile-section-card">
                <div className="section-card-header">
                  <div className="section-title-wrap">
                    <KeyRound size={18} className="section-header-icon" />
                    <h3 className="section-card-title">Đổi mật khẩu tài khoản</h3>
                  </div>
                </div>

                <form onSubmit={handleChangePassword} className="change-password-form">
                  <div className="security-fields-stack">
                    {/* Current Password */}
                    <div className="security-field-item">
                      <label className="field-title">Mật khẩu hiện tại</label>
                      <div className="password-input-wrapper">
                        <input
                          type={showCurrentPass ? 'text' : 'password'}
                          required
                          value={passwordForm.currentPassword}
                          onChange={(e) => setPasswordForm({ ...passwordForm, currentPassword: e.target.value })}
                          placeholder="Nhập mật khẩu hiện tại..."
                          className="profile-input-control pass-input"
                        />
                        <button
                          type="button"
                          className="btn-toggle-eye"
                          onClick={() => setShowCurrentPass(!showCurrentPass)}
                        >
                          {showCurrentPass ? <EyeOff size={16} /> : <Eye size={16} />}
                        </button>
                      </div>
                    </div>

                    {/* New Password */}
                    <div className="security-field-item">
                      <label className="field-title">Mật khẩu mới</label>
                      <div className="password-input-wrapper">
                        <input
                          type={showNewPass ? 'text' : 'password'}
                          required
                          value={passwordForm.newPassword}
                          onChange={(e) => setPasswordForm({ ...passwordForm, newPassword: e.target.value })}
                          placeholder="Nhập mật khẩu mới (ít nhất 8 ký tự)..."
                          className="profile-input-control pass-input"
                        />
                        <button
                          type="button"
                          className="btn-toggle-eye"
                          onClick={() => setShowNewPass(!showNewPass)}
                        >
                          {showNewPass ? <EyeOff size={16} /> : <Eye size={16} />}
                        </button>
                      </div>

                      {/* Password Strength Meter */}
                      {passwordForm.newPassword && (
                        <div className="password-strength-box">
                          <div className="strength-bar-track">
                            <div 
                              className="strength-bar-fill" 
                              style={{ 
                                width: `${(passStrength.score / 3) * 100}%`,
                                backgroundColor: passStrength.color 
                              }} 
                            />
                          </div>
                          <span className="strength-label" style={{ color: passStrength.color }}>
                            Độ mạnh: {passStrength.text}
                          </span>
                        </div>
                      )}
                    </div>

                    {/* Confirm Password */}
                    <div className="security-field-item">
                      <label className="field-title">Xác nhận mật khẩu mới</label>
                      <div className="password-input-wrapper">
                        <input
                          type={showConfirmPass ? 'text' : 'password'}
                          required
                          value={passwordForm.confirmPassword}
                          onChange={(e) => setPasswordForm({ ...passwordForm, confirmPassword: e.target.value })}
                          placeholder="Nhập lại mật khẩu mới..."
                          className="profile-input-control pass-input"
                        />
                        <button
                          type="button"
                          className="btn-toggle-eye"
                          onClick={() => setShowConfirmPass(!showConfirmPass)}
                        >
                          {showConfirmPass ? <EyeOff size={16} /> : <Eye size={16} />}
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* Password Requirements Guide */}
                  <div className="password-guidelines-box">
                    <span className="guide-heading">Quy định bảo mật mật khẩu:</span>
                    <ul className="guide-bullets-list">
                      <li className={passwordForm.newPassword.length >= 8 ? 'fulfilled' : ''}>
                        Độ dài tối thiểu 8 ký tự
                      </li>
                      <li className={/[A-Z]/.test(passwordForm.newPassword) ? 'fulfilled' : ''}>
                        Có ít nhất 1 chữ in hoa (A-Z)
                      </li>
                      <li className={/[0-9]/.test(passwordForm.newPassword) ? 'fulfilled' : ''}>
                        Có ít nhất 1 chữ số (0-9)
                      </li>
                      <li className={/[^A-Za-z0-9]/.test(passwordForm.newPassword) ? 'fulfilled' : ''}>
                        Có ít nhất 1 ký tự đặc biệt (!@#$%^&*...)
                      </li>
                    </ul>
                  </div>

                  {/* Error Alert */}
                  {errorMessage && (
                    <div style={{ marginTop: '16px', padding: '10px 14px', background: '#FEF2F2', border: '1px solid #FCA5A5', borderRadius: '8px', color: '#991B1B', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <AlertCircle size={16} />
                      <span>{errorMessage}</span>
                    </div>
                  )}

                  <div className="password-actions-bar">
                    <button type="submit" className="btn-update-password" disabled={isChangingPass}>
                      {isChangingPass ? (
                        <>
                          <Loader2 size={16} className="animate-spin" />
                          <span>Đang cập nhật...</span>
                        </>
                      ) : (
                        <>
                          <Lock size={16} />
                          <span>Cập nhật mật khẩu mới</span>
                        </>
                      )}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}
        </div>
  );
}
