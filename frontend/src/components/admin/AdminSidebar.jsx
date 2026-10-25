// File Name: AdminSidebar.jsx
// Description: Sidebar navigation component for the Admin portal matching the system design.
// Created At: 2026-09-19
// Created By: Tam Khang
// Updated At: 2026-09-20
// Updated By: Tam Khang

import React from 'react';
import { 
  LayoutGrid, 
  Users, 
  Building2, 
  ShieldCheck, 
  BarChart3, 
  HelpCircle, 
  LogOut,
  GraduationCap
} from 'lucide-react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import './AdminSidebar.css';

export default function AdminSidebar({ isMobileOpen, onCloseMobile }) {
  const navigate = useNavigate();
  const location = useLocation();
  const { logout } = useAuth();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const navItems = [
    {
      id: 'dashboard',
      label: 'Bảng điều khiển',
      enLabel: 'Dashboard',
      icon: LayoutGrid,
      path: '/admin',
    },
    {
      id: 'users',
      label: 'Quản lý người dùng',
      enLabel: 'User Management',
      icon: Users,
      path: '/admin/users',
    },
    {
      id: 'schools',
      label: 'Quản lý trường lớp',
      enLabel: 'School & Classes',
      icon: Building2,
      path: '/admin/classes',
    },
    {
      id: 'permissions',
      label: 'Phân quyền & Vai trò',
      enLabel: 'Roles & Permissions',
      icon: ShieldCheck,
      path: '/admin/roles',
    },
    {
      id: 'reports',
      label: 'Báo cáo & Thống kê',
      enLabel: 'Reports & Analytics',
      icon: BarChart3,
      path: '/admin/reports',
    },
  ];

  const handleNavClick = (path) => {
    navigate(path);
    if (onCloseMobile) {
      onCloseMobile();
    }
  };

  return (
    <aside className={`admin-sidebar ${isMobileOpen ? 'mobile-open' : ''}`}>
      {/* Brand Header */}
      <div className="admin-brand-block" onClick={() => handleNavClick('/admin')}>
        <div className="admin-brand-icon-wrapper">
          <GraduationCap className="admin-brand-icon" size={24} strokeWidth={2.2} />
        </div>
        <div className="admin-brand-text">
          <span className="admin-brand-name">Academic Clarity</span>
          <span className="admin-brand-tagline">Hệ thống quản trị LMS</span>
        </div>
      </div>

      {/* Main Navigation */}
      <div className="admin-nav-section">
        <div className="admin-nav-label">MENU QUẢN TRỊ</div>
        <nav className="admin-nav-list">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path || 
              (item.path === '/admin' && (location.pathname === '/admin/' || location.pathname === '/admin'));

            return (
              <button
                key={item.id}
                type="button"
                className={`admin-nav-item ${isActive ? 'active' : ''}`}
                onClick={() => handleNavClick(item.path)}
              >
                <Icon className="admin-nav-item-icon" size={20} strokeWidth={1.9} />
                <span className="admin-nav-item-text">{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Bottom Actions */}
      <div className="admin-sidebar-footer">
        <button
          type="button"
          className="admin-footer-btn"
          onClick={() => alert('Trung tâm Trợ giúp & Hỗ trợ kỹ thuật LMS')}
        >
          <HelpCircle size={19} strokeWidth={1.8} />
          <span>Trợ giúp & Hỗ trợ</span>
        </button>

        <button
          type="button"
          className="admin-footer-btn logout-btn"
          onClick={handleLogout}
        >
          <LogOut size={19} strokeWidth={1.8} />
          <span>Đăng xuất</span>
        </button>
      </div>
    </aside>
  );
}
