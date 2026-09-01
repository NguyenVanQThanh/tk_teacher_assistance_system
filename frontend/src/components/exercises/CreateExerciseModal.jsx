// File Name: CreateExerciseModal.jsx
// Description: Multi-method Exercise Creation Modal supporting Direct Manual, File Upload, and AI Generation with Multi-Select Document Dropdown.
// Created At: 2026-08-30
// Created By: Tam Khang
// Updated At: 2026-08-30
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
  FolderOpen
} from 'lucide-react';
import './CreateExerciseModal.css';

export default function CreateExerciseModal({ isOpen, onClose, onCreateSuccess }) {
  const navigate = useNavigate();
  // Step 1: 'select_method', Step 2: 'upload', 'ai'
  const [currentStep, setCurrentStep] = useState('select_method');
  const [title, setTitle] = useState('');
  const [grade, setGrade] = useState('12');
  const [subject, setSubject] = useState('math');
  const [type, setType] = useState('quiz');
  const [uploadedFile, setUploadedFile] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

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
    setQuestionCounts({
      mcq: { recognize: 0, understand: 0, apply: 0 },
      tf: { recognize: 0, understand: 0, apply: 0 },
      shortAnswer: { recognize: 0, understand: 0, apply: 0 }
    });
    setSelectedDocIds([]);
    setIsDocDropdownOpen(false);
    setDocSearchQuery('');
    setUploadedFile(null);
    setErrorMsg('');
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

  const selectedDocsList = availableDocuments.filter((doc) =>
    selectedDocIds.includes(doc.id)
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
        id: Date.now(),
        title: generatedTitle,
        type: 'quiz',
        grade: '12',
        subject: 'math',
        questionCount: `${totalQuestions || 10} câu hỏi AI`,
        duration: '20 phút',
        date: new Date().toLocaleDateString('vi-VN'),
        authorName: 'GV. Nguyễn Văn A',
        authorInitial: 'NA',
        hasShare: true,
      };

      if (onCreateSuccess) {
        onCreateSuccess(newExercise);
      }
      handleClose();
    }, 800);
  };

  const handleSubmitUpload = (e) => {
    e.preventDefault();
    if (!uploadedFile) {
      setErrorMsg('Vui lòng chọn file đề bài tải lên.');
      return;
    }

    setIsSubmitting(true);
    setErrorMsg('');

    setTimeout(() => {
      setIsSubmitting(false);
      const finalTitle = title.trim() || uploadedFile.name.replace(/\.[^/.]+$/, '');
      const newExercise = {
        id: Date.now(),
        title: finalTitle,
        type: type,
        grade: grade,
        subject: subject,
        questionCount: '15 câu hỏi',
        duration: '15 phút',
        date: new Date().toLocaleDateString('vi-VN'),
        authorName: 'GV. Nguyễn Văn A',
        authorInitial: 'NA',
        hasShare: true,
      };
      if (onCreateSuccess) {
        onCreateSuccess(newExercise);
      }
      handleClose();
    }, 600);
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
                  Sử dụng file PDF, DOCX hoặc XLSX có sẵn để hệ thống tự động trích xuất nội dung.
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
            {/* Header matching screenshot */}
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

                  {/* Card 3: Trả lời ngắn */}
                  <div className="ai-matrix-card">
                    <h4 className="ai-matrix-card-title">Trả lời ngắn</h4>
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

              {/* SECTION 2: Chọn tài liệu từ kho (Multi-select Dropdown & Chips) */}
              <div className="ai-config-section">
                <div className="ai-section-header">
                  <FileText size={18} className="ai-section-icon" />
                  <span className="ai-section-title">Chọn tài liệu từ kho</span>
                </div>

                {/* Dropdown Selector */}
                <div className="doc-select-dropdown-container" ref={docDropdownRef}>
                  <div 
                    className={`doc-select-trigger ${isDocDropdownOpen ? 'active' : ''}`}
                    onClick={() => setIsDocDropdownOpen(!isDocDropdownOpen)}
                  >
                    <div className="doc-trigger-left">
                      <FolderOpen size={17} className="doc-trigger-icon" />
                      <span className="doc-trigger-text">
                        {selectedDocIds.length === 0 
                          ? 'Bấm để tìm kiếm & chọn tài liệu từ kho...' 
                          : `Đã chọn ${selectedDocIds.length} tài liệu từ kho`}
                      </span>
                    </div>
                    <div className="doc-trigger-right">
                      {selectedDocIds.length > 0 && (
                        <span className="doc-selected-count-badge">
                          {selectedDocIds.length}
                        </span>
                      )}
                      <ChevronDown 
                        size={18} 
                        className={`doc-chevron-icon ${isDocDropdownOpen ? 'rotate' : ''}`} 
                      />
                    </div>
                  </div>

                  {/* Dropdown Menu Popover */}
                  {isDocDropdownOpen && (
                    <div className="doc-dropdown-menu">
                      {/* Search Inside Dropdown */}
                      <div className="doc-search-box">
                        <Search size={15} className="doc-search-icon" />
                        <input 
                          type="text"
                          className="doc-search-input"
                          placeholder="Tìm kiếm tài liệu theo tên, chuyên đề..."
                          value={docSearchQuery}
                          onChange={(e) => setDocSearchQuery(e.target.value)}
                          onClick={(e) => e.stopPropagation()}
                          autoFocus
                        />
                        {docSearchQuery && (
                          <button 
                            type="button" 
                            className="btn-clear-doc-search"
                            onClick={(e) => {
                              e.stopPropagation();
                              setDocSearchQuery('');
                            }}
                          >
                            <X size={14} />
                          </button>
                        )}
                      </div>

                      {/* Document Options List */}
                      <div className="doc-options-list">
                        {filteredDocs.length > 0 ? (
                          filteredDocs.map((doc) => {
                            const isSelected = selectedDocIds.includes(doc.id);
                            return (
                              <div 
                                key={doc.id}
                                className={`doc-option-item ${isSelected ? 'selected' : ''}`}
                                onClick={() => toggleDocumentSelection(doc.id)}
                              >
                                <div className={`doc-option-checkbox ${isSelected ? 'checked' : ''}`}>
                                  {isSelected && <Check size={12} strokeWidth={3} />}
                                </div>
                                <FileText size={16} className="doc-option-icon" />
                                <div className="doc-option-info">
                                  <span className="doc-option-title">{doc.title}</span>
                                  <div className="doc-option-meta">
                                    <span className="doc-tag-badge">{doc.tag}</span>
                                    <span className="doc-size-text">{doc.size}</span>
                                  </div>
                                </div>
                              </div>
                            );
                          })
                        ) : (
                          <div className="doc-options-empty">
                            Không tìm thấy tài liệu phù hợp.
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>

                {/* Selected Document Chips Displayed Outside */}
                {selectedDocsList.length > 0 && (
                  <div className="ai-selected-docs-wrapper">
                    <div className="ai-docs-chips-grid">
                      {selectedDocsList.map((doc) => (
                        <div 
                          key={doc.id}
                          className="ai-doc-chip selected chip-removable"
                        >
                          <FileText size={16} className="ai-chip-doc-icon" />
                          <span className="ai-chip-title">{doc.title}</span>
                          <button 
                            type="button"
                            className="btn-remove-chip"
                            onClick={(e) => removeSelectedDocument(doc.id, e)}
                            title="Xóa tài liệu này khỏi danh sách chọn"
                          >
                            <X size={14} />
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <p className="ai-docs-help-text">
                  AI sẽ dựa trên nội dung các tài liệu đã chọn để tạo câu hỏi chính xác hơn.
                </p>
              </div>

              {/* SECTION 3: Mô tả yêu cầu (Prompt) */}
              <div className="ai-config-section">
                <div className="ai-section-header">
                  <Sparkles size={18} className="ai-section-icon" />
                  <span className="ai-section-title">Mô tả yêu cầu (Prompt)</span>
                </div>

                <div className="ai-prompt-input-wrapper">
                  <textarea
                    rows={3}
                    className="ai-prompt-custom-textarea"
                    placeholder="Ví dụ: Tạo 10 câu hỏi trắc nghiệm về chương Đạo hàm, mức độ thông hiểu và vận dụng..."
                    value={aiPrompt}
                    onChange={(e) => setAiPrompt(e.target.value)}
                  />
                </div>
              </div>

              {/* ACTION BUTTON */}
              <button 
                type="button" 
                className="btn-start-ai-generate"
                onClick={handleStartAiGeneration}
                disabled={isSubmitting}
              >
                <Sparkles size={18} className="sparkle-btn-icon" />
                <span>{isSubmitting ? 'Đang tạo bài tập...' : 'Bắt đầu tạo bài tập'}</span>
              </button>
            </div>

            {/* Footer Navigation matching screenshot */}
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
                <h3 className="form-modal-title">Tải lên từ file có sẵn (PDF/Word/Excel)</h3>
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

              <div className="file-upload-dropzone">
                <input
                  type="file"
                  id="exercise-file-input"
                  className="hidden-input"
                  accept=".pdf,.docx,.doc,.xlsx,.xls"
                  onChange={(e) => {
                    if (e.target.files && e.target.files[0]) {
                      setUploadedFile(e.target.files[0]);
                      if (!title) setTitle(e.target.files[0].name.replace(/\.[^/.]+$/, ''));
                    }
                  }}
                />
                <label htmlFor="exercise-file-input" className="dropzone-label">
                  <UploadCloud size={36} className="dropzone-icon" />
                  {uploadedFile ? (
                    <span className="file-selected-text">
                      Đã chọn: <strong>{uploadedFile.name}</strong>
                    </span>
                  ) : (
                    <>
                      <span className="dropzone-title">Kéo thả file đề bài hoặc bấm để chọn</span>
                      <span className="dropzone-sub">Hỗ trợ PDF, DOCX, XLSX (AI sẽ tự động nhận diện câu hỏi và đáp án)</span>
                    </>
                  )}
                </label>
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

              {/* Grade & Subject */}
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
                  <label className="input-field-label">Môn học</label>
                  <select 
                    className="select-input"
                    value={subject}
                    onChange={(e) => setSubject(e.target.value)}
                  >
                    <option value="math">Toán học</option>
                    <option value="physics">Vật lý</option>
                    <option value="chemistry">Hóa học</option>
                    <option value="english">Tiếng Anh</option>
                    <option value="it">Tin học</option>
                    <option value="history">Lịch sử</option>
                  </select>
                </div>
              </div>

              {/* Footer */}
              <div className="form-modal-footer">
                <button 
                  type="button" 
                  className="btn-form-cancel"
                  onClick={() => setCurrentStep('select_method')}
                >
                  Quay lại
                </button>
                <button 
                  type="submit" 
                  className="btn-form-submit"
                  disabled={isSubmitting}
                >
                  {isSubmitting ? (
                    <span>Đang xử lý...</span>
                  ) : (
                    <span>Tiếp tục & Hoàn thành</span>
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
