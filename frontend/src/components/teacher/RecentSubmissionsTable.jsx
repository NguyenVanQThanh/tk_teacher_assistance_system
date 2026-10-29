// File Name: RecentSubmissionsTable.jsx
// Description: Component listing recent student exercise submissions with direct click-through to grading detail modal.
// Created At: 2026-08-30
// Created By: Tam Khang
// Updated At: 2026-10-29
// Updated By: Tam Khang

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import './RecentSubmissionsTable.css';

export default function RecentSubmissionsTable({ 
  submissions: incomingSubmissions, 
  loading = false, 
  onGradeSubmission 
}) {
  const navigate = useNavigate();

  const handleRowClick = (attemptId) => {
    if (!attemptId) return;
    if (onGradeSubmission) {
      onGradeSubmission(attemptId);
    } else {
      navigate(`/teacher/grading?attempt_id=${attemptId}`);
    }
  };

  const hasData = Array.isArray(incomingSubmissions) && incomingSubmissions.length > 0;
  const submissions = hasData
    ? incomingSubmissions.map(item => ({
        id: item.id,
        studentName: item.student_name || item.studentName,
        avatarInitial: item.avatar_initial || item.avatarInitial,
        avatarBg: item.avatar_bg || item.avatarBg || '#E0E7FF',
        avatarColor: item.avatar_color || item.avatarColor || '#4338CA',
        exerciseTitle: item.exercise_title || item.exerciseTitle,
        submittedTime: item.submitted_time || item.submittedTime,
        status: item.status,
        statusLabel: item.status_label || item.statusLabel,
      }))
    : [];

  return (
    <div className="recent-submissions-card">
      <div className="submissions-header">
        <h2 className="submissions-title">Bài nộp gần đây</h2>
        <button 
          type="button" 
          className="view-all-link-btn"
          onClick={() => navigate('/teacher/grading')}
        >
          Xem tất cả
        </button>
      </div>

      <div className="table-responsive">
        <table className="submissions-table">
          <thead>
            <tr>
              <th>HỌC SINH</th>
              <th>BÀI TẬP</th>
              <th>THỜI GIAN NỘP</th>
              <th>TRẠNG THÁI</th>
              <th>HÀNH ĐỘNG</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan="5" className="submissions-state-cell">
                  <div className="submissions-loading-spinner-wrapper">
                    <Loader2 size={20} className="animate-spin" />
                    <span>Đang tải bài nộp gần đây...</span>
                  </div>
                </td>
              </tr>
            ) : submissions.length === 0 ? (
              <tr>
                <td colSpan="5" className="submissions-state-cell">
                  Chưa có bài tập nào được nộp gần đây.
                </td>
              </tr>
            ) : (
              submissions.map((item) => (
                <tr 
                  key={item.id} 
                  className="clickable-submission-row"
                  onClick={() => handleRowClick(item.id)}
                  title="Bấm để xem chi tiết bài nộp và chấm điểm"
                >
                  <td>
                    <div className="student-cell">
                      <div 
                        className="student-avatar-mini"
                        style={{ backgroundColor: item.avatarBg, color: item.avatarColor }}
                      >
                        {item.avatarInitial}
                      </div>
                      <span className="student-name">{item.studentName}</span>
                    </div>
                  </td>
                  <td className="exercise-title-cell">{item.exerciseTitle}</td>
                  <td className="time-cell">{item.submittedTime}</td>
                  <td>
                    <span className={`status-pill ${item.status}`}>
                      {item.statusLabel}
                    </span>
                  </td>
                  <td>
                    <button 
                      type="button"
                      className="btn-action-grade"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleRowClick(item.id);
                      }}
                      title="Chấm bài này"
                    >
                      Chấm bài
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
