// File Name: RadarChart.jsx
// Description: Interactive SVG Radar Chart visualizing multi-subject performance.
// Created At: 2026-08-30
// Created By: Tam Khang
// Updated At: 2026-08-30
// Updated By: Tam Khang

import React from 'react';

export default function RadarChart({
  size = 260,
  subjects = ['Toán Học', 'Vật Lí', 'Hóa Học', 'Tiếng Anh', 'Lịch Sử', 'Tin học'],
  classData = [8.5, 7.0, 9.0, 8.0, 6.5, 8.8],
  averageData = [6.5, 6.0, 7.5, 7.0, 7.0, 6.5],
  maxScore = 10,
}) {
  const center = size / 2;
  const radius = size * 0.35;
  const totalAxes = subjects.length;
  const angleStep = (Math.PI * 2) / totalAxes;

  // Helper to compute coordinates
  const getCoordinates = (value, index) => {
    const angle = index * angleStep - Math.PI / 2;
    const r = (value / maxScore) * radius;
    const x = center + r * Math.cos(angle);
    const y = center + r * Math.sin(angle);
    return { x, y };
  };

  // Concentric polygon grid levels
  const levels = [0.25, 0.5, 0.75, 1.0];

  const getPolygonPoints = (data) => {
    return data
      .map((val, idx) => {
        const { x, y } = getCoordinates(val, idx);
        return `${x},${y}`;
      })
      .join(' ');
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        {/* Concentric Grid Polygons */}
        {levels.map((level, lvlIdx) => {
          const points = subjects
            .map((_, idx) => {
              const { x, y } = getCoordinates(maxScore * level, idx);
              return `${x},${y}`;
            })
            .join(' ');
          return (
            <polygon
              key={`grid-lvl-${lvlIdx}`}
              points={points}
              fill="none"
              stroke="#e2e8f0"
              strokeWidth="1"
              strokeDasharray={lvlIdx === levels.length - 1 ? 'none' : '3,3'}
            />
          );
        })}

        {/* Axis Spokes & Labels */}
        {subjects.map((subject, idx) => {
          const { x: endX, y: endY } = getCoordinates(maxScore, idx);
          const angle = idx * angleStep - Math.PI / 2;
          const labelRadius = radius + 22;
          const labelX = center + labelRadius * Math.cos(angle);
          const labelY = center + labelRadius * Math.sin(angle) + 4;

          return (
            <g key={`axis-${idx}`}>
              <line
                x1={center}
                y1={center}
                x2={endX}
                y2={endY}
                stroke="#e2e8f0"
                strokeWidth="1"
              />
              <text
                x={labelX}
                y={labelY}
                textAnchor="middle"
                fontSize="11"
                fontWeight="600"
                fill="#64748b"
                fontFamily="inherit"
              >
                {subject}
              </text>
            </g>
          );
        })}

        {/* Data Polygon 2: Trung bình khối (Blue) */}
        <polygon
          points={getPolygonPoints(averageData)}
          fill="rgba(59, 130, 246, 0.12)"
          stroke="#3b82f6"
          strokeWidth="1.8"
          strokeDasharray="4,3"
          style={{
            animation: 'polygonReveal 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards',
            transformOrigin: `${center}px ${center}px`,
          }}
        />

        {/* Data Polygon 1: Lớp 12A1 (Purple) */}
        <polygon
          points={getPolygonPoints(classData)}
          fill="rgba(124, 58, 237, 0.22)"
          stroke="#7c3aed"
          strokeWidth="2"
          style={{
            animation: 'polygonReveal 1s cubic-bezier(0.16, 1, 0.3, 1) forwards',
            transformOrigin: `${center}px ${center}px`,
          }}
        />

        {/* Data points (dots) for Class */}
        {classData.map((val, idx) => {
          const { x, y } = getCoordinates(val, idx);
          return (
            <circle
              key={`dot-class-${idx}`}
              cx={x}
              cy={y}
              r="4"
              fill="#7c3aed"
              stroke="#ffffff"
              strokeWidth="1.5"
              style={{
                animation: `fadeInDot 0.6s ease forwards ${0.3 + idx * 0.08}s`,
                opacity: 0,
              }}
            />
          );
        })}
      </svg>
      <style>{`
        @keyframes polygonReveal {
          from {
            opacity: 0;
            transform: scale(0.6);
          }
          to {
            opacity: 1;
            transform: scale(1);
          }
        }
        @keyframes fadeInDot {
          from {
            opacity: 0;
            transform: scale(0);
          }
          to {
            opacity: 1;
            transform: scale(1);
          }
        }
      `}</style>

      {/* Chart Legend */}
      <div style={{ display: 'flex', gap: '20px', marginTop: '10px', fontSize: '12px', color: '#64748b' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#7c3aed' }}></span>
          <span style={{ fontWeight: 600, color: '#475569' }}>Lớp 12A1</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#3b82f6' }}></span>
          <span style={{ fontWeight: 600, color: '#475569' }}>Trung bình khối</span>
        </div>
      </div>
    </div>
  );
}
