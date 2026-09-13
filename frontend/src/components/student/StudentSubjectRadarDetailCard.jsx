// File Name: StudentSubjectRadarDetailCard.jsx
// Description: Subject-specific cognitive level triangular radar charts and detailed assignments score table matching Image 3 with rich mock data across all 6 high-school subjects.
// Created At: 2026-09-13
// Created By: Tam Khang
// Updated At: 2026-09-13
// Updated By: Tam Khang

import React, { useState } from 'react';
import { 
  BookOpen, 
  Sparkles, 
  CheckCheck,
  ArrowLeft
} from 'lucide-react';
import './StudentSubjectRadarDetailCard.css';

// Rich mock data for all 6 high-school subjects
const SUBJECT_MOCK_DATA = {
  'Toán Học': {
    classRadar: { know: 9.0, comp: 8.6, app: 8.3, total: '18/20 bài', avg: '88%' },
    aiRadar: { know: 8.4, comp: 8.1, app: 7.7, total: '14 bài tập AI', avg: '85%' },
    exercises: [
      { id: 1, title: 'Kiểm tra 15p – Đạo hàm và ứng dụng', attempts: '2 lần làm', scores: ['Lần 1: 7.5', 'Lần 2: 9.0'], best: '9.0', status: 'Đã hoàn thành' },
      { id: 2, title: 'Bài tập về nhà – Hình học không gian Oxyz', attempts: '1 lần làm', scores: ['Lần 1: 8.5'], best: '8.5', status: 'Đã hoàn thành' },
      { id: 3, title: 'Kiểm tra 45p – Khảo sát hàm số và đồ thị', attempts: '1 lần làm', scores: ['Lần 1: 9.2'], best: '9.2', status: 'Đã hoàn thành' },
      { id: 4, title: 'Luyện tập phương trình mũ & logarit', attempts: '3 lần làm', scores: ['Lần 1: 6.8', 'Lần 2: 8.0', 'Lần 3: 8.8'], best: '8.8', status: 'Đã hoàn thành' }
    ]
  },
  'Vật Lí': {
    classRadar: { know: 8.8, comp: 8.2, app: 7.9, total: '16/20 bài', avg: '83%' },
    aiRadar: { know: 8.2, comp: 7.9, app: 7.5, total: '12 bài tập AI', avg: '80%' },
    exercises: [
      { id: 1, title: 'Kiểm tra 15p – Dao động điều hòa con lắc', attempts: '2 lần làm', scores: ['Lần 1: 7.0', 'Lần 2: 8.8'], best: '8.8', status: 'Đã hoàn thành' },
      { id: 2, title: 'Bài tập về nhà – Sóng cơ học và giao thoa sóng', attempts: '1 lần làm', scores: ['Lần 1: 8.2'], best: '8.2', status: 'Đã hoàn thành' },
      { id: 3, title: 'Kiểm tra 45p – Mạch điện xoay chiều RLC', attempts: '2 lần làm', scores: ['Lần 1: 7.8', 'Lần 2: 8.5'], best: '8.5', status: 'Đã hoàn thành' },
      { id: 4, title: 'Thực hành ảo – Hiện tượng sóng dừng trên dây', attempts: '1 lần làm', scores: ['Lần 1: 9.0'], best: '9.0', status: 'Đã hoàn thành' }
    ]
  },
  'Hóa Học': {
    classRadar: { know: 9.2, comp: 8.8, app: 8.5, total: '19/20 bài', avg: '90%' },
    aiRadar: { know: 8.7, comp: 8.5, app: 8.1, total: '15 bài tập AI', avg: '88%' },
    exercises: [
      { id: 1, title: 'Kiểm tra 15p – Este và Lipit căn bản', attempts: '2 lần làm', scores: ['Lần 1: 8.0', 'Lần 2: 9.2'], best: '9.2', status: 'Đã hoàn thành' },
      { id: 2, title: 'Bài tập về nhà – Amin, Amino Axit và Peptit', attempts: '1 lần làm', scores: ['Lần 1: 8.8'], best: '8.8', status: 'Đã hoàn thành' },
      { id: 3, title: 'Kiểm tra 45p – Tổng hợp Hóa học hữu cơ 12', attempts: '1 lần làm', scores: ['Lần 1: 9.5'], best: '9.5', status: 'Đã hoàn thành' },
      { id: 4, title: 'Bài tập rèn luyện – Kim loại kiềm và kiềm thổ', attempts: '2 lần làm', scores: ['Lần 1: 8.2', 'Lần 2: 9.0'], best: '9.0', status: 'Đã hoàn thành' }
    ]
  },
  'Tiếng Anh': {
    classRadar: { know: 9.5, comp: 9.0, app: 8.7, total: '20/20 bài', avg: '92%' },
    aiRadar: { know: 9.0, comp: 8.6, app: 8.4, total: '18 bài tập AI', avg: '89%' },
    exercises: [
      { id: 1, title: 'Reading Comprehension – Unit 3: Life Stories', attempts: '2 lần làm', scores: ['Lần 1: 8.5', 'Lần 2: 9.5'], best: '9.5', status: 'Đã hoàn thành' },
      { id: 2, title: 'Grammar Revision – Relative Clauses & Inversion', attempts: '1 lần làm', scores: ['Lần 1: 9.0'], best: '9.0', status: 'Đã hoàn thành' },
      { id: 3, title: 'Speaking Assignment – Cultural Diversity', attempts: '1 lần làm', scores: ['Lần 1: 8.8'], best: '8.8', status: 'Đã hoàn thành' },
      { id: 4, title: 'Vocabulary Quiz – Endangered Species', attempts: '2 lần làm', scores: ['Lần 1: 8.0', 'Lần 2: 9.2'], best: '9.2', status: 'Đã hoàn thành' }
    ]
  },
  'Lịch Sử': {
    classRadar: { know: 8.5, comp: 8.0, app: 7.6, total: '15/20 bài', avg: '80%' },
    aiRadar: { know: 8.2, comp: 7.7, app: 7.2, total: '11 bài tập AI', avg: '78%' },
    exercises: [
      { id: 1, title: 'Kiểm tra 15p – Trật tự thế giới hai cực Ianta', attempts: '1 lần làm', scores: ['Lần 1: 8.5'], best: '8.5', status: 'Đã hoàn thành' },
      { id: 2, title: 'Bài tập chuyên đề – Phong trào giải phóng dân tộc', attempts: '2 lần làm', scores: ['Lần 1: 7.2', 'Lần 2: 8.2'], best: '8.2', status: 'Đã hoàn thành' },
      { id: 3, title: 'Kiểm tra 45p – Cách mạng tháng Tám 1945', attempts: '1 lần làm', scores: ['Lần 1: 8.8'], best: '8.8', status: 'Đã hoàn thành' }
    ]
  },
  'Tin học': {
    classRadar: { know: 9.3, comp: 8.9, app: 8.6, total: '17/20 bài', avg: '89%' },
    aiRadar: { know: 8.8, comp: 8.4, app: 8.2, total: '16 bài tập AI', avg: '86%' },
    exercises: [
      { id: 1, title: 'Thực hành lập trình – Cấu trúc dữ liệu Mảng và Xâu', attempts: '2 lần làm', scores: ['Lần 1: 8.5', 'Lần 2: 9.5'], best: '9.5', status: 'Đã hoàn thành' },
      { id: 2, title: 'Kiểm tra 15p – Thuật toán sắp xếp và tìm kiếm', attempts: '1 lần làm', scores: ['Lần 1: 9.0'], best: '9.0', status: 'Đã hoàn thành' },
      { id: 3, title: 'Bài tập lớn – Xây dựng ứng dụng quản lý học sinh', attempts: '1 lần làm', scores: ['Lần 1: 9.2'], best: '9.2', status: 'Đã hoàn thành' }
    ]
  }
};

/**
 * Reusable 3-Axis Equilateral Triangular Radar Chart
 * With wide viewBox and extra padding to prevent text truncation
 */
function TriangularRadar({
  scores = { know: 9.0, comp: 8.6, app: 8.3 },
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

  const getVertexCoord = (r, angleIdx) => {
    const a = angles[angleIdx];
    return {
      x: centerX + r * Math.cos(a),
      y: centerY + r * Math.sin(a)
    };
  };

  // Outer grid triangles at 33%, 66%, 100%
  const gridLevels = [0.33, 0.66, 1.0];

  // Data polygon points
  const p1 = getVertexCoord((scores.know / maxScore) * radius, 0);
  const p2 = getVertexCoord((scores.comp / maxScore) * radius, 1);
  const p3 = getVertexCoord((scores.app / maxScore) * radius, 2);
  const dataPolygonPoints = `${p1.x},${p1.y} ${p2.x},${p2.y} ${p3.x},${p3.y}`;

  const isPurple = theme === 'purple';
  const strokeColor = isPurple ? '#7C3AED' : '#2563EB';
  const fillColor = isPurple ? 'rgba(124, 58, 237, 0.18)' : 'rgba(37, 99, 235, 0.18)';
  const dotColor = isPurple ? '#7C3AED' : '#2563EB';

  return (
    <div className="triangular-radar-wrapper">
      <svg 
        width="240" 
        height="200" 
        viewBox="0 0 240 200"
        style={{ width: '240px', height: '200px', minWidth: '240px', minHeight: '200px', display: 'block' }}
      >
        {/* Concentric Grid Triangles */}
        {gridLevels.map((lvl, idx) => {
          const r = radius * lvl;
          const v1 = getVertexCoord(r, 0);
          const v2 = getVertexCoord(r, 1);
          const v3 = getVertexCoord(r, 2);
          return (
            <polygon
              key={`grid-${idx}`}
              points={`${v1.x},${v1.y} ${v2.x},${v2.y} ${v3.x},${v3.y}`}
              fill="none"
              stroke="#E2E8F0"
              strokeWidth="1"
            />
          );
        })}

        {/* 3 Radiating Axis Lines from center */}
        {angles.map((_, idx) => {
          const end = getVertexCoord(radius, idx);
          return (
            <line
              key={`axis-${idx}`}
              x1={centerX}
              y1={centerY}
              x2={end.x}
              y2={end.y}
              stroke="#E2E8F0"
              strokeWidth="1"
            />
          );
        })}

        {/* Vertex text labels */}
        {/* Top: Nhận biết */}
        <text
          x={centerX}
          y={centerY - radius - 10}
          textAnchor="middle"
          fontSize="11.5"
          fontWeight="600"
          fill="#334155"
        >
          Nhận biết
        </text>

        {/* Bottom Right: Thông hiểu */}
        <text
          x={centerX + radius * Math.cos(angles[1]) + 4}
          y={centerY + radius * Math.sin(angles[1]) + 18}
          textAnchor="middle"
          fontSize="11.5"
          fontWeight="600"
          fill="#334155"
        >
          Thông hiểu
        </text>

        {/* Bottom Left: Vận dụng */}
        <text
          x={centerX + radius * Math.cos(angles[2]) - 4}
          y={centerY + radius * Math.sin(angles[2]) + 18}
          textAnchor="middle"
          fontSize="11.5"
          fontWeight="600"
          fill="#334155"
        >
          Vận dụng
        </text>

        {/* Data polygon */}
        <polygon
          points={dataPolygonPoints}
          fill={fillColor}
          stroke={strokeColor}
          strokeWidth="2"
        />

        {/* Data Points */}
        {[p1, p2, p3].map((pt, idx) => (
          <circle
            key={`dot-${idx}`}
            cx={pt.x}
            cy={pt.y}
            r="3.5"
            fill={dotColor}
            stroke="#FFFFFF"
            strokeWidth="1.5"
          />
        ))}
      </svg>
    </div>
  );
}

export default function StudentSubjectRadarDetailCard({
  subjectName = 'Toán Học',
  onBack
}) {
  const allSubjectNames = ['Toán Học', 'Vật Lí', 'Hóa Học', 'Tiếng Anh', 'Lịch Sử', 'Tin học'];
  
  // Internal active subject selector to allow switching inside the modal
  const [currentSubject, setCurrentSubject] = useState(subjectName);

  React.useEffect(() => {
    if (subjectName) {
      setCurrentSubject(subjectName);
    }
  }, [subjectName]);

  const subjectData = SUBJECT_MOCK_DATA[currentSubject] || SUBJECT_MOCK_DATA['Toán Học'];

  return (
    <div className="student-subject-radar-detail-wrapper">
      {/* Top Header Navigation Bar matching Image 3 */}
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

        {/* Quick Subject Tabs to test all subjects */}
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

      {/* Row 1: Two 3-Axis Radar Cards Side-by-Side matching Image 3 */}
      <div className="subject-radar-two-cards-row">
        {/* Card 1: Bài tập trên lớp */}
        <div className="subject-radar-stat-card theme-purple">
          <div className="stat-card-header">
            <div className="card-header-left">
              <div className="card-icon-box purple-bg">
                <BookOpen size={18} className="icon-purple" />
              </div>
              <div>
                <h3 className="stat-card-title">Bài tập trên lớp</h3>
                <p className="stat-card-subtitle">{subjectData.classRadar.avg} Điểm trung bình hoàn thành</p>
              </div>
            </div>
            <span className="card-stat-pill pill-purple">
              Đã làm: {subjectData.classRadar.total}
            </span>
          </div>

          <div className="stat-card-body-content">
            <TriangularRadar
              scores={subjectData.classRadar}
              width={240}
              height={200}
              theme="purple"
            />
            <div className="stat-metrics-column">
              <div className="metric-row-item">
                <span className="metric-bullet purple-bullet">•</span>
                <span className="metric-label">Nhận biết</span>
                <strong className="metric-score">{subjectData.classRadar.know}/10</strong>
              </div>
              <div className="metric-row-item">
                <span className="metric-bullet purple-bullet">•</span>
                <span className="metric-label">Thông hiểu</span>
                <strong className="metric-score">{subjectData.classRadar.comp}/10</strong>
              </div>
              <div className="metric-row-item">
                <span className="metric-bullet purple-bullet">•</span>
                <span className="metric-label">Vận dụng</span>
                <strong className="metric-score">{subjectData.classRadar.app}/10</strong>
              </div>
            </div>
          </div>
        </div>

        {/* Card 2: Bài tập do AI tạo */}
        <div className="subject-radar-stat-card theme-blue">
          <div className="stat-card-header">
            <div className="card-header-left">
              <div className="card-icon-box blue-bg">
                <Sparkles size={18} className="icon-blue" />
              </div>
              <div>
                <h3 className="stat-card-title">Bài tập do AI tạo</h3>
                <p className="stat-card-subtitle">{subjectData.aiRadar.avg} Điểm trung bình hoàn thành</p>
              </div>
            </div>
            <span className="card-stat-pill pill-blue">
              Đã làm: {subjectData.aiRadar.total}
            </span>
          </div>

          <div className="stat-card-body-content">
            <TriangularRadar
              scores={subjectData.aiRadar}
              width={240}
              height={200}
              theme="blue"
            />
            <div className="stat-metrics-column">
              <div className="metric-row-item">
                <span className="metric-bullet blue-bullet">•</span>
                <span className="metric-label">Nhận biết</span>
                <strong className="metric-score">{subjectData.aiRadar.know}/10</strong>
              </div>
              <div className="metric-row-item">
                <span className="metric-bullet blue-bullet">•</span>
                <span className="metric-label">Thông hiểu</span>
                <strong className="metric-score">{subjectData.aiRadar.comp}/10</strong>
              </div>
              <div className="metric-row-item">
                <span className="metric-bullet blue-bullet">•</span>
                <span className="metric-label">Vận dụng</span>
                <strong className="metric-score">{subjectData.aiRadar.app}/10</strong>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Row 2: Table Chi tiết điểm: Bài tập trên lớp matching Image 3 */}
      <div className="subject-exercises-score-table-card">
        <div className="table-card-header">
          <div className="table-card-title-group">
            <div className="table-title-row">
              <BookOpen size={18} className="icon-purple-title" />
              <h3 className="table-card-main-title">Chi tiết điểm: Bài tập trên lớp</h3>
              <span className="table-count-pill">{subjectData.exercises.length} bài</span>
            </div>
            <p className="table-card-subtitle">
              Theo dõi số lần làm bài và điểm số chi tiết của mỗi lần nộp bài trên lớp môn {currentSubject}
            </p>
          </div>
        </div>

        <div className="table-responsive-wrapper">
          <table className="subject-score-data-table">
            <thead>
              <tr>
                <th className="th-name">Tên bài tập trên lớp</th>
                <th className="th-attempts">Số lần làm</th>
                <th className="th-detail-scores">Chi tiết điểm các lần làm</th>
                <th className="th-highest">Điểm cao nhất</th>
                <th className="th-status">Trạng thái</th>
              </tr>
            </thead>
            <tbody>
              {subjectData.exercises.map((item) => (
                <tr key={item.id} className="table-data-row">
                  <td className="td-name">
                    <span className="exercise-row-title">{item.title}</span>
                  </td>
                  <td className="td-attempts">
                    <span className="attempt-count-pill">{item.attempts}</span>
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
                    <span className="highest-score-pill">{item.best}</span>
                  </td>
                  <td className="td-status">
                    <span className="status-completed-pill">
                      <CheckCheck size={14} className="icon-check-double" />
                      <span>{item.status}</span>
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
