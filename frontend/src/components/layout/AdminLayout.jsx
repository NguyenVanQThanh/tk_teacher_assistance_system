// File Name: AdminLayout.jsx
// Description: Master layout wrapper for Admin portal with persistent sidebar, top navigation bar, and router Outlet.
// Created At: 2026-09-19
// Created By: Tam Khang
// Updated At: 2026-09-20
// Updated By: Tam Khang

import React, { useState, useRef, useEffect } from 'react';
import NotificationBell from '../common/NotificationBell';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { 
  Home, 
  HelpCircle, 
  User, 
  Menu, 
  X, 
  LogOut, 
  ChevronDown,
  Search
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import AdminSidebar from '../admin/AdminSidebar';
import './AdminLayout.css';
import toast from '../../components/common/toast';

export default function AdminLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const userRef = useRef(null);

  // Close dropdowns on outside click
  useEffect(() => {
    function handleClickOutside(event) {
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

  const location = useLocation();
  const getSubBreadcrumb = () => {
    const path = location.pathname;
    if (path.startsWith('/admin/users')) return 'Quản lý người dùng';
    if (path.startsWith('/admin/classes')) return 'Quản lý trường lớp';
    if (path.startsWith('/admin/subjects')) return 'Môn học & Tổ trưởng bộ môn';
    if (path.startsWith('/admin/roles')) return 'Phân quyền & Vai trò';
    if (path.startsWith('/admin/reports')) return 'Báo cáo & Thống kê';
    if (path.startsWith('/admin/monitoring')) return 'Giám sát hệ thống';
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
              onClick={() => toast.info('Trung tâm hướng dẫn quản trị viên SmartLMS')}
            >
              <HelpCircle size={20} strokeWidth={1.8} />
            </button>

            <NotificationBell />

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
