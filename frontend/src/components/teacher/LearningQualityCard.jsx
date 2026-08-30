// File Name: LearningQualityCard.jsx
// Description: Learning quality analytics card featuring radar chart and AI commentary.
// Created At: 2026-08-30
// Created By: Tam Khang
// Updated At: 2026-08-30
// Updated By: Tam Khang

import React from 'react';
import { MoreHorizontal } from 'lucide-react';
import RadarChart from './RadarChart';
import './LearningQualityCard.css';

export default function LearningQualityCard() {
  const observations = [
    'Điểm trung bình môn Toán và Khoa học tăng nhẹ so với học kỳ trước.',
    'Cần cải thiện điểm thi giữa kỳ và hoàn thành bài tập về nhà đúng hạn.',
    'Tích cực tham gia thảo luận trên lớp và hoàn thiện các dự án nhóm.',
    'Khuyến nghị ôn tập thêm phần đọc hiểu và kỹ năng phân tích dữ liệu.',
  ];

  return (
    <div className="learning-quality-card">
      <div className="card-header">
        <h2 className="card-title">Chất lượng học tập trung bình</h2>
        <button className="icon-more-btn" aria-label="More options">
          <MoreHorizontal size={18} />
        </button>
      </div>

      <div className="quality-content-layout">
        {/* Radar Chart */}
        <div className="radar-wrapper">
          <RadarChart />
        </div>

        {/* Observation Notes */}
        <div className="observations-box">
          <h3 className="observations-title">Nhận xét</h3>
          <ul className="observations-list">
            {observations.map((text, idx) => (
              <li key={idx} className="observation-item">
                <span className="bullet-dot"></span>
                <span className="observation-text">{text}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
