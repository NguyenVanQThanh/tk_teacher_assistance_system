// File Name: RecentSubmissionsTable.jsx
// Description: Component listing recent student exercise submissions matching the visual dashboard mockup.
// Created At: 2026-08-30
// Created By: Tam Khang
// Updated At: 2026-10-25
// Updated By: Tam Khang

import React from 'react';
import { useNavigate } from 'react-router-dom';
import './RecentSubmissionsTable.css';

export default function RecentSubmissionsTable({ submissions: incomingSubmissions, onGradeSubmission }) {
  const navigate = useNavigate();

  const defaultSubmissions = [
    {
      id: 1,
      studentName: 'Trần Thị B',
      avatarInitial: 'TB',
      avatarBg: '#E0E7FF',
      avatarColor: '#4338CA',
      exerciseTitle: 'Đề thi thử Hóa học #2',
      submittedTime: '10 phút trước',
      status: 'submitted',
      statusLabel: 'Đã nộp',
    },
    {
      id: 2,
      studentName: 'Lê Văn C',
      avatarInitial: 'LC',
      avatarBg: '#FEF3C7',
      avatarColor: '#D97706',
      exerciseTitle: 'Bài tập Toán Hình học',
      submittedTime: '1 giờ trước',
      status: 'late',
      statusLabel: 'Trễ hạn',
    },
    {
      id: 3,
      studentName: 'Phạm Hương D',
      avatarInitial: 'PD',
      avatarBg: '#FCE7F3',
      avatarColor: '#DB2777',
      exerciseTitle: 'Tiểu luận Lịch sử',
      submittedTime: 'Hôm qua, 15:30',
      status: 'submitted',
      statusLabel: 'Đã nộp',
    },
  ];

  const submissions = (incomingSubmissions && incomingSubmissions.length > 0)
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
    : defaultSubmissions;

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
            {submissions.map((item) => (
              <tr key={item.id}>
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
                    onClick={() => onGradeSubmission ? onGradeSubmission(item.id) : navigate('/teacher/grading')}
                  >
                    Chấm bài
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
