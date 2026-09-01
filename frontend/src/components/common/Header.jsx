// File Name: Header.jsx
// Description: Top global navigation header with search, notifications popup, and rich user account profile dropdown.
// Created At: 2026-08-30
// Created By: Tam Khang
// Updated At: 2026-09-01
// Updated By: Tam Khang

import React, { useState, useRef, useEffect } from 'react';
import { 
  Menu, 
  Search, 
  Bell, 
  HelpCircle, 
  User, 
  LogOut, 
  Settings, 
  Shield, 
  Mail, 
  Building2, 
  CheckCircle,
  ChevronRight
} from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import NotificationDropdown from './NotificationDropdown';
import TeacherProfileModal from '../teacher/TeacherProfileModal';
import './Header.css';

export default function Header({ onToggleSidebar }) {
  const { user, logout } = useAuth();
  const [showDropdown, setShowDropdown] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const [isProfileModalOpen, setIsProfileModalOpen] = useState(false);
  const [modalInitialTab, setModalInitialTab] = useState('profile');
  const navigate = useNavigate();

  const notifRef = useRef(null);
  const userMenuRef = useRef(null);

  // Close popups when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (notifRef.current && !notifRef.current.contains(event.target)) {
        setShowNotifications(false);
      }
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

  const displayName = user?.full_name ? `GV. ${user.full_name}` : 'GV. Giáo viên Mẫu';
  const displayEmail = user?.email || 'giaovien.mau@eduglobal.edu.vn';
  const displayRole = user?.role === 'Teacher' ? 'Giáo viên bộ môn Toán - Tin' : 'Giáo viên Chủ nhiệm';
  const initial = user?.full_name ? user.full_name.split(' ').map(n => n[0]).slice(-2).join('').toUpperCase() : 'GM';

  return (
    <>
      <header className="main-header">
        <div className="header-left">
          <button className="icon-btn menu-toggle" onClick={onToggleSidebar} aria-label="Toggle menu">
            <Menu size={20} />
          </button>
          <Link to="/teacher" className="brand-logo-link">
            <span className="brand-text">Academic Clarity</span>
          </Link>
        </div>

        <div className="header-right">
          {/* Search Bar */}
          <div className="header-search-box">
            <Search size={16} className="search-icon" />
            <input 
              type="text" 
              placeholder="Tìm kiếm..." 
              className="search-input" 
            />
          </div>

          {/* Notifications Popover */}
          <div style={{ position: 'relative' }} ref={notifRef}>
            <button 
              className="icon-btn notif-btn" 
              onClick={() => {
                setShowNotifications(!showNotifications);
                setShowDropdown(false);
              }} 
              aria-label="Notifications"
            >
              <Bell size={19} />
              <span className="notif-dot"></span>
            </button>

            {showNotifications && (
              <div style={{
                position: 'absolute',
                top: '46px',
                right: '-40px',
                zIndex: 100
              }}>
                <NotificationDropdown onClose={() => setShowNotifications(false)} />
              </div>
            )}
          </div>

          <button className="icon-btn" aria-label="Help">
            <HelpCircle size={19} />
          </button>

          {/* User Profile Avatar with dropdown */}
          <div style={{ position: 'relative' }} ref={userMenuRef}>
            <button 
              className="user-profile-btn" 
              onClick={() => {
                setShowDropdown(!showDropdown);
                setShowNotifications(false);
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
                    <span className="popover-role-badge">{displayRole}</span>
                    <div className="popover-meta-item">
                      <Mail size={11} className="popover-meta-icon" />
                      <span>{displayEmail}</span>
                    </div>
                    <div className="popover-meta-item">
                      <Building2 size={11} className="popover-meta-icon" />
                      <span>Trường THPT Chuyên • Khoa Tự Nhiên</span>
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

      {/* Interactive Teacher Profile & Security Modal */}
      <TeacherProfileModal
        isOpen={isProfileModalOpen}
        onClose={() => setIsProfileModalOpen(false)}
        defaultTab={modalInitialTab}
      />
    </>
  );
}
