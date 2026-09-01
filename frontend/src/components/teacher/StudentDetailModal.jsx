// File Name: StudentDetailModal.jsx
// Description: Full-screen modal presenting student performance analytics with multi-axis radar chart for all subjects, paginated assignment history across all subjects, and sortable subject final scores.
// Created At: 2026-08-31
// Created By: Tam Khang
// Updated At: 2026-09-01
// Updated By: Tam Khang

import React, { useState, useMemo } from 'react';
import { 
  X, 
  BookOpen, 
  Sparkles, 
  Layers, 
  CheckCircle2,
  CheckCheck,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  ArrowUpDown,
  Filter,
  Printer
} from 'lucide-react';
import StudentTranscriptPrintModal from './StudentTranscriptPrintModal';
import './StudentDetailModal.css';

// Dynamic N-axis SVG Radar Chart Component (supports 3-criteria or 8-subject radar)
function DynamicRadarChart({
  size = 270,
  height = 230,
  values = [9.4, 9.0, 8.6],
  maxScore = 10,
  fillColor = "rgba(124, 58, 237, 0.2)",
  strokeColor = "#7C3AED",
  labels = ['Nhận biết', 'Thông hiểu', 'Vận dụng']
}) {
  const centerX = size / 2;
  const centerY = height / 2;
  const totalAxes = labels.length;
  // Radius calculation: generous padding to avoid label truncation
  const radius = totalAxes > 4 ? size * 0.23 : size * 0.27;
  const angleStep = (Math.PI * 2) / totalAxes;

  // Calculate coordinates for vertices
  const getCoordinates = (val, index) => {
    const angle = index * angleStep - Math.PI / 2;
    const r = (val / maxScore) * radius;
    const x = centerX + r * Math.cos(angle);
    const y = centerY + r * Math.sin(angle);
    return { x, y };
  };

  const levels = [0.33, 0.66, 1.0];

  const polygonPoints = values
    .map((val, idx) => {
      const { x, y } = getCoordinates(val, idx);
      return `${x},${y}`;
    })
    .join(' ');

  // Dynamic label coordinates around radar polygon perimeter
  const getLabelProps = (index) => {
    const angle = index * angleStep - Math.PI / 2;
    const cosVal = Math.cos(angle);
    const sinVal = Math.sin(angle);
    
    const labelDist = radius + (totalAxes > 4 ? 18 : 16);
    const x = centerX + labelDist * cosVal;
    let y = centerY + labelDist * sinVal;

    let textAnchor = 'middle';
    if (cosVal > 0.25) {
      textAnchor = 'start';
    } else if (cosVal < -0.25) {
      textAnchor = 'end';
    }

    if (sinVal > 0.6) {
      y += 3;
    } else if (sinVal < -0.6) {
      y -= 3;
    }

    return { x, y, textAnchor };
  };

  return (
    <div className="three-axis-radar-container">
      <svg width={size} height={height} viewBox={`0 0 ${size} ${height}`} overflow="visible">
        {/* Concentric Grid Polygons */}
        {levels.map((level, lvlIdx) => {
          const points = labels
            .map((_, idx) => {
              const { x, y } = getCoordinates(maxScore * level, idx);
              return `${x},${y}`;
            })
            .join(' ');
          return (
            <polygon
              key={`level-${lvlIdx}`}
              points={points}
              fill={lvlIdx === 0 ? (strokeColor === '#7C3AED' ? "rgba(245, 243, 255, 0.4)" : "rgba(239, 246, 255, 0.4)") : "none"}
              stroke="#E2E8F0"
              strokeWidth="1.2"
              strokeDasharray={lvlIdx === levels.length - 1 ? 'none' : '3,3'}
            />
          );
        })}

        {/* Axis Spokes */}
        {labels.map((_, idx) => {
          const { x: endX, y: endY } = getCoordinates(maxScore, idx);
          return (
            <line
              key={`axis-line-${idx}`}
              x1={centerX}
              y1={centerY}
              x2={endX}
              y2={endY}
              stroke="#CBD5E1"
              strokeWidth="1"
            />
          );
        })}

        {/* Data Polygon */}
        <polygon
          points={polygonPoints}
          fill={fillColor}
          stroke={strokeColor}
          strokeWidth="2.2"
          className="radar-data-polygon"
        />

        {/* Vertex Dots */}
        {values.map((val, idx) => {
          const { x, y } = getCoordinates(val, idx);
          return (
            <circle
              key={`dot-${idx}`}
              cx={x}
              cy={y}
              r="4"
              fill={strokeColor}
              stroke="#FFFFFF"
              strokeWidth="1.6"
            />
          );
        })}

        {/* Text Labels */}
        {labels.map((label, idx) => {
          const { x, y, textAnchor } = getLabelProps(idx);
          return (
            <text
              key={`axis-label-${idx}`}
              x={x}
              y={y}
              textAnchor={textAnchor}
              fontSize={totalAxes > 4 ? "11" : "12"}
              fontWeight="600"
              fill="#334155"
              fontFamily="inherit"
              dominantBaseline="central"
            >
              {label}
            </text>
          );
        })}
      </svg>
    </div>
  );
}

export default function StudentDetailModal({ isOpen, onClose, student, classInfo }) {
  if (!isOpen || !student) return null;

  // 1. Subject filter state for radar charts & assignments ('all' or specific subject)
  const [selectedSubject, setSelectedSubject] = useState('all');

  // 2. Pagination state for both assignment cards
  const [classroomPage, setClassroomPage] = useState(1);
  const [aiPage, setAiPage] = useState(1);
  const itemsPerPage = 3;

  // 3. Sorting & Filtering state for Subject Final Scores Table
  const [scoreSortOrder, setScoreSortOrder] = useState('desc'); // 'desc' (cao đến thấp), 'asc', 'default'
  const [scoreRatingFilter, setScoreRatingFilter] = useState('all');
  const [showPrintModal, setShowPrintModal] = useState(false);

  const subjectOptions = [
    { id: 'all', name: 'Tất cả các môn' },
    { id: 'math', name: 'Toán học' },
    { id: 'physics', name: 'Vật lý' },
    { id: 'chemistry', name: 'Hóa học' },
    { id: 'literature', name: 'Ngữ văn' },
    { id: 'english', name: 'Tiếng Anh' },
    { id: 'biology', name: 'Sinh học' },
    { id: 'history', name: 'Lịch sử' },
    { id: 'informatics', name: 'Tin học' },
  ];

  const currentSubjectObj = subjectOptions.find(s => s.id === selectedSubject) || subjectOptions[0];
  const subjectName = currentSubjectObj.name;
  const className = classInfo?.name || '12A1 - Toán nâng cao';

  const initialName = student.name
    ? student.name.split(' ').map(n => n[0]).slice(-2).join('').toUpperCase()
    : 'HS';

  // Base score for the current view
  const baseScore = selectedSubject === 'all' 
    ? (student.avgScore || 8.5)
    : (student.subjectScores?.[selectedSubject] || student.avgScore || 8.5);

  // Multi-subject labels and values when 'all' is selected
  const allSubjectRadarLabels = ['Toán', 'Vật lý', 'Hóa học', 'Tiếng Anh', 'Ngữ văn', 'Sinh học', 'Lịch sử', 'Tin học'];
  
  const allSubjectClassroomRadarValues = [
    student.subjectScores?.math || 9.2,
    student.subjectScores?.physics || 8.8,
    student.subjectScores?.chemistry || 8.5,
    student.subjectScores?.english || 9.4,
    student.subjectScores?.literature || 8.2,
    student.subjectScores?.biology || 8.2,
    student.subjectScores?.history || 8.7,
    9.6 // Tin học
  ];

  const allSubjectAiRadarValues = [
    (allSubjectClassroomRadarValues[0] * 0.98).toFixed(1),
    (allSubjectClassroomRadarValues[1] * 0.97).toFixed(1),
    (allSubjectClassroomRadarValues[2] * 0.98).toFixed(1),
    (allSubjectClassroomRadarValues[3] * 0.99).toFixed(1),
    (allSubjectClassroomRadarValues[4] * 0.96).toFixed(1),
    (allSubjectClassroomRadarValues[5] * 0.97).toFixed(1),
    (allSubjectClassroomRadarValues[6] * 0.98).toFixed(1),
    (allSubjectClassroomRadarValues[7] * 0.99).toFixed(1),
  ].map(Number);

  // Single-subject 3-criteria values when a specific subject is selected
  const singleSubjectClassroomCriteria = [
    parseFloat((baseScore * 1.02 > 10 ? 9.8 : (baseScore * 1.02)).toFixed(1)),
    parseFloat((baseScore * 0.98).toFixed(1)),
    parseFloat((baseScore * 0.94).toFixed(1))
  ];

  const singleSubjectAiCriteria = [
    parseFloat((baseScore * 0.96).toFixed(1)),
    parseFloat((baseScore * 0.92).toFixed(1)),
    parseFloat((baseScore * 0.88).toFixed(1))
  ];

  // Specific completion counts & percent
  const classroomScores = {
    completedCount: selectedSubject === 'all' ? 42 : selectedSubject === 'math' ? 18 : selectedSubject === 'physics' ? 15 : 16,
    totalCount: selectedSubject === 'all' ? 48 : 20,
    avgPercent: Math.round(baseScore * 10),
    recognition: (baseScore * 1.02 > 10 ? 9.8 : (baseScore * 1.02)).toFixed(1),
    comprehension: (baseScore * 0.98).toFixed(1),
    application: (baseScore * 0.94).toFixed(1),
  };

  const aiScores = {
    completedCount: selectedSubject === 'all' ? 36 : selectedSubject === 'math' ? 14 : selectedSubject === 'physics' ? 12 : 11,
    avgPercent: Math.round(baseScore * 9.7),
    recognition: (baseScore * 0.96).toFixed(1),
    comprehension: (baseScore * 0.92).toFixed(1),
    application: (baseScore * 0.88).toFixed(1),
  };

  // Comprehensive Classroom Assignments list across all subjects
  const allMasterClassroomAssignments = [
    {
      id: 1,
      subjectId: 'math',
      subjectName: 'Toán',
      badgeColor: '#7C3AED',
      title: 'Kiểm tra 15p – Đạo hàm và ứng dụng',
      attemptsCount: 2,
      attemptsDetails: [
        { attempt: 1, score: 7.5, submittedAt: '15/10/2023 14:30' },
        { attempt: 2, score: 9.0, submittedAt: '16/10/2023 09:15' },
      ],
      bestScore: 9.0,
      status: 'Đã hoàn thành',
    },
    {
      id: 2,
      subjectId: 'physics',
      subjectName: 'Vật lý',
      badgeColor: '#2563EB',
      title: 'Kiểm tra 45p – Dao động điều hòa và sóng cơ',
      attemptsCount: 1,
      attemptsDetails: [
        { attempt: 1, score: 8.8, submittedAt: '20/10/2023 10:15' },
      ],
      bestScore: 8.8,
      status: 'Đã hoàn thành',
    },
    {
      id: 3,
      subjectId: 'chemistry',
      subjectName: 'Hóa',
      badgeColor: '#059669',
      title: 'Bài tập về nhà – Este, Lipit và Chất béo',
      attemptsCount: 2,
      attemptsDetails: [
        { attempt: 1, score: 8.0, submittedAt: '25/10/2023 19:30' },
        { attempt: 2, score: 8.5, submittedAt: '26/10/2023 14:20' },
      ],
      bestScore: 8.5,
      status: 'Đã hoàn thành',
    },
    {
      id: 4,
      subjectId: 'english',
      subjectName: 'Tiếng Anh',
      badgeColor: '#0284C7',
      title: 'Kiểm tra 15p – Reading Comprehension Unit 3',
      attemptsCount: 1,
      attemptsDetails: [
        { attempt: 1, score: 9.4, submittedAt: '02/11/2023 08:30' },
      ],
      bestScore: 9.4,
      status: 'Đã hoàn thành',
    },
    {
      id: 5,
      subjectId: 'literature',
      subjectName: 'Ngữ văn',
      badgeColor: '#DC2626',
      title: 'Bài tập tự luận – Phân tích tác phẩm Tây Tiến',
      attemptsCount: 1,
      attemptsDetails: [
        { attempt: 1, score: 8.2, submittedAt: '08/11/2023 21:00' },
      ],
      bestScore: 8.2,
      status: 'Đã hoàn thành',
    },
    {
      id: 6,
      subjectId: 'biology',
      subjectName: 'Sinh học',
      badgeColor: '#16A34A',
      title: 'Kiểm tra 15p – Quy luật di truyền Men-đen',
      attemptsCount: 2,
      attemptsDetails: [
        { attempt: 1, score: 7.8, submittedAt: '14/11/2023 15:40' },
        { attempt: 2, score: 8.2, submittedAt: '15/11/2023 11:20' },
      ],
      bestScore: 8.2,
      status: 'Đã hoàn thành',
    },
    {
      id: 7,
      subjectId: 'informatics',
      subjectName: 'Tin học',
      badgeColor: '#9333EA',
      title: 'Bài tập thực hành – Lập trình Cấu trúc rẽ nhánh',
      attemptsCount: 1,
      attemptsDetails: [
        { attempt: 1, score: 9.6, submittedAt: '18/11/2023 09:10' },
      ],
      bestScore: 9.6,
      status: 'Đã hoàn thành',
    },
    {
      id: 8,
      subjectId: 'history',
      subjectName: 'Lịch sử',
      badgeColor: '#D97706',
      title: 'Kiểm tra 45p – Lịch sử Việt Nam 1919-1930',
      attemptsCount: 1,
      attemptsDetails: [
        { attempt: 1, score: 8.7, submittedAt: '22/11/2023 14:00' },
      ],
      bestScore: 8.7,
      status: 'Đã hoàn thành',
    },
    {
      id: 9,
      subjectId: 'math',
      subjectName: 'Toán',
      badgeColor: '#7C3AED',
      title: 'Bài tập về nhà – Hình học không gian Oxyz',
      attemptsCount: 1,
      attemptsDetails: [
        { attempt: 1, score: 8.5, submittedAt: '26/11/2023 20:15' },
      ],
      bestScore: 8.5,
      status: 'Đã hoàn thành',
    },
  ];

  // Comprehensive AI-Generated Assignments list across all subjects
  const allMasterAiAssignments = [
    {
      id: 1,
      subjectId: 'math',
      subjectName: 'Toán',
      badgeColor: '#7C3AED',
      title: 'Luyện tập AI – Khảo sát hàm số nâng cao',
      attemptsCount: 3,
      attemptsDetails: [
        { attempt: 1, score: 6.5, submittedAt: '18/10/2023 20:00' },
        { attempt: 2, score: 8.0, submittedAt: '19/10/2023 15:45' },
        { attempt: 3, score: 9.2, submittedAt: '20/10/2023 10:20' },
      ],
      bestScore: 9.2,
      status: 'Đã hoàn thành',
    },
    {
      id: 2,
      subjectId: 'physics',
      subjectName: 'Vật lý',
      badgeColor: '#2563EB',
      title: 'Luyện tập AI – Mạch dao động LC và Sóng điện từ',
      attemptsCount: 2,
      attemptsDetails: [
        { attempt: 1, score: 7.8, submittedAt: '24/10/2023 19:30' },
        { attempt: 2, score: 8.8, submittedAt: '25/10/2023 14:10' },
      ],
      bestScore: 8.8,
      status: 'Đã hoàn thành',
    },
    {
      id: 3,
      subjectId: 'chemistry',
      subjectName: 'Hóa',
      badgeColor: '#059669',
      title: 'Luyện tập AI – Bài toán kim loại tác dụng HNO3',
      attemptsCount: 2,
      attemptsDetails: [
        { attempt: 1, score: 8.0, submittedAt: '30/10/2023 20:15' },
        { attempt: 2, score: 8.6, submittedAt: '31/10/2023 16:30' },
      ],
      bestScore: 8.6,
      status: 'Đã hoàn thành',
    },
    {
      id: 4,
      subjectId: 'english',
      subjectName: 'Tiếng Anh',
      badgeColor: '#0284C7',
      title: 'Luyện tập AI – IELTS Vocabulary & Phrasal Verbs',
      attemptsCount: 1,
      attemptsDetails: [
        { attempt: 1, score: 9.5, submittedAt: '05/11/2023 18:40' },
      ],
      bestScore: 9.5,
      status: 'Đã hoàn thành',
    },
    {
      id: 5,
      subjectId: 'literature',
      subjectName: 'Ngữ văn',
      badgeColor: '#DC2626',
      title: 'Luyện tập AI – Phân tích nhân vật văn học hiện thực',
      attemptsCount: 1,
      attemptsDetails: [
        { attempt: 1, score: 8.0, submittedAt: '11/11/2023 21:10' },
      ],
      bestScore: 8.0,
      status: 'Đã hoàn thành',
    },
    {
      id: 6,
      subjectId: 'biology',
      subjectName: 'Sinh học',
      badgeColor: '#16A34A',
      title: 'Luyện tập AI – Đột biến gen và nhiễm sắc thể',
      attemptsCount: 2,
      attemptsDetails: [
        { attempt: 1, score: 7.6, submittedAt: '16/11/2023 19:00' },
        { attempt: 2, score: 8.4, submittedAt: '17/11/2023 15:30' },
      ],
      bestScore: 8.4,
      status: 'Đã hoàn thành',
    },
    {
      id: 7,
      subjectId: 'informatics',
      subjectName: 'Tin học',
      badgeColor: '#9333EA',
      title: 'Luyện tập AI – Thuật toán sắp xếp và tìm kiếm',
      attemptsCount: 1,
      attemptsDetails: [
        { attempt: 1, score: 9.5, submittedAt: '21/11/2023 10:25' },
      ],
      bestScore: 9.5,
      status: 'Đã hoàn thành',
    },
    {
      id: 8,
      subjectId: 'math',
      subjectName: 'Toán',
      badgeColor: '#7C3AED',
      title: 'Luyện tập AI – Tích phân và ứng dụng thực tế',
      attemptsCount: 2,
      attemptsDetails: [
        { attempt: 1, score: 7.8, submittedAt: '25/11/2023 19:30' },
        { attempt: 2, score: 8.8, submittedAt: '26/11/2023 14:10' },
      ],
      bestScore: 8.8,
      status: 'Đã hoàn thành',
    },
  ];

  // Filtered assignments based on current subject filter
  const visibleClassroomAssignments = useMemo(() => {
    if (selectedSubject === 'all') {
      return allMasterClassroomAssignments;
    }
    return allMasterClassroomAssignments.filter(item => item.subjectId === selectedSubject);
  }, [selectedSubject, allMasterClassroomAssignments]);

  const visibleAiAssignments = useMemo(() => {
    if (selectedSubject === 'all') {
      return allMasterAiAssignments;
    }
    return allMasterAiAssignments.filter(item => item.subjectId === selectedSubject);
  }, [selectedSubject, allMasterAiAssignments]);

  // Paginated slices for Classroom & AI assignments
  const totalClassroomPages = Math.max(1, Math.ceil(visibleClassroomAssignments.length / itemsPerPage));
  const pagedClassroomList = visibleClassroomAssignments.slice(
    (classroomPage - 1) * itemsPerPage,
    classroomPage * itemsPerPage
  );

  const totalAiPages = Math.max(1, Math.ceil(visibleAiAssignments.length / itemsPerPage));
  const pagedAiList = visibleAiAssignments.slice(
    (aiPage - 1) * itemsPerPage,
    aiPage * itemsPerPage
  );

  // 3. Full subject final scores dataset for student with 4 regular assessments
  const rawSubjectScores = [
    { id: 'informatics', name: 'Tin học', tx1: 9.5, tx2: 9.5, tx3: 9.5, tx4: 9.6, midterm: 9.8, final: 9.5, avgSubject: 9.6, totalFinal: 9.6, rating: 'Đạt chuẩn giỏi', ratingCode: 'excellent' },
    { id: 'english', name: 'Tiếng Anh', tx1: 9.0, tx2: 9.5, tx3: 9.2, tx4: 9.0, midterm: 9.6, final: 9.4, avgSubject: 9.4, totalFinal: 9.4, rating: 'Đạt chuẩn giỏi', ratingCode: 'excellent' },
    { id: 'math', name: 'Toán học', tx1: 8.5, tx2: 9.0, tx3: 8.8, tx4: 9.2, midterm: 9.5, final: 8.7, avgSubject: 9.2, totalFinal: 9.2, rating: 'Đạt chuẩn giỏi', ratingCode: 'excellent' },
    { id: 'civics', name: 'GDCD', tx1: 9.0, tx2: 9.0, tx3: 9.0, tx4: 9.2, midterm: 9.2, final: 9.0, avgSubject: 9.1, totalFinal: 9.1, rating: 'Đạt chuẩn giỏi', ratingCode: 'excellent' },
    { id: 'physics', name: 'Vật lý', tx1: 8.0, tx2: 8.5, tx3: 8.5, tx4: 9.0, midterm: 9.0, final: 8.8, avgSubject: 8.8, totalFinal: 8.8, rating: 'Đạt chuẩn giỏi', ratingCode: 'excellent' },
    { id: 'history', name: 'Lịch sử', tx1: 8.5, tx2: 8.5, tx3: 8.5, tx4: 8.6, midterm: 8.6, final: 8.8, avgSubject: 8.7, totalFinal: 8.7, rating: 'Đạt chuẩn giỏi', ratingCode: 'excellent' },
    { id: 'chemistry', name: 'Hóa học', tx1: 8.0, tx2: 8.2, tx3: 8.5, tx4: 8.0, midterm: 8.5, final: 8.6, avgSubject: 8.5, totalFinal: 8.5, rating: 'Đạt chuẩn giỏi', ratingCode: 'excellent' },
    { id: 'literature', name: 'Ngữ văn', tx1: 7.5, tx2: 8.0, tx3: 7.8, tx4: 8.0, midterm: 8.2, final: 8.5, avgSubject: 8.2, totalFinal: 8.2, rating: 'Đạt chuẩn giỏi', ratingCode: 'excellent' },
    { id: 'biology', name: 'Sinh học', tx1: 8.0, tx2: 8.0, tx3: 8.2, tx4: 8.0, midterm: 8.4, final: 8.2, avgSubject: 8.2, totalFinal: 8.2, rating: 'Đạt chuẩn giỏi', ratingCode: 'excellent' },
    { id: 'geography', name: 'Địa lý', tx1: 7.0, tx2: 7.5, tx3: 7.5, tx4: 8.0, midterm: 8.0, final: 7.8, avgSubject: 7.8, totalFinal: 7.8, rating: 'Đạt chuẩn khá', ratingCode: 'good' },
  ];

  // Filter & Sort Subject Final Scores
  const filteredAndSortedSubjectScores = useMemo(() => {
    let list = [...rawSubjectScores];

    if (scoreRatingFilter !== 'all') {
      list = list.filter(item => item.ratingCode === scoreRatingFilter);
    }

    if (scoreSortOrder === 'desc') {
      list.sort((a, b) => b.totalFinal - a.totalFinal);
    } else if (scoreSortOrder === 'asc') {
      list.sort((a, b) => a.totalFinal - b.totalFinal);
    }

    return list;
  }, [rawSubjectScores, scoreSortOrder, scoreRatingFilter]);

  return (
    <div className="student-modal-overlay">
      <div className="student-modal-window">
        {/* Top Header: Student Info on Left & Close on Right */}
        <header className="student-modal-topbar">
          <div className="topbar-left">
            <div className="topbar-brand">
              <div className="brand-logo-icon">
                <Layers size={18} color="#FFFFFF" />
              </div>
              <span className="brand-title">Academic Clarity LMS</span>
            </div>

            <div className="topbar-divider"></div>

            {/* Student Info in Top-Left Header */}
            <div className="student-header-pill">
              <div className="student-avatar-small">
                {initialName}
              </div>
              <div className="student-pill-text">
                <span className="student-pill-name">{student.name}</span>
                <span className="student-pill-code">Mã HS: {student.code}</span>
              </div>
            </div>
          </div>

          <div className="topbar-right">
            <span className="class-badge-topbar">{className}</span>
            {/* Close Button */}
            <button 
              type="button" 
              className="btn-modal-close"
              onClick={onClose}
              title="Đóng cửa sổ"
            >
              <X size={20} />
            </button>
          </div>
        </header>

        {/* Scrollable Content Body */}
        <div className="student-modal-content">
          {/* Main Title Section with Subject Filter */}
          <div className="modal-title-row">
            <div className="title-text-group">
              <h1 className="modal-page-title">
                Bảng theo dõi năng lực học sinh: Học kỳ 1, 2023–2024
              </h1>
              <p className="modal-page-subtitle">
                Chi tiết kết quả làm bài tập, biểu đồ năng lực theo chuẩn kiến thức và bảng điểm {selectedSubject === 'all' ? 'tổng hợp tất cả các môn' : `môn ${subjectName}`}.
              </p>
            </div>

            {/* Subject Filter Dropdown for Competency & Assignments */}
            <div className="modal-subject-filter-box">
              <span className="filter-box-label">Phân loại theo môn:</span>
              <div className="subject-select-container">
                <select 
                  className="modal-subject-select"
                  value={selectedSubject}
                  onChange={(e) => {
                    setSelectedSubject(e.target.value);
                    setClassroomPage(1);
                    setAiPage(1);
                  }}
                >
                  {subjectOptions.map(opt => (
                    <option key={opt.id} value={opt.id}>{opt.name}</option>
                  ))}
                </select>
                <ChevronDown size={14} className="subject-select-arrow" />
              </div>
            </div>
          </div>

          {/* Dual Radar Charts Row with Completion Counters (All Subjects or Specific Criteria) */}
          <div className="radar-charts-grid">
            {/* Radar Card 1: Classroom Assignments */}
            <div className="radar-card">
              <div className="radar-card-header">
                <div className="radar-card-icon purple-bg">
                  <BookOpen size={18} color="#7C3AED" />
                </div>
                <div className="radar-header-info">
                  <div className="radar-title-badge-row">
                    <h3 className="radar-card-title">Bài tập trên lớp</h3>
                    <span className="stat-count-badge purple-stat">
                      {selectedSubject === 'all' 
                        ? `Tổng đã làm: ${classroomScores.completedCount}/${classroomScores.totalCount} bài`
                        : `Đã làm: ${classroomScores.completedCount}/${classroomScores.totalCount} bài`}
                    </span>
                  </div>
                  <span className="radar-card-subtitle">{classroomScores.avgPercent}% Điểm trung bình hoàn thành</span>
                </div>
              </div>

              <div className="radar-card-body">
                <DynamicRadarChart
                  size={270}
                  height={230}
                  values={selectedSubject === 'all' ? allSubjectClassroomRadarValues : singleSubjectClassroomCriteria}
                  fillColor="rgba(124, 58, 237, 0.2)"
                  strokeColor="#7C3AED"
                  labels={selectedSubject === 'all' ? allSubjectRadarLabels : ['Nhận biết', 'Thông hiểu', 'Vận dụng']}
                />

                <div className="radar-breakdown-list">
                  {selectedSubject === 'all' ? (
                    <>
                      <div className="breakdown-item">
                        <span className="dot dot-purple"></span>
                        <span className="breakdown-label">Toán học</span>
                        <span className="breakdown-value">9.2/10</span>
                      </div>
                      <div className="breakdown-item">
                        <span className="dot dot-indigo"></span>
                        <span className="breakdown-label">Tin học</span>
                        <span className="breakdown-value">9.6/10</span>
                      </div>
                      <div className="breakdown-item">
                        <span className="dot dot-sky"></span>
                        <span className="breakdown-label">Tiếng Anh</span>
                        <span className="breakdown-value">9.4/10</span>
                      </div>
                      <div className="breakdown-item">
                        <span className="dot dot-lavender"></span>
                        <span className="breakdown-label">Vật lý</span>
                        <span className="breakdown-value">8.8/10</span>
                      </div>
                      <div className="breakdown-item">
                        <span className="dot dot-violet"></span>
                        <span className="breakdown-label">Lịch sử</span>
                        <span className="breakdown-value">8.7/10</span>
                      </div>
                    </>
                  ) : (
                    <>
                      <div className="breakdown-item">
                        <span className="dot dot-purple"></span>
                        <span className="breakdown-label">Nhận biết</span>
                        <span className="breakdown-value">{classroomScores.recognition}/10</span>
                      </div>
                      <div className="breakdown-item">
                        <span className="dot dot-lavender"></span>
                        <span className="breakdown-label">Thông hiểu</span>
                        <span className="breakdown-value">{classroomScores.comprehension}/10</span>
                      </div>
                      <div className="breakdown-item">
                        <span className="dot dot-violet"></span>
                        <span className="breakdown-label">Vận dụng</span>
                        <span className="breakdown-value">{classroomScores.application}/10</span>
                      </div>
                    </>
                  )}
                </div>
              </div>
            </div>

            {/* Radar Card 2: AI-Generated Assignments */}
            <div className="radar-card">
              <div className="radar-card-header">
                <div className="radar-card-icon blue-bg">
                  <Sparkles size={18} color="#2563EB" />
                </div>
                <div className="radar-header-info">
                  <div className="radar-title-badge-row">
                    <h3 className="radar-card-title">Bài tập do AI tạo</h3>
                    <span className="stat-count-badge blue-stat">
                      {selectedSubject === 'all' 
                        ? `Tổng đã làm: ${aiScores.completedCount} bài tập AI`
                        : `Đã làm: ${aiScores.completedCount} bài tập AI`}
                    </span>
                  </div>
                  <span className="radar-card-subtitle">{aiScores.avgPercent}% Điểm trung bình hoàn thành</span>
                </div>
              </div>

              <div className="radar-card-body">
                <DynamicRadarChart
                  size={270}
                  height={230}
                  values={selectedSubject === 'all' ? allSubjectAiRadarValues : singleSubjectAiCriteria}
                  fillColor="rgba(37, 99, 235, 0.18)"
                  strokeColor="#2563EB"
                  labels={selectedSubject === 'all' ? allSubjectRadarLabels : ['Nhận biết', 'Thông hiểu', 'Vận dụng']}
                />

                <div className="radar-breakdown-list">
                  {selectedSubject === 'all' ? (
                    <>
                      <div className="breakdown-item">
                        <span className="dot dot-blue"></span>
                        <span className="breakdown-label">Toán học</span>
                        <span className="breakdown-value">9.0/10</span>
                      </div>
                      <div className="breakdown-item">
                        <span className="dot dot-indigo"></span>
                        <span className="breakdown-label">Tin học</span>
                        <span className="breakdown-value">9.5/10</span>
                      </div>
                      <div className="breakdown-item">
                        <span className="dot dot-sky"></span>
                        <span className="breakdown-label">Tiếng Anh</span>
                        <span className="breakdown-value">9.2/10</span>
                      </div>
                      <div className="breakdown-item">
                        <span className="dot dot-violet"></span>
                        <span className="breakdown-label">Vật lý</span>
                        <span className="breakdown-value">8.6/10</span>
                      </div>
                      <div className="breakdown-item">
                        <span className="dot dot-lavender"></span>
                        <span className="breakdown-label">Hóa học</span>
                        <span className="breakdown-value">8.4/10</span>
                      </div>
                    </>
                  ) : (
                    <>
                      <div className="breakdown-item">
                        <span className="dot dot-blue"></span>
                        <span className="breakdown-label">Nhận biết</span>
                        <span className="breakdown-value">{aiScores.recognition}/10</span>
                      </div>
                      <div className="breakdown-item">
                        <span className="dot dot-sky"></span>
                        <span className="breakdown-label">Thông hiểu</span>
                        <span className="breakdown-value">{aiScores.comprehension}/10</span>
                      </div>
                      <div className="breakdown-item">
                        <span className="dot dot-indigo"></span>
                        <span className="breakdown-label">Vận dụng</span>
                        <span className="breakdown-value">{aiScores.application}/10</span>
                      </div>
                    </>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Section 1: Separate Table for Classroom Assignments with Pageable */}
          <div className="academic-scores-card">
            <div className="scores-card-header">
              <div className="scores-header-left">
                <div className="section-title-with-icon">
                  <BookOpen size={18} color="#7C3AED" />
                  <h3 className="scores-card-title">Chi tiết điểm: Bài tập trên lớp</h3>
                  <span className="count-pill purple-pill">{visibleClassroomAssignments.length} bài</span>
                </div>
                <span className="scores-card-subtitle">
                  Theo dõi số lần làm bài và điểm số chi tiết của mỗi lần nộp bài trên lớp {selectedSubject === 'all' ? 'tổng hợp tất cả các môn' : `môn ${subjectName}`}
                </span>
              </div>
            </div>

            <div className="scores-table-wrapper">
              <table className="single-subject-table">
                <thead>
                  <tr>
                    <th>Tên bài tập trên lớp</th>
                    {selectedSubject === 'all' && <th>Môn học</th>}
                    <th>Số lần làm</th>
                    <th>Chi tiết điểm các lần làm</th>
                    <th>Điểm cao nhất</th>
                    <th>Trạng thái</th>
                  </tr>
                </thead>
                <tbody>
                  {pagedClassroomList.length > 0 ? (
                    pagedClassroomList.map((item) => (
                      <tr key={item.id} className="single-subject-row">
                        <td className="td-subject-name">
                          <strong>{item.title}</strong>
                        </td>
                        {selectedSubject === 'all' && (
                          <td>
                            <span 
                              className="td-subject-badge"
                              style={{ backgroundColor: `${item.badgeColor}18`, color: item.badgeColor, borderColor: `${item.badgeColor}35` }}
                            >
                              {item.subjectName}
                            </span>
                          </td>
                        )}
                        <td>
                          <span className="attempt-count-badge purple-badge">
                            {item.attemptsCount} lần làm
                          </span>
                        </td>
                        <td>
                          <div className="attempts-score-pills">
                            {item.attemptsDetails.map((att) => (
                              <span key={att.attempt} className="attempt-detail-pill" title={`Nộp lúc: ${att.submittedAt}`}>
                                Lần {att.attempt}: <strong>{att.score.toFixed(1)}</strong>
                              </span>
                            ))}
                          </div>
                        </td>
                        <td>
                          <span className="score-pill pill-purple">
                            {item.bestScore.toFixed(1)}
                          </span>
                        </td>
                        <td>
                          <span className="status-badge badge-good">
                            <CheckCheck size={14} className="status-icon" />
                            <span>{item.status}</span>
                          </span>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={selectedSubject === 'all' ? 6 : 5} className="empty-table-cell">
                        Chưa có dữ liệu bài tập trên lớp cho môn học này.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination Controls for Classroom Assignments */}
            {visibleClassroomAssignments.length > 0 && (
              <div className="card-table-pagination">
                <span className="pagination-text">
                  Hiển thị {(classroomPage - 1) * itemsPerPage + 1} - {Math.min(classroomPage * itemsPerPage, visibleClassroomAssignments.length)} trong số {visibleClassroomAssignments.length} bài
                </span>
                <div className="pagination-action-btns">
                  <button
                    type="button"
                    className="btn-page-step"
                    disabled={classroomPage === 1}
                    onClick={() => setClassroomPage(prev => Math.max(1, prev - 1))}
                    title="Trang trước"
                  >
                    <ChevronLeft size={15} />
                  </button>
                  {Array.from({ length: totalClassroomPages }, (_, i) => i + 1).map((p) => (
                    <button
                      key={p}
                      type="button"
                      className={`btn-page-idx ${classroomPage === p ? 'active' : ''}`}
                      onClick={() => setClassroomPage(p)}
                    >
                      {p}
                    </button>
                  ))}
                  <button
                    type="button"
                    className="btn-page-step"
                    disabled={classroomPage === totalClassroomPages}
                    onClick={() => setClassroomPage(prev => Math.min(totalClassroomPages, prev + 1))}
                    title="Trang sau"
                  >
                    <ChevronRight size={15} />
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Section 2: Separate Table for AI-Generated Assignments with Pageable */}
          <div className="academic-scores-card">
            <div className="scores-card-header">
              <div className="scores-header-left">
                <div className="section-title-with-icon">
                  <Sparkles size={18} color="#2563EB" />
                  <h3 className="scores-card-title">Chi tiết điểm: Bài tập do AI tạo</h3>
                  <span className="count-pill blue-pill">{visibleAiAssignments.length} bài</span>
                </div>
                <span className="scores-card-subtitle">
                  Theo dõi số lần làm bài và điểm số chi tiết của các bài tập tự luyện do AI tạo {selectedSubject === 'all' ? 'tổng hợp tất cả các môn' : `môn ${subjectName}`}
                </span>
              </div>
            </div>

            <div className="scores-table-wrapper">
              <table className="single-subject-table">
                <thead>
                  <tr>
                    <th>Tên bài tập AI</th>
                    {selectedSubject === 'all' && <th>Môn học</th>}
                    <th>Số lần làm</th>
                    <th>Chi tiết điểm các lần làm</th>
                    <th>Điểm cao nhất</th>
                    <th>Trạng thái</th>
                  </tr>
                </thead>
                <tbody>
                  {pagedAiList.length > 0 ? (
                    pagedAiList.map((item) => (
                      <tr key={item.id} className="single-subject-row">
                        <td className="td-subject-name">
                          <strong>{item.title}</strong>
                        </td>
                        {selectedSubject === 'all' && (
                          <td>
                            <span 
                              className="td-subject-badge"
                              style={{ backgroundColor: `${item.badgeColor}18`, color: item.badgeColor, borderColor: `${item.badgeColor}35` }}
                            >
                              {item.subjectName}
                            </span>
                          </td>
                        )}
                        <td>
                          <span className="attempt-count-badge blue-badge">
                            {item.attemptsCount} lần làm
                          </span>
                        </td>
                        <td>
                          <div className="attempts-score-pills">
                            {item.attemptsDetails.map((att) => (
                              <span key={att.attempt} className="attempt-detail-pill" title={`Nộp lúc: ${att.submittedAt}`}>
                                Lần {att.attempt}: <strong>{att.score.toFixed(1)}</strong>
                              </span>
                            ))}
                          </div>
                        </td>
                        <td>
                          <span className="score-pill pill-blue">
                            {item.bestScore.toFixed(1)}
                          </span>
                        </td>
                        <td>
                          <span className="status-badge badge-good">
                            <CheckCheck size={14} className="status-icon" />
                            <span>{item.status}</span>
                          </span>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={selectedSubject === 'all' ? 6 : 5} className="empty-table-cell">
                        Chưa có dữ liệu bài tập AI cho môn học này.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination Controls for AI Assignments */}
            {visibleAiAssignments.length > 0 && (
              <div className="card-table-pagination">
                <span className="pagination-text">
                  Hiển thị {(aiPage - 1) * itemsPerPage + 1} - {Math.min(aiPage * itemsPerPage, visibleAiAssignments.length)} trong số {visibleAiAssignments.length} bài
                </span>
                <div className="pagination-action-btns">
                  <button
                    type="button"
                    className="btn-page-step"
                    disabled={aiPage === 1}
                    onClick={() => setAiPage(prev => Math.max(1, prev - 1))}
                    title="Trang trước"
                  >
                    <ChevronLeft size={15} />
                  </button>
                  {Array.from({ length: totalAiPages }, (_, i) => i + 1).map((p) => (
                    <button
                      key={p}
                      type="button"
                      className={`btn-page-idx ${aiPage === p ? 'active' : ''}`}
                      onClick={() => setAiPage(p)}
                    >
                      {p}
                    </button>
                  ))}
                  <button
                    type="button"
                    className="btn-page-step"
                    disabled={aiPage === totalAiPages}
                    onClick={() => setAiPage(prev => Math.min(totalAiPages, prev + 1))}
                    title="Trang sau"
                  >
                    <ChevronRight size={15} />
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Section 3: Subject Final Academic Scores Summary Table with High-to-Low Sort Filter */}
          <div className="academic-scores-card">
            <div className="scores-card-header">
              <div className="scores-header-left">
                <div className="section-title-with-icon">
                  <CheckCircle2 size={18} color="#059669" />
                  <h3 className="scores-card-title">Bảng điểm trung bình môn học</h3>
                </div>
                <span className="scores-card-subtitle">
                  Học kỳ 1 • Khối 12 • Lớp 12A1 • Tổng cộng {filteredAndSortedSubjectScores.length} môn học
                </span>
              </div>

              {/* Sorting, Rating Filter & Export Controls */}
              <div className="scores-header-controls">
                {/* Rating Filter */}
                <div className="score-control-item">
                  <Filter size={14} className="control-icon" />
                  <select 
                    className="score-filter-select"
                    value={scoreRatingFilter}
                    onChange={(e) => setScoreRatingFilter(e.target.value)}
                  >
                    <option value="all">Tất cả xếp loại</option>
                    <option value="excellent">Đạt chuẩn giỏi</option>
                    <option value="good">Đạt chuẩn khá</option>
                  </select>
                  <ChevronDown size={13} className="control-arrow" />
                </div>

                {/* Score Sorting (Cao tới thấp / Thấp tới cao) */}
                <div className="score-control-item sort-control">
                  <ArrowUpDown size={14} className="control-icon" />
                  <select 
                    className="score-filter-select"
                    value={scoreSortOrder}
                    onChange={(e) => setScoreSortOrder(e.target.value)}
                  >
                    <option value="desc">Điểm tổng kết: Cao đến thấp</option>
                    <option value="asc">Điểm tổng kết: Thấp đến cao</option>
                    <option value="default">Thứ tự môn học mặc định</option>
                  </select>
                  <ChevronDown size={13} className="control-arrow" />
                </div>

                {/* Export / Print Transcript Button */}
                <button
                  type="button"
                  className="btn-print-transcript"
                  onClick={() => setShowPrintModal(true)}
                  title="In phiếu điểm học kỳ A4"
                >
                  <Printer size={14} />
                  <span>Xuất bảng điểm</span>
                </button>
              </div>
            </div>

            <div className="scores-table-wrapper">
              <table className="single-subject-table detail-grades-table">
                <thead>
                  <tr>
                    <th rowSpan="2" className="th-main-subj">Môn học</th>
                    <th colSpan="4" className="th-regular-header">Kiểm tra thường xuyên</th>
                    <th rowSpan="2">Điểm Giữa kỳ</th>
                    <th rowSpan="2">Điểm Cuối kỳ</th>
                    <th rowSpan="2">Điểm Trung bình môn</th>
                    <th rowSpan="2">Điểm Tổng kết</th>
                    <th rowSpan="2">Đánh giá</th>
                  </tr>
                  <tr>
                    <th className="th-sub-tx">TX1</th>
                    <th className="th-sub-tx">TX2</th>
                    <th className="th-sub-tx">TX3</th>
                    <th className="th-sub-tx">TX4</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredAndSortedSubjectScores.map((row) => (
                    <tr key={row.id} className="single-subject-row">
                      <td className="td-subject-name">
                        <strong>{row.name}</strong>
                      </td>
                      <td>
                        <span className="score-pill pill-green">
                          {row.tx1.toFixed(1)}
                        </span>
                      </td>
                      <td>
                        <span className="score-pill pill-green">
                          {row.tx2.toFixed(1)}
                        </span>
                      </td>
                      <td>
                        <span className="score-pill pill-green">
                          {row.tx3.toFixed(1)}
                        </span>
                      </td>
                      <td>
                        <span className="score-pill pill-green">
                          {row.tx4.toFixed(1)}
                        </span>
                      </td>
                      <td>
                        <span className="score-pill pill-blue-score">
                          {row.midterm.toFixed(1)}
                        </span>
                      </td>
                      <td>
                        <span className="score-pill pill-red-score">
                          {row.final.toFixed(1)}
                        </span>
                      </td>
                      <td>
                        <span className="score-pill pill-purple">
                          {row.avgSubject.toFixed(1)}
                        </span>
                      </td>
                      <td>
                        <span className="score-pill pill-purple bold-score">
                          {row.totalFinal.toFixed(1)}
                        </span>
                      </td>
                      <td>
                        <span className={`status-badge ${row.ratingCode === 'excellent' ? 'badge-good' : 'badge-fair'}`}>
                          <CheckCircle2 size={13} className="status-icon" />
                          <span>{row.rating}</span>
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      {/* Printable A4 Student Semester Transcript Modal */}
      {showPrintModal && (
        <StudentTranscriptPrintModal
          isOpen={showPrintModal}
          onClose={() => setShowPrintModal(false)}
          student={student}
          classInfo={classInfo}
        />
      )}
    </div>
  );
}
