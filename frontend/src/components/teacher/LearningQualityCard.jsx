// File Name: LearningQualityCard.jsx
// Description: Learning quality analytics card featuring multi-axis radar chart and detailed teacher qualitative feedback notes matching Image.
// Created At: 2026-08-30
// Created By: Tam Khang
// Updated At: 2026-09-07
// Updated By: Tam Khang

import React from 'react';
import { MoreHorizontal } from 'lucide-react';
import RadarChart from './RadarChart';
import { useAuth } from '../../context/AuthContext';
import { getTeacherProfileDefaults } from '../../utils/teacherSubjectHelper';
import './LearningQualityCard.css';

export default function LearningQualityCard() {
  const { user } = useAuth();
  const profileDefaults = getTeacherProfileDefaults(user);
  const className = profileDefaults.homeroomClass ? `Lớp ${profileDefaults.homeroomClass}` : 'Lớp 12A1';

  const feedbackNotes = [
    'Điểm trung bình môn Toán và Khoa học tăng nhẹ so với học kỳ trước.',
    'Cần cải thiện điểm thi giữa kỳ và hoàn thành bài tập về nhà đúng hạn.',
    'Tích cực tham gia thảo luận trên lớp và hoàn thiện các dự án nhóm.',
    'Khuyến nghị ôn tập thêm phần đọc hiểu và kỹ năng phân tích dữ liệu.'
  ];

  return (
    <div className="learning-quality-card">
      <div className="card-header">
        <h2 className="card-title">Chất lượng học tập trung bình</h2>
        <button className="icon-more-btn" aria-label="More options" type="button">
          <MoreHorizontal size={18} />
        </button>
      </div>

      <div className="quality-content-layout">
        {/* Left Column: Radar Chart with Legend */}
        <div className="quality-chart-pane">
          <RadarChart classNameLabel={className} size={250} />
        </div>

        {/* Right Column: Qualitative Feedback Notes Panel */}
        <div className="quality-notes-pane">
          <h3 className="notes-pane-heading">Nhận xét</h3>
          <ul className="notes-bullets-list">
            {feedbackNotes.map((note, index) => (
              <li key={index} className="notes-bullet-item">
                <span className="bullet-dot" />
                <span className="bullet-text">{note}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
