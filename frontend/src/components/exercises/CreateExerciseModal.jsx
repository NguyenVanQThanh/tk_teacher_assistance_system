// File Name: CreateExerciseModal.jsx
// Description: Multi-method Exercise Creation Modal supporting Direct Manual, Multi-file Upload (Question File & Separate Answer Key), and AI Generation.
// Created At: 2026-08-30
// Created By: Tam Khang
// Updated At: 2026-09-01
// Updated By: Tam Khang

import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  X, 
  FileEdit, 
  FileUp, 
  Sparkles, 
  ArrowLeft, 
  UploadCloud, 
  SlidersHorizontal,
  FileText,
  BookOpen,
  CheckCircle2, 
  AlertCircle,
  Check,
  ChevronDown,
  Search,
  FolderOpen,
  Loader2,
  FileCheck
} from 'lucide-react';
import { exercisesApi, subjectsApi } from '../../services/api';
import './CreateExerciseModal.css';

export default function CreateExerciseModal({ isOpen, onClose, onCreateSuccess }) {
  const navigate = useNavigate();
  // Step 1: 'select_method', Step 2: 'upload', 'ai'
  const [currentStep, setCurrentStep] = useState('select_method');
  const [title, setTitle] = useState('');
  const [grade, setGrade] = useState('12');
  const [subject, setSubject] = useState('math');
  const [type, setType] = useState('quiz');
  
  // Multi-file upload states
  const [uploadedFile, setUploadedFile] = useState(null);
  const [answerFile, setAnswerFile] = useState(null);
  const [testCode, setTestCode] = useState('');

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [subjectsList, setSubjectsList] = useState([]);

  // AI Generation Specific State
  const [aiPrompt, setAiPrompt] = useState('');
  
  // Question Matrix: MCQ (4 choices), True/False, Short Answer
  const [questionCounts, setQuestionCounts] = useState({
    mcq: { recognize: 0, understand: 0, apply: 0 },
    tf: { recognize: 0, understand: 0, apply: 0 },
    shortAnswer: { recognize: 0, understand: 0, apply: 0 }
  });

  // Available Documents in Repository
  const availableDocuments = [
    { id: 'doc-1', title: 'Sách giáo khoa Toán 11', type: 'book', tag: 'Sách giáo khoa', size: '14.2 MB' },
    { id: 'doc-2', title: 'Đề cương ôn tập học kỳ 1', type: 'outline', tag: 'Đề cương', size: '2.4 MB' },
    { id: 'doc-3', title: 'Tài liệu bồi dưỡng HSG', type: 'doc', tag: 'Nâng cao', size: '5.1 MB' },
    { id: 'doc-4', title: 'Bài tập bổ trợ Giải tích 12', type: 'exercise', tag: 'Bài tập', size: '3.8 MB' },
    { id: 'doc-5', title: 'Tuyển tập 50 đề thi thử THPT Quốc Gia - Toán', type: 'doc', tag: 'Đề thi', size: '8.6 MB' },
    { id: 'doc-6', title: 'Chuyên đề Hình học không gian Oxyz', type: 'outline', tag: 'Chuyên đề', size: '4.2 MB' },
    { id: 'doc-7', title: 'Sổ tay công thức Đạo hàm & Tích phân', type: 'book', tag: 'Tóm tắt', size: '1.9 MB' },
  ];

  // Selected Documents for AI Context
  const [selectedDocIds, setSelectedDocIds] = useState([]);
  const [isDocDropdownOpen, setIsDocDropdownOpen] = useState(false);
  const [docSearchQuery, setDocSearchQuery] = useState('');
  const docDropdownRef = useRef(null);

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

  // Close document dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (docDropdownRef.current && !docDropdownRef.current.contains(event.target)) {
        setIsDocDropdownOpen(false);
      }
    }
    if (isDocDropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isDocDropdownOpen]);

  if (!isOpen) return null;

  const handleClose = () => {
    setCurrentStep('select_method');
    setTitle('');
    setAiPrompt('');
    setUploadedFile(null);
    setAnswerFile(null);
    setTestCode('');
    setQuestionCounts({
      mcq: { recognize: 0, understand: 0, apply: 0 },
      tf: { recognize: 0, understand: 0, apply: 0 },
      shortAnswer: { recognize: 0, understand: 0, apply: 0 }
    });
    setSelectedDocIds([]);
    setErrorMsg('');
    setIsSubmitting(false);
    onClose();
  };

  const handleSelectMethod = (method) => {
    if (method === 'manual') {
      handleClose();
      navigate('/teacher/exercises/create-manual');
    } else {
      setCurrentStep(method);
      setErrorMsg('');
    }
  };

  const handleMatrixChange = (qType, level, value) => {
    const num = Math.max(0, parseInt(value, 10) || 0);
    setQuestionCounts((prev) => ({
      ...prev,
      [qType]: {
        ...prev[qType],
        [level]: num,
      },
    }));
  };

  const toggleDocumentSelection = (docId) => {
    setSelectedDocIds((prev) => 
      prev.includes(docId) 
        ? prev.filter((id) => id !== docId)
        : [...prev, docId]
    );
  };

  const removeSelectedDocument = (docId, e) => {
    e.stopPropagation();
    setSelectedDocIds((prev) => prev.filter((id) => id !== docId));
  };

  const filteredDocs = availableDocuments.filter((doc) =>
    doc.title.toLowerCase().includes(docSearchQuery.toLowerCase().trim()) ||
    doc.tag.toLowerCase().includes(docSearchQuery.toLowerCase().trim())
  );

  const handleStartAiGeneration = (e) => {
    e.preventDefault();

    const totalQuestions = 
      Object.values(questionCounts.mcq).reduce((a, b) => a + b, 0) +
      Object.values(questionCounts.tf).reduce((a, b) => a + b, 0) +
      Object.values(questionCounts.shortAnswer).reduce((a, b) => a + b, 0);

    if (totalQuestions === 0 && !aiPrompt.trim()) {
      setErrorMsg('Vui lòng thiết lập số lượng câu hỏi hoặc nhập mô tả yêu cầu.');
      return;
    }

    setIsSubmitting(true);
    setErrorMsg('');

    setTimeout(() => {
      setIsSubmitting(false);
      const generatedTitle = aiPrompt.trim() 
        ? (aiPrompt.length > 40 ? `${aiPrompt.substring(0, 40)}...` : aiPrompt)
        : `Bài tập AI Sinh tự động (${totalQuestions || 10} câu)`;

      const newExercise = {
        id: `ai-${Date.now()}`,
        title: generatedTitle,
        type: 'quiz',
        grade: grade,
        subject: 'math',
        subjectName: subjectsList[0]?.subject_name || 'Toán học',
        questionCount: `${totalQuestions || 10} câu hỏi AI`,
        duration: '20 phút',
        date: new Date().toLocaleDateString('vi-VN'),
        authorName: 'Giáo viên',
        authorInitial: 'GV',
        hasShare: true,
      };

      if (onCreateSuccess) {
        onCreateSuccess(newExercise);
      }
      handleClose();
    }, 800);
  };

  const handleSubmitUpload = async (e) => {
    e.preventDefault();
    if (!uploadedFile) {
      setErrorMsg('Vui lòng chọn file đề bài (.docx hoặc .pdf) để tải lên.');
      return;
    }

    const fileName = uploadedFile.name.toLowerCase();
    if (!fileName.endsWith('.docx') && !fileName.endsWith('.pdf')) {
      setErrorMsg('Hệ thống chỉ hỗ trợ định dạng file .docx hoặc .pdf cho file đề bài.');
      return;
    }

    try {
      setIsSubmitting(true);
      setErrorMsg('');

      const finalTitle = title.trim() || uploadedFile.name.replace(/\.[^/.]+$/, '');
      const targetSubjectId = subjectsList.length > 0 ? subjectsList[0].subject_id : subject;

      // Step 1: Create exercise container in DB
      const newEx = await exercisesApi.createExercise({
        title: finalTitle,
        subject_id: targetSubjectId,
        total_questions: 0,
        ai_metadata: {
          grade: grade,
          type: type,
        },
      });

      // Step 2: Upload file(s) to bulk import & parse questions
      const formData = new FormData();
      formData.append('question_file', uploadedFile);
      if (answerFile) {
        formData.append('answer_file', answerFile);
      }
      if (testCode.trim()) {
        formData.append('test_code', testCode.trim());
      }

      const importedQuestions = await exercisesApi.importQuestions(newEx.exercise_id, formData);

      const createdExercise = {
        id: newEx.exercise_id,
        title: finalTitle,
        type: type,
        grade: grade,
        subject: 'math',
        subjectName: subjectsList[0]?.subject_name || 'Toán học',
        questionCount: `${importedQuestions.length || 0} câu hỏi`,
        duration: type === 'quiz' ? '15 phút' : '45 phút',
        date: new Date().toLocaleDateString('vi-VN'),
        authorName: 'Giáo viên',
        authorInitial: 'GV',
        hasShare: true,
      };

      if (onCreateSuccess) {
        onCreateSuccess(createdExercise);
      }
      handleClose();
    } catch (err) {
      setErrorMsg(err.response?.data?.detail?.message || 'Có lỗi xảy ra khi tải lên và bóc tách câu hỏi từ file.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="modal-backdrop-overlay" onClick={handleClose}>
      <div 
        className={`creation-modal-wrapper ${currentStep === 'ai' ? 'modal-ai-mode' : ''}`} 
        onClick={(e) => e.stopPropagation()}
      >
        {/* ================= STEP 1: METHOD SELECTION ================= */}
        {currentStep === 'select_method' && (
          <div className="method-selection-view">
            {/* Header */}
            <div className="selection-modal-header">
              <h2 className="selection-modal-title">Lựa chọn hình thức tạo mới</h2>
              <button 
                type="button" 
                className="btn-modal-close"
                onClick={handleClose}
                aria-label="Đóng"
              >
                <X size={20} />
              </button>
            </div>

            {/* Body: 3 Method Cards */}
            <div className="method-cards-grid">
              {/* Option 1: Tạo trực tiếp */}
              <div 
                className="method-card card-purple"
                onClick={() => handleSelectMethod('manual')}
              >
                <div className="method-icon-circle icon-purple">
                  <FileEdit size={24} strokeWidth={2.2} />
                </div>
                <h3 className="method-card-title">Tạo trực tiếp trên hệ thống</h3>
                <p className="method-card-desc">
                  Tự soạn thảo nội dung, câu hỏi và đáp án trực tiếp bằng bộ công cụ có sẵn.
                </p>
              </div>

              {/* Option 2: Tải lên từ file */}
              <div 
                className="method-card card-blue"
                onClick={() => handleSelectMethod('upload')}
              >
                <div className="method-icon-circle icon-blue">
                  <FileUp size={24} strokeWidth={2.2} />
                </div>
                <h3 className="method-card-title">Tải lên từ file có sẵn</h3>
                <p className="method-card-desc">
                  Sử dụng file đề bài (kèm hoặc không kèm file đáp án riêng) để hệ thống tự động bóc tách.
                </p>
              </div>

              {/* Option 3: Tạo sinh AI */}
              <div 
                className="method-card card-pink"
                onClick={() => handleSelectMethod('ai')}
              >
                <div className="method-icon-circle icon-pink">
                  <Sparkles size={24} strokeWidth={2.2} />
                </div>
                <h3 className="method-card-title">Tạo sinh bài tập AI</h3>
                <p className="method-card-desc">
                  Sử dụng trí tuệ nhân tạo để tự động tạo câu hỏi dựa trên chủ đề hoặc tài liệu của bạn.
                </p>
              </div>
            </div>

            {/* Footer */}
            <div className="selection-modal-footer">
              <button 
                type="button" 
                className="btn-text-cancel"
                onClick={handleClose}
              >
                Hủy bỏ
              </button>
            </div>
          </div>
        )}

        {/* ================= STEP 2: AI EXERCISE CREATION CONFIG ================= */}
        {currentStep === 'ai' && (
          <div className="ai-creation-view">
            {/* Header */}
            <div className="selection-modal-header">
              <h2 className="selection-modal-title">Lựa chọn hình thức tạo mới</h2>
              <button 
                type="button" 
                className="btn-modal-close"
                onClick={handleClose}
                aria-label="Đóng"
              >
                <X size={20} />
              </button>
            </div>

            <div className="ai-modal-content">
              {errorMsg && (
                <div className="form-alert-error">
                  <AlertCircle size={16} />
                  <span>{errorMsg}</span>
                </div>
              )}

              {/* SECTION 1: Số lượng câu hỏi & Mức độ */}
              <div className="ai-config-section">
                <div className="ai-section-header">
                  <SlidersHorizontal size={18} className="ai-section-icon" />
                  <span className="ai-section-title">Số lượng câu hỏi & Mức độ</span>
                </div>

                <div className="ai-matrix-grid">
                  {/* Card 1: Trắc nghiệm 4 lựa chọn */}
                  <div className="ai-matrix-card">
                    <h4 className="ai-matrix-card-title">Trắc nghiệm 4 lựa chọn</h4>
                    <div className="ai-matrix-inputs-row">
                      <div className="ai-matrix-input-col">
                        <label className="ai-matrix-input-label">NHẬN BIẾT</label>
                        <input 
                          type="number" 
                          min="0"
                          className="ai-matrix-number-input"
                          value={questionCounts.mcq.recognize}
                          onChange={(e) => handleMatrixChange('mcq', 'recognize', e.target.value)}
                        />
                      </div>
                      <div className="ai-matrix-input-col">
                        <label className="ai-matrix-input-label">THÔNG HIỂU</label>
                        <input 
                          type="number" 
                          min="0"
                          className="ai-matrix-number-input"
                          value={questionCounts.mcq.understand}
                          onChange={(e) => handleMatrixChange('mcq', 'understand', e.target.value)}
                        />
                      </div>
                      <div className="ai-matrix-input-col">
                        <label className="ai-matrix-input-label">VẬN DỤNG</label>
                        <input 
                          type="number" 
                          min="0"
                          className="ai-matrix-number-input"
                          value={questionCounts.mcq.apply}
                          onChange={(e) => handleMatrixChange('mcq', 'apply', e.target.value)}
                        />
                      </div>
                    </div>
                  </div>

                  {/* Card 2: Trắc nghiệm Đúng/Sai */}
                  <div className="ai-matrix-card">
                    <h4 className="ai-matrix-card-title">Trắc nghiệm Đúng/Sai</h4>
                    <div className="ai-matrix-inputs-row">
                      <div className="ai-matrix-input-col">
                        <label className="ai-matrix-input-label">NHẬN BIẾT</label>
                        <input 
                          type="number" 
                          min="0"
                          className="ai-matrix-number-input"
                          value={questionCounts.tf.recognize}
                          onChange={(e) => handleMatrixChange('tf', 'recognize', e.target.value)}
                        />
                      </div>
                      <div className="ai-matrix-input-col">
                        <label className="ai-matrix-input-label">THÔNG HIỂU</label>
                        <input 
                          type="number" 
                          min="0"
                          className="ai-matrix-number-input"
                          value={questionCounts.tf.understand}
                          onChange={(e) => handleMatrixChange('tf', 'understand', e.target.value)}
                        />
                      </div>
                      <div className="ai-matrix-input-col">
                        <label className="ai-matrix-input-label">VẬN DỤNG</label>
                        <input 
                          type="number" 
                          min="0"
                          className="ai-matrix-number-input"
                          value={questionCounts.tf.apply}
                          onChange={(e) => handleMatrixChange('tf', 'apply', e.target.value)}
                        />
                      </div>
                    </div>
                  </div>

                  {/* Card 3: Trắc nghiệm Trả lời ngắn */}
                  <div className="ai-matrix-card">
                    <h4 className="ai-matrix-card-title">Trắc nghiệm Trả lời ngắn</h4>
                    <div className="ai-matrix-inputs-row">
                      <div className="ai-matrix-input-col">
                        <label className="ai-matrix-input-label">NHẬN BIẾT</label>
                        <input 
                          type="number" 
                          min="0"
                          className="ai-matrix-number-input"
                          value={questionCounts.shortAnswer.recognize}
                          onChange={(e) => handleMatrixChange('shortAnswer', 'recognize', e.target.value)}
                        />
                      </div>
                      <div className="ai-matrix-input-col">
                        <label className="ai-matrix-input-label">THÔNG HIỂU</label>
                        <input 
                          type="number" 
                          min="0"
                          className="ai-matrix-number-input"
                          value={questionCounts.shortAnswer.understand}
                          onChange={(e) => handleMatrixChange('shortAnswer', 'understand', e.target.value)}
                        />
                      </div>
                      <div className="ai-matrix-input-col">
                        <label className="ai-matrix-input-label">VẬN DỤNG</label>
                        <input 
                          type="number" 
                          min="0"
                          className="ai-matrix-number-input"
                          value={questionCounts.shortAnswer.apply}
                          onChange={(e) => handleMatrixChange('shortAnswer', 'apply', e.target.value)}
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* SECTION 2: Chọn tài liệu tham khảo */}
              <div className="ai-config-section">
                <div className="ai-section-header">
                  <BookOpen size={18} className="ai-section-icon" />
                  <span className="ai-section-title">Chọn tài liệu từ Kho tài liệu (Tham khảo nội dung)</span>
                </div>

                <div className="doc-select-custom-wrapper" ref={docDropdownRef}>
                  <div 
                    className="doc-select-input-box"
                    onClick={() => setIsDocDropdownOpen(!isDocDropdownOpen)}
                  >
                    <div className="doc-tags-container">
                      {selectedDocIds.length > 0 ? (
                        selectedDocIds.map((docId) => {
                          const doc = availableDocuments.find((d) => d.id === docId);
                          return (
                            <span key={docId} className="selected-doc-tag">
                              <span className="doc-tag-title">{doc?.title}</span>
                              <button 
                                type="button" 
                                className="btn-remove-tag"
                                onClick={(e) => removeSelectedDocument(docId, e)}
                              >
                                <X size={12} />
                              </button>
                            </span>
                          );
                        })
                      ) : (
                        <span className="placeholder-text">
                          Bấm để chọn 1 hoặc nhiều tài liệu từ kho...
                        </span>
                      )}
                    </div>
                    <ChevronDown size={18} className="arrow-icon" />
                  </div>

                  {/* Dropdown Menu */}
                  {isDocDropdownOpen && (
                    <div className="doc-dropdown-menu">
                      <div className="doc-search-box">
                        <Search size={14} className="doc-search-icon" />
                        <input 
                          type="text" 
                          placeholder="Tìm tài liệu theo tên..."
                          value={docSearchQuery}
                          onChange={(e) => setDocSearchQuery(e.target.value)}
                          onClick={(e) => e.stopPropagation()}
                        />
                      </div>

                      <div className="doc-list-scroll">
                        {filteredDocs.length > 0 ? (
                          filteredDocs.map((doc) => {
                            const isSelected = selectedDocIds.includes(doc.id);
                            return (
                              <div 
                                key={doc.id} 
                                className={`doc-list-item ${isSelected ? 'selected' : ''}`}
                                onClick={() => toggleDocumentSelection(doc.id)}
                              >
                                <div className="doc-checkbox">
                                  {isSelected && <Check size={12} className="check-mark" />}
                                </div>
                                <div className="doc-item-info">
                                  <span className="doc-item-title">{doc.title}</span>
                                  <div className="doc-item-badges">
                                    <span className="doc-type-badge">{doc.tag}</span>
                                    <span className="doc-size-text">{doc.size}</span>
                                  </div>
                                </div>
                              </div>
                            );
                          })
                        ) : (
                          <div className="empty-docs-text">Không tìm thấy tài liệu phù hợp</div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* SECTION 3: Mô tả yêu cầu tạo bài */}
              <div className="ai-config-section">
                <div className="ai-section-header">
                  <FileText size={18} className="ai-section-icon" />
                  <span className="ai-section-title">Mô tả yêu cầu tạo bài (Prompt)</span>
                </div>
                <textarea 
                  className="ai-prompt-textarea"
                  rows={3}
                  placeholder="Nhập hướng dẫn chi tiết cho AI (VD: Tạo đề kiểm tra 15 phút chương Đạo hàm, tập trung vào các câu hỏi tính đạo hàm hàm số hợp và ứng dụng thực tế...)"
                  value={aiPrompt}
                  onChange={(e) => setAiPrompt(e.target.value)}
                />
              </div>
            </div>

            {/* Action Bar */}
            <div className="ai-action-bar">
              <button 
                type="button" 
                className="btn-create-exercise-gradient"
                onClick={handleStartAiGeneration}
                disabled={isSubmitting}
              >
                <Sparkles size={18} />
                <span>{isSubmitting ? 'Đang tạo bài tập...' : 'Bắt đầu tạo bài tập'}</span>
              </button>
            </div>

            {/* Footer Navigation */}
            <div className="ai-modal-bottom-footer">
              <button 
                type="button" 
                className="btn-ai-back"
                onClick={() => setCurrentStep('select_method')}
              >
                <ArrowLeft size={16} />
                <span>Quay lại</span>
              </button>

              <button 
                type="button" 
                className="btn-ai-cancel"
                onClick={handleClose}
              >
                Hủy bỏ
              </button>
            </div>
          </div>
        )}

        {/* ================= STEP 2: UPLOAD FROM FILE METHOD ================= */}
        {currentStep === 'upload' && (
          <div className="method-form-view">
            {/* Header with Back Button */}
            <div className="form-modal-header">
              <div className="form-header-left">
                <button 
                  type="button" 
                  className="btn-back-step"
                  onClick={() => setCurrentStep('select_method')}
                  title="Quay lại chọn hình thức"
                >
                  <ArrowLeft size={18} />
                </button>
                <h3 className="form-modal-title">Tải lên từ file có sẵn (Word / PDF)</h3>
              </div>
              <button 
                type="button" 
                className="btn-modal-close"
                onClick={handleClose}
              >
                <X size={18} />
              </button>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmitUpload} className="form-modal-body">
              {errorMsg && (
                <div className="form-alert-error">
                  <AlertCircle size={16} />
                  <span>{errorMsg}</span>
                </div>
              )}

              {/* 2 Dropzones: File Đề bài & File Đáp án */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
                {/* 1. File Đề bài */}
                <div className="file-upload-dropzone" style={{ minHeight: '140px', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                  <input
                    type="file"
                    id="exercise-file-input"
                    className="hidden-input"
                    accept=".docx,.pdf"
                    onChange={(e) => {
                      if (e.target.files && e.target.files[0]) {
                        setUploadedFile(e.target.files[0]);
                        if (!title) setTitle(e.target.files[0].name.replace(/\.[^/.]+$/, ''));
                      }
                    }}
                  />
                  <label htmlFor="exercise-file-input" className="dropzone-label">
                    <UploadCloud size={32} className="dropzone-icon" />
                    {uploadedFile ? (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '4px' }}>
                        <span className="file-selected-text">
                          <strong>{uploadedFile.name}</strong>
                        </span>
                        <button
                          type="button"
                          onClick={(e) => {
                            e.preventDefault();
                            e.stopPropagation();
                            setUploadedFile(null);
                          }}
                          style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#EF4444', padding: '2px' }}
                        >
                          <X size={14} />
                        </button>
                      </div>
                    ) : (
                      <>
                        <span className="dropzone-title">1. File Đề bài (Bắt buộc) *</span>
                        <span className="dropzone-sub">Hỗ trợ .DOCX, .PDF (chứa câu hỏi & đáp án)</span>
                      </>
                    )}
                  </label>
                </div>

                {/* 2. File Đáp án riêng (Tùy chọn) */}
                <div className="file-upload-dropzone" style={{ minHeight: '140px', display: 'flex', flexDirection: 'column', justifyContent: 'center', borderColor: '#E2E8F0' }}>
                  <input
                    type="file"
                    id="answer-file-input"
                    className="hidden-input"
                    accept=".docx,.pdf,.xlsx,.xls,.txt"
                    onChange={(e) => {
                      if (e.target.files && e.target.files[0]) {
                        setAnswerFile(e.target.files[0]);
                      }
                    }}
                  />
                  <label htmlFor="answer-file-input" className="dropzone-label">
                    <FileCheck size={32} style={{ color: '#10B981', marginBottom: '6px' }} />
                    {answerFile ? (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '4px' }}>
                        <span style={{ fontSize: '13.5px', color: '#047857', fontWeight: 500 }}>
                          <strong>{answerFile.name}</strong>
                        </span>
                        <button
                          type="button"
                          onClick={(e) => {
                            e.preventDefault();
                            e.stopPropagation();
                            setAnswerFile(null);
                          }}
                          style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#EF4444', padding: '2px' }}
                        >
                          <X size={14} />
                        </button>
                      </div>
                    ) : (
                      <>
                        <span className="dropzone-title">2. File Đáp án riêng (Tùy chọn)</span>
                        <span className="dropzone-sub">Hỗ trợ .DOCX, .PDF nếu có file đáp án tách rời</span>
                      </>
                    )}
                  </label>
                </div>
              </div>

              {/* Title */}
              <div className="form-field-group">
                <label className="input-field-label">Tên bài tập / Đề thi *</label>
                <input
                  type="text"
                  className="text-input"
                  placeholder="VD: Đề kiểm tra 15p – Khối 12"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                />
              </div>

              {/* Grade, Subject & Test Code */}
              <div className="form-row-2">
                <div className="form-field-group">
                  <label className="input-field-label">Khối lớp</label>
                  <select 
                    className="select-input"
                    value={grade}
                    onChange={(e) => setGrade(e.target.value)}
                  >
                    <option value="10">Khối 10</option>
                    <option value="11">Khối 11</option>
                    <option value="12">Khối 12</option>
                  </select>
                </div>

                <div className="form-field-group">
                  <label className="input-field-label">Môn giảng dạy</label>
                  <input
                    type="text"
                    className="select-input"
                    value={subjectsList[0]?.subject_name || 'Toán học'}
                    readOnly
                    style={{ backgroundColor: '#F3F4F6', color: '#1F2937', fontWeight: 600, cursor: 'default' }}
                  />
                </div>

                <div className="form-field-group">
                  <label className="input-field-label">Mã đề thi (Tùy chọn)</label>
                  <input
                    type="text"
                    className="text-input"
                    placeholder="VD: 101, 0121, A..."
                    value={testCode}
                    onChange={(e) => setTestCode(e.target.value)}
                  />
                </div>
              </div>

              {/* Footer */}
              <div className="form-modal-footer">
                <button 
                  type="button" 
                  className="btn-form-cancel"
                  onClick={() => setCurrentStep('select_method')}
                  disabled={isSubmitting}
                >
                  Quay lại
                </button>
                <button 
                  type="submit" 
                  className="btn-form-submit"
                  disabled={isSubmitting}
                  style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 size={16} className="animate-spin" />
                      <span>Đang bóc tách đề thi...</span>
                    </>
                  ) : (
                    <span>Tải lên & Hoàn thành</span>
                  )}
                </button>
              </div>
            </form>
          </div>
        )}
      </div>
    </div>
  );
}
