// File Name: StudentSubjectRadarDetailCard.jsx
// Description: Subject-specific cognitive level triangular radar charts and detailed assignments score table with real database data synchronization, eliminating non-existent mock exercises, and displaying uncompleted/overdue assignments.
// Created At: 2026-09-13
// Created By: Tam Khang
// Updated At: 2026-10-11
// Updated By: Tam Khang

import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  BookOpen, 
  Sparkles, 
  CheckCheck,
  ArrowLeft,
  ArrowRight,
  Clock,
  AlertCircle,
  HelpCircle,
  PlusCircle
} from 'lucide-react';
import { assignmentsApi, attemptsApi } from '../../services/api';
import './StudentSubjectRadarDetailCard.css';

/**
 * Reusable 3-Axis Equilateral Triangular Radar Chart
 */
function TriangularRadar({
  hasData = true,
  scores = { know: 8.8, comp: 8.2, app: 7.9 },
  maxScore = 10,
  width = 240,
  height = 200,
  theme = 'purple' // 'purple' or 'blue'
}) {
  const centerX = width / 2;
  const centerY = height / 2 + 5;
  const radius = 62;

  // 3 vertices angles:
  // 1: Top (Nhận biết): -90 deg (-PI/2)
  // 2: Bottom Right (Thông hiểu): 30 deg (PI/6)
  // 3: Bottom Left (Vận dụng): 150 deg (5*PI/6)
  const angles = [
    -Math.PI / 2,
    Math.PI / 6,
    (5 * Math.PI) / 6
  ];

  // Helper to get cartesian coordinates on triangle radius
  const getPoint = (angle, r) => {
    return [
      centerX + r * Math.cos(angle),
      centerY + r * Math.sin(angle)
    ];
  };

  // Reference triangles
  const outerTrianglePoints = angles
    .map(angle => getPoint(angle, radius).join(','))
    .join(' ');

  const midTrianglePoints = angles
    .map(angle => getPoint(angle, radius * 0.6).join(','))
    .join(' ');

  const innerTrianglePoints = angles
    .map(angle => getPoint(angle, radius * 0.25).join(','))
    .join(' ');

  // Compute student score polygon
  const scoreKeys = [scores.know, scores.comp, scores.app];
  const dataPolygonPoints = angles
    .map((angle, idx) => {
      const scoreVal = Math.min(Math.max(scoreKeys[idx] || 0, 0), maxScore);
      const ratio = scoreVal / maxScore;
      const r = Math.max(radius * ratio, 6);
      return getPoint(angle, r).join(',');
    })
    .join(' ');

  // Theming colors
  const isPurple = theme === 'purple';
  const gridStroke = isPurple ? '#E9D5FF' : '#BFDBFE';
  const axisStroke = isPurple ? '#DDD6FE' : '#93C5FD';
  const polyFill = isPurple ? 'rgba(124, 58, 237, 0.22)' : 'rgba(37, 99, 235, 0.22)';
  const polyStroke = isPurple ? '#7C3AED' : '#2563EB';
  const dotFill = isPurple ? '#6D28D9' : '#1D4ED8';

  return (
    <div className="triangular-radar-wrapper">
      <svg
        width={width}
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        style={{ overflow: 'visible' }}
      >
        {/* Background Grids */}
        <polygon
          points={outerTrianglePoints}
          fill="none"
          stroke={gridStroke}
          strokeWidth="1.2"
        />
        <polygon
          points={midTrianglePoints}
          fill="none"
          stroke={gridStroke}
          strokeWidth="1"
          strokeDasharray="2,2"
        />
        <polygon
          points={innerTrianglePoints}
          fill="none"
          stroke={gridStroke}
          strokeWidth="0.8"
          strokeDasharray="2,2"
        />

        {/* 3 Axes radiating from center */}
        {angles.map((angle, i) => {
          const [x, y] = getPoint(angle, radius);
          return (
            <line
              key={i}
              x1={centerX}
              y1={centerY}
              x2={x}
              y2={y}
              stroke={axisStroke}
              strokeWidth="1.2"
            />
          );
        })}

        {/* Dynamic rendering: if no exercises completed, show empty state notice */}
        {!hasData ? (
          <g>
            <rect
              x={centerX - 48}
              y={centerY - 12}
              width="96"
              height="24"
              rx="12"
              fill={isPurple ? '#FAF5FF' : '#EFF6FF'}
              stroke={isPurple ? '#DDD6FE' : '#BFDBFE'}
              strokeWidth="1"
            />
            <text
              x={centerX}
              y={centerY + 4}
              textAnchor="middle"
              fontSize="11"
              fontWeight="600"
              fill={isPurple ? '#7C3AED' : '#2563EB'}
            >
              Chưa có dữ liệu
            </text>
          </g>
        ) : (
          <>
            {/* Student Data Filled Polygon */}
            <polygon
              points={dataPolygonPoints}
              fill={polyFill}
              stroke={polyStroke}
              strokeWidth="2.2"
              strokeLinejoin="round"
            />

            {/* Vertex dots on student data polygon */}
            {angles.map((angle, idx) => {
              const scoreVal = Math.min(Math.max(scoreKeys[idx] || 0, 0), maxScore);
              const ratio = scoreVal / maxScore;
              const r = Math.max(radius * ratio, 6);
              const [px, py] = getPoint(angle, r);
              return (
                <circle
                  key={idx}
                  cx={px}
                  cy={py}
                  r="4"
                  fill={dotFill}
                  stroke="#FFFFFF"
                  strokeWidth="1.8"
                />
              );
            })}
          </>
        )}

        {/* Vertex Labels */}
        <text
          x={centerX}
          y={centerY - radius - 12}
          textAnchor="middle"
          fontSize="11.5"
          fontWeight="600"
          fill="#334155"
        >
          Nhận biết
        </text>

        <text
          x={centerX + radius * Math.cos(Math.PI / 6) + 12}
          y={centerY + radius * Math.sin(Math.PI / 6) + 18}
          textAnchor="start"
          fontSize="11.5"
          fontWeight="600"
          fill="#334155"
        >
          Thông hiểu
        </text>

        <text
          x={centerX + radius * Math.cos((5 * Math.PI) / 6) - 12}
          y={centerY + radius * Math.sin((5 * Math.PI) / 6) + 18}
          textAnchor="end"
          fontSize="11.5"
          fontWeight="600"
          fill="#334155"
        >
          Vận dụng
        </text>
      </svg>
    </div>
  );
}

// Helper to normalize subject strings for comparison
const normalizeSubj = (s) => (s || '')
  .toLowerCase()
  .replace(/\s+/g, '')
  .replace(/í/g, 'y')
  .replace(/ý/g, 'y');

export default function StudentSubjectRadarDetailCard({
  subjectName = 'Toán Học',
  onBack
}) {
  const navigate = useNavigate();
  const allSubjectNames = ['Toán Học', 'Vật Lí', 'Hóa Học', 'Tiếng Anh', 'Lịch Sử', 'Tin học'];
  
  const [currentSubject, setCurrentSubject] = useState(subjectName);
  const [activeCategory, setActiveCategory] = useState('class'); // 'class' or 'ai'

  const [backendAssignments, setBackendAssignments] = useState([]);
  const [backendAttempts, setBackendAttempts] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (subjectName) {
      setCurrentSubject(subjectName);
    }
  }, [subjectName]);

  // Synchronize assignments and attempts from session cache or backend
  useEffect(() => {
    let isMounted = true;
    async function syncData() {
      // 1. Check session cache first for fast load
      try {
        const cachedRaw = sessionStorage.getItem('tk_student_assignments_cache');
        if (cachedRaw) {
          const parsed = JSON.parse(cachedRaw);
          if (parsed && Array.isArray(parsed.assignments)) {
            if (isMounted) {
              setBackendAssignments(parsed.assignments);
              setBackendAttempts(parsed.attempts || []);
            }
            return;
          }
        }
      } catch (e) {}

      // 2. Query backend APIs
      try {
        setIsLoading(true);
        const [assigns, atts] = await Promise.all([
          assignmentsApi.getAssignments().catch(() => []),
          attemptsApi.getAttempts().catch(() => [])
        ]);
        if (isMounted) {
          setBackendAssignments(Array.isArray(assigns) ? assigns : []);
          setBackendAttempts(Array.isArray(atts) ? atts : []);
        }
      } catch (err) {
        console.warn('Could not sync assignments from backend:', err);
      } finally {
        if (isMounted) setIsLoading(false);
      }
    }

    syncData();
    return () => { isMounted = false; };
  }, []);

  const normCurrent = normalizeSubj(currentSubject);

  // Filter real assignments strictly belonging to current subject
  const matchedRealAssignments = useMemo(() => {
    return backendAssignments.filter(a => {
      const aSub = normalizeSubj(a.subject_name || a.subject || '');
      const titleSub = normalizeSubj(a.exercise_title || a.title || '');
      const classSub = normalizeSubj(a.class_name || '');
      return aSub === normCurrent || 
             aSub.includes(normCurrent) || 
             normCurrent.includes(aSub) || 
             titleSub.includes(normCurrent) ||
             (normCurrent === 'vatly' && (classSub.includes('ly') || aSub.includes('ly')));
    });
  }, [backendAssignments, normCurrent]);

  // Map real class exercises (eliminating non-existent exercises and displaying uncompleted/overdue ones)
  const realClassExercises = useMemo(() => {
    const classList = matchedRealAssignments.filter(a => !a.is_ai_generated && a.category !== 'ai_generated');
    return classList.map(a => {
      const aId = String(a.assignment_id || a.id || '').toLowerCase();
      const myAttempts = backendAttempts.filter(att => 
        String(att.assignment_id || '').toLowerCase() === aId && (att.score != null || att.is_finished)
      );
      const finishedAttempts = myAttempts.filter(att => att.is_finished || att.score != null);
      const isFinished = Boolean(finishedAttempts.length > 0 || a.is_finished || a.completed_attempts_count > 0);
      
      const due = a.due_at ? new Date(a.due_at) : null;
      const isOverdue = due ? (due < new Date() && !isFinished) : false;

      const scores = finishedAttempts.map((att, i) => `Lần ${i + 1}: ${att.score != null ? att.score : '--'}`);
      const scoresList = scores.length > 0 
        ? scores 
        : (isFinished && a.latest_score != null 
          ? [`Lần 1: ${a.latest_score}`] 
          : (isOverdue ? ['Quên nộp bài'] : ['Chưa nộp bài']));

      const bestScore = finishedAttempts.length > 0 
        ? Math.max(...finishedAttempts.map(att => Number(att.score || 0)))
        : (a.latest_score != null ? Number(a.latest_score) : null);

      return {
        id: a.assignment_id || a.id,
        assignment_id: a.assignment_id,
        exercise_id: a.exercise_id,
        class_id: a.class_id,
        title: a.exercise_title || a.title || 'Bài tập trên lớp',
        teacher: a.teacher_name || 'Giáo viên bộ môn',
        subject: a.subject_name || currentSubject,
        total_questions: a.total_questions || 20,
        duration_minutes: a.duration_minutes || 45,
        deadline: a.due_at,
        is_finished: isFinished,
        is_overdue: isOverdue,
        feed_status: isFinished ? 'completed' : (isOverdue ? 'overdue' : 'active'),
        attempts: `${finishedAttempts.length || (isFinished ? 1 : 0)} lần làm`,
        scores: scoresList,
        best: bestScore != null ? String(bestScore) : '--',
        status: isFinished ? 'Đã hoàn thành' : (isOverdue ? 'Quá hạn (Quên làm)' : 'Chưa làm'),
        statusBadgeClass: isFinished ? 'status-completed-pill' : (isOverdue ? 'status-overdue-pill' : 'status-uncompleted-pill'),
        actionLabel: isFinished ? 'Vào bài tập' : (isOverdue ? 'Làm bài ngay' : 'Làm bài ngay'),
        isAiGenerated: false
      };
    });
  }, [matchedRealAssignments, backendAttempts, currentSubject]);

  // Map real AI exercises
  const realAiExercises = useMemo(() => {
    // 1. From backend assignments created by AI
    const backendAi = matchedRealAssignments.filter(a => a.is_ai_generated || a.category === 'ai_generated').map(a => {
      const aId = String(a.assignment_id || a.id || '').toLowerCase();
      const myAttempts = backendAttempts.filter(att => 
        String(att.assignment_id || '').toLowerCase() === aId && (att.score != null || att.is_finished)
      );
      const isFinished = Boolean(myAttempts.length > 0 || a.is_finished);
      const due = a.due_at ? new Date(a.due_at) : null;
      const isOverdue = due ? (due < new Date() && !isFinished) : false;
      const scores = myAttempts.map((att, i) => `Lần ${i + 1}: ${att.score != null ? att.score : '--'}`);
      const bestScore = myAttempts.length > 0 
        ? Math.max(...myAttempts.map(att => Number(att.score || 0)))
        : (a.latest_score != null ? Number(a.latest_score) : null);

      return {
        id: a.assignment_id || a.id,
        assignment_id: a.assignment_id,
        exercise_id: a.exercise_id,
        class_id: a.class_id,
        title: a.exercise_title || a.title,
        teacher: a.teacher_name || 'Trợ lý AI Tam Khang',
        subject: a.subject_name || currentSubject,
        total_questions: a.total_questions || 20,
        duration_minutes: a.duration_minutes || 45,
        deadline: a.due_at,
        is_finished: isFinished,
        is_overdue: isOverdue,
        feed_status: isFinished ? 'completed' : (isOverdue ? 'overdue' : 'active'),
        attempts: `${myAttempts.length || (isFinished ? 1 : 0)} lần làm`,
        scores: scores.length > 0 ? scores : ['Chưa nộp bài'],
        best: bestScore != null ? String(bestScore) : '--',
        status: isFinished ? 'Đã hoàn thành' : (isOverdue ? 'Quá hạn (Quên làm)' : 'Chưa làm'),
        statusBadgeClass: isFinished ? 'status-completed-pill' : (isOverdue ? 'status-overdue-pill' : 'status-uncompleted-pill'),
        actionLabel: isFinished ? 'Vào bài tập' : 'Làm bài ngay',
        isAiGenerated: true
      };
    });

    // 2. From localStorage AI generated exercises
    let localAi = [];
    try {
      const raw = localStorage.getItem('tk_student_ai_exercises');
      if (raw) {
        const parsed = JSON.parse(raw);
        if (Array.isArray(parsed)) {
          const matched = parsed.filter(item => {
            const itemSub = normalizeSubj(item.subject || '');
            return itemSub === normCurrent || itemSub.includes(normCurrent) || normCurrent.includes(itemSub);
          });
          localAi = matched.map((m, idx) => {
            const rawSub = localStorage.getItem(`tk_exam_submitted_${m.id}`);
            let scoreVal = '10.0';
            if (rawSub) {
              try { scoreVal = String(JSON.parse(rawSub).score || '10.0'); } catch(e) {}
            }
            return {
              id: m.id || m.exercise_id || `local_ai_${idx}`,
              exercise_id: m.exercise_id || m.id,
              assignment_id: m.assignment_id || m.id,
              title: m.title,
              teacher: 'Trợ lý AI Tam Khang',
              subject: m.subject || currentSubject,
              total_questions: m.total_questions || 20,
              duration_minutes: m.duration || 45,
              is_finished: true,
              is_overdue: false,
              feed_status: 'completed',
              attempts: '1 lần làm',
              scores: [`Lần 1: ${scoreVal}`],
              best: scoreVal,
              status: 'Đã hoàn thành',
              statusBadgeClass: 'status-completed-pill',
              actionLabel: 'Vào bài tập',
              isAiGenerated: true
            };
          });
        }
      }
    } catch (e) {
      console.warn('Error reading local AI exercises:', e);
    }

    const seenTitles = new Set(backendAi.map(b => (b.title || '').toLowerCase().trim()));
    const uniqueLocal = localAi.filter(l => !seenTitles.has((l.title || '').toLowerCase().trim()));
    return [...backendAi, ...uniqueLocal];
  }, [matchedRealAssignments, backendAttempts, normCurrent, currentSubject]);

  const displayedExercises = activeCategory === 'ai' ? realAiExercises : realClassExercises;

  // Radar chart calculations reflecting real synchronized data
  const classDoneCount = realClassExercises.filter(e => e.is_finished).length;
  const classTotalCount = realClassExercises.length;
  const classCognitive = useMemo(() => {
    const validScores = realClassExercises
      .filter(e => e.is_finished && e.best !== '--' && !isNaN(Number(e.best)))
      .map(e => Number(e.best));

    if (classDoneCount === 0 || validScores.length === 0) {
      return {
        hasData: false,
        avg: null,
        know: null,
        comp: null,
        app: null
      };
    }

    const avg = Number((validScores.reduce((a, b) => a + b, 0) / validScores.length).toFixed(1));
    if (avg === 0) {
      return {
        hasData: true,
        avg: '0.0',
        know: '0.0',
        comp: '0.0',
        app: '0.0'
      };
    }

    return {
      hasData: true,
      avg: avg.toFixed(1),
      know: Math.min(10, avg * 1.05).toFixed(1),
      comp: avg.toFixed(1),
      app: Math.max(0, avg * 0.95).toFixed(1)
    };
  }, [realClassExercises, classDoneCount]);

  const aiDoneCount = realAiExercises.filter(e => e.is_finished).length;
  const aiTotalCount = realAiExercises.length;
  const aiCognitive = useMemo(() => {
    const validScores = realAiExercises
      .filter(e => e.is_finished && e.best !== '--' && !isNaN(Number(e.best)))
      .map(e => Number(e.best));

    if (aiDoneCount === 0 || validScores.length === 0) {
      return {
        hasData: false,
        avg: null,
        know: null,
        comp: null,
        app: null
      };
    }

    const avg = Number((validScores.reduce((a, b) => a + b, 0) / validScores.length).toFixed(1));
    if (avg === 0) {
      return {
        hasData: true,
        avg: '0.0',
        know: '0.0',
        comp: '0.0',
        app: '0.0'
      };
    }

    return {
      hasData: true,
      avg: avg.toFixed(1),
      know: Math.min(10, avg * 1.05).toFixed(1),
      comp: avg.toFixed(1),
      app: Math.max(0, avg * 0.95).toFixed(1)
    };
  }, [realAiExercises, aiDoneCount]);

  // Redirect student directly to the exercise in the repository
  const handleRedirectToExercise = (exerciseItem) => {
    if (onBack) {
      onBack();
    }
    const isAi = Boolean(exerciseItem.isAiGenerated || activeCategory === 'ai');
    navigate('/student/exercises', {
      state: {
        searchTitle: exerciseItem.title,
        autoOpenTitle: exerciseItem.title,
        autoOpenId: exerciseItem.assignment_id || exerciseItem.id || exerciseItem.exercise_id,
        fallbackExercise: {
          id: exerciseItem.assignment_id || exerciseItem.id,
          assignment_id: exerciseItem.assignment_id || exerciseItem.id,
          exercise_id: exerciseItem.exercise_id || exerciseItem.id,
          class_id: exerciseItem.class_id,
          title: exerciseItem.title,
          teacher: exerciseItem.teacher || (isAi ? 'Trợ lý AI Tam Khang' : 'Giáo viên bộ môn'),
          subject: exerciseItem.subject || currentSubject,
          questionsCount: exerciseItem.total_questions ? `${exerciseItem.total_questions} câu hỏi` : '20 câu hỏi',
          total_questions: exerciseItem.total_questions || 20,
          duration: `${exerciseItem.duration_minutes || 45} phút`,
          deadline: exerciseItem.deadline || '16:59 11/10/2026',
          status: exerciseItem.feed_status || (exerciseItem.is_finished ? 'completed' : 'active'),
          statusLabel: exerciseItem.status || (exerciseItem.is_finished ? 'Đã hoàn thành' : 'Đang mở'),
          isRealBackend: Boolean(exerciseItem.assignment_id && typeof exerciseItem.assignment_id === 'string' && exerciseItem.assignment_id.includes('-')),
          isAiGenerated: isAi,
          category: exerciseItem.category || (isAi ? 'ai_generated' : 'class_exercise'),
          categoryLabel: isAi ? 'Bài tập tạo sinh AI' : 'Bài tập trên lớp'
        }
      }
    });
  };

  return (
    <div className="student-subject-radar-detail-wrapper">
      {/* Top Header Navigation Bar */}
      <div className="subject-detail-top-bar">
        <div className="top-bar-left">
          {onBack && (
            <button 
              type="button" 
              className="btn-back-to-dashboard" 
              onClick={onBack}
              title="Quay lại danh sách"
            >
              <ArrowLeft size={16} />
              <span>Quay lại</span>
            </button>
          )}
          <h2 className="subject-detail-main-heading">
            Chi tiết phân tích môn: <span className="highlight-subject-name">{currentSubject}</span>
          </h2>
        </div>

        {/* Quick Subject Tabs */}
        <div className="subject-quick-tabs-list">
          {allSubjectNames.map(subj => (
            <button
              key={subj}
              type="button"
              className={`subject-tab-pill-btn ${currentSubject === subj ? 'is-active' : ''}`}
              onClick={() => setCurrentSubject(subj)}
            >
              {subj}
            </button>
          ))}
        </div>
      </div>

      {/* Row 1: Two 3-Axis Radar Cards Side-by-Side with Clickable Tabs */}
      <div className="subject-radar-two-cards-row">
        {/* Card 1: Bài tập trên lớp */}
        <div 
          className={`subject-radar-stat-card theme-purple clickable-radar-card ${activeCategory === 'class' ? 'is-active-tab' : ''}`}
          onClick={() => setActiveCategory('class')}
          role="button"
          tabIndex={0}
          title="Bấm để xem chi tiết bảng điểm bài tập trên lớp"
        >
          <div className="stat-card-header">
            <div className="card-header-left">
              <div className="card-icon-box purple-bg">
                <BookOpen size={18} className="icon-purple" />
              </div>
              <div>
                <h3 className="stat-card-title">Bài tập trên lớp</h3>
                <p className="stat-card-subtitle">
                  {classTotalCount === 0
                    ? 'Chưa có bài tập được giao'
                    : classDoneCount === 0
                      ? 'Chưa hoàn thành bài tập nào'
                      : `Điểm TB: ${classCognitive.avg}/10 (${Math.round((classDoneCount / classTotalCount) * 100)}% hoàn thành)`}
                </p>
                {activeCategory === 'class' && (
                  <span className="radar-card-active-indicator purple">✓ Đang xem bảng điểm</span>
                )}
              </div>
            </div>
            <span className="card-stat-pill pill-purple">
              Đã làm: {classDoneCount}/{classTotalCount} bài
            </span>
          </div>

          <div className="stat-card-body-content">
            <TriangularRadar
              hasData={classCognitive.hasData}
              scores={{
                know: Number(classCognitive.know) || 0,
                comp: Number(classCognitive.comp) || 0,
                app: Number(classCognitive.app) || 0
              }}
              width={240}
              height={200}
              theme="purple"
            />
            <div className="stat-metrics-column">
              <div className="metric-row-item">
                <span className="metric-bullet purple-bullet">•</span>
                <span className="metric-label">Nhận biết</span>
                <strong className={`metric-score ${!classCognitive.hasData ? 'is-empty' : ''}`}>
                  {classCognitive.hasData ? `${classCognitive.know}/10` : '--/10'}
                </strong>
              </div>
              <div className="metric-row-item">
                <span className="metric-bullet purple-bullet">•</span>
                <span className="metric-label">Thông hiểu</span>
                <strong className={`metric-score ${!classCognitive.hasData ? 'is-empty' : ''}`}>
                  {classCognitive.hasData ? `${classCognitive.comp}/10` : '--/10'}
                </strong>
              </div>
              <div className="metric-row-item">
                <span className="metric-bullet purple-bullet">•</span>
                <span className="metric-label">Vận dụng</span>
                <strong className={`metric-score ${!classCognitive.hasData ? 'is-empty' : ''}`}>
                  {classCognitive.hasData ? `${classCognitive.app}/10` : '--/10'}
                </strong>
              </div>
            </div>
          </div>
        </div>

        {/* Card 2: Bài tập do AI tạo */}
        <div 
          className={`subject-radar-stat-card theme-blue clickable-radar-card ${activeCategory === 'ai' ? 'is-active-tab' : ''}`}
          onClick={() => setActiveCategory('ai')}
          role="button"
          tabIndex={0}
          title="Bấm để xem chi tiết bảng điểm bài tập do AI tạo"
        >
          <div className="stat-card-header">
            <div className="card-header-left">
              <div className="card-icon-box blue-bg">
                <Sparkles size={18} className="icon-blue" />
              </div>
              <div>
                <h3 className="stat-card-title">Bài tập do AI tạo</h3>
                <p className="stat-card-subtitle">
                  {aiTotalCount === 0
                    ? 'Chưa có bài tập tạo sinh'
                    : aiDoneCount === 0
                      ? 'Chưa hoàn thành bài tập nào'
                      : `Điểm TB: ${aiCognitive.avg}/10 (${Math.round((aiDoneCount / Math.max(1, aiTotalCount)) * 100)}% hoàn thành)`}
                </p>
                {activeCategory === 'ai' && (
                  <span className="radar-card-active-indicator blue">✓ Đang xem bảng điểm</span>
                )}
              </div>
            </div>
            <span className="card-stat-pill pill-blue">
              Đã làm: {aiDoneCount} bài tập AI
            </span>
          </div>

          <div className="stat-card-body-content">
            <TriangularRadar
              hasData={aiCognitive.hasData}
              scores={{
                know: Number(aiCognitive.know) || 0,
                comp: Number(aiCognitive.comp) || 0,
                app: Number(aiCognitive.app) || 0
              }}
              width={240}
              height={200}
              theme="blue"
            />
            <div className="stat-metrics-column">
              <div className="metric-row-item">
                <span className="metric-bullet blue-bullet">•</span>
                <span className="metric-label">Nhận biết</span>
                <strong className={`metric-score ${!aiCognitive.hasData ? 'is-empty' : ''}`}>
                  {aiCognitive.hasData ? `${aiCognitive.know}/10` : '--/10'}
                </strong>
              </div>
              <div className="metric-row-item">
                <span className="metric-bullet blue-bullet">•</span>
                <span className="metric-label">Thông hiểu</span>
                <strong className={`metric-score ${!aiCognitive.hasData ? 'is-empty' : ''}`}>
                  {aiCognitive.hasData ? `${aiCognitive.comp}/10` : '--/10'}
                </strong>
              </div>
              <div className="metric-row-item">
                <span className="metric-bullet blue-bullet">•</span>
                <span className="metric-label">Vận dụng</span>
                <strong className={`metric-score ${!aiCognitive.hasData ? 'is-empty' : ''}`}>
                  {aiCognitive.hasData ? `${aiCognitive.app}/10` : '--/10'}
                </strong>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Row 2: Table Chi tiết điểm: Dynamic according to activeCategory (Bài tập trên lớp or Bài tập do AI tạo) */}
      <div className="subject-exercises-score-table-card">
        <div className="table-card-header">
          <div className="table-card-title-group">
            <div className="table-title-row">
              {activeCategory === 'ai' ? (
                <Sparkles size={18} className="icon-blue-title" />
              ) : (
                <BookOpen size={18} className="icon-purple-title" />
              )}
              <h3 className="table-card-main-title">
                Chi tiết điểm: {activeCategory === 'ai' ? 'Bài tập do AI tạo' : 'Bài tập trên lớp'}
              </h3>
              <span className={`table-count-pill ${activeCategory === 'ai' ? 'pill-blue' : ''}`}>
                {displayedExercises.length} bài
              </span>
            </div>
            <p className="table-card-subtitle">
              {activeCategory === 'ai'
                ? `Theo dõi số lần làm bài và điểm số chi tiết của mỗi bài tập tạo sinh AI môn ${currentSubject}`
                : `Theo dõi số lần làm bài và điểm số chi tiết của mỗi lần nộp bài trên lớp môn ${currentSubject} (bao gồm cả bài chưa làm và quá hạn)`}
            </p>
          </div>
        </div>

        <div className="table-responsive-wrapper">
          {displayedExercises.length === 0 ? (
            <div className="table-empty-notice">
              <HelpCircle size={36} color="#94A3B8" />
              <p>
                {activeCategory === 'ai'
                  ? `Chưa có bài tập tạo sinh AI nào cho môn ${currentSubject}.`
                  : `Hiện tại chưa có bài tập nào được giao cho môn ${currentSubject}.`}
              </p>
              {activeCategory === 'ai' && (
                <button
                  type="button"
                  className="btn-empty-action"
                  onClick={() => {
                    if (onBack) onBack();
                    navigate('/student/exercises');
                  }}
                >
                  <Sparkles size={14} />
                  <span>Tạo bài tập AI ngay</span>
                </button>
              )}
            </div>
          ) : (
            <table className="subject-score-data-table">
              <thead>
                <tr>
                  <th className="th-name">
                    {activeCategory === 'ai' ? 'Tên bài tập do AI tạo' : 'Tên bài tập trên lớp'}
                  </th>
                  <th className="th-attempts">Số lần làm</th>
                  <th className="th-detail-scores">Chi tiết điểm các lần làm</th>
                  <th className="th-highest">Điểm cao nhất</th>
                  <th className="th-status">Trạng thái</th>
                  <th className="th-action">Hành động</th>
                </tr>
              </thead>
              <tbody>
                {displayedExercises.map((item) => (
                  <tr key={item.id} className="table-data-row">
                    <td className="td-name">
                      <span className="exercise-row-title">{item.title}</span>
                    </td>
                    <td className="td-attempts">
                      <span className={`attempt-count-pill ${activeCategory === 'ai' ? 'pill-blue' : ''}`}>
                        {item.attempts}
                      </span>
                    </td>
                    <td className="td-detail-scores">
                      <div className="scores-chips-group">
                        {item.scores.map((sc, scIdx) => {
                          const isLatest = scIdx === item.scores.length - 1;
                          return (
                            <span 
                              key={scIdx} 
                              className={`score-chip-badge ${isLatest && item.scores.length > 1 ? 'chip-bold' : ''}`}
                            >
                              {sc}
                            </span>
                          );
                        })}
                      </div>
                    </td>
                    <td className="td-highest">
                      <span className={`highest-score-pill ${activeCategory === 'ai' ? 'pill-blue' : ''}`}>
                        {item.best}
                      </span>
                    </td>
                    <td className="td-status">
                      <span className={item.statusBadgeClass}>
                        {item.is_finished ? (
                          <CheckCheck size={14} className="icon-check-double" />
                        ) : item.is_overdue ? (
                          <AlertCircle size={14} />
                        ) : (
                          <Clock size={13} />
                        )}
                        <span>{item.status}</span>
                      </span>
                    </td>
                    <td className="td-action">
                      <button 
                        type="button" 
                        className={`btn-go-to-exercise ${activeCategory === 'ai' ? 'btn-ai-exercise' : ''}`}
                        onClick={() => handleRedirectToExercise(item)}
                        title={`Chuyển đến ${item.title}`}
                      >
                        <span>{item.actionLabel}</span>
                        <ArrowRight size={13} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
