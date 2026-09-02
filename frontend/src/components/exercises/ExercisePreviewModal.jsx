// File Name: ExercisePreviewModal.jsx
// Description: Interactive modal for previewing exercise content, real questions, options, and assigning to classes.
// Created At: 2026-08-30
// Created By: Tam Khang
// Updated At: 2026-09-01
// Updated By: Tam Khang

import React, { useState, useEffect } from 'react';
import { 
  X, 
  Send, 
  CheckCircle2, 
  Clock, 
  HelpCircle, 
  FileText, 
  Check, 
  Download, 
  Loader2, 
  AlertCircle 
} from 'lucide-react';
import { exercisesApi, classesApi } from '../../services/api';
import MathRenderer from '../common/MathRenderer';
import './ExercisePreviewModal.css';

export default function ExercisePreviewModal({ exercise, isOpen, onClose }) {
  const [exerciseDetail, setExerciseDetail] = useState(null);
  const [classList, setClassList] = useState([]);
  const [assignedClass, setAssignedClass] = useState('');
  const [assignedSuccess, setAssignedSuccess] = useState(false);
  const [loading, setLoading] = useState(false);
  const [downloadingPdf, setDownloadingPdf] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!isOpen || !exercise?.id) {
      setExerciseDetail(null);
      return;
    }

    let isMounted = true;

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
            setAssignedClass(classesRes.value[0].class_id);
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

  const handleAssign = () => {
    setAssignedSuccess(true);
    setTimeout(() => {
      setAssignedSuccess(false);
      onClose();
    }, 1200);
  };

  const questions = exerciseDetail?.questions || [];
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
                        <MathRenderer text={q.content_latex || q.content} />
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

        {/* Footer Assign Row */}
        <div className="exercise-preview-footer">
          <div className="assign-class-group">
            <span className="assign-label">Giao cho lớp:</span>
            <select 
              className="class-select"
              value={assignedClass}
              onChange={(e) => setAssignedClass(e.target.value)}
            >
              {classList.length > 0 ? (
                classList.map((c) => (
                  <option key={c.class_id} value={c.class_id}>
                    {c.class_name} ({c.academic_year || '2023-2024'})
                  </option>
                ))
              ) : (
                <option value="default">12A1 - Toán nâng cao</option>
              )}
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
                <span>Đã giao thành công!</span>
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
