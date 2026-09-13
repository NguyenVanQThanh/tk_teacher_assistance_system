// File Name: StudentSidebar.jsx
// Description: Synchronized sidebar navigation component for Student role with dynamic route awareness and teacher sidebar parity.
// Created At: 2026-09-07
// Created By: Tam Khang
// Updated At: 2026-09-12
// Updated By: Tam Khang

import React from 'react';
import { 
  LayoutGrid, 
  ClipboardList, 
  Settings, 
  Sparkles,
  BookOpen,
  Calendar
} from 'lucide-react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import './StudentSidebar.css';

export default function StudentSidebar({ activeNav, onSelectNav }) {
  const { user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const displayName = user?.full_name ? `HS. ${user.full_name}` : 'HS. Nguyễn Hoàng Nam';
  const displayClass = user?.class_name || '12A1';
  const initial = user?.full_name 
    ? user.full_name.split(' ').map(n => n[0]).slice(-2).join('').toUpperCase() 
    : 'HN';

  // Automatically determine active navigation item from URL pathname if not explicitly passed
  let currentActive = activeNav;
  if (!currentActive) {
    const p = location.pathname;
    if (p === '/' || p === '/student' || p === '/student/dashboard') {
      currentActive = 'dashboard';
    } else if (p.startsWith('/student/exercises')) {
      currentActive = 'exercises';
    } else if (p.startsWith('/student/settings')) {
      currentActive = 'settings';
    } else {
      currentActive = 'dashboard';
    }
  }

  const handleActionClick = () => {
    navigate('/student/exercises');
  };

  const handleItemClick = (navId) => {
    if (onSelectNav) {
      onSelectNav(navId);
    }
    
    if (navId === 'dashboard') {
      navigate('/student');
    } else if (navId === 'exercises') {
      navigate('/student/exercises');
    } else if (navId === 'settings') {
      navigate('/student');
    }
  };

  const menuItems = [
    { id: 'dashboard', label: 'Bảng điều khiển', icon: LayoutGrid },
    { id: 'exercises', label: 'Kho bài tập', icon: ClipboardList },
  ];

  return (
    <aside className="student-sidebar">
      {/* Student Profile Section */}
      <div className="sidebar-profile-card">
        <div 
          className="avatar-wrapper" 
          onClick={() => navigate('/student')} 
          title="Xem thông tin cá nhân"
        >
          <div className="student-avatar">
            <span className="avatar-text">{initial}</span>
          </div>
        </div>
        <h3 
          className="student-name" 
          onClick={() => navigate('/student')}
          style={{ cursor: 'pointer' }}
          title="Xem thông tin cá nhân"
        >
          {displayName}
        </h3>
        <p className="student-school">Lớp {displayClass} • Trường THPT Chuyên</p>
      </div>

      {/* Quick Action Button */}
      <button 
        type="button" 
        className="btn-student-action" 
        onClick={handleActionClick}
        title="Vào luyện tập bài tập ngay"
      >
        <Sparkles size={16} strokeWidth={2.2} />
        <span>Luyện tập ngay</span>
      </button>

      {/* Navigation Links */}
      <nav className="sidebar-nav">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentActive === item.id;
          return (
            <button
              key={item.id}
              className={`nav-item-btn ${isActive ? 'active' : ''}`}
              onClick={() => handleItemClick(item.id)}
            >
              <Icon size={18} className="nav-icon" />
              <span className="nav-label">{item.label}</span>
            </button>
          );
        })}
      </nav>

      {/* Bottom Settings Link */}
      <div className="sidebar-bottom-actions">
        <button
          type="button"
          className={`nav-item-btn bottom-setting-btn ${currentActive === 'settings' ? 'active' : ''}`}
          onClick={() => handleItemClick('settings')}
        >
          <Settings size={18} className="nav-icon" />
          <span className="nav-label">Cài đặt</span>
        </button>
      </div>
    </aside>
  );
}
