// File Name: StudentExerciseTakingPage.jsx
// Description: Interactive student examination interface supporting 3 question types: Multiple Choice (4 options), True/False (4 sub-items), and Short Answer (with on-screen numpad helper).
// Created At: 2026-09-07
// Created By: Tam Khang
// Updated At: 2026-10-11
// Updated By: Tam Khang

import React, { useState, useEffect, useMemo } from 'react';
import { 
  Clock, 
  HelpCircle, 
  Settings, 
  Flag, 
  ArrowLeft, 
  ArrowRight, 
  Send, 
  CheckCircle2, 
  XCircle, 
  Hash, 
  Delete, 
  RotateCcw, 
  Sparkles, 
  Info,
  AlertCircle,
  X,
  Check,
  Lightbulb,
  ShieldAlert,
  Eye,
  Lock,
  Loader2,
  Maximize2,
  Minimize2
} from 'lucide-react';
import { useNavigate, Link, useParams, useLocation } from 'react-router-dom';
import { exercisesApi, attemptsApi } from '../../services/api';
import MathRenderer from '../../components/common/MathRenderer';
import './StudentExerciseTakingPage.css';

export default function StudentExerciseTakingPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { exerciseId } = useParams();
  const currentExamId = exerciseId || '1';

  const stateAssignmentId = location.state?.assignmentId;
  const stateExerciseId = location.state?.exerciseId || exerciseId;

  // Real Backend Data States
  const [backendExercise, setBackendExercise] = useState(null);
  const [backendQuestions, setBackendQuestions] = useState([]);
  const [attemptId, setAttemptId] = useState(null);
  const [isLoadingBackend, setIsLoadingBackend] = useState(false);
  const [backendError, setBackendError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Exercise / Exam Metadata from localStorage (for AI generated practice fallback)
  const savedAiExercise = useMemo(() => {
    try {
      const saved = localStorage.getItem('tk_student_ai_exercises');
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed)) {
          return parsed.find(ex => String(ex.id) === String(currentExamId));
        }
      }
    } catch (e) {
      console.error(e);
    }
    return null;
  }, [currentExamId]);

  const isChemistry = currentExamId === '4' || Boolean(savedAiExercise && savedAiExercise.subject === 'Hóa học');
  const isAiExercise = Boolean(savedAiExercise);

  // Helper to normalize any backend question_type (MultipleChoice, TrueFalse, ShortAnswer, etc.)
  const normalizeQType = (typeStr) => {
    const clean = String(typeStr || '').replace(/[^a-zA-Z]/g, '').toUpperCase();
    if (clean.includes('TRUEFALSE') || clean.includes('DUNGSAI')) return 'TRUE_FALSE';
    if (clean.includes('SHORTANSWER') || clean.includes('TRALOI') || clean.includes('NGAN') || clean.includes('FILL') || clean.includes('NUMERIC')) return 'SHORT_ANSWER';
    return 'MULTIPLE_CHOICE';
  };

  // Initialize Backend Exam and Attempt
  useEffect(() => {
    let isMounted = true;
    async function initExam() {
      const isUuid = (id) => typeof id === 'string' && /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(id);

      const targetExerciseId = stateExerciseId || exerciseId;
      let targetAssignmentId = stateAssignmentId;

      // 0. Auto-resolve assignment ID if missing from navigation state
      if (isUuid(targetExerciseId) && !isUuid(targetAssignmentId)) {
        try {
          const assignments = await assignmentsApi.getAssignments();
          const matched = (assignments || []).find(a => 
            String(a.exercise_id).toLowerCase() === String(targetExerciseId).toLowerCase() ||
            String(a.assignment_id).toLowerCase() === String(targetExerciseId).toLowerCase()
          );
          if (matched && matched.assignment_id) {
            targetAssignmentId = matched.assignment_id;
          }
        } catch (resolveErr) {
          console.warn('Assignment lookup fallback error:', resolveErr);
        }
      }

      if (isUuid(targetExerciseId) || isUuid(targetAssignmentId)) {
        try {
          setIsLoadingBackend(true);

          let sortedQ = [];
          let exerciseData = null;
          // 1. Fetch exercise detail from backend
          if (isUuid(targetExerciseId)) {
            try {
              exerciseData = await exercisesApi.getExerciseDetail(targetExerciseId);
            } catch (fetchErr) {
              console.warn('Direct exercise lookup failed, attempting assignment resolution fallback...', fetchErr);
              try {
                const assignments = await assignmentsApi.getAssignments();
                const matched = (assignments || []).find(a => 
                  String(a.assignment_id).toLowerCase() === String(targetExerciseId).toLowerCase()
                );
                if (matched && matched.exercise_id) {
                  exerciseData = await exercisesApi.getExerciseDetail(matched.exercise_id);
                  targetAssignmentId = matched.assignment_id;
                }
              } catch (fallbackErr) {
                console.error('Assignment resolution fallback error:', fallbackErr);
              }
            }

            if (isMounted && exerciseData) {
              setBackendExercise(exerciseData);
              if (exerciseData.questions && exerciseData.questions.length > 0) {
                sortedQ = [...exerciseData.questions]
                  .map(q => ({
                    ...q,
                    answer_options: [...(q.answer_options || [])].sort((a, b) => (a.display_order || 0) - (b.display_order || 0))
                  }))
                  .sort((a, b) => (a.display_order || 0) - (b.display_order || 0));
                setBackendQuestions(sortedQ);
              }
            }
          }

          // 2. Fetch existing attempt from DB (matching assignmentId or exerciseId) or start attempt
          try {
            const myAttempts = await attemptsApi.getAttempts();
            const attemptList = Array.isArray(myAttempts) ? myAttempts : [];
            const matchingAttempts = attemptList.filter(a => 
              (targetAssignmentId && String(a.assignment_id).toLowerCase() === String(targetAssignmentId).toLowerCase()) || 
              (targetExerciseId && String(a.exercise_id).toLowerCase() === String(targetExerciseId).toLowerCase())
            );

            // Prioritize specified attempt from modal or open in-progress attempt, or finished attempt
            const stateAttemptId = location.state?.attemptId;
            const isRetake = Boolean(location.state?.isRetake);
            let specifiedAttempt = null;
            if (stateAttemptId && isUuid(stateAttemptId)) {
              try {
                specifiedAttempt = await attemptsApi.getAttemptDetail(stateAttemptId);
              } catch (e) {
                console.warn('Could not fetch specified attempt detail directly:', e);
              }
            }
            if (!specifiedAttempt && stateAttemptId) {
              specifiedAttempt = matchingAttempts.find(a => String(a.attempt_id).toLowerCase() === String(stateAttemptId).toLowerCase()) || null;
            }

            const openAttempt = matchingAttempts.find(a => !a.is_finished);
            const finishedAttempt = matchingAttempts.find(a => a.is_finished);
            
            const isExamExercise = Boolean(
              backendExercise?.category === 'exam' ||
              (backendExercise?.title || '').toLowerCase().includes('đề thi') ||
              (location.state?.title || '').toLowerCase().includes('đề thi')
            );
            const isExamLocked = isExamExercise && finishedAttempt && !openAttempt;

            // Only enter review mode if specifically requested or if finished and NOT a retake/open attempt (exams can never be retaken once finished)
            const reviewTarget = specifiedAttempt?.is_finished 
              ? specifiedAttempt 
              : (isExamLocked ? finishedAttempt : (!isRetake && !openAttempt && finishedAttempt ? finishedAttempt : null));

            if (reviewTarget && reviewTarget.is_finished) {
              let fullAttempt = reviewTarget;
              if (!fullAttempt.detailed_results) {
                try {
                  const detailAtt = await attemptsApi.getAttemptDetail(reviewTarget.attempt_id);
                  if (detailAtt) fullAttempt = detailAtt;
                } catch (e) {
                  console.warn('Could not fetch full attempt detail:', e);
                }
              }

              if (isMounted) {
                setAttemptId(fullAttempt.attempt_id);
                setAttemptDetailedResults(fullAttempt.detailed_results || null);
                setIsExamSubmitted(true);
                setIsReadOnlyReview(true);

                // Show actual exam duration instead of countdown timer
                if (fullAttempt.total_time_seconds != null) {
                  setTimeLeft(fullAttempt.total_time_seconds);
                }
                
                // Reconstruct student answers from DB detailed_results
                const restored = {};
                if (fullAttempt.detailed_results?.questions && sortedQ.length > 0) {
                  fullAttempt.detailed_results.questions.forEach(qRes => {
                    const qIdx = sortedQ.findIndex(q => String(q.question_id).toLowerCase() === String(qRes.question_id).toLowerCase());
                    if (qIdx !== -1) {
                      const targetQ = sortedQ[qIdx];
                      const normType = normalizeQType(targetQ.question_type);
                      if (normType === 'MULTIPLE_CHOICE') {
                        if (qRes.student_answer_option_id) {
                          const letters = ['A', 'B', 'C', 'D', 'E', 'F'];
                          const optIdx = (targetQ.answer_options || []).findIndex(opt => String(opt.option_id).toLowerCase() === String(qRes.student_answer_option_id).toLowerCase());
                          if (optIdx !== -1) {
                            restored[qIdx] = letters[optIdx] || 'A';
                          }
                        }
                      } else if (normType === 'SHORT_ANSWER') {
                        restored[qIdx] = (qRes.student_answer_text !== null && qRes.student_answer_text !== undefined) 
                          ? String(qRes.student_answer_text).replace(/\./g, ',') 
                          : '';
                      } else if (normType === 'TRUE_FALSE') {
                        if (qRes.student_answer_text) {
                          const tfObj = {};
                          qRes.student_answer_text.split(';').forEach(pair => {
                            const [k, v] = pair.split(':');
                            if (k) tfObj[k.trim()] = (String(v).trim().toLowerCase() === 'true');
                          });
                          restored[qIdx] = tfObj;
                        }
                      }
                    }
                  });
                }
                setAnswers(restored);

                // Count actually answered questions for review display
                const restoredCount = Object.keys(restored).filter(k => {
                  const v = restored[k];
                  if (v === undefined || v === null) return false;
                  if (typeof v === 'string') return v.trim().length > 0;
                  if (typeof v === 'object') return Object.keys(v).length > 0;
                  return false;
                }).length;

                const subData = {
                  submittedAt: fullAttempt.end_time || fullAttempt.created_at,
                  formattedTime: fullAttempt.end_time 
                    ? new Date(fullAttempt.end_time).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }) + ' · ' + new Date(fullAttempt.end_time).toLocaleDateString('vi-VN')
                    : 'Đã nộp trước đó',
                  score: fullAttempt.score !== null && fullAttempt.score !== undefined ? Number(fullAttempt.score).toFixed(2) : null,
                  isExam: true,
                  title: backendExercise?.title || location.state?.title || 'Bài thi trực tuyến',
                  attemptId: fullAttempt.attempt_id,
                  savedAnswers: restored,
                  totalTimeSeconds: fullAttempt.total_time_seconds || null,
                  answeredCount: restoredCount
                };
                setSubmissionResult(subData);

                try {
                  localStorage.setItem(`tk_exam_submitted_${currentExamId}`, JSON.stringify(subData));
                  if (targetAssignmentId) {
                    localStorage.setItem(`tk_exam_submitted_${targetAssignmentId}`, JSON.stringify(subData));
                  }
                } catch (e) {
                  console.warn('Could not cache submission:', e);
                }
              }
            } else {
              // Active taking mode: ensure review states are false and clean up stale local submission flags
              if (isMounted) {
                setIsExamSubmitted(false);
                setIsReadOnlyReview(false);
                setSubmissionResult(null);
              }
              try {
                localStorage.removeItem(`tk_exam_submitted_${currentExamId}`);
                if (targetAssignmentId) localStorage.removeItem(`tk_exam_submitted_${targetAssignmentId}`);
              } catch (e) {}

              if (openAttempt) {
                // Seamlessly resume open attempt
                if (isMounted) {
                  setAttemptId(openAttempt.attempt_id);
                }
              } else if (isUuid(targetAssignmentId)) {
                try {
                  const startRes = await attemptsApi.startAttempt(targetAssignmentId);
                  if (isMounted && startRes?.attempt_id) {
                    setAttemptId(startRes.attempt_id);
                  }
                } catch (startErr) {
                  console.warn('Could not start new attempt, looking for open attempt:', startErr);
                  const refreshed = await attemptsApi.getAttempts();
                  const foundOpen = (refreshed || []).find(a => 
                    String(a.assignment_id).toLowerCase() === String(targetAssignmentId).toLowerCase() && !a.is_finished
                  );
                  if (isMounted && foundOpen) {
                    setAttemptId(foundOpen.attempt_id);
                  }
                }
              }
            }
          } catch (attErr) {
            console.warn('Attempt lookup/start fallback:', attErr);
          }
        } catch (err) {
          console.error('Failed to initialize backend exam:', err);
          if (isMounted) {
            setBackendError(err.response?.data?.detail?.message || 'Không thể tải đề thi từ hệ thống.');
          }
        } finally {
          if (isMounted) {
            setIsLoadingBackend(false);
          }
        }
      }
    }

    initExam();
    return () => {
      isMounted = false;
    };
  }, [exerciseId, stateAssignmentId, stateExerciseId]);

  const exerciseInfo = useMemo(() => {
    if (backendExercise) {
      const qList = backendQuestions;
      const p1 = qList.filter(q => normalizeQType(q.question_type) === 'MULTIPLE_CHOICE').length;
      const p2 = qList.filter(q => normalizeQType(q.question_type) === 'TRUE_FALSE').length;
      const p3 = qList.filter(q => normalizeQType(q.question_type) === 'SHORT_ANSWER').length;
      const isMath = (backendExercise.title || '').toLowerCase().includes('toán');
      return {
        id: backendExercise.exercise_id,
        title: backendExercise.title || location.state?.title || 'Đề thi trực tuyến',
        subject: location.state?.subject || (isMath ? 'Toán học' : 'Hóa học'),
        category: 'exam',
        categoryLabel: 'Bài thi chính thức',
        teacher: location.state?.teacher || 'Sample Teacher (Thầy Nguyễn Văn A)',
        totalQuestions: qList.length || 20,
        part1Count: p1,
        part2Count: p2,
        part3Count: p3,
        durationMinutes: 45,
        isExam: true,
        isBackend: true
      };
    }

    if (savedAiExercise) {
      const p1 = savedAiExercise.part1Count || 15;
      const p2 = savedAiExercise.part2Count || 5;
      const p3 = savedAiExercise.part3Count || 5;
      return {
        id: savedAiExercise.id,
        title: savedAiExercise.title || 'Bài tập tạo sinh AI',
        subject: savedAiExercise.subject || 'Hóa học',
        category: 'exercise',
        categoryLabel: 'Bài tập tạo sinh AI',
        teacher: savedAiExercise.teacher || 'Trợ lý AI Tam Khang',
        totalQuestions: savedAiExercise.totalQuestions || (p1 + p2 + p3),
        part1Count: p1,
        part2Count: p2,
        part3Count: p3,
        durationMinutes: savedAiExercise.durationMinutes || 45,
        isExam: false,
        isAiGenerated: true
      };
    }

    if (isChemistry) {
      return {
        id: 4,
        title: 'Hóa học 12 – Chuyên đề Este & Lipit',
        subject: 'Hóa học',
        category: 'exercise',
        categoryLabel: 'Bài tập rèn luyện',
        teacher: 'Trần Thị Mai',
        totalQuestions: 35,
        part1Count: 15,
        part2Count: 10,
        part3Count: 10,
        durationMinutes: 50,
        isExam: false
      };
    }

    return {
      id: 1,
      title: 'Đề thi khảo sát chất lượng - Môn Toán (THPT 2025)',
      subject: 'Toán học',
      category: 'exam',
      categoryLabel: 'Bài thi chính thức',
      teacher: 'Trần Văn B',
      totalQuestions: 40,
      part1Count: 15,
      part2Count: 15,
      part3Count: 10,
      durationMinutes: 45,
      isExam: true
    };
  }, [backendExercise, backendQuestions, savedAiExercise, isChemistry, location.state]);

  const totalQuestions = exerciseInfo.totalQuestions;

  // Active question index (0-indexed, default is Question 1)
  const [currentQuestionIdx, setCurrentQuestionIdx] = useState(0);
  
  // Dynamic answers dictionary
  const [answers, setAnswers] = useState({});

  const [flaggedQuestions, setFlaggedQuestions] = useState({});
  const [timeLeft, setTimeLeft] = useState(exerciseInfo.durationMinutes * 60);
  const [filterMode, setFilterMode] = useState('all'); // 'all', 'flagged'

  // Check if exam/exercise is already submitted in localStorage (strictly for local offline practice)
  const isBackendTarget = Boolean(
    (exerciseId && /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(exerciseId)) ||
    (stateAssignmentId && /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(stateAssignmentId)) ||
    (stateExerciseId && /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(stateExerciseId))
  );

  const savedSubmission = useMemo(() => {
    if (isBackendTarget) return null;
    try {
      const data = localStorage.getItem(`tk_exam_submitted_${currentExamId}`);
      return data ? JSON.parse(data) : null;
    } catch {
      return null;
    }
  }, [currentExamId, isBackendTarget]);

  // Submission & Exam Lock States
  const [isSubmitModalOpen, setIsSubmitModalOpen] = useState(false);
  const [isReadOnlyReview, setIsReadOnlyReview] = useState(Boolean(!isBackendTarget && savedSubmission));
  const [isExamSubmitted, setIsExamSubmitted] = useState(Boolean(!isBackendTarget && savedSubmission));
  const [submissionResult, setSubmissionResult] = useState(!isBackendTarget ? savedSubmission : null);
  const [attemptDetailedResults, setAttemptDetailedResults] = useState(null);

  // Restore student answers when in review mode
  useEffect(() => {
    if (!isBackendTarget && savedSubmission?.savedAnswers && Object.keys(savedSubmission.savedAnswers).length > 0) {
      setAnswers(savedSubmission.savedAnswers);
      setIsReadOnlyReview(true);
    }
    // Restore actual exam duration for review mode timer
    if (!isBackendTarget && savedSubmission?.totalTimeSeconds != null) {
      setTimeLeft(savedSubmission.totalTimeSeconds);
    }
  }, [savedSubmission, isBackendTarget]);

  // Autosave answers to sessionStorage so an expired session never loses student's work
  useEffect(() => {
    if (!isReadOnlyReview && !isExamSubmitted && answers && Object.keys(answers).length > 0) {
      try {
        sessionStorage.setItem(`tk_exam_draft_${currentExamId}`, JSON.stringify(answers));
      } catch (e) {}
    }
  }, [answers, currentExamId, isReadOnlyReview, isExamSubmitted]);

  // Restore draft answers on mount if available
  useEffect(() => {
    if (!isReadOnlyReview && Object.keys(answers).length === 0) {
      try {
        const savedDraft = sessionStorage.getItem(`tk_exam_draft_${currentExamId}`);
        if (savedDraft) {
          const parsed = JSON.parse(savedDraft);
          if (parsed && typeof parsed === 'object' && Object.keys(parsed).length > 0) {
            setAnswers(parsed);
          }
        }
      } catch (e) {}
    }
  }, [currentExamId, isReadOnlyReview]);

  // Timer countdown (only active when exam is not submitted)
  useEffect(() => {
    if (isExamSubmitted) return;
    const timer = setInterval(() => {
      setTimeLeft(prev => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(timer);
  }, [isExamSubmitted]);

  const formatTimer = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // Toggle flag for current question
  const toggleFlag = (index) => {
    if (isReadOnlyReview || isExamSubmitted) return;
    setFlaggedQuestions(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  // Handler for Multiple Choice 4 options
  const handleSelectOption = (qIdx, optionKey) => {
    if (isReadOnlyReview || isExamSubmitted) return;
    setAnswers(prev => ({
      ...prev,
      [qIdx]: optionKey
    }));
  };

  // Handler for True/False sub-item
  const handleSelectTrueFalse = (qIdx, subKey, boolVal) => {
    if (isReadOnlyReview || isExamSubmitted) return;
    setAnswers(prev => {
      const currentTF = prev[qIdx] && typeof prev[qIdx] === 'object' ? prev[qIdx] : {};
      return {
        ...prev,
        [qIdx]: {
          ...currentTF,
          [subKey]: boolVal
        }
      };
    });
  };

  // Handler to clear/reset answer for a question
  const handleClearAnswer = (qIdx) => {
    if (isReadOnlyReview || isExamSubmitted) return;
    setAnswers(prev => {
      const copy = { ...prev };
      delete copy[qIdx];
      return copy;
    });
  };

  // Anti-cheating & Fullscreen detection
  const [isFullscreen, setIsFullscreen] = useState(Boolean(document.fullscreenElement));
  const [showAntiCheatWarning, setShowAntiCheatWarning] = useState(false);

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(() => {});
      setIsFullscreen(true);
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen().catch(() => {});
        setIsFullscreen(false);
      }
    }
  };

  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden && !isExamSubmitted && !isReadOnlyReview) {
        setShowAntiCheatWarning(true);
      }
    };
    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, [isExamSubmitted, isReadOnlyReview]);

  // Clean and validate Short Answer (Max 4 chars, decimal comma only)
  const cleanShortAnswer = (val) => {
    if (!val) return '';
    let formatted = String(val).replace(/\./g, ',');
    formatted = formatted.replace(/[^0-9,-]/g, '');

    const isNegative = formatted.startsWith('-');
    formatted = formatted.replace(/-/g, '');
    if (isNegative) {
      formatted = '-' + formatted;
    }

    const commaIndex = formatted.indexOf(',');
    if (commaIndex !== -1) {
      formatted = formatted.substring(0, commaIndex + 1) + formatted.substring(commaIndex + 1).replace(/,/g, '');
    }

    return formatted.slice(0, 4);
  };

  // Handler for Short Answer text
  const handleShortAnswerChange = (qIdx, textVal) => {
    if (isReadOnlyReview || isExamSubmitted) return;
    const cleaned = cleanShortAnswer(textVal);
    setAnswers(prev => ({
      ...prev,
      [qIdx]: cleaned
    }));
  };

  // Numpad button click for Short Answer
  const handleNumpadPress = (char) => {
    if (isReadOnlyReview || isExamSubmitted) return;
    const currentVal = typeof answers[currentQuestionIdx] === 'string' ? answers[currentQuestionIdx] : '';
    
    if (char === 'CLEAR') {
      handleShortAnswerChange(currentQuestionIdx, '');
    } else if (char === 'BACKSPACE') {
      handleShortAnswerChange(currentQuestionIdx, currentVal.slice(0, -1));
    } else if (char === '-') {
      if (currentVal.startsWith('-')) {
        return;
      }
      if (currentVal === '') {
        handleShortAnswerChange(currentQuestionIdx, '-');
      } else if (currentVal.length < 4) {
        handleShortAnswerChange(currentQuestionIdx, '-' + currentVal);
      }
    } else if (char === '+') {
      if (currentVal.startsWith('-')) {
        handleShortAnswerChange(currentQuestionIdx, currentVal.substring(1));
      }
    } else if (char === ',') {
      if (!currentVal.includes(',') && currentVal.length < 4) {
        if (currentVal === '' || currentVal === '-') {
          handleShortAnswerChange(currentQuestionIdx, currentVal + '0,');
        } else {
          handleShortAnswerChange(currentQuestionIdx, currentVal + ',');
        }
      }
    } else {
      if (currentVal.length < 4) {
        handleShortAnswerChange(currentQuestionIdx, currentVal + char);
      }
    }
  };

  const handleNext = () => {
    if (currentQuestionIdx < totalQuestions - 1) {
      setCurrentQuestionIdx(prev => prev + 1);
    }
  };

  const handlePrev = () => {
    if (currentQuestionIdx > 0) {
      setCurrentQuestionIdx(prev => prev - 1);
    }
  };

  // Check if a question is answered
  const isQuestionAnswered = (qIdx) => {
    const ans = answers[qIdx];
    if (ans === undefined || ans === null) return false;
    if (typeof ans === 'string') return ans.trim().length > 0;
    if (typeof ans === 'object') return Object.keys(ans).length > 0;
    return false;
  };

  const answeredCount = Object.keys(answers).filter(k => isQuestionAnswered(Number(k)) && Number(k) < totalQuestions).length;
  const unansweredCount = totalQuestions - answeredCount;
  const flaggedCount = Object.keys(flaggedQuestions).filter(k => flaggedQuestions[k] && Number(k) < totalQuestions).length;
  const progressPercent = Math.round((answeredCount / totalQuestions) * 100);

  // Breakdown by Part
  const part1Answered = Array.from({ length: exerciseInfo.part1Count }, (_, i) => i).filter(i => isQuestionAnswered(i)).length;
  const part2Answered = Array.from({ length: exerciseInfo.part2Count }, (_, i) => i + exerciseInfo.part1Count).filter(i => isQuestionAnswered(i)).length;
  const part3Answered = Array.from({ length: exerciseInfo.part3Count }, (_, i) => i + exerciseInfo.part1Count + exerciseInfo.part2Count).filter(i => isQuestionAnswered(i)).length;

  // Open modal confirmation
  const handleOpenSubmitModal = () => {
    if (isExamSubmitted) return;
    setIsSubmitModalOpen(true);
  };

  // Confirm final submission (with Backend API support when attemptId is active)
  const handleConfirmSubmit = async () => {
    if (attemptId) {
      try {
        setIsSubmitting(true);
        const submitAnswers = [];

        backendQuestions.forEach((q, idx) => {
          const userAns = answers[idx];
          if (userAns !== undefined && userAns !== null) {
            const qType = normalizeQType(q.question_type);
            if (qType === 'SHORT_ANSWER') {
              if (userAns !== undefined && userAns !== null && String(userAns).trim() !== '') {
                submitAnswers.push({
                  question_id: q.question_id,
                  answer_text: String(userAns).trim().replace(/,/g, '.')
                });
              }
            } else if (qType === 'TRUE_FALSE') {
              if (typeof userAns === 'object') {
                const tfSummary = Object.entries(userAns).map(([k, v]) => `${k}:${v}`).join(';');
                submitAnswers.push({
                  question_id: q.question_id,
                  answer_text: tfSummary
                });
              }
            } else {
              const selectedLetter = userAns;
              const optIdx = ['A', 'B', 'C', 'D'].indexOf(selectedLetter);
              const sortedOptions = [...(q.answer_options || [])].sort((a, b) => (a.display_order || 0) - (b.display_order || 0));
              const matchedOpt = optIdx !== -1 && sortedOptions[optIdx] ? sortedOptions[optIdx] : null;
              if (matchedOpt) {
                submitAnswers.push({
                  question_id: q.question_id,
                  answer_option_id: matchedOpt.option_id
                });
              } else if (typeof userAns === 'string') {
                submitAnswers.push({
                  question_id: q.question_id,
                  answer_text: userAns
                });
              }
            }
          }
        });

        const currentToken = localStorage.getItem('access_token');
        if (!currentToken) {
          try {
            sessionStorage.setItem(`tk_exam_draft_${currentExamId}`, JSON.stringify(answers));
          } catch (e) {}
          alert('Phiên đăng nhập của bạn đã hết hạn. Các câu trả lời đã được lưu tạm, vui lòng đăng nhập lại để nộp bài.');
          window.location.href = '/login';
          return;
        }

        let targetAttemptId = attemptId;
        if (!targetAttemptId && isUuid(targetAssignmentId)) {
          try {
            const myAttempts = await attemptsApi.getAttempts();
            const open = (myAttempts || []).find(a => 
              String(a.assignment_id).toLowerCase() === String(targetAssignmentId).toLowerCase() && !a.is_finished
            );
            if (open) {
              targetAttemptId = open.attempt_id;
              setAttemptId(targetAttemptId);
            } else {
              const startRes = await attemptsApi.startAttempt(targetAssignmentId);
              targetAttemptId = startRes.attempt_id;
              setAttemptId(targetAttemptId);
            }
          } catch (lookupErr) {
            console.warn('Could not resolve open attempt before submit:', lookupErr);
          }
        }

        if (!targetAttemptId) {
          alert('Không tìm thấy phiên làm bài hợp lệ. Vui lòng tải lại trang.');
          return;
        }

        const submitRes = await attemptsApi.submitAttempt(targetAttemptId, { answers: submitAnswers });
        const score = submitRes?.score !== undefined && submitRes?.score !== null 
          ? Number(submitRes.score).toFixed(2) 
          : ((answeredCount / totalQuestions) * 10).toFixed(2);

        // Clear draft and exercises session cache on successful submit
        try {
          sessionStorage.removeItem(`tk_exam_draft_${currentExamId}`);
          let currentUserId = 'default';
          try {
            const rawUser = localStorage.getItem('user_info');
            if (rawUser) {
              const u = JSON.parse(rawUser);
              currentUserId = u.user_id || u.id || 'default';
            }
          } catch (e) {}
          sessionStorage.removeItem(`tk_student_assignments_session_${currentUserId}`);
          sessionStorage.removeItem(`tk_student_attempts_session_${currentUserId}`);
        } catch (e) {}

        const resultData = {
          submittedAt: new Date().toISOString(),
          formattedTime: new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }) + ' · ' + new Date().toLocaleDateString('vi-VN'),
          answeredCount,
          unansweredCount,
          flaggedCount,
          totalQuestions,
          score,
          isExam: exerciseInfo.isExam,
          title: exerciseInfo.title,
          attemptId: submitRes?.attempt_id || targetAttemptId,
          savedAnswers: { ...answers },
          detailedResults: submitRes?.detailed_results || null
        };

        setAttemptDetailedResults(submitRes?.detailed_results || null);
        setSubmissionResult(resultData);
        setIsExamSubmitted(true);
        setIsReadOnlyReview(false);
        setIsSubmitModalOpen(false);
      } catch (err) {
        console.error('Submit attempt failed:', err);
        const errDetail = err.response?.data?.detail;
        const msg = typeof errDetail === 'object' ? errDetail?.message : errDetail;
        if (err.response?.status === 401 || !localStorage.getItem('access_token')) {
          try {
            sessionStorage.setItem(`tk_exam_draft_${currentExamId}`, JSON.stringify(answers));
          } catch (e) {}
          alert('Phiên làm việc đã hết hạn. Các câu trả lời của bạn đã được lưu tạm, vui lòng đăng nhập lại để nộp bài.');
          window.location.href = '/login';
        } else {
          alert(msg || 'Có lỗi xảy ra khi nộp bài. Vui lòng thử lại.');
        }
      } finally {
        setIsSubmitting(false);
      }
      return;
    }

    // Local / AI practice exercise fallback submit
    const calculatedScore = ((answeredCount / totalQuestions) * 10).toFixed(2);
    const resultData = {
      submittedAt: new Date().toISOString(),
      formattedTime: new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }) + ' · ' + new Date().toLocaleDateString('vi-VN'),
      answeredCount,
      unansweredCount,
      flaggedCount,
      totalQuestions,
      score: calculatedScore,
      isExam: exerciseInfo.isExam,
      title: exerciseInfo.title,
      savedAnswers: { ...answers }
    };

    try {
      localStorage.setItem(`tk_exam_submitted_${currentExamId}`, JSON.stringify(resultData));
      if (stateAssignmentId) {
        localStorage.setItem(`tk_exam_submitted_${stateAssignmentId}`, JSON.stringify(resultData));
      }
    } catch (e) {
      console.error('Failed to save state', e);
    }

    setSubmissionResult(resultData);
    setIsExamSubmitted(true);
    setIsReadOnlyReview(false);
    setIsSubmitModalOpen(false);
  };

  // Allow retake for practice exercises (category === 'exercise')
  const handleRetakeExercise = () => {
    try {
      localStorage.removeItem(`tk_exam_submitted_${currentExamId}`);
    } catch (e) {
      console.error('Failed to remove state', e);
    }
    setAnswers({});
    setFlaggedQuestions({});
    setTimeLeft(exerciseInfo.durationMinutes * 60);
    setIsExamSubmitted(false);
    setIsReadOnlyReview(false);
    setSubmissionResult(null);
    setCurrentQuestionIdx(0);
  };

  // Question Dataset (Dynamic for Backend API vs Chemistry vs Math)
  const questionData = useMemo(() => {
    const qNum = currentQuestionIdx + 1;

    // 0. BACKEND LIVE QUESTIONS (When connected to real backend API)
    if (backendQuestions.length > 0 && backendQuestions[currentQuestionIdx]) {
      const bQ = backendQuestions[currentQuestionIdx];
      const normalizedType = normalizeQType(bQ.question_type);
      let qType = 'single_choice';
      let partLabel = 'Phần I: Trắc nghiệm 4 lựa chọn';

      if (normalizedType === 'TRUE_FALSE') {
        qType = 'true_false';
        partLabel = 'Phần II: Trắc nghiệm Đúng/Sai';
      } else if (normalizedType === 'SHORT_ANSWER') {
        qType = 'short_answer';
        partLabel = 'Phần III: Trả lời ngắn';
      }

      const qRes = attemptDetailedResults?.questions?.find(
        r => String(r.question_id).toLowerCase() === String(bQ.question_id).toLowerCase()
      );

      if (qType === 'single_choice') {
        const letters = ['A', 'B', 'C', 'D', 'E', 'F'];
        const options = (bQ.answer_options && bQ.answer_options.length > 0)
          ? bQ.answer_options.map((opt, oIdx) => {
              let text = opt.content || '';
              text = text.replace(/^[A-Da-d][\.\)]\s*/, '').trim();
              text = text.replace(/[\r\n\s\.]*[√✓\u221a]\s*$/, '').trim();
              text = text.replace(/[\r\n\s\.]*\(\s*\)\s*$/, '').trim();
              return {
                key: letters[oIdx] || String(oIdx + 1),
                text,
                optionId: opt.option_id,
                isCorrect: Boolean(opt.is_correct)
              };
            })
          : [
              { key: 'A', text: 'Phương án A', isCorrect: false },
              { key: 'B', text: 'Phương án B', isCorrect: false },
              { key: 'C', text: 'Phương án C', isCorrect: false },
              { key: 'D', text: 'Phương án D', isCorrect: false }
            ];
        return {
          id: bQ.question_id,
          part: partLabel,
          number: qNum,
          type: 'single_choice',
          statement: bQ.content || 'Nội dung câu hỏi',
          options,
          explanation: bQ.explanation,
          correctAnswer: bQ.correct_answer,
          isCorrect: qRes ? qRes.is_correct : (options.find(o => o.key === answers[currentQuestionIdx])?.isCorrect ?? null),
          qRes
        };
      } else if (qType === 'true_false') {
        const letters = ['a', 'b', 'c', 'd'];
        const items = (bQ.answer_options && bQ.answer_options.length > 0)
          ? bQ.answer_options.map((opt, oIdx) => {
              const letter = letters[oIdx] || String(oIdx + 1);
              let text = opt.content || '';
              text = text.replace(/^[a-dA-D][\.\)]\s*/, '').trim();
              text = text.replace(/[\r\n\s\.]*[√✓\u221a]\s*$/, '').trim();
              text = text.replace(/[\r\n\s\.]*\(\s*\)\s*$/, '').trim();
              return {
                key: letter,
                text,
                optionId: opt.option_id,
                isCorrect: Boolean(opt.is_correct)
              };
            })
          : [
              { key: 'a', text: 'Mệnh đề a', isCorrect: true },
              { key: 'b', text: 'Mệnh đề b', isCorrect: false },
              { key: 'c', text: 'Mệnh đề c', isCorrect: true },
              { key: 'd', text: 'Mệnh đề d', isCorrect: false }
            ];
        return {
          id: bQ.question_id,
          part: partLabel,
          number: qNum,
          type: 'true_false',
          statement: bQ.content || 'Nội dung câu hỏi Đúng/Sai',
          items,
          explanation: bQ.explanation,
          correctAnswer: bQ.correct_answer,
          isCorrect: qRes ? qRes.is_correct : null,
          qRes
        };
      } else {
        return {
          id: bQ.question_id,
          part: partLabel,
          number: qNum,
          type: 'short_answer',
          statement: bQ.content || 'Nội dung câu hỏi trả lời ngắn',
          explanation: bQ.explanation,
          correctAnswer: bQ.correct_answer,
          isCorrect: qRes ? qRes.is_correct : null,
          qRes
        };
      }
    }

    // CHEMISTRY 12 DATASET (Este & Lipit)
    if (isChemistry) {
      // Chemistry Part I: Trắc nghiệm 4 lựa chọn (1 - 15)
      if (currentQuestionIdx < 15) {
        const chemPart1 = [
          {
            title: 'Công thức tổng quát của este no, đơn chức, mạch hở là:',
            options: [
              { key: 'A', text: 'CnH2nO2 (n ≥ 2)' },
              { key: 'B', text: 'CnH2n+2O2 (n ≥ 1)' },
              { key: 'C', text: 'CnH2n-2O2 (n ≥ 3)' },
              { key: 'D', text: 'CnH2nO (n ≥ 2)' }
            ]
          },
          {
            title: 'Thủy phân etyl fomat (HCOOC2H5) trong dung dịch NaOH đun nóng thu được muối nào sau đây?',
            options: [
              { key: 'A', text: 'HCOONa' },
              { key: 'B', text: 'CH3COONa' },
              { key: 'C', text: 'C2H5COONa' },
              { key: 'D', text: 'CH3ONa' }
            ]
          },
          {
            title: 'Chất béo tristearin có công thức cấu tạo thu gọn là:',
            options: [
              { key: 'A', text: '(C17H35COO)3C3H5' },
              { key: 'B', text: '(C17H33COO)3C3H5' },
              { key: 'C', text: '(C15H31COO)3C3H5' },
              { key: 'D', text: '(C17H31COO)3C3H5' }
            ]
          },
          {
            title: 'Este nào sau đây có mùi thơm đặc trưng của quả chuối chín?',
            options: [
              { key: 'A', text: 'Isoamyl axetat' },
              { key: 'B', text: 'Etyl butirat' },
              { key: 'C', text: 'Benzyl axetat' },
              { key: 'D', text: 'Geranyl axetat' }
            ]
          },
          {
            title: 'Cho 8,8 gam etyl axetat (CH3COOC2H5) phản ứng hoàn toàn với dung dịch NaOH vừa đủ, đun nóng. Khối lượng muối natri axetat (CH3COONa) thu được là:',
            options: [
              { key: 'A', text: '8,2 gam' },
              { key: 'B', text: '6,8 gam' },
              { key: 'C', text: '16,4 gam' },
              { key: 'D', text: '10,2 gam' }
            ]
          },
          {
            title: 'Phản ứng giữa axit cacboxylic và ancol có xúc tác H2SO4 đặc, đun nóng được gọi là phản ứng:',
            options: [
              { key: 'A', text: 'Este hóa' },
              { key: 'B', text: 'Xà phòng hóa' },
              { key: 'C', text: 'Trùng hợp' },
              { key: 'D', text: 'Thủy phân kiềm' }
            ]
          },
          {
            title: 'Số đồng phân este đơn chức ứng với công thức phân tử C3H6O2 là:',
            options: [
              { key: 'A', text: '2 đồng phân' },
              { key: 'B', text: '3 đồng phân' },
              { key: 'C', text: '4 đồng phân' },
              { key: 'D', text: '1 đồng phân' }
            ]
          },
          {
            title: 'Chất béo nào sau đây ở trạng thái lỏng ở nhiệt độ phòng (25°C)?',
            options: [
              { key: 'A', text: 'Triolein' },
              { key: 'B', text: 'Tristearin' },
              { key: 'C', text: 'Tripanmitin' },
              { key: 'D', text: 'Axit stearic' }
            ]
          },
          {
            title: 'Thủy phân chất béo trong dung dịch kiềm (NaOH hoặc KOH) luôn thu được sản phẩm là muối của axit béo và:',
            options: [
              { key: 'A', text: 'Glixerol' },
              { key: 'B', text: 'Etylen glicol' },
              { key: 'C', text: 'Ancol etylic' },
              { key: 'D', text: 'Ancol metylic' }
            ]
          },
          {
            title: 'Vinyl axetat (CH3COOCH=CH2) được điều chế trực tiếp từ phản ứng giữa axit axetic và:',
            options: [
              { key: 'A', text: 'Axetilen (C2H2)' },
              { key: 'B', text: 'Etilen (C2H4)' },
              { key: 'C', text: 'Ancol vinylic' },
              { key: 'D', text: 'Ancol etylic' }
            ]
          },
          {
            title: 'Đốt cháy hoàn toàn 1 mol este no, đơn chức, mạch hở thu được tỉ lệ mol CO2 và H2O là:',
            options: [
              { key: 'A', text: 'nCO2 : nH2O = 1 : 1' },
              { key: 'B', text: 'nCO2 : nH2O = 2 : 1' },
              { key: 'C', text: 'nCO2 > nH2O' },
              { key: 'D', text: 'nCO2 < nH2O' }
            ]
          },
          {
            title: 'Dầu mỡ động thực vật để lâu ngày trong không khí thường bị ôi thiu do:',
            options: [
              { key: 'A', text: 'Gốc axit béo không no bị oxi hóa chậm bởi không khí tạo peoxit' },
              { key: 'B', text: 'Este bị thủy phân hoàn toàn thành axit fomic' },
              { key: 'C', text: 'Glixerol bị bay hơi hết' },
              { key: 'D', text: 'Chất béo bị trùng hợp thành nhựa' }
            ]
          },
          {
            title: 'Xà phòng hóa hoàn toàn 1 mol tripanmitin (C15H31COO)3C3H5 cần vừa đủ bao nhiêu mol NaOH?',
            options: [
              { key: 'A', text: '3 mol' },
              { key: 'B', text: '1 mol' },
              { key: 'C', text: '2 mol' },
              { key: 'D', text: '6 mol' }
            ]
          },
          {
            title: 'Chất nào sau đây có nhiệt độ sôi thấp nhất trong các chất có cùng số nguyên tử C?',
            options: [
              { key: 'A', text: 'Etyl fomat (HCOOC2H5)' },
              { key: 'B', text: 'Axit propionic (C2H5COOH)' },
              { key: 'C', text: 'Ancol propylic (C3H7OH)' },
              { key: 'D', text: 'Propylamin (C3H7NH2)' }
            ]
          },
          {
            title: 'Metyl metacrylat (CH2=C(CH3)COOCH3) là monome dùng để trùng hợp tạo ra:',
            options: [
              { key: 'A', text: 'Thủy tinh hữu cơ plexiglas' },
              { key: 'B', text: 'Cao su buna' },
              { key: 'C', text: 'Nilon-6,6' },
              { key: 'D', text: 'Tơ lapsan' }
            ]
          }
        ];

        const q = chemPart1[currentQuestionIdx % chemPart1.length];
        return {
          part: 'Phần I: Trắc nghiệm 4 lựa chọn',
          number: qNum,
          type: 'single_choice',
          statement: q.title,
          options: q.options
        };
      }

      // Chemistry / AI Part II: Trắc nghiệm Đúng/Sai
      if (currentQuestionIdx >= exerciseInfo.part1Count && currentQuestionIdx < exerciseInfo.part1Count + exerciseInfo.part2Count) {
        const chemPart2 = [
          {
            statement: 'Xét các phát biểu sau về tính chất của este và lipit:',
            items: [
              { key: 'a', text: 'Các este thường nhẹ hơn nước, ít tan trong nước và có mùi thơm hoa quả đặc trưng.' },
              { key: 'b', text: 'Phản ứng thủy phân este trong môi trường kiềm (xà phòng hóa) là phản ứng thuận nghịch.' },
              { key: 'c', text: 'Etyl fomat có khả năng tham gia phản ứng tráng gương tạo bạc kim loại Ag.' },
              { key: 'd', text: 'Nhiệt độ sôi của este cao hơn nhiệt độ sôi của axit cacboxylic có cùng khối lượng phân tử.' }
            ]
          },
          {
            statement: 'Cho các phát biểu về chất béo và lipit:',
            items: [
              { key: 'a', text: 'Chất béo là trieste của glixerol với các axit béo monocacboxylic mạch cacbon dài, không phân nhánh.' },
              { key: 'b', text: 'Triolein có công thức (C17H33COO)3C3H5 tồn tại ở trạng thái lỏng ở nhiệt độ thường.' },
              { key: 'c', text: 'Hiđro hóa hoàn toàn chất béo lỏng (xúc tác Ni, đun nóng) thu được chất béo rắn sản xuất bơ nhân tạo.' },
              { key: 'd', text: 'Dầu thực vật và dầu mỡ bôi trơn máy móc đều có bản chất hóa học là este của axit béo.' }
            ]
          },
          {
            statement: 'Tiến hành thí nghiệm điều chế etyl axetat trong phòng thí nghiệm:',
            items: [
              { key: 'a', text: 'Hỗn hợp phản ứng gồm ancol etylic nguyên chất, axit axetic nguyên chất và vài giọt H2SO4 đặc.' },
              { key: 'b', text: 'Axit sunfuric đặc vừa đóng vai trò chất xúc tác, vừa có tác dụng hút nước chuyển dịch cân bằng.' },
              { key: 'c', text: 'Sau khi đun cách thủy, thêm dung dịch NaCl bão hòa để este tách lớp nổi lên trên bề mặt.' },
              { key: 'd', text: 'Để tăng hiệu suất cần đun sôi mạnh hỗn hợp trên ngọn lửa đèn cồn trực tiếp không làm lạnh.' }
            ]
          }
        ];

        const q = chemPart2[(currentQuestionIdx - exerciseInfo.part1Count) % chemPart2.length];
        return {
          part: 'Phần II: Trắc nghiệm Đúng/Sai',
          number: qNum,
          type: 'true_false',
          statement: q.statement,
          items: q.items
        };
      }

      // Chemistry / AI Part III: Trả lời ngắn
      const chemPart3 = [
        { text: 'Cho 0,1 mol một este đơn chức X tác dụng vừa đủ với dung dịch NaOH thu được 6,8 gam muối natri fomat (HCOONa) và 4,6 gam một ancol Y. Khối lượng mol phân tử (M) của este X bằng bao nhiêu gam/mol?' },
        { text: 'Đốt cháy hoàn toàn 6,0 gam một este no, đơn chức, mạch hở X thu được 0,2 mol CO2. Số nguyên tử hiđro (H) trong một phân tử este X là bao nhiêu?' },
        { text: 'Xà phòng hóa hoàn toàn 17,8 gam tristearin (C17H35COO)3C3H5 bằng lượng vừa đủ dung dịch NaOH. Khối lượng (gam) glixerol thu được là bao nhiêu?' },
        { text: 'Cho 4,4 gam etyl axetat phản ứng hoàn toàn với 100 ml dung dịch NaOH 1M, đun nóng. Sau phản ứng, cô cạn dung dịch thu được bao nhiêu gam chất rắn khan?' },
        { text: 'Thủy phân hoàn toàn 8,9 gam chất béo triolein (C17H33COO)3C3H5 trong dung dịch KOH vừa đủ. Khối lượng (gam) KOH cần dùng là bao nhiêu?' },
        { text: 'Cho m gam etyl axetat tác dụng hoàn toàn với dung dịch NaOH vừa đủ thu được 8,2 gam muối natri axetat. Giá trị của m bằng bao nhiêu gam?' },
        { text: 'Đốt cháy hoàn toàn một este đơn chức X cần 0,35 mol O2, thu được 0,3 mol CO2 và 0,3 mol H2O. Số nguyên tử cacbon (C) trong phân tử X là bao nhiêu?' },
        { text: 'Thủy phân hoàn toàn 7,4 gam metyl axetat (CH3COOCH3) bằng 200 ml dung dịch KOH 1M. Cô cạn dung dịch sau phản ứng thu được bao nhiêu gam chất rắn khan?' },
        { text: 'Đun 12,0 gam axit axetic với 13,8 gam ancol etylic (xúc tác H2SO4 đặc) thu được 11,0 gam etyl axetat. Hiệu suất (%) của phản ứng este hóa là bao nhiêu %?' },
        { text: 'Hiđro hóa hoàn toàn 4,42 gam triolein (C17H33COO)3C3H5 cần vừa đủ bao nhiêu lít khí H2 ở điều kiện tiêu chuẩn (làm tròn 2 chữ số thập phân)?' }
      ];

      const q = chemPart3[(currentQuestionIdx - (exerciseInfo.part1Count + exerciseInfo.part2Count)) % chemPart3.length];
      return {
        part: 'Phần III: Trắc nghiệm Trả lời ngắn',
        number: qNum,
        type: 'short_answer',
        statement: q.text
      };
    }

    // MATH 12 DATASET (Đề thi Toán)
    const diagrams = {
      variationTable: (
        <div className="question-diagram-card">
          <svg className="diagram-svg-frame" width="480" height="150" viewBox="0 0 480 150">
            <rect x="10" y="10" width="460" height="130" rx="8" fill="#FAFAFD" stroke="#CBD5E1" strokeWidth="1.5" />
            <line x1="10" y1="48" x2="470" y2="48" stroke="#CBD5E1" strokeWidth="1.5" />
            <line x1="10" y1="84" x2="470" y2="84" stroke="#CBD5E1" strokeWidth="1.5" />
            <line x1="65" y1="10" x2="65" y2="140" stroke="#CBD5E1" strokeWidth="1.5" />
            
            <text x="35" y="34" fontSize="14" fontStyle="italic" fontWeight="700" fill="#4D308D" textAnchor="middle">x</text>
            <text x="35" y="70" fontSize="14" fontStyle="italic" fontWeight="700" fill="#4D308D" textAnchor="middle">y'</text>
            <text x="35" y="118" fontSize="14" fontStyle="italic" fontWeight="700" fill="#4D308D" textAnchor="middle">y</text>
            
            <text x="95" y="34" fontSize="13" fill="#334155" textAnchor="middle">-∞</text>
            <text x="195" y="34" fontSize="13" fontWeight="700" fill="#1E293B" textAnchor="middle">-1</text>
            <text x="315" y="34" fontSize="13" fontWeight="700" fill="#1E293B" textAnchor="middle">2</text>
            <text x="430" y="34" fontSize="13" fill="#334155" textAnchor="middle">+∞</text>
            
            <text x="145" y="70" fontSize="16" fontWeight="700" fill="#10B981" textAnchor="middle">+</text>
            <text x="195" y="70" fontSize="14" fill="#64748B" textAnchor="middle">0</text>
            <text x="255" y="70" fontSize="16" fontWeight="700" fill="#EF4444" textAnchor="middle">-</text>
            <text x="315" y="70" fontSize="14" fill="#64748B" textAnchor="middle">0</text>
            <text x="375" y="70" fontSize="16" fontWeight="700" fill="#10B981" textAnchor="middle">+</text>
            
            <text x="95" y="132" fontSize="12" fill="#64748B" textAnchor="middle">-∞</text>
            <text x="195" y="100" fontSize="13" fontWeight="700" fill="#4D308D" textAnchor="middle">5</text>
            <text x="315" y="134" fontSize="13" fontWeight="700" fill="#4D308D" textAnchor="middle">-4</text>
            <text x="430" y="100" fontSize="12" fill="#64748B" textAnchor="middle">+∞</text>
            
            <defs>
              <marker id="arrowY" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
                <path d="M 0 0 L 10 5 L 0 10 z" fill="#6549A6" />
              </marker>
            </defs>
            <line x1="110" y1="128" x2="182" y2="105" stroke="#6549A6" strokeWidth="1.8" markerEnd="url(#arrowY)" />
            <line x1="208" y1="105" x2="302" y2="128" stroke="#6549A6" strokeWidth="1.8" markerEnd="url(#arrowY)" />
            <line x1="328" y1="128" x2="415" y2="105" stroke="#6549A6" strokeWidth="1.8" markerEnd="url(#arrowY)" />
          </svg>
          <p className="diagram-caption">Hình 1: Bảng biến thiên của hàm số y = f(x)</p>
        </div>
      ),
      pyramid3D: (
        <div className="question-diagram-card">
          <svg className="diagram-svg-frame" width="340" height="200" viewBox="0 0 340 200">
            <polygon points="170,25 60,150 210,165 280,120" fill="#F8FAFC" stroke="#1E293B" strokeWidth="1.5" />
            <line x1="60" y1="150" x2="130" y2="105" stroke="#94A3B8" strokeWidth="1.2" strokeDasharray="4,4" />
            <line x1="130" y1="105" x2="280" y2="120" stroke="#94A3B8" strokeWidth="1.2" strokeDasharray="4,4" />
            <line x1="170" y1="25" x2="130" y2="105" stroke="#94A3B8" strokeWidth="1.2" strokeDasharray="4,4" />
            <line x1="170" y1="25" x2="170" y2="135" stroke="#EF4444" strokeWidth="1.5" strokeDasharray="3,3" />
            <text x="175" y="85" fontSize="12" fontWeight="700" fill="#EF4444">h = 2a</text>
            <text x="168" y="18" fontSize="13" fontWeight="700" fill="#1E1B4B">S</text>
            <text x="45" y="155" fontSize="13" fontWeight="700" fill="#1E1B4B">A</text>
            <text x="212" y="180" fontSize="13" fontWeight="700" fill="#1E1B4B">B</text>
            <text x="288" y="125" fontSize="13" fontWeight="700" fill="#1E1B4B">C</text>
            <text x="120" y="100" fontSize="13" fontWeight="700" fill="#1E1B4B">D</text>
          </svg>
          <p className="diagram-caption">Hình 2: Khối chóp S.ABCD có diện tích đáy B = 6a² và chiều cao h = 2a</p>
        </div>
      ),
      waterTank3D: (
        <div className="question-diagram-card">
          <svg className="diagram-svg-frame" width="320" height="180" viewBox="0 0 320 180">
            <polygon points="60,75 180,75 180,150 60,150" fill="#EFF6FF" stroke="#2563EB" strokeWidth="1.5" />
            <polygon points="180,75 250,35 250,110 180,150" fill="#DBEAFE" stroke="#2563EB" strokeWidth="1.5" />
            <polygon points="60,75 130,35 250,35 180,75" fill="#BFDBFE" stroke="#2563EB" strokeWidth="1.5" />
            <text x="115" y="165" fontSize="13" fontWeight="700" fontStyle="italic" fill="#1E293B" textAnchor="middle">x</text>
            <text x="225" y="138" fontSize="13" fontWeight="700" fontStyle="italic" fill="#1E293B" textAnchor="middle">x</text>
            <text x="45" y="115" fontSize="13" fontWeight="700" fontStyle="italic" fill="#2563EB" textAnchor="middle">h</text>
            <text x="150" y="110" fontSize="12" fontWeight="700" fill="#1E40AF" textAnchor="middle">V = 32 m³</text>
          </svg>
          <p className="diagram-caption">Hình 3: Mô hình bể nước đáy hình vuông cạnh x và chiều cao h</p>
        </div>
      ),
      cubicGraph: (
        <div className="question-diagram-card">
          <svg className="diagram-svg-frame" width="380" height="190" viewBox="0 0 380 190">
            <line x1="30" y1="100" x2="350" y2="100" stroke="#1E293B" strokeWidth="1.5" markerEnd="url(#arrow)" />
            <line x1="190" y1="175" x2="190" y2="20" stroke="#1E293B" strokeWidth="1.5" markerEnd="url(#arrow)" />
            <text x="355" y="104" fontSize="12" fontStyle="italic">x</text>
            <text x="185" y="15" fontSize="12" fontStyle="italic">y</text>
            <text x="178" y="114" fontSize="11">O</text>
            <path d="M 70,170 C 130,-10 160,20 190,100 C 220,180 250,210 310,30" fill="none" stroke="#6549A6" strokeWidth="2.2" />
            <circle cx="135" cy="45" r="3.5" fill="#EF4444" />
            <text x="110" y="40" fontSize="11" fill="#EF4444">(-1; 2)</text>
            <circle cx="245" cy="155" r="3.5" fill="#EF4444" />
            <text x="250" y="165" fontSize="11" fill="#EF4444">(1; -2)</text>
          </svg>
          <p className="diagram-caption">Hình 4: Đồ thị hàm số bậc ba y = f(x)</p>
        </div>
      )
    };

    // PART I: Trắc nghiệm 4 lựa chọn (1 - 15)
    if (currentQuestionIdx < 15) {
      const p1Data = [
        {
          title: 'Cho hàm số y = f(x) có bảng biến thiên như hình vẽ. Hàm số đã cho đạt cực đại tại điểm nào dưới đây?',
          diagram: diagrams.variationTable,
          options: [
            { key: 'A', text: 'x = -1' },
            { key: 'B', text: 'x = 2' },
            { key: 'C', text: 'x = 5' },
            { key: 'D', text: 'x = -4' }
          ]
        },
        {
          title: 'Tiệm cận ngang của đồ thị hàm số y = (2x - 1) / (x + 3) là đường thẳng có phương trình:',
          options: [
            { key: 'A', text: 'y = 2' },
            { key: 'B', text: 'x = -3' },
            { key: 'C', text: 'y = -3' },
            { key: 'D', text: 'x = 2' }
          ]
        },
        {
          title: 'Cho đồ thị hàm số bậc ba y = f(x) như hình vẽ bên dưới. Điểm cực tiểu của đồ thị hàm số là:',
          diagram: diagrams.cubicGraph,
          options: [
            { key: 'A', text: '(1; -2)' },
            { key: 'B', text: '(-1; 2)' },
            { key: 'C', text: 'x = 1' },
            { key: 'D', text: 'y = -2' }
          ]
        },
        {
          title: 'Thể tích của khối chóp có diện tích đáy B = 6a² và chiều cao h = 2a bằng:',
          diagram: diagrams.pyramid3D,
          options: [
            { key: 'A', text: 'V = 4a³' },
            { key: 'B', text: 'V = 12a³' },
            { key: 'C', text: 'V = 6a³' },
            { key: 'D', text: 'V = 2a³' }
          ]
        },
        {
          title: 'Trong không gian Oxyz, cho mặt cầu (S): (x - 1)² + (y + 2)² + (z - 3)² = 16. Tọa độ tâm I và bán kính R của (S) là:',
          options: [
            { key: 'A', text: 'I(1; -2; 3), R = 4' },
            { key: 'B', text: 'I(-1; 2; -3), R = 4' },
            { key: 'C', text: 'I(1; -2; 3), R = 16' },
            { key: 'D', text: 'I(-1; 2; -3), R = 16' }
          ]
        }
      ];

      const q = p1Data[currentQuestionIdx % p1Data.length];
      return {
        part: 'Phần I: Trắc nghiệm 4 lựa chọn',
        number: qNum,
        type: 'single_choice',
        statement: q.title,
        diagram: q.diagram,
        options: q.options
      };
    }

    // PART II: Trắc nghiệm Đúng / Sai
    if (currentQuestionIdx >= 15 && currentQuestionIdx < 15 + exerciseInfo.part2Count) {
      return {
        part: 'Phần II: Trắc nghiệm Đúng/Sai',
        number: qNum,
        type: 'true_false',
        statement: `Cho hàm số y = f(x) = x³ - 3x² + 2 có bảng biến thiên và đồ thị như hình vẽ. Xét tính đúng hay sai của các mệnh đề sau:`,
        diagram: diagrams.cubicGraph,
        items: [
          { key: 'a', text: 'Hàm số đã cho đồng biến trên các khoảng (-∞; 0) và (2; +∞).' },
          { key: 'b', text: 'Giá trị cực đại của hàm số bằng 2, đạt được tại x = 0.' },
          { key: 'c', text: 'Điểm uốn của đồ thị hàm số có tọa độ là I(1; 0).' },
          { key: 'd', text: 'Phương trình f(x) = m có 3 nghiệm thực phân biệt khi và chỉ khi -2 < m < 2.' }
        ]
      };
    }

    // PART III: Trả lời ngắn
    const shortAnswerSamples = [
      {
        text: 'Một bể chứa nước hình hộp chữ nhật có đáy là hình vuông cạnh x (mét) và chiều cao h (mét). Biết thể tích bể là 32 m³. Tìm giá trị cạnh đáy x (mét) để diện tích toàn phần của bể chứa là nhỏ nhất.',
        diagram: diagrams.waterTank3D
      },
      {
        text: 'Tìm giá trị lớn nhất của hàm số f(x) = x³ - 3x + 2 trên đoạn [0; 2].',
        diagram: diagrams.cubicGraph
      },
      {
        text: 'Trong không gian Oxyz, cho khối chóp tứ giác S.ABCD có thể tích V = 48. Tính chiều cao h của khối chóp biết diện tích đáy B = 12.',
        diagram: diagrams.pyramid3D
      }
    ];

    const sItem = shortAnswerSamples[(currentQuestionIdx - (15 + exerciseInfo.part2Count)) % shortAnswerSamples.length];
    return {
      part: 'Phần III: Trắc nghiệm Trả lời ngắn',
      number: qNum,
      type: 'short_answer',
      statement: sItem.text,
      diagram: sItem.diagram
    };
  }, [currentQuestionIdx, isChemistry, exerciseInfo, backendQuestions, attemptDetailedResults, answers]);

  const getQuestionReviewStatus = (qIdx) => {
    if (!isReadOnlyReview) return null;
    if (backendQuestions.length > 0 && backendQuestions[qIdx]) {
      const bQ = backendQuestions[qIdx];
      const qRes = attemptDetailedResults?.questions?.find(
        r => String(r.question_id).toLowerCase() === String(bQ.question_id).toLowerCase()
      );
      if (qRes && qRes.is_correct !== null && qRes.is_correct !== undefined) {
        return qRes.is_correct ? 'correct' : 'wrong';
      }
      const normType = normalizeQType(bQ.question_type);
      if (normType === 'MULTIPLE_CHOICE') {
        const userKey = answers[qIdx];
        if (!userKey) return 'wrong';
        const letters = ['A', 'B', 'C', 'D', 'E', 'F'];
        const optIdx = letters.indexOf(userKey);
        if (optIdx !== -1 && bQ.answer_options?.[optIdx]?.is_correct) {
          return 'correct';
        }
        return 'wrong';
      } else if (normType === 'TRUE_FALSE') {
        const userTF = answers[qIdx];
        if (!userTF || typeof userTF !== 'object' || Object.keys(userTF).length === 0) return 'wrong';
        const answerOpts = bQ.answer_options || [];
        if (answerOpts.length > 0) {
          const isAllCorrect = answerOpts.every((opt, oIdx) => {
            const key = ['a', 'b', 'c', 'd'][oIdx] || String(oIdx + 1);
            return userTF[key] === Boolean(opt.is_correct);
          });
          return isAllCorrect ? 'correct' : 'wrong';
        }
        return 'wrong';
      } else if (normType === 'SHORT_ANSWER') {
        const userVal = answers[qIdx];
        if (!userVal) return 'wrong';
        const correctAns = bQ.correct_answer;
        if (correctAns) {
          const normUser = String(userVal).trim().replace(',', '.');
          const normCorr = String(correctAns).trim().replace(',', '.');
          return normUser === normCorr ? 'correct' : 'wrong';
        }
        return 'wrong';
      }
    }
    const val = answers[qIdx];
    if (val !== undefined && val !== null && val !== '') {
      if (typeof val === 'string' && val.toUpperCase() === 'A') {
        return 'correct';
      }
      return 'wrong';
    }
    return null;
  };

  if (isLoadingBackend) {
    return (
      <div className="exercise-taking-container" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100vh', background: '#F8FAFC' }}>
        <Loader2 size={40} className="animate-spin" style={{ animation: 'spin 1s linear infinite', color: '#2563EB', marginBottom: '16px' }} />
        <p style={{ color: '#475569', fontSize: '15px', fontWeight: 500 }}>Đang tải đề thi và phiên làm bài...</p>
      </div>
    );
  }

  return (
    <div className="exercise-taking-container">
      {/* 1. Top Navbar */}
      <header className="exam-top-navbar">
        <div className="exam-nav-left">
          <Link to="/student" className="exam-brand-logo">
            Academic Clarity
          </Link>
          <div className="exam-nav-divider" />
          <span className="exam-title-text">{exerciseInfo.title}</span>
        </div>

        <div className="exam-nav-right">
          <div className={`exam-timer-pill ${isExamSubmitted ? 'timer-finished' : ''}`}>
            <Clock size={16} className="timer-icon" />
            <span>{isExamSubmitted ? `Đã làm: ${formatTimer(timeLeft)}` : formatTimer(timeLeft)}</span>
          </div>
          <button 
            type="button" 
            className="exam-icon-btn btn-fullscreen-toggle" 
            aria-label="Toàn màn hình" 
            title={isFullscreen ? "Thoát toàn màn hình" : "Chế độ toàn màn hình"}
            onClick={toggleFullscreen}
          >
            {isFullscreen ? <Minimize2 size={18} /> : <Maximize2 size={18} />}
          </button>
          <button type="button" className="exam-icon-btn" aria-label="Help" title="Hướng dẫn làm bài">
            <HelpCircle size={20} />
          </button>
          <button type="button" className="exam-icon-btn" aria-label="Settings" title="Cài đặt giao diện">
            <Settings size={20} />
          </button>
        </div>
      </header>

      {/* 2. Main Workspace Body */}
      <div className="exam-workspace-body">
        {/* Left Palette Sidebar */}
        <aside className="exam-palette-sidebar">
          <div>
            <h3 className="palette-header-title">MỤC LỤC CÂU HỎI</h3>

            {isReadOnlyReview && (
              <div className="palette-review-legend">
                <div className="legend-item"><span className="legend-dot dot-correct" /><span>Đúng</span></div>
                <div className="legend-item"><span className="legend-dot dot-wrong" /><span>Sai / Chưa làm</span></div>
              </div>
            )}

            {/* Filter Toggle Actions */}
            <div className="palette-filter-actions">
              <button 
                type="button" 
                className={`palette-action-btn ${filterMode === 'flagged' ? 'active' : ''}`}
                onClick={() => setFilterMode(prev => prev === 'flagged' ? 'all' : 'flagged')}
              >
                <Flag size={14} fill={filterMode === 'flagged' ? '#DC2626' : 'none'} />
                <span>
                  {filterMode === 'flagged' ? 'Tất cả câu hỏi' : `Đã gắn cờ (${Object.values(flaggedQuestions).filter(Boolean).length})`}
                </span>
              </button>
            </div>

            {/* Flagged Filter Status Banner */}
            {filterMode === 'flagged' && (
              <div className="palette-flagged-banner">
                <div className="flagged-banner-left">
                  <span className="flagged-banner-dot" />
                  <span>Đang lọc: {Object.values(flaggedQuestions).filter(Boolean).length} câu gắn cờ</span>
                </div>
                <button 
                  type="button" 
                  className="flagged-banner-clear" 
                  onClick={() => setFilterMode('all')}
                  title="Hiện tất cả câu hỏi"
                >
                  Xóa lọc
                </button>
              </div>
            )}

            {/* Empty state when filtering flagged but no questions are flagged */}
            {filterMode === 'flagged' && Object.values(flaggedQuestions).filter(Boolean).length === 0 ? (
              <div className="palette-empty-flagged">
                <div className="empty-flag-icon-wrap">
                  <Flag size={24} className="empty-flag-icon" />
                </div>
                <h4 className="empty-flag-title">Chưa có câu gắn cờ</h4>
                <p className="empty-flag-desc">
                  Nhấn nút <strong>"Đánh dấu để xem lại"</strong> ở đầu mỗi câu hỏi để lưu vào danh sách này.
                </p>
                <button 
                  type="button" 
                  className="btn-back-all-questions" 
                  onClick={() => setFilterMode('all')}
                >
                  Xem tất cả câu hỏi
                </button>
              </div>
            ) : (
              /* Question Groups */
              <div className="palette-sections-list">
                {/* Group 1: Trắc nghiệm 4 lựa chọn */}
                {exerciseInfo.part1Count > 0 && (
                  <div className="palette-section-group">
                    <span className="palette-section-label">Trắc nghiệm 4 lựa chọn ({exerciseInfo.part1Count})</span>
                    <div className="palette-buttons-grid">
                      {Array.from({ length: exerciseInfo.part1Count }, (_, i) => {
                        const qNum = i + 1;
                        const isAns = isQuestionAnswered(i);
                        const isFlagged = Boolean(flaggedQuestions[i]);
                        const isActive = currentQuestionIdx === i;
                        const isDimmed = filterMode === 'flagged' && !isFlagged;
                        const reviewStatus = getQuestionReviewStatus(i);
                        return (
                          <button
                            key={qNum}
                            type="button"
                            className={`palette-num-btn ${isActive ? 'active' : ''} ${isAns ? 'answered' : ''} ${isFlagged ? 'flagged' : ''} ${isDimmed ? 'dimmed' : ''} ${reviewStatus ? `review-${reviewStatus}` : ''}`}
                            onClick={() => setCurrentQuestionIdx(i)}
                            title={`Câu ${qNum}${reviewStatus === 'correct' ? ' (Đúng)' : reviewStatus === 'wrong' ? ' (Sai)' : ''}${isFlagged ? ' (Đã gắn cờ)' : ''}`}
                          >
                            {qNum}
                            {isReadOnlyReview && reviewStatus ? (
                              <span className={`review-dot ${reviewStatus}`} />
                            ) : (
                              isAns && !isActive && <span className="answered-dot" />
                            )}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Group 2: Trắc nghiệm Đúng/Sai */}
                {exerciseInfo.part2Count > 0 && (
                  <div className="palette-section-group">
                    <span className="palette-section-label">Trắc nghiệm Đúng/Sai ({exerciseInfo.part2Count})</span>
                    <div className="palette-buttons-grid">
                      {Array.from({ length: exerciseInfo.part2Count }, (_, i) => {
                        const qIdx = i + exerciseInfo.part1Count;
                        const qNum = qIdx + 1;
                        const isAns = isQuestionAnswered(qIdx);
                        const isFlagged = Boolean(flaggedQuestions[qIdx]);
                        const isActive = currentQuestionIdx === qIdx;
                        const isDimmed = filterMode === 'flagged' && !isFlagged;
                        const reviewStatus = getQuestionReviewStatus(qIdx);
                        return (
                          <button
                            key={qNum}
                            type="button"
                            className={`palette-num-btn ${isActive ? 'active' : ''} ${isAns ? 'answered' : ''} ${isFlagged ? 'flagged' : ''} ${isDimmed ? 'dimmed' : ''} ${reviewStatus ? `review-${reviewStatus}` : ''}`}
                            onClick={() => setCurrentQuestionIdx(qIdx)}
                            title={`Câu ${qNum}${reviewStatus === 'correct' ? ' (Đúng)' : reviewStatus === 'wrong' ? ' (Sai)' : ''}${isFlagged ? ' (Đã gắn cờ)' : ''}`}
                          >
                            {qNum}
                            {isReadOnlyReview && reviewStatus ? (
                              <span className={`review-dot ${reviewStatus}`} />
                            ) : (
                              isAns && !isActive && <span className="answered-dot" />
                            )}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Group 3: Trả lời ngắn */}
                {exerciseInfo.part3Count > 0 && (
                  <div className="palette-section-group">
                    <span className="palette-section-label">Trả lời ngắn ({exerciseInfo.part3Count})</span>
                    <div className="palette-buttons-grid">
                      {Array.from({ length: exerciseInfo.part3Count }, (_, i) => {
                        const qIdx = i + exerciseInfo.part1Count + exerciseInfo.part2Count;
                        const qNum = qIdx + 1;
                        const isAns = isQuestionAnswered(qIdx);
                        const isFlagged = Boolean(flaggedQuestions[qIdx]);
                        const isActive = currentQuestionIdx === qIdx;
                        const isDimmed = filterMode === 'flagged' && !isFlagged;
                        const reviewStatus = getQuestionReviewStatus(qIdx);
                        return (
                          <button
                            key={qNum}
                            type="button"
                            className={`palette-num-btn ${isActive ? 'active' : ''} ${isAns ? 'answered' : ''} ${isFlagged ? 'flagged' : ''} ${isDimmed ? 'dimmed' : ''} ${reviewStatus ? `review-${reviewStatus}` : ''}`}
                            onClick={() => setCurrentQuestionIdx(qIdx)}
                            title={`Câu ${qNum}${reviewStatus === 'correct' ? ' (Đúng)' : reviewStatus === 'wrong' ? ' (Sai)' : ''}${isFlagged ? ' (Đã gắn cờ)' : ''}`}
                          >
                            {qNum}
                            {isReadOnlyReview && reviewStatus ? (
                              <span className={`review-dot ${reviewStatus}`} />
                            ) : (
                              isAns && !isActive && <span className="answered-dot" />
                            )}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Submit Button on Sidebar Bottom */}
          <button 
            type="button" 
            disabled={isExamSubmitted}
            className={`btn-submit-exam-sidebar ${isExamSubmitted ? 'submitted-locked' : ''}`}
            onClick={!isExamSubmitted ? handleOpenSubmitModal : undefined}
            title={isExamSubmitted ? 'Bài đã được nộp thành công' : undefined}
          >
            {isExamSubmitted ? (
              exerciseInfo.isExam ? (
                <>
                  <Lock size={15} />
                  <span>Đã nộp (Đã khóa)</span>
                </>
              ) : (
                <>
                  <CheckCircle2 size={15} />
                  <span>Đã nộp bài tập</span>
                </>
              )
            ) : (
              <>
                <span>{exerciseInfo.isExam ? 'Nộp bài thi' : 'Nộp bài tập'}</span>
                <ArrowRight size={16} />
              </>
            )}
          </button>
        </aside>

        {/* Center Question Viewport */}
        <main className="exam-question-viewport">
          {/* Readonly Review Banner */}
          {isExamSubmitted && isReadOnlyReview && (
            <div className={`exam-readonly-banner ${!exerciseInfo.isExam ? 'banner-practice' : ''}`}>
              <div className="readonly-banner-text">
                {exerciseInfo.isExam ? <Lock size={15} className="lock-icon" /> : <Sparkles size={15} className="practice-icon" />}
                <span>
                  <strong>{exerciseInfo.isExam ? 'Chế độ xem lại bài thi:' : 'Chế độ xem lại bài tập:'}</strong> {exerciseInfo.isExam ? `Đã nộp thành công lúc ${submissionResult?.formattedTime || 'trước đó'}. Bài thi này không cho phép làm lại.` : `Đã nộp lúc ${submissionResult?.formattedTime || 'trước đó'}. Bạn có thể bấm "Làm lại bài tập" bất cứ lúc nào.`}
                </span>
              </div>
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                <button
                  type="button"
                  className="btn-banner-view-score"
                  onClick={() => setIsReadOnlyReview(false)}
                  title="Xem lại bảng điểm và kết quả tổng quan"
                >
                  <Eye size={14} />
                  <span>Xem bảng điểm & tổng quan</span>
                </button>
                {!exerciseInfo.isExam && (
                  <button 
                    type="button" 
                    className="btn-exit-review-badge"
                    style={{ background: '#F1F5F9', color: '#334155' }}
                    onClick={handleRetakeExercise}
                    title="Xóa lượt thi cũ để làm lại bài"
                  >
                    <RotateCcw size={14} />
                    <span>Làm lại bài</span>
                  </button>
                )}
                <button 
                  type="button" 
                  className="btn-exit-review-badge"
                  onClick={() => navigate('/student/exercises')}
                >
                  <span>Về Kho bài tập</span>
                  <ArrowRight size={14} />
                </button>
              </div>
            </div>
          )}

          <div className="question-card-panel">
            {/* Question Top Header */}
            <div className="question-card-header">
              <div className="question-header-left">
                <span className="question-section-pill">{questionData.part}</span>
                <span className="question-number-badge">
                  Câu {questionData.number}
                </span>
              </div>
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                {!isReadOnlyReview && !isExamSubmitted && answers[currentQuestionIdx] !== undefined && (
                  <button 
                    type="button" 
                    className="btn-clear-answer"
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      padding: '6px 12px',
                      borderRadius: '8px',
                      border: '1px solid #E2E8F0',
                      background: '#FFFFFF',
                      color: '#64748B',
                      fontSize: '13px',
                      fontWeight: 500,
                      cursor: 'pointer'
                    }}
                    onClick={() => handleClearAnswer(currentQuestionIdx)}
                    title="Xóa lựa chọn đáp án câu này"
                  >
                    <RotateCcw size={14} />
                    <span>Xóa đáp án</span>
                  </button>
                )}
                <button 
                  type="button" 
                  disabled={isReadOnlyReview}
                  className={`btn-flag-review ${flaggedQuestions[currentQuestionIdx] ? 'flagged' : ''} ${isReadOnlyReview ? 'readonly' : ''}`}
                  onClick={() => toggleFlag(currentQuestionIdx)}
                >
                  <Flag size={15} fill={flaggedQuestions[currentQuestionIdx] ? '#DC2626' : 'none'} />
                  <span>
                    {flaggedQuestions[currentQuestionIdx] ? 'Đã gắn cờ xem lại' : 'Đánh dấu để xem lại'}
                  </span>
                </button>
              </div>
            </div>

            {/* Question Statement */}
            <div className="question-statement-text">
              <MathRenderer text={questionData.statement} />
            </div>

            {/* Dynamic Diagram */}
            {questionData.diagram ? (
              questionData.diagram
            ) : null}

            {/* ============================================================ */}
            {/* TYPE 1: MULTIPLE CHOICE 4 OPTIONS */}
            {/* ============================================================ */}
            {questionData.type === 'single_choice' && (
              <div className="question-options-wrapper">
                <h4 className="question-prompt-label">Chọn 01 đáp án đúng:</h4>
                <div className="question-options-grid">
                  {questionData.options.map((opt) => {
                    const isSelected = answers[currentQuestionIdx] === opt.key;
                    const isCorrectOpt = opt.isCorrect === true || (questionData.correctAnswer && String(questionData.correctAnswer).toUpperCase() === opt.key);
                    let reviewClass = '';
                    if (isReadOnlyReview) {
                      if (isCorrectOpt) {
                        reviewClass = 'review-correct-option';
                      } else if (isSelected && !isCorrectOpt) {
                        reviewClass = 'review-wrong-option';
                      }
                    }

                    return (
                      <div
                        key={opt.key}
                        className={`option-select-box ${isSelected ? 'selected' : ''} ${isReadOnlyReview ? 'readonly-option' : ''} ${reviewClass}`}
                        onClick={() => !isReadOnlyReview && handleSelectOption(currentQuestionIdx, opt.key)}
                      >
                        <div className="option-letter-badge">
                          {isReadOnlyReview && isCorrectOpt ? (
                            <Check size={16} className="opt-status-icon correct-icon" />
                          ) : isReadOnlyReview && isSelected && !isCorrectOpt ? (
                            <X size={16} className="opt-status-icon wrong-icon" />
                          ) : (
                            opt.key
                          )}
                        </div>
                        <span className="option-content-text">
                          <MathRenderer text={(opt.text || '').replace(/^[A-Da-d][\.\)]\s*/, '').trim()} />
                        </span>
                        {isReadOnlyReview && isCorrectOpt && (
                          <span className="review-badge-tag correct-tag">Đáp án đúng</span>
                        )}
                        {isReadOnlyReview && isSelected && !isCorrectOpt && (
                          <span className="review-badge-tag wrong-tag">Lựa chọn của bạn</span>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* ============================================================ */}
            {/* TYPE 2: TRUE / FALSE MULTIPLE ITEMS */}
            {/* ============================================================ */}
            {questionData.type === 'true_false' && (
              <div className="question-tf-wrapper">
                <div className="tf-header-bar">
                  <h4 className="question-prompt-label">Xét tính Đúng / Sai của từng mệnh đề dưới đây:</h4>
                  <span className="tf-guide-note">
                    {isReadOnlyReview ? 'Xem lại kết quả Đúng/Sai đối chiếu với đáp án chuẩn' : 'Chọn một phương án [Đúng] hoặc [Sai] cho mỗi ý'}
                  </span>
                </div>

                <div className="tf-items-list">
                  {questionData.items.map((item) => {
                    const userChoice = answers[currentQuestionIdx] && typeof answers[currentQuestionIdx] === 'object'
                      ? answers[currentQuestionIdx][item.key]
                      : undefined;
                    const correctVal = item.isCorrect;
                    const isAnswered = userChoice !== undefined && userChoice !== null;
                    const isUserCorrect = isReadOnlyReview && isAnswered && correctVal !== undefined
                      ? (userChoice === correctVal)
                      : false;

                    let rowReviewClass = '';
                    if (isReadOnlyReview) {
                      rowReviewClass = isUserCorrect ? 'tf-review-correct' : 'tf-review-wrong';
                    }

                    return (
                      <div key={item.key} className={`tf-item-row ${isAnswered ? 'has-answer' : ''} ${rowReviewClass}`}>
                        <div className="tf-item-content">
                          <span className="tf-sub-key-badge">{item.key})</span>
                          <span className="tf-sub-text">
                            <MathRenderer text={(item.text || '').replace(/^[a-dA-D][\.\)]\s*/, '').replace(/[\r\n\s\.]*[√✓\u221a]\s*$/, '').replace(/[\r\n\s\.]*\(\s*\)\s*$/, '').trim()} />
                          </span>
                          {isReadOnlyReview && correctVal !== undefined && (
                            <span className={`tf-key-verdict-pill ${correctVal ? 'pill-true' : 'pill-false'}`}>
                              Đáp án chuẩn: {correctVal ? 'Đúng' : 'Sai'}
                            </span>
                          )}
                        </div>

                        <div className="tf-toggle-actions">
                          <button
                            type="button"
                            disabled={isReadOnlyReview}
                            className={`tf-btn btn-true ${
                              isReadOnlyReview
                                ? userChoice === true
                                  ? isUserCorrect
                                    ? 'active user-correct'
                                    : 'active user-wrong'
                                  : 'faded'
                                : userChoice === true
                                ? 'active'
                                : ''
                            }`}
                            onClick={() => !isReadOnlyReview && handleSelectTrueFalse(currentQuestionIdx, item.key, true)}
                          >
                            {isReadOnlyReview && userChoice === true ? (
                              isUserCorrect ? <CheckCircle2 size={16} /> : <XCircle size={16} />
                            ) : (
                              <CheckCircle2 size={16} />
                            )}
                            <span>Đúng</span>
                          </button>

                          <button
                            type="button"
                            disabled={isReadOnlyReview}
                            className={`tf-btn btn-false ${
                              isReadOnlyReview
                                ? userChoice === false
                                  ? isUserCorrect
                                    ? 'active user-correct'
                                    : 'active user-wrong'
                                  : 'faded'
                                : userChoice === false
                                ? 'active'
                                : ''
                            }`}
                            onClick={() => !isReadOnlyReview && handleSelectTrueFalse(currentQuestionIdx, item.key, false)}
                          >
                            {isReadOnlyReview && userChoice === false ? (
                              isUserCorrect ? <CheckCircle2 size={16} /> : <XCircle size={16} />
                            ) : (
                              <XCircle size={16} />
                            )}
                            <span>Sai</span>
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* ============================================================ */}
            {/* TYPE 3: SHORT ANSWER INPUT */}
            {/* ============================================================ */}
            {questionData.type === 'short_answer' && (
              <div className="question-short-answer-wrapper">
                <div className="short-answer-header-row">
                  <h4 className="question-prompt-label">Điền câu trả lời ngắn của bạn:</h4>
                  <span className="short-answer-rule-badge">Tối đa 4 ký tự • Phân tách thập phân bằng dấu ","</span>
                </div>

                <div className="short-answer-layout">
                  {/* Left: Input Box, 4-cell slots & Instructions */}
                  <div className="short-answer-input-side">
                    <div className="short-answer-input-container">
                      <span className="short-answer-prefix">Kết quả =</span>
                      <input 
                        type="text" 
                        maxLength={4}
                        readOnly={isReadOnlyReview}
                        className="short-answer-input-field" 
                        placeholder="VD: 3,75 hoặc -2,5"
                        value={typeof answers[currentQuestionIdx] === 'string' ? answers[currentQuestionIdx] : ''}
                        onChange={(e) => handleShortAnswerChange(currentQuestionIdx, e.target.value)}
                      />
                      <span className="char-count-pill">
                        {String(answers[currentQuestionIdx] || '').length}/4
                      </span>
                      {answers[currentQuestionIdx] && !isReadOnlyReview && (
                        <button 
                          type="button" 
                          className="btn-clear-input"
                          onClick={() => handleShortAnswerChange(currentQuestionIdx, '')}
                          title="Xóa kết quả"
                        >
                          <Delete size={16} />
                        </button>
                      )}
                    </div>

                    {/* 4 Optical Grid Slot Indicators */}
                    <div className="short-answer-slots-preview">
                      <span className="slots-label">Khung hiển thị 4 ô ký tự:</span>
                      <div className="slots-cells-row">
                        {[0, 1, 2, 3].map((slotIdx) => {
                          const strVal = String(answers[currentQuestionIdx] || '');
                          const charAtSlot = strVal[slotIdx] || '';
                          const isFilled = Boolean(charAtSlot);
                          return (
                            <div 
                              key={slotIdx} 
                              className={`slot-cell-box ${isFilled ? 'filled' : ''} ${strVal.length === slotIdx && !isReadOnlyReview ? 'active-typing' : ''}`}
                            >
                              <span className="slot-index-hint">Ô {slotIdx + 1}</span>
                              <span className="slot-char-val">{charAtSlot || '·'}</span>
                            </div>
                          );
                        })}
                      </div>
                    </div>

                    <div className="short-answer-note-box">
                      <Info size={16} className="note-icon" />
                      <div className="note-text">
                        <strong>Quy tắc ghi đáp án trả lời ngắn:</strong>
                        <p>• Câu trả lời chỉ chứa tối đa <strong>4 ký tự</strong> (kể cả dấu âm <code>-</code> và dấu phẩy <code>,</code>).</p>
                        <p>• Ký tự số thập phân được phân chia bằng dấu phẩy <strong><code>,</code></strong> (Ví dụ: <code>3,75</code>, <code>-2,5</code>, <code>120</code>, <code>-14</code>).</p>
                        <p>• Nếu gõ dấu chấm <code>.</code>, hệ thống sẽ tự động chuyển thành dấu phẩy <code>,</code>.</p>
                      </div>
                    </div>
                  </div>

                  {/* Right: Quick Virtual Numpad */}
                  <div className="virtual-numpad-card">
                    <div className="numpad-header">
                      <Hash size={14} />
                      <span>Bàn phím số nhanh</span>
                    </div>
                    <div className="numpad-grid">
                      {['7', '8', '9', '4', '5', '6', '1', '2', '3', '+', '0', '-'].map((k) => (
                        <button
                          key={k}
                          type="button"
                          disabled={isReadOnlyReview}
                          className={`numpad-key-btn ${k === '+' ? 'key-plus' : ''} ${k === '-' ? 'key-minus' : ''}`}
                          onClick={() => handleNumpadPress(k)}
                        >
                          {k}
                        </button>
                      ))}
                      <button
                        type="button"
                        disabled={isReadOnlyReview}
                        className="numpad-key-btn key-comma"
                        onClick={() => handleNumpadPress(',')}
                        title="Dấu phẩy phân tách thập phân"
                      >
                        ,
                      </button>
                      <button
                        type="button"
                        disabled={isReadOnlyReview}
                        className="numpad-key-btn key-backspace"
                        onClick={() => handleNumpadPress('BACKSPACE')}
                        title="Xóa ký tự cuối (Backspace)"
                      >
                        <Delete size={15} />
                        <span style={{ fontSize: '11.5px' }}>Xóa</span>
                      </button>
                      <button
                        type="button"
                        disabled={isReadOnlyReview}
                        className="numpad-key-btn key-clear"
                        onClick={() => handleNumpadPress('CLEAR')}
                        title="Xóa toàn bộ kết quả"
                      >
                        <RotateCcw size={14} />
                      </button>
                    </div>
                  </div>
                </div>

                {isReadOnlyReview && (
                  <div className="short-answer-review-comparison">
                    <div className={`comparison-box student-ans-box ${
                      questionData.correctAnswer && answers[currentQuestionIdx]
                        ? String(answers[currentQuestionIdx]).trim().replace(',', '.') === String(questionData.correctAnswer).trim().replace(',', '.')
                          ? 'sa-correct'
                          : 'sa-wrong'
                        : 'sa-wrong'
                    }`}>
                      <span className="comparison-label">Câu trả lời của bạn:</span>
                      <span className="comparison-value">{answers[currentQuestionIdx] || '(Chưa trả lời)'}</span>
                    </div>
                    {questionData.correctAnswer && (
                      <div className="comparison-box correct-ans-box">
                        <span className="comparison-label">Đáp án chuẩn của đề:</span>
                        <span className="comparison-value">{questionData.correctAnswer}</span>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* Explanation & Solution Guide in Review Mode */}
            {isReadOnlyReview && (questionData.explanation || questionData.solutionGuide) && (
              <div className="review-solution-guide-card">
                <div className="solution-guide-header">
                  <Lightbulb size={18} className="guide-bulb-icon" />
                  <span className="guide-title">Lời giải chi tiết & Phương pháp giải</span>
                </div>
                <div className="solution-guide-body">
                  <MathRenderer text={questionData.explanation || questionData.solutionGuide} />
                </div>
              </div>
            )}
          </div>
        </main>
      </div>

      {/* 3. Bottom Fixed Navbar */}
      <footer className="exam-bottom-navbar">
        <div className="exam-progress-group">
          <span className="progress-label-text">
            Tiến độ hoàn thành: <strong>{answeredCount}</strong>/{totalQuestions} ({progressPercent}%)
          </span>
          <div className="progress-track-bar">
            <div 
              className="progress-filled-bar" 
              style={{ width: `${progressPercent}%` }} 
            />
          </div>
        </div>

        <div className="exam-nav-buttons-row">
          <button 
            type="button" 
            className="btn-nav-prev"
            disabled={currentQuestionIdx === 0}
            onClick={handlePrev}
          >
            <ArrowLeft size={16} />
            <span>Câu trước</span>
          </button>
          <button 
            type="button" 
            className="btn-nav-next"
            disabled={currentQuestionIdx === totalQuestions - 1}
            onClick={handleNext}
          >
            <span>Câu tiếp theo</span>
            <ArrowRight size={16} />
          </button>
        </div>
      </footer>

      {/* ============================================================ */}
      {/* 4. ANTI-CHEATING WARNING MODAL */}
      {/* ============================================================ */}
      {showAntiCheatWarning && (
        <div className="exam-modal-backdrop" onClick={() => setShowAntiCheatWarning(false)}>
          <div className="exam-submit-modal-card" style={{ maxWidth: '480px' }} onClick={(e) => e.stopPropagation()}>
            <div className="submit-modal-header" style={{ borderBottom: 'none', paddingBottom: 0 }}>
              <div className="modal-header-info">
                <div className="modal-icon-badge" style={{ background: '#FEE2E2', color: '#DC2626' }}>
                  <ShieldAlert size={24} />
                </div>
                <div>
                  <h3 className="modal-heading-title" style={{ color: '#991B1B' }}>
                    Cảnh báo chống gian lận thi cử!
                  </h3>
                  <p className="modal-heading-sub">Phát hiện rời khỏi màn hình làm bài</p>
                </div>
              </div>
            </div>
            <div style={{ padding: '16px 24px', color: '#475569', fontSize: '14px', lineHeight: 1.6 }}>
              <p>
                Hệ thống giám sát ghi nhận bạn vừa chuyển sang cửa sổ hoặc ứng dụng khác. 
                Vui lòng duy trì chế độ tập trung toàn màn hình để đảm bảo tính công bằng và tính hợp lệ của bài thi.
              </p>
            </div>
            <div className="submit-modal-actions" style={{ padding: '16px 24px', background: '#F8FAFC', borderTop: '1px solid #E2E8F0', display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
              <button
                type="button"
                className="btn-confirm-submit-modal"
                style={{ background: '#DC2626', color: '#FFFFFF' }}
                onClick={() => {
                  setShowAntiCheatWarning(false);
                  toggleFullscreen();
                }}
              >
                Tôi đã hiểu & Tiếp tục làm bài
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ============================================================ */}
      {/* 5. CONFIRMATION SUBMIT MODAL DIALOG */}
      {/* ============================================================ */}
      {isSubmitModalOpen && (
        <div className="exam-modal-backdrop" onClick={() => setIsSubmitModalOpen(false)}>
          <div className="exam-submit-modal-card" onClick={(e) => e.stopPropagation()}>
            {/* Modal Top Header */}
            <div className="submit-modal-header">
              <div className="modal-header-info">
                <div className="modal-icon-badge">
                  <Send size={20} />
                </div>
                <div>
                  <h3 className="modal-heading-title">
                    {exerciseInfo.isExam ? 'Xác nhận nộp bài thi' : 'Xác nhận nộp bài tập'}
                  </h3>
                  <p className="modal-heading-sub">{exerciseInfo.title} ({exerciseInfo.totalQuestions} câu / {exerciseInfo.durationMinutes} phút)</p>
                </div>
              </div>
              <button 
                type="button" 
                className="btn-close-modal"
                onClick={() => setIsSubmitModalOpen(false)}
                title="Đóng"
              >
                <X size={18} />
              </button>
            </div>

            {/* Quick Analytics Grid */}
            <div className="modal-analytics-grid">
              <div className="modal-stat-box box-answered">
                <div className="stat-box-icon">
                  <CheckCircle2 size={18} />
                </div>
                <div className="stat-box-data">
                  <span className="stat-box-num">{answeredCount}/{totalQuestions}</span>
                  <span className="stat-box-desc">Câu đã làm</span>
                </div>
              </div>

              <div className={`modal-stat-box ${unansweredCount > 0 ? 'box-unanswered' : 'box-clean'}`}>
                <div className="stat-box-icon">
                  <AlertCircle size={18} />
                </div>
                <div className="stat-box-data">
                  <span className="stat-box-num">{unansweredCount}</span>
                  <span className="stat-box-desc">Câu chưa làm</span>
                </div>
              </div>

              <div className="modal-stat-box box-flagged">
                <div className="stat-box-icon">
                  <Flag size={18} />
                </div>
                <div className="stat-box-data">
                  <span className="stat-box-num">{flaggedCount}</span>
                  <span className="stat-box-desc">Đang gắn cờ</span>
                </div>
              </div>

              <div className="modal-stat-box box-time">
                <div className="stat-box-icon">
                  <Clock size={18} />
                </div>
                <div className="stat-box-data">
                  <span className="stat-box-num">{formatTimer(timeLeft)}</span>
                  <span className="stat-box-desc">Thời gian còn</span>
                </div>
              </div>
            </div>

            {/* Progress Breakdown across 3 Parts */}
            <div className="modal-parts-progress-card">
              <span className="parts-progress-title">Tiến độ chi tiết từng phần bài làm:</span>
              <div className="parts-progress-list">
                <div className="part-progress-item">
                  <div className="part-progress-info">
                    <span>Phần I: Trắc nghiệm 4 lựa chọn</span>
                    <strong>{part1Answered}/{exerciseInfo.part1Count} câu</strong>
                  </div>
                  <div className="part-bar-track">
                    <div className="part-bar-fill fill-purple" style={{ width: `${(part1Answered / exerciseInfo.part1Count) * 100}%` }} />
                  </div>
                </div>

                <div className="part-progress-item">
                  <div className="part-progress-info">
                    <span>Phần II: Trắc nghiệm Đúng / Sai</span>
                    <strong>{part2Answered}/{exerciseInfo.part2Count} câu</strong>
                  </div>
                  <div className="part-bar-track">
                    <div className="part-bar-fill fill-indigo" style={{ width: `${(part2Answered / exerciseInfo.part2Count) * 100}%` }} />
                  </div>
                </div>

                <div className="part-progress-item">
                  <div className="part-progress-info">
                    <span>Phần III: Trả lời ngắn</span>
                    <strong>{part3Answered}/{exerciseInfo.part3Count} câu</strong>
                  </div>
                  <div className="part-bar-track">
                    <div className="part-bar-fill fill-violet" style={{ width: `${(part3Answered / exerciseInfo.part3Count) * 100}%` }} />
                  </div>
                </div>
              </div>
            </div>

            {/* Strict Exam vs Regular Practice Notice */}
            {exerciseInfo.isExam ? (
              <div className="modal-strict-policy-notice">
                <ShieldAlert size={22} className="policy-notice-icon" />
                <div className="policy-notice-body">
                  <strong>Quy chế bài thi chính thức:</strong>
                  <p>
                    Đây là <strong>Bài thi</strong> (khác với bài tập rèn luyện). Sau khi xác nhận nộp bài, hệ thống sẽ tự động khóa và <strong>KHÔNG CHO PHÉP LÀM LẠI</strong>.
                  </p>
                </div>
              </div>
            ) : (
              <div className="modal-practice-policy-notice">
                <Sparkles size={22} className="policy-notice-icon-practice" />
                <div className="policy-notice-body-practice">
                  <strong>Lưu ý bài tập rèn luyện:</strong>
                  <p>
                    Đây là <strong>Bài tập thông thường</strong>. Sau khi nộp bài, hệ thống sẽ chấm điểm chi tiết và bạn <strong>HOÀN TOÀN CÓ THỂ LÀM LẠI / LUYỆN TẬP LẠI</strong> nhiều lần để nâng cao kết quả.
                  </p>
                </div>
              </div>
            )}

            {/* Modal Bottom Actions */}
            <div className="modal-submit-actions">
              <button
                type="button"
                className="btn-modal-back-check"
                onClick={() => setIsSubmitModalOpen(false)}
              >
                <ArrowLeft size={16} />
                <span>Tiếp tục làm bài</span>
              </button>

              <button
                type="button"
                className="btn-modal-final-submit"
                onClick={handleConfirmSubmit}
              >
                <span>{exerciseInfo.isExam ? 'Xác nhận nộp bài thi' : 'Xác nhận nộp bài tập'}</span>
                <Send size={16} />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ============================================================ */}
      {/* 5. SUBMITTED RESULT / EXAM LOCKED FULLSCREEN OVERLAY */}
      {/* ============================================================ */}
      {isExamSubmitted && !isReadOnlyReview && (
        <div className="exam-submitted-overlay-screen">
          <div className="submitted-result-modal-box">
            <div className={`submitted-success-sparkle-icon ${!exerciseInfo.isExam ? 'practice-icon-glow' : ''}`}>
              <CheckCircle2 size={48} />
            </div>

            {exerciseInfo.isExam ? (
              <div className="submitted-lock-badge">
                <Lock size={13} />
                <span>Bài thi đã hoàn thành • Không cho phép làm lại</span>
              </div>
            ) : (
              <div className="submitted-practice-badge">
                <Sparkles size={13} />
                <span>Bài tập đã nộp • Cho phép làm lại không giới hạn</span>
              </div>
            )}

            <h2 className="submitted-success-title">
              {exerciseInfo.isExam ? 'Nộp bài thi thành công!' : 'Nộp bài tập thành công!'}
            </h2>
            <p className="submitted-success-desc">
              {exerciseInfo.isExam 
                ? 'Bài làm của bạn đã được ghi nhận an toàn vào hệ thống khảo sát.' 
                : `Bạn đã hoàn thành bài tập "${exerciseInfo.title}". Hệ thống đã chấm điểm tự động.`}
            </p>

            {/* Summary Stat Tiles */}
            <div className="submitted-result-tiles-row">
              <div className="result-tile-card">
                <span className="tile-label">Số câu đã làm</span>
                <span className="tile-value">{submissionResult?.answeredCount || answeredCount}/{totalQuestions}</span>
                <span className="tile-sub">({Math.round(((submissionResult?.answeredCount || answeredCount) / totalQuestions) * 100)}% hoàn thành)</span>
              </div>

              <div className="result-tile-card highlight-card">
                <span className="tile-label">Điểm đạt được</span>
                <span className="tile-value score-text">{submissionResult?.score || ((answeredCount / totalQuestions) * 10).toFixed(2)}</span>
                <span className="tile-sub">Thang điểm 10.0</span>
              </div>

              <div className="result-tile-card">
                <span className="tile-label">Thời điểm nộp</span>
                <span className="tile-value time-text">{submissionResult?.formattedTime || 'Vừa xong'}</span>
                <span className="tile-sub">Đã lưu kết quả</span>
              </div>
            </div>

            <div className={`submitted-guidance-card ${!exerciseInfo.isExam ? 'practice-guidance' : ''}`}>
              <Info size={18} className="guidance-icon" />
              <span>
                {exerciseInfo.isExam 
                  ? 'Theo quy chế, bài thi không thể làm lại. Điểm chính thức và lời giải chi tiết sẽ được giáo viên công bố sau khi hết hạn làm bài.'
                  : 'Đây là bài tập rèn luyện. Bạn có thể xem lại bài làm hoặc bấm "Làm lại bài tập" để luyện tập thêm.'}
              </span>
            </div>

            {/* Action Buttons */}
            <div className="submitted-actions-flex">
              {!exerciseInfo.isExam && (
                <button
                  type="button"
                  className="btn-retake-exam-active"
                  onClick={handleRetakeExercise}
                >
                  <RotateCcw size={16} />
                  <span>Làm lại bài tập</span>
                </button>
              )}

              <button
                type="button"
                className="btn-view-answers-readonly"
                onClick={() => setIsReadOnlyReview(true)}
              >
                <Eye size={16} />
                <span>Xem lại bài làm</span>
              </button>

              <button
                type="button"
                className="btn-return-exercises-hub"
                onClick={() => navigate('/student/exercises')}
              >
                <span>Về Kho bài tập</span>
                <ArrowRight size={16} />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
