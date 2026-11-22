// File Name: CreateExerciseManualPage.jsx
// Description: Full-page manual exercise creation using the same split layout as the exercise edit modal (question list left, editor right).
// Created At: 2026-08-30
// Created By: Tam Khang
// Updated At: 2026-11-21
// Updated By: AI Agent

import React, { useState, useEffect, useRef } from 'react';
import {
  X, Save, FileEdit, Image as ImageIcon, Plus, Eye, ChevronDown, Check,
  ListOrdered, FileCode2, ListChecks, Trash2, Loader2, Sigma, Table2, HelpCircle,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { exercisesApi, subjectsApi, questionsApi } from '../../services/api';
import MathTextEditor from '../../components/common/MathTextEditor';
import MathShortcutsHelp from '../../components/common/MathShortcutsHelp';
import MathRenderer from '../../components/common/MathRenderer';
import { symbolCategoriesBySubject } from '../../components/common/mathSymbols';
import confirmDialog from '../../components/common/confirmDialog';
import {
  QUESTION_TYPES, fourSlots, convertAnswerSetup, buildQuestionPayload,
} from '../../components/documents/EditExerciseModal';
import '../../components/documents/EditExerciseModal.css';
import './CreateExerciseManualPage.css';
import toast from '../../components/common/toast';
import { getErrorMessage } from '../../utils/errorMessages';

const LEVELS = ['Nhận biết', 'Thông hiểu', 'Vận dụng'];
const TYPE_HINTS = {
  MultipleChoice: 'Chọn 1 đáp án chính xác',
  TrueFalse: 'Chọn Đúng/Sai cho từng mệnh đề',
  ShortAnswer: 'Nhập đáp án',
  Other: 'Danh sách các ý của câu hỏi',
};
const SUBJECT_TABS = [['math', 'Toán học'], ['physics', 'Vật lí'], ['chemistry', 'Hóa học'], ['greek', 'Ký tự Hy Lạp']];

const newQuestion = () => ({
  id: `q-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
  level: 'Nhận biết',
  content: '',
  questionType: 'MultipleChoice',
  options: fourSlots([], 0),
  correctOption: 'A',
  solutionGuide: '',
});

const levelClass = (l) => (l === 'Nhận biết' ? 'badge-level-know' : l === 'Thông hiểu' ? 'badge-level-comp' : 'badge-level-app');

export default function CreateExerciseManualPage() {
  const navigate = useNavigate();
  const { isGuest, user } = useAuth();

  // Exercise metadata
  const [title, setTitle] = useState('');
  const [exerciseKind, setExerciseKind] = useState('EXAM'); // EXAM | PRACTICE
  const [grade, setGrade] = useState('12');
  const [subject, setSubject] = useState('');
  const [duration, setDuration] = useState('15');
  const [startTime, setStartTime] = useState('');
  const [dueTime, setDueTime] = useState('');
  const [subjectsList, setSubjectsList] = useState([]);

  // Questions
  const [questions, setQuestions] = useState(() => [newQuestion()]);
  const [selectedId, setSelectedId] = useState(() => null);
  const active = questions.find((q) => q.id === selectedId) || questions[0];
  const activeIdx = questions.findIndex((q) => q.id === active.id);

  const [isSaving, setIsSaving] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  // Editor tooling: toolbar inserts into the last focused field
  const editorRefs = useRef({});
  const activeEditorRef = useRef(null);
  const setActive = (key) => { activeEditorRef.current = editorRefs.current[key]; };
  const reg = (key) => (r) => { editorRefs.current[key] = r; };
  const getEditor = () => activeEditorRef.current || editorRefs.current.content;
  const insertMath = (tpl, opts = {}) => getEditor()?.insertMath(tpl, opts);
  const [subjectTab, setSubjectTab] = useState('math');
  const symbolData = symbolCategoriesBySubject[subjectTab] || symbolCategoriesBySubject.math;
  const imageInputRef = useRef(null);
  const helpBtnRef = useRef(null);
  const [isHelpOpen, setIsHelpOpen] = useState(false);
  const [tableDims, setTableDims] = useState({ open: false, rows: 3, cols: 3 });
  const [editorFontSize, setEditorFontSize] = useState(14);
  const [isUploadingImage, setIsUploadingImage] = useState(false);

  const updateActive = (patch) =>
    setQuestions((prev) => prev.map((q) => (q.id === active.id ? { ...q, ...patch } : q)));
  const setOption = (key, patch) =>
    updateActive({ options: active.options.map((o) => (o.key === key ? { ...o, ...patch } : o)) });

  const handleSelect = (id) => { activeEditorRef.current = null; setSelectedId(id); };

  const handleAdd = () => {
    const q = newQuestion();
    setQuestions((prev) => [...prev, q]);
    handleSelect(q.id);
  };

  const handleDelete = async () => {
    if (questions.length <= 1) { toast.error('Đề thi cần có ít nhất 1 câu hỏi.'); return; }
    if (!(await confirmDialog('Xóa câu hỏi này khỏi bài?', { title: 'Xóa câu hỏi', confirmText: 'Xóa' }))) return;
    const rest = questions.filter((q) => q.id !== active.id);
    setQuestions(rest);
    handleSelect(rest[Math.max(0, activeIdx - 1)].id);
  };

  const handleChangeType = async (next) => {
    if (next === active.questionType) return;
    const conv = convertAnswerSetup(active.questionType, next, active.options, active.correctOption);
    if (conv.lost && !(await confirmDialog('Đổi loại câu hỏi sẽ bỏ một phần dữ liệu đáp án hiện tại (không còn chỗ chứa). Tiếp tục?', { title: 'Đổi loại câu hỏi', confirmText: 'Tiếp tục' }))) return;
    updateActive({ questionType: next, options: conv.options, correctOption: conv.correctOption });
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
      getEditor()?.insertImage((meta.original_name || 'hinh-anh').replace(/[[\]]/g, ''), meta.url);
    } catch (err) {
      setErrorMsg(getErrorMessage(err, 'Không thể tải ảnh lên.'));
    } finally {
      setIsUploadingImage(false);
    }
  };

  // Draft: exercises have no server-side DRAFT state, so drafts live in localStorage per user.
  const draftKey = `manual_exercise_draft_v2:${user?.id ?? user?.user_id ?? 'anon'}`;
  const [pendingDraft, setPendingDraft] = useState(null);
  const [draftReady, setDraftReady] = useState(false);
  const [draftSavedAt, setDraftSavedAt] = useState(null);
  const writeDraft = () => {
    try {
      const snap = { title, exerciseKind, grade, subject, duration, startTime, dueTime, questions, savedAt: Date.now() };
      localStorage.setItem(draftKey, JSON.stringify(snap));
      setDraftSavedAt(snap.savedAt);
      return true;
    } catch {
      return false;
    }
  };
  const clearDraft = () => { try { localStorage.removeItem(draftKey); } catch { /* storage unavailable */ } };
  const applyDraft = (d) => {
    setTitle(d.title || ''); setExerciseKind(d.exerciseKind || 'EXAM'); setGrade(d.grade || '12');
    setSubject(d.subject || ''); setDuration(d.duration || '15');
    setStartTime(d.startTime || ''); setDueTime(d.dueTime || '');
    if (d.questions?.length) { setQuestions(d.questions); setSelectedId(d.questions[0].id); }
    setPendingDraft(null);
    setDraftReady(true);
  };

  useEffect(() => {
    try {
      const raw = localStorage.getItem(draftKey);
      if (raw) { setPendingDraft(JSON.parse(raw)); return; }
    } catch { /* corrupt or unavailable draft is ignored */ }
    setDraftReady(true);
  }, [draftKey]);

  useEffect(() => {
    if (!draftReady) return undefined;
    const t = setTimeout(writeDraft, 1500);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [draftReady, title, exerciseKind, grade, subject, duration, startTime, dueTime, questions]);

  useEffect(() => {
    let mounted = true;
    subjectsApi.getSubjects().then((subjs) => {
      if (!mounted || !Array.isArray(subjs)) return;
      setSubjectsList(subjs);
      // Guests must choose a subject explicitly; others keep the first as default.
      if (subjs.length > 0 && !isGuest) setSubject((cur) => cur || subjs[0].subject_id);
    }).catch(() => { /* subject list is optional */ });
    return () => { mounted = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fail = (msg) => { setErrorMsg(msg); window.scrollTo({ top: 0, behavior: 'smooth' }); };

  const handleSave = async () => {
    if (!title.trim()) return fail('Vui lòng nhập tên bài tập.');
    const valid = questions.filter((q) => q.content.trim());
    if (valid.length === 0) return fail('Vui lòng nhập nội dung cho ít nhất 1 câu hỏi.');
    if (isGuest && !subject) return fail('Vui lòng chọn môn học.');

    try {
      setIsSaving(true);
      setErrorMsg('');
      const subjectId = subject || subjectsList[0]?.subject_id;
      const created = await exercisesApi.createExercise({
        title: title.trim(),
        subject_id: subjectId,
        exercise_kind: exerciseKind,
        total_questions: valid.length,
        ai_metadata: {
          grade: grade || '12',
          duration: duration ? `${duration} phút` : '15 phút',
          type: exerciseKind === 'EXAM' ? 'exam' : 'practice',
          start_time: startTime,
          due_time: dueTime,
        },
      });
      for (let i = 0; i < valid.length; i += 1) {
        await exercisesApi.addQuestion(created.exercise_id, buildQuestionPayload(valid[i], i + 1));
      }
      setDraftReady(false);
      clearDraft();
      toast.success(`Đã tạo thành công bài tập "${title.trim()}" với ${valid.length} câu hỏi!`);
      navigate('/teacher/exercises');
    } catch (err) {
      fail(getErrorMessage(err, 'Có lỗi xảy ra khi lưu bài tập.'));
    } finally {
      setIsSaving(false);
    }
  };

  const snippet = (q) => (q.content.split('\n').find((l) => l.trim()) || '').trim() || '(Chưa có nội dung câu hỏi)';
  const answersMeta = (q) => {
    if (q.questionType === 'ShortAnswer') return `Đáp án: ${q.correctOption || 'Chưa nhập'}`;
    if (q.questionType === 'TrueFalse') return `${q.options.length} mệnh đề (Đúng/Sai)`;
    if (q.questionType === 'Other') return `${q.options.length} ý`;
    return `${q.options.length} đáp án (${q.correctOption || 'Chưa chọn'}*)`;
  };

  const optionInput = (opt, placeholder) => (
    <MathTextEditor
      singleLine
      ref={reg(`option:${opt.key}`)}
      className="option-choice-input"
      value={opt.text}
      onChange={(v) => setOption(opt.key, { text: v })}
      onFocus={() => setActive(`option:${opt.key}`)}
      placeholder={placeholder}
      ariaLabel={placeholder}
    />
  );

  return (
    <div className="manual-exam-page">
      <div className="edit-modal-dialog">
        {/* HEADER */}
        <header className="edit-modal-header">
          <div className="header-left-cluster">
            <div className="header-icon-badge"><FileEdit size={22} /></div>
            <div className="header-text-block">
              <div className="header-title-row">
                <h2 className="header-main-title">Tạo bài tập mới (Soạn thảo trực tiếp)</h2>
                <span className="header-autosave-notice">
                  <span className="autosave-dot" />
                  {draftSavedAt ? `Đã tự động lưu nháp lúc ${new Date(draftSavedAt).toLocaleTimeString('vi-VN')}` : 'Chưa lưu nháp'}
                </span>
              </div>
              <div className="header-doc-rename-row">
                <div className="doc-rename-input-wrap">
                  <input
                    type="text"
                    className="doc-rename-input"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="Nhập tên bài tập *"
                    aria-label="Tên bài tập"
                  />
                  <FileEdit size={13} className="doc-rename-icon" />
                </div>
                <span className="doc-rename-divider">•</span>
                <select className="doc-grade-filter" value={exerciseKind} onChange={(e) => setExerciseKind(e.target.value)}
                  title="Đề thi sẽ ẩn đáp án với học sinh cho đến khi giáo viên công bố">
                  <option value="EXAM">Đề thi / kiểm tra (Tính điểm)</option>
                  <option value="PRACTICE">Bài tập luyện tập</option>
                </select>
                <span className="doc-rename-divider">•</span>
                <select className="doc-grade-filter" value={grade} onChange={(e) => setGrade(e.target.value)} aria-label="Khối">
                  <option value="10">Khối 10</option>
                  <option value="11">Khối 11</option>
                  <option value="12">Khối 12</option>
                </select>
                <select className="doc-grade-filter" value={subject} onChange={(e) => setSubject(e.target.value)} aria-label="Môn học" required={isGuest}>
                  <option value="" disabled={isGuest}>{isGuest ? 'Chọn môn học *' : 'Môn mặc định'}</option>
                  {subjectsList.map((s) => (<option key={s.subject_id} value={s.subject_id}>{s.subject_name}</option>))}
                </select>
              </div>
              <div className="header-doc-rename-row" style={{ marginTop: 6 }}>
                <label className="doc-rename-label">Giờ mở bài:</label>
                <input type="datetime-local" className="doc-grade-filter" value={startTime} onChange={(e) => setStartTime(e.target.value)} />
                <label className="doc-rename-label">Hạn nộp:</label>
                <input type="datetime-local" className="doc-grade-filter" value={dueTime} onChange={(e) => setDueTime(e.target.value)} />
              </div>
            </div>
          </div>

          <div className="header-right-actions">
            <button type="button" className="btn-header-close" onClick={() => navigate('/teacher/exercises')} disabled={isSaving}>
              <X size={15} /><span>Đóng</span>
            </button>
            <button type="button" className="btn-header-save" onClick={handleSave} disabled={isSaving}>
              {isSaving ? (<><Loader2 size={16} className="animate-spin" /><span>Đang lưu...</span></>) : (<><Save size={16} /><span>Lưu & Đăng</span></>)}
            </button>
          </div>
        </header>

        {/* BODY */}
        <div className="edit-modal-scrollable-body">
          {errorMsg && <div role="alert" className="manual-exam-alert error">{errorMsg}</div>}
          {pendingDraft && (
            <div className="manual-exam-alert draft">
              <span>Có bản nháp chưa hoàn tất{pendingDraft.savedAt ? ` (lưu lúc ${new Date(pendingDraft.savedAt).toLocaleString('vi-VN')})` : ''}. Khôi phục?</span>
              <button type="button" className="btn-add-question-header" onClick={() => applyDraft(pendingDraft)}>Khôi phục</button>
              <button type="button" className="btn-footer-cancel" onClick={() => { clearDraft(); setPendingDraft(null); setDraftReady(true); }}>Bỏ nháp</button>
            </div>
          )}

          {/* Formula toolbar */}
          <section className="formula-toolbar-container">
            <div className="formula-toolbar-top-strip">
              <div className="formula-top-left-cluster">
                <div className="formula-sigma-label"><span className="sigma-symbol">Σ</span><span className="sigma-text">Bảng ký hiệu:</span></div>
                <div className="formula-subject-tabs">
                  {SUBJECT_TABS.map(([k, label]) => (
                    <button key={k} type="button" className={`subject-tab-btn ${subjectTab === k ? 'active' : ''}`} onClick={() => setSubjectTab(k)}>
                      <span>{label}</span>
                    </button>
                  ))}
                </div>
              </div>
              <div className="formula-top-meta-cluster">
                <div className="toolbar-duration-pill-container" title="Thời gian làm bài">
                  <input
                    type="text"
                    className="toolbar-duration-input"
                    value={duration}
                    onChange={(e) => setDuration(e.target.value.replace(/[^0-9]/g, '').slice(0, 3))}
                    placeholder="45"
                  />
                  <span className="toolbar-duration-unit">phút</span>
                </div>
              </div>
            </div>

            <div className="formula-categories-row">
              {symbolData.groups.map((cat, idx) => (
                <div key={idx} className="formula-group-seg">
                  <span className="formula-group-title">{cat.group}</span>
                  <div className="formula-chips-wrap">
                    {cat.items.map((item, i) => (
                      <button key={i} type="button" className="formula-chip-btn" onMouseDown={(e) => e.preventDefault()}
                        onClick={() => insertMath(item.tpl || item.code)} title={`${item.tip} (${item.code})`}>
                        <MathRenderer text={`$${item.display}$`} />
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>

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
                    <button type="button" className="btn-toolbar-tool" onMouseDown={(e) => e.preventDefault()}
                      onClick={() => { getEditor()?.insertTable(tableDims.rows, tableDims.cols); setTableDims((d) => ({ ...d, open: false })); }}>Chèn</button>
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
                  {[14, 16, 18, 20, 24, 28].map((s) => (<option key={s} value={s}>{s}px</option>))}
                </select>
              </label>
              <MathShortcutsHelp open={isHelpOpen} onClose={() => setIsHelpOpen(false)} anchorRef={helpBtnRef} />
            </div>
          </section>

          {/* Split body */}
          <div className="edit-modal-split-body" style={{ '--math-editor-fs': `${editorFontSize}px` }}>
            {/* LEFT: question list */}
            <div className="left-questions-list-col">
              <div className="questions-list-header-bar">
                <div className="list-title-left">
                  <ListOrdered size={16} className="list-icon" />
                  <h3 className="list-main-title">
                    <span>Danh sách câu hỏi</span>
                    <span className="list-title-count">({questions.length} câu hỏi)</span>
                  </h3>
                </div>
                <button type="button" className="btn-add-question-header" onClick={handleAdd}>
                  <Plus size={13} /><span>Thêm câu hỏi</span>
                </button>
              </div>
              <div className="questions-cards-scroll-container">
                {questions.map((q, i) => {
                  const sel = q.id === active.id;
                  return (
                    <div key={q.id} className={`question-item-card ${sel ? 'is-selected' : ''}`} onClick={() => handleSelect(q.id)}>
                      <div className="question-card-top-row">
                        <div className="top-pills-cluster">
                          <span className="pill-qnum">Câu {i + 1}</span>
                          <span className={`pill-qlevel ${levelClass(q.level)}`}>{q.level}</span>
                        </div>
                        {sel && (<span className="pill-active-badge"><span className="active-dot" />Đang chọn</span>)}
                      </div>
                      <p className="question-card-snippet-text"><MathRenderer text={snippet(q)} /></p>
                      <div className="question-card-bottom-row">
                        <span className="meta-left-text">{q.content.includes('$') ? 'Chứa công thức' : 'Văn bản thường'}</span>
                        <span className="meta-right-text">{answersMeta(q)}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* RIGHT: editor */}
            <div className="right-question-editor-col" key={active.id}>
              <div className="editor-col-top-bar">
                <div className="editor-col-title-left">
                  <FileEdit size={16} className="edit-pencil-icon" />
                  <span className="editor-q-label">Chỉnh sửa Câu {activeIdx + 1}</span>
                  <div className="editor-level-inline-wrap" title="Chọn cấp độ tư duy">
                    <select className="editor-level-select" value={active.level} onChange={(e) => updateActive({ level: e.target.value })}>
                      {LEVELS.map((l) => (<option key={l} value={l}>{l}</option>))}
                    </select>
                    <ChevronDown size={13} className="editor-level-chevron" />
                  </div>
                </div>
                <button type="button" className="btn-delete-active-q" onClick={handleDelete} title="Xóa câu hỏi này"
                  style={{ display: 'inline-flex', alignItems: 'center', gap: 4, padding: '5px 9px', borderRadius: 6, border: '1px solid #FECACA', background: '#FEF2F2', color: '#DC2626', fontSize: 12, fontWeight: 500, cursor: 'pointer' }}>
                  <Trash2 size={13} /><span>Xóa câu hỏi</span>
                </button>
              </div>

              <div className="editor-textarea-section">
                <div className="textarea-section-header">
                  <div className="section-header-left"><FileCode2 size={15} /><span>Nội dung bài tập</span></div>
                  <span className="katex-support-hint">Nhấn Alt+= hoặc $ để chèn công thức</span>
                </div>
                <MathTextEditor
                  ref={reg('content')}
                  className="question-latex-textarea"
                  value={active.content}
                  onChange={(v) => updateActive({ content: v })}
                  onFocus={() => setActive('content')}
                  placeholder="Nhập nội dung bài tập... (chọn công thức ở thanh ký hiệu phía trên để chèn)"
                  ariaLabel="Question content"
                />
              </div>

              <section className="solution-and-answers-section">
                <div className="solution-section-header">
                  <div className="solution-header-left">
                    <ListChecks size={18} className="solution-header-icon" />
                    <h3 className="solution-header-title">Thiết lập đáp án</h3>
                  </div>
                  <span className="solution-header-hint">{TYPE_HINTS[active.questionType]}</span>
                </div>

                <div role="radiogroup" aria-label="Question type" style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 12 }}>
                  {QUESTION_TYPES.map((t) => {
                    const on = active.questionType === t.value;
                    return (
                      <button key={t.value} type="button" role="radio" aria-checked={on} onClick={() => handleChangeType(t.value)}
                        style={{ padding: '6px 12px', borderRadius: 6, fontSize: 13, cursor: 'pointer', border: `1px solid ${on ? '#2563EB' : '#CBD5E1'}`, background: on ? '#EFF6FF' : '#FFFFFF', color: on ? '#1D4ED8' : '#334155', fontWeight: on ? 600 : 400 }}>
                        {t.label}
                      </button>
                    );
                  })}
                </div>

                {active.questionType === 'MultipleChoice' && (
                  <div className="options-grid-row">
                    {active.options.map((opt) => {
                      const ok = active.correctOption === opt.key;
                      return (
                        <div key={opt.key} className={`option-choice-card ${ok ? 'is-selected-correct' : ''}`}
                          onClick={() => updateActive({ correctOption: opt.key, options: active.options.map((o) => ({ ...o, isCorrect: o.key === opt.key })) })}>
                          <div className="option-choice-left">
                            <span className={`option-radio-dot ${ok ? 'checked' : ''}`}>{ok && <span className="radio-inner-dot" />}</span>
                            <span className="option-choice-letter">{opt.key}.</span>
                            <div onClick={(e) => e.stopPropagation()} style={{ flex: 1, minWidth: 0 }}>{optionInput(opt, `Nhập đáp án ${opt.key}...`)}</div>
                          </div>
                          {ok && (<div className="option-correct-badge" title="Đáp án chính xác"><Check size={12} strokeWidth={3} /></div>)}
                        </div>
                      );
                    })}
                  </div>
                )}

                {active.questionType === 'TrueFalse' && (
                  <div className="options-grid-row options-grid-row--single">
                    {active.options.map((opt) => (
                      <div key={opt.key} className={`option-choice-card ${opt.isCorrect ? 'is-selected-correct' : ''}`}>
                        <div className="option-choice-left">
                          <span className="option-choice-letter">{opt.key.toLowerCase()})</span>
                          <div style={{ flex: 1, minWidth: 0 }}>{optionInput(opt, `Nhập mệnh đề ${opt.key.toLowerCase()})...`)}</div>
                          <button type="button" onClick={() => setOption(opt.key, { isCorrect: !opt.isCorrect })}
                            style={{ marginLeft: 8, padding: '4px 10px', borderRadius: 6, cursor: 'pointer', border: '1px solid #CBD5E1', fontWeight: 600, background: opt.isCorrect ? '#DCFCE7' : '#FEE2E2', color: opt.isCorrect ? '#166534' : '#991B1B' }}>
                            {opt.isCorrect ? 'Đúng' : 'Sai'}
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {active.questionType === 'ShortAnswer' && (
                  <div className="solution-guide-box">
                    <label className="solution-guide-label">Đáp án (số hoặc biểu thức ngắn)</label>
                    <input type="text" className="option-choice-input" value={active.correctOption || ''}
                      onChange={(e) => updateActive({ correctOption: e.target.value })}
                      placeholder="Nhập đáp án đúng..." aria-label="Short answer value"
                      style={{ width: '100%', padding: '8px 10px', border: '1px solid #CBD5E1', borderRadius: 6 }} />
                  </div>
                )}

                {active.questionType === 'Other' && (
                  <div className="options-grid-row">
                    {active.options.map((opt) => (
                      <div key={opt.key} className="option-choice-card">
                        <div className="option-choice-left">
                          <span className="option-choice-letter">Ý {opt.key}.</span>
                          <div style={{ flex: 1, minWidth: 0 }}>{optionInput(opt, `Nhập ý ${opt.key}...`)}</div>
                          <button type="button" title="Xóa ý này"
                            onClick={() => {
                              const rest = active.options.filter((o) => o.key !== opt.key);
                              const next = rest.length ? rest : [{ key: '1', text: '', isCorrect: false }];
                              updateActive({ options: next.map((o, i) => ({ ...o, key: String(i + 1) })) });
                            }}
                            style={{ marginLeft: 8, border: 'none', background: 'transparent', cursor: 'pointer', color: '#DC2626' }}>
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </div>
                    ))}
                    <button type="button"
                      onClick={() => updateActive({ options: [...active.options, { key: String(active.options.length + 1), text: '', isCorrect: false }] })}
                      style={{ padding: '6px 12px', borderRadius: 6, border: '1px dashed #94A3B8', background: 'transparent', cursor: 'pointer' }}>
                      <Plus size={14} /> Thêm ý
                    </button>
                  </div>
                )}

                <div className="solution-guide-box">
                  <label className="solution-guide-label">Hướng dẫn giải (hiển thị cho học sinh sau khi nộp bài)</label>
                  <MathTextEditor
                    ref={reg('guide')}
                    className="solution-guide-textarea"
                    value={active.solutionGuide}
                    onChange={(v) => updateActive({ solutionGuide: v })}
                    onFocus={() => setActive('guide')}
                    placeholder="Nhập hướng dẫn giải và lời giải chi tiết..."
                    ariaLabel="Solution guide"
                  />
                </div>
              </section>

              {/* Live preview */}
              <div className="editor-preview-section">
                <div className="preview-section-header">
                  <div className="section-header-left"><Eye size={15} className="green-eye-icon" /><span>Xem trước trực quan</span></div>
                  <span className="badge-render-exact">Render chuẩn xác</span>
                </div>
                <div className="preview-rendered-box">
                  <div className="preview-header-lead-row">
                    <span className="preview-qnum-lead">Câu {activeIdx + 1} ({active.level}):</span>
                  </div>
                  <div className="preview-dynamic-body">
                    {active.content.trim()
                      ? active.content.split('\n').filter((l) => l.trim()).map((l, i) => (<div key={i} className="preview-content-line"><MathRenderer text={l} /></div>))
                      : <p className="preview-empty-text">(Chưa có nội dung câu hỏi)</p>}
                  </div>
                  {active.questionType === 'ShortAnswer' ? (
                    <div className="preview-options-container">Đáp án: {active.correctOption || '(Chưa nhập)'}</div>
                  ) : (
                    <div className="preview-options-container">
                      <div className="preview-options-grid">
                        {active.options.map((opt) => {
                          const ok = active.questionType === 'MultipleChoice' ? active.correctOption === opt.key : active.questionType === 'TrueFalse' && opt.isCorrect;
                          const letter = active.questionType === 'TrueFalse' ? `${opt.key.toLowerCase()})` : active.questionType === 'Other' ? `Ý ${opt.key}.` : `${opt.key}.`;
                          return (
                            <div key={opt.key} className={`preview-option-item ${ok ? 'is-correct-preview' : ''}`}>
                              <span className="preview-option-letter">{letter}</span>
                              <span className="preview-option-content"><MathRenderer text={opt.text || `(Chưa nhập ${opt.key})`} /></span>
                              {ok && (<span className="preview-option-check-badge"><Check size={12} strokeWidth={3} /></span>)}
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                  {active.solutionGuide.trim() && (
                    <div className="preview-solution-guide-box">
                      <div className="preview-solution-header"><span className="preview-solution-title">Hướng dẫn giải & Lời giải chi tiết:</span></div>
                      <div className="preview-solution-body">
                        {active.solutionGuide.split('\n').filter((l) => l.trim()).map((l, i) => (<p key={i} className="preview-solution-line"><MathRenderer text={l.trim()} /></p>))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* FOOTER */}
        <footer className="edit-modal-footer">
          <div className="footer-cta-buttons" style={{ marginLeft: 'auto' }}>
            <button type="button" className="btn-footer-cancel" onClick={() => navigate('/teacher/exercises')} disabled={isSaving}>Hủy bỏ</button>
            <button type="button" className="btn-footer-cancel"
              onClick={() => (writeDraft() ? toast.success('Đã lưu nháp.') : toast.error('Không thể lưu nháp trên trình duyệt này.'))}
              disabled={isSaving}>Lưu nháp</button>
            <button type="button" className="btn-footer-confirm" onClick={handleSave} disabled={isSaving}>
              {isSaving ? (<><Loader2 size={16} className="animate-spin" /><span>Đang lưu...</span></>) : (<><Check size={16} /><span>Lưu & Đăng</span></>)}
            </button>
          </div>
        </footer>
      </div>
    </div>
  );
}
