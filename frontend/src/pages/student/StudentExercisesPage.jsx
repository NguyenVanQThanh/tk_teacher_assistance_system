// File Name: StudentExercisesPage.jsx
// Description: Student exercise repository page connected to backend assignments feed, with tabs (active, overdue, completed), subject and title search filtering, briefing cards, and AI exercise generator modal.
// Created At: 2026-09-07
// Created By: Tam Khang
// Updated At: 2026-10-04
// Updated By: Tam Khang

import React, { useState, useEffect, useMemo } from 'react';
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
  RotateCcw,
  Loader2,
  Search
} from 'lucide-react';
import { classesApi, assignmentsApi, attemptsApi, subjectsApi, exercisesApi } from '../../services/api';
import './StudentExercisesPage.css';

// Helper to format deadline preserving exact date & time without unwanted UTC shifts
export const formatDeadline = (dueAtStr) => {
  if (!dueAtStr) return 'Không có';
  try {
    if (typeof dueAtStr === 'string' && dueAtStr.includes('T')) {
      const [datePart, rawTime] = dueAtStr.split('T');
      const [y, m, d] = datePart.split('-');
      const timePart = (rawTime || '').replace('Z', '').split('.')[0];
      const [hh, mm] = timePart.split(':');
      if (d && m && y && hh && mm) {
        return `${hh}:${mm} ${d}/${m}/${y}`;
      }
    }
    const d = new Date(dueAtStr);
    return isNaN(d.getTime()) ? 'Không có' : d.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
  } catch (e) {
    return 'Không có';
  }
};

export default function StudentExercisesPage() {
  const navigate = useNavigate();
  const [selectedTab, setSelectedTab] = useState('all'); // 'all', 'active', 'overdue', 'completed'
  const [searchTitle, setSearchTitle] = useState('');
  const [selectedSubject, setSelectedSubject] = useState('all');
  const [selectedType, setSelectedType] = useState('all');
  const [availableSubjects, setAvailableSubjects] = useState([]);
  const [selectedExerciseDetail, setSelectedExerciseDetail] = useState(null);
  const [selectedAttemptId, setSelectedAttemptId] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [backendAssignments, setBackendAssignments] = useState([]);
  const [backendAttempts, setBackendAttempts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [localAiExercisesTrigger, setLocalAiExercisesTrigger] = useState(0);

  // Real backend detail & attempt history state
  const [detailSummary, setDetailSummary] = useState(null);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);

  // Fetch real assignment result summary & attempts when modal opens
  useEffect(() => {
    let isMounted = true;
    async function fetchDetailSummary() {
      if (!selectedExerciseDetail) {
        setDetailSummary(null);
        return;
      }
      const isUuid = (id) => typeof id === 'string' && /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(id);
      const targetAssignmentId = selectedExerciseDetail.assignment_id || selectedExerciseDetail.exercise_id || selectedExerciseDetail.id;

      if (isUuid(targetAssignmentId)) {
        try {
          setIsLoadingDetail(true);
          const data = await assignmentsApi.getAssignmentResult(targetAssignmentId);
          if (isMounted && data) {
            setDetailSummary(data);
            if (data.best_attempt?.id || data.best_attempt?.attempt_id) {
              setSelectedAttemptId(data.best_attempt.id || data.best_attempt.attempt_id);
            } else if (data.latest_attempt?.id || data.latest_attempt?.attempt_id) {
              setSelectedAttemptId(data.latest_attempt.id || data.latest_attempt.attempt_id);
            } else if (data.attempts?.length > 0) {
              setSelectedAttemptId(data.attempts[data.attempts.length - 1].id || data.attempts[data.attempts.length - 1].attempt_id);
            }
          }
        } catch (err) {
          console.warn('Could not fetch assignment result from BE:', err);
          if (isMounted) {
            setDetailSummary(null);
          }
        } finally {
          if (isMounted) {
            setIsLoadingDetail(false);
          }
        }
      } else {
        setDetailSummary(null);
      }
    }

    fetchDetailSummary();

    return () => {
      isMounted = false;
    };
  }, [selectedExerciseDetail]);

  // Dynamic Attempts dataset reflecting real completions
  const activeAttempts = useMemo(() => {
    if (detailSummary && Array.isArray(detailSummary.attempts)) {
      return detailSummary.attempts.filter(att => 
        att.is_finished !== false && (att.score != null || att.score_val != null)
      );
    }
    // Fallback to attempts from backendAssignments/backendAttempts for this assignment
    if (selectedExerciseDetail) {
      const targetAssignmentId = String(selectedExerciseDetail.assignment_id || selectedExerciseDetail.id || '').toLowerCase();
      const matched = backendAttempts.filter(att => 
        String(att.assignment_id || '').toLowerCase() === targetAssignmentId &&
        att.is_finished && att.score != null
      );
      if (matched.length > 0) {
        return matched.map((att, idx) => {
          const scoreVal = Number(att.score);
          const totalQ = selectedExerciseDetail.total_questions || parseInt(selectedExerciseDetail.questionsCount) || 2;
          const correctCount = Math.round((scoreVal / 10) * totalQ);
          return {
            id: att.attempt_id || att.id || idx + 1,
            attempt_id: att.attempt_id || att.id,
            attempt_num: idx + 1,
            badge_label: `Lần ${idx + 1}${idx === matched.length - 1 ? ' (Mới nhất)' : ''}`,
            date_text: att.end_time ? formatDeadline(att.end_time) : (att.created_at ? formatDeadline(att.created_at) : 'Vừa xong'),
            status_tag: 'Đã chấm điểm',
            status_tag_class: 'attempt-status-tag-outline-green',
            score: scoreVal,
            score_label: `KẾT QUẢ (LẦN ${idx + 1})`,
            grade: scoreVal >= 8 ? 'Giỏi' : scoreVal >= 6.5 ? 'Khá' : scoreVal >= 5 ? 'Trung bình' : 'Yếu',
            correct_count: correctCount,
            total_count: totalQ,
            correct_pct: `${Math.round((correctCount / totalQ) * 100)}%`,
            time_spent: (() => {
              let sec = att.total_time_seconds;
              const limitMin = selectedExerciseDetail.duration_minutes || parseInt(selectedExerciseDetail.duration) || 45;
              if (sec && limitMin && sec > limitMin * 60) {
                sec = limitMin * 60;
              }
              return sec ? `${Math.floor(sec / 60)} phút${sec % 60 > 0 ? ' ' + (sec % 60) + ' giây' : ''}` : (selectedExerciseDetail.duration || '45 phút');
            })(),
            cognitive: {
              recognition: { correct: correctCount, total: totalQ, pct: `${Math.round((correctCount / totalQ) * 100)}%` },
              understanding: { correct: 0, total: 0, pct: '0%' },
              application: { correct: 0, total: 0, pct: '0%' }
            }
          };
        });
      }
      // Check localStorage submission (strictly for local AI practice exercises that are not in DB)
      if (selectedExerciseDetail.isAiGenerated && !selectedExerciseDetail.isRealBackend) {
        const localKeyId = selectedExerciseDetail.id || selectedExerciseDetail.assignment_id || selectedExerciseDetail.exercise_id;
        const rawSaved = localStorage.getItem(`tk_exam_submitted_${localKeyId}`) ||
                         (selectedExerciseDetail.exercise_id && localStorage.getItem(`tk_exam_submitted_${selectedExerciseDetail.exercise_id}`)) ||
                         (selectedExerciseDetail.assignment_id && localStorage.getItem(`tk_exam_submitted_${selectedExerciseDetail.assignment_id}`));
        if (rawSaved) {
          try {
            const parsed = JSON.parse(rawSaved);
            const scoreVal = parsed.score != null ? Number(parsed.score) : 10.0;
            const totalQ = parsed.totalQuestions || selectedExerciseDetail.totalQuestions || selectedExerciseDetail.total_questions || 4;
            const correctCount = parsed.answeredCount != null ? Number(parsed.answeredCount) : Math.round((scoreVal / 10) * totalQ);
            const recTot = Math.max(1, Math.round(totalQ * 0.5));
            const compTot = Math.max(1, Math.round(totalQ * 0.3));
            const appTot = Math.max(0, totalQ - recTot - compTot);
            const recCor = Math.min(recTot, correctCount);
            const compCor = Math.min(compTot, Math.max(0, correctCount - recCor));
            const appCor = Math.min(appTot, Math.max(0, correctCount - recCor - compCor));

            return [{
              id: parsed.attemptId || 'local_1',
              attempt_id: parsed.attemptId || 'local_1',
              attempt_num: 1,
              badge_label: 'Lần 1 (Mới nhất)',
              is_latest: true,
              is_best: true,
              date_text: parsed.formattedTime || 'Vừa xong',
              status_tag: 'Đã chấm điểm',
              status_tag_class: 'attempt-status-tag-outline-green',
              score: scoreVal,
              score_label: 'KẾT QUẢ CAO NHẤT (LẦN 1)',
              grade: scoreVal >= 8 ? 'Giỏi' : scoreVal >= 6.5 ? 'Khá' : scoreVal >= 5 ? 'Trung bình' : 'Yếu',
              correct_count: correctCount,
              total_count: totalQ,
              correct_pct: `${Math.round((correctCount / totalQ) * 100)}%`,
              time_spent: parsed.totalTimeSeconds ? `${Math.floor(parsed.totalTimeSeconds / 60)} phút ${parsed.totalTimeSeconds % 60} giây` : (selectedExerciseDetail.duration || '45 phút'),
              cognitive: {
                recognition: { correct: recCor, total: recTot, pct: `${Math.round((recCor / recTot) * 100)}%` },
                understanding: { correct: compCor, total: compTot, pct: `${Math.round((compCor / compTot) * 100)}%` },
                application: { correct: appCor, total: appTot, pct: `${appTot > 0 ? Math.round((appCor / appTot) * 100) : 0}%` }
              }
            }];
          } catch (e) {
            console.error('Error parsing local attempt in modal:', e);
          }
        }
      }
    }
    return [];
  }, [detailSummary, selectedExerciseDetail, backendAttempts]);

  const currentAttempt = useMemo(() => {
    if (activeAttempts.length > 0) {
      const found = activeAttempts.find(a => 
        String(a.id || a.attempt_id) === String(selectedAttemptId)
      );
      return found || detailSummary?.best_attempt || detailSummary?.latest_attempt || activeAttempts[activeAttempts.length - 1];
    }
    return null;
  }, [activeAttempts, selectedAttemptId, detailSummary]);

  const defaultSeeds = useMemo(() => [
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
  ], []);

  // Debounced search title for backend query
  const [debouncedSearch, setDebouncedSearch] = useState('');
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedSearch(searchTitle);
    }, 250);
    return () => clearTimeout(handler);
  }, [searchTitle]);

  const [tabCounts, setTabCounts] = useState({ all: 0, active: 0, overdue: 0, completed: 0 });

  // Fetch real backend assignments and attempts for student (scoped to DB query params)
  useEffect(() => {
    let isMounted = true;
    async function loadData() {
      try {
        setLoading(true);

        const params = {};
        if (selectedTab && selectedTab !== 'all') {
          params.tab = selectedTab;
        }
        if (selectedSubject && selectedSubject !== 'all') {
          const matchedSub = (availableSubjects || []).find(s => s.subject_name === selectedSubject);
          if (matchedSub?.subject_id) {
            params.subject_id = matchedSub.subject_id;
          }
        }
        if (debouncedSearch.trim()) {
          params.search = debouncedSearch.trim();
        }

        const [assignmentsRes, allUnfilteredRes, attemptsRes, subjectsRes] = await Promise.allSettled([
          assignmentsApi.getAssignments(params),
          assignmentsApi.getAssignments(),
          attemptsApi.getAttempts().catch(() => []),
          availableSubjects.length === 0 ? subjectsApi.getSubjects().catch(() => []) : Promise.resolve(availableSubjects),
        ]);

        const studentAttempts = attemptsRes.status === 'fulfilled' && Array.isArray(attemptsRes.value) ? attemptsRes.value : [];
        if (isMounted) {
          setBackendAttempts(studentAttempts);
        }

        if (subjectsRes.status === 'fulfilled' && Array.isArray(subjectsRes.value)) {
          setAvailableSubjects(subjectsRes.value);
        }

        // Accurately compute tab counts from all active assignments in DB + local AI exercises
        if (allUnfilteredRes.status === 'fulfilled' && Array.isArray(allUnfilteredRes.value)) {
          let active = 0;
          let overdue = 0;
          let completed = 0;
          allUnfilteredRes.value.forEach(a => {
            const feedStatus = a.feed_status || (a.is_finished ? 'completed' : a.is_overdue ? 'overdue' : 'active');
            if (feedStatus === 'completed') completed++;
            else if (feedStatus === 'overdue') overdue++;
            else active++;
          });

          // Also count local AI exercises that are not yet in DB
          try {
            const savedLocal = JSON.parse(localStorage.getItem('tk_student_ai_exercises') || '[]');
            const dbIds = new Set(allUnfilteredRes.value.map(x => String(x.assignment_id || x.exercise_id || '').toLowerCase()));
            savedLocal.forEach(item => {
              const itemId = String(item.id || item.assignment_id || item.exercise_id || '').toLowerCase();
              if (!itemId || !dbIds.has(itemId)) {
                const isFinished = item.status === 'completed' || Boolean(localStorage.getItem(`tk_exam_submitted_${item.id}`));
                if (isFinished) completed++;
                else active++;
              }
            });
          } catch (e) {
            console.error('Error computing local AI exercise counts:', e);
          }

          if (isMounted) {
            setTabCounts({
              all: active + overdue + completed,
              active,
              overdue,
              completed,
            });
          }
        }

        const rawAssignments = assignmentsRes.status === 'fulfilled' && Array.isArray(assignmentsRes.value) ? assignmentsRes.value : [];

        const allAssigned = rawAssignments.map(a => {
          const myAttempts = studentAttempts.filter(att => 
            String(att.assignment_id || '').toLowerCase() === String(a.assignment_id || '').toLowerCase()
          );
          const finishedAttempt = myAttempts.find(att => att.is_finished);
          const hasFinishedBackend = Boolean(finishedAttempt || a.is_finished || (a.completed_attempts_count > 0));
          const isFinished = hasFinishedBackend;
          const maxAttempts = a.max_attempts || 1;

          const due = a.due_at ? new Date(a.due_at) : null;
          const now = new Date();
          const isOverdue = due ? (due < now && !isFinished) : false;
          const formattedDue = formatDeadline(a.due_at);
          const isToday = due ? now.toDateString() === due.toDateString() : false;

          const feedStatus = isFinished ? 'completed' : isOverdue ? 'overdue' : 'active';
          const statusLabel = isFinished ? 'Đã nộp bài' : isOverdue ? 'Quá hạn' : 'Đang mở';
          const completedAttempts = myAttempts.filter(att => att.is_finished);
          const completedCount = a.completed_attempts_count != null ? a.completed_attempts_count : completedAttempts.length;
          const finalCompletedCount = isFinished ? Math.max(1, completedCount) : completedCount;
          const isAi = Boolean(a.is_ai_generated || a.category === 'ai_generated');

          return {
            id: a.assignment_id,
            assignment_id: a.assignment_id,
            exercise_id: a.exercise_id,
            class_id: a.class_id,
            className: a.class_name || 'Lớp học',
            type: 'quiz',
            category: a.category || (isAi ? 'ai_generated' : ((a.exercise_title || '').toLowerCase().includes('đề thi') ? 'exam' : 'class_exercise')),
            categoryLabel: a.categoryLabel || (isAi ? 'Bài tập tạo sinh AI' : ((a.exercise_title || '').toLowerCase().includes('đề thi') ? 'Bài thi' : 'Bài tập trên lớp')),
            title: a.exercise_title || 'Bài tập được giao',
            teacher: a.teacher_name || (isAi ? 'Trợ lý AI Tam Khang' : 'Giáo viên bộ môn'),
            subject: a.subject_name || (a.class_name?.includes('Lý') ? 'Vật lý' : a.class_name?.includes('Hóa') ? 'Hóa học' : 'Toán học'),
            questionsCount: a.total_questions ? `${a.total_questions} câu hỏi` : 'Đề thi trắc nghiệm',
            total_questions: a.total_questions || 0,
            duration: `${a.duration_minutes || 45} phút`,
            deadline: formattedDue,
            due_at: a.due_at,
            isToday,
            status: feedStatus,
            statusLabel,
            maxAttempts: (((a.category || '').toLowerCase() === 'exam' || (a.exercise_title || '').toLowerCase().includes('đề thi')) ? 1 : null),
            completedAttemptsCount: finalCompletedCount,
            attempt: finishedAttempt || myAttempts[0],
            score: a.latest_score ?? (finishedAttempt?.score ?? null),
            isRealBackend: true,
            isAiGenerated: isAi
          };
        });

        if (isMounted) {
          setBackendAssignments(allAssigned);
        }
      } catch (err) {
        console.error('Failed to load student assignments:', err);
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }
    loadData();

    return () => {
      isMounted = false;
    };
  }, [selectedTab, selectedSubject, debouncedSearch, localAiExercisesTrigger]);

  // Safe icon helper that always returns a valid Lucide component even after JSON parsing
  const getAssignmentIcon = (item) => {
    if (item.category === 'ai_generated' || item.isAiGenerated || item.type === 'ai_generated') return Sparkles;
    if (item.type === 'speaking') return Mic;
    if (item.type === 'quiz') {
      return item.category === 'exam' ? Award : HelpCircle;
    }
    return FileText;
  };

  // Combine backend assignments and saved AI exercises with strict deduplication
  const assignmentsList = useMemo(() => {
    let localAiList = [];
    try {
      const saved = localStorage.getItem('tk_student_ai_exercises');
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length > 0) {
          localAiList = parsed;
        }
      }
    } catch (e) {
      console.error(e);
    }

    // 1. Deduplicate backend assignments by assignment_id and exercise_id
    const seenAssignmentIds = new Set();
    const seenExerciseIds = new Set();
    const dedupedBackend = [];

    backendAssignments.forEach(item => {
      const aId = item.assignment_id || item.id;
      const eId = item.exercise_id;
      if (aId && seenAssignmentIds.has(String(aId).toLowerCase())) return;
      if (eId && seenExerciseIds.has(String(eId).toLowerCase())) return;
      if (aId) seenAssignmentIds.add(String(aId).toLowerCase());
      if (eId) seenExerciseIds.add(String(eId).toLowerCase());
      dedupedBackend.push(item);
    });

    // 2. Filter local AI items:
    // Only exclude a local AI item if:
    // a) Its exact ID is already present in backend assignments
    // b) Or an AI-generated backend assignment already has the exact same title
    const seenIds = new Set([
      ...Array.from(seenAssignmentIds),
      ...Array.from(seenExerciseIds)
    ]);

    const filteredLocal = localAiList.filter(localItem => {
      const localId = String(localItem.id || localItem.assignment_id || localItem.exercise_id || '').toLowerCase();
      if (localId && seenIds.has(localId)) return false;

      const localTitle = (localItem.title || '').trim().toLowerCase().replace(/\s+/g, ' ');
      if (!localTitle) return false;

      // Only check collision against backend items that are ALSO AI-generated exercises
      const duplicateAiInBackend = dedupedBackend.some(b => 
        b.isAiGenerated && (b.title || '').trim().toLowerCase().replace(/\s+/g, ' ') === localTitle
      );
      if (duplicateAiInBackend) return false;

      return true;
    });

    const mappedLocal = filteredLocal.map(item => {
      const isAi = Boolean(item.isAiGenerated || item.type === 'ai_generated' || item.category === 'ai_generated');
      let cat = item.category;
      if (!cat || cat === 'exercise') {
        cat = isAi ? 'ai_generated' : 'class_exercise';
      }
      return {
        ...item,
        category: cat,
        categoryLabel: item.categoryLabel || (cat === 'ai_generated' ? 'Bài tập tạo sinh AI' : 'Bài tập trên lớp'),
        isAiGenerated: isAi,
        status: item.status || 'active',
        statusLabel: item.statusLabel || 'Đang mở'
      };
    });

    if (dedupedBackend.length > 0 || mappedLocal.length > 0) {
      return [...dedupedBackend, ...mappedLocal];
    }
    return [];
  }, [backendAssignments, localAiExercisesTrigger]);

  // AI Generator Modal States
  const [isAiModalOpen, setIsAiModalOpen] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationStep, setGenerationStep] = useState(0);
  const [generatedExerciseId, setGeneratedExerciseId] = useState(null);
  const [generatedAiResult, setGeneratedAiResult] = useState(null);

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

  // Submit AI Generation Handler (Persisted to Database)
  const handleGenerateAiExercise = async () => {
    if (totalAiQuestions === 0) {
      alert('Vui lòng chọn số lượng câu hỏi lớn hơn 0.');
      return;
    }

    setIsGenerating(true);
    setGenerationStep(1);

    const step2Timer = setTimeout(() => {
      setGenerationStep(2);
    }, 800);

    const step3Timer = setTimeout(() => {
      setGenerationStep(3);
    }, 1600);

    try {
      const payload = {
        subject_name: aiSubject,
        grade_name: aiGrade,
        topic_prompt: aiTopicPrompt,
        part1_count: part1Total,
        part2_count: part2Total,
        part3_count: part3Total,
        duration_minutes: aiDuration
      };

      const result = await exercisesApi.generateAiExercise(payload);

      clearTimeout(step2Timer);
      clearTimeout(step3Timer);

      // Keep local backup as well so it's always available across reloads
      try {
        const existingLocal = JSON.parse(localStorage.getItem('tk_student_ai_exercises') || '[]');
        const newLocalItem = {
          id: result.exercise_id,
          exercise_id: result.exercise_id,
          assignment_id: result.assignment_id,
          class_id: result.class_id,
          className: result.class_name || '12A1',
          type: 'quiz',
          category: 'ai_generated',
          categoryLabel: 'Bài tập tạo sinh AI',
          title: result.title,
          teacher: 'Trợ lý AI Tam Khang',
          subject: result.subject_name,
          questionsCount: `${result.total_questions} câu hỏi`,
          total_questions: result.total_questions,
          duration: `${result.duration_minutes} phút`,
          status: 'active',
          statusLabel: 'Đang mở',
          isAiGenerated: true,
          isRealBackend: true,
          topicPrompt: aiTopicPrompt
        };
        const updated = [newLocalItem, ...existingLocal.filter(x => x.id !== result.exercise_id && x.title !== result.title)];
        localStorage.setItem('tk_student_ai_exercises', JSON.stringify(updated));
      } catch (err) {
        console.warn('Could not save local copy of AI exercise', err);
      }

      setGeneratedAiResult(result);
      setGeneratedExerciseId(result.exercise_id);
      setIsGenerating(false);
      setGenerationStep(4);
      setLocalAiExercisesTrigger(prev => prev + 1);
    } catch (err) {
      clearTimeout(step2Timer);
      clearTimeout(step3Timer);
      console.error('Failed to generate AI exercise in DB:', err);
      const errMsg = err.response?.data?.detail?.message || err.message || 'Có lỗi khi tạo bài tập trên máy chủ. Vui lòng thử lại.';
      alert(errMsg);
      setIsGenerating(false);
      setGenerationStep(0);
    }
  };

  const handleCloseAiModal = () => {
    setIsAiModalOpen(false);
    setIsGenerating(false);
    setGenerationStep(0);
    setGeneratedExerciseId(null);
    setGeneratedAiResult(null);
    setLocalAiExercisesTrigger(prev => prev + 1);
  };

  const subjectOptions = useMemo(() => {
    const list = new Set(['Toán học', 'Hóa học', 'Vật lý', 'Tiếng Anh', 'Sinh học', 'Ngữ văn', 'Lịch sử']);
    if (Array.isArray(availableSubjects)) {
      availableSubjects.forEach(s => {
        if (s.subject_name) list.add(s.subject_name);
      });
    }
    assignmentsList.forEach(a => {
      if (a.subject) list.add(a.subject);
    });
    return Array.from(list);
  }, [availableSubjects, assignmentsList]);

  const filteredAssignments = useMemo(() => {
    return assignmentsList.filter(item => {
      // 1. Category / Type filter
      if (selectedType !== 'all') {
        const itemCat = item.category || (item.isAiGenerated ? 'ai_generated' : 'class_exercise');
        if (selectedType === 'class_exercise') {
          // "Bài tập trên lớp" includes class_exercise, exercise, and AI practice exercises
          if (itemCat === 'exam') return false;
        } else if (selectedType === 'ai_generated') {
          if (itemCat !== 'ai_generated' && !item.isAiGenerated) return false;
        } else if (selectedType === 'exam') {
          if (itemCat !== 'exam') return false;
        }
      }

      // 2. For local-only AI/practice items, apply tab, subject and search filters client-side
      if (item.isAiGenerated || !item.isRealBackend) {
        const savedData = localStorage.getItem(`tk_exam_submitted_${item.id}`) ||
                          (item.assignment_id && localStorage.getItem(`tk_exam_submitted_${item.assignment_id}`)) ||
                          (item.exercise_id && localStorage.getItem(`tk_exam_submitted_${item.exercise_id}`));
        const isFinished = item.status === 'completed' || Boolean(savedData);
        if (selectedTab === 'overdue') return false;
        if (selectedTab === 'completed' && !isFinished) return false;
        // On 'active' tab, practice exercise remains open for retakes

        if (selectedSubject !== 'all' && item.subject !== selectedSubject) return false;
        if (searchTitle.trim()) {
          const query = searchTitle.toLowerCase().trim();
          const matchesTitle = item.title?.toLowerCase().includes(query);
          const matchesSubject = item.subject?.toLowerCase().includes(query);
          if (!matchesTitle && !matchesSubject) return false;
        }
      }

      return true;
    });
  }, [assignmentsList, selectedType, selectedSubject, searchTitle, selectedTab]);

  const handleStartExercise = (item) => {
    const targetExerciseId = item.exercise_id || item.exerciseId || item.id;
    const targetAssignmentId = item.assignment_id || item.id;
    navigate(`/student/exercises/${targetExerciseId}/taking`, {
      state: {
        assignmentId: targetAssignmentId,
        exerciseId: targetExerciseId,
        classId: item.class_id,
        title: item.title
      }
    });
  };

  const handleCardClick = (item) => {
    setSelectedExerciseDetail(item);
    setSelectedAttemptId(null);
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

      {/* Exercise Tabs Row */}
      <div className="exercises-tabs-bar">
        <button 
          type="button" 
          className={`exercises-tab-pill ${selectedTab === 'all' ? 'active' : ''}`}
          onClick={() => { setSelectedTab('all'); setCurrentPage(1); }}
        >
          <span>Tất cả</span>
          <span className="tab-pill-count">{tabCounts.all}</span>
        </button>
        <button 
          type="button" 
          className={`exercises-tab-pill ${selectedTab === 'active' ? 'active' : ''}`}
          onClick={() => { setSelectedTab('active'); setCurrentPage(1); }}
        >
          <span>Đang diễn ra</span>
          <span className="tab-pill-count count-active">{tabCounts.active}</span>
        </button>
        <button 
          type="button" 
          className={`exercises-tab-pill ${selectedTab === 'overdue' ? 'active' : ''}`}
          onClick={() => { setSelectedTab('overdue'); setCurrentPage(1); }}
        >
          <span>Quá hạn</span>
          <span className="tab-pill-count count-overdue">{tabCounts.overdue}</span>
        </button>
        <button 
          type="button" 
          className={`exercises-tab-pill ${selectedTab === 'completed' ? 'active' : ''}`}
          onClick={() => { setSelectedTab('completed'); setCurrentPage(1); }}
        >
          <span>Đã hoàn thành</span>
          <span className="tab-pill-count count-completed">{tabCounts.completed}</span>
        </button>
      </div>

      {/* Filter Card */}
      <div className="exercises-filter-card">
        <div className="filter-field-group search-field-group">
          <label className="filter-field-label">Tìm kiếm bài tập</label>
          <div className="filter-search-input-wrap">
            <Search size={16} className="filter-search-icon" />
            <input 
              type="text"
              className="filter-search-input"
              placeholder="Nhập tên bài tập, đề thi, môn học..."
              value={searchTitle}
              onChange={(e) => { setSearchTitle(e.target.value); setCurrentPage(1); }}
            />
            {searchTitle && (
              <button 
                type="button" 
                className="filter-search-clear" 
                onClick={() => { setSearchTitle(''); setCurrentPage(1); }}
                aria-label="Xóa tìm kiếm"
              >
                <X size={14} />
              </button>
            )}
          </div>
        </div>

        <div className="filter-field-group">
          <label className="filter-field-label">Môn học</label>
          <select 
            className="filter-select-input"
            value={selectedSubject}
            onChange={(e) => { setSelectedSubject(e.target.value); setCurrentPage(1); }}
          >
            <option value="all">Tất cả môn học</option>
            {subjectOptions.map(sub => (
              <option key={sub} value={sub}>{sub}</option>
            ))}
          </select>
        </div>

        <div className="filter-field-group">
          <label className="filter-field-label">Loại bài tập / Đề thi</label>
          <select 
            className="filter-select-input"
            value={selectedType}
            onChange={(e) => { setSelectedType(e.target.value); setCurrentPage(1); }}
          >
            <option value="all">Tất cả thể loại</option>
            <option value="exam">Bài thi</option>
            <option value="class_exercise">Bài tập trên lớp</option>
            <option value="ai_generated">Bài tập tạo sinh AI</option>
          </select>
        </div>
      </div>

      {/* Exercises Cards Grid */}
      <div className="exercises-cards-grid">
        {filteredAssignments.length === 0 ? (
          <div className="exercises-empty-state" style={{ gridColumn: '1 / -1', textAlign: 'center', padding: '48px 24px', backgroundColor: '#FFFFFF', borderRadius: '14px', border: '1px solid #EBE8F0' }}>
            <HelpCircle size={44} color="#94A3B8" style={{ margin: '0 auto 12px' }} />
            <h3 style={{ fontSize: '16px', fontWeight: 700, color: '#1E293B', margin: '0 0 6px' }}>Không tìm thấy bài tập phù hợp</h3>
            <p style={{ fontSize: '13.5px', color: '#64748B', margin: 0 }}>Thử chuyển tab trạng thái, chọn môn học khác hoặc xóa từ khóa tìm kiếm.</p>
          </div>
        ) : (
          filteredAssignments.map(item => {
            const Icon = getAssignmentIcon(item);
            const savedData = !item.isRealBackend ? (
              localStorage.getItem(`tk_exam_submitted_${item.id}`) ||
              (item.assignment_id && localStorage.getItem(`tk_exam_submitted_${item.assignment_id}`)) ||
              (item.exercise_id && localStorage.getItem(`tk_exam_submitted_${item.exercise_id}`))
            ) : null;
            const isSubmitted = item.status === 'completed' || Boolean(savedData);
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
                    <span className="meta-chip-item" title="Số lượt làm bài">
                      <RotateCcw size={13} />
                      {isExam ? `Lượt làm: ${item.completedAttemptsCount || (isSubmitted ? 1 : 0)}/1` : (item.completedAttemptsCount > 0 ? `Lượt làm: ${item.completedAttemptsCount} (Không giới hạn)` : 'Không giới hạn lượt làm')}
                    </span>
                    {item.className && (
                      <span className="meta-chip-item class-badge">
                        {item.className}
                      </span>
                    )}
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
                  ) : item.status === 'overdue' ? (
                    <button 
                      type="button" 
                      className="btn-card-action btn-overdue"
                      onClick={() => handleStartExercise(item)}
                    >
                      Quá hạn
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
          })
        )}
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
                      const targetExerciseId = generatedAiResult?.exercise_id || generatedExerciseId;
                      const targetAssignmentId = generatedAiResult?.assignment_id;
                      const targetClassId = generatedAiResult?.class_id;
                      const targetTitle = generatedAiResult?.title;
                      handleCloseAiModal();
                      navigate(`/student/exercises/${targetExerciseId}/taking`, {
                        state: {
                          assignmentId: targetAssignmentId,
                          exerciseId: targetExerciseId,
                          classId: targetClassId,
                          title: targetTitle
                        }
                      });
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
      {/* EXERCISE DETAIL & ATTEMPT HISTORY MODAL */}
      {/* ============================================================ */}
      {selectedExerciseDetail && (
        <div className="detail-modal-backdrop" onClick={() => setSelectedExerciseDetail(null)}>
          <div className="exercise-detail-modal-card" onClick={(e) => e.stopPropagation()}>
            {/* Modal Header */}
            <div className="detail-modal-header">
              <div className="detail-modal-header-left">
                <div className="detail-modal-top-tags">
                  <span className={detailSummary?.status === 'completed' || (detailSummary?.attempts?.some(a => a.is_finished || a.score != null)) || (selectedExerciseDetail.isRealBackend ? selectedExerciseDetail.score != null : selectedExerciseDetail.status === 'completed') ? "modal-status-pill-green" : "modal-status-pill-blue"}>
                    {detailSummary?.status === 'completed' || (detailSummary?.attempts?.some(a => a.is_finished || a.score != null)) || (selectedExerciseDetail.isRealBackend ? selectedExerciseDetail.score != null : selectedExerciseDetail.status === 'completed') ? 'Đã hoàn thành' : 'Đang mở'}
                  </span>
                  <span className="modal-subject-grade-text">
                    {detailSummary?.subject_name || selectedExerciseDetail.subject || 'Toán học'} • {detailSummary?.grade_name || selectedExerciseDetail.grade || 'Lớp 12'}
                  </span>
                </div>
                <h2 className="detail-modal-main-title">
                  Chi tiết kết quả & Lịch sử làm bài - {detailSummary?.title || selectedExerciseDetail.title}
                </h2>
                <p className="detail-modal-meta-line">
                  Giáo viên: <strong>Thầy {detailSummary?.teacher_name || selectedExerciseDetail.teacher}</strong> • Thời lượng: <strong>{detailSummary?.duration_minutes ? `${detailSummary.duration_minutes} phút` : selectedExerciseDetail.duration}</strong> • Số lượng: <strong>{detailSummary?.total_questions ? `${detailSummary.total_questions} câu hỏi` : selectedExerciseDetail.questionsCount}</strong> • Hạn nộp: <strong className="due-highlight">{detailSummary?.deadline_text || selectedExerciseDetail.deadline}</strong>
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
              {isLoadingDetail ? (
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '260px', gap: '12px' }}>
                  <Loader2 size={32} className="animate-spin text-purple-600" />
                  <span style={{ fontSize: '14px', color: '#6b7280' }}>Đang tải chi tiết kết quả từ hệ thống...</span>
                </div>
              ) : currentAttempt ? (
                <>
                  {/* 1. Dynamic Result Summary Card reflecting clicked attempt */}
                  <div className="best-result-summary-box">
                    <div className="best-result-top-row">
                      <div className="best-score-left-col">
                        <span className="best-score-label">{currentAttempt.score_label || currentAttempt.scoreLabel}</span>
                        <div className="best-score-digits-row">
                          <span className="score-number-big">{currentAttempt.score != null ? currentAttempt.score : '--'}</span>
                          <span className="score-scale-denom">/ 10</span>
                          <span className="score-grade-pill">{currentAttempt.grade}</span>
                        </div>
                      </div>

                      <div className="best-stat-cell">
                        <span className="stat-cell-title">Đúng</span>
                        <span className="stat-cell-val val-green">
                          {currentAttempt.correct_count ?? currentAttempt.correctCount} / {currentAttempt.total_count ?? currentAttempt.totalCount} câu <span className="stat-cell-pct">({currentAttempt.correct_pct || currentAttempt.correctPct})</span>
                        </span>
                      </div>

                      <div className="best-stat-cell">
                        <span className="stat-cell-title">Thời gian làm</span>
                        <span className="stat-cell-val val-dark">{currentAttempt.time_spent || currentAttempt.timeSpent}</span>
                      </div>
                    </div>

                    {/* Cognitive Level Analysis */}
                    {currentAttempt.cognitive && (
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
                    )}
                  </div>

                  {/* 2. Attempt History List */}
                  <div className="attempts-history-wrapper">
                    <div className="attempts-history-header">
                      <Clock size={16} className="history-clock-icon" />
                      <h3 className="attempts-history-title">Lịch sử các lần làm bài</h3>
                      <span className="attempts-unlimited-pill">Không giới hạn số lượt</span>
                    </div>

                    <div className="attempts-cards-list">
                      {activeAttempts.map((attempt) => {
                        const attId = attempt.id || attempt.attempt_id;
                        const isSelected = String(selectedAttemptId) === String(attId);
                        return (
                          <div
                            key={attId}
                            className={`attempt-record-card ${isSelected ? 'is-selected-attempt' : ''} ${attempt.is_latest || attempt.isLatest ? 'is-latest-attempt' : ''}`}
                            onClick={() => setSelectedAttemptId(attId)}
                            title="Bấm để xem chi tiết kết quả lần làm bài này"
                          >
                            <div className="attempt-record-left">
                              <div className="attempt-badge-row">
                                <span className={`attempt-num-badge ${attempt.is_latest || attempt.isLatest ? 'badge-latest-purple' : ''}`}>
                                  {attempt.badge_label || attempt.badgeLabel}
                                </span>
                                <span className="attempt-date-text">{attempt.date_text || attempt.dateText}</span>
                                <span className={attempt.status_tag_class || attempt.statusTagClass}>{attempt.status_tag || attempt.statusTag}</span>
                                {isSelected && (
                                  <span className="attempt-viewing-tag">Đang hiển thị</span>
                                )}
                              </div>
                              <div className="attempt-stats-row">
                                <span>Điểm: <strong>{attempt.score != null ? attempt.score : '--'} / 10</strong></span>
                                <span className="attempt-stat-divider">•</span>
                                <span>Thời gian: <strong>{attempt.time_spent || attempt.timeSpent}</strong></span>
                              </div>
                            </div>

                            <button 
                              type="button" 
                              className="btn-view-attempt-detail"
                              onClick={(e) => {
                                e.stopPropagation();
                                const targetExerciseId = detailSummary?.exercise_id || selectedExerciseDetail.exercise_id || selectedExerciseDetail.exerciseId || selectedExerciseDetail.id;
                                const targetAssignmentId = detailSummary?.assignment_id || selectedExerciseDetail.assignment_id || selectedExerciseDetail.id;
                                const targetAttemptId = attempt.id || attempt.attempt_id;
                                setSelectedExerciseDetail(null);
                                navigate(`/student/exercises/${targetExerciseId}/taking`, {
                                  state: {
                                    assignmentId: targetAssignmentId,
                                    exerciseId: targetExerciseId,
                                    attemptId: targetAttemptId,
                                    classId: detailSummary?.class_id || selectedExerciseDetail.class_id,
                                    title: detailSummary?.title || selectedExerciseDetail.title
                                  }
                                });
                              }}
                            >
                              {attempt.is_finished || attempt.score != null ? 'Xem chi tiết bài làm' : 'Tiếp tục làm bài'}
                            </button>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </>
              ) : (
                <div style={{ textAlign: 'center', padding: '48px 24px' }}>
                  <p style={{ color: '#4b5563', fontSize: '15px', marginBottom: '20px' }}>
                    Chưa có lượt làm bài nào cho bài tập này.
                  </p>
                  <button
                    type="button"
                    className="btn-modal-retake-purple"
                    onClick={() => {
                      const targetItem = selectedExerciseDetail;
                      setSelectedExerciseDetail(null);
                      handleStartExercise(targetItem);
                    }}
                  >
                    Bắt đầu làm bài ngay
                  </button>
                </div>
              )}
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
                {(currentAttempt?.is_finished || currentAttempt?.score != null || selectedExerciseDetail.score != null) && (
                  <button 
                    type="button" 
                    className="btn-modal-view-answers-outline"
                    onClick={() => {
                      const targetExerciseId = detailSummary?.exercise_id || selectedExerciseDetail.exercise_id || selectedExerciseDetail.exerciseId || selectedExerciseDetail.id;
                      const targetAssignmentId = detailSummary?.assignment_id || selectedExerciseDetail.assignment_id || selectedExerciseDetail.id;
                      const targetAttemptId = currentAttempt ? (currentAttempt.id || currentAttempt.attempt_id) : null;
                      setSelectedExerciseDetail(null);
                      navigate(`/student/exercises/${targetExerciseId}/taking`, {
                        state: {
                          assignmentId: targetAssignmentId,
                          exerciseId: targetExerciseId,
                          attemptId: targetAttemptId,
                          classId: detailSummary?.class_id || selectedExerciseDetail.class_id,
                          title: detailSummary?.title || selectedExerciseDetail.title
                        }
                      });
                    }}
                  >
                    Xem đáp án & giải thích chi tiết
                  </button>
                )}

                <button 
                  type="button" 
                  className="btn-modal-retake-purple"
                  onClick={() => {
                    const targetExerciseId = detailSummary?.exercise_id || selectedExerciseDetail.exercise_id || selectedExerciseDetail.exerciseId || selectedExerciseDetail.id;
                    const targetAssignmentId = detailSummary?.assignment_id || selectedExerciseDetail.assignment_id || selectedExerciseDetail.id;
                    setSelectedExerciseDetail(null);
                    navigate(`/student/exercises/${targetExerciseId}/taking`, {
                      state: {
                        assignmentId: targetAssignmentId,
                        exerciseId: targetExerciseId,
                        classId: detailSummary?.class_id || selectedExerciseDetail.class_id,
                        title: detailSummary?.title || selectedExerciseDetail.title,
                        isRetake: true
                      }
                    });
                  }}
                  title="Làm bài thi"
                >
                  <RotateCcw size={15} />
                  <span>
                    {(currentAttempt?.is_finished || selectedExerciseDetail.score != null)
                      ? (selectedExerciseDetail.category === 'exam' ? 'Làm lại bài thi' : 'Luyện tập lại')
                      : (activeAttempts.length > 0 ? 'Tiếp tục làm bài' : 'Bắt đầu làm bài')}
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
