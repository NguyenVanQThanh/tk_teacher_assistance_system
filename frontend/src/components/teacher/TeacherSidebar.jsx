// File Name: TeacherSidebar.jsx
// Description: Synchronized sidebar navigation component for Teacher role with dynamic route awareness.
// Created At: 2026-08-30
// Created By: Tam Khang
// Updated At: 2026-09-02
// Updated By: Tam Khang

import React from 'react';
import { 
  LayoutGrid, 
  GraduationCap, 
  Users,
  Star, 
  FolderOpen, 
  ClipboardList, 
  Calendar, 
  Settings, 
  Plus 
} from 'lucide-react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { getTeacherProfileDefaults } from '../../utils/teacherSubjectHelper';
import './TeacherSidebar.css';

export default function TeacherSidebar({ 
  activeNav, 
  onSelectNav, 
  onCreateAction,
  createButtonText = 'Tạo bài tập mới'
}) {
  const { user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const displayName = user?.full_name ? `GV. ${user.full_name}` : 'GV. Sample Teacher (Thầy Nguyễn Văn A)';
  const initial = user?.full_name ? user.full_name.split(' ').map(n => n[0]).slice(-2).join('').toUpperCase() : 'VA';

  // Automatically determine active navigation item from URL pathname if not explicitly passed
  let currentActive = activeNav;
  if (!currentActive) {
    const p = location.pathname;
    if (p === '/' || p === '/teacher') {
      currentActive = 'dashboard';
    } else if (p.startsWith('/teacher/classes')) {
      currentActive = 'classes';
    } else if (p.startsWith('/teacher/homeroom')) {
      currentActive = 'homeroom';
    } else if (p.startsWith('/teacher/grading')) {
      currentActive = 'grading';
    } else if (p.startsWith('/teacher/documents')) {
      currentActive = 'documents';
    } else if (p.startsWith('/teacher/exercises')) {
      currentActive = 'exercises';
    } else if (p.startsWith('/teacher/schedule')) {
      currentActive = 'schedule';
    } else if (p.startsWith('/teacher/profile')) {
      currentActive = 'settings';
    } else {
      currentActive = 'dashboard';
    }
  }

  const handleCreateClick = () => {
    if (onCreateAction) {
      onCreateAction();
    } else {
      navigate('/teacher/exercises');
    }
  };

  const handleItemClick = (navId) => {
    if (onSelectNav) {
      onSelectNav(navId);
    }
    
    // Synchronized hyperlinks across the entire system
    if (navId === 'dashboard') {
      navigate('/teacher');
    } else if (navId === 'classes') {
      navigate('/teacher/classes');
    } else if (navId === 'homeroom') {
      navigate('/teacher/homeroom');
    } else if (navId === 'grading') {
      navigate('/teacher/grading');
    } else if (navId === 'documents') {
      navigate('/teacher/documents');
    } else if (navId === 'exercises') {
      navigate('/teacher/exercises');
    } else if (navId === 'schedule') {
      navigate('/teacher/schedule');
    } else if (navId === 'settings') {
      navigate('/teacher/profile');
    }
  };

  const teacherDefaults = getTeacherProfileDefaults(user);
  const isHomeroomTeacher = user?.role === 'HomeroomTeacher' || user?.is_homeroom_teacher || teacherDefaults.isHomeroom;

  const menuItems = [
    { id: 'dashboard', label: 'Bảng điều khiển', icon: LayoutGrid },
    { id: 'classes', label: 'Lớp học của tôi', icon: GraduationCap },
    ...(isHomeroomTeacher ? [{ id: 'homeroom', label: 'Lớp chủ nhiệm', icon: Users }] : []),
    { id: 'grading', label: 'Chấm bài & Phản hồi', icon: Star },
    { id: 'documents', label: 'Kho tài liệu', icon: FolderOpen },
    { id: 'exercises', label: 'Kho bài tập', icon: ClipboardList },
    { id: 'schedule', label: 'Lịch giảng dạy', icon: Calendar }
  ];

  return (
    <aside className="teacher-sidebar">
      {/* Teacher Profile Section */}
      <div className="sidebar-profile-card">
        <div 
          className="avatar-wrapper" 
          onClick={() => navigate('/teacher/profile')} 
          title="Xem thông tin cá nhân"
        >
          <div className="teacher-avatar">
            <span className="avatar-text">{initial}</span>
          </div>
        </div>
        <h3 
          className="teacher-name" 
          onClick={() => navigate('/teacher/profile')}
          style={{ cursor: 'pointer' }}
          title="Xem thông tin cá nhân"
        >
          {displayName}
        </h3>
        <p className="teacher-school">Trường THPT Chuyên</p>
      </div>

      {/* Create Action Button */}
      <button 
        type="button" 
        className="btn-create-exercise" 
        onClick={handleCreateClick}
        title={createButtonText}
      >
        <Plus size={17} strokeWidth={2.5} />
        <span>{createButtonText}</span>
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
