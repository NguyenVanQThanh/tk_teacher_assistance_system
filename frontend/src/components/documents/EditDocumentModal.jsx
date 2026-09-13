// File Name: EditDocumentModal.jsx
// Description: Full-featured interactive modal dialog matching Image 1 exactly with left question list (5 questions), right selected question LaTeX editor, live KaTeX preview, Desmos SVG attachment, formula toolbar, and save synchronization.
// Created At: 2026-09-12
// Created By: Tam Khang
// Updated At: 2026-09-13
// Updated By: Tam Khang

import React, { useState, useEffect, useRef } from 'react';
import { 
  X, 
  Save, 
  FileEdit, 
  Image as ImageIcon, 
  Code, 
  Plus, 
  Eye, 
  RefreshCw, 
  Link2, 
  ChevronDown, 
  Check, 
  ShieldCheck, 
  ListOrdered,
  FileCode2,
  ListChecks,
  Info
} from 'lucide-react';
import MathRenderer from '../common/MathRenderer';
import AddQuestionModal from './AddQuestionModal';
import './EditDocumentModal.css';

export default function EditDocumentModal({ isOpen, doc, onClose, onSave }) {
  if (!isOpen || !doc) return null;

  // Header Data
  const [docTitle, setDocTitle] = useState(doc.title || 'Đề cương ôn tập Toán 12 - Học kì 1 (Nâng cao)');
  const docCode = doc.code || '#TL-TOAN12-HK1';
  const gradeSubject = doc.subject && doc.grade ? `${doc.subject} - Lớp ${doc.grade}` : 'Toán học - Lớp 12';

  // Topic Metadata
  const [lessonTitle, setLessonTitle] = useState(
    'Chuyên đề 01: Khảo sát sự biến thiên và vẽ đồ thị hàm số chứa tham số m'
  );
  const [difficultyLevel, setDifficultyLevel] = useState('Vận dụng');
  const [durationMinutes, setDurationMinutes] = useState('45');
  const [maxScore, setMaxScore] = useState('10.0 điểm');
  const [isAddQuestionModalOpen, setIsAddQuestionModalOpen] = useState(false);

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
      formulaMeta: '18 công thức LaTeX • 1 đồ thị SVG',
      answersMeta: '4 đáp án trắc nghiệm (A*)',
      attachmentName: 'Do_thi_ham_bac_ba_cau_1.svg',
      attachmentDesc: 'Đã nạp 1 hình minh họa vector tọa độ Desmos chất lượng cao (SVG)',
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
      formulaMeta: '3 công thức LaTeX',
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
      formulaMeta: '1 công thức LaTeX',
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
      formulaMeta: '8 công thức LaTeX',
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
      formulaMeta: '5 công thức LaTeX • 1 hình vẽ',
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

  // Active question being edited in right panel
  const activeQuestion = questions.find(q => q.id === selectedQuestionId) || questions[0];

  // Editor states for active question
  const [currentLevel, setCurrentLevel] = useState(activeQuestion.levelRange);
  const [currentScore, setCurrentScore] = useState(activeQuestion.score);
  const [currentContent, setCurrentContent] = useState(activeQuestion.content);
  const [currentOptions, setCurrentOptions] = useState(
    activeQuestion.options || [
      { key: 'A', text: 'm ∈ (-1; 4) \\ {0; 3}' },
      { key: 'B', text: 'm ∈ [-2; 5)' },
      { key: 'C', text: 'm ∈ (0; 3) ∪ {4}' },
      { key: 'D', text: 'm ∈ (-∞; -1) ∪ (4; +∞)' }
    ]
  );
  const [currentCorrectOption, setCurrentCorrectOption] = useState(activeQuestion.correctOption || 'A');
  const [currentSolutionGuide, setCurrentSolutionGuide] = useState(activeQuestion.solutionGuide || '');
  const [saveToast, setSaveToast] = useState(false);
  const textareaRef = useRef(null);
  const isSwitchingRef = useRef(false);

  // Select question handler with safety against race condition
  const handleSelectQuestion = (qId) => {
    isSwitchingRef.current = true;
    setSelectedQuestionId(qId);
    const targetQ = questions.find(q => q.id === qId);
    if (targetQ) {
      setCurrentLevel(targetQ.levelRange);
      setCurrentScore(targetQ.score);
      setCurrentContent(targetQ.content);
      setCurrentOptions(targetQ.options || [
        { key: 'A', text: '' },
        { key: 'B', text: '' },
        { key: 'C', text: '' },
        { key: 'D', text: '' }
      ]);
      setCurrentCorrectOption(targetQ.correctOption || null);
      setCurrentSolutionGuide(targetQ.solutionGuide || '');
    }
    setTimeout(() => {
      isSwitchingRef.current = false;
    }, 60);
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

  // Option text change handler
  const handleOptionTextChange = (key, val) => {
    setCurrentOptions(prev => prev.map(o => o.key === key ? { ...o, text: val } : o));
  };

  // Symbol Categories for Math, Physics, Chemistry & Greek like Word Equation Ribbon
  const [activeSubjectTab, setActiveSubjectTab] = useState('math');

  const symbolCategoriesBySubject = {
    math: {
      name: 'Toán học',
      icon: '📐',
      groups: [
        {
          group: 'Đại số:',
          items: [
            { label: '\\frac{a}{b}', code: '\\frac{a}{b}', display: '\\frac{a}{b}', tip: 'Phân số a/b' },
            { label: 'x^n', code: 'x^{n}', display: 'x^{n}', tip: 'Lũy thừa x^n' },
            { label: 'x_k', code: 'x_{k}', display: 'x_{k}', tip: 'Chỉ số dưới x_k' },
            { label: '\\sqrt{x}', code: '\\sqrt{x}', display: '\\sqrt{x}', tip: 'Căn bậc 2' },
            { label: '\\sqrt[n]{x}', code: '\\sqrt[n]{x}', display: '\\sqrt[n]{x}', tip: 'Căn bậc n' },
            { label: '|x|', code: '|x|', display: '|x|', tip: 'Giá trị tuyệt đối' },
            { label: '\\pm', code: '\\pm', display: '\\pm', tip: 'Cộng trừ' },
            { label: '\\times', code: '\\times', display: '\\times', tip: 'Phép nhân' },
            { label: '\\div', code: '\\div', display: '\\div', tip: 'Phép chia' },
            { label: '\\log_a b', code: '\\log_{a} b', display: '\\log_{a} b', tip: 'Logarit cơ số a của b' },
            { label: '\\ln x', code: '\\ln x', display: '\\ln x', tip: 'Logarit tự nhiên' }
          ]
        },
        {
          group: 'Giải tích:',
          items: [
            { label: '\\int_{a}^{b}', code: '\\int_{a}^{b} f(x)\\,dx', display: '\\int_{a}^{b}', tip: 'Tích phân xác định' },
            { label: '\\int', code: '\\int f(x)\\,dx', display: '\\int', tip: 'Nguyên hàm' },
            { label: '\\frac{dy}{dx}', code: '\\frac{dy}{dx}', display: '\\frac{dy}{dx}', tip: 'Đạo hàm dy/dx' },
            { label: "f'(x)", code: "f'(x)", display: "f'(x)", tip: 'Đạo hàm f(x)' },
            { label: '\\sum_{i=1}^{n}', code: '\\sum_{i=1}^{n}', display: '\\sum_{i=1}^{n}', tip: 'Tổng sigma' },
            { label: '\\lim_{x \\to x_0}', code: '\\lim_{x \\to x_0}', display: '\\lim_{x \\to x_0}', tip: 'Giới hạn lim' },
            { label: '\\infty', code: '\\infty', display: '\\infty', tip: 'Vô cực' }
          ]
        },
        {
          group: 'Hình học:',
          items: [
            { label: '\\vec{u}', code: '\\vec{u}', display: '\\vec{u}', tip: 'Véc-tơ u' },
            { label: '\\overrightarrow{AB}', code: '\\overrightarrow{AB}', display: '\\overrightarrow{AB}', tip: 'Véc-tơ AB' },
            { label: '\\widehat{ABC}', code: '\\widehat{ABC}', display: '\\widehat{ABC}', tip: 'Góc ABC' },
            { label: '\\perp', code: '\\perp', display: '\\perp', tip: 'Vuông góc' },
            { label: '\\parallel', code: '\\parallel', display: '\\parallel', tip: 'Song song' },
            { label: '\\Delta', code: '\\Delta', display: '\\Delta', tip: 'Tam giác / Delta' },
            { label: '\\angle', code: '\\angle', display: '\\angle', tip: 'Ký hiệu góc' },
            { label: '^{\\circ}', code: '^{\\circ}', display: '^{\\circ}', tip: 'Độ' }
          ]
        },
        {
          group: 'Tập hợp & Quan hệ:',
          items: [
            { label: '\\in', code: '\\in', display: '\\in', tip: 'Thuộc' },
            { label: '\\notin', code: '\\notin', display: '\\notin', tip: 'Không thuộc' },
            { label: '\\subset', code: '\\subset', display: '\\subset', tip: 'Tập con' },
            { label: '\\cup', code: '\\cup', display: '\\cup', tip: 'Hợp' },
            { label: '\\cap', code: '\\cap', display: '\\cap', tip: 'Giao' },
            { label: '\\setminus', code: '\\setminus', display: '\\setminus', tip: 'Hiệu' },
            { label: '\\emptyset', code: '\\emptyset', display: '\\emptyset', tip: 'Tập rỗng' },
            { label: '\\le', code: '\\le', display: '\\le', tip: 'Nhỏ hơn hoặc bằng' },
            { label: '\\ge', code: '\\ge', display: '\\ge', tip: 'Lớn hơn hoặc bằng' },
            { label: '\\neq', code: '\\neq', display: '\\neq', tip: 'Khác' },
            { label: '\\approx', code: '\\approx', display: '\\approx', tip: 'Xấp xỉ' },
            { label: '\\Rightarrow', code: '\\Rightarrow', display: '\\Rightarrow', tip: 'Suy ra' },
            { label: '\\Leftrightarrow', code: '\\Leftrightarrow', display: '\\Leftrightarrow', tip: 'Tương đương' }
          ]
        }
      ]
    },
    physics: {
      name: 'Vật lí',
      icon: '⚡',
      groups: [
        {
          group: 'Cơ học & Nhiệt:',
          items: [
            { label: '\\vec{F}', code: '\\vec{F}', display: '\\vec{F}', tip: 'Véc-tơ lực F' },
            { label: '\\vec{v}', code: '\\vec{v}', display: '\\vec{v}', tip: 'Véc-tơ vận tốc v' },
            { label: '\\vec{a}', code: '\\vec{a}', display: '\\vec{a}', tip: 'Véc-tơ gia tốc a' },
            { label: '\\Delta t', code: '\\Delta t', display: '\\Delta t', tip: 'Thời gian Delta t' },
            { label: '\\vec{p}', code: '\\vec{p}', display: '\\vec{p}', tip: 'Động lượng' },
            { label: 'E_d', code: 'E_d = \\frac{1}{2}mv^2', display: 'E_d', tip: 'Động năng' },
            { label: 'E_t', code: 'E_t = mgh', display: 'E_t', tip: 'Thế năng' },
            { label: 'W', code: 'W = F \\cdot s \\cdot \\cos\\alpha', display: 'W', tip: 'Công cơ học' },
            { label: '\\mu', code: '\\mu', display: '\\mu', tip: 'Hệ số ma sát' },
            { label: '\\rho', code: '\\rho', display: '\\rho', tip: 'Khối lượng riêng' },
            { label: 'T(K)', code: 'T\\text{ (K)}', display: 'T\\text{ (K)}', tip: 'Nhiệt độ Kelvin' },
            { label: '^{\\circ}C', code: '^{\\circ}\\text{C}', display: '^{\\circ}\\text{C}', tip: 'Độ C' },
            { label: 'Q', code: 'Q = mc\\Delta t', display: 'Q', tip: 'Nhiệt lượng' }
          ]
        },
        {
          group: 'Điện - Từ & Sóng:',
          items: [
            { label: '\\lambda', code: '\\lambda', display: '\\lambda', tip: 'Bước sóng lambda' },
            { label: '\\omega', code: '\\omega', display: '\\omega', tip: 'Tần số góc omega' },
            { label: '\\Omega', code: '\\Omega', display: '\\Omega', tip: 'Điện trở Ôm (Ohm)' },
            { label: '\\mu F', code: '\\mu\\text{F}', display: '\\mu\\text{F}', tip: 'Microfarad' },
            { label: 'mH', code: '\\text{mH}', display: '\\text{mH}', tip: 'Milihenry' },
            { label: '\\vec{E}', code: '\\vec{E}', display: '\\vec{E}', tip: 'Điện trường' },
            { label: '\\vec{B}', code: '\\vec{B}', display: '\\vec{B}', tip: 'Từ trường' },
            { label: '\\Phi', code: '\\Phi', display: '\\Phi', tip: 'Từ thông' },
            { label: '\\mathcal{E}', code: '\\mathcal{E}', display: '\\mathcal{E}', tip: 'Suất điện động' },
            { label: 'I=U/R', code: 'I = \\frac{U}{R}', display: 'I=\\frac{U}{R}', tip: 'Định luật Ôm' },
            { label: 'P=UI', code: 'P = U \\cdot I', display: 'P=UI', tip: 'Công suất điện' }
          ]
        },
        {
          group: 'Lượng tử & Hạt nhân:',
          items: [
            { label: 'h\\nu', code: '\\varepsilon = h\\nu', display: 'h\\nu', tip: 'Lượng tử năng lượng' },
            { label: 'E=mc^2', code: 'E = mc^2', display: 'E=mc^2', tip: 'Hệ thức Einstein' },
            { label: '_{Z}^{A}X', code: '_{Z}^{A}\\text{X}', display: '_{Z}^{A}\\text{X}', tip: 'Ký hiệu hạt nhân' },
            { label: '_{2}^{4}He', code: '_{2}^{4}\\text{He}', display: '_{2}^{4}\\text{He}', tip: 'Hạt alpha' },
            { label: '_{-1}^{0}e', code: '_{-1}^{0}\\text{e}', display: '_{-1}^{0}\\text{e}', tip: 'Hạt beta' },
            { label: '\\gamma', code: '\\gamma', display: '\\gamma', tip: 'Tia gamma' },
            { label: 'T_{1/2}', code: 'T_{1/2}', display: 'T_{1/2}', tip: 'Chu kỳ bán rã' }
          ]
        }
      ]
    },
    chemistry: {
      name: 'Hóa học',
      icon: '🧪',
      groups: [
        {
          group: 'Mũi tên & Điều kiện:',
          items: [
            { label: '\\rightarrow', code: '\\rightarrow', display: '\\rightarrow', tip: 'Phản ứng một chiều' },
            { label: '\\rightleftharpoons', code: '\\rightleftharpoons', display: '\\rightleftharpoons', tip: 'Phản ứng thuận nghịch' },
            { label: '\\uparrow', code: '\\uparrow', display: '\\uparrow', tip: 'Khí thoát ra' },
            { label: '\\downarrow', code: '\\downarrow', display: '\\downarrow', tip: 'Kết tủa' },
            { label: '\\xrightarrow{t^{\\circ}}', code: '\\xrightarrow{t^{\\circ}}', display: '\\xrightarrow{t^{\\circ}}', tip: 'Nhiệt độ' },
            { label: '\\xrightarrow{\\text{xt}}', code: '\\xrightarrow{\\text{xt}}', display: '\\xrightarrow{\\text{xt}}', tip: 'Chất xúc tác' },
            { label: '\\xrightarrow{\\text{xt, } t^{\\circ}}', code: '\\xrightarrow{\\text{xt, } t^{\\circ}}', display: '\\xrightarrow{\\text{xt, } t^{\\circ}}', tip: 'Xúc tác & nhiệt độ' }
          ]
        },
        {
          group: 'Ion & Chất phổ biến:',
          items: [
            { label: 'H_2O', code: '\\text{H}_2\\text{O}', display: '\\text{H}_2\\text{O}', tip: 'Nước' },
            { label: 'CO_2', code: '\\text{CO}_2', display: '\\text{CO}_2', tip: 'Khí carbonic' },
            { label: 'H^+', code: '\\text{H}^+', display: '\\text{H}^+', tip: 'Ion H+' },
            { label: 'OH^-', code: '\\text{OH}^-', display: '\\text{OH}^-', tip: 'Ion OH-' },
            { label: 'SO_4^{2-}', code: '\\text{SO}_4^{2-}', display: '\\text{SO}_4^{2-}', tip: 'Ion sunfat' },
            { label: 'CO_3^{2-}', code: '\\text{CO}_3^{2-}', display: '\\text{CO}_3^{2-}', tip: 'Ion cacbonat' },
            { label: 'NO_3^-', code: '\\text{NO}_3^-', display: '\\text{NO}_3^-', tip: 'Ion nitrat' },
            { label: 'Cl^-', code: '\\text{Cl}^-', display: '\\text{Cl}^-', tip: 'Ion clorua' },
            { label: 'Ca^{2+}', code: '\\text{Ca}^{2+}', display: '\\text{Ca}^{2+}', tip: 'Ion Canxi' },
            { label: 'Fe^{3+}', code: '\\text{Fe}^{3+}', display: '\\text{Fe}^{3+}', tip: 'Ion Sắt III' },
            { label: 'Al^{3+}', code: '\\text{Al}^{3+}', display: '\\text{Al}^{3+}', tip: 'Ion Nhôm' }
          ]
        },
        {
          group: 'Liên kết & Hữu cơ:',
          items: [
            { label: '-', code: '-', display: '-', tip: 'Liên kết đơn' },
            { label: '=', code: '=', display: '=', tip: 'Liên kết đôi' },
            { label: '\\equiv', code: '\\equiv', display: '\\equiv', tip: 'Liên kết ba' },
            { label: 'R-COOH', code: '\\text{R-COOH}', display: '\\text{R-COOH}', tip: 'Axit cacboxylic' },
            { label: 'R-OH', code: '\\text{R-OH}', display: '\\text{R-OH}', tip: 'Ancol' },
            { label: 'R-NH_2', code: '\\text{R-NH}_2', display: '\\text{R-NH}_2', tip: 'Amin' },
            { label: '_{6}^{12}C', code: '_{6}^{12}\\text{C}', display: '_{6}^{12}\\text{C}', tip: 'Đồng vị cacbon 12' },
            { label: '\\Delta H < 0', code: '\\Delta H < 0', display: '\\Delta H < 0', tip: 'Phản ứng tỏa nhiệt' },
            { label: '\\Delta H > 0', code: '\\Delta H > 0', display: '\\Delta H > 0', tip: 'Phản ứng thu nhiệt' }
          ]
        }
      ]
    },
    greek: {
      name: 'Ký tự Hy Lạp',
      icon: 'Ω',
      groups: [
        {
          group: 'Chữ thường:',
          items: [
            { label: '\\alpha', code: '\\alpha', display: '\\alpha', tip: 'alpha' },
            { label: '\\beta', code: '\\beta', display: '\\beta', tip: 'beta' },
            { label: '\\gamma', code: '\\gamma', display: '\\gamma', tip: 'gamma' },
            { label: '\\delta', code: '\\delta', display: '\\delta', tip: 'delta' },
            { label: '\\epsilon', code: '\\epsilon', display: '\\epsilon', tip: 'epsilon' },
            { label: '\\theta', code: '\\theta', display: '\\theta', tip: 'theta' },
            { label: '\\lambda', code: '\\lambda', display: '\\lambda', tip: 'lambda' },
            { label: '\\mu', code: '\\mu', display: '\\mu', tip: 'mu' },
            { label: '\\pi', code: '\\pi', display: '\\pi', tip: 'pi' },
            { label: '\\rho', code: '\\rho', display: '\\rho', tip: 'rho' },
            { label: '\\sigma', code: '\\sigma', display: '\\sigma', tip: 'sigma' },
            { label: '\\tau', code: '\\tau', display: '\\tau', tip: 'tau' },
            { label: '\\phi', code: '\\phi', display: '\\phi', tip: 'phi' },
            { label: '\\omega', code: '\\omega', display: '\\omega', tip: 'omega' }
          ]
        },
        {
          group: 'Chữ hoa:',
          items: [
            { label: '\\Delta', code: '\\Delta', display: '\\Delta', tip: 'Delta hoa' },
            { label: '\\Gamma', code: '\\Gamma', display: '\\Gamma', tip: 'Gamma hoa' },
            { label: '\\Theta', code: '\\Theta', display: '\\Theta', tip: 'Theta hoa' },
            { label: '\\Lambda', code: '\\Lambda', display: '\\Lambda', tip: 'Lambda hoa' },
            { label: '\\Sigma', code: '\\Sigma', display: '\\Sigma', tip: 'Sigma hoa' },
            { label: '\\Phi', code: '\\Phi', display: '\\Phi', tip: 'Phi hoa' },
            { label: '\\Omega', code: '\\Omega', display: '\\Omega', tip: 'Omega hoa' }
          ]
        }
      ]
    }
  };

  const currentSubjectData = symbolCategoriesBySubject[activeSubjectTab] || symbolCategoriesBySubject.math;

  // Insert LaTeX snippet at textarea cursor position and update preview (inserts raw snippet as-is)
  const insertSnippet = (snippet, tipName) => {
    const textarea = textareaRef.current;
    if (!textarea) {
      setCurrentContent(prev => prev + ' ' + snippet);
      setLastInserted({ code: snippet, name: tipName || snippet });
      return;
    }

    const start = textarea.selectionStart ?? currentContent.length;
    const end = textarea.selectionEnd ?? currentContent.length;
    const currentText = currentContent;

    // Directly insert the snippet as-is without automatically wrapping with $ or $$
    const textToInsert = snippet;

    const newText = currentText.substring(0, start) + textToInsert + currentText.substring(end);
    setCurrentContent(newText);

    setTimeout(() => {
      textarea.focus();
      const newCursorPos = start + textToInsert.length;
      textarea.setSelectionRange(newCursorPos, newCursorPos);
    }, 50);
  };

  // Save changes to current question in list
  const handleSaveActiveQuestion = () => {
    setQuestions(prev => prev.map(q => {
      if (q.id === activeQuestion.id) {
        return {
          ...q,
          levelRange: currentLevel,
          level: currentLevel.split(' ')[0],
          score: currentScore,
          content: currentContent,
          options: currentOptions,
          correctOption: currentCorrectOption,
          solutionGuide: currentSolutionGuide,
          answersMeta: currentCorrectOption 
            ? `4 đáp án (${currentCorrectOption}*)` 
            : '4 đáp án (Chưa chọn)',
          previewSnippet: currentContent.split('\n')[1] || currentContent.slice(0, 80)
        };
      }
      return q;
    }));
    setSaveToast(true);
    setTimeout(() => setSaveToast(false), 2000);
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
  const handleAddNewQuestion = () => {
    const newId = Date.now();
    const newNum = questions.length + 1;
    const newQ = {
      id: newId,
      number: newNum,
      level: 'Vận dụng',
      levelRange: 'Vận dụng (7.0 - 10.0)',
      score: '2.0 điểm',
      suggestedTime: '10 phút',
      previewSnippet: `Câu ${newNum}: Nhập nội dung câu hỏi mới...`,
      formulaMeta: '0 công thức LaTeX',
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
    setQuestions([...questions, newQ]);
    handleSelectQuestion(newId);
  };

  const handleSaveFromAddModal = (newQuestionData) => {
    setQuestions((prev) => [...prev, newQuestionData]);
    setSelectedQuestionId(newQuestionData.id);
    setActiveQuestion(newQuestionData);
    setCurrentLevel(newQuestionData.levelRange || newQuestionData.level);
    setCurrentScore(newQuestionData.score);
    setCurrentTime(newQuestionData.suggestedTime);
    setCurrentContent(newQuestionData.content);
    setCurrentOptions(newQuestionData.options || []);
    setCurrentCorrectOption(newQuestionData.correctOption || null);
    setCurrentSolutionGuide(newQuestionData.solutionGuide || '');
  };

  const handleSaveAndContinueFromAddModal = (newQuestionData) => {
    setQuestions((prev) => [...prev, newQuestionData]);
  };

  // Main Save Handler
  const handleMainSave = () => {
    handleSaveActiveQuestion();
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
    if (onSave) {
      onSave(updated);
    }
    onClose();
  };

  // Helper to get Level Badge styling class
  const getLevelBadgeClass = (level) => {
    if (level?.includes('Nhận biết')) return 'badge-level-know';
    if (level?.includes('Thông hiểu')) return 'badge-level-comp';
    return 'badge-level-app';
  };

  return (
    <div className="edit-modal-backdrop" onClick={onClose}>
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
              onClick={onClose}
            >
              <X size={15} />
              <span>Đóng</span>
            </button>
            <button 
              type="button" 
              className="btn-header-save"
              onClick={handleMainSave}
            >
              <Save size={16} />
              <span>Lưu & Cập nhật</span>
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

              {/* Mức độ tư duy và thời gian làm bài chung khung bảng ký hiệu (Hình 2 style) */}
              <div className="formula-top-meta-cluster">
                {/* Mức độ tư duy */}
                <div className="toolbar-level-pill-wrap" title="Mức độ tư duy đề thi">
                  <select
                    className="toolbar-level-select"
                    value={getSimpleLevel(difficultyLevel)}
                    onChange={(e) => setDifficultyLevel(e.target.value)}
                  >
                    <option value="Nhận biết">Nhận biết</option>
                    <option value="Thông hiểu">Thông hiểu</option>
                    <option value="Vận dụng">Vận dụng</option>
                  </select>
                  <ChevronDown size={13} className="toolbar-level-chevron" />
                </div>

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
                        onClick={() => insertSnippet(item.code, item.tip)}
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
            <div className="toolbar-bottom-actions">
              <button 
                type="button" 
                className="btn-toolbar-tool"
                onClick={() => insertSnippet('\n![Minh họa đồ thị](Do_thi_ham_bac_ba_cau_1.svg)\n', 'Hình vẽ SVG')}
              >
                <ImageIcon size={14} />
                <span>Chèn hình vẽ</span>
              </button>

              <button 
                type="button" 
                className="btn-toolbar-tool"
                onClick={() => insertSnippet('$$\n\\int_{a}^{b} f(x)\\,dx\n$$', 'Khối LaTeX')}
              >
                <Code size={14} />
                <span>Chèn khối LaTeX</span>
              </button>

              <button 
                type="button" 
                className="btn-toolbar-tool"
                onClick={() => insertSnippet('$$\n\\begin{cases}\nax + by = c \\\\\na\'x + b\'y = c\'\n\\end{cases}\n$$', 'Hệ phương trình')}
              >
                <span>Chèn hệ phương trình</span>
              </button>

              <button 
                type="button" 
                className="btn-toolbar-tool"
                onClick={() => insertSnippet('$$\n\\begin{pmatrix}\na & b \\\\\nc & d\n\\end{pmatrix}\n$$', 'Ma trận')}
              >
                <span>Chèn ma trận</span>
              </button>
            </div>
          </section>

          {/* Main Split Body: Questions List (Left) & Editor (Right) */}
          <div className="edit-modal-split-body">
            {/* LEFT COLUMN: Questions List */}
            <div className="left-questions-list-col">
              <div className="questions-list-header-bar">
                <div className="list-title-left">
                  <ListOrdered size={16} className="list-icon" />
                  <h3 className="list-main-title">
                    <span>Danh sách câu hỏi đề thi</span>
                    <span className="list-title-count">({questions.length} câu hỏi - 10.0 điểm)</span>
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
                  <span className="editor-q-label">Chỉnh sửa Câu {activeQuestion.number}</span>

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

                <button 
                  type="button" 
                  className="btn-save-single-question"
                  onClick={handleSaveActiveQuestion}
                >
                  <Save size={14} />
                  <span>{saveToast ? 'Đã lưu!' : 'Lưu thay đổi câu hỏi'}</span>
                </button>
              </div>

              {/* LaTeX Textarea Section */}
              <div className="editor-textarea-section">
                <div className="textarea-section-header">
                  <div className="section-header-left">
                    <FileCode2 size={15} />
                    <span>Nội dung câu hỏi & Mã LaTeX</span>
                  </div>
                  <span className="katex-support-hint">Hỗ trợ KaTeX & Markdown</span>
                </div>

                <textarea 
                  ref={textareaRef}
                  className="question-latex-textarea"
                  rows={7}
                  value={currentContent}
                  onChange={(e) => setCurrentContent(e.target.value)}
                  spellCheck={false}
                />
              </div>

              {/* ============================================================ */}
              {/* THIẾT LẬP ĐÁP ÁN TRẮC NGHIỆM & HƯỚNG DẪN GIẢI CHI TIẾT */}
              {/* ============================================================ */}
              <section className="solution-and-answers-section">
                <div className="solution-section-header">
                  <div className="solution-header-left">
                    <ListChecks size={18} className="solution-header-icon" />
                    <h3 className="solution-header-title">
                      Thiết lập đáp án
                    </h3>
                  </div>
                  <span className="solution-header-hint">Chọn 1 đáp án chính xác</span>
                </div>

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
                          <input
                            type="text"
                            className="option-choice-input"
                            value={opt.text}
                            onChange={(e) => handleOptionTextChange(opt.key, e.target.value)}
                            placeholder={`Nhập đáp án ${opt.key}...`}
                            onClick={(e) => e.stopPropagation()}
                          />
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

                <div className="solution-guide-box">
                  <label className="solution-guide-label">
                    Hướng dẫn giải (hiển thị cho học sinh sau khi nộp bài)
                  </label>
                  <textarea 
                    className="solution-guide-textarea"
                    value={currentSolutionGuide}
                    onChange={(e) => setCurrentSolutionGuide(e.target.value)}
                    rows={3}
                    placeholder="Nhập hướng dẫn giải và lời giải chi tiết..."
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
                      Câu {activeQuestion.number} ({getSimpleLevel(currentLevel)} - {currentScore}):
                    </span>
                  </div>

                  {/* Dynamic KaTeX live rendered content */}
                  <div className="preview-dynamic-body">
                    {renderLiveContent(cleanContentForPreview(currentContent, activeQuestion.number))}
                  </div>

                  {/* SVG Attachment Banner */}
                  {activeQuestion.attachmentName && (
                    <div className="preview-svg-attachment-banner">
                      <div className="attachment-left-info">
                        <Link2 size={16} className="attachment-link-icon" />
                        <span className="attachment-file-text">{activeQuestion.attachmentName}</span>
                      </div>
                      <button type="button" className="btn-view-image-link">
                        <span>Xem ảnh</span>
                      </button>
                    </div>
                  )}

                  {/* Dynamic Live Options Preview */}
                  {currentOptions && currentOptions.length > 0 && (
                    <div className="preview-options-container">
                      <div className="preview-options-grid">
                        {currentOptions.map((opt) => {
                          const isCorrect = currentCorrectOption === opt.key;
                          return (
                            <div 
                              key={opt.key} 
                              className={`preview-option-item ${isCorrect ? 'is-correct-preview' : ''}`}
                            >
                              <span className="preview-option-letter">{opt.key}.</span>
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
                  <span>{saveToast ? 'Đã lưu câu hỏi!' : 'Lưu thay đổi câu hỏi'}</span>
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
          <div className="footer-version-info">
            <ShieldCheck size={15} />
            <span>Phiên bản v2.4 • Người cập nhật: <strong>GV. Nguyễn Văn A</strong></span>
          </div>

          <div className="footer-cta-buttons">
            <button 
              type="button" 
              className="btn-footer-cancel"
              onClick={onClose}
            >
              Hủy bỏ
            </button>
            <button 
              type="button" 
              className="btn-footer-confirm"
              onClick={handleMainSave}
            >
              <Check size={16} />
              <span>Xác nhận lưu thay đổi</span>
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
