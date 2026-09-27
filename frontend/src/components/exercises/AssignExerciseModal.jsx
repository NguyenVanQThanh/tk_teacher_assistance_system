// File Name: AssignExerciseModal.jsx
// Description: Modal component for assigning an exercise from the repository to multiple target classes simultaneously.
// Created At: 2026-09-12
// Created By: Tam Khang
// Updated At: 2026-09-27
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
  const [selectedClassIds, setSelectedClassIds] = useState([]);
  
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
          // Default select all classes for convenience
          setSelectedClassIds(classList.map(c => c.class_id));
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

  const handleToggleClass = (classId) => {
    setSelectedClassIds(prev =>
      prev.includes(classId)
        ? prev.filter(id => id !== classId)
        : [...prev, classId]
    );
  };

  const handleToggleAll = () => {
    if (selectedClassIds.length === classes.length) {
      setSelectedClassIds([]);
    } else {
      setSelectedClassIds(classes.map(c => c.class_id));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (selectedClassIds.length === 0) {
      setErrorMessage('Vui lòng chọn ít nhất 1 lớp học cần giao bài.');
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

      const results = await assignmentsApi.assignToMultipleClasses(selectedClassIds, {
        exercise_id: exercise.id || exercise.raw?.exercise_id,
        due_at: dueDateObj.toISOString(),
      });

      const successes = results.filter(r => r.success);
      const duplicates = results.filter(r => !r.success && r.code === 'ERR-EXE-DUPLICATE_ASSIGNMENT');
      const failures = results.filter(r => !r.success && r.code !== 'ERR-EXE-DUPLICATE_ASSIGNMENT');

      if (successes.length > 0) {
        let msg = `Giao bài tập thành công cho ${successes.length} lớp!`;
        if (duplicates.length > 0) {
          msg += ` (${duplicates.length} lớp đã được giao trước đó)`;
        }
        setSuccessMessage(msg);
        setTimeout(() => {
          if (onAssignedSuccess) {
            onAssignedSuccess();
          }
          onClose();
        }, 1400);
      } else if (duplicates.length > 0 && failures.length === 0) {
        setErrorMessage(`Bài tập này đã được giao cho tất cả ${duplicates.length} lớp đã chọn trước đó.`);
      } else {
        const firstErr = failures[0]?.error || 'Không thể giao bài tập cho các lớp đã chọn.';
        setErrorMessage(firstErr);
      }
    } catch (err) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'string' ? detail : detail?.message || 'Không thể giao bài tập. Vui lòng thử lại.';
      setErrorMessage(msg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="assign-modal-overlay" onClick={onClose}>
      <div 
        className="assign-modal-container"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
      >
        {/* Header */}
        <div className="assign-modal-header">
          <div className="assign-modal-title-wrap">
            <div className="assign-modal-icon">
              <Send size={20} />
            </div>
            <div>
              <h3 className="assign-modal-heading">Giao bài tập cho học sinh</h3>
              <p className="assign-modal-subheading">
                Chọn một hoặc nhiều lớp học và thiết lập thời hạn nộp bài.
              </p>
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
          {/* Class Multi-Select Field */}
          <div className="assign-form-group">
            <div className="assign-classes-header">
              <label className="assign-label">
                <GraduationCap size={16} />
                <span>Chọn các lớp nhận bài tập:</span>
              </label>
              {classes.length > 0 && (
                <button
                  type="button"
                  className="btn-select-all-classes"
                  onClick={handleToggleAll}
                >
                  {selectedClassIds.length === classes.length ? 'Bỏ chọn tất cả' : `Chọn tất cả (${classes.length} lớp)`}
                </button>
              )}
            </div>

            {loadingClasses ? (
              <div className="assign-loading-classes">
                <Loader2 size={18} className="animate-spin" />
                <span>Đang tải danh sách lớp...</span>
              </div>
            ) : classes.length === 0 ? (
              <div className="assign-no-classes">Không có lớp học nào khả dụng</div>
            ) : (
              <div className="assign-classes-grid">
                {classes.map((cls) => {
                  const isSelected = selectedClassIds.includes(cls.class_id);
                  return (
                    <div
                      key={cls.class_id}
                      className={`class-card-item ${isSelected ? 'selected' : ''}`}
                      onClick={() => handleToggleClass(cls.class_id)}
                    >
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => handleToggleClass(cls.class_id)}
                        className="class-card-checkbox"
                      />
                      <div className="class-card-info">
                        <span className="class-card-name">{(cls.class_name || '').replace(/[^a-zA-Z0-9\sÀ-ỹ]/g, '').trim()}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
            <div className="selected-classes-summary">
              Đã chọn: <strong>{selectedClassIds.length}</strong> / {classes.length} lớp
            </div>
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
              disabled={submitting || classes.length === 0 || selectedClassIds.length === 0}
            >
              {submitting ? (
                <>
                  <Loader2 size={18} className="animate-spin" />
                  <span>Đang giao bài...</span>
                </>
              ) : (
                <>
                  <Send size={16} />
                  <span>Xác nhận giao cho {selectedClassIds.length} lớp</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
