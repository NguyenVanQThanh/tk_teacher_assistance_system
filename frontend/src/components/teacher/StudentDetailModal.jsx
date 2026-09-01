// File Name: StudentDetailModal.jsx
// Description: Full-screen modal presenting student performance analytics with separate tables for Classroom vs AI assignments, and subject final scores.
// Created At: 2026-08-31
// Created By: Tam Khang
// Updated At: 2026-08-31
// Updated By: Tam Khang

import React from 'react';
import { 
  X, 
  BookOpen, 
  Sparkles, 
  Layers, 
  CheckCircle2,
  CheckCheck
} from 'lucide-react';
import './StudentDetailModal.css';

// 3-axis SVG Radar Chart Component for "Nhận biết - Thông hiểu - Vận dụng" with generous label padding
function ThreeAxisRadarChart({
  size = 240,
  values = [9.4, 9.0, 8.6], // [Nhận biết, Thông hiểu, Vận dụng]
  maxScore = 10,
  fillColor = "rgba(124, 58, 237, 0.2)",
  strokeColor = "#7C3AED",
  labels = ['Nhận biết', 'Thông hiểu', 'Vận dụng']
}) {
  const center = size / 2;
  const radius = size * 0.30;
  const totalAxes = 3;
  const angleStep = (Math.PI * 2) / totalAxes;

  // Calculate coordinates for vertices
  const getCoordinates = (value, index) => {
    const angle = index * angleStep - Math.PI / 2;
    const r = (value / maxScore) * radius;
    const x = center + r * Math.cos(angle);
    const y = center + r * Math.sin(angle);
    return { x, y };
  };

  const levels = [0.33, 0.66, 1.0];

  const polygonPoints = values
    .map((val, idx) => {
      const { x, y } = getCoordinates(val, idx);
      return `${x},${y}`;
    })
    .join(' ');

  // Explicit label positions to prevent text truncation
  const getLabelProps = (index) => {
    if (index === 0) {
      // Top: Nhận biết
      return {
        x: center,
        y: center - radius - 14,
        textAnchor: 'middle',
      };
    } else if (index === 1) {
      // Bottom Right: Thông hiểu
      return {
        x: center + radius * 0.866 + 8,
        y: center + radius * 0.5 + 18,
        textAnchor: 'start',
      };
    } else {
      // Bottom Left: Vận dụng
      return {
        x: center - radius * 0.866 - 8,
        y: center + radius * 0.5 + 18,
        textAnchor: 'end',
      };
    }
  };

  return (
    <div className="three-axis-radar-container">
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        {/* Concentric Triangles */}
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
              fill={lvlIdx === 0 ? "rgba(245, 243, 255, 0.4)" : "none"}
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
              x1={center}
              y1={center}
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
              r="4.5"
              fill={strokeColor}
              stroke="#FFFFFF"
              strokeWidth="1.8"
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
              fontSize="12"
              fontWeight="600"
              fill="#334155"
              fontFamily="inherit"
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

  const initialName = student.name
    ? student.name.split(' ').map(n => n[0]).slice(-2).join('').toUpperCase()
    : 'HS';

  const subjectName = classInfo?.subjectName || 'Toán học';
  const className = classInfo?.name || '12A1 - Toán nâng cao';

  // Specific 3-criteria values for Classroom & AI assignments
  const classroomScores = {
    completedCount: 18,
    totalCount: 20,
    avgPercent: 88,
    recognition: (student.avgScore * 1.02 > 10 ? 9.8 : (student.avgScore * 1.02)).toFixed(1), // Nhận biết
    comprehension: (student.avgScore * 0.98).toFixed(1), // Thông hiểu
    application: (student.avgScore * 0.94).toFixed(1), // Vận dụng
  };

  const aiScores = {
    completedCount: 14,
    avgPercent: 85,
    recognition: (student.avgScore * 0.96).toFixed(1),
    comprehension: (student.avgScore * 0.92).toFixed(1),
    application: (student.avgScore * 0.88).toFixed(1),
  };

  // 1. Separate Classroom Assignments list
  const classroomAssignmentsHistory = [
    {
      id: 1,
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
      title: 'Bài tập về nhà – Hình học không gian Oxyz',
      attemptsCount: 1,
      attemptsDetails: [
        { attempt: 1, score: 8.5, submittedAt: '25/10/2023 21:00' },
      ],
      bestScore: 8.5,
      status: 'Đã hoàn thành',
    },
    {
      id: 3,
      title: 'Kiểm tra 45p – Khảo sát sự biến thiên hàm số',
      attemptsCount: 1,
      attemptsDetails: [
        { attempt: 1, score: 9.2, submittedAt: '05/11/2023 08:45' },
      ],
      bestScore: 9.2,
      status: 'Đã hoàn thành',
    },
  ];

  // 2. Separate AI-Generated Assignments list
  const aiAssignmentsHistory = [
    {
      id: 1,
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
      title: 'Luyện tập AI – Tích phân và ứng dụng thực tế',
      attemptsCount: 2,
      attemptsDetails: [
        { attempt: 1, score: 7.8, submittedAt: '02/11/2023 19:30' },
        { attempt: 2, score: 8.8, submittedAt: '03/11/2023 14:10' },
      ],
      bestScore: 8.8,
      status: 'Đã hoàn thành',
    },
    {
      id: 3,
      title: 'Luyện tập AI – Phương trình mặt phẳng và đường thẳng',
      attemptsCount: 2,
      attemptsDetails: [
        { attempt: 1, score: 8.0, submittedAt: '10/11/2023 20:15' },
        { attempt: 2, score: 8.5, submittedAt: '11/11/2023 16:30' },
      ],
      bestScore: 8.5,
      status: 'Đã hoàn thành',
    },
  ];

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
          {/* Main Title Section */}
          <div className="modal-title-row">
            <div>
              <h1 className="modal-page-title">
                Bảng theo dõi năng lực học sinh: Học kỳ 1, 2023–2024
              </h1>
              <p className="modal-page-subtitle">
                Chi tiết kết quả làm bài tập, biểu đồ năng lực theo chuẩn kiến thức và bảng điểm môn {subjectName}.
              </p>
            </div>
          </div>

          {/* Dual 3-Axis Radar Charts Row with Completion Counters */}
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
                      Đã làm: {classroomScores.completedCount}/{classroomScores.totalCount} bài
                    </span>
                  </div>
                  <span className="radar-card-subtitle">{classroomScores.avgPercent}% Điểm trung bình hoàn thành</span>
                </div>
              </div>

              <div className="radar-card-body">
                <ThreeAxisRadarChart
                  size={230}
                  values={[
                    parseFloat(classroomScores.recognition),
                    parseFloat(classroomScores.comprehension),
                    parseFloat(classroomScores.application),
                  ]}
                  fillColor="rgba(124, 58, 237, 0.2)"
                  strokeColor="#7C3AED"
                  labels={['Nhận biết', 'Thông hiểu', 'Vận dụng']}
                />

                <div className="radar-breakdown-list">
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
                      Đã làm: {aiScores.completedCount} bài tập AI
                    </span>
                  </div>
                  <span className="radar-card-subtitle">{aiScores.avgPercent}% Điểm trung bình hoàn thành</span>
                </div>
              </div>

              <div className="radar-card-body">
                <ThreeAxisRadarChart
                  size={230}
                  values={[
                    parseFloat(aiScores.recognition),
                    parseFloat(aiScores.comprehension),
                    parseFloat(aiScores.application),
                  ]}
                  fillColor="rgba(37, 99, 235, 0.18)"
                  strokeColor="#2563EB"
                  labels={['Nhận biết', 'Thông hiểu', 'Vận dụng']}
                />

                <div className="radar-breakdown-list">
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
                </div>
              </div>
            </div>
          </div>

          {/* Section 1: Separate Table for Classroom Assignments */}
          <div className="academic-scores-card">
            <div className="scores-card-header">
              <div className="scores-header-left">
                <div className="section-title-with-icon">
                  <BookOpen size={18} color="#7C3AED" />
                  <h3 className="scores-card-title">Chi tiết điểm: Bài tập trên lớp</h3>
                  <span className="count-pill purple-pill">{classroomAssignmentsHistory.length} bài</span>
                </div>
                <span className="scores-card-subtitle">
                  Theo dõi số lần làm bài và điểm số chi tiết của mỗi lần nộp bài trên lớp
                </span>
              </div>
            </div>

            <div className="scores-table-wrapper">
              <table className="single-subject-table">
                <thead>
                  <tr>
                    <th>Tên bài tập trên lớp</th>
                    <th>Số lần làm</th>
                    <th>Chi tiết điểm các lần làm</th>
                    <th>Điểm cao nhất</th>
                    <th>Trạng thái</th>
                  </tr>
                </thead>
                <tbody>
                  {classroomAssignmentsHistory.map((item) => (
                    <tr key={item.id} className="single-subject-row">
                      <td className="td-subject-name">
                        <strong>{item.title}</strong>
                      </td>
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
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Section 2: Separate Table for AI-Generated Assignments */}
          <div className="academic-scores-card">
            <div className="scores-card-header">
              <div className="scores-header-left">
                <div className="section-title-with-icon">
                  <Sparkles size={18} color="#2563EB" />
                  <h3 className="scores-card-title">Chi tiết điểm: Bài tập do AI tạo</h3>
                  <span className="count-pill blue-pill">{aiAssignmentsHistory.length} bài</span>
                </div>
                <span className="scores-card-subtitle">
                  Theo dõi số lần làm bài và điểm số chi tiết của các bài tập tự luyện do AI tạo
                </span>
              </div>
            </div>

            <div className="scores-table-wrapper">
              <table className="single-subject-table">
                <thead>
                  <tr>
                    <th>Tên bài tập AI</th>
                    <th>Số lần làm</th>
                    <th>Chi tiết điểm các lần làm</th>
                    <th>Điểm cao nhất</th>
                    <th>Trạng thái</th>
                  </tr>
                </thead>
                <tbody>
                  {aiAssignmentsHistory.map((item) => (
                    <tr key={item.id} className="single-subject-row">
                      <td className="td-subject-name">
                        <strong>{item.title}</strong>
                      </td>
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
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Section 3: Subject Final Academic Scores Summary Table */}
          <div className="academic-scores-card">
            <div className="scores-card-header">
              <div className="scores-header-left">
                <div className="section-title-with-icon">
                  <CheckCircle2 size={18} color="#059669" />
                  <h3 className="scores-card-title">Bảng điểm trung bình môn học</h3>
                </div>
                <span className="scores-card-subtitle">
                  Học kỳ 1 • Khối 12 • Lớp 12A1
                </span>
              </div>
            </div>

            <div className="scores-table-wrapper">
              <table className="single-subject-table">
                <thead>
                  <tr>
                    <th>Môn học</th>
                    <th>Kiểm tra 15p (x3)</th>
                    <th>Điểm Giữa kỳ</th>
                    <th>Điểm Cuối kỳ</th>
                    <th>Điểm Trung bình môn</th>
                    <th>Điểm Tổng kết</th>
                    <th>Đánh giá</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="single-subject-row">
                    <td className="td-subject-name">
                      <strong>{subjectName}</strong>
                    </td>
                    <td>
                      <span className="score-pill pill-green">
                        {(student.avgScore * 0.97).toFixed(1)}
                      </span>
                    </td>
                    <td>
                      <span className="score-pill pill-green">
                        {(student.avgScore * 1.03 > 10 ? 9.8 : (student.avgScore * 1.03)).toFixed(1)}
                      </span>
                    </td>
                    <td>
                      <span className="score-pill pill-green">
                        {(student.avgScore * 0.95).toFixed(1)}
                      </span>
                    </td>
                    <td>
                      <span className="score-pill pill-purple">
                        {student.avgScore.toFixed(1)}
                      </span>
                    </td>
                    <td>
                      <span className="score-pill pill-purple">
                        {student.avgScore.toFixed(1)}
                      </span>
                    </td>
                    <td>
                      <span className="status-badge badge-good">
                        <CheckCircle2 size={13} className="status-icon" />
                        <span>Đạt chuẩn giỏi</span>
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
