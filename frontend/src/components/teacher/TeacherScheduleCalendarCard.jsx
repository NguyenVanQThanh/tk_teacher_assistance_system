// File Name: TeacherScheduleCalendarCard.jsx
// Description: Interactive weekly and monthly teaching schedule calendar selector for Teacher Dashboard.
// Created At: 2026-09-07
// Created By: Tam Khang
// Updated At: 2026-09-07
// Updated By: Tam Khang

import React, { useState } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import './TeacherScheduleCalendarCard.css';

export default function TeacherScheduleCalendarCard({ selectedDay = 5, onSelectDay }) {
  const [currentMonthIndex, setCurrentMonthIndex] = useState(9); // 9 for October (0-indexed)
  const [currentYear, setCurrentYear] = useState(2023);

  const monthNames = [
    'Tháng 1', 'Tháng 2', 'Tháng 3', 'Tháng 4', 'Tháng 5', 'Tháng 6',
    'Tháng 7', 'Tháng 8', 'Tháng 9', 'Tháng 10', 'Tháng 11', 'Tháng 12'
  ];

  const handlePrevMonth = () => {
    if (currentMonthIndex === 0) {
      setCurrentMonthIndex(11);
      setCurrentYear(prev => prev - 1);
    } else {
      setCurrentMonthIndex(prev => prev - 1);
    }
  };

  const handleNextMonth = () => {
    if (currentMonthIndex === 11) {
      setCurrentMonthIndex(0);
      setCurrentYear(prev => prev + 1);
    } else {
      setCurrentMonthIndex(prev => prev + 1);
    }
  };

  // Calendar dates matrix matching the exact mockup
  const weekDays = ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN'];

  const calendarDays = [
    // Row 1
    { id: 'd-25', day: 25, isMuted: true, hasEvent: false },
    { id: 'd-26', day: 26, isMuted: true, hasEvent: false },
    { id: 'd-27', day: 27, isMuted: true, hasEvent: false },
    { id: 'd-28', day: 28, isMuted: true, hasEvent: false },
    { id: 'd-29', day: 29, isMuted: true, hasEvent: false },
    { id: 'd-30', day: 30, isMuted: true, hasEvent: false },
    { id: 'd-1', day: 1, isMuted: false, hasEvent: false },
    // Row 2
    { id: 'd-2', day: 2, isMuted: false, hasEvent: true },
    { id: 'd-3', day: 3, isMuted: false, hasEvent: false },
    { id: 'd-4', day: 4, isMuted: false, hasEvent: true },
    { id: 'd-5', day: 5, isMuted: false, hasEvent: true },
    { id: 'd-6', day: 6, isMuted: false, hasEvent: true },
    { id: 'd-7', day: 7, isMuted: false, hasEvent: false },
    { id: 'd-8', day: 8, isMuted: false, hasEvent: false },
  ];

  return (
    <div className="teacher-schedule-calendar-card">
      <div className="cal-card-header">
        <h2 className="cal-card-title">Lịch giảng dạy</h2>
        <div className="cal-header-right">
          <span className="cal-month-label">{monthNames[currentMonthIndex]}, {currentYear}</span>
          <div className="cal-nav-buttons">
            <button 
              type="button" 
              className="cal-arrow-btn" 
              onClick={handlePrevMonth}
              aria-label="Previous month"
            >
              <ChevronLeft size={16} />
            </button>
            <button 
              type="button" 
              className="cal-arrow-btn" 
              onClick={handleNextMonth}
              aria-label="Next month"
            >
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
      </div>

      <div className="cal-grid-container">
        {/* Weekday headers */}
        <div className="cal-weekdays-row">
          {weekDays.map((wd) => (
            <div key={wd} className="cal-weekday-col">
              {wd}
            </div>
          ))}
        </div>

        {/* Days grid */}
        <div className="cal-days-grid">
          {calendarDays.map((item) => {
            const isSelected = !item.isMuted && selectedDay === item.day;
            return (
              <button
                key={item.id}
                type="button"
                className={`cal-day-cell ${item.isMuted ? 'muted' : ''} ${isSelected ? 'selected' : ''}`}
                onClick={() => {
                  if (!item.isMuted && onSelectDay) {
                    onSelectDay(item.day);
                  }
                }}
              >
                <span className={`day-number-text ${isSelected ? 'selected-day-text' : ''}`}>
                  {item.day}
                </span>
                {item.hasEvent && (
                  <span className={`event-dot-indicator ${isSelected ? 'dot-white' : 'dot-red'}`} />
                )}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
