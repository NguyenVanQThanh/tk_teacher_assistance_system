// File Name: TeacherFeedbackNoteCard.jsx
// Description: Teacher qualitative note card with quote and avatar attribution.
// Created At: 2026-09-07
// Created By: Tam Khang
// Updated At: 2026-09-07
// Updated By: Tam Khang

import React from 'react';
import './TeacherFeedbackNoteCard.css';

export default function TeacherFeedbackNoteCard({
  title = 'Nhận xét',
  quote = '"Kỹ năng giao tiếp và tổ chức đang có sự tiến bộ rõ rệt trong tháng này."',
  authorName = 'Mr. Anderson',
  authorInitial = 'M',
  authorBg = '#EDE9FE',
  authorColor = '#7C3AED'
}) {
  return (
    <div className="feedback-note-card">
      <h2 className="feedback-card-title">{title}</h2>
      <div className="feedback-quote-box">
        <p className="feedback-quote-text">{quote}</p>
        <div className="feedback-author-row">
          <div 
            className="author-avatar-badge"
            style={{ backgroundColor: authorBg, color: authorColor }}
          >
            {authorInitial}
          </div>
          <span className="author-name-text">{authorName}</span>
        </div>
      </div>
    </div>
  );
}
