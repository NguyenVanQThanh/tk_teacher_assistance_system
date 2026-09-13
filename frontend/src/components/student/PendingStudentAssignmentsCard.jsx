// File Name: PendingStudentAssignmentsCard.jsx
// Description: Card widget showing pending homework assignments for students with checkboxes and due dates.
// Created At: 2026-09-07
// Created By: Tam Khang
// Updated At: 2026-09-07
// Updated By: Tam Khang

import React from 'react';
import { useNavigate } from 'react-router-dom';
import './PendingStudentAssignmentsCard.css';

export default function PendingStudentAssignmentsCard() {
  const navigate = useNavigate();

  const tasks = [
    {
      id: 1,
      title: 'Hoàn thành báo cáo tuần',
      dueLabel: 'Trễ 2 ngày',
      isOverdue: true,
      link: '/student/exercises'
    },
    {
      id: 2,
      title: 'Cập nhật thông tin phụ huynh',
      dueLabel: 'Đến hạn: Ngày mai',
      isOverdue: false,
      link: '/student/exercises'
    }
  ];

  return (
    <div className="pending-assignments-card">
      <h2 className="pending-card-title">Bài tập chưa làm</h2>
      <div className="assignments-list">
        {tasks.map(task => (
          <div 
            key={task.id} 
            className="assignment-item-row"
            onClick={() => navigate(task.link)}
          >
            <div className="assignment-checkbox-custom" />
            <div className="assignment-info">
              <span className="assignment-name">{task.title}</span>
              <span className={`assignment-due-tag ${task.isOverdue ? 'overdue' : 'normal'}`}>
                {task.dueLabel}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
