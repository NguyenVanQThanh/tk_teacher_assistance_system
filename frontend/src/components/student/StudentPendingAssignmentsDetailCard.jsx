// File Name: StudentPendingAssignmentsDetailCard.jsx
// Description: Detailed pending assignments panel for student dashboard, categorized into classroom exercises and AI-generated exercises with filtering, status tracking, and quick actions.
// Created At: 2026-09-27
// Created By: Tam Khang
// Updated At: 2026-09-27
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

// Rich mock data for student pending assignments
const PENDING_ASSIGNMENTS_DATA = [
  {
    id: 1,
    title: 'Toán 12: Đạo hàm & Khảo sát hàm số',
    subject: 'Toán học',
    type: 'classroom',
    typeLabel: 'Trên lớp',
    teacher: 'Thầy Nguyễn Văn A',
    classCode: '12A1',
    dueLabel: 'Trễ 2 ngày',
    dueDate: '25/03/2024',
    isOverdue: true,
    dueStatus: 'danger',
    questionCount: 25,
    duration: '45 phút',
    link: '/student/exercises'
  },
  {
    id: 2,
    title: 'Hóa học: Chuyên đề Este – Lipit & Bài toán đốt cháy',
    subject: 'Hóa học',
    type: 'classroom',
    typeLabel: 'Trên lớp',
    teacher: 'Cô Trần Thị B',
    classCode: '12A1',
    dueLabel: 'Đến hạn 22:00 hôm nay',
    dueDate: '27/03/2024',
    isOverdue: false,
    dueStatus: 'warning',
    questionCount: 20,
    duration: '30 phút',
    link: '/student/exercises'
  },
  {
    id: 3,
    title: 'Vật lý: Dao động điều hòa & Con lắc lò xo',
    subject: 'Vật lý',
    type: 'classroom',
    typeLabel: 'Trên lớp',
    teacher: 'Thầy Lê Văn C',
    classCode: '12A1',
    dueLabel: 'Đến hạn ngày mai',
    dueDate: '28/03/2024',
    isOverdue: false,
    dueStatus: 'info',
    questionCount: 30,
    duration: '45 phút',
    link: '/student/exercises'
  },
  {
    id: 4,
    title: 'AI Generator: Rèn luyện Đọc hiểu Tiếng Anh Unit 4',
    subject: 'Tiếng Anh',
    type: 'ai_generated',
    typeLabel: 'Tạo sinh AI',
    teacher: 'Hệ thống AI Assistant',
    classCode: 'Tự học',
    dueLabel: 'Luyện tập tự do',
    dueDate: 'Không giới hạn',
    isOverdue: false,
    dueStatus: 'success',
    questionCount: 15,
    duration: '20 phút',
    link: '/student/exercises'
  },
  {
    id: 5,
    title: 'AI Generator: Ôn thi THPT QG Môn Toán (Mức độ Vận dụng)',
    subject: 'Toán học',
    type: 'ai_generated',
    typeLabel: 'Tạo sinh AI',
    teacher: 'Hệ thống AI Assistant',
    classCode: 'Rèn luyện AI',
    dueLabel: 'Gợi ý hoàn thành tuần này',
    dueDate: '30/03/2024',
    isOverdue: false,
    dueStatus: 'purple',
    questionCount: 10,
    duration: '25 phút',
    link: '/student/exercises'
  }
];

export default function StudentPendingAssignmentsDetailCard({ onSwitchToSchedule }) {
  const navigate = useNavigate();
  const [filterType, setFilterType] = useState('all'); // 'all' | 'classroom' | 'ai_generated'

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
                    onClick={() => navigate(assignment.link)}
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
