// File Name: LearningQualityCard.jsx
// Description: Learning quality analytics card featuring multi-axis radar chart and detailed teacher qualitative feedback notes matching Image.
// Created At: 2026-08-30
// Created By: Tam Khang
// Updated At: 2026-10-25
// Updated By: Tam Khang

import React from 'react';
import { MoreHorizontal } from 'lucide-react';
import RadarChart from './RadarChart';
import { useAuth } from '../../context/AuthContext';
import { getTeacherProfileDefaults } from '../../utils/teacherSubjectHelper';
import './LearningQualityCard.css';

export default function LearningQualityCard({ learningQuality }) {
  const { user } = useAuth();
  const profileDefaults = getTeacherProfileDefaults(user);
  const className = learningQuality?.class_name || (profileDefaults.homeroomClass ? `Lớp ${profileDefaults.homeroomClass}` : 'Lớp 12A1');

  const defaultNotes = [
    'Điểm trung bình môn Toán và Khoa học tăng nhẹ so với học kỳ trước.',
    'Cần cải thiện điểm thi giữa kỳ và hoàn thành bài tập về nhà đúng hạn.',
    'Tích cực tham gia thảo luận trên lớp và hoàn thiện các dự án nhóm.',
    'Khuyến nghị ôn tập thêm phần đọc hiểu và kỹ năng phân tích dữ liệu.'
  ];

  const feedbackNotes = (learningQuality?.feedback_notes && learningQuality.feedback_notes.length > 0)
    ? learningQuality.feedback_notes
    : defaultNotes;

  const radarData = learningQuality?.radar_data;
  const subjects = radarData && radarData.length > 0 ? radarData.map(r => r.subject_name) : undefined;
  const classData = radarData && radarData.length > 0 ? radarData.map(r => r.class_score) : undefined;
  const averageData = radarData && radarData.length > 0 ? radarData.map(r => r.grade_score) : undefined;

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
          <RadarChart 
            classNameLabel={className} 
            size={250}
            subjects={subjects}
            classData={classData}
            averageData={averageData}
          />
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
