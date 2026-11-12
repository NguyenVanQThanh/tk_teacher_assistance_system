// File Name: CreateExerciseModal.jsx
// Description: Multi-method Exercise Creation Modal supporting Direct Manual, Multi-file Upload (Question File & Separate Answer Key), and AI Generation.
// Created At: 2026-08-30
// Created By: Tam Khang
// Updated At: 2026-09-13
// Updated By: Tam Khang

import React, { useState, useRef, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  X, 
  FileEdit, 
  FileUp, 
  Sparkles, 
  ArrowLeft, 
  UploadCloud, 
  SlidersHorizontal,
  GraduationCap,
  FileText,
  BookOpen,
  CheckCircle2, 
  AlertCircle,
  Check,
  ChevronDown,
  Search,
  FolderOpen,
  Loader2,
  FileCheck,
  Lock
} from 'lucide-react';
import { exercisesApi, subjectsApi, documentsApi } from '../../services/api';
import './CreateExerciseModal.css';

const formatFileSize = (bytes) => {
  if (!bytes || bytes <= 0) return '0 KB';
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

// Normalize grade values coming from the API ('Lớp 10', '10', ...) to plain digits ('10')
const normalizeGrade = (grade) => String(grade ?? '').replace(/\D/g, '');

// Modal title per creation method step
const METHOD_TITLES = {
  select_method: 'Lựa chọn hình thức tạo mới',
  ai: 'Tạo sinh bài tập AI',
  upload: 'Tải lên từ file có sẵn (Word / PDF)',
};

export default function CreateExerciseModal({ isOpen, onClose, onCreateSuccess }) {
  const navigate = useNavigate();
  // Step 1: 'select_method', Step 2: 'upload', 'ai'
  const [currentStep, setCurrentStep] = useState('select_method');
  const [title, setTitle] = useState('');
  const [grade, setGrade] = useState('12');
  const [subject, setSubject] = useState('math');
  const [type, setType] = useState('quiz');
  const [exerciseKind, setExerciseKind] = useState('PRACTICE');
  
  // Multi-file upload states
  const [uploadedFile, setUploadedFile] = useState(null);
  const [answerFile, setAnswerFile] = useState(null);
  const [testCode, setTestCode] = useState('');

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [progressPercent, setProgressPercent] = useState(0);
  const [progressStage, setProgressStage] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const [toast, setToast] = useState(null);
  const toastTimerRef = useRef(null);
  const closeTimerRef = useRef(null);
  const [subjectsList, setSubjectsList] = useState([]);

  // AI Generation Specific State
  const [aiPrompt, setAiPrompt] = useState('');
  
  // Question Matrix: MCQ (4 choices), True/False, Short Answer
  const [questionCounts, setQuestionCounts] = useState({
    mcq: { recognize: 0, understand: 0, apply: 0 },
    tf: { recognize: 0, understand: 0, apply: 0 },
    shortAnswer: { recognize: 0, understand: 0, apply: 0 }
  });

  // Available Documents in the teacher's repository (loaded from BE API)
  const [availableDocuments, setAvailableDocuments] = useState([]);

  // Selected Documents for AI Context
  const [selectedDocIds, setSelectedDocIds] = useState([]);
  const [isDocDropdownOpen, setIsDocDropdownOpen] = useState(false);
  const [docSearchQuery, setDocSearchQuery] = useState('');
  const [docGradeFilter, setDocGradeFilter] = useState('all');
  const docDropdownRef = useRef(null);
  // Documents of the teacher still being ingested (hidden from the picker)
  const [processingCount, setProcessingCount] = useState(0);
  // AI result step state: created exercise + RAG sources used
  const [aiResult, setAiResult] = useState(null);
  const [aiFailed, setAiFailed] = useState(false);

  // Documents filtered by search text AND khối (grade block) filter (memoized)
  const filteredDocs = useMemo(() => availableDocuments.filter((doc) => {
    const q = docSearchQuery.trim().toLowerCase();
    const matchSearch = !q || doc.title.toLowerCase().includes(q);
    const matchGrade = docGradeFilter === 'all' || normalizeGrade(doc.grade) === docGradeFilter;
    return matchSearch && matchGrade;
  }), [availableDocuments, docSearchQuery, docGradeFilter]);

  // Modal title changes according to the selected creation method
  // Modal title changes according to the selected creation method
  const modalTitle = METHOD_TITLES[currentStep] || METHOD_TITLES.select_method;

  useEffect(() => {
    if (!isOpen) return undefined;
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

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      isMounted = false;
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  // Load only documents the teacher can use for RAG: own, uploaded, ingested, matching grade/subject
  useEffect(() => {
    if (!isOpen) return undefined;
    let isMounted = true;
    async function loadDocuments() {
      try {
        const params = { grade };
        if (subject) params.subject_id = subject;
        const [res, all] = await Promise.all([
          documentsApi.getUsableDocuments(params),
          documentsApi.getDocuments({ mine: true, status: 'Uploaded', page_size: 1, ...params }),
        ]);
        const items = Array.isArray(res) ? res : (res.items || []);
        if (isMounted) {
          const readyTotal = Array.isArray(res) ? items.length : (res.total ?? items.length);
          const allTotal = Array.isArray(all) ? all.length : (all.total ?? readyTotal);
          setProcessingCount(Math.max(0, allTotal - readyTotal));
          const readyIds = new Set(items.map((d) => d.document_id));
          setSelectedDocIds((prev) => prev.filter((id) => readyIds.has(id)));
          setAvailableDocuments(items.map((d) => ({
            id: d.document_id,
            title: d.title,
            tag: d.document_type || 'Tài liệu',
            size: formatFileSize(d.file_size || 0),
            grade: normalizeGrade(d.grade),
            subjectName: d.subject_name || '',
          })));
        }
      } catch {
        // Keep the picker empty if the repository cannot be loaded
      }
    }
    loadDocuments();
    return () => { isMounted = false; };
  }, [isOpen, grade, subject]);

  // Clear pending toast/close timers when the component unmounts
  useEffect(() => () => {
    if (toastTimerRef.current) clearTimeout(toastTimerRef.current);
    if (closeTimerRef.current) clearTimeout(closeTimerRef.current);
  }, []);

  // Close document dropdown when clicking outside
  function handleClickOutside(event) {
    if (docDropdownRef.current && !docDropdownRef.current.contains(event.target)) {
      setIsDocDropdownOpen(false);
    }
  }

  const toggleDocumentSelection = (docId) => {
    setSelectedDocIds((prev) =>
      prev.includes(docId) ? prev.filter((id) => id !== docId) : [...prev, docId]
    );
  };

  const removeSelectedDocument = (docId, e) => {
    e.stopPropagation();
    setSelectedDocIds((prev) => prev.filter((id) => id !== docId));
  };

  if (!isOpen) return null;

  const handleClose = () => {
    if (isSubmitting) return; // Prevent closing while processing OCR
    if (toastTimerRef.current) {
      clearTimeout(toastTimerRef.current);
      toastTimerRef.current = null;
    }
    if (closeTimerRef.current) {
      clearTimeout(closeTimerRef.current);
      closeTimerRef.current = null;
    }
    setToast(null);
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
    setAiResult(null);
    setAiFailed(false);
    setIsDocDropdownOpen(false);
    setProgressPercent(0);
    setProgressStage('');
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

  const calculateTotalQuestions = () => {
    let total = 0;
    Object.keys(questionCounts).forEach((cat) => {
      Object.keys(questionCounts[cat]).forEach((lvl) => {
        total += questionCounts[cat][lvl];
      });
    });
    return total;
  };

  const showToast = (message, type = 'info', title = '') => {
    if (toastTimerRef.current) clearTimeout(toastTimerRef.current);
    setToast({ message, type, title });
    toastTimerRef.current = setTimeout(() => setToast(null), 4200);
  };

  const handleStartAiGeneration = async (e) => {
    if (e?.preventDefault) e.preventDefault();
    setAiFailed(false);

    const totalQuestions = calculateTotalQuestions();

    if (totalQuestions === 0 && !aiPrompt.trim()) {
      const msg = 'Vui lòng thiết lập số lượng câu hỏi hoặc nhập mô tả yêu cầu.';
      setErrorMsg(msg);
      showToast(msg, 'error', 'Không thể tạo bài tập');
      return;
    }

    setIsSubmitting(true);
    setErrorMsg('');

    try {
      const payload = {
        subject_name: subjectsList[0]?.subject_name || 'Toán học',
        grade_name: `Lớp ${grade}`,
        topic_prompt: aiPrompt.trim() || `Ôn tập kiến thức khối ${grade}`,
        duration_minutes: 45,
      };
      if (selectedDocIds.length > 0) payload.document_ids = selectedDocIds;
      const p1 = questionCounts.mcq.recognize + questionCounts.mcq.understand + questionCounts.mcq.apply;
      const p2 = questionCounts.tf.recognize + questionCounts.tf.understand + questionCounts.tf.apply;
      const p3 = questionCounts.shortAnswer.recognize + questionCounts.shortAnswer.understand + questionCounts.shortAnswer.apply;
      if (p1 > 0) payload.part1_count = p1;
      if (p2 > 0) payload.part2_count = p2;
      if (p3 > 0) payload.part3_count = p3;

      const res = await exercisesApi.generateAiExercise(payload);

      // Persist the custom name entered by the teacher
      if (title.trim() && res.exercise_id) {
        try {
          await exercisesApi.updateExercise(res.exercise_id, { title: title.trim() });
          res.title = title.trim();
        } catch {
          // Title update is best-effort; the exercise was still created
        }
      }

      const createdExercise = {
        id: res.exercise_id,
        title: res.title,
        type: type,
        grade: grade,
        subject: subject,
        subjectName: subjectsList[0]?.subject_name || 'Toán học',
        questionCount: `${res.total_questions || 0} câu hỏi`,
        duration: type === 'quiz' ? '15 phút' : '45 phút',
        date: new Date().toLocaleDateString('vi-VN'),
        authorName: 'Giáo viên',
        authorInitial: 'GV',
        hasShare: true,
      };

      showToast(`Đã tạo thành công bài tập "${res.title}" (${res.total_questions} câu hỏi).`, 'success', 'Tạo bài tập AI thành công');
      if (onCreateSuccess) onCreateSuccess(createdExercise);
      // Stay open on a result step so the teacher can review the sources used
      setAiResult({ title: res.title, total: res.total_questions || 0, sources: Array.isArray(res.sources) ? res.sources : [] });
      setCurrentStep('ai_result');
    } catch (err) {
      const detail = err.response?.data?.detail;
      const isGenFailed = detail && typeof detail === 'object' && detail.code === 'ERR-EXE-AI_GENERATION_FAILED';
      setAiFailed(Boolean(isGenFailed));
      const msg = isGenFailed
        ? 'AI không thể tạo bài tập từ nội dung đã chọn. Hệ thống không tự động thay thế bằng nội dung khác. Thầy/Cô vui lòng thử lại.'
        : (detail && typeof detail === 'object' ? detail.message : detail) || err.message || 'Tạo bài tập AI thất bại. Vui lòng thử lại.';
      setErrorMsg(msg);
      showToast(msg, 'error', 'Bài tập tạo sinh gặp lỗi');
    } finally {
      setIsSubmitting(false);
    }
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

    // Keep files <= 1MB so the vision OCR provider stays stable and fast
    const MAX_IMPORT_BYTES = 1 * 1024 * 1024;
    if (uploadedFile.size > MAX_IMPORT_BYTES) {
      setErrorMsg('File đề bài vượt quá 1MB. Vui lòng nén hoặc tách nhỏ file trước khi tải lên.');
      return;
    }
    if (answerFile && answerFile.size > MAX_IMPORT_BYTES) {
      setErrorMsg('File đáp án vượt quá 1MB. Vui lòng nén hoặc tách nhỏ file trước khi tải lên.');
      return;
    }

    let progressTimer = null;
    try {
      setIsSubmitting(true);
      setErrorMsg('');
      setProgressPercent(8);
      setProgressStage('Đang khởi tạo tác vụ và tải tài liệu lên máy chủ...');

      // Dynamic progress ticker with friendly teacher-oriented stages
      progressTimer = setInterval(() => {
        setProgressPercent((prev) => {
          if (prev < 25) {
            setProgressStage('Đang đọc file và chuẩn bị các trang đề thi sắc nét...');
            return prev + 3;
          } else if (prev < 68) {
            setProgressStage('Đang đọc kỹ từng câu hỏi, hình vẽ & công thức Toán học...');
            return prev + 2;
          } else if (prev < 88) {
            setProgressStage('Đang đối chiếu bảng đáp án và hoàn thiện đề thi...');
            return prev + 1;
          } else if (prev < 96) {
            setProgressStage('Đang lưu bài tập vào kho tài nguyên của Thầy/Cô...');
            return prev + 0.5;
          }
          return prev;
        });
      }, 280);

      const finalTitle = title.trim() || uploadedFile.name.replace(/\.[^/.]+$/, '');
      const targetSubjectId = subjectsList.length > 0 ? subjectsList[0].subject_id : subject;

      // Step 1: Create exercise container in DB
      const newEx = await exercisesApi.createExercise({
        title: finalTitle,
        subject_id: targetSubjectId,
        exercise_kind: exerciseKind,
        total_questions: 0,
        ai_metadata: {
          grade: grade,
          type: type,
        },
      });

      // Step 2: Upload file(s) to bulk import & parse questions with Gemini Vision
      const formData = new FormData();
      formData.append('question_file', uploadedFile);
      if (answerFile) {
        formData.append('answer_file', answerFile);
      }
      if (testCode.trim()) {
        formData.append('test_code', testCode.trim());
      }

      const importedQuestions = await exercisesApi.importQuestions(newEx.exercise_id, formData);

      if (importedQuestions.skippedCount > 0) {
        showToast?.(
          `Đã bóc tách ${importedQuestions.length} câu hỏi, nhưng có ${importedQuestions.skippedCount} câu bị bỏ qua do lỗi dữ liệu (xem log backend để biết chi tiết).`,
          'warning',
          'Cảnh báo import'
        );
      }

      if (progressTimer) clearInterval(progressTimer);
      setProgressPercent(100);
      setProgressStage('Bóc tách hoàn tất! Đang mở bài tập cho Thầy/Cô...');

      await new Promise(r => setTimeout(r, 600));

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
      if (progressTimer) clearInterval(progressTimer);
      setErrorMsg(err.response?.data?.detail?.message || 'Có lỗi xảy ra khi tải lên và bóc tách câu hỏi từ file.');
    } finally {
      if (progressTimer) clearInterval(progressTimer);
      setIsSubmitting(false);
      setProgressPercent(0);
      setProgressStage('');
    }
  };

  return (
    <div className="modal-backdrop-overlay" onClick={handleClose}>
      <div 
        className={`creation-modal-wrapper ${currentStep === 'ai' ? 'modal-ai-mode' : ''}`} 
        onClick={(e) => e.stopPropagation()}
        style={{ position: 'relative' }}
      >
        {/* Toast notification (e.g. AI generation failure) */}
        {toast && (
          <div className={`ai-toast toast-${toast.type}`} role="alert">
            {toast.type === 'error' ? <AlertCircle size={16} /> : <CheckCircle2 size={16} />}
            <div className="ai-toast-text">
              <strong>{toast.title}</strong>
              <span>{toast.message}</span>
            </div>
            <button type="button" className="ai-toast-close" onClick={() => setToast(null)} aria-label="Đóng thông báo">
              <X size={14} />
            </button>
          </div>
        )}
        {/* ================= FULL MODAL OCR PROCESSING OVERLAY (SCREEN LOCK) ================= */}
        {isSubmitting && (
          <div className="modal-ocr-loading-overlay">
            <div className="ocr-loading-icon-wrapper">
              <div className="ocr-loading-spinner" />
              <Sparkles className="ocr-loading-sparkle" size={32} />
            </div>

            <div className="ocr-progress-percent-display">
              {Math.min(100, Math.floor(progressPercent))}%
            </div>

            <h3 className="ocr-loading-heading">
              Đang bóc tách và chuẩn hóa đề thi
            </h3>

            <div className="ocr-progress-bar-container">
              <div className="ocr-progress-track">
                <div 
                  className="ocr-progress-fill" 
                  style={{ width: `${Math.min(100, Math.floor(progressPercent))}%` }} 
                />
              </div>
            </div>

            <p className="ocr-stage-description">
              {progressStage}
            </p>

            <div className="ocr-lock-banner">
              <span>☕ Thầy/Cô đợi xíu nhé, hệ thống đang xử lý bài tập và tạm khóa màn hình để tránh gián đoạn dữ liệu ạ.</span>
            </div>
          </div>
        )}

        {/* ================= STEP 1: METHOD SELECTION ================= */}
        {currentStep === 'select_method' && (
          <div className="method-selection-view">
            {/* Header */}
            <div className="selection-modal-header">
              <h2 className="selection-modal-title">{modalTitle}</h2>
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
              <h2 className="selection-modal-title">{modalTitle}</h2>
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
                  {aiFailed && (
                    <button type="button" className="btn-ai-retry" onClick={handleStartAiGeneration} disabled={isSubmitting}>
                      Thử lại
                    </button>
                  )}
                </div>
              )}

              {/* SECTION: Đặt tên cho bài tập */}
              <div className="ai-config-section">
                <div className="ai-section-header">
                  <FileEdit size={18} className="ai-section-icon" />
                  <span className="ai-section-title">Đặt tên cho bài tập</span>
                </div>
                <input
                  type="text"
                  className="ai-title-input"
                  placeholder="VD: Đề kiểm tra 15 phút chương Đạo hàm - Khối 12"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                />
              </div>

              {/* SECTION 0: Khối lớp (bài tập giao cho khối nào) */}
              <div className="ai-config-section">
                <div className="ai-section-header">
                  <GraduationCap size={18} className="ai-section-icon" />
                  <span className="ai-section-title">Khối lớp (bài tập giao cho khối nào)</span>
                </div>
                <div className="ai-grade-row">
                  <select
                    className="ai-grade-select"
                    value={grade}
                    onChange={(e) => { setGrade(e.target.value); setDocGradeFilter(e.target.value); }}
                    title="Chọn khối lớp cho bài tập"
                  >
                    <option value="10">Khối 10</option>
                    <option value="11">Khối 11</option>
                    <option value="12">Khối 12</option>
                  </select>
                  <span className="ai-grade-hint">SGK của khối và môn đã chọn luôn được tự động sử dụng làm nguồn tham khảo. Khối đã chọn cũng lọc các tài liệu của Thầy/Cô bên dưới.</span>
                </div>
              </div>

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
                      <div className="doc-filter-row">
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
                        <select
                          className="doc-grade-filter"
                          value={docGradeFilter}
                          onChange={(e) => setDocGradeFilter(e.target.value)}
                          onClick={(e) => e.stopPropagation()}
                          title="Lọc tài liệu theo khối lớp"
                        >
                          <option value="all">Tất cả khối</option>
                          <option value="10">Khối 10</option>
                          <option value="11">Khối 11</option>
                          <option value="12">Khối 12</option>
                        </select>
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
                                    {doc.grade
                                      ? <span className="doc-grade-badge">Khối {doc.grade}</span>
                                      : <span className="doc-grade-badge">Chưa gán khối</span>}
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
                      {processingCount > 0 && (
                        <div className="empty-docs-text" role="status">
                          {processingCount} tài liệu đang được xử lý, chưa thể sử dụng.
                        </div>
                      )}
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

        {/* ================= STEP 3: AI RESULT + SOURCES USED ================= */}
        {currentStep === 'ai_result' && aiResult && (
          <div className="ai-creation-view">
            <div className="selection-modal-header">
              <h2 className="selection-modal-title">Đã tạo bài tập thành công</h2>
              <button type="button" className="btn-modal-close" onClick={handleClose} aria-label="Đóng">
                <X size={20} />
              </button>
            </div>
            <div className="ai-modal-content">
              <p>
                Bài tập <strong>{aiResult.title}</strong> ({aiResult.total} câu hỏi) đã được lưu.
              </p>
              <details className="ai-sources">
                <summary>Nguồn tham khảo ({aiResult.sources.length})</summary>
                {aiResult.sources.length === 0 ? (
                  <p className="ai-grade-hint">Không có nguồn tham khảo nào được ghi nhận.</p>
                ) : (
                  <ul className="ai-sources-list">
                    {aiResult.sources.map((s, i) => (
                      <li key={`${s.document_id || 'src'}-${s.page}-${i}`} className="ai-source-item">
                        <span className={`ai-source-badge ${s.source === 'sgk' ? 'sgk' : 'teacher'}`}>
                          {s.source === 'sgk' ? 'SGK' : 'Tài liệu GV'}
                        </span>
                        <span className="ai-source-label">{s.label}</span>
                        {s.page != null && <span className="ai-source-page">Trang {s.page}</span>}
                        {s.image_url && (
                          <a href={`${API_BASE}${s.image_url}`} target="_blank" rel="noopener noreferrer">
                            <img
                              className="ai-source-thumb"
                              src={`${API_BASE}${s.image_url}`}
                              alt={`Hình minh họa: ${s.label}${s.page != null ? `, trang ${s.page}` : ''}`}
                              loading="lazy"
                            />
                          </a>
                        )}
                      </li>
                    ))}
                  </ul>
                )}
              </details>
            </div>
            <div className="ai-action-bar">
              <button type="button" className="btn-create-exercise-gradient" onClick={handleClose}>
                <span>Hoàn tất</span>
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
                <h3 className="form-modal-title">{modalTitle}</h3>
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
                        <span className="dropzone-sub">Hỗ trợ .DOCX, .PDF (tối đa 1MB)</span>
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
                        <span className="dropzone-sub">Hỗ trợ .DOCX, .PDF (tối đa 1MB) nếu có file đáp án tách rời</span>
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
                  <label className="input-field-label">Loại bài</label>
                  <select
                    className="select-input"
                    value={exerciseKind}
                    onChange={(e) => setExerciseKind(e.target.value)}
                  >
                    <option value="PRACTICE">Bài tập luyện tập (hiện đáp án)</option>
                    <option value="EXAM">Đề thi / kiểm tra (ẩn đáp án đến khi công bố)</option>
                  </select>
                </div>

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
