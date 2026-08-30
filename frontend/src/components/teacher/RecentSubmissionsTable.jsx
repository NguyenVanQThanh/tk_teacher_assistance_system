// File Name: RecentSubmissionsTable.jsx
// Description: Component listing recent student exercise submissions.
// Created At: 2026-08-30
// Created By: Tam Khang
// Updated At: 2026-08-30
// Updated By: Tam Khang

import React from 'react';
import './RecentSubmissionsTable.css';

export default function RecentSubmissionsTable({ onGradeSubmission }) {
  const submissions = [
    {
      id: 1,
      studentName: 'Trần Thị B',
      avatarInitial: 'TB',
      exerciseTitle: 'Đề thi thử Hóa học #2',
      submittedTime: '10 phút trước',
      status: 'submitted',
      statusLabel: 'Đã nộp',
    },
    {
      id: 2,
      studentName: 'Lê Văn C',
      avatarInitial: 'LC',
      exerciseTitle: 'Bài tập Toán Hình học',
      submittedTime: '1 giờ trước',
      status: 'late',
      statusLabel: 'Trễ hạn',
    },
    {
      id: 3,
      studentName: 'Phạm Hương D',
      avatarInitial: 'PD',
      exerciseTitle: 'Tiểu luận Lịch sử',
      submittedTime: 'Hôm qua, 15:30',
      status: 'submitted',
      statusLabel: 'Đã nộp',
    },
    {
      id: 4,
      studentName: 'Nguyễn Hoàng Long',
      avatarInitial: 'NL',
      exerciseTitle: 'Kiểm tra 15 phút Vật Lí',
      submittedTime: 'Hôm qua, 11:20',
      status: 'submitted',
      statusLabel: 'Đã nộp',
    },
  ];

  return (
    <div className="recent-submissions-card">
      <div className="submissions-header">
        <h2 className="submissions-title">Bài nộp gần đây</h2>
        <a href="#view-all" className="view-all-link">Xem tất cả</a>
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
                    <div className={`student-avatar-mini ${item.id}`}>
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
                    className="btn-action-grade"
                    onClick={() => onGradeSubmission && onGradeSubmission(item.id)}
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
