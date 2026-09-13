// File Name: NotificationDropdown.jsx
// Description: Interactive notification popover matching the exact visual mockup design with Q&A and fullscreen notification dialog callback.
// Created At: 2026-08-30
// Created By: Tam Khang
// Updated At: 2026-09-13
// Updated By: Tam Khang

import React, { useState } from 'react';
import { MessageSquare, Settings, FileText } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import './NotificationDropdown.css';

export default function NotificationDropdown({ onClose, onOpenQA, onOpenAllNotifs, initialNotifications }) {
  const { user } = useAuth();
  const isTeacher = user?.role !== 'Student';

  const defaultItems = [
    {
      id: 1,
      type: 'qa',
      title: 'Giải đáp thắc mắc',
      content: isTeacher 
        ? 'Học sinh Hoàng Anh đã gửi câu hỏi thắc mắc về bài tập Toán 12A1.' 
        : 'Giáo viên đã phản hồi câu hỏi của bạn về bài tập Toán.',
      time: '2 phút trước',
      unread: true,
      icon: MessageSquare,
      iconTheme: 'purple',
    },
    {
      id: 2,
      type: 'system',
      title: 'Bảo trì hệ thống',
      content: 'Hệ thống sẽ bảo trì định kỳ vào lúc 23:00 tối nay.',
      time: '1 giờ trước',
      unread: false,
      icon: Settings,
      iconTheme: 'purple',
    },
    {
      id: 3,
      type: 'activity',
      title: isTeacher ? 'Bài tập đã nộp' : 'Hoạt động học tập',
      content: isTeacher 
        ? 'Có 15 học sinh lớp 12A1 vừa hoàn thành bài tập trắc nghiệm Toán.' 
        : 'Bạn có bài tập tạo sinh mới trong môn Tiếng Anh.',
      time: '3 giờ trước',
      unread: true,
      icon: FileText,
      iconTheme: 'purple',
    },
  ];

  const [notifications, setNotifications] = useState(initialNotifications || defaultItems);

  const handleMarkAllRead = (e) => {
    e.stopPropagation();
    setNotifications(prev => prev.map(n => ({ ...n, unread: false })));
  };

  const handleItemClick = (item) => {
    setNotifications(prev =>
      prev.map(n => (n.id === item.id ? { ...n, unread: false } : n))
    );
    if (item.type === 'qa' && onOpenQA) {
      if (onClose) onClose();
      onOpenQA();
    }
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
              onClick={() => handleItemClick(item)}
            >
              {/* Icon Container */}
              <div className={`notif-icon-circle ${item.iconTheme}`}>
                <IconComponent size={18} strokeWidth={2} />
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
        <button 
          type="button" 
          className="btn-view-all-notifs"
          onClick={() => {
            if (onClose) onClose();
            if (onOpenAllNotifs) onOpenAllNotifs();
          }}
        >
          Xem tất cả thông báo
        </button>
      </div>
    </div>
  );
}
