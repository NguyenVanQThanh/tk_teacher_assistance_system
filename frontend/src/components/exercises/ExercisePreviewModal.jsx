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
  AlertCircle,
  Edit2,
  Trash2,
  Save,
  RotateCcw
} from 'lucide-react';
import { exercisesApi, classesApi, assignmentsApi, questionsApi } from '../../services/api';
import MathRenderer from '../common/MathRenderer';
import './ExercisePreviewModal.css';

export default function ExercisePreviewModal({ exercise, isOpen, onClose }) {
  const [exerciseDetail, setExerciseDetail] = useState(null);
  const [classList, setClassList] = useState([]);
  const [assignedClass, setAssignedClass] = useState('');
  const [assignedSuccess, setAssignedSuccess] = useState(false);
  const [assigning, setAssigning] = useState(false);
  const [assignError, setAssignError] = useState('');
  const [loading, setLoading] = useState(false);
  const [downloadingPdf, setDownloadingPdf] = useState(false);
  const [error, setError] = useState(null);

  // Question editing / deleting states
  const [editingQuestionId, setEditingQuestionId] = useState(null);
  const [editFormData, setEditFormData] = useState({});
  const [isSavingQuestion, setIsSavingQuestion] = useState(false);
  const [deletingQuestionId, setDeletingQuestionId] = useState(null);

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

  const handleAssign = async () => {
    if (!assignedClass) {
      setAssignError('Vui lòng chọn lớp học.');
      return;
    }

    try {
      setAssigning(true);
      setAssignError('');

      // Default due date: 7 days from now at 23:59
      const d = new Date();
      d.setDate(d.getDate() + 7);
      d.setHours(23, 59, 0, 0);

      await assignmentsApi.createAssignment(assignedClass, {
        exercise_id: exercise.id,
        due_at: d.toISOString(),
      });

      setAssignedSuccess(true);
      setTimeout(() => {
        setAssignedSuccess(false);
        onClose();
      }, 1200);
    } catch (err) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'string' ? detail : detail?.message || 'Không thể giao bài tập.';
      setAssignError(msg);
    } finally {
      setAssigning(false);
    }
  };

  const handleStartEditQuestion = (q) => {
    setEditingQuestionId(q.question_id);
    setEditFormData({
      content: q.content || q.content_latex || '',
      difficulty: q.difficulty || 'Nhận biết',
      correct_answer: q.correct_answer || '',
      question_type: q.question_type || 'MultipleChoice',
      answer_options: (q.answer_options || []).map(opt => ({
        option_id: opt.option_id,
        content: opt.content,
        is_correct: Boolean(opt.is_correct),
        display_order: opt.display_order || 0
      }))
    });
  };

  const handleCancelEditQuestion = () => {
    setEditingQuestionId(null);
    setEditFormData({});
  };

  const handleSaveEditQuestion = async (qId) => {
    try {
      setIsSavingQuestion(true);
      const payload = {
        content: editFormData.content.trim(),
        difficulty: editFormData.difficulty,
        correct_answer: editFormData.correct_answer,
        question_type: editFormData.question_type,
        answer_options: editFormData.answer_options && editFormData.answer_options.length > 0
          ? editFormData.answer_options.map((opt, idx) => ({
              content: opt.content.trim(),
              is_correct: opt.is_correct,
              display_order: idx + 1
            }))
          : undefined
      };

      const updated = await questionsApi.updateQuestion(qId, payload);
      setExerciseDetail(prev => ({
        ...prev,
        questions: (prev.questions || []).map(q => q.question_id === qId ? { ...q, ...updated, ...payload } : q)
      }));
      setEditingQuestionId(null);
      setEditFormData({});
    } catch (err) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'string' ? detail : detail?.message || 'Không thể cập nhật câu hỏi.';
      alert(msg);
    } finally {
      setIsSavingQuestion(false);
    }
  };

  const handleDeleteQuestion = async (qId) => {
    if (!window.confirm('Bạn có chắc chắn muốn xóa câu hỏi này khỏi đề bài?')) return;
    try {
      setDeletingQuestionId(qId);
      await questionsApi.deleteQuestion(qId);
      setExerciseDetail(prev => ({
        ...prev,
        questions: (prev.questions || []).filter(q => q.question_id !== qId),
        total_questions: Math.max(0, (prev.total_questions || prev.questions?.length || 1) - 1)
      }));
    } catch (err) {
      alert('Không thể xóa câu hỏi.');
    } finally {
      setDeletingQuestionId(null);
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
              const isEditingThis = editingQuestionId === q.question_id;

              return (
                <div key={q.question_id || idx} className="question-item-card" style={isEditingThis ? { border: '2px solid #6366F1', background: '#F8FAFC' } : {}}>
                  <div className="question-header">
                    <span className="q-number">Câu {q.display_order || idx + 1}:</span>
                    <div style={{ flex: 1 }}>
                      {isEditingThis ? (
                        <textarea
                          rows={2}
                          value={editFormData.content}
                          onChange={(e) => setEditFormData({ ...editFormData, content: e.target.value })}
                          style={{ width: '100%', padding: '8px 12px', border: '1px solid #CBD5E1', borderRadius: '6px', fontSize: '14px', fontFamily: 'inherit', resize: 'vertical' }}
                        />
                      ) : (
                        <div className="q-text">
                          <MathRenderer text={q.content || q.content_latex} />
                        </div>
                      )}
                      
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

                    {/* Question Action Buttons */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginLeft: '12px' }}>
                      {q.question_id && !isEditingThis && (
                        <>
                          <button
                            type="button"
                            onClick={() => handleStartEditQuestion(q)}
                            title="Chỉnh sửa câu hỏi"
                            style={{ padding: '6px 10px', background: '#F3F4F6', border: '1px solid #E5E7EB', borderRadius: '6px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '12px', color: '#374151' }}
                          >
                            <Edit2 size={13} />
                            <span>Sửa</span>
                          </button>
                          <button
                            type="button"
                            onClick={() => handleDeleteQuestion(q.question_id)}
                            disabled={deletingQuestionId === q.question_id}
                            title="Xóa câu hỏi khỏi đề bài"
                            style={{ padding: '6px 10px', background: '#FEF2F2', border: '1px solid #FECACA', borderRadius: '6px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '12px', color: '#DC2626' }}
                          >
                            {deletingQuestionId === q.question_id ? <Loader2 size={13} className="animate-spin" /> : <Trash2 size={13} />}
                            <span>Xóa</span>
                          </button>
                        </>
                      )}
                      {isEditingThis && (
                        <>
                          <button
                            type="button"
                            onClick={() => handleSaveEditQuestion(q.question_id)}
                            disabled={isSavingQuestion}
                            style={{ padding: '6px 12px', background: '#4F46E5', color: '#FFFFFF', border: 'none', borderRadius: '6px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '12px', fontWeight: 600 }}
                          >
                            {isSavingQuestion ? <Loader2 size={13} className="animate-spin" /> : <Save size={13} />}
                            <span>Lưu</span>
                          </button>
                          <button
                            type="button"
                            onClick={handleCancelEditQuestion}
                            disabled={isSavingQuestion}
                            style={{ padding: '6px 10px', background: '#E5E7EB', color: '#374151', border: 'none', borderRadius: '6px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '12px' }}
                          >
                            <RotateCcw size={13} />
                            <span>Hủy</span>
                          </button>
                        </>
                      )}
                    </div>
                  </div>

                  {/* Part 1: Multiple Choice Options */}
                  {!isTrueFalse && !isShortAnswer && options.length > 0 && (
                    <div className="options-grid">
                      {options.map((opt, optIdx) => {
                        const isCorrect = opt.is_correct || q.correct_answer === optionLabels[optIdx];
                        const labelChar = optionLabels[optIdx] || opt.display_order;
                        const cleanOptText = (opt.content || '').replace(/^[A-DF-Z][\.\:\)\s]+\s*/i, '');

                        if (isEditingThis) {
                          const currentOpt = editFormData.answer_options?.[optIdx] || opt;
                          return (
                            <div key={opt.option_id || optIdx} className={`option-item ${currentOpt.is_correct ? 'is-correct' : ''}`} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                              <span className="opt-label">{labelChar}.</span>
                              <input
                                type="text"
                                value={currentOpt.content || ''}
                                onChange={(e) => {
                                  const textVal = e.target.value;
                                  setEditFormData(prev => ({
                                    ...prev,
                                    answer_options: prev.answer_options.map((o, i) => i === optIdx ? { ...o, content: textVal } : o)
                                  }));
                                }}
                                style={{ flex: 1, padding: '4px 8px', border: '1px solid #CBD5E1', borderRadius: '4px', fontSize: '13px' }}
                              />
                              <button
                                type="button"
                                onClick={() => {
                                  setEditFormData(prev => ({
                                    ...prev,
                                    correct_answer: labelChar,
                                    answer_options: prev.answer_options.map((o, i) => ({
                                      ...o,
                                      is_correct: i === optIdx
                                    }))
                                  }));
                                }}
                                style={{ padding: '3px 8px', borderRadius: '4px', fontSize: '11px', cursor: 'pointer', border: currentOpt.is_correct ? '1px solid #10B981' : '1px solid #CBD5E1', background: currentOpt.is_correct ? '#ECFDF5' : '#FFFFFF', color: currentOpt.is_correct ? '#059669' : '#64748B', fontWeight: 600 }}
                              >
                                {currentOpt.is_correct ? '✓ Đúng' : 'Chọn đúng'}
                              </button>
                            </div>
                          );
                        }

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
                      {isEditingThis ? (
                        <input
                          type="text"
                          value={editFormData.correct_answer || ''}
                          onChange={(e) => setEditFormData({ ...editFormData, correct_answer: e.target.value })}
                          placeholder="Nhập đáp án chuẩn..."
                          style={{ flex: 1, padding: '4px 10px', border: '1px solid #CBD5E1', borderRadius: '4px', fontSize: '13px' }}
                        />
                      ) : (
                        <span style={{ fontWeight: 700, color: '#4D308D', fontSize: '14px', background: '#EDE9FE', padding: '3px 12px', borderRadius: '6px', border: '1px solid #DDD6FE' }}>
                          {q.correct_answer || '(Chưa có đáp án)'}
                        </span>
                      )}
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
          <div className="assign-class-group">
            <span className="assign-label">Giao cho lớp:</span>
            <select 
              className="class-select"
              value={assignedClass}
              onChange={(e) => setAssignedClass(e.target.value)}
              disabled={assigning}
            >
              {classList.length > 0 ? (
                classList.map((c) => (
                  <option key={c.class_id} value={c.class_id}>
                    {c.class_name} {c.school_year ? `(${c.school_year})` : ''}
                  </option>
                ))
              ) : (
                <option value="">Không có lớp</option>
              )}
            </select>
          </div>

          <button 
            type="button" 
            className="btn-assign-action"
            onClick={handleAssign}
            disabled={assignedSuccess || assigning || classList.length === 0}
          >
            {assigning ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                <span>Đang giao...</span>
              </>
            ) : assignedSuccess ? (
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
