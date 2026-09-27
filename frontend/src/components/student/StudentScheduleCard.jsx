// File Name: StudentScheduleCard.jsx
// Description: Student monthly schedule calendar card widget matching visual mockup with interactive day selection and container focus switching.
// Created At: 2026-09-07
// Created By: Tam Khang
// Updated At: 2026-09-27
// Updated By: Tam Khang

import React, { useState } from 'react';
import { ChevronLeft, ChevronRight, ArrowUpRight } from 'lucide-react';
import './StudentScheduleCard.css';

export default function StudentScheduleCard({ 
  selectedDay: controlledDay, 
  onSelectDay,
  isActive = false,
  onClickCard
}) {
  const [internalDay, setInternalDay] = useState(8);
  const selectedDay = controlledDay !== undefined ? controlledDay : internalDay;

  const handleSelectDay = (day) => {
    setInternalDay(day);
    if (onSelectDay) onSelectDay(day);
    if (onClickCard) onClickCard();
  };

  const handleCardClick = () => {
    if (onClickCard) onClickCard();
  };

  const weekdays = ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN'];

  // March 2024 calendar days matching mockup
  const days = [
    { day: 26, isMuted: true },
    { day: 27, isMuted: true },
    { day: 28, isMuted: true },
    { day: 29, isMuted: true },
    { day: 1, isMuted: false },
    { day: 2, isMuted: false },
    { day: 3, isMuted: false },
    { day: 4, isMuted: false },
    { day: 5, isMuted: false },
    { day: 6, isMuted: false },
    { day: 7, isMuted: false },
    { day: 8, isMuted: false },
    { day: 9, isMuted: false },
    { day: 10, isMuted: false },
    { day: 11, isMuted: false },
    { day: 12, isMuted: false },
    { day: 13, isMuted: false },
    { day: 14, isMuted: false },
    { day: 15, isMuted: false },
    { day: 16, isMuted: false },
    { day: 17, isMuted: false },
  ];

  return (
    <div 
      className={`student-schedule-card ${isActive ? 'is-active-card' : ''}`}
      onClick={handleCardClick}
      title="Nhấn để xem chi tiết Lịch học hôm nay bên phải"
    >
      <div className="schedule-card-header-row">
        <h2 className="schedule-card-title">Lịch trình</h2>
        <div className="schedule-indicator-chip">
          <span>Ngày {selectedDay} Thg 3</span>
        </div>
      </div>

      <div className="schedule-month-nav-row">
        <span className="schedule-month-heading">Tháng 3, 2024</span>
        <div className="schedule-nav-arrows">
          <button 
            type="button" 
            className="cal-nav-btn" 
            aria-label="Previous"
            onClick={(e) => e.stopPropagation()}
          >
            <ChevronLeft size={16} />
          </button>
          <button 
            type="button" 
            className="cal-nav-btn" 
            aria-label="Next"
            onClick={(e) => e.stopPropagation()}
          >
            <ChevronRight size={16} />
          </button>
        </div>
      </div>

      <div className="schedule-weekdays-row">
        {weekdays.map(wd => (
          <span key={wd} className="schedule-weekday-label">{wd}</span>
        ))}
      </div>

      <div className="schedule-days-grid">
        {days.map((item, idx) => (
          <div
            key={idx}
            className={`schedule-day-cell ${item.isMuted ? 'muted' : ''} ${!item.isMuted && selectedDay === item.day ? 'active' : ''}`}
            onClick={(e) => {
              e.stopPropagation();
              if (!item.isMuted) handleSelectDay(item.day);
            }}
          >
            {item.day}
          </div>
        ))}
      </div>

      {/* Footer prompt */}
      <div className="schedule-card-footer-prompt">
        <span className="footer-prompt-text">
          {isActive ? 'Đang xem lịch học bên phải' : 'Xem lịch học chi tiết'}
        </span>
        <ArrowUpRight size={14} className="prompt-arrow-icon" />
      </div>
    </div>
  );
}
