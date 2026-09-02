// File Name: CreateExerciseManualPage.jsx
// Description: Full-page direct exercise creation layout connected to backend APIs (Multiple Choice, True/False, Short Answer).
// Created At: 2026-08-30
// Created By: Tam Khang
// Updated At: 2026-09-01
// Updated By: Tam Khang

import React, { useState, useEffect } from 'react';
import { 
  ChevronRight, 
  Plus, 
  Trash2, 
  Save, 
  ArrowLeft,
  CheckCircle2,
  AlertCircle,
  Loader2
} from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { exercisesApi, subjectsApi } from '../../services/api';
import './CreateExerciseManualPage.css';

export default function CreateExerciseManualPage() {
  const [showSidebar, setShowSidebar] = useState(true);
  const navigate = useNavigate();

  // Basic Info State
  const [title, setTitle] = useState('');
  const [exerciseType, setExerciseType] = useState('exam'); // 'exam' (Bài kiểm tra), 'practice' (Luyện tập tại nhà)
  const [grade, setGrade] = useState('12');
  const [subject, setSubject] = useState('');
  const [duration, setDuration] = useState('15');
  const [level, setLevel] = useState('basic');
  const [startTime, setStartTime] = useState('');
  const [dueTime, setDueTime] = useState('');

  const [subjectsList, setSubjectsList] = useState([]);

  // Part 1: Multiple Choice Questions (4 options)
  const [mcqQuestions, setMcqQuestions] = useState([
    {
      id: 'mcq-1',
      questionNumber: 1,
      content: '',
      options: [
        { key: 'A', text: '', isCorrect: true },
        { key: 'B', text: '', isCorrect: false },
        { key: 'C', text: '', isCorrect: false },
        { key: 'D', text: '', isCorrect: false },
      ],
      cognitiveLevel: 'knowledge', // 'knowledge' (Nhận biết), 'comprehension' (Thông hiểu), 'application' (Vận dụng)
    },
  ]);

  // Part 2: True/False Questions
  const [tfQuestions, setTfQuestions] = useState([
    {
      id: 'tf-1',
      questionNumber: 2,
      content: '',
      correctAnswer: 'true', // 'true' or 'false'
      cognitiveLevel: 'comprehension',
    },
  ]);

  // Part 3: Short Answer Questions
  const [saQuestions, setSaQuestions] = useState([
    {
      id: 'sa-1',
      questionNumber: 3,
      content: '',
      expectedAnswer: '',
      cognitiveLevel: 'application',
    },
  ]);

  const [isSaving, setIsSaving] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    let isMounted = true;
    async function loadSubjects() {
      try {
        const subjs = await subjectsApi.getSubjects();
        if (isMounted && Array.isArray(subjs)) {
          setSubjectsList(subjs);
          if (subjs.length > 0) {
            setSubject(subjs[0].subject_id);
          }
        }
      } catch {
        // Fallback
      }
    }
    loadSubjects();
    return () => {
      isMounted = false;
    };
  }, []);

  // Calculate next question index
  const getTotalQuestionsCount = () => {
    return mcqQuestions.length + tfQuestions.length + saQuestions.length;
  };

  // Add handlers
  const handleAddMcq = () => {
    const nextNum = getTotalQuestionsCount() + 1;
    setMcqQuestions((prev) => [
      ...prev,
      {
        id: `mcq-${Date.now()}`,
        questionNumber: nextNum,
        content: '',
        options: [
          { key: 'A', text: '', isCorrect: true },
          { key: 'B', text: '', isCorrect: false },
          { key: 'C', text: '', isCorrect: false },
          { key: 'D', text: '', isCorrect: false },
        ],
        cognitiveLevel: 'knowledge',
      },
    ]);
  };

  const handleUpdateMcqOption = (qId, optKey, newText) => {
    setMcqQuestions((prev) =>
      prev.map((q) => {
        if (q.id !== qId) return q;
        return {
          ...q,
          options: q.options.map((opt) =>
            opt.key === optKey ? { ...opt, text: newText } : opt
          ),
        };
      })
    );
  };

  const handleSetMcqCorrectOption = (qId, optKey) => {
    setMcqQuestions((prev) =>
      prev.map((q) => {
        if (q.id !== qId) return q;
        return {
          ...q,
          options: q.options.map((opt) => ({
            ...opt,
            isCorrect: opt.key === optKey,
          })),
        };
      })
    );
  };

  const handleDeleteMcq = (id) => {
    setMcqQuestions((prev) => prev.filter((q) => q.id !== id));
  };

  const handleAddTf = () => {
    const nextNum = getTotalQuestionsCount() + 1;
    setTfQuestions((prev) => [
      ...prev,
      {
        id: `tf-${Date.now()}`,
        questionNumber: nextNum,
        content: '',
        correctAnswer: 'true',
        cognitiveLevel: 'comprehension',
      },
    ]);
  };

  const handleDeleteTf = (id) => {
    setTfQuestions((prev) => prev.filter((q) => q.id !== id));
  };

  const handleAddSa = () => {
    const nextNum = getTotalQuestionsCount() + 1;
    setSaQuestions((prev) => [
      ...prev,
      {
        id: `sa-${Date.now()}`,
        questionNumber: nextNum,
        content: '',
        expectedAnswer: '',
        cognitiveLevel: 'application',
      },
    ]);
  };

  const handleDeleteSa = (id) => {
    setSaQuestions((prev) => prev.filter((q) => q.id !== id));
  };

  const mapCognitiveLevel = (levelKey) => {
    switch (levelKey) {
      case 'knowledge':
        return 'Nhận biết';
      case 'comprehension':
        return 'Thông hiểu';
      case 'application':
        return 'Vận dụng';
      default:
        return 'Nhận biết';
    }
  };

  const handleSaveAndPublish = async () => {
    if (!title.trim()) {
      setErrorMsg('Vui lòng nhập tên bài tập.');
      window.scrollTo({ top: 0, behavior: 'smooth' });
      return;
    }

    const validMcqs = mcqQuestions.filter((q) => q.content.trim());
    const validTfs = tfQuestions.filter((q) => q.content.trim());
    const validSas = saQuestions.filter((q) => q.content.trim());
    const totalValidQuestions = validMcqs.length + validTfs.length + validSas.length;

    if (totalValidQuestions === 0) {
      setErrorMsg('Vui lòng nhập nội dung cho ít nhất 1 câu hỏi.');
      window.scrollTo({ top: 0, behavior: 'smooth' });
      return;
    }

    try {
      setIsSaving(true);
      setErrorMsg('');

      let targetSubjectId = subject;
      if (!targetSubjectId && subjectsList.length > 0) {
        targetSubjectId = subjectsList[0].subject_id;
      }

      // Step 1: Create Exercise Record
      const newExercise = await exercisesApi.createExercise({
        title: title.trim(),
        subject_id: targetSubjectId,
        total_questions: totalValidQuestions,
        ai_metadata: {
          grade: grade || '12',
          duration: duration ? `${duration} phút` : '15 phút',
          type: exerciseType,
          level: level,
          start_time: startTime,
          due_time: dueTime,
        },
      });

      let currentOrder = 1;

      // Step 2: Add Multiple Choice Questions
      for (const q of validMcqs) {
        const correctOpt = q.options.find((o) => o.isCorrect);
        const correctKey = correctOpt ? correctOpt.key : 'A';
        const answerOptionsPayload = q.options.map((opt, idx) => ({
          content: opt.text.trim() || `Lựa chọn ${opt.key}`,
          is_correct: opt.isCorrect,
          display_order: idx + 1,
        }));

        await exercisesApi.addQuestion(newExercise.exercise_id, {
          content: q.content.trim(),
          question_type: 'MultipleChoice',
          difficulty: mapCognitiveLevel(q.cognitiveLevel),
          correct_answer: correctKey,
          display_order: currentOrder++,
          answer_options: answerOptionsPayload,
        });
      }

      // Step 3: Add True/False Questions
      for (const q of validTfs) {
        await exercisesApi.addQuestion(newExercise.exercise_id, {
          content: q.content.trim(),
          question_type: 'TrueFalse',
          difficulty: mapCognitiveLevel(q.cognitiveLevel),
          correct_answer: q.correctAnswer === 'true' ? 'Đúng' : 'Sai',
          display_order: currentOrder++,
        });
      }

      // Step 4: Add Short Answer Questions
      for (const q of validSas) {
        await exercisesApi.addQuestion(newExercise.exercise_id, {
          content: q.content.trim(),
          question_type: 'ShortAnswer',
          difficulty: mapCognitiveLevel(q.cognitiveLevel),
          correct_answer: q.expectedAnswer.trim() || 'Đáp án mẫu',
          display_order: currentOrder++,
        });
      }

      alert(`Đã tạo thành công bài tập "${title}" với ${totalValidQuestions} câu hỏi!`);
      navigate('/teacher/exercises');
    } catch (err) {
      setErrorMsg(err.response?.data?.detail?.message || 'Có lỗi xảy ra khi lưu bài tập.');
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="create-manual-main">
          {/* Breadcrumb & Title */}
          <div className="manual-top-header">
            <nav className="breadcrumb-nav">
              <Link to="/teacher" className="breadcrumb-link">Trang chủ</Link>
              <ChevronRight size={14} className="breadcrumb-separator" />
              <Link to="/teacher/exercises" className="breadcrumb-link">Kho bài tập</Link>
              <ChevronRight size={14} className="breadcrumb-separator" />
              <span className="breadcrumb-current">Tạo bài tập mới</span>
            </nav>
            <h1 className="page-main-heading">Tạo bài tập mới (Soạn thảo trực tiếp)</h1>
            <p className="page-sub-desc">
              Tự soạn thảo câu hỏi trắc nghiệm, đúng/sai và điền từ vào đề bài.
            </p>
          </div>

          {/* Error Alert */}
          {errorMsg && (
            <div className="manual-alert-error" style={{ marginBottom: '16px', padding: '12px 16px', background: '#FEF2F2', border: '1px solid #FCA5A5', borderRadius: '8px', color: '#991B1B', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <AlertCircle size={18} />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* CARD 1: THÔNG TIN CƠ BẢN */}
          <div className="form-card-section">
            <h2 className="section-card-title">Thông tin cơ bản</h2>

            {/* Row 1: Tên bài tập & Môn học */}
            <div className="form-row-2-1">
              <div className="form-field-item flex-2">
                <label className="field-label">Tên bài tập / Đề thi *</label>
                <input
                  type="text"
                  className="custom-text-input"
                  placeholder="VD: Kiểm tra 15p Chương 1 – Đạo hàm"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  required
                />
              </div>

              <div className="form-field-item flex-1">
                <label className="field-label">Môn giảng dạy</label>
                <input
                  type="text"
                  className="custom-text-input"
                  value={subjectsList[0]?.subject_name || 'Toán học'}
                  readOnly
                  style={{ backgroundColor: '#F3F4F6', color: '#1F2937', fontWeight: 600, cursor: 'default' }}
                />
              </div>
            </div>

            {/* Row 2: Khối, Thời gian, Loại bài tập */}
            <div className="form-grid-3">
              <div className="form-field-item">
                <label className="field-label">Khối lớp *</label>
                <select
                  className="custom-select-input"
                  value={grade}
                  onChange={(e) => setGrade(e.target.value)}
                >
                  <option value="10">Khối 10</option>
                  <option value="11">Khối 11</option>
                  <option value="12">Khối 12</option>
                </select>
              </div>

              <div className="form-field-item">
                <label className="field-label">Thời gian làm bài (Phút)</label>
                <input
                  type="text"
                  className="custom-text-input"
                  placeholder="VD: 15, 45, 60"
                  value={duration}
                  onChange={(e) => setDuration(e.target.value)}
                />
              </div>

              <div className="form-field-item">
                <label className="field-label">Loại bài tập</label>
                <select
                  className="custom-select-input"
                  value={exerciseType}
                  onChange={(e) => setExerciseType(e.target.value)}
                >
                  <option value="exam">Bài kiểm tra (Tính điểm)</option>
                  <option value="practice">Luyện tập tại nhà</option>
                </select>
              </div>
            </div>
          </div>

          {/* CARD 2: PHẦN 1 - TRẮC NGHIỆM 4 LỰA CHỌN */}
          <div className="form-card-section">
            <div className="section-header-flex">
              <div>
                <h2 className="section-card-title">Phần 1: Trắc nghiệm 4 lựa chọn (MCQ)</h2>
                <p className="section-sub-desc">Mỗi câu hỏi có 4 phương án, chọn 1 phương án đúng nhất</p>
              </div>
              <button 
                type="button" 
                className="btn-add-question-outline"
                onClick={handleAddMcq}
              >
                <Plus size={16} />
                <span>Thêm câu hỏi trắc nghiệm</span>
              </button>
            </div>

            <div className="questions-list-wrapper">
              {mcqQuestions.map((q, qIndex) => (
                <div key={q.id} className="question-composer-card">
                  {/* Header row */}
                  <div className="question-card-top-row">
                    <span className="q-badge-label">Câu {qIndex + 1}</span>
                    <div className="q-actions-right">
                      <select
                        className="level-select-pill"
                        value={q.cognitiveLevel}
                        onChange={(e) => {
                          const val = e.target.value;
                          setMcqQuestions((prev) =>
                            prev.map((item) =>
                              item.id === q.id ? { ...item, cognitiveLevel: val } : item
                            )
                          );
                        }}
                      >
                        <option value="knowledge">Nhận biết</option>
                        <option value="comprehension">Thông hiểu</option>
                        <option value="application">Vận dụng</option>
                      </select>

                      <button
                        type="button"
                        className="btn-trash-action"
                        onClick={() => handleDeleteMcq(q.id)}
                        title="Xóa câu hỏi này"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </div>

                  {/* Question Content */}
                  <div className="question-content-input-group">
                    <textarea
                      className="question-textarea"
                      placeholder="Nhập nội dung câu hỏi (hỗ trợ công thức LaTeX ví dụ $y = x^2$)..."
                      rows={2}
                      value={q.content}
                      onChange={(e) => {
                        const val = e.target.value;
                        setMcqQuestions((prev) =>
                          prev.map((item) =>
                            item.id === q.id ? { ...item, content: val } : item
                          )
                        );
                      }}
                    />
                  </div>

                  {/* 4 Options Grid */}
                  <div className="options-composer-grid">
                    {q.options.map((opt) => (
                      <div
                        key={opt.key}
                        className={`option-composer-item ${opt.isCorrect ? 'is-selected-correct' : ''}`}
                        onClick={() => handleSetMcqCorrectOption(q.id, opt.key)}
                      >
                        <span className="opt-key-badge">{opt.key}</span>
                        <input
                          type="text"
                          className="opt-text-input"
                          placeholder={`Phương án ${opt.key}...`}
                          value={opt.text}
                          onChange={(e) => handleUpdateMcqOption(q.id, opt.key, e.target.value)}
                          onClick={(e) => e.stopPropagation()}
                        />
                        <button
                          type="button"
                          className={`btn-correct-radio ${opt.isCorrect ? 'active' : ''}`}
                          onClick={(e) => {
                            e.stopPropagation();
                            handleSetMcqCorrectOption(q.id, opt.key);
                          }}
                          title="Đánh dấu đáp án đúng"
                        >
                          {opt.isCorrect ? <CheckCircle2 size={18} /> : <div className="radio-circle-empty" />}
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* CARD 3: PHẦN 2 - ĐÚNG / SAI */}
          <div className="form-card-section">
            <div className="section-header-flex">
              <div>
                <h2 className="section-card-title">Phần 2: Trắc nghiệm Đúng / Sai</h2>
                <p className="section-sub-desc">Mỗi câu hỏi học sinh chọn khẳng định là Đúng hoặc Sai</p>
              </div>
              <button 
                type="button" 
                className="btn-add-question-outline"
                onClick={handleAddTf}
              >
                <Plus size={16} />
                <span>Thêm câu hỏi Đúng/Sai</span>
              </button>
            </div>

            <div className="questions-list-wrapper">
              {tfQuestions.map((q, qIndex) => (
                <div key={q.id} className="question-composer-card">
                  <div className="question-card-top-row">
                    <span className="q-badge-label">Câu {mcqQuestions.length + qIndex + 1}</span>
                    <div className="q-actions-right">
                      <select
                        className="level-select-pill"
                        value={q.cognitiveLevel}
                        onChange={(e) => {
                          const val = e.target.value;
                          setTfQuestions((prev) =>
                            prev.map((item) =>
                              item.id === q.id ? { ...item, cognitiveLevel: val } : item
                            )
                          );
                        }}
                      >
                        <option value="knowledge">Nhận biết</option>
                        <option value="comprehension">Thông hiểu</option>
                        <option value="application">Vận dụng</option>
                      </select>

                      <button
                        type="button"
                        className="btn-trash-action"
                        onClick={() => handleDeleteTf(q.id)}
                        title="Xóa câu hỏi này"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </div>

                  <div className="question-content-input-group">
                    <textarea
                      className="question-textarea"
                      placeholder="Nhập nhận định / câu hỏi..."
                      rows={2}
                      value={q.content}
                      onChange={(e) => {
                        const val = e.target.value;
                        setTfQuestions((prev) =>
                          prev.map((item) =>
                            item.id === q.id ? { ...item, content: val } : item
                          )
                        );
                      }}
                    />
                  </div>

                  {/* True / False Choice */}
                  <div className="tf-choice-row">
                    <span className="tf-choice-label">Đáp án đúng:</span>
                    <div className="tf-btn-group">
                      <button
                        type="button"
                        className={`tf-toggle-btn ${q.correctAnswer === 'true' ? 'active-true' : ''}`}
                        onClick={() => {
                          setTfQuestions((prev) =>
                            prev.map((item) =>
                              item.id === q.id ? { ...item, correctAnswer: 'true' } : item
                            )
                          );
                        }}
                      >
                        Đúng
                      </button>
                      <button
                        type="button"
                        className={`tf-toggle-btn ${q.correctAnswer === 'false' ? 'active-false' : ''}`}
                        onClick={() => {
                          setTfQuestions((prev) =>
                            prev.map((item) =>
                              item.id === q.id ? { ...item, correctAnswer: 'false' } : item
                            )
                          );
                        }}
                      >
                        Sai
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* CARD 4: PHẦN 3 - TRẢ LỜI NGẮN */}
          <div className="form-card-section">
            <div className="section-header-flex">
              <div>
                <h2 className="section-card-title">Phần 3: Trắc nghiệm Trả lời ngắn</h2>
                <p className="section-sub-desc">Học sinh tự điền kết quả số hoặc chuỗi ngắn</p>
              </div>
              <button 
                type="button" 
                className="btn-add-question-outline"
                onClick={handleAddSa}
              >
                <Plus size={16} />
                <span>Thêm câu trả lời ngắn</span>
              </button>
            </div>

            <div className="questions-list-wrapper">
              {saQuestions.map((q, qIndex) => (
                <div key={q.id} className="question-composer-card">
                  <div className="question-card-top-row">
                    <span className="q-badge-label">Câu {mcqQuestions.length + tfQuestions.length + qIndex + 1}</span>
                    <div className="q-actions-right">
                      <select
                        className="level-select-pill"
                        value={q.cognitiveLevel}
                        onChange={(e) => {
                          const val = e.target.value;
                          setSaQuestions((prev) =>
                            prev.map((item) =>
                              item.id === q.id ? { ...item, cognitiveLevel: val } : item
                            )
                          );
                        }}
                      >
                        <option value="knowledge">Nhận biết</option>
                        <option value="comprehension">Thông hiểu</option>
                        <option value="application">Vận dụng</option>
                      </select>

                      <button
                        type="button"
                        className="btn-trash-action"
                        onClick={() => handleDeleteSa(q.id)}
                        title="Xóa câu hỏi này"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </div>

                  <div className="question-content-input-group">
                    <textarea
                      className="question-textarea"
                      placeholder="Nhập nội dung câu hỏi tính toán..."
                      rows={2}
                      value={q.content}
                      onChange={(e) => {
                        const val = e.target.value;
                        setSaQuestions((prev) =>
                          prev.map((item) =>
                            item.id === q.id ? { ...item, content: val } : item
                          )
                        );
                      }}
                    />
                  </div>

                  {/* Short Answer Input */}
                  <div className="sa-answer-input-row">
                    <span className="sa-label">Đáp án chuẩn:</span>
                    <input
                      type="text"
                      className="custom-text-input flex-1"
                      placeholder="Nhập kết quả số (VD: 4.5, -2, 100)..."
                      value={q.expectedAnswer}
                      onChange={(e) => {
                        const val = e.target.value;
                        setSaQuestions((prev) =>
                          prev.map((item) =>
                            item.id === q.id ? { ...item, expectedAnswer: val } : item
                          )
                        );
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* BOTTOM SUBMIT BAR */}
          <div className="manual-bottom-actions-bar">
            <button
              type="button"
              className="btn-bottom-cancel"
              onClick={() => navigate('/teacher/exercises')}
              disabled={isSaving}
            >
              Hủy bỏ
            </button>

            <button
              type="button"
              className="btn-bottom-publish"
              onClick={handleSaveAndPublish}
              disabled={isSaving}
              style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
            >
              {isSaving ? (
                <>
                  <Loader2 size={18} className="animate-spin" />
                  <span>Đang lưu bài tập...</span>
                </>
              ) : (
                <>
                  <Save size={18} />
                  <span>Lưu bài tập</span>
                </>
              )}
            </button>
          </div>
    </div>
  );
}
