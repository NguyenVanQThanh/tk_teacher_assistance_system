// File Name: GradingFeedbackModal.jsx
// Description: Interactive grading and feedback modal with question result overrides, warning confirmation popup on answer key changes, and automatic batch cascade regrading.
// Created At: 2026-09-01
// Created By: Tam Khang
// Updated At: 2026-09-01
// Updated By: Tam Khang

import React, { useState, useEffect } from 'react';
import { 
  X, 
  Sparkles, 
  CheckCircle2, 
  AlertCircle, 
  FileText, 
  Send, 
  Award, 
  Clock, 
  User, 
  HelpCircle,
  ThumbsUp,
  MessageSquare,
  Check,
  RotateCcw,
  AlertTriangle,
  Loader2
} from 'lucide-react';
import { attemptsApi, exercisesApi } from '../../services/api';
import './GradingFeedbackModal.css';

export default function GradingFeedbackModal({ 
  isOpen, 
  onClose, 
  submission, 
  onSaveGrade,
  hasNextPending = false,
  onSaveAndNext
}) {
  if (!isOpen || !submission) return null;

  const isPendingGrading = submission.status === 'pending_grading' || submission.statusLabel === 'Chờ chấm';
  const isPendingReview = submission.status === 'pending_review' || submission.statusLabel === 'Chờ duyệt';
  const isAiExercise = submission.exerciseTypeCode === 'ai' || submission.exerciseType === 'Tạo sinh';

  // Base mock questions fallback
  const initialQuestions = [
    {
      id: 1,
      type: 'multiple_choice',
      typeName: 'CÂU 1 (TRẮC NGHIỆM)',
      maxPoints: 0.25,
      studentOption: 'A',
      correctOption: 'A',
      currentPoints: 0.25,
      isCorrect: true,
      needsManualGrading: false,
      stem: 'Tìm đạo hàm của hàm số y = x^3 - 3x^2 + 2 tại điểm x = 2.',
      options: [
        { key: 'A', text: "y'(2) = 0" },
        { key: 'B', text: "y'(2) = 3" },
        { key: 'C', text: "y'(2) = -3" },
        { key: 'D', text: "y'(2) = 6" },
      ]
    },
    {
      id: 2,
      type: 'true_false',
      typeName: 'CÂU 2 (TRẮC NGHIỆM ĐÚNG/SAI)',
      maxPoints: 0.25,
      studentOption: 'true',
      correctOption: 'true',
      currentPoints: 0.25,
      isCorrect: true,
      needsManualGrading: false,
      stem: 'Hàm số y = x^2 + 1 là hàm số chẵn. Đúng hay Sai?',
      options: [
        { key: 'true', text: 'Đúng' },
        { key: 'false', text: 'Sai' }
      ]
    },
    {
      id: 3,
      type: 'short_answer',
      typeName: 'CÂU 3 (TRẢ LỜI NGẮN)',
      maxPoints: 0.4,
      studentAnswer: '5',
      correctAnswer: '5',
      isCorrect: isPendingGrading ? true : (submission.score !== null ? submission.score >= 8 : true),
      currentPoints: 0.4,
      needsManualGrading: isPendingGrading,
      stem: 'Tìm giá trị cực đại của hàm số y = -x^2 + 4x + 1.'
    }
  ];

  const [questions, setQuestions] = useState(initialQuestions);
  const [score, setScore] = useState(submission.score !== null && submission.score !== undefined ? submission.score : 8.5);
  const [feedback, setFeedback] = useState(submission.feedback || '');
  const [isGeneratingAi, setIsGeneratingAi] = useState(false);
  const [hasModifiedAnswerKey, setHasModifiedAnswerKey] = useState(false);
  const [showWarningConfirmModal, setShowWarningConfirmModal] = useState(false);
  const [loadingDetails, setLoadingDetails] = useState(false);

  useEffect(() => {
    if (!submission) return;

    const initScore = submission.score !== null && submission.score !== undefined ? submission.score : 8.5;
    setScore(initScore);
    setFeedback(submission.feedback || 'Em làm bài tốt, tư duy giải mạch lạc.');
    setHasModifiedAnswerKey(false);
    setShowWarningConfirmModal(false);

    if (submission.attempt_id && submission.exercise_id) {
      let isMounted = true;
      async function loadRealDetails() {
        try {
          setLoadingDetails(true);
          const [attRes, exRes] = await Promise.allSettled([
            attemptsApi.getAttemptDetail(submission.attempt_id),
            exercisesApi.getExerciseDetail(submission.exercise_id)
          ]);

          if (!isMounted) return;

          if (exRes.status === 'fulfilled' && exRes.value && exRes.value.questions && exRes.value.questions.length > 0) {
            const exQuestions = exRes.value.questions;
            const attData = attRes.status === 'fulfilled' ? attRes.value : null;
            const attResults = (attData?.detailed_results?.questions || []);
            const resultsMap = {};
            attResults.forEach((r) => {
              resultsMap[r.question_id] = r;
            });

            const pointsPerQ = 10.0 / exQuestions.length;

            const mapped = exQuestions.map((q, idx) => {
              const res = resultsMap[q.question_id] || {};
              const isMC = q.question_type === 'MultipleChoice';
              
              let studentOptKey = null;
              let correctOptKey = null;
              const formattedOptions = (q.answer_options || []).map((opt, oIdx) => {
                const letter = String.fromCharCode(65 + oIdx);
                if (opt.is_correct) correctOptKey = letter;
                if (opt.option_id === res.student_answer_option_id) studentOptKey = letter;
                return { key: letter, text: opt.content, option_id: opt.option_id };
              });

              const isCorrect = res.is_correct !== undefined ? res.is_correct : (studentOptKey && studentOptKey === correctOptKey);
              const currentPoints = isCorrect ? pointsPerQ : 0;

              return {
                id: q.question_id,
                type: isMC ? 'multiple_choice' : 'short_answer',
                typeName: `CÂU ${idx + 1} (${isMC ? 'TRẮC NGHIỆM' : 'TRẢ LỜI NGẮN'})`,
                maxPoints: pointsPerQ,
                studentOption: studentOptKey,
                correctOption: correctOptKey,
                studentAnswer: res.student_answer_text || studentOptKey,
                correctAnswer: q.correct_answer || correctOptKey,
                currentPoints: currentPoints,
                isCorrect: isCorrect,
                needsManualGrading: res.pending_manual_grade || false,
                stem: q.content,
                options: formattedOptions
              };
            });

            setQuestions(mapped);
            if (attData && attData.score !== null && attData.score !== undefined) {
              setScore(attData.score);
            }
          } else {
            setQuestions(initialQuestions);
          }
        } catch (err) {
          setQuestions(initialQuestions);
        } finally {
          if (isMounted) setLoadingDetails(false);
        }
      }

      loadRealDetails();
      return () => { isMounted = false; };
    } else {
      setQuestions(initialQuestions);
    }
  }, [submission]);

  // Recalculate total score dynamically (scale to 10-point rubric)
  const recalculateOverallScore = (updatedQuestions) => {
    let earned = 0;
    let total = 0;
    updatedQuestions.forEach((q) => {
      earned += q.currentPoints;
      total += q.maxPoints;
    });
    const ratio = total > 0 ? earned / total : 1;
    const computedScore = parseFloat((ratio * 10).toFixed(1));
    setScore(computedScore);
  };

  // Teacher clicks on an option to set it as the correct answer
  const handleSelectCorrectOption = (qId, optionKey) => {
    setHasModifiedAnswerKey(true);
    const updated = questions.map((q) => {
      if (q.id === qId) {
        const isCorrect = q.studentOption === optionKey;
        const currentPoints = isCorrect ? q.maxPoints : 0;
        return {
          ...q,
          correctOption: optionKey,
          isCorrect,
          currentPoints
        };
      }
      return q;
    });
    setQuestions(updated);
    recalculateOverallScore(updated);
  };

  // Teacher toggles short answer correctness (changes 0.4 points)
  const handleToggleShortAnswer = (qId, isCorrect) => {
    setHasModifiedAnswerKey(true);
    const updated = questions.map((q) => {
      if (q.id === qId) {
        const currentPoints = isCorrect ? q.maxPoints : 0;
        return {
          ...q,
          isCorrect,
          currentPoints,
          needsManualGrading: false // Marked as graded once clicked
        };
      }
      return q;
    });
    setQuestions(updated);
    recalculateOverallScore(updated);
  };

  const quickFeedbackTemplates = [
    'Làm bài tốt, tư duy sắc bén và chính xác.',
    'Cần trình bày chi tiết các bước giải trung gian.',
    'Chú ý kiểm tra lại điều kiện xác định của phương trình.',
    'Rất tiến bộ, nắm chắc phương pháp và công thức.'
  ];

  const handleApplyAiFeedback = () => {
    setIsGeneratingAi(true);
    setTimeout(() => {
      setIsGeneratingAi(false);
      const generated = `[AI Gợi ý] Học sinh nắm vững kiến thức trọng tâm về ${submission.exerciseTitle}. Điểm mạnh: Khả năng vận dụng công thức nhanh, logic lời giải tốt. Điểm cần cải thiện: Cần cẩn thận hơn ở khâu rút gọn biểu thức và ghi chú đơn vị.`;
      setFeedback(generated);
    }, 600);
  };

  // Triggered when user clicks "Hoàn tất" button
  const handleInitiateSave = () => {
    if (hasModifiedAnswerKey) {
      setShowWarningConfirmModal(true);
    } else {
      executeSave(false);
    }
  };

  // Performs actual save action
  const executeSave = (cascade) => {
    setShowWarningConfirmModal(false);
    onSaveGrade({
      ...submission,
      score: parseFloat(score),
      feedback: feedback,
      status: 'approved',
      statusLabel: 'Đã duyệt',
      questionsData: questions,
      cascadeRegrade: cascade,
      modifiedQuestions: questions
    });
    onClose();
  };

  const q1 = questions[0];
  const q2 = questions[1];
  const q3 = questions[2];

  // Dynamic rubric scores
  const scoreNum = parseFloat(score) || 0;
  const recognitionScore = Math.min(10, (scoreNum >= 5 ? 10 : 6)).toFixed(1);
  const logicScore = Math.min(10, Math.max(0, scoreNum * 0.95)).toFixed(1);
  const calcScore = Math.min(10, Math.max(0, scoreNum * 0.9)).toFixed(1);

  return (
    <>
      <div className="grading-modal-overlay">
        <div className="grading-modal-window">
          {/* Modal Header */}
          <header className="grading-modal-header">
            <div className="modal-header-left">
              <button 
                type="button" 
                className="btn-modal-close-left" 
                onClick={onClose}
                title="Đóng cửa sổ"
              >
                <X size={20} />
              </button>

              <div className="submission-student-badge">
                <div className="student-initials-circle">
                  {submission.avatarInitial}
                </div>
                <div className="student-info-col">
                  <div className="student-name-row">
                    <h2 className="student-full-name">{submission.studentName}</h2>
                    <span className="class-tag">{submission.className}</span>
                    {isPendingGrading && (
                      <span className="status-badge amber modal-head-status">Chờ chấm</span>
                    )}
                    {isPendingReview && (
                      <span className="status-badge blue modal-head-status">Chờ duyệt</span>
                    )}
                  </div>
                  <div className="submission-meta-row">
                    <span className="exercise-name-badge">{submission.exerciseTitle}</span>
                    <span className="meta-separator">•</span>
                    <span className="sub-type-badge">{submission.exerciseType}</span>
                    <span className="meta-separator">•</span>
                    <span className="submit-time-text">
                      <Clock size={13} /> {submission.submittedTime}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </header>

          {/* Modal Main Body */}
          <div className="grading-modal-body">
            {/* Left Column: Student Submission & Interactive Question Overrides */}
            <div className="grading-content-panel">
              <div className="panel-section-header">
                <div className="section-title-wrap">
                  <FileText size={18} className="title-icon text-purple" />
                  <h3 className="section-title">Nội dung bài nộp của học sinh</h3>
                </div>
                <span className="status-badge-chip success">
                  <CheckCircle2 size={13} /> 10/10 câu đã làm
                </span>
              </div>

              {/* Interactive Notice Banner for Teacher Overrides & Manual Grading */}
              <div className={`ai-grading-edit-banner ${isPendingGrading ? 'amber-banner' : ''}`}>
                <div className="banner-icon-title">
                  {isPendingGrading ? (
                    <AlertTriangle size={16} className="text-amber" />
                  ) : (
                    <Sparkles size={16} className="text-purple" />
                  )}
                  <span className="banner-title">
                    {isPendingGrading 
                      ? 'Chế độ chấm bài: Câu hỏi cần giáo viên chấm được làm nổi bật màu vàng'
                      : 'Chế độ duyệt & chỉnh sửa kết quả trực tiếp'}
                  </span>
                </div>
                <p className="banner-desc">
                  Giáo viên có thể bấm trực tiếp vào đáp án để thay đổi kết quả (Đúng/Sai). Điểm số tổng kết và các tiêu chí sẽ tự động tính toán lại tương ứng.
                </p>
              </div>

              {/* Questions list */}
              <div className="submission-questions-container">
                {/* Question 1: Trắc nghiệm 4 lựa chọn (0.25đ) */}
                <div className={`question-review-card ${!q1.isCorrect ? 'incorrect-marked' : ''}`}>
                  <div className="question-card-head">
                    <span className="question-num-tag">{q1.typeName}</span>
                    <span className={`question-points-tag ${q1.currentPoints === 0 ? 'zero-points' : ''}`}>
                      {q1.currentPoints} điểm
                    </span>
                  </div>

                  <p className="question-stem-text">
                    {q1.stem}
                  </p>

                  <div className="options-review-grid">
                    {q1.options.map((opt) => {
                      const isStudentChoice = opt.key === q1.studentOption;
                      const isCorrectChoice = opt.key === q1.correctOption;

                      let optionClass = 'option-choice clickable-option';
                      let badge = null;

                      if (isCorrectChoice && isStudentChoice) {
                        optionClass += ' correct selected';
                        badge = <span className="badge-correct">Đúng</span>;
                      } else if (isCorrectChoice && !isStudentChoice) {
                        optionClass += ' correct teacher-correct';
                        badge = <span className="badge-correct">Đáp án đúng</span>;
                      } else if (!isCorrectChoice && isStudentChoice) {
                        optionClass += ' incorrect-option student-wrong';
                        badge = <span className="badge-correct badge-wrong">Học sinh chọn (Sai)</span>;
                      }

                    return (
                      <div
                        key={opt.key}
                        className={optionClass}
                        onClick={() => handleSelectCorrectOption(1, opt.key)}
                        title={`Bấm để chọn đáp án ${opt.key} làm đáp án đúng`}
                      >
                        <span className="option-letter">{opt.key}.</span>
                        <span className="option-text">{opt.text}</span>
                        {badge}
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Question 2: Trắc nghiệm Đúng/Sai (0.25đ) */}
              <div className={`question-review-card ${!q2.isCorrect ? 'incorrect-marked' : ''}`}>
                <div className="question-card-head">
                  <span className="question-num-tag">{q2.typeName}</span>
                  <span className={`question-points-tag ${q2.currentPoints === 0 ? 'zero-points' : ''}`}>
                    {q2.currentPoints} điểm
                  </span>
                </div>

                <p className="question-stem-text">
                  {q2.stem}
                </p>

                <div className="options-truefalse-grid">
                  {q2.options.map((opt) => {
                    const isStudentChoice = opt.key === q2.studentOption;
                    const isCorrectChoice = opt.key === q2.correctOption;

                    let optionClass = 'option-choice clickable-option';
                    let badge = null;

                    if (isCorrectChoice && isStudentChoice) {
                      optionClass += ' correct selected';
                      badge = <span className="badge-correct">Đã chọn</span>;
                    } else if (isCorrectChoice && !isStudentChoice) {
                      optionClass += ' correct teacher-correct';
                      badge = <span className="badge-correct">Đáp án đúng</span>;
                    } else if (!isCorrectChoice && isStudentChoice) {
                      optionClass += ' incorrect-option student-wrong';
                      badge = <span className="badge-correct badge-wrong">Học sinh chọn (Sai)</span>;
                    }

                    return (
                      <div
                        key={opt.key}
                        className={optionClass}
                        onClick={() => handleSelectCorrectOption(2, opt.key)}
                        title={`Bấm để đặt đáp án ${opt.text} làm đáp án đúng`}
                      >
                        <span className="option-text">{opt.text}</span>
                        {badge}
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Question 3: Trả lời ngắn / Tự luận (0.4đ) - COVERED IN DISTINCT COLOR IN "CHỜ CHẤM" */}
              <div 
                className={`question-review-card ${
                  isPendingGrading || q3.needsManualGrading ? 'manual-grading-highlight' : ''
                } ${!q3.isCorrect ? 'incorrect-marked' : ''}`}
              >
                <div className="question-card-head">
                  <div className="head-badge-group">
                    <span className="question-num-tag">{q3.typeName}</span>
                    {(isPendingGrading || q3.needsManualGrading) && (
                      <span className="manual-grade-alert-pill">
                        ⚡ CẦN GIÁO VIÊN CHẤM
                      </span>
                    )}
                  </div>
                  <span className={`question-points-tag ${q3.currentPoints === 0 ? 'zero-points' : ''}`}>
                    {q3.currentPoints} điểm
                  </span>
                </div>

                <p className="question-stem-text">
                  {q3.stem}
                </p>

                <div className={`student-written-answer-box ${
                  isPendingGrading || q3.needsManualGrading ? 'manual-grading-answer-box' : ''
                } ${!q3.isCorrect ? 'written-wrong' : ''}`}>
                  <div className="written-box-header">
                    <span className="written-label">BÀI GIẢI CỦA HỌC SINH:</span>
                    <div className="written-toggle-actions">
                      <button
                        type="button"
                        className={`btn-written-eval ${q3.isCorrect ? 'active-correct' : ''}`}
                        onClick={() => handleToggleShortAnswer(3, true)}
                        title="Đánh dấu câu trả lời Đúng (+0.4 điểm)"
                      >
                        <Check size={12} /> Đúng (+0.4đ)
                      </button>
                      <button
                        type="button"
                        className={`btn-written-eval ${!q3.isCorrect ? 'active-wrong' : ''}`}
                        onClick={() => handleToggleShortAnswer(3, false)}
                        title="Đánh dấu câu trả lời Sai (0 điểm)"
                      >
                        <X size={12} /> Sai (0đ)
                      </button>
                    </div>
                  </div>
                  <div className="written-content-row">
                    <span className="short-answer-val">{q3.studentAnswer}</span>
                    <span className={`badge-correct ${!q3.isCorrect ? 'badge-wrong' : ''}`}>
                      {q3.isCorrect ? 'Đúng' : 'Sai'}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: Grading Controls & Feedback */}
          <div className="grading-action-panel">
            {/* Score Summary Card (Strictly calculated based on correct answers) */}
            <div className="grading-score-card">
              <div className="score-card-top">
                <div className="score-label-group">
                  <Award size={18} className="text-purple" />
                  <div>
                    <span className="score-label">Điểm số tổng kết</span>
                    <span className="score-sub-calc-note">Tự động tính theo số câu đúng</span>
                  </div>
                </div>
                <div className="score-badge-auto-display">
                  <span className="score-val-huge">{score}</span>
                  <span className="max-score-text">/ 10</span>
                </div>
              </div>

              {/* Automatic question correctness breakdown bar */}
              <div className="score-stats-breakdown-row">
                <span className="stats-breakdown-text">
                  Đúng <strong>{questions.filter(q => q.isCorrect).length}/{questions.length} câu</strong> ({((questions.filter(q => q.isCorrect).length / questions.length) * 100).toFixed(0)}%)
                </span>
                <span className="stats-breakdown-points">
                  Tổng điểm thành phần: <strong>{questions.reduce((acc, q) => acc + q.currentPoints, 0).toFixed(2)}/0.90đ</strong>
                </span>
              </div>
            </div>

            {/* Rubrics breakdown */}
            <div className="criteria-rubric-card">
              <h4 className="rubric-title">Đánh giá theo tiêu chí chuẩn</h4>
              <div className="criteria-row">
                <span className="criteria-name">Nhận biết & Thông hiểu</span>
                <span className="criteria-val">{recognitionScore}/10</span>
              </div>
              <div className="criteria-row">
                <span className="criteria-name">Vận dụng logic & Lời giải</span>
                <span className="criteria-val">{logicScore}/10</span>
              </div>
              <div className="criteria-row">
                <span className="criteria-name">Trình bày & Tính toán</span>
                <span className="criteria-val">{calcScore}/10</span>
              </div>
            </div>

            {/* AI Feedback Suggestion & Textarea */}
            <div className="feedback-section-card">
              <div className="feedback-head-row">
                <div className="feedback-title-wrap">
                  <MessageSquare size={16} className="text-purple" />
                  <h4 className="feedback-heading">Nhận xét & Lời khuyên</h4>
                </div>
                <button
                  type="button"
                  className="btn-ai-generate"
                  onClick={handleApplyAiFeedback}
                  disabled={isGeneratingAi}
                >
                  <Sparkles size={13} />
                  <span>{isGeneratingAi ? 'Đang tạo...' : 'Gợi ý từ AI'}</span>
                </button>
              </div>

              {/* Quick comment chips */}
              <div className="feedback-templates-list">
                {quickFeedbackTemplates.map((item, idx) => (
                  <button
                    key={idx}
                    type="button"
                    className="template-chip"
                    onClick={() => setFeedback(item)}
                  >
                    <ThumbsUp size={12} />
                    <span>{item}</span>
                  </button>
                ))}
              </div>

              <textarea
                className="feedback-textarea"
                rows={4}
                value={feedback}
                onChange={(e) => setFeedback(e.target.value)}
                placeholder="Nhập lời nhận xét hoặc sử dụng nút Gợi ý từ AI..."
              />
            </div>

            {/* Bottom Actions matching Image 2 */}
            <div className="grading-modal-footer">
              <button 
                type="button" 
                className="btn-cancel" 
                onClick={onClose}
              >
                Hủy
              </button>

              <button 
                type="button" 
                className="btn-submit-grade" 
                onClick={handleInitiateSave}
              >
                <CheckCircle2 size={16} />
                <span>Hoàn tất</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    {/* Warning Confirmation Dialog for Answer Key Override */}
    {showWarningConfirmModal && (
      <div 
        className="warning-confirm-overlay"
        onClick={() => setShowWarningConfirmModal(false)}
      >
        <div 
          className="warning-confirm-dialog"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="warning-dialog-body">
            <div className="warning-icon-circle">
              <AlertTriangle size={32} className="warning-alert-icon" />
            </div>

            <div className="warning-text-container">
              <h3 className="warning-title-text">Xác nhận thay đổi đáp án</h3>
              <p className="warning-main-prompt">
                Thầy/Cô có chắc chắn muốn cập nhật đáp án cho câu hỏi này không?
              </p>
              
              <div className="warning-note-callout">
                <span className="warning-note-label">Chú thích:</span>
                <p className="warning-note-text">
                  Khi thay đổi, hệ thống sẽ lưu đáp án mới và <strong>tự động tính lại điểm số cho tất cả bài làm của học sinh thuộc bài tập này</strong>.
                </p>
              </div>
            </div>
          </div>

          <div className="warning-dialog-actions">
            <button
              type="button"
              className="btn-warning-back"
              onClick={() => setShowWarningConfirmModal(false)}
            >
              Hủy
            </button>

            <button
              type="button"
              className="btn-warning-accept"
              onClick={() => executeSave(true)}
            >
              <CheckCircle2 size={16} />
              <span>Xác nhận & Cập nhật điểm</span>
            </button>
          </div>
        </div>
      </div>
    )}
  </>
  );
}
