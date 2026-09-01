// File Name: TeacherSidebar.jsx
// Description: Sidebar navigation component for Teacher role with dynamic route support.
// Created At: 2026-08-30
// Created By: Tam Khang
// Updated At: 2026-09-01
// Updated By: Tam Khang

import React from 'react';
import { 
  LayoutDashboard, 
  GraduationCap, 
  Users, 
  Star, 
  FolderOpen, 
  BookOpen, 
  Calendar, 
  Settings, 
  Plus 
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import './TeacherSidebar.css';

export default function TeacherSidebar({ 
  activeNav = 'dashboard', 
  onSelectNav, 
  onCreateAction,
  createButtonText = 'Tạo bài tập'
}) {
  const { user } = useAuth();
  const navigate = useNavigate();
  const displayName = user?.full_name ? `GV. ${user.full_name}` : 'GV. Nguyễn Văn A';
  const initial = user?.full_name ? user.full_name.split(' ').map(n => n[0]).slice(-2).join('').toUpperCase() : 'NA';

  const handleCreateClick = () => {
    if (onCreateAction) {
      onCreateAction();
    } else if (activeNav === 'classes') {
      alert('Tạo lớp học mới');
    } else {
      navigate('/teacher/exercises');
    }
  };

  const handleItemClick = (navId) => {
    if (onSelectNav) {
      onSelectNav(navId);
    }
    
    // Always route if not overridden or handled
    if (navId === 'dashboard') {
      navigate('/teacher');
    } else if (navId === 'classes') {
      navigate('/teacher/classes');
    } else if (navId === 'homeroom') {
      navigate('/teacher/homeroom');
    } else if (navId === 'documents') {
      navigate('/teacher/documents');
    } else if (navId === 'exercises') {
      navigate('/teacher/exercises');
    }
  };

  const menuItems = [
    { id: 'dashboard', label: 'Bảng điều khiển', icon: LayoutDashboard },
    { id: 'classes', label: 'Lớp học của tôi', icon: GraduationCap },
    { id: 'homeroom', label: 'Lớp chủ nhiệm', icon: Users },
    { id: 'grading', label: 'Chấm bài & Phản hồi', icon: Star },
    { id: 'documents', label: 'Kho tài liệu', icon: FolderOpen },
    { id: 'exercises', label: 'Kho bài tập', icon: BookOpen },
    { id: 'schedule', label: 'Lịch giảng dạy', icon: Calendar },
    { id: 'settings', label: 'Cài đặt', icon: Settings },
  ];

  return (
    <aside className="teacher-sidebar">
      {/* Teacher Profile Section */}
      <div className="sidebar-profile-card">
        <div className="avatar-wrapper">
          <div className="teacher-avatar">
            <span className="avatar-text">{initial}</span>
          </div>
        </div>
        <h3 className="teacher-name">{displayName}</h3>
        <p className="teacher-school">{user?.role === 'Teacher' ? 'Giáo viên bộ môn' : 'Trường THPT Chuyên'}</p>
      </div>

      {/* Create Action Button */}
      <button 
        type="button" 
        className="btn-create-exercise" 
        onClick={handleCreateClick}
        title={createButtonText}
      >
        <Plus size={18} strokeWidth={2.5} />
        <span>{createButtonText}</span>
      </button>

      {/* Navigation Links */}
      <nav className="sidebar-nav">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeNav === item.id;
          return (
            <button
              key={item.id}
              className={`nav-item-btn ${isActive ? 'active' : ''}`}
              onClick={() => handleItemClick(item.id)}
            >
              <Icon size={19} className="nav-icon" />
              <span className="nav-label">{item.label}</span>
            </button>
          );
        })}
      </nav>
    </aside>
  );
}


