// File Name: StudentSubjectRadarModal.jsx
// Description: Fullscreen interactive modal displaying subject-specific triangular radars and assignments scores matching Image 3.
// Created At: 2026-09-13
// Created By: Tam Khang
// Updated At: 2026-09-13
// Updated By: Tam Khang

import React from 'react';
import StudentSubjectRadarDetailCard from './StudentSubjectRadarDetailCard';
import './StudentSubjectRadarModal.css';

export default function StudentSubjectRadarModal({
  isOpen,
  subjectName = 'Toán học',
  onClose
}) {
  if (!isOpen) return null;

  return (
    <div className="subject-radar-modal-backdrop" onClick={onClose}>
      <div 
        className="subject-radar-modal-content"
        onClick={(e) => e.stopPropagation()}
      >
        <StudentSubjectRadarDetailCard
          subjectName={subjectName}
          onBack={onClose}
        />
      </div>
    </div>
  );
}
