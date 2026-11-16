// File Name: StudentHeader.jsx
// Description: Top global navigation header for Student portal matching teacher header aesthetics with brand logo, notifications, and rich user profile popover.
// Created At: 2026-09-07
// Created By: Tam Khang
// Updated At: 2026-09-12
// Updated By: Tam Khang

import React, { useState, useRef, useEffect } from 'react';
import { 
  Menu, 
  HelpCircle, 
  User, 
  LogOut, 
  Shield, 
  Mail, 
  GraduationCap, 
  ChevronRight
} from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import NotificationBell from '../common/NotificationBell';
import TeacherProfileModal from '../teacher/TeacherProfileModal';
import './StudentHeader.css';

export default function StudentHeader({ onToggleSidebar }) {
  const { user, logout } = useAuth();
  const [showDropdown, setShowDropdown] = useState(false);
  const [isProfileModalOpen, setIsProfileModalOpen] = useState(false);
  const [modalInitialTab, setModalInitialTab] = useState('profile');
  const navigate = useNavigate();

  const userMenuRef = useRef(null);

  // Close popups when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target)) {
        setShowDropdown(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const displayName = user?.full_name ? `HS. ${user.full_name}` : 'HS. Nguyễn Hoàng Nam';
  const displayEmail = user?.email || 'student01@school.com';
  const displayClass = user?.is_guest ? 'Khách' : (user?.class_name || '12A1');
  const initial = user?.full_name 
    ? user.full_name.split(' ').map(n => n[0]).slice(-2).join('').toUpperCase() 
    : 'HN';

  return (
    <>
      <header className="student-main-header">
        <div className="header-left">
          {onToggleSidebar && (
            <button className="icon-btn menu-toggle" onClick={onToggleSidebar} aria-label="Toggle menu">
              <Menu size={20} />
            </button>
          )}
          <Link to="/student" className="brand-logo-link">
            <span className="brand-text">Academic Clarity</span>
          </Link>
        </div>

        <div className="header-right">
          {/* Notifications Popover */}
          <NotificationBell />

          <button className="icon-btn" aria-label="Help" title="Trợ giúp & Hướng dẫn">
            <HelpCircle size={19} />
          </button>

          {/* User Profile Avatar with dropdown */}
          <div style={{ position: 'relative' }} ref={userMenuRef}>
            <button 
              className="user-profile-btn" 
              onClick={() => {
                setShowDropdown(!showDropdown);
              }}
              title={displayName}
            >
              <div className="user-avatar-placeholder">
                <span className="header-avatar-initial">{initial}</span>
                <span className="header-online-status-dot" />
              </div>
            </button>

            {showDropdown && (
              <div className="header-account-menu-popover">
                {/* Profile Card Header */}
                <div className="account-popover-head">
                  <div className="popover-avatar-circle">
                    <span>{initial}</span>
                  </div>
                  <div className="popover-user-info">
                    <h4 className="popover-user-name">{displayName}</h4>
                    <span className="popover-role-badge">Học sinh</span>
                    <div className="popover-meta-item">
                      <Mail size={11} className="popover-meta-icon" />
                      <span>{displayEmail}</span>
                    </div>
                    <div className="popover-meta-item">
                      <GraduationCap size={11} className="popover-meta-icon" />
                      <span>{user?.is_guest ? 'Học sinh khách' : `Lớp ${displayClass}`} • Trường THPT Chuyên</span>
                    </div>
                  </div>
                </div>

                {/* Quick Actions List */}
                <div className="account-menu-actions-list">
                  <button 
                    type="button" 
                    className="account-menu-item"
                    onClick={() => {
                      setModalInitialTab('profile');
                      setIsProfileModalOpen(true);
                      setShowDropdown(false);
                    }}
                  >
                    <div className="menu-item-left">
                      <User size={15} className="menu-item-icon" />
                      <span>Hồ sơ & Thông tin cá nhân</span>
                    </div>
                    <ChevronRight size={13} className="menu-item-arrow" />
                  </button>

                  <button 
                    type="button" 
                    className="account-menu-item"
                    onClick={() => {
                      setModalInitialTab('security');
                      setIsProfileModalOpen(true);
                      setShowDropdown(false);
                    }}
                  >
                    <div className="menu-item-left">
                      <Shield size={15} className="menu-item-icon" />
                      <span>Bảo mật & Đổi mật khẩu</span>
                    </div>
                    <ChevronRight size={13} className="menu-item-arrow" />
                  </button>

                  <div className="account-menu-divider" />

                  <button
                    type="button"
                    onClick={handleLogout}
                    className="account-menu-item item-logout"
                  >
                    <div className="menu-item-left">
                      <LogOut size={15} />
                      <span>Đăng xuất tài khoản</span>
                    </div>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Interactive Profile & Security Modal */}
      <TeacherProfileModal
        isOpen={isProfileModalOpen}
        onClose={() => setIsProfileModalOpen(false)}
        defaultTab={modalInitialTab}
      />
    </>
  );
}
