// File Name: StudentPendingAssignmentsDetailCard.jsx
// Description: Detailed pending assignments panel for student dashboard with quick exercise opening and filtering.
// Created At: 2026-09-27
// Created By: Tam Khang
// Updated At: 2026-10-11
// Updated By: Tam Khang

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  BookOpen, 
  Sparkles, 
  Clock, 
  Calendar, 
  AlertCircle, 
  ArrowRight, 
  ChevronRight,
  HelpCircle
} from 'lucide-react';
import './StudentPendingAssignmentsDetailCard.css';

export default function StudentPendingAssignmentsDetailCard({ onSwitchToSchedule, assignments = null }) {
  const navigate = useNavigate();
  // Real pending (unfinished) assignments from the dashboard API
  const PENDING_ASSIGNMENTS_DATA = (Array.isArray(assignments) ? assignments : [])
    .filter(a => !a.is_completed)
    .map(a => ({
      id: a.assignment_id,
      assignment_id: a.assignment_id,
      exercise_id: a.exercise_id,
      title: a.title,
      subject: a.subject_name,
      type: a.is_ai_generated ? 'ai_generated' : 'classroom',
      typeLabel: a.is_ai_generated ? 'Tạo sinh AI' : (a.subject_name || 'Trên lớp'),
      teacher: a.is_ai_generated ? 'Trợ lý AI' : (a.subject_name || 'Giáo viên bộ môn'),
      classCode: a.is_ai_generated ? 'Tự học' : 'Trên lớp',
      dueLabel: a.is_overdue ? 'Đã quá hạn' : (a.due_at ? `Hạn: ${new Date(a.due_at).toLocaleDateString('vi-VN')}` : 'Đến hạn'),
      isOverdue: Boolean(a.is_overdue),
      dueStatus: a.is_overdue ? 'danger' : 'normal',
      questionCount: a.total_questions || 0,
      duration: `${a.duration_minutes || 45} phút`
    }));
  const [filterType, setFilterType] = useState('all'); // 'all' | 'classroom' | 'ai_generated'

  const handleOpenExercise = (assignment) => {
    navigate('/student/exercises', {
      state: {
        searchTitle: assignment.title,
        autoOpenTitle: assignment.title,
        autoOpenId: assignment.id || assignment.assignment_id
      }
    });
  };

  const filteredAssignments = PENDING_ASSIGNMENTS_DATA.filter(item => {
    if (filterType === 'all') return true;
    return item.type === filterType;
  });

  const classroomCount = PENDING_ASSIGNMENTS_DATA.filter(i => i.type === 'classroom').length;
  const aiGeneratedCount = PENDING_ASSIGNMENTS_DATA.filter(i => i.type === 'ai_generated').length;

  return (
    <div className="student-pending-detail-container">
      {/* Main Detailed Card */}
      <div className="pending-detail-main-card">
        {/* Header */}
        <div className="pending-detail-header">
          <div className="pending-header-title-row">
            <div className="pending-header-left">
              <h3 className="pending-detail-title">Bài tập chưa làm</h3>
              <span className="pending-total-badge">{PENDING_ASSIGNMENTS_DATA.length} bài</span>
            </div>
            {onSwitchToSchedule && (
              <button 
                type="button" 
                className="btn-back-to-schedule"
                onClick={onSwitchToSchedule}
                title="Chuyển về xem Lịch học hôm nay"
              >
                <Calendar size={13} />
                <span>Xem lịch học</span>
              </button>
            )}
          </div>

          {/* Quick Category Summary Bar */}
          <div className="pending-category-pills">
            <button 
              type="button" 
              className={`category-pill-btn ${filterType === 'all' ? 'active' : ''}`}
              onClick={() => setFilterType('all')}
            >
              Tất cả ({PENDING_ASSIGNMENTS_DATA.length})
            </button>
            <button 
              type="button" 
              className={`category-pill-btn classroom ${filterType === 'classroom' ? 'active' : ''}`}
              onClick={() => setFilterType('classroom')}
            >
              <BookOpen size={13} />
              <span>Trên lớp ({classroomCount})</span>
            </button>
            <button 
              type="button" 
              className={`category-pill-btn ai ${filterType === 'ai_generated' ? 'active' : ''}`}
              onClick={() => setFilterType('ai_generated')}
            >
              <Sparkles size={13} />
              <span>Tạo sinh AI ({aiGeneratedCount})</span>
            </button>
          </div>
        </div>

        {/* Assignments Stack */}
        <div className="pending-assignments-stack">
          {filteredAssignments.map((assignment) => {
            const isAi = assignment.type === 'ai_generated';
            return (
              <div 
                key={assignment.id} 
                className={`pending-assignment-card ${isAi ? 'border-ai' : 'border-classroom'}`}
              >
                <div className="assignment-top-row">
                  <div className="assignment-title-group">
                    <h4 className="assignment-heading">{assignment.title}</h4>
                    <span className="assignment-author-tag">{assignment.teacher} · {assignment.classCode}</span>
                  </div>
                  <span className={`assignment-category-badge ${isAi ? 'badge-ai' : 'badge-classroom'}`}>
                    {isAi ? <Sparkles size={11} /> : <BookOpen size={11} />}
                    {assignment.typeLabel}
                  </span>
                </div>

                <div className="assignment-middle-row">
                  <div className="assignment-meta-item">
                    <Clock size={12} className="meta-icon" />
                    <span>{assignment.duration}</span>
                  </div>
                  <div className="assignment-meta-item">
                    <HelpCircle size={12} className="meta-icon" />
                    <span>{assignment.questionCount} câu hỏi</span>
                  </div>
                  <span className={`due-status-pill ${assignment.dueStatus}`}>
                    {assignment.isOverdue && <AlertCircle size={11} />}
                    {assignment.dueLabel}
                  </span>
                </div>

                <div className="assignment-footer-row">
                  <button 
                    type="button" 
                    className={`btn-start-assignment ${isAi ? 'btn-ai-style' : 'btn-class-style'}`}
                    onClick={() => handleOpenExercise(assignment)}
                    title="Lọc và mở chi tiết bài tập này trong Kho bài tập"
                  >
                    <span>{isAi ? 'Luyện tập ngay' : 'Làm bài ngay'}</span>
                    <ArrowRight size={13} />
                  </button>
                </div>
              </div>
            );
          })}
        </div>

        {/* Bottom Link to Full Exercise Repository */}
        <div className="pending-detail-footer-action">
          <button 
            type="button" 
            className="btn-view-all-exercises"
            onClick={() => navigate('/student/exercises')}
          >
            <span>Đến kho bài tập đầy đủ</span>
            <ChevronRight size={15} />
          </button>
        </div>
      </div>
    </div>
  );
}
