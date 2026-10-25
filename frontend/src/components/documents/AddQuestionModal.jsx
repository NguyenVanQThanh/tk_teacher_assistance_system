// File Name: AddQuestionModal.jsx
// Description: Interactive Add Question modal with filter metadata row, comprehensive math symbol palette (Image 3), LaTeX editor, answer options, and live KaTeX preview matching Image 2.
// Created At: 2026-09-13
// Created By: Tam Khang
// Updated At: 2026-09-13
// Updated By: Tam Khang

import React, { useState, useEffect, useRef } from 'react';
import {
  X,
  Plus,
  Trash2,
  Check,
  Eye,
  EyeOff,
  Bookmark,
  History,
  Sparkles,
  Shuffle,
  FileText,
  Compass,
  Star,
  Clock,
  Tag,
  ChevronDown,
  Image as ImageIcon,
  Code,
  FileSpreadsheet,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  RotateCcw,
  Layers,
  Send,
  Save,
  Grid
} from 'lucide-react';
import MathRenderer from '../common/MathRenderer';
import './AddQuestionModal.css';

export default function AddQuestionModal({
  isOpen,
  onClose,
  onSave,
  onSaveAndContinue,
  documentTitle = 'Đề cương ôn tập Toán 12 - Học kì 1 (Nâng cao)',
  gradeSubject = 'Toán 12 • Kì 1',
  topicName = 'Chương I: Ứng dụng đạo hàm',
  questionNumber = 1,
  initialData = null
}) {
  const textareaRef = useRef(null);

  // Question Type: 'multiple_choice', 'true_false', 'short_answer'
  const [questionType, setQuestionType] = useState('multiple_choice');

  // Filter / Metadata Row states (matching Image 2 & 3-level rule)
  const [difficulty, setDifficulty] = useState('Vận dụng');
  const [score, setScore] = useState('3.0');
  const [duration, setDuration] = useState('10');
  const [topic, setTopic] = useState('Khảo sát hàm số & Cực trị');

  // Symbol Palette Tab: 'math', 'physics', 'chem', 'greek'
  const [activeSymbolTab, setActiveSymbolTab] = useState('math');

  // Question Content State (matching default content from Image 2)
  const [content, setContent] = useState(
    `Cho hàm số bậc ba $y = f(x) = ax^3 + bx^2 + cx + d$ $(a \\neq 0)$ có đồ thị như hình vẽ bên. Biết rằng đồ thị hàm số đạt cực đại tại điểm $x = -1$ và đạt cực tiểu tại điểm $x = 1$.\n\nPhương trình $f(x) - 2 = 0$ có bao nhiêu nghiệm thực phân biệt?`
  );

  // Options State (matching Image 2: A, B, C*, D with C having solution note)
  const [options, setOptions] = useState([
    { key: 'A', text: 'Có 1 nghiệm duy nhất.', isCorrect: false },
    { key: 'B', text: 'Có 2 nghiệm thực phân biệt.', isCorrect: false },
    { key: 'C', text: 'Có 3 nghiệm thực phân biệt.', isCorrect: true },
    { key: 'D', text: 'Vô nghiệm.', isCorrect: false }
  ]);

  // True/False state for 'true_false' mode
  const [tfItems, setTfItems] = useState([
    { key: 'a', statement: 'Hàm số đã cho đồng biến trên khoảng (-1; 1).', isTrue: false },
    { key: 'b', statement: 'Điểm cực tiểu của đồ thị hàm số là (1; f(1)).', isTrue: true },
    { key: 'c', statement: 'Phương trình f\'(x) = 0 có hai nghiệm phân biệt.', isTrue: true },
    { key: 'd', statement: 'Giá trị lớn nhất của hàm số trên [-2; 2] bằng 2.', isTrue: false }
  ]);

  // Short answer expected value for 'short_answer' mode
  const [shortAnswerExpected, setShortAnswerExpected] = useState('3');

  // Solution Guide / Explanation Note (as seen under option C in Image 2)
  const [solutionGuide, setSolutionGuide] = useState(
    'Đường thẳng y = 2 cắt đồ thị f(x) tại 3 điểm phân biệt do y_CD > 2 > y_CT.'
  );

  // UI States
  const [showLivePreview, setShowLivePreview] = useState(false);
  const [lastSavedTime, setLastSavedTime] = useState('14:32:05');
  const [isSavedFeedback, setIsSavedFeedback] = useState(false);
  const [showDraftHistory, setShowDraftHistory] = useState(false);
  const [draftsList, setDraftsList] = useState([
    { id: 1, time: '14:30:12', preview: 'Bản nháp tự động - 4 lựa chọn' },
    { id: 2, time: '14:22:45', preview: 'Bản nháp câu hỏi cực trị tham số m' }
  ]);
  const [showAiNotice, setShowAiNotice] = useState(false);

  // Helper to get simple 3-level name
  const getSimpleLevel = (levelStr) => {
    if (!levelStr) return 'Vận dụng';
    if (levelStr.startsWith('Vận dụng')) return 'Vận dụng';
    if (levelStr.startsWith('Thông hiểu')) return 'Thông hiểu';
    if (levelStr.startsWith('Nhận biết')) return 'Nhận biết';
    return levelStr.split('(')[0].trim();
  };

  // Helper to extract raw numeric score string
  const getRawScore = (scoreStr) => {
    if (!scoreStr) return '';
    return String(scoreStr).replace('điểm', '').replace('đ', '').trim();
  };

  // Score input handler: max 4 chars, only numbers and '.', single dot
  const handleScoreInputChange = (e) => {
    let val = e.target.value;
    val = val.replace(/[^0-9.]/g, '');
    const parts = val.split('.');
    if (parts.length > 2) {
      val = parts[0] + '.' + parts.slice(1).join('');
    }
    if (val.length > 4) {
      val = val.slice(0, 4);
    }
    setScore(val);
  };

  // Initialize with initialData if provided
  useEffect(() => {
    if (initialData) {
      if (initialData.content) setContent(initialData.content);
      if (initialData.levelRange) setDifficulty(initialData.levelRange);
      else if (initialData.level) setDifficulty(initialData.level);
      if (initialData.score) setScore(initialData.score.replace(' điểm', ''));
      if (initialData.suggestedTime) setDuration(initialData.suggestedTime.replace(' phút', ''));
      if (initialData.options && Array.isArray(initialData.options)) {
        setOptions(
          initialData.options.map((opt) => ({
            key: opt.key,
            text: opt.text || '',
            isCorrect: initialData.correctOption === opt.key
          }))
        );
      }
      if (initialData.solutionGuide) {
        setSolutionGuide(initialData.solutionGuide);
      }
    }
  }, [initialData]);

  // Auto-save timer simulation
  useEffect(() => {
    const timer = setInterval(() => {
      const now = new Date();
      const timeStr = now.toTimeString().split(' ')[0];
      setLastSavedTime(timeStr);
    }, 45000);
    return () => clearInterval(timer);
  }, []);

  if (!isOpen) return null;

  // Insert LaTeX at cursor helper
  const insertLatexSnippet = (snippet) => {
    const textarea = textareaRef.current;
    if (!textarea) {
      setContent((prev) => prev + snippet);
      return;
    }

    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const textBefore = content.substring(0, start);
    const textAfter = content.substring(end);

    const updatedText = textBefore + snippet + textAfter;
    setContent(updatedText);

    setTimeout(() => {
      textarea.focus();
      textarea.setSelectionRange(start + snippet.length, start + snippet.length);
    }, 50);
  };

  // Word count & LaTeX block count calculation
  const wordCount = content.trim() ? content.trim().split(/\s+/).length : 0;
  const latexMatches = content.match(/\$[^$]+\$|\$\$[\s\S]*?\$\$/g);
  const latexBlocksCount = latexMatches ? latexMatches.length : 0;

  // Option handlers
  const handleSelectCorrectOption = (key) => {
    setOptions((prev) =>
      prev.map((opt) => ({
        ...opt,
        isCorrect: opt.key === key
      }))
    );
  };

  const handleOptionTextChange = (key, val) => {
    setOptions((prev) =>
      prev.map((opt) => (opt.key === key ? { ...opt, text: val } : opt))
    );
  };

  const handleDeleteOption = (key) => {
    if (options.length <= 2) return;
    const filtered = options.filter((opt) => opt.key !== key);
    // Re-index keys A, B, C, ...
    const reindexed = filtered.map((opt, idx) => ({
      ...opt,
      key: String.fromCharCode(65 + idx)
    }));
    setOptions(reindexed);
  };

  const handleAddOption = () => {
    if (options.length >= 6) return;
    const nextKey = String.fromCharCode(65 + options.length);
    setOptions([
      ...options,
      { key: nextKey, text: `Phương án ${nextKey}`, isCorrect: false }
    ]);
  };

  const handleShuffleOptions = () => {
    const texts = options.map((o) => o.text);
    // Fisher-Yates shuffle texts
    for (let i = texts.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [texts[i], texts[j]] = [texts[j], texts[i]];
    }
    setOptions((prev) =>
      prev.map((opt, idx) => ({
        ...opt,
        text: texts[idx]
      }))
    );
  };

  const handleAiFormat = () => {
    setShowAiNotice(true);
    setTimeout(() => setShowAiNotice(false), 2000);
  };

  // Build final question object
  const buildQuestionData = () => {
    const correctOpt = options.find((o) => o.isCorrect)?.key || 'A';
    return {
      id: initialData?.id || Date.now(),
      number: questionNumber,
      questionType,
      level: getSimpleLevel(difficulty),
      levelRange: getSimpleLevel(difficulty),
      score: `${getRawScore(score) || '3.0'} điểm`,
      suggestedTime: `${duration} phút`,
      topic,
      content,
      correctOption: correctOpt,
      options,
      tfItems,
      shortAnswerExpected,
      solutionGuide,
      previewSnippet: content.slice(0, 120) + (content.length > 120 ? '...' : ''),
      formulaMeta: `${latexBlocksCount} công thức LaTeX`,
      answersMeta: `${options.length} đáp án (${correctOpt}*)`
    };
  };

  const handleSaveToExam = () => {
    const data = buildQuestionData();
    setIsSavedFeedback(true);
    setTimeout(() => {
      setIsSavedFeedback(false);
      if (onSave) onSave(data);
      onClose();
    }, 400);
  };

  const handleSaveAndContinueNext = () => {
    const data = buildQuestionData();
    if (onSaveAndContinue) {
      onSaveAndContinue(data);
    }
    // Reset fields for the next question
    setContent('Nhập nội dung đề bài cho câu hỏi tiếp theo...');
    setOptions([
      { key: 'A', text: '', isCorrect: true },
      { key: 'B', text: '', isCorrect: false },
      { key: 'C', text: '', isCorrect: false },
      { key: 'D', text: '', isCorrect: false }
    ]);
    setSolutionGuide('');
    setIsSavedFeedback(true);
    setTimeout(() => setIsSavedFeedback(false), 1200);
  };

  return (
    <div className="add-q-modal-overlay" onClick={onClose}>
      <div className="add-q-modal-container" onClick={(e) => e.stopPropagation()}>
        {/* ============================================================ */}
        {/* 1. TOP HEADER (Matching Image 2) */}
        {/* ============================================================ */}
        <header className="add-q-header">
          <div className="add-q-header-left">
            <div className="add-q-icon-box">
              <FileSpreadsheet size={22} className="add-q-main-icon" />
            </div>
            <div className="add-q-title-meta">
              <div className="add-q-title-row">
                <h2 className="add-q-title">Thêm câu hỏi mới</h2>
                <span className="add-q-badge-grade">{gradeSubject}</span>
              </div>
              <div className="add-q-subtitle-row">
                <FileText size={13} className="subtitle-icon" />
                <span className="subtitle-doc-name">Tài liệu: {documentTitle}</span>
                <span className="subtitle-separator">•</span>
                <span className="subtitle-topic">{topicName}</span>
              </div>
            </div>
          </div>

          <div className="add-q-header-actions">
            <button
              type="button"
              className="btn-draft-history"
              onClick={() => setShowDraftHistory(!showDraftHistory)}
              title="Xem lịch sử các bản nháp đã lưu"
            >
              <History size={15} />
              <span>Lịch sử nháp</span>
            </button>

            {showDraftHistory && (
              <div className="draft-history-popover">
                <div className="draft-history-title">Các bản nháp gần đây</div>
                {draftsList.map((d) => (
                  <div key={d.id} className="draft-item">
                    <span className="draft-time">{d.time}</span>
                    <span className="draft-preview">{d.preview}</span>
                  </div>
                ))}
              </div>
            )}

            <button
              type="button"
              className="btn-save-to-exam"
              onClick={handleSaveToExam}
            >
              <Bookmark size={15} />
              <span>{isSavedFeedback ? 'Đã lưu!' : 'Lưu câu hỏi vào đề'}</span>
            </button>

            <button
              type="button"
              className="btn-close-modal"
              onClick={onClose}
              title="Đóng cửa sổ"
            >
              <X size={18} />
            </button>
          </div>
        </header>

        {/* ============================================================ */}
        {/* 2. QUESTION TYPE SELECTOR & METADATA FILTERS TOOLBAR */}
        {/* ============================================================ */}
        <div className="add-q-type-tabs-bar">
          <div className="qtype-tabs-left">
            <button
              type="button"
              className={`qtype-tab-btn ${questionType === 'multiple_choice' ? 'is-active' : ''}`}
              onClick={() => setQuestionType('multiple_choice')}
            >
              <span className="qtype-radio-dot">
                {questionType === 'multiple_choice' && <span className="dot-inner" />}
              </span>
              <span>Trắc nghiệm 4 lựa chọn</span>
            </button>

            <button
              type="button"
              className={`qtype-tab-btn ${questionType === 'true_false' ? 'is-active' : ''}`}
              onClick={() => setQuestionType('true_false')}
            >
              <span className="qtype-icon-prefix">⇌</span>
              <span>Đúng / Sai</span>
            </button>

            <button
              type="button"
              className={`qtype-tab-btn ${questionType === 'short_answer' ? 'is-active' : ''}`}
              onClick={() => setQuestionType('short_answer')}
            >
              <span className="qtype-icon-prefix">✎</span>
              <span>Tự luận / Trả lời ngắn</span>
            </button>
          </div>

          <div className="qtype-filters-right">
            {/* Cognitive Level Dropdown (Image 2 style) */}
            <div className="add-q-level-pill-wrap" title="Chọn cấp độ tư duy">
              <select
                className="add-q-level-select"
                value={getSimpleLevel(difficulty)}
                onChange={(e) => setDifficulty(e.target.value)}
              >
                <option value="Nhận biết">Nhận biết</option>
                <option value="Thông hiểu">Thông hiểu</option>
                <option value="Vận dụng">Vận dụng</option>
              </select>
              <ChevronDown size={13} className="add-q-level-chevron" />
            </div>

            {/* Red Score Badge Editable Input (Image 2 style) */}
            <div className="add-q-score-pill-container" title="Bấm để chỉnh sửa điểm số">
              <input
                type="text"
                className="add-q-score-input"
                value={getRawScore(score)}
                onChange={handleScoreInputChange}
                placeholder="3.0"
              />
              <span className="add-q-score-unit">điểm</span>
            </div>
          </div>
        </div>

        {/* ============================================================ */}
        {/* 4. BẢNG KÝ HIỆU (User: "phần bảng kí hiệu hiển thị giống hình 3") */}
        {/* ============================================================ */}
        <div className="symbol-palette-card">
          {/* Header of Symbol Palette */}
          <div className="symbol-palette-header">
            <div className="symbol-palette-title-cluster">
              <span className="symbol-sigma">∑</span>
              <span className="symbol-title-text">Bảng ký hiệu:</span>
            </div>

            {/* Subject Tabs (Toán học, Vật lí, Hóa học, Ký tự Hy Lạp) */}
            <div className="symbol-subject-tabs">
              <button
                type="button"
                className={`subject-tab-btn ${activeSymbolTab === 'math' ? 'is-active' : ''}`}
                onClick={() => setActiveSymbolTab('math')}
              >
                <span className="tab-icon">📐</span>
                <span>Toán học</span>
              </button>

              <button
                type="button"
                className={`subject-tab-btn ${activeSymbolTab === 'physics' ? 'is-active' : ''}`}
                onClick={() => setActiveSymbolTab('physics')}
              >
                <span className="tab-icon">⚡</span>
                <span>Vật lí</span>
              </button>

              <button
                type="button"
                className={`subject-tab-btn ${activeSymbolTab === 'chem' ? 'is-active' : ''}`}
                onClick={() => setActiveSymbolTab('chem')}
              >
                <span className="tab-icon">🧪</span>
                <span>Hóa học</span>
              </button>

              <button
                type="button"
                className={`subject-tab-btn ${activeSymbolTab === 'greek' ? 'is-active' : ''}`}
                onClick={() => setActiveSymbolTab('greek')}
              >
                <span className="tab-icon">Ω</span>
                <span>Ký tự Hy Lạp</span>
              </button>
            </div>
          </div>

          {/* Symbol Grid by Tab */}
          <div className="symbol-palette-body">
            {activeSymbolTab === 'math' && (
              <>
                {/* Row 1: Đại số & Giải tích (Matching Image 3) */}
                <div className="symbol-categories-row">
                  {/* Đại số */}
                  <div className="symbol-subgroup">
                    <span className="symbol-subgroup-label">Đại số:</span>
                    <div className="symbol-buttons-wrap">
                      <button type="button" className="sym-key-btn" title="Phân số" onClick={() => insertLatexSnippet('\\frac{a}{b}')}>
                        <MathRenderer text="$\frac{a}{b}$" />
                      </button>
                      <button type="button" className="sym-key-btn" title="Lũy thừa" onClick={() => insertLatexSnippet('x^{n}')}>
                        <MathRenderer text="$x^n$" />
                      </button>
                      <button type="button" className="sym-key-btn" title="Chỉ số dưới" onClick={() => insertLatexSnippet('x_{k}')}>
                        <MathRenderer text="$x_k$" />
                      </button>
                      <button type="button" className="sym-key-btn" title="Căn bậc hai" onClick={() => insertLatexSnippet('\\sqrt{x}')}>
                        <MathRenderer text="$\sqrt{x}$" />
                      </button>
                      <button type="button" className="sym-key-btn" title="Căn bậc n" onClick={() => insertLatexSnippet('\\sqrt[n]{x}')}>
                        <MathRenderer text="$\sqrt[n]{x}$" />
                      </button>
                      <button type="button" className="sym-key-btn" title="Giá trị tuyệt đối" onClick={() => insertLatexSnippet('|x|')}>
                        <MathRenderer text="$|x|$" />
                      </button>
                      <button type="button" className="sym-key-btn" title="Cộng trừ" onClick={() => insertLatexSnippet('\\pm ')}>
                        <MathRenderer text="$\pm$" />
                      </button>
                      <button type="button" className="sym-key-btn" title="Phép nhân" onClick={() => insertLatexSnippet('\\times ')}>
                        <MathRenderer text="$\times$" />
                      </button>
                      <button type="button" className="sym-key-btn" title="Phép chia" onClick={() => insertLatexSnippet('\\div ')}>
                        <MathRenderer text="$\div$" />
                      </button>
                      <button type="button" className="sym-key-btn" title="Logarit cơ số a" onClick={() => insertLatexSnippet('\\log_{a} b')}>
                        <MathRenderer text="$\log_a b$" />
                      </button>
                      <button type="button" className="sym-key-btn" title="Logarit tự nhiên" onClick={() => insertLatexSnippet('\\ln x')}>
                        <MathRenderer text="$\ln x$" />
                      </button>
                    </div>
                  </div>

                  {/* Giải tích */}
                  <div className="symbol-subgroup">
                    <span className="symbol-subgroup-label">Giải tích:</span>
                    <div className="symbol-buttons-wrap">
                      <button type="button" className="sym-key-btn" title="Tích phân có cận" onClick={() => insertLatexSnippet('\\int_{a}^{b} f(x)\\,dx')}>
                        <MathRenderer text="$\int_{a}^{b}$" />
                      </button>
                      <button type="button" className="sym-key-btn" title="Nguyên hàm / Tích phân vô định" onClick={() => insertLatexSnippet('\\int f(x)\\,dx')}>
                        <MathRenderer text="$\int$" />
                      </button>
                      <button type="button" className="sym-key-btn" title="Đạo hàm" onClick={() => insertLatexSnippet('\\frac{dy}{dx}')}>
                        <MathRenderer text="$\frac{dy}{dx}$" />
                      </button>
                      <button type="button" className="sym-key-btn" title="Đạo hàm f'(x)" onClick={() => insertLatexSnippet("f'(x)")}>
                        <MathRenderer text="$f'(x)$" />
                      </button>
                      <button type="button" className="sym-key-btn" title="Tổng Sigma" onClick={() => insertLatexSnippet('\\sum_{i=1}^{n}')}>
                        <MathRenderer text="$\sum_{i=1}^n$" />
                      </button>
                      <button type="button" className="sym-key-btn" title="Giới hạn" onClick={() => insertLatexSnippet('\\lim_{x \\to x_0}')}>
                        <MathRenderer text="$\lim_{x\to x_0}$" />
                      </button>
                      <button type="button" className="sym-key-btn" title="Vô cực" onClick={() => insertLatexSnippet('\\infty')}>
                        <MathRenderer text="$\infty$" />
                      </button>
                    </div>
                  </div>
                </div>

                {/* Row 2: Hình học & Tập hợp (Matching Image 3) */}
                <div className="symbol-categories-row">
                  {/* Hình học */}
                  <div className="symbol-subgroup">
                    <span className="symbol-subgroup-label">Hình học:</span>
                    <div className="symbol-buttons-wrap">
                      <button type="button" className="sym-key-btn" title="Vector u" onClick={() => insertLatexSnippet('\\vec{u}')}>
                        <MathRenderer text="$\vec{u}$" />
                      </button>
                      <button type="button" className="sym-key-btn" title="Vector AB" onClick={() => insertLatexSnippet('\\vec{AB}')}>
                        <MathRenderer text="$\vec{AB}$" />
                      </button>
                      <button type="button" className="sym-key-btn" title="Góc ABC" onClick={() => insertLatexSnippet('\\widehat{ABC}')}>
                        <MathRenderer text="$\widehat{ABC}$" />
                      </button>
                      <button type="button" className="sym-key-btn" title="Vuông góc" onClick={() => insertLatexSnippet('\\perp')}>
                        <MathRenderer text="$\perp$" />
                      </button>
                      <button type="button" className="sym-key-btn" title="Song song" onClick={() => insertLatexSnippet('\\parallel')}>
                        <MathRenderer text="$\parallel$" />
                      </button>
                      <button type="button" className="sym-key-btn" title="Tam giác Delta" onClick={() => insertLatexSnippet('\\Delta')}>
                        <MathRenderer text="$\Delta$" />
                      </button>
                      <button type="button" className="sym-key-btn" title="Ký hiệu góc" onClick={() => insertLatexSnippet('\\angle')}>
                        <MathRenderer text="$\angle$" />
                      </button>
                      <button type="button" className="sym-key-btn" title="Độ" onClick={() => insertLatexSnippet('^{\\circ}')}>
                        <MathRenderer text="$^{\circ}$" />
                      </button>
                    </div>
                  </div>

                  {/* Tập hợp & Quan hệ */}
                  <div className="symbol-subgroup">
                    <span className="symbol-subgroup-label">Tập hợp & Quan hệ:</span>
                    <div className="symbol-buttons-wrap">
                      <button type="button" className="sym-key-btn" title="Thuộc" onClick={() => insertLatexSnippet('\\in ')}>
                        <MathRenderer text="$\in$" />
                      </button>
                      <button type="button" className="sym-key-btn" title="Không thuộc" onClick={() => insertLatexSnippet('\\notin ')}>
                        <MathRenderer text="$\notin$" />
                      </button>
                      <button type="button" className="sym-key-btn" title="Tập con" onClick={() => insertLatexSnippet('\\subset ')}>
                        <MathRenderer text="$\subset$" />
                      </button>
                      <button type="button" className="sym-key-btn" title="Hợp" onClick={() => insertLatexSnippet('\\cup ')}>
                        <MathRenderer text="$\cup$" />
                      </button>
                      <button type="button" className="sym-key-btn" title="Giao" onClick={() => insertLatexSnippet('\\cap ')}>
                        <MathRenderer text="$\cap$" />
                      </button>
                      <button type="button" className="sym-key-btn" title="Hiệu tập hợp" onClick={() => insertLatexSnippet('\\setminus ')}>
                        <MathRenderer text="$\setminus$" />
                      </button>
                      <button type="button" className="sym-key-btn" title="Tập rỗng" onClick={() => insertLatexSnippet('\\emptyset')}>
                        <MathRenderer text="$\emptyset$" />
                      </button>
                      <button type="button" className="sym-key-btn" title="Nhỏ hơn hoặc bằng" onClick={() => insertLatexSnippet('\\le ')}>
                        <MathRenderer text="$\le$" />
                      </button>
                      <button type="button" className="sym-key-btn" title="Lớn hơn hoặc bằng" onClick={() => insertLatexSnippet('\\ge ')}>
                        <MathRenderer text="$\ge$" />
                      </button>
                      <button type="button" className="sym-key-btn" title="Khác" onClick={() => insertLatexSnippet('\\neq ')}>
                        <MathRenderer text="$\neq$" />
                      </button>
                      <button type="button" className="sym-key-btn" title="Xấp xỉ" onClick={() => insertLatexSnippet('\\approx ')}>
                        <MathRenderer text="$\approx$" />
                      </button>
                      <button type="button" className="sym-key-btn" title="Suy ra" onClick={() => insertLatexSnippet('\\Rightarrow ')}>
                        <MathRenderer text="$\Rightarrow$" />
                      </button>
                      <button type="button" className="sym-key-btn" title="Tương đương" onClick={() => insertLatexSnippet('\\Leftrightarrow ')}>
                        <MathRenderer text="$\Leftrightarrow$" />
                      </button>
                    </div>
                  </div>
                </div>
              </>
            )}

            {/* Tab: Vật lí */}
            {activeSymbolTab === 'physics' && (
              <div className="symbol-categories-row">
                <div className="symbol-subgroup">
                  <span className="symbol-subgroup-label">Công thức Vật lí:</span>
                  <div className="symbol-buttons-wrap">
                    <button type="button" className="sym-key-btn" onClick={() => insertLatexSnippet('\\vec{F} = m\\vec{a}')}>
                      <MathRenderer text="$\vec{F} = m\vec{a}$" />
                    </button>
                    <button type="button" className="sym-key-btn" onClick={() => insertLatexSnippet('v = v_0 + at')}>
                      <MathRenderer text="$v = v_0 + at$" />
                    </button>
                    <button type="button" className="sym-key-btn" onClick={() => insertLatexSnippet('E = mc^2')}>
                      <MathRenderer text="$E = mc^2$" />
                    </button>
                    <button type="button" className="sym-key-btn" onClick={() => insertLatexSnippet('I = \\frac{U}{R}')}>
                      <MathRenderer text="$I = \frac{U}{R}$" />
                    </button>
                    <button type="button" className="sym-key-btn" onClick={() => insertLatexSnippet('\\lambda = \\frac{v}{f}')}>
                      <MathRenderer text="$\lambda = \frac{v}{f}$" />
                    </button>
                    <button type="button" className="sym-key-btn" onClick={() => insertLatexSnippet('\\omega = 2\\pi f')}>
                      <MathRenderer text="$\omega = 2\pi f$" />
                    </button>
                    <button type="button" className="sym-key-btn" onClick={() => insertLatexSnippet('\\Omega')}>
                      <MathRenderer text="$\Omega$" />
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Tab: Hóa học */}
            {activeSymbolTab === 'chem' && (
              <div className="symbol-categories-row">
                <div className="symbol-subgroup">
                  <span className="symbol-subgroup-label">Ký hiệu Hóa học:</span>
                  <div className="symbol-buttons-wrap">
                    <button type="button" className="sym-key-btn" onClick={() => insertLatexSnippet('\\rightarrow ')}>
                      <MathRenderer text="$\rightarrow$" />
                    </button>
                    <button type="button" className="sym-key-btn" onClick={() => insertLatexSnippet('\\rightleftharpoons ')}>
                      <MathRenderer text="$\rightleftharpoons$" />
                    </button>
                    <button type="button" className="sym-key-btn" onClick={() => insertLatexSnippet('\\uparrow ')}>
                      <MathRenderer text="$\uparrow$" />
                    </button>
                    <button type="button" className="sym-key-btn" onClick={() => insertLatexSnippet('\\downarrow ')}>
                      <MathRenderer text="$\downarrow$" />
                    </button>
                    <button type="button" className="sym-key-btn" onClick={() => insertLatexSnippet('\\text{pH}')}>
                      <MathRenderer text="$\text{pH}$" />
                    </button>
                    <button type="button" className="sym-key-btn" onClick={() => insertLatexSnippet('\\Delta H')}>
                      <MathRenderer text="$\Delta H$" />
                    </button>
                    <button type="button" className="sym-key-btn" onClick={() => insertLatexSnippet('\\text{H}_2\\text{O}')}>
                      <MathRenderer text="$\text{H}_2\text{O}$" />
                    </button>
                    <button type="button" className="sym-key-btn" onClick={() => insertLatexSnippet('\\text{CO}_2')}>
                      <MathRenderer text="$\text{CO}_2$" />
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Tab: Ký tự Hy Lạp */}
            {activeSymbolTab === 'greek' && (
              <div className="symbol-categories-row">
                <div className="symbol-subgroup">
                  <span className="symbol-subgroup-label">Ký tự Hy Lạp:</span>
                  <div className="symbol-buttons-wrap">
                    {['\\alpha', '\\beta', '\\gamma', '\\delta', '\\epsilon', '\\theta', '\\lambda', '\\mu', '\\pi', '\\rho', '\\sigma', '\\tau', '\\phi', '\\omega', '\\Delta', '\\Omega'].map((sym) => (
                      <button key={sym} type="button" className="sym-key-btn" onClick={() => insertLatexSnippet(sym + ' ')}>
                        <MathRenderer text={`$${sym}$`} />
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Row 3: Quick Action Buttons (Always at bottom of palette) */}
            <div className="symbol-actions-row">
              <button
                type="button"
                className="btn-structure-insert"
                onClick={() => insertLatexSnippet('\n\n[Hình vẽ minh họa đồ thị hàm số]\n')}
              >
                <ImageIcon size={14} className="btn-struct-icon" />
                <span>Chèn hình vẽ</span>
              </button>

              <button
                type="button"
                className="btn-structure-insert"
                onClick={() => insertLatexSnippet('\n$$\n\\begin{aligned}\n  \n\\end{aligned}\n$$\n')}
              >
                <Code size={14} className="btn-struct-icon" />
                <span>Chèn khối LaTeX</span>
              </button>

              <button
                type="button"
                className="btn-structure-insert"
                onClick={() => insertLatexSnippet('\n$$\n\\begin{cases}\n  a_1 x + b_1 y = c_1 \\\\\n  a_2 x + b_2 y = c_2\n\\end{cases}\n$$\n')}
              >
                <span>Chèn hệ phương trình</span>
              </button>

              <button
                type="button"
                className="btn-structure-insert"
                onClick={() => insertLatexSnippet('\n$$\n\\begin{pmatrix}\n  a & b \\\\\n  c & d\n\\end{pmatrix}\n$$\n')}
              >
                <span>Chèn ma trận</span>
              </button>
            </div>
          </div>
        </div>

        {/* ============================================================ */}
        {/* 5. NỘI DUNG ĐỀ BÀI & LỰA CHỌN (Matching Image 2) */}
        {/* ============================================================ */}
        <section className="add-q-content-section">
          <div className="section-title-bar">
            <div className="section-title-left">
              <span className="section-title-indicator" />
              <h3 className="section-main-title">Nội dung đề bài & Lựa chọn</h3>
            </div>
            <span className="badge-katex-support">
              <span className="katex-icon-square">KaTeX</span>
              <span>Hỗ trợ Markdown & LaTeX chuẩn KaTeX</span>
            </span>
          </div>

          {/* Question Textarea Box */}
          <div className="question-input-card">
            <div className="textarea-top-hint-row">
              <span className="textarea-lead-label">Đề bài câu hỏi (Kèm công thức LaTeX):</span>
              <span className="textarea-syntax-guide">Đặt công thức trong cặp dấu $...$</span>
            </div>

            <textarea
              ref={textareaRef}
              className="question-main-textarea"
              rows={5}
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Nhập nội dung câu hỏi tại đây... (Ví dụ: Cho hàm số $y = f(x)$...)"
              spellCheck={false}
            />

            {/* Textarea Bottom Metadata Bar */}
            <div className="textarea-bottom-bar">
              <div className="meta-counts-cluster">
                <span>{wordCount} từ</span>
                <span className="meta-bullet">•</span>
                <span>{latexBlocksCount} khối công thức LaTeX</span>
              </div>

              <div className="ai-tools-cluster">
                {showAiNotice && (
                  <span className="ai-notice-toast">Đã tối ưu hóa cú pháp LaTeX!</span>
                )}
                <button
                  type="button"
                  className="btn-ai-format"
                  onClick={handleAiFormat}
                >
                  <Sparkles size={14} className="sparkle-icon" />
                  <span>Định dạng bằng AI</span>
                </button>
              </div>
            </div>

            {/* Live KaTeX Render Preview Accordion */}
            <div className="inline-live-preview-box">
              <div className="inline-preview-header" onClick={() => setShowLivePreview(!showLivePreview)}>
                <div className="preview-header-title">
                  <Eye size={14} className="text-emerald" />
                  <span>Xem trước hiển thị trực quan</span>
                </div>
                <button type="button" className="btn-toggle-inline-preview">
                  {showLivePreview ? 'Thu gọn' : 'Mở rộng'}
                </button>
              </div>

              {showLivePreview && (
                <div className="inline-preview-content">
                  <MathRenderer text={content || '(Chưa nhập nội dung)'} />
                </div>
              )}
            </div>
          </div>

          {/* ============================================================ */}
          {/* 6. OPTIONS SECTION (Matching Image 2) */}
          {/* ============================================================ */}
          {questionType === 'multiple_choice' && (
            <div className="options-editor-card">
              <div className="options-card-header">
                <div className="options-header-left">
                  <h4 className="options-title">Các phương án trả lời</h4>
                  <span className="badge-choose-one">Chọn 1 đáp án đúng</span>
                </div>

                <button
                  type="button"
                  className="btn-shuffle-options"
                  onClick={handleShuffleOptions}
                  title="Đảo ngẫu nhiên vị trí các phương án"
                >
                  <Shuffle size={14} />
                  <span>Đảo ngẫu nhiên</span>
                </button>
              </div>

              {/* Options List */}
              <div className="options-items-list">
                {options.map((opt) => {
                  const isCorrect = opt.isCorrect;
                  return (
                    <div
                      key={opt.key}
                      className={`option-row-card ${isCorrect ? 'is-correct-selected' : ''}`}
                    >
                      <div className="option-main-line">
                        {/* Letter badge (A, B, C, D) */}
                        <span className="option-letter-badge">{opt.key}</span>

                        {/* Radio selection circle */}
                        <button
                          type="button"
                          className={`option-radio-btn ${isCorrect ? 'is-active' : ''}`}
                          onClick={() => handleSelectCorrectOption(opt.key)}
                          title={`Chọn ${opt.key} làm đáp án đúng`}
                        >
                          {isCorrect && <span className="radio-check-dot" />}
                        </button>

                        {/* Input text */}
                        <input
                          type="text"
                          className="option-text-input"
                          value={opt.text}
                          onChange={(e) => handleOptionTextChange(opt.key, e.target.value)}
                          placeholder={`Nhập phương án ${opt.key}...`}
                        />

                        {/* Correct badge tag */}
                        {isCorrect && (
                          <div className="correct-answer-pill">
                            <Check size={12} strokeWidth={3} />
                            <span>Đáp án chuẩn</span>
                          </div>
                        )}

                        {/* Delete option button */}
                        <button
                          type="button"
                          className="btn-delete-option"
                          onClick={() => handleDeleteOption(opt.key)}
                          title="Xóa phương án này"
                        >
                          <Trash2 size={15} />
                        </button>
                      </div>

                      {/* Explanation Note Box for the Correct Answer (Matching Image 2 under option C) */}
                      {isCorrect && (
                        <div className="option-solution-box">
                          <span className="solution-prefix">Lời giải phụ:</span>
                          <input
                            type="text"
                            className="solution-input"
                            value={solutionGuide}
                            onChange={(e) => setSolutionGuide(e.target.value)}
                            placeholder="Nhập ghi chú hoặc căn cứ lời giải ngắn gọn..."
                          />
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>

              {/* Add Option Button */}
              {options.length < 6 && (
                <button
                  type="button"
                  className="btn-add-new-option"
                  onClick={handleAddOption}
                >
                  <Plus size={15} />
                  <span>Thêm phương án lựa chọn</span>
                </button>
              )}
            </div>
          )}

          {/* True / False Mode */}
          {questionType === 'true_false' && (
            <div className="options-editor-card">
              <div className="options-card-header">
                <h4 className="options-title">Các mệnh đề Đúng / Sai</h4>
                <span className="badge-choose-one">Chọn Đúng hoặc Sai cho từng ý</span>
              </div>
              <div className="options-items-list">
                {tfItems.map((item, idx) => (
                  <div key={item.key} className="option-row-card">
                    <div className="option-main-line">
                      <span className="option-letter-badge">{item.key})</span>
                      <input
                        type="text"
                        className="option-text-input"
                        value={item.statement}
                        onChange={(e) => {
                          const updated = [...tfItems];
                          updated[idx].statement = e.target.value;
                          setTfItems(updated);
                        }}
                      />
                      <div className="tf-toggle-group">
                        <button
                          type="button"
                          className={`btn-tf-choice ${item.isTrue ? 'tf-true-active' : ''}`}
                          onClick={() => {
                            const updated = [...tfItems];
                            updated[idx].isTrue = true;
                            setTfItems(updated);
                          }}
                        >
                          Đúng
                        </button>
                        <button
                          type="button"
                          className={`btn-tf-choice ${!item.isTrue ? 'tf-false-active' : ''}`}
                          onClick={() => {
                            const updated = [...tfItems];
                            updated[idx].isTrue = false;
                            setTfItems(updated);
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
          )}

          {/* Short Answer Mode */}
          {questionType === 'short_answer' && (
            <div className="options-editor-card">
              <div className="options-card-header">
                <h4 className="options-title">Đáp số mong đợi</h4>
                <span className="badge-choose-one">Hệ thống sẽ so khớp câu trả lời này</span>
              </div>
              <div className="short-answer-input-box">
                <input
                  type="text"
                  className="short-answer-field"
                  value={shortAnswerExpected}
                  onChange={(e) => setShortAnswerExpected(e.target.value)}
                  placeholder="Ví dụ: 3, -1/2, 2.5..."
                />
              </div>
            </div>
          )}
        </section>

        {/* ============================================================ */}
        {/* 7. STICKY BOTTOM ACTION BAR (Matching Image 2) */}
        {/* ============================================================ */}
        <footer className="add-q-bottom-bar">
          <div className="auto-saved-cluster">
            <span className="cloud-icon">☁️</span>
            <span>Đã tự động lưu nháp lúc <strong>{lastSavedTime}</strong></span>
          </div>

          <div className="bottom-actions-cluster">
            <button
              type="button"
              className="btn-bottom-cancel"
              onClick={onClose}
            >
              Hủy bỏ
            </button>

            <button
              type="button"
              className="btn-bottom-preview"
              onClick={() => setShowLivePreview(!showLivePreview)}
            >
              <Eye size={15} />
              <span>Xem trước</span>
            </button>

            <button
              type="button"
              className="btn-bottom-continue"
              onClick={handleSaveAndContinueNext}
            >
              <Plus size={15} />
              <span>Thêm & Soạn tiếp</span>
            </button>

            <button
              type="button"
              className="btn-bottom-finish"
              onClick={handleSaveToExam}
            >
              <Check size={16} strokeWidth={2.5} />
              <span>Hoàn tất & Đóng</span>
            </button>
          </div>
        </footer>
      </div>
    </div>
  );
}
