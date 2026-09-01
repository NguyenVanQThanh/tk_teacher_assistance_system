// File Name: CreateExerciseManualPage.jsx
// Description: Full-page direct exercise creation layout with multi-part questions (Multiple Choice, True/False, Short Answer).
// Created At: 2026-08-30
// Created By: Tam Khang
// Updated At: 2026-08-30
// Updated By: Tam Khang

import React, { useState } from 'react';
import { 
  ChevronRight, 
  Plus, 
  Trash2, 
  Save, 
  ArrowLeft,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import Header from '../../components/common/Header';
import TeacherSidebar from '../../components/teacher/TeacherSidebar';
import './CreateExerciseManualPage.css';

export default function CreateExerciseManualPage() {
  const [showSidebar, setShowSidebar] = useState(true);
  const navigate = useNavigate();

  // Basic Info State
  const [title, setTitle] = useState('');
  const [exerciseType, setExerciseType] = useState('exam'); // 'exam' (Bài kiểm tra), 'practice' (Luyện tập tại nhà)
  const [grade, setGrade] = useState('');
  const [duration, setDuration] = useState('');
  const [level, setLevel] = useState('');
  const [startTime, setStartTime] = useState('');
  const [dueTime, setDueTime] = useState('');

  // Part 1: Multiple Choice Questions (4 options)
  const [mcqQuestions, setMcqQuestions] = useState([
    {
      id: 'mcq-1',
      questionNumber: 1,
      content: '',
      options: [
        { key: 'A', text: '', isCorrect: false },
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
          { key: 'A', text: '', isCorrect: false },
          { key: 'B', text: '', isCorrect: false },
          { key: 'C', text: '', isCorrect: false },
          { key: 'D', text: '', isCorrect: false },
        ],
        cognitiveLevel: 'knowledge',
      },
    ]);
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

  const handleSaveAndPublish = () => {
    if (!title.trim()) {
      setErrorMsg('Vui lòng nhập tên bài tập.');
      window.scrollTo({ top: 0, behavior: 'smooth' });
      return;
    }

    setIsSaving(true);
    setErrorMsg('');

    setTimeout(() => {
      setIsSaving(false);
      alert(`Đã lưu và đăng bài tập "${title}" thành công!`);
      navigate('/teacher/exercises');
    }, 700);
  };

  return (
    <div className="create-manual-page-layout">
      {/* Top Header */}
      <Header onToggleSidebar={() => setShowSidebar(!showSidebar)} />

      <div className="create-manual-body">
        {/* Left Sidebar */}
        {showSidebar && (
          <TeacherSidebar 
            activeNav="exercises" 
            onSelectNav={(id) => {
              if (id === 'dashboard') navigate('/teacher');
              else if (id === 'classes') navigate('/teacher/classes');
              else if (id === 'documents') navigate('/teacher/documents');
              else if (id === 'exercises') navigate('/teacher/exercises');
            }} 
          />
        )}

        {/* Main Form Content */}
        <main className="create-manual-main">
          {/* Breadcrumb & Title */}
          <div className="manual-top-header">
            <nav className="breadcrumb-nav">
              <Link to="/teacher" className="breadcrumb-link">Trang chủ</Link>
              <ChevronRight size={14} className="breadcrumb-separator" />
              <Link to="/teacher/exercises" className="breadcrumb-link">Kho bài tập</Link>
              <ChevronRight size={14} className="breadcrumb-separator" />
              <span className="breadcrumb-current">Tạo bài tập mới</span>
            </nav>
            <h1 className="page-main-heading">Tạo bài tập mới</h1>
            <p className="page-sub-desc">
              Thiết lập nội dung và cấu trúc cho bài tập mới.
            </p>
          </div>

          {errorMsg && (
            <div className="alert-box-error">
              <AlertCircle size={18} />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* CARD 1: THÔNG TIN CƠ BẢN */}
          <div className="form-card-section">
            <h2 className="section-card-title">Thông tin cơ bản</h2>

            {/* Row 1: Tên bài tập & Loại bài tập */}
            <div className="form-row-2-1">
              <div className="form-field-item flex-2">
                <label className="field-label">Tên bài tập *</label>
                <input
                  type="text"
                  className="custom-text-input"
                  placeholder="Nhập tên bài tập..."
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  required
                />
              </div>

              <div className="form-field-item flex-1">
                <label className="field-label">Loại bài tập *</label>
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

            {/* Row 2: Khối, Thời gian, Phân loại cấp độ */}
            <div className="form-grid-3">
              {/* Khối */}
              <div className="form-field-item">
                <label className="field-label">Khối *</label>
                <select
                  className="custom-select-input"
                  value={grade}
                  onChange={(e) => setGrade(e.target.value)}
                >
                  <option value="">Chọn khối</option>
                  <option value="10">Khối 10</option>
                  <option value="11">Khối 11</option>
                  <option value="12">Khối 12</option>
                </select>
              </div>

              {/* Thời gian */}
              <div className="form-field-item">
                <label className="field-label">
                  Thời gian làm bài {exerciseType === 'exam' ? '(Phút) *' : '(Tùy chọn)'}
                </label>
                <input
                  type="text"
                  className="custom-text-input"
                  placeholder="VD: 15, 45, 60 phút"
                  value={duration}
                  onChange={(e) => setDuration(e.target.value)}
                />
              </div>

              {/* Phân loại cấp độ */}
              <div className="form-field-item">
                <label className="field-label">Phân loại cấp độ</label>
                <select
                  className="custom-select-input"
                  value={level}
                  onChange={(e) => setLevel(e.target.value)}
                >
                  <option value="">Chọn cấp độ</option>
                  <option value="basic">Cơ bản (Nhận biết / Thông hiểu)</option>
                  <option value="medium">Trung bình (Vận dụng)</option>
                  <option value="advanced">Nâng cao (Vận dụng cao)</option>
                </select>
              </div>
            </div>

            {/* Row 3: Giờ mở bài & Hạn nộp bài */}
            <div className="form-grid-2">
              <div className="form-field-item">
                <label className="field-label">Giờ mở bài (Tùy chọn)</label>
                <input
                  type="datetime-local"
                  className="custom-text-input"
                  value={startTime}
                  onChange={(e) => setStartTime(e.target.value)}
                />
              </div>

              <div className="form-field-item">
                <label className="field-label">Hạn nộp bài (Tùy chọn)</label>
                <input
                  type="datetime-local"
                  className="custom-text-input"
                  value={dueTime}
                  onChange={(e) => setDueTime(e.target.value)}
                />
              </div>
            </div>
          </div>

          {/* CARD 2: NỘI DUNG CÂU HỎI */}
          <div className="form-card-section">
            <h2 className="section-card-title">Nội dung câu hỏi</h2>

            {/* SECTION 1: TRẮC NGHIỆM 4 LỰA CHỌN */}
            <div className="question-category-section">
              <div className="category-header-row">
                <span className="category-title">Phần 1: Trắc nghiệm 4 lựa chọn</span>
                <button 
                  type="button" 
                  className="btn-add-question"
                  onClick={handleAddMcq}
                >
                  <Plus size={16} />
                  <span>Thêm câu hỏi</span>
                </button>
              </div>

              {mcqQuestions.map((q, idx) => (
                <div key={q.id} className="question-editor-card">
                  <div className="q-card-header">
                    <div className="q-header-left">
                      <span className="q-badge-purple">Câu {idx + 1}</span>
                      <span className="q-type-label">Trắc nghiệm 4 lựa chọn</span>
                    </div>
                    {mcqQuestions.length > 1 && (
                      <button 
                        type="button" 
                        className="btn-delete-q"
                        onClick={() => handleDeleteMcq(q.id)}
                        title="Xóa câu hỏi này"
                      >
                        <Trash2 size={16} />
                      </button>
                    )}
                  </div>

                  <textarea
                    rows={3}
                    className="q-content-textarea"
                    placeholder="Nhập nội dung câu hỏi..."
                    value={q.content}
                    onChange={(e) => {
                      const val = e.target.value;
                      setMcqQuestions(prev => prev.map(item => item.id === q.id ? { ...item, content: val } : item));
                    }}
                  />

                  {/* 4 Options Grid */}
                  <div className="mcq-options-grid">
                    {q.options.map((opt, oIdx) => (
                      <div key={opt.key} className="mcq-option-field">
                        <input
                          type="radio"
                          name={`correct-opt-${q.id}`}
                          id={`opt-${q.id}-${opt.key}`}
                          checked={opt.isCorrect}
                          onChange={() => {
                            setMcqQuestions(prev => prev.map(item => {
                              if (item.id === q.id) {
                                return {
                                  ...item,
                                  options: item.options.map(o => ({ ...o, isCorrect: o.key === opt.key }))
                                };
                              }
                              return item;
                            }));
                          }}
                          className="opt-radio-circle"
                        />
                        <input
                          type="text"
                          className="opt-text-input"
                          placeholder={`Đáp án ${opt.key}`}
                          value={opt.text}
                          onChange={(e) => {
                            const val = e.target.value;
                            setMcqQuestions(prev => prev.map(item => {
                              if (item.id === q.id) {
                                return {
                                  ...item,
                                  options: item.options.map(o => o.key === opt.key ? { ...o, text: val } : o)
                                };
                              }
                              return item;
                            }));
                          }}
                        />
                      </div>
                    ))}
                  </div>

                  {/* Cognitive level */}
                  <div className="cognitive-level-row">
                    <span className="cog-label">Mức độ nhận thức (Tùy chọn)</span>
                    <div className="cog-radio-group">
                      <label className="cog-radio-item">
                        <input 
                          type="radio" 
                          name={`cog-${q.id}`} 
                          checked={q.cognitiveLevel === 'knowledge'}
                          onChange={() => setMcqQuestions(prev => prev.map(item => item.id === q.id ? { ...item, cognitiveLevel: 'knowledge' } : item))}
                        />
                        <span>Nhận biết</span>
                      </label>
                      <label className="cog-radio-item">
                        <input 
                          type="radio" 
                          name={`cog-${q.id}`} 
                          checked={q.cognitiveLevel === 'comprehension'}
                          onChange={() => setMcqQuestions(prev => prev.map(item => item.id === q.id ? { ...item, cognitiveLevel: 'comprehension' } : item))}
                        />
                        <span>Thông hiểu</span>
                      </label>
                      <label className="cog-radio-item">
                        <input 
                          type="radio" 
                          name={`cog-${q.id}`} 
                          checked={q.cognitiveLevel === 'application'}
                          onChange={() => setMcqQuestions(prev => prev.map(item => item.id === q.id ? { ...item, cognitiveLevel: 'application' } : item))}
                        />
                        <span>Vận dụng</span>
                      </label>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* SECTION 2: TRẮC NGHIỆM ĐÚNG/SAI */}
            <div className="question-category-section">
              <div className="category-header-row">
                <span className="category-title">Phần 2: Trắc nghiệm đúng/sai</span>
                <button 
                  type="button" 
                  className="btn-add-question"
                  onClick={handleAddTf}
                >
                  <Plus size={16} />
                  <span>Thêm câu hỏi</span>
                </button>
              </div>

              {tfQuestions.map((q, idx) => (
                <div key={q.id} className="question-editor-card">
                  <div className="q-card-header">
                    <div className="q-header-left">
                      <span className="q-badge-purple">Câu {mcqQuestions.length + idx + 1}</span>
                      <span className="q-type-label">Trắc nghiệm đúng/sai:</span>
                    </div>
                    {tfQuestions.length > 1 && (
                      <button 
                        type="button" 
                        className="btn-delete-q"
                        onClick={() => handleDeleteTf(q.id)}
                        title="Xóa câu hỏi này"
                      >
                        <Trash2 size={16} />
                      </button>
                    )}
                  </div>

                  <textarea
                    rows={3}
                    className="q-content-textarea"
                    placeholder="Nhập nội dung câu hỏi..."
                    value={q.content}
                    onChange={(e) => {
                      const val = e.target.value;
                      setTfQuestions(prev => prev.map(item => item.id === q.id ? { ...item, content: val } : item));
                    }}
                  />

                  {/* True / False choices */}
                  <div className="tf-options-row">
                    <label className={`tf-pill-item ${q.correctAnswer === 'true' ? 'is-active' : ''}`}>
                      <input
                        type="radio"
                        name={`tf-opt-${q.id}`}
                        checked={q.correctAnswer === 'true'}
                        onChange={() => setTfQuestions(prev => prev.map(item => item.id === q.id ? { ...item, correctAnswer: 'true' } : item))}
                      />
                      <span>Đúng</span>
                    </label>

                    <label className={`tf-pill-item ${q.correctAnswer === 'false' ? 'is-active' : ''}`}>
                      <input
                        type="radio"
                        name={`tf-opt-${q.id}`}
                        checked={q.correctAnswer === 'false'}
                        onChange={() => setTfQuestions(prev => prev.map(item => item.id === q.id ? { ...item, correctAnswer: 'false' } : item))}
                      />
                      <span>Sai</span>
                    </label>
                  </div>

                  {/* Cognitive level */}
                  <div className="cognitive-level-row">
                    <span className="cog-label">Mức độ nhận thức (Tùy chọn)</span>
                    <div className="cog-radio-group">
                      <label className="cog-radio-item">
                        <input 
                          type="radio" 
                          name={`cog-tf-${q.id}`} 
                          checked={q.cognitiveLevel === 'knowledge'}
                          onChange={() => setTfQuestions(prev => prev.map(item => item.id === q.id ? { ...item, cognitiveLevel: 'knowledge' } : item))}
                        />
                        <span>Nhận biết</span>
                      </label>
                      <label className="cog-radio-item">
                        <input 
                          type="radio" 
                          name={`cog-tf-${q.id}`} 
                          checked={q.cognitiveLevel === 'comprehension'}
                          onChange={() => setTfQuestions(prev => prev.map(item => item.id === q.id ? { ...item, cognitiveLevel: 'comprehension' } : item))}
                        />
                        <span>Thông hiểu</span>
                      </label>
                      <label className="cog-radio-item">
                        <input 
                          type="radio" 
                          name={`cog-tf-${q.id}`} 
                          checked={q.cognitiveLevel === 'application'}
                          onChange={() => setTfQuestions(prev => prev.map(item => item.id === q.id ? { ...item, cognitiveLevel: 'application' } : item))}
                        />
                        <span>Vận dụng</span>
                      </label>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* SECTION 3: TRẢ LỜI NGẮN */}
            <div className="question-category-section">
              <div className="category-header-row">
                <span className="category-title">Phần 3: Trả lời ngắn</span>
                <button 
                  type="button" 
                  className="btn-add-question"
                  onClick={handleAddSa}
                >
                  <Plus size={16} />
                  <span>Thêm câu hỏi</span>
                </button>
              </div>

              {saQuestions.map((q, idx) => (
                <div key={q.id} className="question-editor-card">
                  <div className="q-card-header">
                    <div className="q-header-left">
                      <span className="q-badge-purple">Câu {mcqQuestions.length + tfQuestions.length + idx + 1}</span>
                      <span className="q-type-label">Trả lời ngắn:</span>
                    </div>
                    {saQuestions.length > 1 && (
                      <button 
                        type="button" 
                        className="btn-delete-q"
                        onClick={() => handleDeleteSa(q.id)}
                        title="Xóa câu hỏi này"
                      >
                        <Trash2 size={16} />
                      </button>
                    )}
                  </div>

                  <textarea
                    rows={3}
                    className="q-content-textarea"
                    placeholder="Nhập nội dung câu hỏi..."
                    value={q.content}
                    onChange={(e) => {
                      const val = e.target.value;
                      setSaQuestions(prev => prev.map(item => item.id === q.id ? { ...item, content: val } : item));
                    }}
                  />

                  {/* Expected answer input */}
                  <div className="sa-answer-box">
                    <label className="sa-label">Đáp án dự kiến</label>
                    <input
                      type="text"
                      className="custom-text-input"
                      placeholder="Nhập câu trả lời ngắn..."
                      value={q.expectedAnswer}
                      onChange={(e) => {
                        const val = e.target.value;
                        setSaQuestions(prev => prev.map(item => item.id === q.id ? { ...item, expectedAnswer: val } : item));
                      }}
                    />
                  </div>

                  {/* Cognitive level */}
                  <div className="cognitive-level-row">
                    <span className="cog-label">Mức độ nhận thức (Tùy chọn)</span>
                    <div className="cog-radio-group">
                      <label className="cog-radio-item">
                        <input 
                          type="radio" 
                          name={`cog-sa-${q.id}`} 
                          checked={q.cognitiveLevel === 'knowledge'}
                          onChange={() => setSaQuestions(prev => prev.map(item => item.id === q.id ? { ...item, cognitiveLevel: 'knowledge' } : item))}
                        />
                        <span>Nhận biết</span>
                      </label>
                      <label className="cog-radio-item">
                        <input 
                          type="radio" 
                          name={`cog-sa-${q.id}`} 
                          checked={q.cognitiveLevel === 'comprehension'}
                          onChange={() => setSaQuestions(prev => prev.map(item => item.id === q.id ? { ...item, cognitiveLevel: 'comprehension' } : item))}
                        />
                        <span>Thông hiểu</span>
                      </label>
                      <label className="cog-radio-item">
                        <input 
                          type="radio" 
                          name={`cog-sa-${q.id}`} 
                          checked={q.cognitiveLevel === 'application'}
                          onChange={() => setSaQuestions(prev => prev.map(item => item.id === q.id ? { ...item, cognitiveLevel: 'application' } : item))}
                        />
                        <span>Vận dụng</span>
                      </label>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Bottom Action Buttons */}
          <div className="manual-page-footer-actions">
            <button 
              type="button" 
              className="btn-footer-cancel"
              onClick={() => navigate('/teacher/exercises')}
            >
              Hủy
            </button>
            <button 
              type="button" 
              className="btn-footer-publish"
              onClick={handleSaveAndPublish}
              disabled={isSaving}
            >
              <Save size={16} />
              <span>{isSaving ? 'Đang lưu...' : 'Lưu & Đăng'}</span>
            </button>
          </div>
        </main>
      </div>
    </div>
  );
}
