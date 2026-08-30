// File Name: NotificationDropdown.jsx
// Description: Notification dropdown popover matching Academic Clarity design specifications.
// Created At: 2026-08-30
// Created By: Tam Khang
// Updated At: 2026-08-30
// Updated By: Tam Khang

import React, { useState } from 'react';
import { MessageSquare, Settings, CheckSquare } from 'lucide-react';
import './NotificationDropdown.css';

export default function NotificationDropdown({ onClose }) {
  const [notifications, setNotifications] = useState([
    {
      id: 1,
      type: 'qa',
      title: 'Giải đáp thắc mắc',
      content: 'Học sinh Lê Minh đã yêu cầu giải đáp thắc mắc về bài tập Hóa học.',
      time: '15 phút trước',
      unread: true,
      icon: MessageSquare,
      iconTheme: 'purple',
    },
    {
      id: 2,
      type: 'system',
      title: 'Bảo trì hệ thống',
      content: 'Hệ thống: Lịch bảo trì định kỳ vào 23:00 tối nay.',
      time: '1 giờ trước',
      unread: false,
      icon: Settings,
      iconTheme: 'purple',
    },
    {
      id: 3,
      type: 'submission',
      title: 'Bài nộp mới',
      content: 'Trần Thị B đã nộp bài Đề thi thử Hóa học #2.',
      time: '3 giờ trước',
      unread: false,
      icon: CheckSquare,
      iconTheme: 'blue',
    },
  ]);

  const handleMarkAllRead = (e) => {
    e.stopPropagation();
    setNotifications(prev => prev.map(n => ({ ...n, unread: false })));
  };

  const handleItemClick = (id) => {
    setNotifications(prev =>
      prev.map(n => (n.id === id ? { ...n, unread: false } : n))
    );
  };

  return (
    <div className="notification-dropdown-container">
      {/* Header */}
      <div className="notif-header">
        <h3 className="notif-title">Thông báo</h3>
        <button 
          type="button" 
          className="btn-mark-read"
          onClick={handleMarkAllRead}
        >
          Đánh dấu tất cả là đã đọc
        </button>
      </div>

      {/* List of notification items */}
      <div className="notif-list">
        {notifications.map((item) => {
          const IconComponent = item.icon;
          return (
            <div
              key={item.id}
              className={`notif-item ${item.unread ? 'is-unread' : ''}`}
              onClick={() => handleItemClick(item.id)}
            >
              {/* Icon Container */}
              <div className={`notif-icon-circle ${item.iconTheme}`}>
                <IconComponent size={20} strokeWidth={2} />
              </div>

              {/* Text info */}
              <div className="notif-content-col">
                <div className="notif-item-header">
                  <h4 className="notif-item-title">{item.title}</h4>
                  {item.unread && <span className="unread-dot"></span>}
                </div>
                <p className="notif-item-desc">{item.content}</p>
                <span className="notif-item-time">{item.time}</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Footer */}
      <div className="notif-footer">
        <button type="button" className="btn-view-all-notifs">
          Xem tất cả thông báo
        </button>
      </div>
    </div>
  );
}
