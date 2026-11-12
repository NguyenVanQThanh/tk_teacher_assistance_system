// File Name: EditExerciseModal.jsx
// Description: Full-featured interactive modal dialog matching Image 1 exactly with left question list, right selected question LaTeX editor, live KaTeX preview, Desmos SVG attachment, formula toolbar, and save synchronization.
// Created At: 2026-09-12
// Created By: Tam Khang
// Updated At: 2026-11-12
// Updated By: AI Agent

import React, { useState, useEffect, useRef } from 'react';
import useUnsavedChangesGuard from '../../hooks/useUnsavedChangesGuard';
import { 
  X, 
  Save, 
  FileEdit, 
  Image as ImageIcon, 
  Plus, 
  Eye, 
  RefreshCw, 
  ChevronDown, 
  Check, 
  ShieldCheck, 
  ListOrdered,
  FileCode2,
  ListChecks,
  Info,
  Trash2,
  Loader2,
  Sigma,
  Table2,
  HelpCircle
} from 'lucide-react';
import { exercisesApi, questionsApi, documentsApi } from '../../services/api';
import MathRenderer, { resolveMediaUrl } from '../common/MathRenderer';
import MarkdownTable from '../common/MarkdownTable';
import { splitTableBlocks } from '../common/tableMarkdown';
import MathTextEditor from '../common/MathTextEditor';
import MathShortcutsHelp from '../common/MathShortcutsHelp';
import { symbolCategoriesBySubject } from '../common/mathSymbols';
import AddQuestionModal from './AddQuestionModal';
import QuestionMedia from '../exercises/QuestionMedia';
import confirmDialog from '../common/confirmDialog';
import './EditExerciseModal.css';

const isUuid = (val) =>
  typeof val === 'string' &&
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(val);

const QUESTION_TYPES = [
  { value: 'MultipleChoice', label: 'Trắc nghiệm 4 lựa chọn' },
  { value: 'TrueFalse', label: 'Đúng/Sai' },
  { value: 'ShortAnswer', label: 'Trả lời ngắn' },
  { value: 'Other', label: 'Khác' }
];

const normalizeQType = (raw) => {
  const t = String(raw || '').toLowerCase();
  if (t.includes('true_false') || t.includes('truefalse')) return 'TrueFalse';
  if (t.includes('short_answer') || t.includes('shortanswer')) return 'ShortAnswer';
  if (t === 'other') return 'Other';
  return 'MultipleChoice';
};

// Remove a leading "a) " / "A." style label so statements can be re-labelled per type.
const stripLabel = (t) => String(t || '').replace(/^\s*[A-Da-d][.):]\s*/, '');

const OPTION_LETTERS = ['A', 'B', 'C', 'D'];
const fourSlots = (texts, correctIdx) =>
  OPTION_LETTERS.map((k, i) => ({ key: k, text: texts[i] || '', isCorrect: i === correctIdx }));

/**
 * Convert the answer setup between question types, reusing texts where possible.
 * Returns { options, correctOption, lost } where lost = data the user would not see anymore.
 */
const convertAnswerSetup = (from, to, options, correctOption) => {
  const texts = from === 'ShortAnswer'
    ? []
    : options.map((o) => (from === 'TrueFalse' ? stripLabel(o.text) : o.text || ''));
  const filled = texts.filter((t) => t.trim());
  const shortValue = from === 'ShortAnswer' ? String(correctOption || '').trim() : '';
  const correctIdx = options.findIndex((o) => o.isCorrect);
  const trueCount = options.filter((o) => o.isCorrect).length;

  if (to === 'ShortAnswer') {
    return { options: [], correctOption: '', lost: filled.length > 0 };
  }
  let lost = Boolean(shortValue);
  if (to === 'MultipleChoice') {
    if (filled.length > 4) lost = true;
    if (from === 'TrueFalse' && trueCount > 1) lost = true;
    const safe = from === 'MultipleChoice' || from === 'TrueFalse' ? Math.max(0, correctIdx) : 0;
    return { options: fourSlots(texts, safe), correctOption: OPTION_LETTERS[safe], lost };
  }
  if (to === 'TrueFalse') {
    if (filled.length > 4) lost = true;
    const slots = fourSlots(texts, -1).map((o, i) => ({
      ...o,
      isCorrect: from === 'MultipleChoice' ? Boolean(options[i]?.isCorrect) : false
    }));
    return { options: slots, correctOption: 'A', lost };
  }
  // Other: one sub-question per non-empty text
  const subs = (filled.length ? filled : ['']).map((t, i) => ({ key: String(i + 1), text: t, isCorrect: false }));
  return { options: subs, correctOption: 'A', lost };
};

const buildQuestionPayload = (q, displayOrder) => {
  let difficulty = 'NhanBiet';
  const levelStr = String(q.level || q.levelRange || '').toLowerCase();
  if (levelStr.includes('thông hiểu') || levelStr.includes('comprehension')) {
    difficulty = 'ThongHieu';
  } else if (levelStr.includes('vận dụng') || levelStr.includes('application')) {
    difficulty = 'VanDung';
  }

  const qType = normalizeQType(q.questionType);

  let optionsPayload = [];
  if (qType === 'MultipleChoice') {
    const correctKey = q.correctOption || 'A';
    optionsPayload = (q.options || []).map((opt, idx) => ({
      content: opt.text?.trim() || `Lựa chọn ${opt.key || String.fromCharCode(65 + idx)}`,
      is_correct: opt.key === correctKey || opt.isCorrect === true,
      display_order: idx + 1
    }));
    if (optionsPayload.length < 2) {
      optionsPayload = [
        { content: 'Lựa chọn A', is_correct: true, display_order: 1 },
        { content: 'Lựa chọn B', is_correct: false, display_order: 2 }
      ];
    }
  } else if (qType === 'TrueFalse') {
    if (Array.isArray(q.tfItems) && q.tfItems.length > 0) {
      optionsPayload = q.tfItems.map((item, idx) => ({
        content: `${item.key || String.fromCharCode(97 + idx)}) ${item.text || ''}`.trim(),
        is_correct: Boolean(item.isCorrect),
        display_order: idx + 1
      }));
    } else if (Array.isArray(q.options) && q.options.length > 0) {
      optionsPayload = q.options.map((opt, idx) => ({
        content: `${String.fromCharCode(97 + idx)}) ${stripLabel(opt.text).trim() || `Mệnh đề ${idx + 1}`}`,
        is_correct: Boolean(opt.isCorrect),
        display_order: idx + 1
      }));
    } else {
      const isTrue = q.correctOption === 'true' || q.correctOption === 'Đúng' || q.correctAnswer === 'true';
      optionsPayload = [
        {
          content: `a) ${q.content?.trim() || 'Mệnh đề kiểm tra'}`,
          is_correct: isTrue,
          display_order: 1
        }
      ];
    }
  } else if (qType === 'Other') {
    optionsPayload = (q.options || [])
      .filter((opt) => opt.text?.trim())
      .map((opt, idx) => ({ content: opt.text.trim(), is_correct: false, display_order: idx + 1 }));
    if (optionsPayload.length === 0) {
      optionsPayload = [{ content: 'Ý 1', is_correct: false, display_order: 1 }];
    }
  }

  return {
    content: (q.content || 'Nội dung câu hỏi').trim(),
    content_latex: (q.content || '').trim(),
    content_markdown: (q.content || '').trim(),
    question_type: qType,
    difficulty: difficulty,
    correct_answer: qType === 'Other' ? null : (q.correctOption || q.shortAnswerExpected || (qType === 'TrueFalse' ? 'Đúng' : 'A')),
    explanation: q.solutionGuide?.trim() || null,
    image_url: q.imageUrl || null,
    image_metadata: q.imageMeta || null,
    // Segments are sent only after a table edit so untouched questions keep their original structure.
    ...(q.segmentsEdited ? { segments: q.segments } : {}),
    display_order: displayOrder,
    // Always send the list (even empty) so a type change replaces stale option rows.
    answer_options: optionsPayload
  };
};

// Wrapper keeps hooks unconditional and remounts the editor per exercise so state never leaks between exercises.
export default function EditExerciseModal(props) {
  if (!props.isOpen || !props.doc) return null;
  return <EditExerciseModalInner key={props.doc.id || props.doc.exercise_id} {...props} />;
}

function EditExerciseModalInner({ isOpen, doc, onClose, onSave }) {

  // Header Data
  const [docTitle, setDocTitle] = useState(doc.title || 'Đề cương ôn tập Toán 12 - Học kì 1 (Nâng cao)');
  const docCode = doc.code || '#TL-TOAN12-HK1';
  const subjectLabel = doc.subjectName || doc.subject;
  const gradeSubject = subjectLabel && doc.grade ? `${subjectLabel} - Lớp ${doc.grade}` : 'Toán học - Lớp 12';

  // Topic Metadata
  const [lessonTitle, setLessonTitle] = useState(
    'Chuyên đề 01: Khảo sát sự biến thiên và vẽ đồ thị hàm số chứa tham số m'
  );
  const [difficultyLevel, setDifficultyLevel] = useState('Vận dụng');
  const [durationMinutes, setDurationMinutes] = useState('45');
  const [maxScore, setMaxScore] = useState('10.0 điểm');
  const [isAddQuestionModalOpen, setIsAddQuestionModalOpen] = useState(false);

  // Backend Sync States
  const [isLoadingBackend, setIsLoadingBackend] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [deletedQuestionIds, setDeletedQuestionIds] = useState([]);
  const [saveStatusText, setSaveStatusText] = useState('');
  const [saveError, setSaveError] = useState('');

  // Initial 5 Questions Matching Image 1 & 2
  const initialQuestions = [
    {
      id: 1,
      number: 1,
      level: 'Vận dụng',
      levelRange: 'Vận dụng (7.0 - 10.0)',
      score: '2.0 điểm',
      suggestedTime: '10 phút',
      previewSnippet: 'Cho hàm số bậc ba $y = f(x) = ax^3 + bx^2 + cx + d$ có đồ thị như hình vẽ bên dưới. Tìm tất cả các giá trị thực của tham số $m$ để phương trình sau có đúng 4...',
      formulaMeta: '18 công thức • 1 đồ thị',
      answersMeta: '4 đáp án trắc nghiệm (A*)',
      attachmentName: 'Do_thi_ham_bac_ba_cau_1.svg',
      attachmentDesc: 'Đã nạp 1 hình minh họa vector tọa độ Desmos chất lượng cao ',
      content: `Cho hàm số bậc ba $y = f(x) = ax^3 + bx^2 + cx + d$ có đồ thị như hình vẽ bên dưới.

Tìm tất cả các giá trị thực của tham số $m$ để phương trình sau có đúng 4 nghiệm thực phân biệt:
$$|f(|x| - 1) + 2| = m^2 - 3m$$

Biết rằng hàm số đạt cực trị tại hai điểm $x_1 = -1$ và $x_2 = 2$, đồng thời thỏa mãn phương trình tích phân:
$$\\int_{-1}^{2} [f''(x) - 6x]\\,dx = 0$$`,
      correctOption: 'A',
      options: [
        { key: 'A', text: 'm ∈ (-1; 4) \\ {0; 3}' },
        { key: 'B', text: 'm ∈ [-2; 5)' },
        { key: 'C', text: 'm ∈ (0; 3) ∪ {4}' },
        { key: 'D', text: 'm ∈ (-∞; -1) ∪ (4; +∞)' }
      ],
      solutionGuide: `Bước 1: Khảo sát hàm số gốc y = f(x) dựa vào điểm cực trị và tích phân đã cho.
Bước 2: Sử dụng phép tịnh tiến và lấy đối xứng đồ thị để suy ra số giao điểm của đồ thị hàm |f(|x| - 1) + 2| với đường thẳng y = m^2 - 3m.
Bước 3: Kết luận điều kiện của m để có 4 nghiệm phân biệt.`
    },
    {
      id: 2,
      number: 2,
      level: 'Thông hiểu',
      levelRange: 'Thông hiểu (5.0 - 7.0)',
      score: '2.0 điểm',
      suggestedTime: '8 phút',
      previewSnippet: 'Tìm nguyên hàm của hàm số $f(x) = 2x + e^x$. Biết rằng một nguyên hàm $F(x)$ thỏa mãn $F(0) = 3$...',
      formulaMeta: '3 công thức',
      answersMeta: '4 đáp án (Chưa chọn)',
      attachmentName: null,
      attachmentDesc: null,
      content: `Tìm nguyên hàm của hàm số $f(x) = 2x + e^x$. Biết rằng một nguyên hàm $F(x)$ thỏa mãn $F(0) = 3$. Tính giá trị của biểu thức $F(1) - F(-1)$.`,
      correctOption: null,
      options: [
        { key: 'A', text: 'F(x) = x^2 + e^x + 2' },
        { key: 'B', text: 'F(x) = x^2 + e^x + 3' },
        { key: 'C', text: 'F(x) = 2x^2 + e^x + 1' },
        { key: 'D', text: 'F(x) = x^2 - e^x + 4' }
      ],
      solutionGuide: `Ta có nguyên hàm: F(x) = ∫ (2x + e^x) dx = x^2 + e^x + C.
Theo giả thiết F(0) = 0 + e^0 + C = 1 + C = 3 => C = 2.
Vậy F(x) = x^2 + e^x + 2.`
    },
    {
      id: 3,
      number: 3,
      level: 'Nhận biết',
      levelRange: 'Nhận biết (0.0 - 5.0)',
      score: '1.5 điểm',
      suggestedTime: '4 phút',
      previewSnippet: 'Cho khối lăng trụ có diện tích đáy $B = 6$ và chiều cao $h = 3$. Thể tích của khối lăng trụ đã cho bằng bao nhiêu?...',
      formulaMeta: '1 công thức',
      answersMeta: '4 đáp án (B*)',
      attachmentName: null,
      attachmentDesc: null,
      content: `Cho khối lăng trụ có diện tích đáy $B = 6$ và chiều cao $h = 3$. Thể tích của khối lăng trụ đã cho bằng bao nhiêu?`,
      correctOption: 'B',
      options: [
        { key: 'A', text: 'V = 9' },
        { key: 'B', text: 'V = 18' },
        { key: 'C', text: 'V = 6' },
        { key: 'D', text: 'V = 54' }
      ],
      solutionGuide: `Thể tích của khối lăng trụ đã cho: V = B · h = 6 · 3 = 18 (đvtt).`
    },
    {
      id: 4,
      number: 4,
      level: 'Vận dụng',
      levelRange: 'Vận dụng (7.0 - 10.0)',
      score: '2.5 điểm',
      suggestedTime: '12 phút',
      previewSnippet: 'Trong không gian $Oxyz$, cho mặt cầu $(S): x^2 + y^2 + z^2 - 2x + 4y - 6z - 11 = 0$ và mặt phẳng $(P): 2x + 2y - z + 17 = 0$...',
      formulaMeta: '8 công thức',
      answersMeta: '4 đáp án (D*)',
      attachmentName: null,
      attachmentDesc: null,
      content: `Trong không gian $Oxyz$, cho mặt cầu $(S): x^2 + y^2 + z^2 - 2x + 4y - 6z - 11 = 0$ và mặt phẳng $(P): 2x + 2y - z + 17 = 0$. Xác định vị trí tương đối giữa mặt phẳng $(P)$ và mặt cầu $(S)$.`,
      correctOption: 'D',
      options: [
        { key: 'A', text: 'd = 3, tiếp xúc' },
        { key: 'B', text: 'd = 5, cắt theo đường tròn bán kính r = 3' },
        { key: 'C', text: 'd = 7, không có điểm chung' },
        { key: 'D', text: 'd = 4, cắt theo đường tròn bán kính r = 3' }
      ],
      solutionGuide: `Mặt cầu (S) có tâm I(1; -2; 3) và bán kính R = 5.
Khoảng cách từ I đến mặt phẳng (P): d = |2(1) + 2(-2) - 3 + 17| / 3 = 12 / 3 = 4.
Do d < R nên mặt phẳng (P) cắt (S) theo đường tròn bán kính r = √(25 - 16) = 3.`
    },
    {
      id: 5,
      number: 5,
      level: 'Thông hiểu',
      levelRange: 'Thông hiểu (5.0 - 7.0)',
      score: '2.0 điểm',
      suggestedTime: '6 phút',
      previewSnippet: 'Cho hình chóp $S.ABCD$ có đáy $ABCD$ là hình vuông cạnh $a$, $SA$ vuông góc với đáy, $SA = a\\sqrt{3}$. Tính góc giữa đường thẳng $SB$ và mặt phẳng...',
      formulaMeta: '5 công thức • 1 hình vẽ',
      answersMeta: '4 đáp án (A*)',
      attachmentName: null,
      attachmentDesc: null,
      content: `Cho hình chóp $S.ABCD$ có đáy $ABCD$ là hình vuông cạnh $a$, cạnh bên $SA$ vuông góc với mặt phẳng đáy và $SA = a\\sqrt{3}$. Tính góc giữa đường thẳng $SB$ và mặt phẳng $(ABCD)$.`,
      correctOption: 'A',
      options: [
        { key: 'A', text: '60°' },
        { key: 'B', text: '45°' },
        { key: 'C', text: '30°' },
        { key: 'D', text: '90°' }
      ],
      solutionGuide: `Hình chiếu vuông góc của SB lên mặt đáy (ABCD) là AB. Góc giữa SB và (ABCD) là góc ∠SBA.
Tam giác vuông SAB tại A: tan(∠SBA) = SA / AB = a√3 / a = √3 => ∠SBA = 60°.`
    }
  ];

  // Helpers
  const getSimpleLevel = (levelStr) => {
    if (!levelStr) return 'Vận dụng';
    if (levelStr.startsWith('Vận dụng')) return 'Vận dụng';
    if (levelStr.startsWith('Thông hiểu')) return 'Thông hiểu';
    if (levelStr.startsWith('Nhận biết')) return 'Nhận biết';
    return levelStr.split('(')[0].trim();
  };

  // Helper to extract numeric score string without 'điểm'
  const getRawScore = (scoreStr) => {
    if (!scoreStr) return '';
    return scoreStr.replace('điểm', '').replace('đ', '').trim();
  };

  // Score input handler: max 4 chars, only digits and '.', single dot
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
    setCurrentScore(`${val} điểm`);
  };

  const cleanContentForPreview = (content, qNum) => {
    if (!content) return '';
    const prefixRegex = new RegExp(`^Câu\\s*${qNum}[^:]*:\\s*`, 'i');
    return content.replace(prefixRegex, '').trim();
  };

  const renderLiveContent = (rawText) => {
    if (!rawText) return <p className="preview-empty-text">(Chưa có nội dung câu hỏi)</p>;
    // Markdown tables render as real tables; remaining text keeps the per-line rendering
    const parts = splitTableBlocks(rawText);
    if (parts.some((p) => p.type === 'table')) {
      return parts.map((p, i) => (p.type === 'table'
        ? <MarkdownTable key={`t${i}`} markdown={p.value} />
        : <React.Fragment key={`x${i}`}>{renderLiveText(p.value)}</React.Fragment>));
    }
    return renderLiveText(rawText);
  };

  const renderLiveText = (rawText) => {
    if (!rawText.trim()) return null;
    const blocks = rawText.split(/\n\s*\n/);
    return blocks.map((block, bIdx) => {
      const trimmed = block.trim();
      if (!trimmed) return null;

      if (trimmed.startsWith('$$') && trimmed.endsWith('$$')) {
        return (
          <div key={bIdx} className="preview-highlight-formula-card">
            <MathRenderer text={trimmed} />
          </div>
        );
      }

      return (
        <div key={bIdx} className="preview-content-block">
          {block.split('\n').map((line, lIdx) => {
            const trimmedLine = line.trim();
            if (!trimmedLine) return null;
            if (trimmedLine.startsWith('$$') && trimmedLine.endsWith('$$')) {
              return (
                <div key={lIdx} className="preview-highlight-formula-card">
                  <MathRenderer text={trimmedLine} />
                </div>
              );
            }
            return (
              <div key={lIdx} className="preview-content-line">
                <MathRenderer text={line} />
              </div>
            );
          })}
        </div>
      );
    });
  };

  // Questions List State
  const [questions, setQuestions] = useState(initialQuestions);
  const [selectedQuestionId, setSelectedQuestionId] = useState(1);

  // Load real questions from backend when modal opens
  useEffect(() => {
    if (!isOpen || !doc) return;
    let isMounted = true;
    const targetId = doc.id || doc.exercise_id;

    if (isUuid(targetId)) {
      setIsLoadingBackend(true);
      exercisesApi.getExerciseDetail(targetId)
        .then((detail) => {
          if (!isMounted || !detail) return;
          if (detail.title) setDocTitle(detail.title);
          if (Array.isArray(detail.questions) && detail.questions.length > 0) {
            const mapped = detail.questions.filter((q) => q.status !== 'DELETED').map((q, idx) => {
              const letters = ['A', 'B', 'C', 'D', 'E', 'F'];
              const loadedType = normalizeQType(q.question_type);
              let options = (q.answer_options || [])
                .slice()
                .sort((a, b) => (a.display_order || 0) - (b.display_order || 0))
                .map((opt, oIdx) => ({
                  id: opt.option_id,
                  key: loadedType === 'Other' ? String(oIdx + 1) : (letters[oIdx] || String(oIdx + 1)),
                  text: loadedType === 'TrueFalse' ? stripLabel(opt.content) : opt.content,
                  isCorrect: Boolean(opt.is_correct)
                }));
              if (loadedType === 'TrueFalse') {
                // Pad legacy statements to the 4 slots a-d
                options = OPTION_LETTERS.map((k, i) => ({ ...(options[i] || { text: '', isCorrect: false }), key: k }));
              } else if (loadedType === 'Other' && options.length === 0) {
                options = [{ key: '1', text: '', isCorrect: false }];
              }
              const correctOpt = loadedType === 'ShortAnswer' ? (q.correct_answer || '') : (options.find(o => o.isCorrect)?.key || q.correct_answer || 'A');
              let levelText = 'Nhận biết';
              if (q.difficulty === 'ThongHieu') levelText = 'Thông hiểu';
              else if (q.difficulty === 'VanDung') levelText = 'Vận dụng';

              return {
                id: q.question_id,
                backendQuestionId: q.question_id,
                number: q.display_order || idx + 1,
                level: levelText,
                levelRange: `${levelText} (0.0 - 10.0)`,
                score: '2.0 điểm',
                suggestedTime: '5 phút',
                previewSnippet: q.content ? q.content.slice(0, 120) + (q.content.length > 120 ? '...' : '') : '',
                formulaMeta: q.content?.includes('$') ? 'Chứa công thức' : 'Văn bản thường',
                answersMeta: `${options.length} đáp án (${correctOpt}*)`,
                content: q.content || q.content_latex || '',
                questionType: loadedType,
                correctOption: correctOpt,
                options: (options.length > 0 || loadedType === 'ShortAnswer') ? options : [
                  { key: 'A', text: '', isCorrect: true },
                  { key: 'B', text: '', isCorrect: false },
                  { key: 'C', text: '', isCorrect: false },
                  { key: 'D', text: '', isCorrect: false }
                ],
                solutionGuide: q.explanation || '',
                imageUrl: q.image_url || null,
                imageMeta: q.image_metadata || null,
                segments: Array.isArray(q.segments) ? q.segments : []
              };
            }).sort((a, b) => a.number - b.number);
            setQuestions(mapped);
            if (mapped.length > 0) {
              const firstQ = mapped[0];
              setSelectedQuestionId(firstQ.id);
              setCurrentLevel(firstQ.levelRange || `${firstQ.level || 'Nhận biết'} (0.0 - 10.0)`);
              setCurrentScore(firstQ.score || '2.0 điểm');
              setCurrentContent(firstQ.content || '');
              setCurrentOptions(firstQ.options || [
                { key: 'A', text: '', isCorrect: true },
                { key: 'B', text: '', isCorrect: false },
                { key: 'C', text: '', isCorrect: false },
                { key: 'D', text: '', isCorrect: false }
              ]);
              setCurrentCorrectOption(firstQ.correctOption || 'A');
              setCurrentSolutionGuide(firstQ.solutionGuide || '');
            }
          }
          setDeletedQuestionIds([]);
        })
        .catch((err) => {
          console.warn('Could not load exercise questions from backend:', err);
        })
        .finally(() => {
          if (isMounted) setIsLoadingBackend(false);
        });
    }
    return () => {
      isMounted = false;
    };
  }, [isOpen, doc]);

  // Active question being edited in right panel
  const activeQuestion = questions.find(q => q.id === selectedQuestionId) || questions[0] || {};

  // Editor states for active question
  const [currentLevel, setCurrentLevel] = useState(activeQuestion?.levelRange || 'Nhận biết (0.0 - 10.0)');
  const [currentScore, setCurrentScore] = useState(activeQuestion?.score || '2.0 điểm');
  const [currentContent, setCurrentContent] = useState(activeQuestion?.content || '');
  const [currentOptions, setCurrentOptions] = useState(
    activeQuestion?.options || [
      { key: 'A', text: 'm ∈ (-1; 4) \\ {0; 3}' },
      { key: 'B', text: 'm ∈ [-2; 5)' },
      { key: 'C', text: 'm ∈ (0; 3) ∪ {4}' },
      { key: 'D', text: 'm ∈ (-∞; -1) ∪ (4; +∞)' }
    ]
  );
  const [currentCorrectOption, setCurrentCorrectOption] = useState(activeQuestion?.correctOption || 'A');
  const [currentSolutionGuide, setCurrentSolutionGuide] = useState(activeQuestion?.solutionGuide || '');
  const [saveToast, setSaveToast] = useState(false);
  const editorRefs = useRef({});
  const activeEditorRef = useRef(null);
  const activeFieldRef = useRef('content');
  const setActive = (key) => { activeFieldRef.current = key; activeEditorRef.current = editorRefs.current[key]; };
  const [isHelpOpen, setIsHelpOpen] = useState(false);
  const [tableDims, setTableDims] = useState({ open: false, rows: 3, cols: 3 });
  const [editorFontSize, setEditorFontSize] = useState(14);
  const helpBtnRef = useRef(null);
  const imageInputRef = useRef(null);
  const [isUploadingImage, setIsUploadingImage] = useState(false);
  // Warn before dismissing with unsaved edits (raw onClose is still used after a successful save)
  const guardedClose = useUnsavedChangesGuard(
    { docTitle, lessonTitle, difficultyLevel, durationMinutes, questions, deletedQuestionIds, currentLevel, currentScore, currentContent, currentOptions, currentCorrectOption, currentSolutionGuide },
    onClose,
    !isLoadingBackend
  );
  const isSwitchingRef = useRef(false);

  // Select question handler with safety against race condition
  const handleSelectQuestion = (qId) => {
    isSwitchingRef.current = true;
    activeFieldRef.current = 'content';
    setSelectedQuestionId(qId);
    const targetQ = questions.find(q => q.id === qId);
    if (targetQ) {
      setCurrentLevel(targetQ.levelRange || `${targetQ.level || 'Nhận biết'} (0.0 - 10.0)`);
      setCurrentScore(targetQ.score || '2.0 điểm');
      setCurrentContent(targetQ.content || '');
      setCurrentOptions(targetQ.options || [
        { key: 'A', text: '', isCorrect: true },
        { key: 'B', text: '', isCorrect: false },
        { key: 'C', text: '', isCorrect: false },
        { key: 'D', text: '', isCorrect: false }
      ]);
      setCurrentCorrectOption(targetQ.correctOption || 'A');
      setCurrentSolutionGuide(targetQ.solutionGuide || '');
    }
    setTimeout(() => {
      isSwitchingRef.current = false;
    }, 80);
  };

  // Real-time synchronization of editor fields into questions list
  useEffect(() => {
    if (isSwitchingRef.current) return;
    setQuestions(prev => prev.map(q => {
      if (q.id === selectedQuestionId) {
        return {
          ...q,
          levelRange: currentLevel,
          level: getSimpleLevel(currentLevel),
          score: currentScore,
          content: currentContent,
          options: currentOptions,
          correctOption: currentCorrectOption,
          solutionGuide: currentSolutionGuide,
          answersMeta: currentCorrectOption 
            ? `4 đáp án (${currentCorrectOption}*)` 
            : '4 đáp án (Chưa chọn)',
          previewSnippet: currentContent.split('\n').filter(l => l.trim().length > 0)[0] || 'Nội dung câu hỏi...'
        };
      }
      return q;
    }));
  }, [currentLevel, currentScore, currentContent, currentOptions, currentCorrectOption, currentSolutionGuide, selectedQuestionId]);

  const activeType = normalizeQType(activeQuestion?.questionType);

  // Switch question type: keep content, convert only the answer setup (confirm before dropping data).
  // Replace the markdown of the table segment at `segIdx`; null removes it.
  const updateTableSegment = (segIdx, md) => {
    setQuestions(prev => prev.map(q => {
      if (q.id !== selectedQuestionId) return q;
      const segs = (q.segments || []).map((sg, i) => (i === segIdx ? { ...sg, content: md } : sg))
        .filter((sg, i) => !(i === segIdx && md === null));
      return { ...q, segments: segs, segmentsEdited: true };
    }));
  };

  const handleChangeType = async (nextType) => {
    if (nextType === activeType) return;
    const conv = convertAnswerSetup(activeType, nextType, currentOptions || [], currentCorrectOption);
    if (conv.lost && !(await confirmDialog('Đổi loại câu hỏi sẽ bỏ một phần dữ liệu đáp án hiện tại (không còn chỗ chứa). Tiếp tục?', { title: 'Đổi loại câu hỏi', confirmText: 'Tiếp tục' }))) {
      return;
    }
    setQuestions(prev => prev.map(q => (q.id === selectedQuestionId ? { ...q, questionType: nextType } : q)));
    setCurrentOptions(conv.options);
    setCurrentCorrectOption(conv.correctOption);
  };

  const handleToggleTf = (key) => {
    setCurrentOptions(prev => prev.map(o => (o.key === key ? { ...o, isCorrect: !o.isCorrect } : o)));
  };

  const handleAddSubQuestion = () => {
    setCurrentOptions(prev => [...prev, { key: String(prev.length + 1), text: '', isCorrect: false }]);
  };

  const handleRemoveSubQuestion = (key) => {
    setCurrentOptions(prev => {
      const rest = prev.filter(o => o.key !== key);
      const next = rest.length ? rest : [{ key: '1', text: '', isCorrect: false }];
      return next.map((o, i) => ({ ...o, key: String(i + 1) }));
    });
  };

  // Option text change handler
  const handleOptionTextChange = (key, val) => {
    setCurrentOptions(prev => prev.map(o => o.key === key ? { ...o, text: val } : o));
  };

  // Symbol Categories for Math, Physics, Chemistry & Greek like Word Equation Ribbon
  const [activeSubjectTab, setActiveSubjectTab] = useState('math');

  const currentSubjectData = symbolCategoriesBySubject[activeSubjectTab] || symbolCategoriesBySubject.math;

  // Insert a LaTeX template into the active editor (MathLive placeholders: #? slot, #@ selection)
  const insertTable = () => {
    (activeEditorRef.current || editorRefs.current.content)?.insertTable(tableDims.rows, tableDims.cols);
    setTableDims((d) => ({ ...d, open: false }));
  };
  const insertMath = (tpl, opts = {}) => (activeEditorRef.current || editorRefs.current.content)?.insertMath(tpl, opts);

  // Upload a real image to BE storage, insert its markdown into the active field,
  // and persist the returned metadata on the active question (saved to DB on save).
  const handleImagePick = async (e) => {
    const file = e.target.files && e.target.files[0];
    e.target.value = '';
    if (!file) return;
    if (!/^image\//.test(file.type || '')) {
      setSaveError('Chỉ chấp nhận tệp hình ảnh (png, jpg, jpeg, gif, bmp, webp, svg).');
      return;
    }
    setIsUploadingImage(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const meta = await questionsApi.uploadImage(formData);
      const alt = (meta.original_name || 'hinh-anh').replace(/[[\]]/g, '');
      (activeEditorRef.current || editorRefs.current.content)?.insertImage(alt, meta.url);
      const imageMeta = {
        url: meta.url,
        filename: meta.filename,
        original_name: meta.original_name,
        size_bytes: meta.size_bytes,
        content_type: meta.content_type,
        width: meta.width,
        height: meta.height,
        uploaded_at: new Date().toISOString()
      };
      setQuestions(prev => prev.map(q => (q.id === activeQuestion.id ? { ...q, imageUrl: meta.url, imageMeta } : q)));
      setSaveStatusText('Đã tải ảnh lên!');
      setSaveToast(true);
      setTimeout(() => { setSaveToast(false); setSaveStatusText(''); }, 2200);
    } catch (err) {
      console.error('Upload image failed:', err);
      setSaveError('Không thể tải ảnh lên. Vui lòng thử lại.');
    } finally {
      setIsUploadingImage(false);
    }
  };

  // Save changes to current question in list and sync with DB if real exercise
  const handleSaveActiveQuestion = async () => {
    let updatedAnswersMeta = currentCorrectOption 
      ? `${currentOptions?.length || 4} đáp án (${currentCorrectOption}*)` 
      : `${currentOptions?.length || 4} đáp án (Chưa chọn)`;
    if (activeType === 'ShortAnswer') {
      updatedAnswersMeta = `Đáp án: ${currentCorrectOption || 'Chưa nhập'}`;
    } else if (activeType === 'TrueFalse') {
      updatedAnswersMeta = `${currentOptions?.length || 4} mệnh đề (Đúng/Sai)`;
    } else if (activeType === 'Other') {
      updatedAnswersMeta = `${currentOptions?.length || 0} ý`;
    }

    const currentQData = {
      levelRange: currentLevel,
      level: getSimpleLevel(currentLevel),
      score: currentScore,
      content: currentContent,
      options: currentOptions,
      correctOption: currentCorrectOption,
      solutionGuide: currentSolutionGuide,
      questionType: activeType,
      answersMeta: updatedAnswersMeta,
      previewSnippet: currentContent.split('\n').filter(l => l.trim().length > 0)[0] || 'Nội dung câu hỏi...'
    };

    setQuestions(prev => prev.map(q => {
      if (q.id === activeQuestion.id) {
        return { ...q, ...currentQData };
      }
      return q;
    }));

    // Directly save/update this question to DB if attached to real exercise
    const targetId = doc.id || doc.exercise_id;
    if (isUuid(targetId)) {
      const qToSave = { ...activeQuestion, ...currentQData };
      const qIndex = questions.findIndex(q => q.id === activeQuestion.id);
      const payload = buildQuestionPayload(qToSave, qIndex !== -1 ? qIndex + 1 : 1);
      try {
        if (isUuid(activeQuestion.backendQuestionId || activeQuestion.id)) {
          await questionsApi.updateQuestion(activeQuestion.backendQuestionId || activeQuestion.id, payload);
          setSaveStatusText('Đã lưu vào DB!');
        } else {
          const created = await exercisesApi.addQuestion(targetId, payload);
          if (created?.question_id) {
            setQuestions(prev => prev.map(q => q.id === activeQuestion.id ? { ...q, id: created.question_id, backendQuestionId: created.question_id } : q));
          }
          setSaveStatusText('Đã thêm mới vào DB!');
        }
      } catch (err) {
        console.error('Failed to save question to DB:', err);
        setSaveStatusText('Lỗi lưu DB');
      }
    } else {
      setSaveStatusText('Đã lưu câu hỏi!');
    }

    setSaveToast(true);
    setTimeout(() => {
      setSaveToast(false);
      setSaveStatusText('');
    }, 2200);
  };

  // Keyboard shortcut Ctrl + S
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') {
        e.preventDefault();
        handleSaveActiveQuestion();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [currentLevel, currentScore, currentContent, currentOptions, currentCorrectOption, currentSolutionGuide, activeQuestion.id]);

  // Add new question handler
  const handleAddNewQuestion = async () => {
    const newId = `new-${Date.now()}`;
    const newNum = questions.length + 1;
    const newQ = {
      id: newId,
      number: newNum,
      level: 'Vận dụng',
      levelRange: 'Vận dụng (7.0 - 10.0)',
      score: '2.0 điểm',
      suggestedTime: '10 phút',
      previewSnippet: `Câu ${newNum}: Nhập nội dung câu hỏi mới...`,
      formulaMeta: '0 công thức',
      answersMeta: '4 đáp án (Chưa chọn)',
      attachmentName: null,
      attachmentDesc: null,
      content: 'Nhập nội dung đề bài tại đây...',
      correctOption: null,
      options: [
        { key: 'A', text: 'Đáp án A' },
        { key: 'B', text: 'Đáp án B' },
        { key: 'C', text: 'Đáp án C' },
        { key: 'D', text: 'Đáp án D' }
      ],
      solutionGuide: ''
    };

    const targetId = doc.id || doc.exercise_id;
    if (isUuid(targetId)) {
      try {
        const payload = buildQuestionPayload(newQ, newNum);
        const created = await exercisesApi.addQuestion(targetId, payload);
        if (created?.question_id) {
          newQ.id = created.question_id;
          newQ.backendQuestionId = created.question_id;
        }
      } catch (err) {
        console.error('Failed to add new question to backend:', err);
      }
    }

    setQuestions([...questions, newQ]);
    handleSelectQuestion(newQ.id);
  };

  // Delete question handler
  const handleDeleteQuestion = async (qId) => {
    if (questions.length <= 1) {
      alert('Đề thi cần có ít nhất 1 câu hỏi.');
      return;
    }
    const targetId = doc.id || doc.exercise_id;
    const targetQ = questions.find(q => q.id === qId);
    const backendQId = targetQ?.backendQuestionId || (isUuid(qId) ? qId : null);

    if (backendQId && isUuid(targetId)) {
      try {
        await questionsApi.deleteQuestion(backendQId);
        setDeletedQuestionIds(prev => [...prev, backendQId]);
      } catch (err) {
        console.error('Failed to delete question from backend:', err);
      }
    }

    const remaining = questions.filter(q => q.id !== qId);
    setQuestions(remaining);
    if (selectedQuestionId === qId && remaining.length > 0) {
      handleSelectQuestion(remaining[0].id);
    }
  };

  const handleSaveFromAddModal = async (newQuestionData) => {
    const targetId = doc.id || doc.exercise_id;
    if (isUuid(targetId)) {
      try {
        const payload = buildQuestionPayload(newQuestionData, questions.length + 1);
        const created = await exercisesApi.addQuestion(targetId, payload);
        if (created?.question_id) {
          newQuestionData.id = created.question_id;
          newQuestionData.backendQuestionId = created.question_id;
        }
      } catch (err) {
        console.error('Failed to add question from modal to backend:', err);
      }
    }
    setQuestions((prev) => [...prev, newQuestionData]);
    handleSelectQuestion(newQuestionData.id);
  };

  const handleSaveAndContinueFromAddModal = async (newQuestionData) => {
    const targetId = doc.id || doc.exercise_id;
    if (isUuid(targetId)) {
      try {
        const payload = buildQuestionPayload(newQuestionData, questions.length + 1);
        const created = await exercisesApi.addQuestion(targetId, payload);
        if (created?.question_id) {
          newQuestionData.id = created.question_id;
          newQuestionData.backendQuestionId = created.question_id;
        }
      } catch (err) {
        console.error('Failed to add question from modal to backend:', err);
      }
    }
    setQuestions((prev) => [...prev, newQuestionData]);
  };

  // Main Save Handler with Full Backend Persistence
  const handleMainSave = async () => {
    setIsSaving(true);
    setSaveError('');
    const targetId = doc.id || doc.exercise_id;

    if (isUuid(targetId)) {
      try {
        // 1. Update document/exercise title if modified
        if (docTitle.trim() && docTitle.trim() !== doc.title) {
          try {
            await documentsApi.updateDocument(targetId, { title: docTitle.trim() });
          } catch (e) {
            try {
              await exercisesApi.updateExercise(targetId, { title: docTitle.trim() });
            } catch (err2) {
              console.warn('Could not update title in backend:', err2);
            }
          }
        }

        // 2. Ensure current active question has latest form state
        const activeIdx = questions.findIndex(q => q.id === activeQuestion?.id);
        const upToDateQuestions = questions.map((q, idx) => {
          if (idx === activeIdx) {
            return {
              ...q,
              levelRange: currentLevel,
              level: getSimpleLevel(currentLevel),
              score: currentScore,
              content: currentContent,
              options: currentOptions,
              correctOption: currentCorrectOption,
              solutionGuide: currentSolutionGuide,
            };
          }
          return q;
        });

        // 3. Batch save/update each question
        for (let i = 0; i < upToDateQuestions.length; i++) {
          const q = upToDateQuestions[i];
          const payload = buildQuestionPayload(q, i + 1);
          const backendQId = q.backendQuestionId || (isUuid(q.id) ? q.id : null);
          if (backendQId) {
            await questionsApi.updateQuestion(backendQId, payload);
          } else {
            const created = await exercisesApi.addQuestion(targetId, payload);
            if (created?.question_id) {
              q.id = created.question_id;
              q.backendQuestionId = created.question_id;
            }
          }
        }
      } catch (err) {
        console.error('Failed to sync all changes to backend:', err);
        // Keep the modal open so unsaved edits are not lost.
        setSaveError('Failed to save changes. Please try again.');
        setIsSaving(false);
        return;
      }
    }

    const updated = {
      ...doc,
      title: docTitle,
      lessonTitle,
      difficultyLevel,
      questionsCount: `${questions.length} câu hỏi`,
      duration: `${durationMinutes} phút`,
      questions,
      updatedAt: new Date().toISOString()
    };
    try {
      if (onSave) {
        await onSave(updated);
      }
      onClose();
    } catch (err) {
      console.error('Failed to save exercise:', err);
      setSaveError('Failed to save changes. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  // Helper to get Level Badge styling class
  const getLevelBadgeClass = (level) => {
    if (level?.includes('Nhận biết')) return 'badge-level-know';
    if (level?.includes('Thông hiểu')) return 'badge-level-comp';
    return 'badge-level-app';
  };

  return (
    <div className="edit-modal-backdrop" onClick={guardedClose}>
      <div className="edit-modal-dialog" onClick={(e) => e.stopPropagation()}>
        {/* ============================================================ */}
        {/* 1. TOP HEADER */}
        {/* ============================================================ */}
        <header className="edit-modal-header">
          <div className="header-left-cluster">
            <div className="header-icon-badge">
              <FileEdit size={22} />
            </div>
            <div className="header-text-block">
              <div className="header-title-row">
                <h2 className="header-main-title">Chỉnh sửa nội dung tài liệu & bài tập</h2>
                <span className="header-tag-pill">{gradeSubject}</span>
                <span className="header-autosave-notice">
                  <span className="autosave-dot" />
                  Đã tự động lưu nháp 2 phút trước
                </span>
              </div>
              <div className="header-doc-rename-row">
                <span className="doc-rename-label">Tài liệu:</span>
                <div className="doc-rename-input-wrap">
                  <input
                    type="text"
                    className="doc-rename-input"
                    value={docTitle}
                    onChange={(e) => setDocTitle(e.target.value)}
                    placeholder="Nhập tên tài liệu..."
                    title="Bấm để chỉnh sửa tên tài liệu"
                  />
                  <FileEdit size={13} className="doc-rename-icon" />
                </div>
                <span className="doc-rename-divider">•</span>
                <span className="doc-code-badge">Mã TL: {docCode}</span>
              </div>
            </div>
          </div>

          <div className="header-right-actions">
            <button 
              type="button" 
              className="btn-header-close"
              onClick={guardedClose}
              disabled={isSaving}
            >
              <X size={15} />
              <span>Đóng</span>
            </button>
            <button 
              type="button" 
              className="btn-header-save"
              onClick={handleMainSave}
              disabled={isSaving}
            >
              {isSaving ? (
                <>
                  <Loader2 size={16} className="animate-spin" />
                  <span>Đang lưu DB...</span>
                </>
              ) : (
                <>
                  <Save size={16} />
                  <span>Lưu & Cập nhật</span>
                </>
              )}
            </button>
          </div>
        </header>

        {/* ============================================================ */}
        {/* 2. SCROLLABLE DIALOG BODY */}
        {/* ============================================================ */}
        <div className="edit-modal-scrollable-body">
          {/* Formula Toolbar */}
          <section className="formula-toolbar-container">
            {/* Subject Tabs like MS Word Symbol / Equation Ribbon */}
            <div className="formula-toolbar-top-strip">
              <div className="formula-top-left-cluster">
                <div className="formula-sigma-label">
                  <span className="sigma-symbol">Σ</span>
                  <span className="sigma-text">Bảng ký hiệu:</span>
                </div>

                <div className="formula-subject-tabs">
                  <button 
                    type="button" 
                    className={`subject-tab-btn ${activeSubjectTab === 'math' ? 'active' : ''}`}
                    onClick={() => setActiveSubjectTab('math')}
                  >
                    <span className="tab-icon">📐</span>
                    <span>Toán học</span>
                  </button>
                  <button 
                    type="button" 
                    className={`subject-tab-btn ${activeSubjectTab === 'physics' ? 'active' : ''}`}
                    onClick={() => setActiveSubjectTab('physics')}
                  >
                    <span className="tab-icon">⚡</span>
                    <span>Vật lí</span>
                  </button>
                  <button 
                    type="button" 
                    className={`subject-tab-btn ${activeSubjectTab === 'chemistry' ? 'active' : ''}`}
                    onClick={() => setActiveSubjectTab('chemistry')}
                  >
                    <span className="tab-icon">🧪</span>
                    <span>Hóa học</span>
                  </button>
                  <button 
                    type="button" 
                    className={`subject-tab-btn ${activeSubjectTab === 'greek' ? 'active' : ''}`}
                    onClick={() => setActiveSubjectTab('greek')}
                  >
                    <span className="tab-icon">Ω</span>
                    <span>Ký tự Hy Lạp</span>
                  </button>
                </div>
              </div>

              {/* Thời gian làm bài chung khung bảng ký hiệu (Hình 2 style) */}
              <div className="formula-top-meta-cluster">
                {/* Thời gian làm bài */}
                <div className="toolbar-duration-pill-container" title="Thời gian làm bài">
                  <input
                    type="text"
                    className="toolbar-duration-input"
                    value={String(durationMinutes).replace(/[^0-9]/g, '')}
                    onChange={(e) => {
                      const val = e.target.value.replace(/[^0-9]/g, '').slice(0, 3);
                      setDurationMinutes(val || '1');
                    }}
                    placeholder="45"
                  />
                  <span className="toolbar-duration-unit">phút</span>
                </div>
              </div>
            </div>

            {/* Symbols groups for active subject */}
            <div className="formula-categories-row">
              {currentSubjectData.groups.map((cat, idx) => (
                <div key={idx} className="formula-group-seg">
                  <span className="formula-group-title">{cat.group}</span>
                  <div className="formula-chips-wrap">
                    {cat.items.map((item, i) => (
                      <button
                        key={i}
                        type="button"
                        className="formula-chip-btn"
                        onMouseDown={(e) => e.preventDefault()}
                        onClick={() => insertMath(item.tpl || item.code)}
                        title={`${item.tip} (${item.code})`}
                      >
                        <MathRenderer text={`$${item.display}$`} />
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            {/* Quick Insert Actions Row */}
            <div className="toolbar-bottom-actions" style={{ position: 'relative' }}>
              <button
                type="button"
                className="btn-toolbar-tool"
                onMouseDown={(e) => e.preventDefault()}
                onClick={() => imageInputRef.current && imageInputRef.current.click()}
                disabled={isUploadingImage}
                title="Tải ảnh từ máy lên rồi chèn vào ô đang soạn thảo"
              >
                {isUploadingImage ? <Loader2 size={14} className="animate-spin" /> : <ImageIcon size={14} />}
                <span>{isUploadingImage ? 'Đang tải ảnh...' : 'Chèn hình ảnh'}</span>
              </button>
              <input
                ref={imageInputRef}
                type="file"
                accept="image/*"
                style={{ display: 'none' }}
                onChange={handleImagePick}
              />

              <button
                type="button"
                className="btn-toolbar-tool"
                onMouseDown={(e) => e.preventDefault()}
                onClick={() => insertMath('#?x^2+#?x+#?=0', { display: true })}
                title="Chèn phương trình bậc 2: ax² + bx + c = 0"
              >
                <Sigma size={14} />
                <span>PT bậc 2</span>
              </button>

              <button
                type="button"
                className="btn-toolbar-tool"
                onMouseDown={(e) => e.preventDefault()}
                onClick={() => insertMath('#?x^3+#?x^2+#?x+#?=0', { display: true })}
                title="Chèn phương trình bậc 3: ax³ + bx² + cx + d = 0"
              >
                <Sigma size={14} />
                <span>PT bậc 3</span>
              </button>

              <button
                type="button"
                className="btn-toolbar-tool"
                onMouseDown={(e) => e.preventDefault()}
                onClick={() => insertMath('#?x^4+#?x^3+#?x^2+#?x+#?=0', { display: true })}
                title="Chèn phương trình bậc 4: ax⁴ + bx³ + cx² + dx + e = 0"
              >
                <Sigma size={14} />
                <span>PT bậc 4</span>
              </button>

              <div style={{ position: 'relative', display: 'inline-block' }}>
                <button
                  type="button"
                  className="btn-toolbar-tool"
                  onMouseDown={(e) => e.preventDefault()}
                  onClick={() => setTableDims((d) => ({ ...d, open: !d.open }))}
                  title="Chèn bảng vào ô đang soạn thảo"
                >
                  <Table2 size={14} />
                  <span>Chèn bảng</span>
                </button>
                {tableDims.open && (
                  <div style={{ position: 'absolute', top: '110%', left: 0, zIndex: 50, background: '#fff', border: '1px solid #E2E8F0', borderRadius: 8, padding: 10, boxShadow: '0 8px 24px rgba(15,23,42,.15)', display: 'flex', gap: 8, alignItems: 'center', whiteSpace: 'nowrap', fontSize: 13 }}>
                    <label>Dòng <input type="number" min={1} max={20} value={tableDims.rows} onChange={(e) => setTableDims((d) => ({ ...d, rows: Number(e.target.value) || 1 }))} style={{ width: 48 }} /></label>
                    <label>Cột <input type="number" min={1} max={10} value={tableDims.cols} onChange={(e) => setTableDims((d) => ({ ...d, cols: Number(e.target.value) || 1 }))} style={{ width: 48 }} /></label>
                    <button type="button" className="btn-toolbar-tool" onMouseDown={(e) => e.preventDefault()} onClick={insertTable}>Chèn</button>
                  </div>
                )}
              </div>

              <button
                type="button"
                ref={helpBtnRef}
                className="btn-toolbar-tool"
                onMouseDown={(e) => e.preventDefault()}
                onClick={() => setIsHelpOpen((v) => !v)}
                title="Hướng dẫn phím tắt soạn công thức"
              >
                <HelpCircle size={14} />
                <span>Hướng dẫn</span>
              </button>
              <label className="btn-toolbar-tool" title="Cỡ chữ vùng soạn thảo">
                <span>Cỡ chữ</span>
                <select
                  value={editorFontSize}
                  onChange={(e) => setEditorFontSize(Number(e.target.value))}
                  style={{ border: 'none', background: 'transparent', font: 'inherit' }}
                >
                  {[14, 16, 18, 20, 24, 28].map((s) => (
                    <option key={s} value={s}>{s}px</option>
                  ))}
                </select>
              </label>
              <MathShortcutsHelp open={isHelpOpen} onClose={() => setIsHelpOpen(false)} anchorRef={helpBtnRef} />
            </div>
          </section>

          {/* Main Split Body: Questions List (Left) & Editor (Right) */}
          <div className="edit-modal-split-body" style={{ '--math-editor-fs': `${editorFontSize}px` }}>
            {/* LEFT COLUMN: Questions List */}
            <div className="left-questions-list-col">
              <div className="questions-list-header-bar">
                <div className="list-title-left">
                  <ListOrdered size={16} className="list-icon" />
                  <h3 className="list-main-title">
                    <span>Danh sách câu hỏi đề thi</span>
                    <span className="list-title-count">
                      {isLoadingBackend ? `(${questions.length} câu hỏi • Đang tải từ DB...)` : `(${questions.length} câu hỏi - 10.0 điểm)`}
                    </span>
                  </h3>
                </div>
                <button 
                  type="button" 
                  className="btn-add-question-header"
                  onClick={() => setIsAddQuestionModalOpen(true)}
                >
                  <Plus size={13} />
                  <span>Thêm câu hỏi</span>
                </button>
              </div>

              {/* Scrollable Questions Cards */}
              <div className="questions-cards-scroll-container">
                {questions.map((q) => {
                  const isSelected = q.id === selectedQuestionId;
                  const levelClass = getLevelBadgeClass(q.level);

                  return (
                    <div 
                      key={q.id}
                      className={`question-item-card ${isSelected ? 'is-selected' : ''}`}
                      onClick={() => handleSelectQuestion(q.id)}
                    >
                      <div className="question-card-top-row">
                        <div className="top-pills-cluster">
                          <span className="pill-qnum">Câu {q.number}</span>
                          <span className={`pill-qlevel ${levelClass}`}>{q.level}</span>
                          <span className="pill-qscore">{q.score}</span>
                        </div>

                        {isSelected ? (
                          <span className="pill-active-badge">
                            <span className="active-dot" />
                            Đang chọn
                          </span>
                        ) : (
                          <span className="pill-qtime">Thời gian: {q.suggestedTime}</span>
                        )}
                      </div>

                      <p className="question-card-snippet-text">
                        <MathRenderer text={q.previewSnippet} />
                      </p>

                      <div className="question-card-bottom-row">
                        <span className="meta-left-text">{q.formulaMeta}</span>
                        <span className="meta-right-text">{q.answersMeta}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* RIGHT COLUMN: Question Editor & Live Preview */}
            <div className="right-question-editor-col">
              {/* Top Toolbar of Right Column */}
              <div className="editor-col-top-bar">
                <div className="editor-col-title-left">
                  <FileEdit size={16} className="edit-pencil-icon" />
                  <span className="editor-q-label">Chỉnh sửa Câu {activeQuestion?.number || 1}</span>

                  {/* Level dropdown on the same line without score range */}
                  <div className="editor-level-inline-wrap" title="Chọn cấp độ tư duy">
                    <select
                      className="editor-level-select"
                      value={getSimpleLevel(currentLevel)}
                      onChange={(e) => setCurrentLevel(e.target.value)}
                    >
                      <option value="Nhận biết">Nhận biết</option>
                      <option value="Thông hiểu">Thông hiểu</option>
                      <option value="Vận dụng">Vận dụng</option>
                    </select>
                    <ChevronDown size={13} className="editor-level-chevron" />
                  </div>

                  {/* Editable red score pill: max 4 chars, '.' separator + " điểm" */}
                  <div className="editor-score-pill-container" title="Bấm để chỉnh sửa điểm số">
                    <input
                      type="text"
                      className="editor-score-input"
                      value={getRawScore(currentScore)}
                      onChange={handleScoreInputChange}
                      placeholder="2.0"
                    />
                    <span className="editor-score-unit">điểm</span>
                  </div>
                </div>

                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                  <button 
                    type="button" 
                    className="btn-delete-active-q"
                    onClick={() => handleDeleteQuestion(activeQuestion?.id)}
                    title="Xóa câu hỏi này khỏi đề thi"
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '4px',
                      padding: '5px 9px',
                      borderRadius: '6px',
                      border: '1px solid #FECACA',
                      background: '#FEF2F2',
                      color: '#DC2626',
                      fontSize: '12px',
                      fontWeight: 500,
                      cursor: 'pointer'
                    }}
                  >
                    <Trash2 size={13} />
                    <span>Xóa câu hỏi</span>
                  </button>

                  <button 
                    type="button" 
                    className="btn-save-single-question"
                    onClick={handleSaveActiveQuestion}
                  >
                    <Save size={14} />
                    <span>{saveToast ? (saveStatusText || 'Đã lưu!') : 'Lưu thay đổi câu hỏi'}</span>
                  </button>
                </div>
              </div>

              {/* LaTeX Textarea Section */}
              <div className="editor-textarea-section">
                <div className="textarea-section-header">
                  <div className="section-header-left">
                    <FileCode2 size={15} />
                    <span>Nội dung bài tập</span>
                  </div>
                  <span className="katex-support-hint">Nhấn Alt+= hoặc $ để chèn công thức</span>
                </div>

                <MathTextEditor
                  ref={(r) => { editorRefs.current.content = r; }}
                  className="question-latex-textarea"
                  value={currentContent}
                  onChange={setCurrentContent}
                  onFocus={() => setActive('content')}
                  placeholder="Nhập nội dung bài tập... (chọn công thức ở thanh ký hiệu phía trên để chèn và hiển thị trực quan)"
                  ariaLabel="Question content"
                />
              </div>

              {/* ============================================================ */}
              {/* THIẾT LẬP ĐÁP ÁN TRẮC NGHIỆM & HƯỚNG DẪN GIẢI CHI TIẾT */}
              {/* ============================================================ */}
              {(activeQuestion?.segments || []).some((sg) => sg?.type === 'table') && (
                <section className="solution-and-answers-section" data-testid="table-editor">
                  <div className="solution-section-header">
                    <h3 className="solution-header-title">Bảng số liệu</h3>
                    <span className="solution-header-hint">Chỉnh sửa bảng, xem trước bên dưới</span>
                  </div>
                  {activeQuestion.segments.map((sg, i) => sg?.type === 'table' && (
                    <div key={i} style={{ marginBottom: 12 }}>
                      <textarea
                        value={sg.content || ''}
                        onChange={(e) => updateTableSegment(i, e.target.value)}
                        rows={Math.min(12, (sg.content || '').split('\n').length + 1)}
                        aria-label="Table content"
                        style={{ width: '100%', fontFamily: 'monospace', fontSize: 13, padding: 8, border: '1px solid #DCD6E8', borderRadius: 8, boxSizing: 'border-box' }}
                      />
                      <MarkdownTable markdown={sg.content || ''} />
                      <button type="button" onClick={() => updateTableSegment(i, null)}
                        style={{ marginTop: 6, padding: '4px 10px', borderRadius: 6, border: '1px solid #FCA5A5', background: '#FEE2E2', color: '#991B1B', cursor: 'pointer', fontWeight: 600 }}>
                        Xóa bảng
                      </button>
                    </div>
                  ))}
                </section>
              )}

              <section className="solution-and-answers-section">
                <div className="solution-section-header">
                  <div className="solution-header-left">
                    <ListChecks size={18} className="solution-header-icon" />
                    <h3 className="solution-header-title">
                      Thiết lập đáp án
                    </h3>
                  </div>
                  <span className="solution-header-hint">{{ MultipleChoice: 'Chọn 1 đáp án chính xác', TrueFalse: 'Chọn Đúng/Sai cho từng mệnh đề', ShortAnswer: 'Nhập đáp án', Other: 'Danh sách các ý của câu hỏi' }[activeType]}</span>
                </div>

                <div className="question-type-selector" role="radiogroup" aria-label="Question type"
                  style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '12px' }}>
                  {QUESTION_TYPES.map((t) => (
                    <button
                      key={t.value}
                      type="button"
                      role="radio"
                      aria-checked={activeType === t.value}
                      onClick={() => handleChangeType(t.value)}
                      style={{
                        padding: '6px 12px',
                        borderRadius: '6px',
                        fontSize: '13px',
                        cursor: 'pointer',
                        border: `1px solid ${activeType === t.value ? '#2563EB' : '#CBD5E1'}`,
                        background: activeType === t.value ? '#EFF6FF' : '#FFFFFF',
                        color: activeType === t.value ? '#1D4ED8' : '#334155',
                        fontWeight: activeType === t.value ? 600 : 400
                      }}
                    >
                      {t.label}
                    </button>
                  ))}
                </div>

                {activeType === 'MultipleChoice' && (
                <div className="options-grid-row">
                  {currentOptions.map((opt) => {
                    const isCorrect = currentCorrectOption === opt.key;
                    return (
                      <div
                        key={opt.key}
                        className={`option-choice-card ${isCorrect ? 'is-selected-correct' : ''}`}
                        onClick={() => setCurrentCorrectOption(opt.key)}
                      >
                        <div className="option-choice-left">
                          <span className={`option-radio-dot ${isCorrect ? 'checked' : ''}`}>
                            {isCorrect && <span className="radio-inner-dot" />}
                          </span>
                          <span className="option-choice-letter">{opt.key}.</span>
                          <div onClick={(e) => e.stopPropagation()} style={{ flex: 1, minWidth: 0 }}>
                            <MathTextEditor
                              singleLine
                              ref={(r) => { editorRefs.current[`option:${opt.key}`] = r; }}
                              className="option-choice-input"
                              value={opt.text}
                              onChange={(v) => handleOptionTextChange(opt.key, v)}
                              onFocus={() => setActive(`option:${opt.key}`)}
                              placeholder={`Nhập đáp án ${opt.key}...`}
                              ariaLabel={`Answer option ${opt.key}`}
                            />
                          </div>
                        </div>
                        {isCorrect && (
                          <div className="option-correct-badge" title="Đáp án chính xác">
                            <Check size={12} strokeWidth={3} />
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
                )}

                {activeType === 'TrueFalse' && (
                  <div className="options-grid-row options-grid-row--single">
                    {currentOptions.map((opt) => (
                      <div key={opt.key} className={`option-choice-card ${opt.isCorrect ? 'is-selected-correct' : ''}`}>
                        <div className="option-choice-left">
                          <span className="option-choice-letter">{opt.key.toLowerCase()})</span>
                          <div style={{ flex: 1, minWidth: 0 }}>
                            <MathTextEditor
                              singleLine
                              ref={(r) => { editorRefs.current[`option:${opt.key}`] = r; }}
                              className="option-choice-input"
                              value={opt.text}
                              onChange={(v) => handleOptionTextChange(opt.key, v)}
                              onFocus={() => setActive(`option:${opt.key}`)}
                              placeholder={`Nhập mệnh đề ${opt.key.toLowerCase()})...`}
                              ariaLabel={`Statement ${opt.key.toLowerCase()}`}
                            />
                          </div>
                          <button
                            type="button"
                            onClick={() => handleToggleTf(opt.key)}
                            style={{
                              marginLeft: '8px', padding: '4px 10px', borderRadius: '6px', cursor: 'pointer',
                              border: '1px solid #CBD5E1', fontWeight: 600,
                              background: opt.isCorrect ? '#DCFCE7' : '#FEE2E2',
                              color: opt.isCorrect ? '#166534' : '#991B1B'
                            }}
                          >
                            {opt.isCorrect ? 'Đúng' : 'Sai'}
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {activeType === 'ShortAnswer' && (
                  <div className="solution-guide-box">
                    <label className="solution-guide-label">Đáp án (số hoặc biểu thức ngắn)</label>
                    <input
                      type="text"
                      className="option-choice-input"
                      value={currentCorrectOption || ''}
                      onChange={(e) => setCurrentCorrectOption(e.target.value)}
                      placeholder="Nhập đáp án đúng..."
                      aria-label="Short answer value"
                      style={{ width: '100%', padding: '8px 10px', border: '1px solid #CBD5E1', borderRadius: '6px' }}
                    />
                  </div>
                )}

                {activeType === 'Other' && (
                  <div className="options-grid-row">
                    {currentOptions.map((opt) => (
                      <div key={opt.key} className="option-choice-card">
                        <div className="option-choice-left">
                          <span className="option-choice-letter">Ý {opt.key}.</span>
                          <div style={{ flex: 1, minWidth: 0 }}>
                            <MathTextEditor
                              singleLine
                              ref={(r) => { editorRefs.current[`option:${opt.key}`] = r; }}
                              className="option-choice-input"
                              value={opt.text}
                              onChange={(v) => handleOptionTextChange(opt.key, v)}
                              onFocus={() => setActive(`option:${opt.key}`)}
                              placeholder={`Nhập ý ${opt.key}...`}
                              ariaLabel={`Sub-question ${opt.key}`}
                            />
                          </div>
                          <button
                            type="button"
                            onClick={() => handleRemoveSubQuestion(opt.key)}
                            title="Xóa ý này"
                            style={{ marginLeft: '8px', border: 'none', background: 'transparent', cursor: 'pointer', color: '#DC2626' }}
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </div>
                    ))}
                    <button
                      type="button"
                      onClick={handleAddSubQuestion}
                      style={{ padding: '6px 12px', borderRadius: '6px', border: '1px dashed #94A3B8', background: 'transparent', cursor: 'pointer' }}
                    >
                      <Plus size={14} /> Thêm ý
                    </button>
                  </div>
                )}

                <div className="solution-guide-box">
                  <label className="solution-guide-label">
                    Hướng dẫn giải (hiển thị cho học sinh sau khi nộp bài)
                  </label>
                  <MathTextEditor
                    ref={(r) => { editorRefs.current.guide = r; }}
                    className="solution-guide-textarea"
                    value={currentSolutionGuide}
                    onChange={setCurrentSolutionGuide}
                    onFocus={() => setActive('guide')}
                    placeholder="Nhập hướng dẫn giải và lời giải chi tiết..."
                    ariaLabel="Solution guide"
                  />
                </div>
              </section>

              {/* Live Preview Section */}
              <div className="editor-preview-section">
                <div className="preview-section-header">
                  <div className="section-header-left">
                    <Eye size={15} className="green-eye-icon" />
                    <span>Xem trước trực quan</span>
                  </div>
                  <span className="badge-render-exact">Render chuẩn xác</span>
                </div>

                <div className="preview-rendered-box">
                  {/* Dynamic Question Header Lead */}
                  <div className="preview-header-lead-row">
                    <span className="preview-qnum-lead">
                      Câu {activeQuestion?.number || 1} ({getSimpleLevel(currentLevel)} - {currentScore}):
                    </span>
                  </div>

                  {/* Dynamic KaTeX live rendered content */}
                  <div className="preview-dynamic-body">
                    {renderLiveContent(cleanContentForPreview(currentContent, activeQuestion?.number || 1))}
                  </div>

                  {/* Attachment preview: click to view the image inline (lightbox), no new tab */}
                  {(activeQuestion?.imageUrl || activeQuestion?.segments?.length > 0) && (
                    <QuestionMedia
                      compact
                      question={{
                        image_url: activeQuestion.imageUrl,
                        image_metadata: activeQuestion.imageMeta,
                        segments: activeQuestion.segments,
                      }}
                    />
                  )}

                  {/* Dynamic Live Options Preview */}
                  {activeType === 'Other' && currentOptions.length > 0 && (
                    <ol className="preview-options-container">
                      {currentOptions.map((opt) => (
                        <li key={opt.key}><MathRenderer text={opt.text || `(Chưa nhập ý ${opt.key})`} /></li>
                      ))}
                    </ol>
                  )}
                  {activeType === 'ShortAnswer' && (
                    <div className="preview-options-container">Đáp án: {currentCorrectOption || '(Chưa nhập)'}</div>
                  )}
                  {(activeType === 'MultipleChoice' || activeType === 'TrueFalse') && currentOptions && currentOptions.length > 0 && (
                    <div className="preview-options-container">
                      <div className="preview-options-grid">
                        {currentOptions.map((opt) => {
                          const isCorrect = activeType === 'TrueFalse' ? opt.isCorrect : currentCorrectOption === opt.key;
                          return (
                            <div 
                              key={opt.key} 
                              className={`preview-option-item ${isCorrect ? 'is-correct-preview' : ''}`}
                            >
                              <span className="preview-option-letter">{activeType === 'TrueFalse' ? `${opt.key.toLowerCase()})` : `${opt.key}.`}</span>
                              <span className="preview-option-content">
                                <MathRenderer text={opt.text || `(Chưa nhập đáp án ${opt.key})`} />
                              </span>
                              {isCorrect && (
                                <span className="preview-option-check-badge" title="Đáp án đúng">
                                  <Check size={12} strokeWidth={3} />
                                </span>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  {/* Dynamic Live Solution Guide Preview */}
                  {currentSolutionGuide && currentSolutionGuide.trim() && (
                    <div className="preview-solution-guide-box">
                      <div className="preview-solution-header">
                        <span className="preview-solution-title">💡 Hướng dẫn giải & Lời giải chi tiết:</span>
                      </div>
                      <div className="preview-solution-body">
                        {currentSolutionGuide.split('\n').map((line, sIdx) => {
                          const trimmedLine = line.trim();
                          if (!trimmedLine) return null;
                          return (
                            <p key={sIdx} className="preview-solution-line">
                              <MathRenderer text={trimmedLine} />
                            </p>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Bottom Save Action Row matching Image 1 */}
              <div className="editor-question-save-row">
                <button 
                  type="button" 
                  className="btn-save-question-block"
                  onClick={handleSaveActiveQuestion}
                >
                  <Save size={15} />
                  <span>{saveToast ? (saveStatusText || 'Đã lưu câu hỏi!') : 'Lưu thay đổi câu hỏi'}</span>
                </button>
                <span className="ctrl-s-hint">
                  <Info size={14} className="info-icon" />
                  <span>Nhấn Ctrl + S để lưu nhanh câu hỏi này</span>
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* ============================================================ */}
        {/* 5. MODAL FOOTER */}
        {/* ============================================================ */}
        <footer className="edit-modal-footer">
          {saveError && <div role="alert" style={{ color: '#e11d48', fontSize: 13 }}>{saveError}</div>}
          <div className="footer-version-info">
            <ShieldCheck size={15} />
            <span>Phiên bản v2.4 • Người cập nhật: <strong>GV. Nguyễn Văn A</strong></span>
          </div>

          <div className="footer-cta-buttons">
            <button 
              type="button" 
              className="btn-footer-cancel"
              onClick={guardedClose}
              disabled={isSaving}
            >
              Hủy bỏ
            </button>
            <button 
              type="button" 
              className="btn-footer-confirm"
              onClick={handleMainSave}
              disabled={isSaving}
            >
              {isSaving ? (
                <>
                  <Loader2 size={16} className="animate-spin" />
                  <span>Đang lưu DB...</span>
                </>
              ) : (
                <>
                  <Check size={16} />
                  <span>Xác nhận lưu thay đổi</span>
                </>
              )}
            </button>
          </div>
        </footer>

        {/* Add New Question Modal (Matching Image 2 & 3) */}
        <AddQuestionModal
          isOpen={isAddQuestionModalOpen}
          onClose={() => setIsAddQuestionModalOpen(false)}
          onSave={handleSaveFromAddModal}
          onSaveAndContinue={handleSaveAndContinueFromAddModal}
          documentTitle={docTitle}
          gradeSubject={gradeSubject}
          topicName={lessonTitle}
          questionNumber={questions.length + 1}
        />
      </div>
    </div>
  );
}
