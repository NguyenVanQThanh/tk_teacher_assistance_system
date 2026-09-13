// File Name: RecentSubmissionsSummaryCard.jsx
// Description: Compact widget displaying the latest student submissions and status pills.
// Created At: 2026-09-07
// Created By: Tam Khang
// Updated At: 2026-09-07
// Updated By: Tam Khang

import React from 'react';
import { useNavigate } from 'react-router-dom';
import './RecentSubmissionsSummaryCard.css';

export default function RecentSubmissionsSummaryCard() {
  const navigate = useNavigate();

  const recentList = [
    {
      id: 'sub-1',
      studentName: 'Trần Thị Bích Ngọc',
      className: 'Lớp 10A1',
      initials: 'BN',
      status: 'submitted',
      statusLabel: 'Đã nộp',
      avatarBg: '#E0E7FF',
      avatarColor: '#4338CA',
    },
    {
      id: 'sub-2',
      studentName: 'Lê Hoàng Nam',
      className: 'Lớp 11B2',
      initials: 'HN',
      status: 'submitted',
      statusLabel: 'Đã nộp',
      avatarBg: '#FEF3C7',
      avatarColor: '#D97706',
    },
  ];

  return (
    <div className="recent-submissions-summary-card">
      <div className="recent-card-header">
        <h2 className="recent-card-title">Bài nộp gần đây</h2>
      </div>

      <div className="recent-column-labels">
        <span className="label-student">Học sinh / Lớp</span>
        <span className="label-status">Trạng thái</span>
      </div>

      <div className="recent-items-list">
        {recentList.map((item) => (
          <div 
            key={item.id} 
            className="recent-item-row"
            onClick={() => navigate('/teacher/grading')}
          >
            <div className="student-profile-cell">
              <div 
                className="student-avatar-badge"
                style={{ backgroundColor: item.avatarBg, color: item.avatarColor }}
              >
                <span>{item.initials}</span>
              </div>
              <div className="student-text-group">
                <span className="student-fullname">{item.studentName}</span>
                <span className="student-class-label">{item.className}</span>
              </div>
            </div>

            <div className="status-badge-cell">
              <span className={`recent-status-pill status-${item.status}`}>
                {item.statusLabel}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
