// File Name: StudentActivityTimelineCard.jsx
// Description: Student dashboard right-panel activity feed and notification history.
// Created At: 2026-09-07
// Created By: Tam Khang
// Updated At: 2026-09-07
// Updated By: Tam Khang

import React from 'react';
import { 
  Download, 
  UserPlus, 
  MessageSquare, 
  AlertTriangle, 
  MoreVertical 
} from 'lucide-react';
import './StudentActivityTimelineCard.css';

export default function StudentActivityTimelineCard() {
  const activities = [
    {
      id: 1,
      icon: Download,
      variant: 'purple',
      title: 'Đã tải xuống báo cáo',
      description: 'Báo cáo đánh giá năng lực học sinh quý 1 đã được tải xuống.',
      time: '10 phút trước'
    },
    {
      id: 2,
      icon: UserPlus,
      variant: 'purple',
      title: 'Thêm hồ sơ mới',
      description: 'Hồ sơ của học sinh Nguyễn Văn A đã được tạo mới thành công.',
      time: '2 giờ trước'
    },
    {
      id: 3,
      icon: MessageSquare,
      variant: 'purple',
      title: 'Cập nhật ghi chú',
      description: 'Ghi chú cuộc họp phụ huynh lớp 10A2 đã được cập nhật.',
      time: 'Hôm qua, 15:30'
    },
    {
      id: 4,
      icon: AlertTriangle,
      variant: 'red',
      title: 'Cảnh báo trễ hạn',
      description: 'Có 2 công việc chưa hoàn thành vượt quá thời hạn quy định.',
      time: 'Hôm qua, 09:00'
    },
  ];

  return (
    <div className="student-activity-card">
      <div>
        <div className="activity-header">
          <h2 className="activity-card-title">Chi tiết dashboard</h2>
          <button type="button" className="activity-more-btn" aria-label="More options">
            <MoreVertical size={18} />
          </button>
        </div>

        <div className="activity-items-list">
          {activities.map(item => {
            const Icon = item.icon;
            return (
              <div key={item.id} className="activity-item-row">
                <div className={`activity-icon-wrapper ${item.variant}`}>
                  <Icon size={18} />
                </div>
                <div className="activity-info">
                  <span className="activity-title">{item.title}</span>
                  <p className="activity-description">{item.description}</p>
                  <span className="activity-time">{item.time}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <button 
        type="button" 
        className="btn-view-all-activities"
        onClick={() => alert('Đang hiển thị toàn bộ lịch sử hoạt động học tập.')}
      >
        Xem toàn bộ hoạt động
      </button>
    </div>
  );
}
