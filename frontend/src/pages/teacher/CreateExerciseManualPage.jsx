// File Name: CreateExerciseManualPage.jsx
// Description: Direct exercise creation page. Same split layout as the exercise edit screen: question list on the left, math editor with live preview on the right.
// Created At: 2026-08-30
// Created By: Tam Khang
// Updated At: 2026-11-15
// Updated By: AI Agent

import React, { useState, useEffect, useRef } from 'react';
import {
  ChevronRight, ChevronDown, Plus, Trash2, Save, AlertCircle, Loader2,
  ListOrdered, FileCode2, ListChecks, Eye, Check, Image as ImageIcon, Table2, Sigma,
} from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { exercisesApi, subjectsApi, questionsApi } from '../../services/api';
import MathRenderer from '../../components/common/MathRenderer';
import MathTextEditor from '../../components/common/MathTextEditor';
import { symbolCategoriesBySubject } from '../../components/common/mathSymbols';
import {
  QUESTION_TYPES, OPTION_LETTERS, fourSlots, convertAnswerSetup, buildQuestionPayload,
} from '../../components/documents/EditExerciseModal';
import toast from '../../components/common/toast';
import confirmDialog from '../../components/common/confirmDialog';
import { getErrorMessage } from '../../utils/errorMessages';
import '../../components/documents/EditExerciseModal.css';
import './CreateExerciseManualPage.css';

const SUBJECT_TABS = [
  { key: 'math', label: 'Toán học' },
  { key: 'physics', label: 'Vật lí' },
  { key: 'chemistry', label: 'Hóa học' },
  { key: 'greek', label: 'Ký tự Hy Lạp' },
];

const HINTS = {
  MultipleChoice: 'Chọn 1 đáp án chính xác',
  TrueFalse: 'Chọn Đúng/Sai cho từng mệnh đề',
  ShortAnswer: 'Nhập đáp án',
  Other: 'Danh sách các ý của câu hỏi',
};

let seq = 0;
const newQuestion = (type = 'MultipleChoice') => ({
  id: `new-${Date.now()}-${seq++}`,
  level: 'Nhận biết',
  content: '',
  questionType: type,
  options: type === 'ShortAnswer' ? [] : type === 'Other' ? [{ key: '1', text: '', isCorrect: false }] : fourSlots([], type === 'TrueFalse' ? -1 : 0),
  correctOption: type === 'ShortAnswer' ? '' : 'A',
  solutionGuide: '',
  imageUrl: null,
  imageMeta: null,
});

const levelClass = (l) => (l === 'Nhận biết' ? 'badge-level-know' : l === 'Thông hiểu' ? 'badge-level-comp' : 'badge-level-app');
const typeLabel = (t) => QUESTION_TYPES.find((x) => x.value === t)?.label || t;

export default function CreateExerciseManualPage() {
  const navigate = useNavigate();

  const [title, setTitle] = useState('');
  const [exerciseType, setExerciseType] = useState('exam');
  const [grade, setGrade] = useState('12');
  const [subject, setSubject] = useState('');
  const [duration, setDuration] = useState('45');
  const [startTime, setStartTime] = useState('');
  const [dueTime, setDueTime] = useState('');
  const [subjectsList, setSubjectsList] = useState([]);

  const [questions, setQuestions] = useState(() => [newQuestion()]);
  const [selectedId, setSelectedId] = useState(() => null);
  const [isSaving, setIsSaving] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const [subjectTab, setSubjectTab] = useState('math');
  const [tableDims, setTableDims] = useState({ open: false, rows: 3, cols: 3 });
  const [isUploadingImage, setIsUploadingImage] = useState(false);
  const editorRefs = useRef({});
  const activeEditorRef = useRef(null);
  const imageInputRef = useRef(null);
  const setActive = (key) => { activeEditorRef.current = editorRefs.current[key]; };
  const getEditor = () => activeEditorRef.current || editorRefs.current.content;

  const active = questions.find((q) => q.id === selectedId) || questions[0];
  const activeIdx = questions.indexOf(active);
  const type = active.questionType;

  useEffect(() => {
    let alive = true;
    subjectsApi.getSubjects().then((subjs) => {
      if (alive && Array.isArray(subjs) && subjs.length) {
        setSubjectsList(subjs);
        setSubject((cur) => cur || subjs[0].subject_id);
      }
    }).catch(() => {});
    return () => { alive = false; };
  }, []);

  const patch = (changes) => setQuestions((prev) => prev.map((q) => (q.id === active.id ? { ...q, ...changes } : q)));
  const patchOption = (key, changes) => patch({ options: active.options.map((o) => (o.key === key ? { ...o, ...changes } : o)) });

  const addQuestion = () => {
    const q = newQuestion();
    setQuestions((prev) => [...prev, q]);
    setSelectedId(q.id);
  };

  const deleteQuestion = (id) => {
    if (questions.length <= 1) { toast.error('Đề cần có ít nhất 1 câu hỏi.'); return; }
    const rest = questions.filter((q) => q.id !== id);
    setQuestions(rest);
    if (active.id === id) setSelectedId(rest[Math.max(0, activeIdx - 1)].id);
  };

  const changeType = async (next) => {
    if (next === type) return;
    const conv = convertAnswerSetup(type, next, active.options, active.correctOption);
    if (conv.lost && !(await confirmDialog('Đổi loại câu hỏi sẽ bỏ một phần dữ liệu đáp án hiện tại. Tiếp tục?', { title: 'Đổi loại câu hỏi', confirmText: 'Tiếp tục' }))) return;
    patch({ questionType: next, options: conv.options, correctOption: conv.correctOption });
  };

  const handleImagePick = async (e) => {
    const file = e.target.files?.[0];
    e.target.value = '';
    if (!file) return;
    if (!/^image\//.test(file.type || '')) { setErrorMsg('Chỉ chấp nhận tệp hình ảnh.'); return; }
    setIsUploadingImage(true);
    try {
      const fd = new FormData();
      fd.append('file', file);
      const meta = await questionsApi.uploadImage(fd);
      getEditor()?.insertImage((meta.original_name || 'hinh-anh').replace(/[[\]]/g, ''), meta.url);
      patch({ imageUrl: meta.url, imageMeta: { url: meta.url, filename: meta.filename, original_name: meta.original_name, size_bytes: meta.size_bytes, content_type: meta.content_type, width: meta.width, height: meta.height, uploaded_at: new Date().toISOString() } });
    } catch {
      setErrorMsg('Không thể tải ảnh lên. Vui lòng thử lại.');
    } finally {
      setIsUploadingImage(false);
    }
  };

  const handleSave = async () => {
    const fail = (msg) => { setErrorMsg(msg); window.scrollTo({ top: 0, behavior: 'smooth' }); };
    if (!title.trim()) return fail('Vui lòng nhập tên bài tập.');
    const valid = questions.filter((q) => q.content.trim());
    if (!valid.length) return fail('Vui lòng nhập nội dung cho ít nhất 1 câu hỏi.');

    setIsSaving(true);
    setErrorMsg('');
    try {
      const ex = await exercisesApi.createExercise({
        title: title.trim(),
        subject_id: subject || subjectsList[0]?.subject_id,
        exercise_kind: exerciseType === 'exam' ? 'EXAM' : 'PRACTICE',
        total_questions: valid.length,
        ai_metadata: { grade, duration: `${duration || 15} phút`, type: exerciseType, start_time: startTime, due_time: dueTime },
      });
      for (let i = 0; i < valid.length; i++) {
        await exercisesApi.addQuestion(ex.exercise_id, buildQuestionPayload(valid[i], i + 1));
      }
      toast.success(`Đã tạo bài tập "${title}" với ${valid.length} câu hỏi!`);
      navigate('/teacher/exercises');
    } catch (err) {
      fail(getErrorMessage(err, 'Có lỗi xảy ra khi lưu bài tập.'));
    } finally {
      setIsSaving(false);
    }
  };

  const symbols = symbolCategoriesBySubject[subjectTab] || symbolCategoriesBySubject.math;
  const snippet = (q) => q.content.split('\n').find((l) => l.trim()) || 'Nội dung câu hỏi...';

  const optionInput = (opt, placeholder, label) => (
    <MathTextEditor
      singleLine
      ref={(r) => { editorRefs.current[`option:${opt.key}`] = r; }}
      className="option-choice-input"
      value={opt.text}
      onChange={(v) => patchOption(opt.key, { text: v })}
      onFocus={() => setActive(`option:${opt.key}`)}
      placeholder={placeholder}
      ariaLabel={label}
    />
  );

  return (
    <div className="create-manual-main" style={{ maxWidth: 1400 }}>
      <div className="manual-top-header">
        <nav className="breadcrumb-nav">
          <Link to="/teacher" className="breadcrumb-link">Trang chủ</Link>
          <ChevronRight size={14} className="breadcrumb-separator" />
          <Link to="/teacher/exercises" className="breadcrumb-link">Kho bài tập</Link>
          <ChevronRight size={14} className="breadcrumb-separator" />
          <span className="breadcrumb-current">Tạo bài tập mới</span>
        </nav>
        <h1 className="page-main-heading">Tạo bài tập mới (Soạn thảo trực tiếp)</h1>
        <p className="page-sub-desc">Soạn câu hỏi trắc nghiệm, đúng/sai, trả lời ngắn với công thức, hình ảnh và bảng.</p>
      </div>

      {errorMsg && (
        <div role="alert" style={{ marginBottom: 16, padding: '12px 16px', background: '#FEF2F2', border: '1px solid #FCA5A5', borderRadius: 8, color: '#991B1B', display: 'flex', alignItems: 'center', gap: 8 }}>
          <AlertCircle size={18} /><span>{errorMsg}</span>
        </div>
      )}

      {/* Basic info */}
      <div className="form-card-section">
        <h2 className="section-card-title">Thông tin cơ bản</h2>
        <div className="form-row-2-1">
          <div className="form-field-item flex-2">
            <label className="field-label">Tên bài tập *</label>
            <input className="custom-text-input" placeholder="Nhập tên bài tập..." value={title} onChange={(e) => setTitle(e.target.value)} />
          </div>
          <div className="form-field-item flex-1">
            <label className="field-label">Loại bài tập *</label>
            <select className="custom-select-input" value={exerciseType} onChange={(e) => setExerciseType(e.target.value)}>
              <option value="exam">Bài kiểm tra (Tính điểm)</option>
              <option value="practice">Luyện tập tại nhà</option>
            </select>
          </div>
        </div>
        <div className="form-grid-3">
          <div className="form-field-item">
            <label className="field-label">Môn học *</label>
            <select className="custom-select-input" value={subject} onChange={(e) => setSubject(e.target.value)}>
              {subjectsList.map((s) => <option key={s.subject_id} value={s.subject_id}>{s.subject_name || s.name}</option>)}
            </select>
          </div>
          <div className="form-field-item">
            <label className="field-label">Khối *</label>
            <select className="custom-select-input" value={grade} onChange={(e) => setGrade(e.target.value)}>
              {['10', '11', '12'].map((g) => <option key={g} value={g}>Khối {g}</option>)}
            </select>
          </div>
          <div className="form-field-item">
            <label className="field-label">Thời gian làm bài (phút)</label>
            <input className="custom-text-input" inputMode="numeric" value={duration} onChange={(e) => setDuration(e.target.value.replace(/\D/g, '').slice(0, 3))} />
          </div>
        </div>
        <div className="form-grid-2">
          <div className="form-field-item">
            <label className="field-label">Giờ mở bài (Tùy chọn)</label>
            <input type="datetime-local" className="custom-text-input" value={startTime} onChange={(e) => setStartTime(e.target.value)} />
          </div>
          <div className="form-field-item">
            <label className="field-label">Hạn nộp bài (Tùy chọn)</label>
            <input type="datetime-local" className="custom-text-input" value={dueTime} onChange={(e) => setDueTime(e.target.value)} />
          </div>
        </div>
      </div>

      {/* Formula toolbar */}
      <section className="formula-toolbar-container" style={{ marginBottom: 16, borderRadius: 12, border: '1px solid #E8E4F0' }}>
        <div className="formula-toolbar-top-strip">
          <div className="formula-top-left-cluster">
            <div className="formula-sigma-label"><span className="sigma-symbol">Σ</span><span className="sigma-text">Bảng ký hiệu:</span></div>
            <div className="formula-subject-tabs">
              {SUBJECT_TABS.map((t) => (
                <button key={t.key} type="button" className={`subject-tab-btn ${subjectTab === t.key ? 'active' : ''}`} onClick={() => setSubjectTab(t.key)}>
                  <span>{t.label}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
        <div className="formula-categories-row">
          {symbols.groups.map((cat) => (
            <div key={cat.group} className="formula-group-seg">
              <span className="formula-group-title">{cat.group}</span>
              <div className="formula-chips-wrap">
                {cat.items.map((item) => (
                  <button key={item.code} type="button" className="formula-chip-btn" onMouseDown={(e) => e.preventDefault()}
                    onClick={() => getEditor()?.insertMath(item.tpl || item.code)} title={`${item.tip} (${item.code})`}>
                    <MathRenderer text={`$${item.display}$`} />
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
        <div className="toolbar-bottom-actions" style={{ position: 'relative' }}>
          <button type="button" className="btn-toolbar-tool" onMouseDown={(e) => e.preventDefault()} disabled={isUploadingImage} onClick={() => imageInputRef.current?.click()}>
            {isUploadingImage ? <Loader2 size={14} className="animate-spin" /> : <ImageIcon size={14} />}
            <span>{isUploadingImage ? 'Đang tải ảnh...' : 'Chèn hình ảnh'}</span>
          </button>
          <input ref={imageInputRef} type="file" accept="image/*" style={{ display: 'none' }} onChange={handleImagePick} />
          <button type="button" className="btn-toolbar-tool" onMouseDown={(e) => e.preventDefault()} onClick={() => getEditor()?.insertMath('#?x^2+#?x+#?=0', { display: true })}>
            <Sigma size={14} /><span>PT bậc 2</span>
          </button>
          <div style={{ position: 'relative', display: 'inline-block' }}>
            <button type="button" className="btn-toolbar-tool" onMouseDown={(e) => e.preventDefault()} onClick={() => setTableDims((d) => ({ ...d, open: !d.open }))}>
              <Table2 size={14} /><span>Chèn bảng</span>
            </button>
            {tableDims.open && (
              <div style={{ position: 'absolute', top: '110%', left: 0, zIndex: 50, background: '#fff', border: '1px solid #E2E8F0', borderRadius: 8, padding: 10, boxShadow: '0 8px 24px rgba(15,23,42,.15)', display: 'flex', gap: 8, alignItems: 'center', whiteSpace: 'nowrap', fontSize: 13 }}>
                <label>Dòng <input type="number" min={1} max={20} value={tableDims.rows} onChange={(e) => setTableDims((d) => ({ ...d, rows: Number(e.target.value) || 1 }))} style={{ width: 48 }} /></label>
                <label>Cột <input type="number" min={1} max={10} value={tableDims.cols} onChange={(e) => setTableDims((d) => ({ ...d, cols: Number(e.target.value) || 1 }))} style={{ width: 48 }} /></label>
                <button type="button" className="btn-toolbar-tool" onMouseDown={(e) => e.preventDefault()} onClick={() => { getEditor()?.insertTable(tableDims.rows, tableDims.cols); setTableDims((d) => ({ ...d, open: false })); }}>Chèn</button>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* Split body */}
      <div className="edit-modal-split-body" style={{ borderRadius: 12, border: '1px solid #E8E4F0' }}>
        <div className="left-questions-list-col">
          <div className="questions-list-header-bar">
            <div className="list-title-left">
              <ListOrdered size={16} className="list-icon" />
              <h3 className="list-main-title"><span>Danh sách câu hỏi</span><span className="list-title-count">({questions.length} câu)</span></h3>
            </div>
            <button type="button" className="btn-add-question-header" onClick={addQuestion}><Plus size={13} /><span>Thêm câu hỏi</span></button>
          </div>
          <div className="questions-cards-scroll-container">
            {questions.map((q, i) => (
              <div key={q.id} className={`question-item-card ${q.id === active.id ? 'is-selected' : ''}`} onClick={() => setSelectedId(q.id)}>
                <div className="question-card-top-row">
                  <div className="top-pills-cluster">
                    <span className="pill-qnum">Câu {i + 1}</span>
                    <span className={`pill-qlevel ${levelClass(q.level)}`}>{q.level}</span>
                  </div>
                  {q.id === active.id && <span className="pill-active-badge"><span className="active-dot" />Đang chọn</span>}
                </div>
                <p className="question-card-snippet-text"><MathRenderer text={snippet(q)} /></p>
                <div className="question-card-bottom-row">
                  <span className="meta-left-text">{typeLabel(q.questionType)}</span>
                  <span className="meta-right-text">{q.content.trim() ? '' : 'Chưa có nội dung'}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="right-question-editor-col">
          <div className="editor-col-top-bar">
            <div className="editor-col-title-left">
              <span className="editor-q-label">Soạn Câu {activeIdx + 1}</span>
              <div className="editor-level-inline-wrap" title="Chọn cấp độ tư duy">
                <select className="editor-level-select" value={active.level} onChange={(e) => patch({ level: e.target.value })}>
                  <option>Nhận biết</option><option>Thông hiểu</option><option>Vận dụng</option>
                </select>
                <ChevronDown size={13} className="editor-level-chevron" />
              </div>
            </div>
            <button type="button" className="btn-delete-active-q" onClick={() => deleteQuestion(active.id)}
              style={{ display: 'inline-flex', alignItems: 'center', gap: 4, padding: '5px 9px', borderRadius: 6, border: '1px solid #FECACA', background: '#FEF2F2', color: '#DC2626', fontSize: 12, fontWeight: 500, cursor: 'pointer' }}>
              <Trash2 size={13} /><span>Xóa câu hỏi</span>
            </button>
          </div>

          <div className="editor-textarea-section">
            <div className="textarea-section-header">
              <div className="section-header-left"><FileCode2 size={15} /><span>Nội dung câu hỏi</span></div>
              <span className="katex-support-hint">Nhấn Alt+= hoặc $ để chèn công thức</span>
            </div>
            <MathTextEditor
              key={`content-${active.id}`}
              ref={(r) => { editorRefs.current.content = r; }}
              className="question-latex-textarea"
              value={active.content}
              onChange={(v) => patch({ content: v })}
              onFocus={() => setActive('content')}
              placeholder="Nhập nội dung câu hỏi..."
              ariaLabel="Question content"
            />
          </div>

          <section className="solution-and-answers-section">
            <div className="solution-section-header">
              <div className="solution-header-left">
                <ListChecks size={18} className="solution-header-icon" />
                <h3 className="solution-header-title">Thiết lập đáp án</h3>
              </div>
              <span className="solution-header-hint">{HINTS[type]}</span>
            </div>

            <div role="radiogroup" aria-label="Question type" style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 12 }}>
              {QUESTION_TYPES.map((t) => {
                const on = type === t.value;
                return (
                  <button key={t.value} type="button" role="radio" aria-checked={on} onClick={() => changeType(t.value)}
                    style={{ padding: '6px 12px', borderRadius: 6, fontSize: 13, cursor: 'pointer', border: `1px solid ${on ? '#2563EB' : '#CBD5E1'}`, background: on ? '#EFF6FF' : '#fff', color: on ? '#1D4ED8' : '#334155', fontWeight: on ? 600 : 400 }}>
                    {t.label}
                  </button>
                );
              })}
            </div>

            {type === 'MultipleChoice' && (
              <div className="options-grid-row">
                {active.options.map((opt) => {
                  const ok = active.correctOption === opt.key;
                  return (
                    <div key={opt.key} className={`option-choice-card ${ok ? 'is-selected-correct' : ''}`} onClick={() => patch({ correctOption: opt.key })}>
                      <div className="option-choice-left">
                        <span className={`option-radio-dot ${ok ? 'checked' : ''}`}>{ok && <span className="radio-inner-dot" />}</span>
                        <span className="option-choice-letter">{opt.key}.</span>
                        <div onClick={(e) => e.stopPropagation()} style={{ flex: 1, minWidth: 0 }}>{optionInput(opt, `Nhập đáp án ${opt.key}...`, `Answer option ${opt.key}`)}</div>
                      </div>
                      {ok && <div className="option-correct-badge"><Check size={12} strokeWidth={3} /></div>}
                    </div>
                  );
                })}
              </div>
            )}

            {type === 'TrueFalse' && (
              <div className="options-grid-row options-grid-row--single">
                {active.options.map((opt) => (
                  <div key={opt.key} className={`option-choice-card ${opt.isCorrect ? 'is-selected-correct' : ''}`}>
                    <div className="option-choice-left">
                      <span className="option-choice-letter">{opt.key.toLowerCase()})</span>
                      <div style={{ flex: 1, minWidth: 0 }}>{optionInput(opt, `Nhập mệnh đề ${opt.key.toLowerCase()})...`, `Statement ${opt.key}`)}</div>
                      <button type="button" onClick={() => patchOption(opt.key, { isCorrect: !opt.isCorrect })}
                        style={{ marginLeft: 8, padding: '4px 10px', borderRadius: 6, cursor: 'pointer', border: '1px solid #CBD5E1', fontWeight: 600, background: opt.isCorrect ? '#DCFCE7' : '#FEE2E2', color: opt.isCorrect ? '#166534' : '#991B1B' }}>
                        {opt.isCorrect ? 'Đúng' : 'Sai'}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {type === 'ShortAnswer' && (
              <div className="solution-guide-box">
                <label className="solution-guide-label">Đáp án (số hoặc biểu thức ngắn)</label>
                <input type="text" value={active.correctOption || ''} onChange={(e) => patch({ correctOption: e.target.value })} placeholder="Nhập đáp án đúng..." aria-label="Short answer value"
                  style={{ width: '100%', padding: '8px 10px', border: '1px solid #CBD5E1', borderRadius: 6, boxSizing: 'border-box' }} />
              </div>
            )}

            {type === 'Other' && (
              <div className="options-grid-row">
                {active.options.map((opt) => (
                  <div key={opt.key} className="option-choice-card">
                    <div className="option-choice-left">
                      <span className="option-choice-letter">Ý {opt.key}.</span>
                      <div style={{ flex: 1, minWidth: 0 }}>{optionInput(opt, `Nhập ý ${opt.key}...`, `Sub-question ${opt.key}`)}</div>
                      <button type="button" title="Xóa ý này" style={{ marginLeft: 8, border: 'none', background: 'transparent', cursor: 'pointer', color: '#DC2626' }}
                        onClick={() => {
                          const rest = active.options.filter((o) => o.key !== opt.key);
                          patch({ options: (rest.length ? rest : [{ text: '', isCorrect: false }]).map((o, i) => ({ ...o, key: String(i + 1) })) });
                        }}>
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>
                ))}
                <button type="button" style={{ padding: '6px 12px', borderRadius: 6, border: '1px dashed #94A3B8', background: 'transparent', cursor: 'pointer' }}
                  onClick={() => patch({ options: [...active.options, { key: String(active.options.length + 1), text: '', isCorrect: false }] })}>
                  <Plus size={14} /> Thêm ý
                </button>
              </div>
            )}

            <div className="solution-guide-box">
              <label className="solution-guide-label">Hướng dẫn giải (hiển thị cho học sinh sau khi nộp bài)</label>
              <MathTextEditor
                key={`guide-${active.id}`}
                ref={(r) => { editorRefs.current.guide = r; }}
                className="solution-guide-textarea"
                value={active.solutionGuide}
                onChange={(v) => patch({ solutionGuide: v })}
                onFocus={() => setActive('guide')}
                placeholder="Nhập hướng dẫn giải và lời giải chi tiết..."
                ariaLabel="Solution guide"
              />
            </div>
          </section>

          <div className="editor-preview-section">
            <div className="preview-section-header">
              <div className="section-header-left"><Eye size={15} className="green-eye-icon" /><span>Xem trước trực quan</span></div>
            </div>
            <div className="preview-rendered-box">
              <div className="preview-header-lead-row">
                <span className="preview-qnum-lead">Câu {activeIdx + 1} ({active.level}):</span>
              </div>
              <div className="preview-dynamic-body">
                {active.content.trim()
                  ? active.content.split('\n').filter((l) => l.trim()).map((l, i) => <div key={i} className="preview-content-line"><MathRenderer text={l} /></div>)
                  : <p className="preview-empty-text">(Chưa có nội dung câu hỏi)</p>}
              </div>
              {(type === 'MultipleChoice' || type === 'TrueFalse') && (
                <div className="preview-options-container">
                  <div className="preview-options-grid">
                    {active.options.map((opt) => {
                      const ok = type === 'TrueFalse' ? opt.isCorrect : active.correctOption === opt.key;
                      return (
                        <div key={opt.key} className={`preview-option-item ${ok ? 'is-correct-preview' : ''}`}>
                          <span className="preview-option-letter">{type === 'TrueFalse' ? `${opt.key.toLowerCase()})` : `${opt.key}.`}</span>
                          <span className="preview-option-content"><MathRenderer text={opt.text || `(Chưa nhập ${opt.key})`} /></span>
                          {ok && <span className="preview-option-check-badge"><Check size={12} strokeWidth={3} /></span>}
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
              {type === 'ShortAnswer' && <div className="preview-options-container">Đáp án: {active.correctOption || '(Chưa nhập)'}</div>}
              {type === 'Other' && (
                <ol className="preview-options-container">
                  {active.options.map((o) => <li key={o.key}><MathRenderer text={o.text || `(Chưa nhập ý ${o.key})`} /></li>)}
                </ol>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="manual-page-footer-actions">
        <button type="button" className="btn-footer-cancel" onClick={() => navigate('/teacher/exercises')}>Hủy</button>
        <button type="button" className="btn-footer-publish" onClick={handleSave} disabled={isSaving}>
          {isSaving ? <><Loader2 size={16} className="animate-spin" /><span>Đang lưu...</span></> : <><Save size={16} /><span>Lưu & Đăng</span></>}
        </button>
      </div>
    </div>
  );
}
