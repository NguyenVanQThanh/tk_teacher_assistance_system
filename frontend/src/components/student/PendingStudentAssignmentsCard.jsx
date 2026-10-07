// File Name: PendingStudentAssignmentsCard.jsx
// Description: Card widget showing categorized pending homework assignments (Classroom vs AI Generated) with counts, badges, and interactive selection to display details in flexible container.
// Created At: 2026-09-07
// Created By: Tam Khang
// Updated At: 2026-09-27
// Updated By: Tam Khang

import React from 'react';
import { BookOpen, Sparkles, ChevronRight, AlertCircle, ArrowUpRight } from 'lucide-react';
import './PendingStudentAssignmentsCard.css';

export default function PendingStudentAssignmentsCard({ 
  isActive = false, 
  onClickCard,
  assignments = null
}) {
  const dynamicTasks = Array.isArray(assignments) && assignments.length > 0
    ? assignments.slice(0, 3).map((a, idx) => ({
        id: a.assignment_id || idx,
        title: a.title,
        type: 'classroom',
        typeLabel: a.subject_name || 'Trên lớp',
        dueLabel: a.is_overdue ? 'Đã quá hạn' : (a.due_at ? `Hạn: ${new Date(a.due_at).toLocaleDateString('vi-VN')}` : 'Đến hạn'),
        isOverdue: Boolean(a.is_overdue)
      }))
    : null;

  const classroomCount = dynamicTasks ? assignments.length : 3;
  const aiGeneratedCount = 2;
  const totalCount = classroomCount + aiGeneratedCount;

  const tasks = dynamicTasks || [
    {
      id: 1,
      title: 'Toán 12: Đạo hàm & Khảo sát hàm số',
      type: 'classroom',
      typeLabel: 'Trên lớp',
      dueLabel: 'Trễ 2 ngày',
      isOverdue: true
    },
    {
      id: 2,
      title: 'Hóa học: Chuyên đề Este – Lipit',
      type: 'classroom',
      typeLabel: 'Trên lớp',
      dueLabel: 'Đến hạn: 22:00',
      isOverdue: false
    }
  ];

  const handleCardClick = (e) => {
    if (onClickCard) {
      onClickCard();
    }
  };

  return (
    <div 
      className={`pending-assignments-card ${isActive ? 'is-active-card' : ''}`}
      onClick={handleCardClick}
      title="Nhấn để xem chi tiết danh sách bài tập chưa làm"
    >
      {/* Header */}
      <div className="pending-card-header-row">
        <h2 className="pending-card-title">Bài tập chưa làm</h2>
        <div className="pending-count-chip">
          <span>{totalCount} bài</span>
        </div>
      </div>

      {/* Categorization Stat Grid: Trên lớp vs Tạo sinh AI */}
      <div className="pending-category-stats-grid">
        {/* Category 1: Bài tập trên lớp */}
        <div className="category-stat-card classroom-theme">
          <div className="stat-card-icon-wrap classroom-icon">
            <BookOpen size={16} />
          </div>
          <div className="stat-card-info">
            <span className="stat-type-label">Bài tập trên lớp</span>
            <div className="stat-count-row">
              <span className="stat-number">{classroomCount}</span>
              <span className="stat-subtext">chưa làm</span>
            </div>
          </div>
        </div>

        {/* Category 2: Bài tập tạo sinh AI */}
        <div className="category-stat-card ai-theme">
          <div className="stat-card-icon-wrap ai-icon">
            <Sparkles size={16} />
          </div>
          <div className="stat-card-info">
            <span className="stat-type-label">Tạo sinh AI</span>
            <div className="stat-count-row">
              <span className="stat-number">{aiGeneratedCount}</span>
              <span className="stat-subtext">chưa làm</span>
            </div>
          </div>
        </div>
      </div>

      {/* Assignment Quick Preview List */}
      <div className="assignments-list">
        {tasks.map(task => (
          <div key={task.id} className="assignment-item-row">
            <div className="assignment-checkbox-custom" />
            <div className="assignment-info">
              <div className="assignment-name-row">
                <span className="assignment-name">{task.title}</span>
                <span className={`assignment-tag-type ${task.type}`}>
                  {task.typeLabel}
                </span>
              </div>
              <span className={`assignment-due-tag ${task.isOverdue ? 'overdue' : 'normal'}`}>
                {task.isOverdue && <AlertCircle size={11} />}
                {task.dueLabel}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Footer prompt to open detail */}
      <div className="pending-card-footer-prompt">
        <span className="footer-prompt-text">
          {isActive ? 'Đang xem chi tiết bên phải' : 'Xem chi tiết các bài tập'}
        </span>
        <ArrowUpRight size={14} className="prompt-arrow-icon" />
      </div>
    </div>
  );
}
