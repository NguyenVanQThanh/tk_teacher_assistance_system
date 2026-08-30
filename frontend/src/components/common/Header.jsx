// File Name: Header.jsx
// Description: Top global navigation header with search, notifications popup, and user logout menu.
// Created At: 2026-08-30
// Created By: Tam Khang
// Updated At: 2026-08-30
// Updated By: Tam Khang

import React, { useState, useRef, useEffect } from 'react';
import { Menu, Search, Bell, HelpCircle, User, LogOut } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import NotificationDropdown from './NotificationDropdown';
import './Header.css';

export default function Header({ onToggleSidebar }) {
  const { user, logout } = useAuth();
  const [showDropdown, setShowDropdown] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
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

  return (
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
            title={user?.full_name || 'Tài khoản'}
            style={{ background: 'none', border: 'none', cursor: 'pointer' }}
          >
            <div className="user-avatar-placeholder">
              <User size={18} />
            </div>
          </button>

          {showDropdown && (
            <div style={{
              position: 'absolute',
              top: '46px',
              right: '0px',
              width: '200px',
              backgroundColor: '#FFFFFF',
              borderRadius: '12px',
              boxShadow: '0 10px 25px rgba(0,0,0,0.1)',
              border: '1px solid #EBE8F0',
              padding: '8px',
              zIndex: 100,
              fontFamily: 'Be Vietnam Pro, sans-serif'
            }}>
              <div style={{ padding: '8px 12px', borderBottom: '1px solid #F1F3F7' }}>
                <p style={{ fontSize: '13px', fontWeight: 700, color: '#1D1928', margin: 0 }}>
                  {user?.full_name || 'Giáo viên'}
                </p>
                <p style={{ fontSize: '11px', color: '#64748B', margin: '2px 0 0' }}>
                  {user?.role || 'Teacher'}
                </p>
              </div>
              <button
                onClick={handleLogout}
                style={{
                  width: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '8px 12px',
                  fontSize: '13px',
                  color: '#DC2626',
                  background: 'none',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  marginTop: '4px',
                  fontFamily: 'inherit',
                  fontWeight: 600,
                  textAlign: 'left'
                }}
                onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#FEF2F2'}
                onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
              >
                <LogOut size={16} />
                <span>Đăng xuất</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
