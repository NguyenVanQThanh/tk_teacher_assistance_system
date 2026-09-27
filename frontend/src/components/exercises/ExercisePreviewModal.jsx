// File Name: ExercisePreviewModal.jsx
// Description: Interactive modal for previewing exercise content, real questions, options, and assigning to classes.
// Created At: 2026-08-30
// Created By: Tam Khang
// Updated At: 2026-09-27
// Updated By: Tam Khang

import React, { useState, useEffect, useRef } from 'react';
import { 
  X, 
  Send, 
  CheckCircle2, 
  Clock, 
  Check, 
  Download, 
  Loader2, 
  AlertCircle,
  Users,
  ChevronDown
} from 'lucide-react';
import { exercisesApi, classesApi, assignmentsApi } from '../../services/api';
import MathRenderer from '../common/MathRenderer';
import './ExercisePreviewModal.css';

export default function ExercisePreviewModal({ exercise, isOpen, onClose }) {
  const [exerciseDetail, setExerciseDetail] = useState(null);
  const [classList, setClassList] = useState([]);
  const [selectedClassIds, setSelectedClassIds] = useState([]);
  const [isClassDropdownOpen, setIsClassDropdownOpen] = useState(false);
  const [assignedSuccess, setAssignedSuccess] = useState(false);
  const [successInfo, setSuccessInfo] = useState('');
  const [assigning, setAssigning] = useState(false);
  const [assignError, setAssignError] = useState('');
  const [loading, setLoading] = useState(false);
  const [downloadingPdf, setDownloadingPdf] = useState(false);
  const [error, setError] = useState(null);
  const dropdownRef = useRef(null);

  useEffect(() => {
    if (!isOpen || !exercise?.id) {
      setExerciseDetail(null);
      return;
    }

    let isMounted = true;
    setAssignError('');
    setAssignedSuccess(false);

    async function loadDetail() {
      try {
        setLoading(true);
        setError(null);

        // Fetch full exercise details and available classes concurrently
        const [detailRes, classesRes] = await Promise.allSettled([
          exercisesApi.getExerciseDetail(exercise.id),
          classesApi.getClasses()
        ]);

        if (!isMounted) return;

        if (detailRes.status === 'fulfilled' && detailRes.value) {
          setExerciseDetail(detailRes.value);
        } else {
          setExerciseDetail(exercise);
        }

        if (classesRes.status === 'fulfilled' && Array.isArray(classesRes.value)) {
          setClassList(classesRes.value);
          if (classesRes.value.length > 0) {
            setSelectedClassIds([classesRes.value[0].class_id]);
          }
        }
      } catch (err) {
        if (isMounted) {
          setError('Không thể tải chi tiết bài tập.');
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }

    loadDetail();

    return () => {
      isMounted = false;
    };
  }, [isOpen, exercise]);

  // Close dropdown on click outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsClassDropdownOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  if (!isOpen || !exercise) return null;

  const handleDownloadPdf = async () => {
    try {
      setDownloadingPdf(true);
      const blob = await exercisesApi.exportPdf(exercise.id);
      const url = window.URL.createObjectURL(new Blob([blob], { type: 'application/pdf' }));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${exercise.title || 'de_bai'}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert('Không thể xuất file PDF cho bài tập này.');
    } finally {
      setDownloadingPdf(false);
    }
  };

  const cleanClassName = (name) => (name || '').replace(/[^a-zA-Z0-9\sÀ-ỹ]/g, '').trim();

  const getSelectedLabel = () => {
    if (classList.length === 0) return 'Không có lớp học';
    if (selectedClassIds.length === 0) return 'Chọn các lớp học...';
    if (selectedClassIds.length === classList.length && classList.length > 1) {
      return `Tất cả các lớp (${classList.length} lớp)`;
    }
    const names = classList
      .filter(c => selectedClassIds.includes(c.class_id))
      .map(c => cleanClassName(c.class_name));
    if (names.length === 1) return names[0];
    return `${names.slice(0, 2).join(', ')}${names.length > 2 ? ` (+${names.length - 2})` : ''} (${names.length} lớp)`;
  };

  const handleToggleClass = (classId) => {
    setSelectedClassIds(prev => 
      prev.includes(classId) 
        ? prev.filter(id => id !== classId)
        : [...prev, classId]
    );
  };

  const handleToggleAllClasses = () => {
    if (selectedClassIds.length === classList.length) {
      setSelectedClassIds([]);
    } else {
      setSelectedClassIds(classList.map(c => c.class_id));
    }
  };

  const handleAssign = async () => {
    if (selectedClassIds.length === 0) {
      setAssignError('Vui lòng chọn ít nhất một lớp học.');
      return;
    }

    try {
      setAssigning(true);
      setAssignError('');
      setSuccessInfo('');

      // Default due date: 7 days from now at 23:59
      const d = new Date();
      d.setDate(d.getDate() + 7);
      d.setHours(23, 59, 0, 0);

      const results = await assignmentsApi.assignToMultipleClasses(selectedClassIds, {
        exercise_id: exercise.id,
        due_at: d.toISOString(),
      });

      const successes = results.filter(r => r.success);
      const duplicates = results.filter(r => !r.success && r.code === 'ERR-EXE-DUPLICATE_ASSIGNMENT');
      const failures = results.filter(r => !r.success && r.code !== 'ERR-EXE-DUPLICATE_ASSIGNMENT');

      if (successes.length > 0) {
        setAssignedSuccess(true);
        let msg = `Đã giao thành công cho ${successes.length} lớp!`;
        if (duplicates.length > 0) {
          msg += ` (${duplicates.length} lớp đã được giao trước đó)`;
        }
        setSuccessInfo(msg);
        setTimeout(() => {
          setAssignedSuccess(false);
          onClose();
        }, 1500);
      } else if (duplicates.length > 0 && failures.length === 0) {
        setAssignError(`Bài tập này đã được giao cho tất cả ${duplicates.length} lớp đã chọn trước đó.`);
      } else {
        const firstError = failures[0]?.error || 'Không thể giao bài tập cho các lớp đã chọn.';
        setAssignError(firstError);
      }
    } catch (err) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'string' ? detail : detail?.message || 'Không thể giao bài tập.';
      setAssignError(msg);
    } finally {
      setAssigning(false);
    }
  };

  const questions = (exerciseDetail?.questions || [])
    .slice()
    .sort((a, b) => (a.display_order || 0) - (b.display_order || 0));
  const questionCountText = `${questions.length || exercise.total_questions || 0} câu hỏi`;
  const durationText = exerciseDetail?.ai_metadata?.duration || exercise.duration;

  return (
    <div className="modal-backdrop-overlay" onClick={onClose}>
      <div className="exercise-preview-container" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="exercise-preview-header">
          <div className="preview-info-box">
            <h3 className="preview-heading">{exercise.title}</h3>
            <div className="preview-sub-badges">
              <span className="badge-tag">{questionCountText}</span>
              {durationText && <span className="badge-tag">{durationText}</span>}
              <span className="badge-tag">Tác giả: {exercise.authorName || 'Giáo viên'}</span>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <button
              type="button"
              className="icon-action-btn download-btn"
              onClick={handleDownloadPdf}
              disabled={downloadingPdf}
              title="Tải đề bài file PDF"
              style={{ padding: '6px 12px', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', background: '#F3F4F6', borderRadius: '6px', border: '1px solid #E5E7EB', cursor: 'pointer' }}
            >
              {downloadingPdf ? <Loader2 size={15} className="animate-spin" /> : <Download size={15} />}
              <span>{downloadingPdf ? 'Đang tải...' : 'Tải PDF'}</span>
            </button>
            <button type="button" className="btn-modal-close" onClick={onClose}>
              <X size={18} />
            </button>
          </div>
        </div>

        {/* Content viewer body */}
        <div className="exercise-preview-body">
          {error && (
            <div style={{ padding: '12px 16px', background: '#FEF2F2', border: '1px solid #FCA5A5', borderRadius: '8px', color: '#991B1B', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <AlertCircle size={18} />
              <span>{error}</span>
            </div>
          )}

          {loading ? (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '220px', gap: '10px', color: '#6B7280' }}>
              <Loader2 size={28} className="animate-spin" />
              <p>Đang tải danh sách câu hỏi...</p>
            </div>
          ) : questions.length > 0 ? (
            questions.map((q, idx) => {
              const optionLabels = ['A', 'B', 'C', 'D', 'E', 'F'];
              const options = q.answer_options || [];
              const isTrueFalse = q.question_type === 'TrueFalse' || q.part === 'Part2' || (options.length > 0 && /^[a-d]\)/i.test(options[0]?.content || ''));
              const isShortAnswer = q.question_type === 'ShortAnswer' || q.part === 'Part3' || (options.length === 0 && Boolean(q.correct_answer));

              return (
                <div key={q.question_id || idx} className="question-item-card">
                  <div className="question-header">
                    <span className="q-number">Câu {q.display_order || idx + 1}:</span>
                    <div style={{ flex: 1 }}>
                      <div className="q-text">
                        <MathRenderer text={q.content || q.content_latex} />
                      </div>
                      
                      <div style={{ display: 'flex', gap: '6px', marginTop: '6px', alignItems: 'center' }}>
                        {isTrueFalse && (
                          <span style={{ fontSize: '11px', padding: '2px 8px', borderRadius: '4px', background: '#FDF2F8', color: '#DB2777', fontWeight: 600 }}>
                            Trắc nghiệm Đúng/Sai
                          </span>
                        )}
                        {isShortAnswer && (
                          <span style={{ fontSize: '11px', padding: '2px 8px', borderRadius: '4px', background: '#F0FDF4', color: '#16A34A', fontWeight: 600 }}>
                            Trả lời ngắn
                          </span>
                        )}
                        {q.difficulty && (
                          <span style={{ fontSize: '11px', padding: '2px 8px', borderRadius: '4px', background: '#EEF2FF', color: '#4F46E5', fontWeight: 500 }}>
                            Mức độ: {q.difficulty}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Part 1: Multiple Choice Options */}
                  {!isTrueFalse && !isShortAnswer && options.length > 0 && (
                    <div className="options-grid">
                      {options.map((opt, optIdx) => {
                        const isCorrect = opt.is_correct || q.correct_answer === optionLabels[optIdx];
                        const labelChar = optionLabels[optIdx] || opt.display_order;
                        const cleanOptText = (opt.content || '').replace(/^[A-DF-Z][\.\:\)\s]+\s*/i, '');

                        return (
                          <div 
                            key={opt.option_id || optIdx} 
                            className={`option-item ${isCorrect ? 'is-correct' : ''}`}
                          >
                            <span className="opt-label">{labelChar}.</span>
                            <span><MathRenderer text={cleanOptText || opt.content} /></span>
                            {isCorrect && (
                              <span className="correct-tag"><Check size={12} /> Đáp án đúng</span>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  )}

                  {/* Part 2: True/False 4 statements */}
                  {isTrueFalse && options.length > 0 && (
                    <div className="options-grid true-false-grid">
                      {options.map((opt, optIdx) => {
                        const tfLabels = ['a', 'b', 'c', 'd', 'e', 'f'];
                        const isTrue = opt.is_correct === true || opt.is_correct === 'True' || opt.is_correct === 1;
                        const labelChar = tfLabels[optIdx] ? `${tfLabels[optIdx]})` : opt.display_order;
                        const cleanOptText = (opt.content || '').replace(/^[a-f][\.\:\)\s]+\s*/i, '');

                        return (
                          <div 
                            key={opt.option_id || optIdx} 
                            className={`option-item ${isTrue ? 'is-correct' : 'is-incorrect'}`}
                            style={!isTrue ? { borderColor: '#FED7AA', background: '#FFFDF9' } : {}}
                          >
                            <span className="opt-label" style={{ fontWeight: 700 }}>{labelChar}</span>
                            <span style={{ flex: 1 }}><MathRenderer text={cleanOptText || opt.content} /></span>
                            {isTrue ? (
                              <span className="correct-tag" style={{ background: '#ECFDF5', color: '#059669', borderColor: '#A7F3D0' }}>
                                <Check size={12} /> Đúng
                              </span>
                            ) : (
                              <span className="correct-tag" style={{ background: '#FEF2F2', color: '#DC2626', borderColor: '#FECACA' }}>
                                <X size={12} /> Sai
                              </span>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  )}

                  {/* Part 3: Short Answer Box */}
                  {isShortAnswer && (
                    <div style={{ marginTop: '12px', padding: '12px 16px', background: '#F9FAFB', border: '1px dashed #CBD5E1', borderRadius: '8px', display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <span style={{ fontWeight: 600, color: '#475569', fontSize: '13px' }}>Đáp án:</span>
                      <span style={{ fontWeight: 700, color: '#4D308D', fontSize: '14px', background: '#EDE9FE', padding: '3px 12px', borderRadius: '6px', border: '1px solid #DDD6FE' }}>
                        {q.correct_answer || '(Chưa có đáp án)'}
                      </span>
                    </div>
                  )}
                </div>
              );
            })
          ) : (
            <div style={{ textAlign: 'center', padding: '32px 16px', color: '#6B7280' }}>
              <p>Bài tập này hiện chưa có câu hỏi nào trong hệ thống.</p>
            </div>
          )}
        </div>

        {/* Error Alert if assign failed */}
        {assignError && (
          <div style={{ margin: '0 24px 12px 24px', padding: '10px 14px', background: '#FEF2F2', border: '1px solid #FCA5A5', borderRadius: '8px', color: '#991B1B', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertCircle size={16} />
            <span>{assignError}</span>
          </div>
        )}

        {/* Footer Assign Row */}
        <div className="exercise-preview-footer">
          <div className="assign-class-group" ref={dropdownRef}>
            <span className="assign-label">Giao cho lớp:</span>
            <div className="multi-class-dropdown-container">
              <button
                type="button"
                className="multi-class-trigger"
                onClick={() => setIsClassDropdownOpen(prev => !prev)}
                disabled={assigning || classList.length === 0}
              >
                <Users size={16} className="trigger-icon" />
                <span className="trigger-text">{getSelectedLabel()}</span>
                {selectedClassIds.length > 0 && (
                  <span className="trigger-count-badge">{selectedClassIds.length}</span>
                )}
                <ChevronDown size={15} className={`trigger-chevron ${isClassDropdownOpen ? 'open' : ''}`} />
              </button>

              {isClassDropdownOpen && (
                <div className="multi-class-menu">
                  <div className="multi-class-menu-header" onClick={handleToggleAllClasses}>
                    <input
                      type="checkbox"
                      id="select-all-classes-preview"
                      checked={selectedClassIds.length === classList.length && classList.length > 0}
                      onChange={handleToggleAllClasses}
                      className="class-checkbox"
                    />
                    <label htmlFor="select-all-classes-preview" className="checkbox-label">
                      Chọn tất cả ({classList.length} lớp)
                    </label>
                  </div>
                  <div className="multi-class-menu-divider" />
                  <div className="multi-class-menu-list">
                    {classList.map(c => {
                      const isChecked = selectedClassIds.includes(c.class_id);
                      return (
                        <div
                          key={c.class_id}
                          className={`multi-class-menu-item ${isChecked ? 'selected' : ''}`}
                          onClick={() => handleToggleClass(c.class_id)}
                        >
                          <input
                            type="checkbox"
                            checked={isChecked}
                            onChange={() => handleToggleClass(c.class_id)}
                            className="class-checkbox"
                          />
                          <div className="class-item-details">
                            <span className="class-item-name">{cleanClassName(c.class_name)}</span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          </div>

          <button 
            type="button" 
            className="btn-assign-action"
            onClick={handleAssign}
            disabled={assignedSuccess || assigning || selectedClassIds.length === 0}
          >
            {assigning ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                <span>Đang giao {selectedClassIds.length} lớp...</span>
              </>
            ) : assignedSuccess ? (
              <>
                <CheckCircle2 size={16} />
                <span>{successInfo || 'Đã giao thành công!'}</span>
              </>
            ) : (
              <>
                <Send size={16} />
                <span>Giao bài tập {selectedClassIds.length > 0 ? `(${selectedClassIds.length} lớp)` : ''}</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
