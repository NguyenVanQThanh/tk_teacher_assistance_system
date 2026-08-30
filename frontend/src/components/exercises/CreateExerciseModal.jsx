// File Name: CreateExerciseModal.jsx
// Description: Multi-method Creation Modal for exercises matching exact 3-card selection design.
// Created At: 2026-08-30
// Created By: Tam Khang
// Updated At: 2026-08-30
// Updated By: Tam Khang

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  X, 
  FileEdit, 
  FileUp, 
  Sparkles, 
  ArrowLeft, 
  UploadCloud, 
  CheckCircle2, 
  AlertCircle 
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
  const [aiTopic, setAiTopic] = useState('');
  const [uploadedFile, setUploadedFile] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  if (!isOpen) return null;

  const handleClose = () => {
    setCurrentStep('select_method');
    setTitle('');
    setAiTopic('');
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

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!title.trim() && currentStep !== 'ai' && currentStep !== 'upload') {
      setErrorMsg('Vui lòng nhập tên bài tập.');
      return;
    }

    setIsSubmitting(true);
    setErrorMsg('');

    let finalTitle = title.trim();
    if (currentStep === 'ai') {
      finalTitle = title.trim() || `Bài tập AI: ${aiTopic || 'Chuyên đề ôn tập'}`;
    } else if (currentStep === 'upload') {
      finalTitle = title.trim() || uploadedFile?.name?.replace(/\.[^/.]+$/, '') || 'Bài tập trích xuất từ file';
    }

    setTimeout(() => {
      setIsSubmitting(false);
      const newExercise = {
        id: Date.now(),
        title: finalTitle,
        type: type,
        grade: grade,
        subject: subject,
        questionCount: currentStep === 'ai' ? '20 câu trắc nghiệm' : '15 câu hỏi',
        duration: '15 phút',
        date: new Date().toLocaleDateString('vi-VN'),
        authorName: 'Thầy Sample Teacher',
        authorInitial: 'ST',
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
      <div className="creation-modal-wrapper" onClick={(e) => e.stopPropagation()}>
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

        {/* ================= STEP 2: DETAIL FORM FOR CHOSEN METHOD ================= */}
        {currentStep !== 'select_method' && (
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
                <h3 className="form-modal-title">
                  {currentStep === 'manual' && 'Tạo bài tập trực tiếp'}
                  {currentStep === 'upload' && 'Tải lên từ file có sẵn (PDF/Word/Excel)'}
                  {currentStep === 'ai' && 'Sinh bài tập tự động bằng AI'}
                </h3>
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
            <form onSubmit={handleSubmit} className="form-modal-body">
              {errorMsg && (
                <div className="form-alert-error">
                  <AlertCircle size={16} />
                  <span>{errorMsg}</span>
                </div>
              )}

              {/* If Upload Method */}
              {currentStep === 'upload' && (
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
              )}

              {/* If AI Method */}
              {currentStep === 'ai' && (
                <div className="ai-prompt-box">
                  <label className="input-field-label">Chủ đề hoặc Yêu cầu tạo bài tập *</label>
                  <textarea
                    rows={3}
                    className="ai-textarea"
                    placeholder="VD: Tạo 15 câu trắc nghiệm Toán 12 về Đạo hàm và Khảo sát đồ thị hàm số, độ khó 60% Thông hiểu, 40% Vận dụng..."
                    value={aiTopic}
                    onChange={(e) => setAiTopic(e.target.value)}
                    required
                  />
                </div>
              )}

              {/* Common title */}
              <div className="form-field-group">
                <label className="input-field-label">Tên bài tập / Đề thi *</label>
                <input
                  type="text"
                  className="text-input"
                  placeholder="VD: Đề kiểm tra 15p – Khối 12"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  required={currentStep === 'manual'}
                />
              </div>

              {/* Common grade & subject */}
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
