// File Name: TeacherScheduleCalendarCard.jsx
// Description: Interactive weekly and monthly teaching schedule calendar selector for Teacher Dashboard.
// Created At: 2026-09-07
// Created By: Tam Khang
// Updated At: 2026-10-25
// Updated By: Tam Khang

import React, { useState } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import './TeacherScheduleCalendarCard.css';

export default function TeacherScheduleCalendarCard({ selectedDay, onSelectDay, scheduleItems }) {
  const now = React.useMemo(() => new Date(), []);
  const [currentMonthIndex, setCurrentMonthIndex] = useState(now.getMonth());
  const [currentYear, setCurrentYear] = useState(now.getFullYear());

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

  // Calendar dates matrix matching current month
  const weekDays = ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN'];

  const calendarDays = React.useMemo(() => {
    const firstDayIndex = new Date(currentYear, currentMonthIndex, 1).getDay();
    const leadingOffset = firstDayIndex === 0 ? 6 : firstDayIndex - 1;
    const daysInCurrentMonth = new Date(currentYear, currentMonthIndex + 1, 0).getDate();
    const prevMonthDaysCount = new Date(currentYear, currentMonthIndex, 0).getDate();

    const days = [];
    for (let i = leadingOffset - 1; i >= 0; i--) {
      days.push({
        id: `prev-${prevMonthDaysCount - i}`,
        day: prevMonthDaysCount - i,
        isMuted: true,
        hasEvent: false,
      });
    }

    const eventDays = new Set(
      (scheduleItems || [])
        .map(s => s.day || (s.date_str ? parseInt(s.date_str.split('-')[2], 10) : (s.date_number ? parseInt(s.date_number, 10) : null)))
        .filter(Boolean)
    );

    for (let d = 1; d <= daysInCurrentMonth; d++) {
      days.push({
        id: `cur-${d}`,
        day: d,
        isMuted: false,
        hasEvent: eventDays.has(d),
      });
    }

    const totalCells = Math.ceil(days.length / 7) * 7;
    const remaining = totalCells - days.length;
    for (let nextDay = 1; nextDay <= remaining; nextDay++) {
      days.push({
        id: `next-${nextDay}`,
        day: nextDay,
        isMuted: true,
        hasEvent: false,
      });
    }

    return days;
  }, [currentYear, currentMonthIndex, scheduleItems]);

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
