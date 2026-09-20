// File Name: AssignExerciseModal.jsx
// Description: Modal component for assigning an exercise from the repository to a target class.
// Created At: 2026-09-12
// Created By: Tam Khang
// Updated At: 2026-09-12
// Updated By: Tam Khang

import React, { useState, useEffect } from 'react';
import { 
  X, 
  Send, 
  Calendar, 
  Clock, 
  BookOpen, 
  GraduationCap, 
  AlertCircle, 
  CheckCircle2, 
  Loader2 
} from 'lucide-react';
import { classesApi, assignmentsApi } from '../../services/api';
import './AssignExerciseModal.css';

export default function AssignExerciseModal({ isOpen, onClose, exercise, onAssignedSuccess }) {
  const [classes, setClasses] = useState([]);
  const [loadingClasses, setLoadingClasses] = useState(false);
  const [selectedClassId, setSelectedClassId] = useState('');
  
  // Default due date: 7 days from now at 23:59
  const getDefaultDueDate = (daysAhead = 7) => {
    const d = new Date();
    d.setDate(d.getDate() + daysAhead);
    d.setHours(23, 59, 0, 0);
    const tzOffset = d.getTimezoneOffset() * 60000;
    return new Date(d.getTime() - tzOffset).toISOString().slice(0, 16);
  };

  const [dueAt, setDueAt] = useState(getDefaultDueDate(7));
  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  // Fetch classes when modal opens
  useEffect(() => {
    if (!isOpen) return;

    setErrorMessage('');
    setSuccessMessage('');
    setDueAt(getDefaultDueDate(7));

    async function fetchClasses() {
      try {
        setLoadingClasses(true);
        const res = await classesApi.getClasses();
        const classList = Array.isArray(res) ? res : res.items || [];
        setClasses(classList);
        if (classList.length > 0) {
          setSelectedClassId(classList[0].class_id);
        }
      } catch (err) {
        setErrorMessage(err.response?.data?.detail?.message || 'Không thể tải danh sách lớp học.');
      } finally {
        setLoadingClasses(false);
      }
    }

    fetchClasses();
  }, [isOpen]);

  if (!isOpen || !exercise) return null;

  const handleQuickPreset = (days) => {
    setDueAt(getDefaultDueDate(days));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!selectedClassId) {
      setErrorMessage('Vui lòng chọn lớp học cần giao bài.');
      return;
    }

    const dueDateObj = new Date(dueAt);
    if (isNaN(dueDateObj.getTime()) || dueDateObj <= new Date()) {
      setErrorMessage('Hạn nộp bài phải là thời gian trong tương lai.');
      return;
    }

    try {
      setSubmitting(true);
      setErrorMessage('');

      await assignmentsApi.createAssignment(selectedClassId, {
        exercise_id: exercise.id || exercise.raw?.exercise_id,
        due_at: dueDateObj.toISOString(),
      });

      setSuccessMessage('Giao bài tập thành công!');
      setTimeout(() => {
        if (onAssignedSuccess) {
          onAssignedSuccess();
        }
        onClose();
      }, 1200);
    } catch (err) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'string' ? detail : detail?.message || 'Không thể giao bài tập. Vui lòng thử lại.';
      setErrorMessage(msg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="assign-modal-backdrop" onClick={onClose}>
      <div className="assign-modal-container" onClick={(e) => e.stopPropagation()}>
        {/* Modal Header */}
        <div className="assign-modal-header">
          <div className="assign-modal-title-wrap">
            <div className="assign-modal-icon">
              <Send size={20} />
            </div>
            <div>
              <h2 className="assign-modal-heading">Giao bài tập cho lớp</h2>
              <p className="assign-modal-subheading">Học sinh trong lớp sẽ nhận được bài tập để làm trực tuyến.</p>
            </div>
          </div>
          <button 
            type="button" 
            className="assign-modal-close-btn" 
            onClick={onClose}
            aria-label="Đóng"
          >
            <X size={20} />
          </button>
        </div>

        {/* Exercise Summary Card */}
        <div className="assign-exercise-preview-box">
          <div className="preview-box-icon">
            <BookOpen size={20} />
          </div>
          <div className="preview-box-content">
            <h4 className="preview-box-title">{exercise.title}</h4>
            <div className="preview-box-meta">
              <span className="preview-meta-badge">
                {exercise.subjectName || 'Môn học'}
              </span>
              <span className="preview-meta-text">
                {exercise.questionCount || '0 câu hỏi'}
              </span>
              {exercise.duration && (
                <span className="preview-meta-text">
                  • {exercise.duration}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Alert Messages */}
        {errorMessage && (
          <div className="assign-alert assign-alert-error">
            <AlertCircle size={18} />
            <span>{errorMessage}</span>
          </div>
        )}

        {successMessage && (
          <div className="assign-alert assign-alert-success">
            <CheckCircle2 size={18} />
            <span>{successMessage}</span>
          </div>
        )}

        {/* Assignment Form */}
        <form onSubmit={handleSubmit} className="assign-form">
          {/* Class Select Field */}
          <div className="assign-form-group">
            <label className="assign-label" htmlFor="select-class">
              <GraduationCap size={16} />
              <span>Chọn lớp học nhận bài:</span>
            </label>
            {loadingClasses ? (
              <div className="assign-loading-classes">
                <Loader2 size={18} className="animate-spin" />
                <span>Đang tải danh sách lớp...</span>
              </div>
            ) : (
              <select
                id="select-class"
                className="assign-select"
                value={selectedClassId}
                onChange={(e) => setSelectedClassId(e.target.value)}
                required
              >
                {classes.length === 0 ? (
                  <option value="">Không có lớp học nào khả dụng</option>
                ) : (
                  classes.map((cls) => (
                    <option key={cls.class_id} value={cls.class_id}>
                      {cls.class_name} {cls.school_year ? `(${cls.school_year})` : ''}
                    </option>
                  ))
                )}
              </select>
            )}
          </div>

          {/* Due Date & Time Field */}
          <div className="assign-form-group">
            <label className="assign-label" htmlFor="due-date-input">
              <Calendar size={16} />
              <span>Hạn nộp bài (Ngày & Giờ):</span>
            </label>
            <input
              id="due-date-input"
              type="datetime-local"
              className="assign-datetime-input"
              value={dueAt}
              onChange={(e) => setDueAt(e.target.value)}
              required
            />
            
            {/* Quick Presets */}
            <div className="assign-presets-row">
              <span className="presets-label">Gợi ý nhanh:</span>
              <button 
                type="button" 
                className="preset-btn"
                onClick={() => handleQuickPreset(1)}
              >
                1 ngày
              </button>
              <button 
                type="button" 
                className="preset-btn"
                onClick={() => handleQuickPreset(3)}
              >
                3 ngày
              </button>
              <button 
                type="button" 
                className="preset-btn active"
                onClick={() => handleQuickPreset(7)}
              >
                1 tuần
              </button>
              <button 
                type="button" 
                className="preset-btn"
                onClick={() => handleQuickPreset(14)}
              >
                2 tuần
              </button>
            </div>
          </div>

          {/* Modal Actions */}
          <div className="assign-modal-actions">
            <button
              type="button"
              className="btn-assign-cancel"
              onClick={onClose}
              disabled={submitting}
            >
              Hủy
            </button>
            <button
              type="submit"
              className="btn-assign-submit"
              disabled={submitting || classes.length === 0}
            >
              {submitting ? (
                <>
                  <Loader2 size={18} className="animate-spin" />
                  <span>Đang giao bài...</span>
                </>
              ) : (
                <>
                  <Send size={16} />
                  <span>Xác nhận giao bài</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
