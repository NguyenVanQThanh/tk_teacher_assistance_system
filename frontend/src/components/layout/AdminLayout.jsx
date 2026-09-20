// File Name: AdminLayout.jsx
// Description: Master layout wrapper for Admin portal with persistent sidebar, top navigation bar, and router Outlet.
// Created At: 2026-09-19
// Created By: Tam Khang
// Updated At: 2026-09-20
// Updated By: Tam Khang

import React, { useState, useRef, useEffect } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { 
  Home, 
  HelpCircle, 
  Bell, 
  User, 
  Menu, 
  X, 
  LogOut, 
  CheckCircle2, 
  ShieldAlert,
  ChevronDown,
  Search
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import AdminSidebar from '../admin/AdminSidebar';
import './AdminLayout.css';

export default function AdminLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);
  const [showNotifMenu, setShowNotifMenu] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const notifRef = useRef(null);
  const userRef = useRef(null);

  // Close dropdowns on outside click
  useEffect(() => {
    function handleClickOutside(event) {
      if (notifRef.current && !notifRef.current.contains(event.target)) {
        setShowNotifMenu(false);
      }
      if (userRef.current && !userRef.current.contains(event.target)) {
        setShowUserMenu(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const notifications = [
    {
      id: 1,
      title: '5 lần đăng nhập thất bại liên tiếp',
      time: '10 phút trước',
      type: 'warning',
      desc: 'IP: 118.70.12.91 đã bị tạm khóa bảo mật 30 phút'
    },
    {
      id: 2,
      title: 'Yêu cầu cấp tài khoản mới',
      time: '15 phút trước',
      type: 'info',
      desc: 'ThS. Lê Nguyên yêu cầu tài khoản Giảng viên'
    }
  ];

  const location = useLocation();
  const getSubBreadcrumb = () => {
    const path = location.pathname;
    if (path.startsWith('/admin/users')) return 'Quản lý người dùng';
    if (path.startsWith('/admin/classes')) return 'Quản lý trường lớp';
    if (path.startsWith('/admin/roles')) return 'Phân quyền & Vai trò';
    if (path.startsWith('/admin/reports')) return 'Báo cáo & Thống kê';
    if (path.startsWith('/admin/settings')) return 'Cài đặt hệ thống';
    return null;
  };
  const subBreadcrumb = getSubBreadcrumb();

  return (
    <div className="admin-layout-container">
      {/* Sidebar Navigation */}
      <AdminSidebar 
        isMobileOpen={isMobileSidebarOpen} 
        onCloseMobile={() => setIsMobileSidebarOpen(false)} 
      />

      {/* Mobile Backdrop */}
      {isMobileSidebarOpen && (
        <div 
          className="admin-sidebar-backdrop" 
          onClick={() => setIsMobileSidebarOpen(false)} 
        />
      )}

      {/* Main Content Area */}
      <div className="admin-main-wrapper">
        {/* Top Header Bar */}
        <header className="admin-topbar">
          <div className="admin-topbar-left">
            <button 
              type="button" 
              className="admin-mobile-toggle"
              onClick={() => setIsMobileSidebarOpen(prev => !prev)}
            >
              {isMobileSidebarOpen ? <X size={22} /> : <Menu size={22} />}
            </button>

            {/* Breadcrumbs */}
            <div className="admin-breadcrumb">
              <Home size={17} className="admin-breadcrumb-home" onClick={() => navigate('/admin')} style={{ cursor: 'pointer' }} />
              <span className="admin-breadcrumb-sep">/</span>
              <span 
                className="admin-breadcrumb-link" 
                onClick={() => navigate('/admin')}
                style={{ cursor: subBreadcrumb ? 'pointer' : 'default' }}
              >
                Quản trị hệ thống
              </span>
              {subBreadcrumb && (
                <>
                  <span className="admin-breadcrumb-sep">/</span>
                  <span className="admin-breadcrumb-current">{subBreadcrumb}</span>
                </>
              )}
            </div>
          </div>

          {/* Topbar Center Global Search */}
          <div className="admin-topbar-center">
            <div className="topbar-global-search">
              <Search size={15} className="topbar-search-icon" />
              <input 
                type="text" 
                placeholder="Tìm kiếm khối lớp, môn học, giáo viên..." 
                className="topbar-search-input"
              />
            </div>
          </div>

          <div className="admin-topbar-right">
            {/* Help Button */}
            <button 
              type="button" 
              className="admin-icon-btn" 
              title="Trung tâm hỗ trợ"
              onClick={() => alert('Trung tâm hướng dẫn quản trị viên SmartLMS')}
            >
              <HelpCircle size={20} strokeWidth={1.8} />
            </button>

            {/* Notifications Button & Dropdown */}
            <div className="admin-dropdown-wrapper" ref={notifRef}>
              <button 
                type="button" 
                className="admin-icon-btn" 
                title="Thông báo hệ thống"
                onClick={() => setShowNotifMenu(prev => !prev)}
              >
                <Bell size={20} strokeWidth={1.8} />
                <span className="admin-notif-badge">2</span>
              </button>

              {showNotifMenu && (
                <div className="admin-dropdown-menu admin-notif-menu">
                  <div className="admin-dropdown-header">
                    <span className="admin-dropdown-title">Thông báo hệ thống</span>
                    <span className="admin-notif-count-pill">2 mới</span>
                  </div>
                  <div className="admin-notif-list">
                    {notifications.map(item => (
                      <div key={item.id} className="admin-notif-item">
                        <div className={`admin-notif-icon-box ${item.type}`}>
                          {item.type === 'warning' ? <ShieldAlert size={16} /> : <CheckCircle2 size={16} />}
                        </div>
                        <div className="admin-notif-details">
                          <p className="admin-notif-title">{item.title}</p>
                          <p className="admin-notif-desc">{item.desc}</p>
                          <span className="admin-notif-time">{item.time}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className="admin-dropdown-footer">
                    <button type="button" onClick={() => setShowNotifMenu(false)}>
                      Đánh dấu tất cả đã đọc
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Admin User Profile Capsule */}
            <div className="admin-dropdown-wrapper" ref={userRef}>
              <div 
                className="admin-user-capsule" 
                onClick={() => setShowUserMenu(prev => !prev)}
              >
                <div className="admin-user-avatar">
                  <User size={18} strokeWidth={2.2} />
                </div>
                <div className="admin-user-info">
                  <span className="admin-user-name">Admin</span>
                  <span className="admin-user-role">Quản trị viên</span>
                </div>
                <ChevronDown size={14} className="admin-user-chevron" />
              </div>

              {showUserMenu && (
                <div className="admin-dropdown-menu admin-user-menu">
                  <div className="admin-user-menu-header">
                    <p className="admin-user-menu-fullname">{user?.full_name || 'Quản trị viên Hệ thống'}</p>
                    <p className="admin-user-menu-email">{user?.email || 'admin@school.com'}</p>
                  </div>
                  <div className="admin-user-menu-actions">
                    <button 
                      type="button" 
                      className="admin-user-menu-item"
                      onClick={() => {
                        setShowUserMenu(false);
                        navigate('/admin/settings');
                      }}
                    >
                      <User size={16} />
                      <span>Thông tin tài khoản</span>
                    </button>
                    <button 
                      type="button" 
                      className="admin-user-menu-item text-danger"
                      onClick={handleLogout}
                    >
                      <LogOut size={16} />
                      <span>Đăng xuất</span>
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </header>

        {/* Scrollable Main Content Container */}
        <main className="admin-content-viewport">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
