// File Name: ExercisePreviewModal.jsx
// Description: Interactive modal for previewing exercise content, questions, and assigning to classes.
// Created At: 2026-08-30
// Created By: Tam Khang
// Updated At: 2026-08-30
// Updated By: Tam Khang

import React, { useState } from 'react';
import { X, Send, CheckCircle2, Clock, HelpCircle, FileText, Check } from 'lucide-react';
import './ExercisePreviewModal.css';

export default function ExercisePreviewModal({ exercise, isOpen, onClose }) {
  const [assignedClass, setAssignedClass] = useState('12A1');
  const [assignedSuccess, setAssignedSuccess] = useState(false);

  if (!isOpen || !exercise) return null;

  const handleAssign = () => {
    setAssignedSuccess(true);
    setTimeout(() => {
      setAssignedSuccess(false);
      onClose();
    }, 1200);
  };

  return (
    <div className="modal-backdrop-overlay" onClick={onClose}>
      <div className="exercise-preview-container" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="exercise-preview-header">
          <div className="preview-info-box">
            <h3 className="preview-heading">{exercise.title}</h3>
            <div className="preview-sub-badges">
              <span className="badge-tag">{exercise.questionCount}</span>
              {exercise.duration && <span className="badge-tag">{exercise.duration}</span>}
              <span className="badge-tag">Tạo bởi: {exercise.authorName}</span>
            </div>
          </div>
          <button type="button" className="btn-modal-close" onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        {/* Content viewer body */}
        <div className="exercise-preview-body">
          {/* Question 1 */}
          <div className="question-item-card">
            <div className="question-header">
              <span className="q-number">Câu 1:</span>
              <p className="q-text">
                Cho hàm số y = f(x) có đạo hàm f'(x) = x(x - 1)(x + 2)^3 trên R. Số điểm cực trị của hàm số đã cho là:
              </p>
            </div>
            <div className="options-grid">
              <div className="option-item is-correct">
                <span className="opt-label">A.</span>
                <span>3</span>
                <span className="correct-tag"><Check size={12} /> Đáp án đúng</span>
              </div>
              <div className="option-item">
                <span className="opt-label">B.</span>
                <span>2</span>
              </div>
              <div className="option-item">
                <span className="opt-label">C.</span>
                <span>1</span>
              </div>
              <div className="option-item">
                <span className="opt-label">D.</span>
                <span>4</span>
              </div>
            </div>
          </div>

          {/* Question 2 */}
          <div className="question-item-card">
            <div className="question-header">
              <span className="q-number">Câu 2:</span>
              <p className="q-text">
                Tìm đạo hàm của hàm số f(x) = (2x^2 + 1)^3 tại điểm x = 1:
              </p>
            </div>
            <div className="options-grid">
              <div className="option-item">
                <span className="opt-label">A.</span>
                <span>36</span>
              </div>
              <div className="option-item is-correct">
                <span className="opt-label">B.</span>
                <span>108</span>
                <span className="correct-tag"><Check size={12} /> Đáp án đúng</span>
              </div>
              <div className="option-item">
                <span className="opt-label">C.</span>
                <span>54</span>
              </div>
              <div className="option-item">
                <span className="opt-label">D.</span>
                <span>72</span>
              </div>
            </div>
          </div>
        </div>

        {/* Footer Assign Row */}
        <div className="exercise-preview-footer">
          <div className="assign-class-group">
            <span className="assign-label">Giao cho lớp:</span>
            <select 
              className="class-select"
              value={assignedClass}
              onChange={(e) => setAssignedClass(e.target.value)}
            >
              <option value="12A1">Lớp 12A1 (Sĩ số: 40)</option>
              <option value="12A2">Lớp 12A2 (Sĩ số: 38)</option>
              <option value="11B1">Lớp 11B1 (Sĩ số: 42)</option>
              <option value="10C1">Lớp 10C1 (Sĩ số: 45)</option>
            </select>
          </div>

          <button 
            type="button" 
            className="btn-assign-action"
            onClick={handleAssign}
            disabled={assignedSuccess}
          >
            {assignedSuccess ? (
              <>
                <CheckCircle2 size={16} />
                <span>Đã giao thành công cho {assignedClass}!</span>
              </>
            ) : (
              <>
                <Send size={16} />
                <span>Giao bài tập</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
