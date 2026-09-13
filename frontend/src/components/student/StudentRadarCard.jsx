// File Name: StudentRadarCard.jsx
// Description: Multi-subject radar distribution card for students with centered total count badge matching mockup.
// Created At: 2026-09-07
// Created By: Tam Khang
// Updated At: 2026-09-07
// Updated By: Tam Khang

import React from 'react';
import './StudentRadarCard.css';

export default function StudentRadarCard({
  title = 'Bài tập trên lớp',
  totalLabel = 'Tổng: 15',
  scores = [8.5, 7.5, 8.0, 7.0, 6.0, 7.5],
  maxScore = 10,
  size = 220,
  selectedSubject = null,
  onSelectSubject
}) {
  const subjects = ['Toán Học', 'Vật Lí', 'Hóa Học', 'Tiếng Anh', 'Lịch Sử', 'Tin học'];
  const center = size / 2;
  const radius = size * 0.36;
  const totalAxes = subjects.length;
  const angleStep = (Math.PI * 2) / totalAxes;

  const getCoordinates = (value, index) => {
    const angle = index * angleStep - Math.PI / 2;
    const r = (value / maxScore) * radius;
    const x = center + r * Math.cos(angle);
    const y = center + r * Math.sin(angle);
    return { x, y };
  };

  const levels = [0.33, 0.66, 1.0];

  const polygonPoints = scores
    .map((val, idx) => {
      const { x, y } = getCoordinates(val, idx);
      return `${x},${y}`;
    })
    .join(' ');

  return (
    <div className="student-radar-card">
      <h2 className="radar-card-title">{title}</h2>
      <div className="radar-chart-wrapper">
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
          {/* Concentric Background Grid Polygons */}
          {levels.map((level, lvlIdx) => {
            const points = subjects
              .map((_, idx) => {
                const { x, y } = getCoordinates(maxScore * level, idx);
                return `${x},${y}`;
              })
              .join(' ');
            return (
              <polygon
                key={`grid-${lvlIdx}`}
                points={points}
                fill="none"
                stroke="#E2E8F0"
                strokeWidth="1"
              />
            );
          })}

          {/* Axis lines and text labels */}
          {subjects.map((subj, idx) => {
            const { x: endX, y: endY } = getCoordinates(maxScore, idx);
            const angle = idx * angleStep - Math.PI / 2;
            const labelRadius = radius + 20;
            const lx = center + labelRadius * Math.cos(angle);
            const ly = center + labelRadius * Math.sin(angle) + 4;
            const isSelected = selectedSubject && (
              selectedSubject.toLowerCase() === subj.toLowerCase() ||
              subj.toLowerCase().includes(selectedSubject.toLowerCase())
            );

            return (
              <g 
                key={`axis-${idx}`}
                onClick={() => onSelectSubject && onSelectSubject(subj)}
                style={{ cursor: 'pointer' }}
                className="radar-subject-axis-group"
              >
                <line
                  x1={center}
                  y1={center}
                  x2={endX}
                  y2={endY}
                  stroke={isSelected ? '#7C3AED' : '#E2E8F0'}
                  strokeWidth={isSelected ? '2' : '1'}
                />
                <text
                  x={lx}
                  y={ly}
                  textAnchor="middle"
                  fontSize={isSelected ? "11.5" : "10.5"}
                  fontWeight={isSelected ? "800" : "600"}
                  fill={isSelected ? "#7C3AED" : "#475569"}
                  fontFamily="inherit"
                  className="radar-clickable-subject-label"
                >
                  {subj}
                </text>
              </g>
            );
          })}

          {/* Filled polygon for student data */}
          <polygon
            points={polygonPoints}
            fill="rgba(124, 58, 237, 0.16)"
            stroke="#4D308D"
            strokeWidth="2"
          />

          {/* Center Total Count Box */}
          <foreignObject
            x={center - 36}
            y={center - 14}
            width="72"
            height="28"
          >
            <div
              style={{
                backgroundColor: '#FFFFFF',
                border: '1.5px solid #4D308D',
                borderRadius: '8px',
                padding: '2px 6px',
                fontSize: '11px',
                fontWeight: '800',
                color: '#4D308D',
                textAlign: 'center',
                boxShadow: '0 2px 6px rgba(77, 48, 141, 0.12)',
                lineHeight: '22px'
              }}
            >
              {totalLabel}
            </div>
          </foreignObject>
        </svg>
      </div>
    </div>
  );
}
