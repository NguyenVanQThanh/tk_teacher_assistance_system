// File Name: StudentExercisesPage.jsx
// Description: Student exercise repository page with filter bar, exercise cards, exam/exercise categorization, status tracking, and interactive AI-powered exercise generator modal.
// Created At: 2026-09-07
// Created By: Tam Khang
// Updated At: 2026-09-13
// Updated By: Tam Khang

import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  HelpCircle, 
  Mic, 
  BookOpen, 
  FileText, 
  ListFilter, 
  Clock, 
  Calendar, 
  ListChecks, 
  ChevronLeft, 
  ChevronRight,
  Lock,
  Award,
  Sparkles,
  Bot,
  Wand2,
  X,
  Plus,
  Minus,
  CheckCircle2,
  Layers,
  BrainCircuit,
  MessageSquare,
  Flame,
  SendHorizontal,
  Sliders,
  Check,
  Zap,
  ArrowRight,
  RotateCcw
} from 'lucide-react';
import './StudentExercisesPage.css';

export default function StudentExercisesPage() {
  const navigate = useNavigate();
  const [selectedSubject, setSelectedSubject] = useState('all');
  const [selectedType, setSelectedType] = useState('all');
  const [selectedExerciseDetail, setSelectedExerciseDetail] = useState(null);
  const [selectedAttemptId, setSelectedAttemptId] = useState(2); // Default to attempt 2 (highest result)
  const [currentPage, setCurrentPage] = useState(1);

  // Dynamic Attempts dataset reflecting each completion with detailed analytics
  const attemptsData = useMemo(() => [
    {
      id: 1,
      attemptNum: 1,
      badgeLabel: 'Lần 1',
      dateText: '14/10/2023 – 19:30',
      statusTag: 'Đã hoàn thành',
      statusTagClass: 'attempt-status-tag',
      score: '7.2',
      scoreLabel: 'KẾT QUẢ (LẦN 1)',
      grade: 'Khá',
      correctCount: 29,
      totalCount: 40,
      correctPct: '72.5%',
      timeSpent: '42 phút',
      cognitive: {
        recognition: { correct: 9, total: 10, pct: '90%' },
        understanding: { correct: 13, total: 16, pct: '81.3%' },
        application: { correct: 7, total: 14, pct: '50%' }
      }
    },
    {
      id: 2,
      attemptNum: 2,
      badgeLabel: 'Lần 2 (Mới nhất)',
      isLatest: true,
      isBest: true,
      dateText: '15/10/2023 – 14:20',
      statusTag: 'Đã chấm điểm',
      statusTagClass: 'attempt-status-tag-outline-green',
      score: '8.5',
      scoreLabel: 'KẾT QUẢ CAO NHẤT (LẦN 2)',
      grade: 'Giỏi',
      correctCount: 34,
      totalCount: 40,
      correctPct: '85%',
      timeSpent: '38 phút 15 giây',
      cognitive: {
        recognition: { correct: 10, total: 10, pct: '100%' },
        understanding: { correct: 15, total: 16, pct: '93.8%' },
        application: { correct: 9, total: 14, pct: '64.3%' }
      }
    }
  ], []);

  const currentAttempt = useMemo(() => {
    return attemptsData.find(a => a.id === selectedAttemptId) || attemptsData[1];
  }, [attemptsData, selectedAttemptId]);
  const defaultSeeds = [
    {
      id: 1,
      type: 'quiz',
      category: 'exam', // Bài thi - no retake allowed
      categoryLabel: 'Bài thi',
      icon: Award,
      title: 'Đề thi khảo sát Toán 12 – Kỳ I',
      teacher: 'Trần Văn B',
      subject: 'Toán học',
      questionsCount: '40 câu hỏi',
      duration: '50 phút',
      deadline: '23:59, Hnay',
      isToday: true,
      status: 'uncompleted',
      statusLabel: 'Chưa làm'
    },
    {
      id: 2,
      type: 'speaking',
      category: 'class_exercise', // Bài tập trên lớp - retake allowed
      categoryLabel: 'Bài tập trên lớp',
      icon: Mic,
      title: 'Tiếng Anh – Luyện nói Unit 3',
      teacher: 'Anna Smith',
      subject: 'Tiếng Anh',
      questionsCount: 'Ghi âm',
      duration: '15 phút',
      deadline: '15/10/2023',
      isToday: false,
      status: 'uncompleted',
      statusLabel: 'Chưa làm'
    },
    {
      id: 3,
      type: 'quiz',
      category: 'exam', // Bài thi - no retake allowed
      categoryLabel: 'Bài thi',
      icon: HelpCircle,
      title: 'Đề thi thử: Vật lý 12 – Dao động cơ',
      teacher: 'Nguyễn Văn An',
      subject: 'Vật lý',
      questionsCount: '30 câu hỏi',
      duration: '40 phút',
      deadline: '18/10/2023',
      isToday: false,
      status: 'uncompleted',
      statusLabel: 'Chưa làm'
    },
    {
      id: 4,
      type: 'essay',
      category: 'class_exercise', // Bài tập trên lớp - retake allowed
      categoryLabel: 'Bài tập trên lớp',
      icon: FileText,
      title: 'Hóa học 12 – Chuyên đề Este & Lipit',
      teacher: 'Trần Thị Mai',
      subject: 'Hóa học',
      questionsCount: '35 câu hỏi',
      duration: '50 phút',
      deadline: '20/10/2023',
      isToday: false,
      status: 'uncompleted',
      statusLabel: 'Chưa làm'
    }
  ];

  // Safe icon helper that always returns a valid Lucide component even after JSON parsing
  const getAssignmentIcon = (item) => {
    if (item.category === 'ai_generated' || item.isAiGenerated || item.type === 'ai_generated') return Sparkles;
    if (item.type === 'speaking') return Mic;
    if (item.type === 'quiz') {
      return item.category === 'exam' ? Award : HelpCircle;
    }
    return FileText;
  };

  // Initialize assignments list combining saved AI exercises from localStorage + defaults
  const [assignmentsList, setAssignmentsList] = useState(() => {
    try {
      const saved = localStorage.getItem('tk_student_ai_exercises');
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length > 0) {
          return [...parsed, ...defaultSeeds];
        }
      }
    } catch (e) {
      console.error(e);
    }
    return defaultSeeds;
  });

  // AI Generator Modal States
  const [isAiModalOpen, setIsAiModalOpen] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationStep, setGenerationStep] = useState(0);
  const [generatedExerciseId, setGeneratedExerciseId] = useState(null);

  // Form Configuration for AI Exercise
  const [aiSubject, setAiSubject] = useState('Hóa học');
  const [aiGrade, setAiGrade] = useState('Lớp 12');
  const [aiDuration, setAiDuration] = useState(45);
  const [aiTopicPrompt, setAiTopicPrompt] = useState('Este và Lipit – Phản ứng xà phòng hóa, este hóa và chất béo triolein');

  // Question counts by Part & Difficulty Levels (Nhận biết, Thông hiểu, Vận dụng)
  const [part1Levels, setPart1Levels] = useState({ know: 6, comp: 5, app: 4 }); // Part I: MC 4 options
  const [part2Levels, setPart2Levels] = useState({ know: 1, comp: 2, app: 1 }); // Part II: True/False
  const [part3Levels, setPart3Levels] = useState({ know: 0, comp: 2, app: 4 }); // Part III: Short Answer

  // Calculations
  const part1Total = part1Levels.know + part1Levels.comp + part1Levels.app;
  const part2Total = part2Levels.know + part2Levels.comp + part2Levels.app;
  const part3Total = part3Levels.know + part3Levels.comp + part3Levels.app;
  const totalAiQuestions = part1Total + part2Total + part3Total;

  const totalKnow = part1Levels.know + part2Levels.know + part3Levels.know;
  const totalComp = part1Levels.comp + part2Levels.comp + part3Levels.comp;
  const totalApp = part1Levels.app + part2Levels.app + part3Levels.app;

  // Quick Topic Suggestions
  const topicSuggestions = [
    { label: 'Este & Lipit (Hóa 12)', subject: 'Hóa học', prompt: 'Chuyên đề Este & Lipit: Phản ứng este hóa, xà phòng hóa, tính chất triolein và bài toán đốt cháy' },
    { label: 'Hàm số & Khảo sát (Toán 12)', subject: 'Toán học', prompt: 'Khảo sát sự biến thiên và vẽ đồ thị hàm số, cực trị, tiệm cận, bài toán thực tế tối ưu' },
    { label: 'Dao động điều hòa (Vật lý 12)', subject: 'Vật lý', prompt: 'Dao động cơ: Con lắc lò xo, con lắc đơn, năng lượng dao động điều hòa và đồ thị li độ' },
    { label: 'Di truyền học (Sinh học 12)', subject: 'Sinh học', prompt: 'Di truyền liên kết, hoán vị gen, quy luật Menđen và cấu trúc di truyền quần thể' },
    { label: 'Grammar: Cleft Sentences (Tiếng Anh)', subject: 'Tiếng Anh', prompt: 'Advanced English Grammar: Cleft Sentences, Inversion, and Conditional Sentences' }
  ];

  // Increment / Decrement handlers for difficulty counts
  const handleLevelChange = (setter, key, delta) => {
    setter(prev => ({
      ...prev,
      [key]: Math.max(0, prev[key] + delta)
    }));
  };

  // Submit AI Generation Handler
  const handleGenerateAiExercise = () => {
    if (totalAiQuestions === 0) {
      alert('Vui lòng chọn số lượng câu hỏi lớn hơn 0.');
      return;
    }

    setIsGenerating(true);
    setGenerationStep(1);

    setTimeout(() => {
      setGenerationStep(2);
    }, 850);

    setTimeout(() => {
      setGenerationStep(3);
    }, 1750);

    setTimeout(() => {
      const newId = Date.now();
      const newExercise = {
        id: newId,
        type: 'ai_generated',
        category: 'exercise',
        categoryLabel: 'Bài tập tạo sinh AI',
        icon: Sparkles,
        title: `${aiSubject} ${aiGrade.replace('Lớp ', '')} – ${aiTopicPrompt.slice(0, 48)}${aiTopicPrompt.length > 48 ? '...' : ''}`,
        teacher: 'Trợ lý AI Tam Khang',
        subject: aiSubject,
        grade: aiGrade,
        topicPrompt: aiTopicPrompt,
        questionsCount: `${totalAiQuestions} câu hỏi`,
        totalQuestions: totalAiQuestions,
        part1Count: part1Total,
        part2Count: part2Total,
        part3Count: part3Total,
        durationMinutes: aiDuration,
        duration: `${aiDuration} phút`,
        deadline: 'Tự do rèn luyện',
        isToday: true,
        status: 'uncompleted',
        statusLabel: 'Chưa làm',
        isAiGenerated: true,
        createdAt: new Date().toISOString(),
        matrix: {
          part1: part1Total,
          part2: part2Total,
          part3: part3Total,
          know: totalKnow,
          comp: totalComp,
          app: totalApp
        }
      };

      // Persist permanently in localStorage
      try {
        const currentSaved = JSON.parse(localStorage.getItem('tk_student_ai_exercises') || '[]');
        localStorage.setItem('tk_student_ai_exercises', JSON.stringify([newExercise, ...currentSaved]));
      } catch (e) {
        console.error('Error saving AI exercise to localStorage:', e);
      }

      setAssignmentsList(prev => [newExercise, ...prev]);
      setGeneratedExerciseId(newId);
      setIsGenerating(false);
      setGenerationStep(4); // Completed stage
    }, 2500);
  };

  const handleCloseAiModal = () => {
    setIsAiModalOpen(false);
    setIsGenerating(false);
    setGenerationStep(0);
    setGeneratedExerciseId(null);
  };

  const filteredAssignments = assignmentsList.filter(item => {
    if (selectedSubject !== 'all' && item.subject !== selectedSubject) return false;
    if (selectedType !== 'all' && item.category !== selectedType) return false;
    return true;
  });

  const handleStartExercise = (item) => {
    navigate(`/student/exercises/${item.id}/taking`);
  };

  const handleCardClick = (item) => {
    setSelectedExerciseDetail(item);
    setSelectedAttemptId(2);
  };

  return (
    <div className="student-exercises-container">
      {/* Page Header with Action Button */}
      <div className="exercises-page-header-row">
        <div className="exercises-page-header-left">
          <h1 className="exercises-main-title">Kho bài tập & Đề thi</h1>
          <p className="exercises-main-subtitle">
            Khám phá và hoàn thành các bài tập, đề thi từ giáo viên hoặc tự tạo bài tập rèn luyện thông minh với AI.
          </p>
        </div>

        <button 
          type="button" 
          className="btn-open-ai-generator"
          onClick={() => setIsAiModalOpen(true)}
        >
          <div className="ai-btn-glow-ring" />
          <Sparkles size={18} className="ai-btn-sparkle-icon" />
          <span>Tạo bài tập tạo sinh AI</span>
          <div className="ai-btn-badge">AI 2.0</div>
        </button>
      </div>

      {/* Filter Card */}
      <div className="exercises-filter-card">
        <div className="filter-field-group">
          <label className="filter-field-label">Môn học</label>
          <select 
            className="filter-select-input"
            value={selectedSubject}
            onChange={(e) => setSelectedSubject(e.target.value)}
          >
            <option value="all">Tất cả môn học</option>
            <option value="Toán học">Toán học</option>
            <option value="Hóa học">Hóa học</option>
            <option value="Vật lý">Vật lý</option>
            <option value="Tiếng Anh">Tiếng Anh</option>
            <option value="Sinh học">Sinh học</option>
            <option value="Ngữ văn">Ngữ văn</option>
          </select>
        </div>

        <div className="filter-field-group">
          <label className="filter-field-label">Loại bài tập / Đề thi</label>
          <select 
            className="filter-select-input"
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
          >
            <option value="all">Tất cả thể loại</option>
            <option value="exam">Bài thi</option>
            <option value="class_exercise">Bài tập trên lớp</option>
            <option value="ai_generated">Bài tập tạo sinh AI</option>
          </select>
        </div>

        <button type="button" className="btn-filter-submit">
          <ListFilter size={16} />
          <span>Lọc kết quả</span>
        </button>
      </div>

      {/* Exercises Cards Grid */}
      <div className="exercises-cards-grid">
        {filteredAssignments.map(item => {
          const Icon = getAssignmentIcon(item);
          const savedData = localStorage.getItem(`tk_exam_submitted_${item.id}`);
          const isSubmitted = Boolean(savedData);
          const isExam = item.category === 'exam';
          const displayCategoryLabel = item.category === 'exam' 
            ? 'Bài thi' 
            : item.category === 'ai_generated' 
              ? 'Bài tập tạo sinh AI' 
              : 'Bài tập trên lớp';

          const currentStatus = isSubmitted ? 'completed' : item.status;
          const currentStatusLabel = isSubmitted ? 'Đã nộp bài' : item.statusLabel;

          return (
            <div 
              key={item.id} 
              className={`student-assignment-card clickable-card ${isExam ? 'is-exam-card' : ''} ${item.isAiGenerated ? 'is-ai-card' : ''}`}
              onClick={() => handleCardClick(item)}
            >
              <div className="card-top-row">
                <div className="card-type-left">
                  <div className={`card-type-icon-box ${isExam ? 'exam-icon-accent' : ''} ${item.isAiGenerated ? 'ai-icon-accent' : ''}`}>
                    <Icon size={18} strokeWidth={2.2} />
                  </div>
                  <span className={`card-category-tag ${item.category === 'exam' ? 'tag-exam' : item.category === 'ai_generated' ? 'tag-ai' : 'tag-class'}`}>
                    {displayCategoryLabel}
                  </span>
                </div>
                <span className={`card-status-pill ${currentStatus}`}>
                  {currentStatusLabel}
                </span>
              </div>

              <div className="card-body-content">
                <h3 className="card-assignment-title">{item.title}</h3>
                <p className="card-teacher-name">Giáo viên: {item.teacher}</p>

                <div className="card-meta-chips-row">
                  <span className="meta-chip-item">
                    <ListChecks size={13} />
                    {item.questionsCount}
                  </span>
                  <span className="meta-chip-item">
                    <Clock size={13} />
                    {item.duration}
                  </span>
                </div>
              </div>

              <div className="card-bottom-footer" onClick={(e) => e.stopPropagation()}>
                <span className={`card-due-text ${item.isToday ? 'is-today' : ''}`}>
                  <Calendar size={13} />
                  Hạn chót: {item.deadline}
                </span>

                {isExam && isSubmitted ? (
                  <div className="card-exam-locked-action">
                    <button 
                      type="button" 
                      className="btn-card-action"
                      onClick={() => setSelectedExerciseDetail(item)}
                    >
                      Xem kết quả
                    </button>
                    <span className="exam-no-retake-badge">
                      <Lock size={11} />
                      <span>Không thể làm lại</span>
                    </span>
                  </div>
                ) : isSubmitted ? (
                  <button 
                    type="button" 
                    className="btn-card-action"
                    onClick={() => setSelectedExerciseDetail(item)}
                  >
                    Luyện tập lại
                  </button>
                ) : (
                  <button 
                    type="button" 
                    className="btn-card-action"
                    onClick={() => handleStartExercise(item)}
                  >
                    {isExam ? 'Làm bài thi' : 'Bắt đầu'}
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Pagination Footer */}
      <div className="exercises-pagination-footer">
        <span>Hiển thị 1 đến {filteredAssignments.length} trong số {assignmentsList.length} bài tập</span>
        <div className="pagination-controls">
          <button 
            type="button" 
            className="page-nav-btn" 
            aria-label="Previous page"
            onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
          >
            <ChevronLeft size={16} />
          </button>
          <button 
            type="button" 
            className={`page-nav-btn ${currentPage === 1 ? 'active' : ''}`}
            onClick={() => setCurrentPage(1)}
          >
            1
          </button>
          <button 
            type="button" 
            className={`page-nav-btn ${currentPage === 2 ? 'active' : ''}`}
            onClick={() => setCurrentPage(2)}
          >
            2
          </button>
          <button 
            type="button" 
            className={`page-nav-btn ${currentPage === 3 ? 'active' : ''}`}
            onClick={() => setCurrentPage(3)}
          >
            3
          </button>
          <button 
            type="button" 
            className="page-nav-btn" 
            aria-label="Next page"
            onClick={() => setCurrentPage(prev => prev + 1)}
          >
            <ChevronRight size={16} />
          </button>
        </div>
      </div>

      {/* ============================================================ */}
      {/* AI EXERCISE GENERATION MODAL */}
      {/* ============================================================ */}
      {isAiModalOpen && (
        <div className="ai-modal-backdrop" onClick={handleCloseAiModal}>
          <div className="ai-generator-modal-card" onClick={(e) => e.stopPropagation()}>
            {/* Modal Header */}
            <div className="ai-modal-header">
              <div className="ai-modal-header-left">
                <div className="ai-modal-icon-badge">
                  <Sparkles size={22} />
                </div>
                <div>
                  <h2 className="ai-modal-title">Tạo bài tập tạo sinh AI</h2>
                  <p className="ai-modal-subtitle">
                    Thiết lập môn học, yêu cầu chủ đề và ma trận số câu theo từng mức độ nhận thức
                  </p>
                </div>
              </div>
              <button 
                type="button" 
                className="ai-modal-close-btn"
                onClick={handleCloseAiModal}
                title="Đóng"
              >
                <X size={20} />
              </button>
            </div>

            {/* Modal Body / Steps */}
            {generationStep === 4 ? (
              /* Success Stage */
              <div className="ai-success-content-box">
                <div className="ai-success-circle-icon">
                  <CheckCircle2 size={54} />
                </div>
                <h3 className="ai-success-title">Khởi tạo bài tập AI thành công!</h3>
                <p className="ai-success-desc">
                  Bài tập <strong>"{aiSubject} – {aiTopicPrompt.slice(0, 45)}"</strong> gồm <strong>{totalAiQuestions} câu hỏi</strong> đã được tạo xong và thêm vào Kho bài tập của bạn.
                </p>

                <div className="ai-success-matrix-pill-row">
                  <span className="pill-item fill-know">Nhận biết: <strong>{totalKnow} câu</strong></span>
                  <span className="pill-item fill-comp">Thông hiểu: <strong>{totalComp} câu</strong></span>
                  <span className="pill-item fill-app">Vận dụng: <strong>{totalApp} câu</strong></span>
                  <span className="pill-item fill-time">Thời gian: <strong>{aiDuration} phút</strong></span>
                </div>

                <div className="ai-success-actions-row">
                  <button 
                    type="button" 
                    className="btn-modal-cancel"
                    onClick={handleCloseAiModal}
                  >
                    Đóng và xem danh sách
                  </button>
                  <button 
                    type="button" 
                    className="btn-modal-start-generated"
                    onClick={() => {
                      const targetId = generatedExerciseId || '4';
                      handleCloseAiModal();
                      navigate(`/student/exercises/${targetId}/taking`);
                    }}
                  >
                    <span>Làm bài ngay</span>
                    <ArrowRight size={16} />
                  </button>
                </div>
              </div>
            ) : isGenerating ? (
              /* Generating Animation Stage */
              <div className="ai-generating-animation-box">
                <div className="ai-pulse-spinner">
                  <BrainCircuit size={48} className="spinner-brain-icon" />
                  <div className="spinner-wave-ring" />
                </div>
                
                <h3 className="generating-status-title">
                  {generationStep === 1 && 'Đang kết nối mô hình AI & phân tích chủ đề...'}
                  {generationStep === 2 && `Đang soạn ${part1Total} câu trắc nghiệm & ${part2Total} câu Đúng/Sai...`}
                  {generationStep === 3 && `Đang tạo ${part3Total} câu trả lời ngắn & hoàn thiện ma trận đề...`}
                </h3>
                <p className="generating-status-sub">
                  Vui lòng đợi giây lát trong khi AI tổng hợp dữ liệu chuẩn kiến thức.
                </p>

                <div className="generating-step-bars">
                  <div className={`step-bar-seg ${generationStep >= 1 ? 'active' : ''}`} />
                  <div className={`step-bar-seg ${generationStep >= 2 ? 'active' : ''}`} />
                  <div className={`step-bar-seg ${generationStep >= 3 ? 'active' : ''}`} />
                </div>
              </div>
            ) : (
              /* Main Configuration Form */
              <div className="ai-modal-scrollable-form">
                {/* 1. Basic Setup: Subject, Grade, Duration */}
                <div className="ai-config-section">
                  <div className="section-label-header">
                    <Sliders size={16} />
                    <span>1. Thông tin môn học & Thời gian</span>
                  </div>

                  <div className="ai-config-grid-3cols">
                    <div className="ai-form-group">
                      <label className="ai-form-label">Môn học</label>
                      <select 
                        className="ai-form-select"
                        value={aiSubject}
                        onChange={(e) => setAiSubject(e.target.value)}
                      >
                        <option value="Hóa học">Hóa học</option>
                        <option value="Toán học">Toán học</option>
                        <option value="Vật lý">Vật lý</option>
                        <option value="Sinh học">Sinh học</option>
                        <option value="Tiếng Anh">Tiếng Anh</option>
                        <option value="Lịch sử">Lịch sử</option>
                        <option value="Địa lý">Địa lý</option>
                        <option value="Tin học">Tin học</option>
                      </select>
                    </div>

                    <div className="ai-form-group">
                      <label className="ai-form-label">Khối lớp</label>
                      <select 
                        className="ai-form-select"
                        value={aiGrade}
                        onChange={(e) => setAiGrade(e.target.value)}
                      >
                        <option value="Lớp 12">Lớp 12</option>
                        <option value="Lớp 11">Lớp 11</option>
                        <option value="Lớp 10">Lớp 10</option>
                      </select>
                    </div>

                    <div className="ai-form-group">
                      <label className="ai-form-label">Thời gian làm bài</label>
                      <select 
                        className="ai-form-select"
                        value={aiDuration}
                        onChange={(e) => setAiDuration(Number(e.target.value))}
                      >
                        <option value={15}>15 phút</option>
                        <option value={30}>30 phút</option>
                        <option value={45}>45 phút</option>
                        <option value={50}>50 phút</option>
                        <option value={60}>60 phút</option>
                        <option value={90}>90 phút</option>
                      </select>
                    </div>
                  </div>
                </div>

                {/* 2. Topic & Chatbox AI Prompt */}
                <div className="ai-config-section">
                  <div className="section-label-header">
                    <MessageSquare size={16} />
                    <span>2. Chủ đề & Yêu cầu trọng tâm (Chatbox AI)</span>
                  </div>

                  <div className="ai-chatbox-card">
                    <div className="chatbox-input-wrapper">
                      <textarea 
                        className="ai-topic-textarea"
                        rows={3}
                        placeholder="Nhập chủ đề kiến thức, dạng bài tập cụ thể hoặc yêu cầu mở rộng (Ví dụ: Tập trung phản ứng este hóa, chất béo triolein, các câu hỏi tính khối lượng muối xà phòng hóa...)"
                        value={aiTopicPrompt}
                        onChange={(e) => setAiTopicPrompt(e.target.value)}
                      />
                      <div className="chatbox-hint-row">
                        <span className="char-counter">{aiTopicPrompt.length}/300 ký tự</span>
                        <span className="ai-magic-tag"><Sparkles size={12} /> AI Sáng tạo & Chuẩn đề Bộ GD</span>
                      </div>
                    </div>

                    {/* Quick Suggestion Chips */}
                    <div className="quick-suggestions-box">
                      <span className="suggestions-title"><Flame size={13} /> Gợi ý chủ đề nhanh:</span>
                      <div className="suggestion-chips-flex">
                        {topicSuggestions.map((item, idx) => (
                          <button
                            key={idx}
                            type="button"
                            className="suggestion-chip-btn"
                            onClick={() => {
                              setAiSubject(item.subject);
                              setAiTopicPrompt(item.prompt);
                            }}
                          >
                            <span>{item.label}</span>
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>

                {/* 3. Question Structure & Difficulty Distribution (Nhận biết, Thông hiểu, Vận dụng) */}
                <div className="ai-config-section">
                  <div className="section-label-header">
                    <Layers size={16} />
                    <span>3. Phân bổ câu hỏi theo cấu trúc & Mức độ nhận thức</span>
                  </div>

                  <div className="parts-config-container">
                    {/* PART I: Trắc nghiệm 4 lựa chọn */}
                    <div className="part-config-card">
                      <div className="part-card-top">
                        <div className="part-card-title-group">
                          <span className="part-badge part-badge-1">Phần I</span>
                          <span className="part-name">Trắc nghiệm 4 lựa chọn</span>
                        </div>
                        <div className="part-total-counter-box">
                          <span className="part-total-label">Tổng số câu Phần I:</span>
                          <strong className="part-total-value">{part1Total} câu</strong>
                        </div>
                      </div>

                      <div className="difficulty-controls-row">
                        <div className="diff-control-item item-know">
                          <div className="diff-item-info">
                            <span className="diff-dot dot-know" />
                            <span className="diff-label">Nhận biết</span>
                          </div>
                          <div className="counter-btn-group">
                            <button 
                              type="button" 
                              className="btn-counter-ctrl"
                              onClick={() => handleLevelChange(setPart1Levels, 'know', -1)}
                            >
                              <Minus size={13} />
                            </button>
                            <span className="counter-num-display">{part1Levels.know}</span>
                            <button 
                              type="button" 
                              className="btn-counter-ctrl"
                              onClick={() => handleLevelChange(setPart1Levels, 'know', 1)}
                            >
                              <Plus size={13} />
                            </button>
                          </div>
                        </div>

                        <div className="diff-control-item item-comp">
                          <div className="diff-item-info">
                            <span className="diff-dot dot-comp" />
                            <span className="diff-label">Thông hiểu</span>
                          </div>
                          <div className="counter-btn-group">
                            <button 
                              type="button" 
                              className="btn-counter-ctrl"
                              onClick={() => handleLevelChange(setPart1Levels, 'comp', -1)}
                            >
                              <Minus size={13} />
                            </button>
                            <span className="counter-num-display">{part1Levels.comp}</span>
                            <button 
                              type="button" 
                              className="btn-counter-ctrl"
                              onClick={() => handleLevelChange(setPart1Levels, 'comp', 1)}
                            >
                              <Plus size={13} />
                            </button>
                          </div>
                        </div>

                        <div className="diff-control-item item-app">
                          <div className="diff-item-info">
                            <span className="diff-dot dot-app" />
                            <span className="diff-label">Vận dụng</span>
                          </div>
                          <div className="counter-btn-group">
                            <button 
                              type="button" 
                              className="btn-counter-ctrl"
                              onClick={() => handleLevelChange(setPart1Levels, 'app', -1)}
                            >
                              <Minus size={13} />
                            </button>
                            <span className="counter-num-display">{part1Levels.app}</span>
                            <button 
                              type="button" 
                              className="btn-counter-ctrl"
                              onClick={() => handleLevelChange(setPart1Levels, 'app', 1)}
                            >
                              <Plus size={13} />
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* PART II: Trắc nghiệm Đúng / Sai */}
                    <div className="part-config-card">
                      <div className="part-card-top">
                        <div className="part-card-title-group">
                          <span className="part-badge part-badge-2">Phần II</span>
                          <span className="part-name">Trắc nghiệm Đúng / Sai (4 ý a, b, c, d)</span>
                        </div>
                        <div className="part-total-counter-box">
                          <span className="part-total-label">Tổng số câu Phần II:</span>
                          <strong className="part-total-value">{part2Total} câu</strong>
                        </div>
                      </div>

                      <div className="difficulty-controls-row">
                        <div className="diff-control-item item-know">
                          <div className="diff-item-info">
                            <span className="diff-dot dot-know" />
                            <span className="diff-label">Nhận biết</span>
                          </div>
                          <div className="counter-btn-group">
                            <button 
                              type="button" 
                              className="btn-counter-ctrl"
                              onClick={() => handleLevelChange(setPart2Levels, 'know', -1)}
                            >
                              <Minus size={13} />
                            </button>
                            <span className="counter-num-display">{part2Levels.know}</span>
                            <button 
                              type="button" 
                              className="btn-counter-ctrl"
                              onClick={() => handleLevelChange(setPart2Levels, 'know', 1)}
                            >
                              <Plus size={13} />
                            </button>
                          </div>
                        </div>

                        <div className="diff-control-item item-comp">
                          <div className="diff-item-info">
                            <span className="diff-dot dot-comp" />
                            <span className="diff-label">Thông hiểu</span>
                          </div>
                          <div className="counter-btn-group">
                            <button 
                              type="button" 
                              className="btn-counter-ctrl"
                              onClick={() => handleLevelChange(setPart2Levels, 'comp', -1)}
                            >
                              <Minus size={13} />
                            </button>
                            <span className="counter-num-display">{part2Levels.comp}</span>
                            <button 
                              type="button" 
                              className="btn-counter-ctrl"
                              onClick={() => handleLevelChange(setPart2Levels, 'comp', 1)}
                            >
                              <Plus size={13} />
                            </button>
                          </div>
                        </div>

                        <div className="diff-control-item item-app">
                          <div className="diff-item-info">
                            <span className="diff-dot dot-app" />
                            <span className="diff-label">Vận dụng</span>
                          </div>
                          <div className="counter-btn-group">
                            <button 
                              type="button" 
                              className="btn-counter-ctrl"
                              onClick={() => handleLevelChange(setPart2Levels, 'app', -1)}
                            >
                              <Minus size={13} />
                            </button>
                            <span className="counter-num-display">{part2Levels.app}</span>
                            <button 
                              type="button" 
                              className="btn-counter-ctrl"
                              onClick={() => handleLevelChange(setPart2Levels, 'app', 1)}
                            >
                              <Plus size={13} />
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* PART III: Trắc nghiệm Trả lời ngắn */}
                    <div className="part-config-card">
                      <div className="part-card-top">
                        <div className="part-card-title-group">
                          <span className="part-badge part-badge-3">Phần III</span>
                          <span className="part-name">Trắc nghiệm Trả lời ngắn</span>
                        </div>
                        <div className="part-total-counter-box">
                          <span className="part-total-label">Tổng số câu Phần III:</span>
                          <strong className="part-total-value">{part3Total} câu</strong>
                        </div>
                      </div>

                      <div className="difficulty-controls-row">
                        <div className="diff-control-item item-know">
                          <div className="diff-item-info">
                            <span className="diff-dot dot-know" />
                            <span className="diff-label">Nhận biết</span>
                          </div>
                          <div className="counter-btn-group">
                            <button 
                              type="button" 
                              className="btn-counter-ctrl"
                              onClick={() => handleLevelChange(setPart3Levels, 'know', -1)}
                            >
                              <Minus size={13} />
                            </button>
                            <span className="counter-num-display">{part3Levels.know}</span>
                            <button 
                              type="button" 
                              className="btn-counter-ctrl"
                              onClick={() => handleLevelChange(setPart3Levels, 'know', 1)}
                            >
                              <Plus size={13} />
                            </button>
                          </div>
                        </div>

                        <div className="diff-control-item item-comp">
                          <div className="diff-item-info">
                            <span className="diff-dot dot-comp" />
                            <span className="diff-label">Thông hiểu</span>
                          </div>
                          <div className="counter-btn-group">
                            <button 
                              type="button" 
                              className="btn-counter-ctrl"
                              onClick={() => handleLevelChange(setPart3Levels, 'comp', -1)}
                            >
                              <Minus size={13} />
                            </button>
                            <span className="counter-num-display">{part3Levels.comp}</span>
                            <button 
                              type="button" 
                              className="btn-counter-ctrl"
                              onClick={() => handleLevelChange(setPart3Levels, 'comp', 1)}
                            >
                              <Plus size={13} />
                            </button>
                          </div>
                        </div>

                        <div className="diff-control-item item-app">
                          <div className="diff-item-info">
                            <span className="diff-dot dot-app" />
                            <span className="diff-label">Vận dụng</span>
                          </div>
                          <div className="counter-btn-group">
                            <button 
                              type="button" 
                              className="btn-counter-ctrl"
                              onClick={() => handleLevelChange(setPart3Levels, 'app', -1)}
                            >
                              <Minus size={13} />
                            </button>
                            <span className="counter-num-display">{part3Levels.app}</span>
                            <button 
                              type="button" 
                              className="btn-counter-ctrl"
                              onClick={() => handleLevelChange(setPart3Levels, 'app', 1)}
                            >
                              <Plus size={13} />
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* 4. Matrix Breakdown Summary */}
                <div className="ai-matrix-summary-box">
                  <div className="matrix-summary-header">
                    <span className="summary-title">Tổng quan ma trận đề sinh AI:</span>
                    <span className="summary-total-tag">
                      Tổng số: <strong>{totalAiQuestions} câu</strong> • {aiDuration} phút
                    </span>
                  </div>

                  {/* Ratio bar */}
                  <div className="matrix-ratio-bar">
                    <div 
                      className="ratio-segment seg-know" 
                      style={{ width: `${totalAiQuestions > 0 ? (totalKnow / totalAiQuestions) * 100 : 33.3}%` }} 
                      title={`Nhận biết: ${totalKnow} câu`}
                    />
                    <div 
                      className="ratio-segment seg-comp" 
                      style={{ width: `${totalAiQuestions > 0 ? (totalComp / totalAiQuestions) * 100 : 33.3}%` }} 
                      title={`Thông hiểu: ${totalComp} câu`}
                    />
                    <div 
                      className="ratio-segment seg-app" 
                      style={{ width: `${totalAiQuestions > 0 ? (totalApp / totalAiQuestions) * 100 : 33.3}%` }} 
                      title={`Vận dụng: ${totalApp} câu`}
                    />
                  </div>

                  <div className="matrix-legend-row">
                    <div className="legend-item">
                      <span className="legend-dot dot-know" />
                      <span>Nhận biết: <strong>{totalKnow}</strong> ({totalAiQuestions > 0 ? Math.round((totalKnow / totalAiQuestions) * 100) : 0}%)</span>
                    </div>
                    <div className="legend-item">
                      <span className="legend-dot dot-comp" />
                      <span>Thông hiểu: <strong>{totalComp}</strong> ({totalAiQuestions > 0 ? Math.round((totalComp / totalAiQuestions) * 100) : 0}%)</span>
                    </div>
                    <div className="legend-item">
                      <span className="legend-dot dot-app" />
                      <span>Vận dụng: <strong>{totalApp}</strong> ({totalAiQuestions > 0 ? Math.round((totalApp / totalAiQuestions) * 100) : 0}%)</span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Modal Bottom Actions */}
            {generationStep < 4 && !isGenerating && (
              <div className="ai-modal-bottom-actions">
                <button 
                  type="button" 
                  className="btn-modal-cancel"
                  onClick={handleCloseAiModal}
                >
                  Hủy bỏ
                </button>

                <button 
                  type="button" 
                  className="btn-modal-generate-submit"
                  onClick={handleGenerateAiExercise}
                  disabled={totalAiQuestions === 0}
                >
                  <Sparkles size={16} />
                  <span>Khởi tạo bài tập với AI ({totalAiQuestions} câu)</span>
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ============================================================ */}
      {/* EXERCISE DETAIL & ATTEMPT HISTORY MODAL (EXACTLY LIKE IMAGE 1) */}
      {/* ============================================================ */}
      {selectedExerciseDetail && (
        <div className="detail-modal-backdrop" onClick={() => setSelectedExerciseDetail(null)}>
          <div className="exercise-detail-modal-card" onClick={(e) => e.stopPropagation()}>
            {/* Modal Header */}
            <div className="detail-modal-header">
              <div className="detail-modal-header-left">
                <div className="detail-modal-top-tags">
                  <span className="modal-status-pill-green">Đã hoàn thành</span>
                  <span className="modal-subject-grade-text">
                    {selectedExerciseDetail.subject || 'Toán học'} • {selectedExerciseDetail.grade || 'Lớp 12'}
                  </span>
                </div>
                <h2 className="detail-modal-main-title">
                  Chi tiết kết quả & Lịch sử làm bài - {selectedExerciseDetail.title}
                </h2>
                <p className="detail-modal-meta-line">
                  Giáo viên: <strong>Thầy {selectedExerciseDetail.teacher}</strong> • Thời lượng: <strong>{selectedExerciseDetail.duration}</strong> • Số lượng: <strong>{selectedExerciseDetail.questionsCount}</strong> • Hạn nộp: <strong className="due-highlight">{selectedExerciseDetail.deadline}</strong>
                </p>
              </div>
              <button 
                type="button" 
                className="detail-modal-close-btn"
                onClick={() => setSelectedExerciseDetail(null)}
                title="Đóng"
              >
                <X size={20} />
              </button>
            </div>

            {/* Modal Body */}
            <div className="detail-modal-scrollable-body">
              {/* 1. Dynamic Result Summary Card reflecting clicked attempt */}
              <div className="best-result-summary-box">
                <div className="best-result-top-row">
                  <div className="best-score-left-col">
                    <span className="best-score-label">{currentAttempt.scoreLabel}</span>
                    <div className="best-score-digits-row">
                      <span className="score-number-big">{currentAttempt.score}</span>
                      <span className="score-scale-denom">/ 10</span>
                      <span className="score-grade-pill">{currentAttempt.grade}</span>
                    </div>
                  </div>

                  <div className="best-stat-cell">
                    <span className="stat-cell-title">Đúng</span>
                    <span className="stat-cell-val val-green">
                      {currentAttempt.correctCount} / {currentAttempt.totalCount} câu <span className="stat-cell-pct">({currentAttempt.correctPct})</span>
                    </span>
                  </div>

                  <div className="best-stat-cell">
                    <span className="stat-cell-title">Thời gian làm</span>
                    <span className="stat-cell-val val-dark">{currentAttempt.timeSpent}</span>
                  </div>
                </div>

                {/* Cognitive Level Analysis */}
                <div className="cognitive-analysis-section">
                  <h4 className="cognitive-section-heading">Phân tích mức độ nhận thức</h4>
                  
                  <div className="cognitive-progress-list">
                    <div className="cognitive-progress-item">
                      <div className="cognitive-item-info">
                        <span className="cognitive-level-name">Nhận biết</span>
                        <span className="cognitive-level-score green-text">
                          {currentAttempt.cognitive.recognition.correct}/{currentAttempt.cognitive.recognition.total} ({currentAttempt.cognitive.recognition.pct})
                        </span>
                      </div>
                      <div className="cognitive-track">
                        <div 
                          className="cognitive-bar bar-green" 
                          style={{ width: currentAttempt.cognitive.recognition.pct }} 
                        />
                      </div>
                    </div>

                    <div className="cognitive-progress-item">
                      <div className="cognitive-item-info">
                        <span className="cognitive-level-name">Thông hiểu</span>
                        <span className="cognitive-level-score blue-text">
                          {currentAttempt.cognitive.understanding.correct}/{currentAttempt.cognitive.understanding.total} ({currentAttempt.cognitive.understanding.pct})
                        </span>
                      </div>
                      <div className="cognitive-track">
                        <div 
                          className="cognitive-bar bar-blue" 
                          style={{ width: currentAttempt.cognitive.understanding.pct }} 
                        />
                      </div>
                    </div>

                    <div className="cognitive-progress-item">
                      <div className="cognitive-item-info">
                        <span className="cognitive-level-name">Vận dụng</span>
                        <span className="cognitive-level-score purple-text">
                          {currentAttempt.cognitive.application.correct}/{currentAttempt.cognitive.application.total} ({currentAttempt.cognitive.application.pct})
                        </span>
                      </div>
                      <div className="cognitive-track">
                        <div 
                          className="cognitive-bar bar-purple" 
                          style={{ width: currentAttempt.cognitive.application.pct }} 
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* 2. Attempt History List */}
              <div className="attempts-history-wrapper">
                <div className="attempts-history-header">
                  <Clock size={16} className="history-clock-icon" />
                  <h3 className="attempts-history-title">Lịch sử các lần làm bài</h3>
                  <span className="attempts-unlimited-pill">Không giới hạn số lượt</span>
                </div>

                <div className="attempts-cards-list">
                  {attemptsData.map((attempt) => {
                    const isSelected = selectedAttemptId === attempt.id;
                    return (
                      <div
                        key={attempt.id}
                        className={`attempt-record-card ${isSelected ? 'is-selected-attempt' : ''} ${attempt.isLatest ? 'is-latest-attempt' : ''}`}
                        onClick={() => setSelectedAttemptId(attempt.id)}
                        title="Bấm để xem chi tiết kết quả lần làm bài này"
                      >
                        <div className="attempt-record-left">
                          <div className="attempt-badge-row">
                            <span className={`attempt-num-badge ${attempt.isLatest ? 'badge-latest-purple' : ''}`}>
                              {attempt.badgeLabel}
                            </span>
                            <span className="attempt-date-text">{attempt.dateText}</span>
                            <span className={attempt.statusTagClass}>{attempt.statusTag}</span>
                            {isSelected && (
                              <span className="attempt-viewing-tag">Đang hiển thị</span>
                            )}
                          </div>
                          <div className="attempt-stats-row">
                            <span>Điểm: <strong>{attempt.score} / 10</strong></span>
                            <span className="attempt-stat-divider">•</span>
                            <span>Thời gian: <strong>{attempt.timeSpent}</strong></span>
                          </div>
                        </div>

                        <button 
                          type="button" 
                          className="btn-view-attempt-detail"
                          onClick={(e) => {
                            e.stopPropagation();
                            const targetId = selectedExerciseDetail.id;
                            setSelectedExerciseDetail(null);
                            navigate(`/student/exercises/${targetId}/taking`);
                          }}
                        >
                          Xem chi tiết bài làm
                        </button>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Modal Bottom Actions */}
            <div className="detail-modal-footer-actions">
              <button 
                type="button" 
                className="btn-modal-close-flat"
                onClick={() => setSelectedExerciseDetail(null)}
              >
                Đóng
              </button>

              <div className="modal-footer-right-group">
                <button 
                  type="button" 
                  className="btn-modal-view-answers-outline"
                  onClick={() => {
                    const id = selectedExerciseDetail.id;
                    setSelectedExerciseDetail(null);
                    navigate(`/student/exercises/${id}/taking`);
                  }}
                >
                  Xem đáp án & giải thích chi tiết
                </button>

                <button 
                  type="button" 
                  className="btn-modal-retake-purple"
                  onClick={() => {
                    const id = selectedExerciseDetail.id;
                    setSelectedExerciseDetail(null);
                    navigate(`/student/exercises/${id}/taking`);
                  }}
                  title="Làm lại bài (Không giới hạn số lượt)"
                >
                  <RotateCcw size={15} />
                  <span>
                    {selectedExerciseDetail.category === 'exam' ? 'Làm lại bài thi' : 'Làm lại bài'}
                  </span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
