// File Name: PendingStudentAssignmentsCard.jsx
// Description: Card widget showing categorized pending homework assignments (Classroom vs AI Generated) with counts, badges, and interactive selection.
// Created At: 2026-09-07
// Created By: Tam Khang
// Updated At: 2026-10-11
// Updated By: Tam Khang

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { BookOpen, Sparkles, ChevronRight, AlertCircle } from 'lucide-react';
import './PendingStudentAssignmentsCard.css';

export default function PendingStudentAssignmentsCard({ 
  isActive = false, 
  onClickCard,
  assignments = null
}) {
  // Only unfinished assignments count as pending (matches the exercise library "active"/"overdue" tabs)
  const pending = Array.isArray(assignments) ? assignments.filter(a => !a.is_completed) : null;
  const toTask = (a) => ({
    id: a.assignment_id,
    assignment_id: a.assignment_id,
    exercise_id: a.exercise_id,
    title: a.title,
    type: a.is_ai_generated ? 'ai' : 'classroom',
    typeLabel: a.is_ai_generated ? 'Tạo sinh AI' : (a.subject_name || 'Trên lớp'),
    dueLabel: a.is_overdue ? 'Đã quá hạn' : (a.due_at ? `Hạn: ${new Date(a.due_at).toLocaleDateString('vi-VN')}` : 'Đến hạn'),
    isOverdue: Boolean(a.is_overdue)
  });
  const classroomCount = pending ? pending.filter(a => !a.is_ai_generated).length : 0;
  const aiGeneratedCount = pending ? pending.filter(a => a.is_ai_generated).length : 0;
  const totalCount = classroomCount + aiGeneratedCount;
  const tasks = pending ? pending.slice(0, 3).map(toTask) : [];

  const navigate = useNavigate();

  const handleCardClick = (e) => {
    if (onClickCard) {
      onClickCard();
    }
  };

  const handleOpenTask = (e, task) => {
    e.stopPropagation();
    navigate('/student/exercises', {
      state: {
        searchTitle: task.title,
        autoOpenTitle: task.title,
        autoOpenId: task.id || task.assignment_id
      }
    });
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
          <div 
            key={task.id} 
            className="assignment-item-row"
            onClick={(e) => handleOpenTask(e, task)}
            title="Bấm để lọc bài tập này trong Kho bài tập"
            style={{ cursor: 'pointer' }}
          >
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
    </div>
  );
}
