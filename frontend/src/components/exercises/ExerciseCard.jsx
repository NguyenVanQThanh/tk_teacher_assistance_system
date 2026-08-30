// File Name: ExerciseCard.jsx
// Description: Reusable card component for exercises, quizzes, homework, and test materials.
// Created At: 2026-08-30
// Created By: Tam Khang
// Updated At: 2026-08-30
// Updated By: Tam Khang

import React from 'react';
import { 
  FileText, 
  HelpCircle, 
  Clock, 
  Calendar, 
  ListOrdered, 
  MoreVertical, 
  Eye, 
  Edit3, 
  Share2, 
  Download 
} from 'lucide-react';
import './ExerciseCard.css';

export default function ExerciseCard({ exercise, onPreview, onEdit, onShare, onDownload, onMore }) {
  const isQuiz = exercise.type === 'quiz' || exercise.type === 'test';

  return (
    <div className="exercise-card">
      {/* Top Header: Icon & Options */}
      <div className="exercise-card-top">
        <div className={`exercise-icon-badge ${isQuiz ? 'quiz-badge' : 'homework-badge'}`}>
          {isQuiz ? (
            <HelpCircle size={20} strokeWidth={2.2} />
          ) : (
            <FileText size={20} strokeWidth={2.2} />
          )}
        </div>
        <button 
          type="button" 
          className="exercise-more-btn"
          onClick={() => onMore && onMore(exercise)}
          aria-label="Tùy chọn khác"
        >
          <MoreVertical size={18} />
        </button>
      </div>

      {/* Exercise Title */}
      <h3 className="exercise-title" title={exercise.title}>
        {exercise.title}
      </h3>

      {/* Meta items */}
      <div className="exercise-meta-list">
        {/* Questions / Tasks count */}
        <div className="exercise-meta-row">
          <ListOrdered size={14} className="meta-icon" />
          <span>{exercise.questionCount}</span>
        </div>

        {/* Duration (if quiz/test) */}
        {exercise.duration && (
          <div className="exercise-meta-row">
            <Clock size={14} className="meta-icon" />
            <span>{exercise.duration}</span>
          </div>
        )}

        {/* Created / Due date */}
        <div className="exercise-meta-row">
          <Calendar size={14} className="meta-icon" />
          <span>{exercise.date}</span>
        </div>

        {/* Author Teacher */}
        <div className="exercise-author-row">
          <div className="author-avatar-mini">
            {exercise.authorInitial || 'GV'}
          </div>
          <span className="author-name">{exercise.authorName}</span>
        </div>
      </div>

      {/* Bottom Actions Bar */}
      <div className="exercise-card-footer">
        <button 
          type="button" 
          className="btn-action-preview"
          onClick={() => onPreview && onPreview(exercise)}
        >
          <Eye size={15} />
          <span>Xem</span>
        </button>

        <div className="exercise-action-icons">
          <button 
            type="button" 
            className="icon-action-btn edit-btn"
            onClick={() => onEdit && onEdit(exercise)}
            title="Chỉnh sửa bài tập"
          >
            <Edit3 size={16} />
          </button>

          {exercise.hasShare ? (
            <button 
              type="button" 
              className="icon-action-btn share-btn"
              onClick={() => onShare && onShare(exercise)}
              title="Chia sẻ / Giao bài cho lớp"
            >
              <Share2 size={16} />
            </button>
          ) : (
            <button 
              type="button" 
              className="icon-action-btn download-btn"
              onClick={() => onDownload && onDownload(exercise)}
              title="Tải về đề bài"
            >
              <Download size={16} />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
