// File Name: CreateExerciseManualPage.jsx
// Description: Full-page direct exercise creation layout connected to backend APIs (Multiple Choice, True/False, Short Answer).
// Created At: 2026-08-30
// Created By: Tam Khang
// Updated At: 2026-11-20
// Updated By: AI Agent

import React, { useState, useEffect, useRef } from 'react';
import { 
  ChevronRight, 
  Plus, 
  Trash2, 
  Save, 
  ArrowLeft,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Image as ImageIcon,
  Sigma,
  Table2,
  HelpCircle
} from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { exercisesApi, subjectsApi, questionsApi } from '../../services/api';
import MathTextEditor from '../../components/common/MathTextEditor';
import MathSymbolToolbar from '../../components/common/MathSymbolToolbar';
import MathShortcutsHelp from '../../components/common/MathShortcutsHelp';
import '../../components/documents/EditExerciseModal.css';
import './CreateExerciseManualPage.css';
import toast from '../../components/common/toast';
import { getErrorMessage } from '../../utils/errorMessages';

export default function CreateExerciseManualPage() {
  const [showSidebar, setShowSidebar] = useState(true);
  const navigate = useNavigate();

  // Basic Info State
  const [title, setTitle] = useState('');
  const [exerciseType, setExerciseType] = useState('exam'); // 'exam' (Bài kiểm tra), 'practice' (Luyện tập tại nhà)
  const [grade, setGrade] = useState('12');
  const { isGuest, user } = useAuth();
  const [subject, setSubject] = useState('');
  const [duration, setDuration] = useState('15');
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

  // Shared editor tooling: the toolbar inserts into the last focused field.
  const editorRefs = useRef({});
  const activeEditorRef = useRef(null);
  const regEditor = (key) => (r) => { editorRefs.current[key] = r; };
  const setActive = (key) => { activeEditorRef.current = editorRefs.current[key]; };
  const imageInputRef = useRef(null);
  const helpBtnRef = useRef(null);
  const [isHelpOpen, setIsHelpOpen] = useState(false);
  const [tableDims, setTableDims] = useState({ open: false, rows: 3, cols: 3 });
  const [editorFontSize, setEditorFontSize] = useState(14);
  const [isUploadingImage, setIsUploadingImage] = useState(false);
  const getActiveEditor = () => activeEditorRef.current || Object.values(editorRefs.current).find(Boolean);
  const insertMath = (tpl, opts = {}) => getActiveEditor()?.insertMath(tpl, opts);
  const insertTable = () => {
    getActiveEditor()?.insertTable(tableDims.rows, tableDims.cols);
    setTableDims((d) => ({ ...d, open: false }));
  };
  const handleImagePick = async (e) => {
    const file = e.target.files && e.target.files[0];
    e.target.value = '';
    if (!file) return;
    if (!/^image\//.test(file.type || '')) {
      setErrorMsg('Chỉ chấp nhận tệp hình ảnh (png, jpg, jpeg, gif, bmp, webp, svg).');
      return;
    }
    setIsUploadingImage(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const meta = await questionsApi.uploadImage(formData);
      const alt = (meta.original_name || 'hinh-anh').replace(/[[\]]/g, '');
      getActiveEditor()?.insertImage(alt, meta.url);
    } catch (err) {
      setErrorMsg(getErrorMessage(err, 'Không thể tải ảnh lên.'));
    } finally {
      setIsUploadingImage(false);
    }
  };

  // Draft: exercises have no server-side DRAFT state, so drafts live in localStorage per user.
  const draftKey = `manual_exercise_draft:${user?.id ?? user?.user_id ?? 'anon'}`;
  const [pendingDraft, setPendingDraft] = useState(null);
  const [draftReady, setDraftReady] = useState(false);
  const [draftSavedAt, setDraftSavedAt] = useState(null);
  const writeDraft = () => {
    try {
      const snap = {
        title, exerciseType, grade, subject, duration, startTime, dueTime,
        mcqQuestions, tfQuestions, saQuestions, savedAt: Date.now(),
      };
      localStorage.setItem(draftKey, JSON.stringify(snap));
      setDraftSavedAt(snap.savedAt);
      return true;
    } catch {
      return false;
    }
  };
  const clearDraft = () => {
    try { localStorage.removeItem(draftKey); } catch { /* storage unavailable */ }
  };
  const applyDraft = (d) => {
    setTitle(d.title || ''); setExerciseType(d.exerciseType || 'exam'); setGrade(d.grade || '12');
    setSubject(d.subject || ''); setDuration(d.duration || '15');
    setStartTime(d.startTime || ''); setDueTime(d.dueTime || '');
    if (d.mcqQuestions?.length) setMcqQuestions(d.mcqQuestions);
    if (d.tfQuestions?.length) setTfQuestions(d.tfQuestions);
    if (d.saQuestions?.length) setSaQuestions(d.saQuestions);
    setPendingDraft(null);
    setDraftReady(true);
  };
  const handleSaveDraft = () => {
    if (writeDraft()) toast.success('Đã lưu nháp.');
    else toast.error('Không thể lưu nháp trên trình duyệt này.');
  };

  // Offer restore on open; autosave stays off until the teacher decides.
  useEffect(() => {
    try {
      const raw = localStorage.getItem(draftKey);
      if (raw) {
        setPendingDraft(JSON.parse(raw));
        return;
      }
    } catch { /* corrupt or unavailable draft is ignored */ }
    setDraftReady(true);
  }, [draftKey]);

  // Debounced autosave of the in-progress form.
  useEffect(() => {
    if (!draftReady) return undefined;
    const t = setTimeout(writeDraft, 1500);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [draftReady, title, exerciseType, grade, subject, duration, startTime, dueTime, mcqQuestions, tfQuestions, saQuestions]);

  useEffect(() => {
    let isMounted = true;
    async function loadSubjects() {
      try {
        const subjs = await subjectsApi.getSubjects();
        if (isMounted && Array.isArray(subjs)) {
          setSubjectsList(subjs);
          // Guests must choose a subject explicitly; others keep the first as default.
          if (subjs.length > 0 && !isGuest) {
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
        return 'NhanBiet';
      case 'comprehension':
        return 'ThongHieu';
      case 'application':
        return 'VanDung';
      default:
        return 'NhanBiet';
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

    if (isGuest && !subject) {
      setErrorMsg('Vui lòng chọn môn học.');
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
        exercise_kind: exerciseType === 'exam' ? 'EXAM' : 'PRACTICE',
        total_questions: totalValidQuestions,
        ai_metadata: {
          grade: grade || '12',
          duration: duration ? `${duration} phút` : '15 phút',
          type: exerciseType,
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
          answer_options: [
            {
              content: `a) ${q.content.trim()}`,
              is_correct: q.correctAnswer === 'true',
              display_order: 1,
            },
          ],
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

      setDraftReady(false);
      clearDraft();
      toast.success(`Đã tạo thành công bài tập "${title}" với ${totalValidQuestions} câu hỏi!`);
      navigate('/teacher/exercises');
    } catch (err) {
      setErrorMsg(getErrorMessage(err, 'Có lỗi xảy ra khi lưu bài tập.'));
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

          {pendingDraft && (
            <div style={{ marginBottom: 16, padding: '12px 16px', background: '#F5F3FF', border: '1px solid #C4B5FD', borderRadius: 8, display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
              <span>
                Có bản nháp chưa hoàn tất{pendingDraft.savedAt ? ` (lưu lúc ${new Date(pendingDraft.savedAt).toLocaleString('vi-VN')})` : ''}. Bạn có muốn khôi phục không?
              </span>
              <button type="button" className="btn-add-question" onClick={() => applyDraft(pendingDraft)}>Khôi phục</button>
              <button type="button" className="btn-footer-cancel" onClick={() => { clearDraft(); setPendingDraft(null); setDraftReady(true); }}>Bỏ nháp</button>
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

            {/* Row 2: Khối, Môn học, Thời gian */}
            <div className="form-grid-3">
              <div className="form-field-item">
                <label className="field-label">Khối *</label>
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
                <label className="field-label">Môn học {isGuest ? '*' : ''}</label>
                <select
                  className="custom-select-input"
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                  required={isGuest}
                >
                  <option value="" disabled={isGuest}>{isGuest ? 'Chọn môn học' : 'Mặc định'}</option>
                  {subjectsList.map((s) => (
                    <option key={s.subject_id} value={s.subject_id}>{s.subject_name}</option>
                  ))}
                </select>
              </div>

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

          {/* CARD 2: CÂU HỎI VÀ ĐÁP ÁN */}
          <div className="form-card-section">
            <h2 className="section-card-title">Câu hỏi và Đáp án</h2>

            {/* Shared formula toolbar: inserts into the last focused field */}
            <MathSymbolToolbar onInsert={(tpl) => insertMath(tpl)} />
            <div className="toolbar-bottom-actions" style={{ position: 'relative' }}>
              <button type="button" className="btn-toolbar-tool" onMouseDown={(e) => e.preventDefault()}
                onClick={() => imageInputRef.current && imageInputRef.current.click()} disabled={isUploadingImage}
                title="Tải ảnh từ máy lên rồi chèn vào ô đang soạn thảo">
                {isUploadingImage ? <Loader2 size={14} className="animate-spin" /> : <ImageIcon size={14} />}
                <span>{isUploadingImage ? 'Đang tải ảnh...' : 'Chèn hình ảnh'}</span>
              </button>
              <input ref={imageInputRef} type="file" accept="image/*" style={{ display: 'none' }} onChange={handleImagePick} />
              {[['PT bậc 2', '#?x^2+#?x+#?=0'], ['PT bậc 3', '#?x^3+#?x^2+#?x+#?=0'], ['PT bậc 4', '#?x^4+#?x^3+#?x^2+#?x+#?=0']].map(([label, tpl]) => (
                <button key={label} type="button" className="btn-toolbar-tool" onMouseDown={(e) => e.preventDefault()}
                  onClick={() => insertMath(tpl, { display: true })} title={`Chèn ${label.toLowerCase()}`}>
                  <Sigma size={14} /><span>{label}</span>
                </button>
              ))}
              <div style={{ position: 'relative', display: 'inline-block' }}>
                <button type="button" className="btn-toolbar-tool" onMouseDown={(e) => e.preventDefault()}
                  onClick={() => setTableDims((d) => ({ ...d, open: !d.open }))} title="Chèn bảng vào ô đang soạn thảo">
                  <Table2 size={14} /><span>Chèn bảng</span>
                </button>
                {tableDims.open && (
                  <div style={{ position: 'absolute', top: '110%', left: 0, zIndex: 50, background: '#fff', border: '1px solid #E2E8F0', borderRadius: 8, padding: 10, boxShadow: '0 8px 24px rgba(15,23,42,.15)', display: 'flex', gap: 8, alignItems: 'center', whiteSpace: 'nowrap', fontSize: 13 }}>
                    <label>Dòng <input type="number" min={1} max={20} value={tableDims.rows} onChange={(e) => setTableDims((d) => ({ ...d, rows: Number(e.target.value) || 1 }))} style={{ width: 48 }} /></label>
                    <label>Cột <input type="number" min={1} max={10} value={tableDims.cols} onChange={(e) => setTableDims((d) => ({ ...d, cols: Number(e.target.value) || 1 }))} style={{ width: 48 }} /></label>
                    <button type="button" className="btn-toolbar-tool" onMouseDown={(e) => e.preventDefault()} onClick={insertTable}>Chèn</button>
                  </div>
                )}
              </div>
              <button type="button" ref={helpBtnRef} className="btn-toolbar-tool" onMouseDown={(e) => e.preventDefault()}
                onClick={() => setIsHelpOpen((v) => !v)} title="Hướng dẫn phím tắt soạn công thức">
                <HelpCircle size={14} /><span>Hướng dẫn</span>
              </button>
              <label className="btn-toolbar-tool" title="Cỡ chữ vùng soạn thảo">
                <span>Cỡ chữ</span>
                <select value={editorFontSize} onChange={(e) => setEditorFontSize(Number(e.target.value))}
                  style={{ border: 'none', background: 'transparent', font: 'inherit' }}>
                  {[14, 16, 18, 20, 24, 28].map((sz) => (<option key={sz} value={sz}>{sz}px</option>))}
                </select>
              </label>
              <MathShortcutsHelp open={isHelpOpen} onClose={() => setIsHelpOpen(false)} anchorRef={helpBtnRef} />
              <span className="katex-support-hint">Nhấn Alt+= hoặc $ để chèn công thức</span>
            </div>

            {/* SECTION 1: TRẮC NGHIỆM */}
            <div className="question-category-section" style={{ '--math-editor-fs': `${editorFontSize}px` }}>
              <div className="category-header-row">
                <span className="category-title">Phần 1: Trắc nghiệm</span>
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
                      <span className="q-type-label">Trắc nghiệm:</span>
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

                  <MathTextEditor
                    ref={regEditor(`mcq:${q.id}:content`)}
                    className="q-content-textarea"
                    placeholder="Nhập nội dung câu hỏi..."
                    value={q.content}
                    onChange={(val) => setMcqQuestions(prev => prev.map(item => item.id === q.id ? { ...item, content: val } : item))}
                    onFocus={() => setActive(`mcq:${q.id}:content`)}
                    ariaLabel="Question content"
                  />

                  {/* Options 2x2 grid */}
                  <div className="mcq-options-grid">
                    {q.options.map((opt) => (
                      <div key={opt.key} className="mcq-option-field">
                        <input
                          type="radio"
                          name={`correct-mcq-${q.id}`}
                          className="opt-radio-circle"
                          checked={opt.isCorrect}
                          onChange={() => handleSetMcqCorrectOption(q.id, opt.key)}
                          title="Chọn làm đáp án đúng"
                        />
                        <MathTextEditor
                          singleLine
                          ref={regEditor(`mcq:${q.id}:opt:${opt.key}`)}
                          className="opt-text-input"
                          placeholder={`Lựa chọn ${opt.key}...`}
                          value={opt.text}
                          onChange={(val) => handleUpdateMcqOption(q.id, opt.key, val)}
                          onFocus={() => setActive(`mcq:${q.id}:opt:${opt.key}`)}
                          ariaLabel={`Answer option ${opt.key}`}
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
                          name={`cog-mcq-${q.id}`} 
                          checked={q.cognitiveLevel === 'knowledge'}
                          onChange={() => setMcqQuestions(prev => prev.map(item => item.id === q.id ? { ...item, cognitiveLevel: 'knowledge' } : item))}
                        />
                        <span>Nhận biết</span>
                      </label>
                      <label className="cog-radio-item">
                        <input 
                          type="radio" 
                          name={`cog-mcq-${q.id}`} 
                          checked={q.cognitiveLevel === 'comprehension'}
                          onChange={() => setMcqQuestions(prev => prev.map(item => item.id === q.id ? { ...item, cognitiveLevel: 'comprehension' } : item))}
                        />
                        <span>Thông hiểu</span>
                      </label>
                      <label className="cog-radio-item">
                        <input 
                          type="radio" 
                          name={`cog-mcq-${q.id}`} 
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

            {/* SECTION 2: ĐÚNG / SAI */}
            <div className="question-category-section" style={{ '--math-editor-fs': `${editorFontSize}px` }}>
              <div className="category-header-row">
                <span className="category-title">Phần 2: Đúng / Sai</span>
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
                      <span className="q-type-label">Đúng / Sai:</span>
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

                  <MathTextEditor
                    ref={regEditor(`tf:${q.id}:content`)}
                    className="q-content-textarea"
                    placeholder="Nhập nhận định / câu hỏi..."
                    value={q.content}
                    onChange={(val) => setTfQuestions(prev => prev.map(item => item.id === q.id ? { ...item, content: val } : item))}
                    onFocus={() => setActive(`tf:${q.id}:content`)}
                    ariaLabel="Statement content"
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
            <div className="question-category-section" style={{ '--math-editor-fs': `${editorFontSize}px` }}>
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

                  <MathTextEditor
                    ref={regEditor(`sa:${q.id}:content`)}
                    className="q-content-textarea"
                    placeholder="Nhập nội dung câu hỏi..."
                    value={q.content}
                    onChange={(val) => setSaQuestions(prev => prev.map(item => item.id === q.id ? { ...item, content: val } : item))}
                    onFocus={() => setActive(`sa:${q.id}:content`)}
                    ariaLabel="Question content"
                  />

                  {/* Expected answer input */}
                  <div className="sa-answer-box">
                    <label className="sa-label">Đáp án dự kiến</label>
                    <MathTextEditor
                      singleLine
                      ref={regEditor(`sa:${q.id}:answer`)}
                      className="custom-text-input"
                      placeholder="Nhập câu trả lời ngắn..."
                      value={q.expectedAnswer}
                      onChange={(val) => setSaQuestions(prev => prev.map(item => item.id === q.id ? { ...item, expectedAnswer: val } : item))}
                      onFocus={() => setActive(`sa:${q.id}:answer`)}
                      ariaLabel="Expected answer"
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
            <span className="katex-support-hint" style={{ marginRight: 'auto' }}>
              {draftSavedAt ? `Đã tự động lưu nháp lúc ${new Date(draftSavedAt).toLocaleTimeString('vi-VN')}` : 'Chưa lưu nháp'}
            </span>
            <button type="button" className="btn-footer-cancel" onClick={handleSaveDraft} disabled={isSaving}>
              Lưu nháp
            </button>
            <button 
              type="button" 
              className="btn-footer-publish"
              onClick={handleSaveAndPublish}
              disabled={isSaving}
            >
              {isSaving ? (
                <>
                  <Loader2 size={16} className="animate-spin" />
                  <span>Đang lưu...</span>
                </>
              ) : (
                <>
                  <Save size={16} />
                  <span>Lưu & Đăng</span>
                </>
              )}
            </button>
          </div>
    </div>
  );
}
